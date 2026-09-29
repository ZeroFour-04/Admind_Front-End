from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.forms import CodigoForm, IngresoForm, RecuperarForm, RestablecerForm
from apps.cuentas.sesion import (
    abrir_sesion,
    antes_del_segundo_factor,
    cerrar_sesion,
    destino_despues_de_entrar,
    guardar_estado,
    publica,
    segundo_factor_pendiente,
)
from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi, token_de


def errores_de_la_api_al_formulario(formulario, error):
    """Cada error de la API cae bajo su campo; los que no son de un campo, arriba del formulario."""
    for campo, mensajes in error.campos.items():
        formulario.add_error(campo if campo in formulario.fields else None, mensajes)
    if not error.campos:
        formulario.add_error(None, error.mensaje)


@publica
@require_http_methods(["GET", "POST"])
def ingreso(request):
    # Quien ya tiene sesión no pide un segundo token: sigue donde iba.
    if token_de(request):
        return destino_despues_de_entrar(request)

    formulario = IngresoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            datos = api_cuentas.iniciar_sesion(request, **formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            abrir_sesion(request, datos)
            return destino_despues_de_entrar(request)

    contexto = {"formulario": formulario, "restablecida": "restablecida" in request.GET}
    return render(request, "cuentas/ingreso.html", contexto)


@antes_del_segundo_factor
@require_POST
def salir(request):
    try:
        api_cuentas.cerrar_sesion(request)
    except (ApiNoDisponible, ErrorDeApi):
        # Si el token ya venció o la API no responde, la sesión de este lado se cierra igual.
        pass
    cerrar_sesion(request)
    return redirect("cuentas:ingreso")


@antes_del_segundo_factor
@require_http_methods(["GET"])
def perfil(request):
    try:
        usuario = api_cuentas.obtener_perfil(request)
    except ApiNoDisponible:
        usuario = None
        error = MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        usuario = None
        error = api_error.mensaje
    else:
        error = None
    return render(request, "cuentas/perfil.html", {"usuario": usuario, "error": error})


# Recuperación de contraseña (HU-01)


@publica
@require_http_methods(["GET", "POST"])
def recuperar_contrasena(request):
    formulario = RecuperarForm(request.POST or None)
    enviado = None
    if request.method == "POST" and formulario.is_valid():
        try:
            respuesta = api_cuentas.solicitar_recuperacion(request, formulario.cleaned_data["correo"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            # El mismo mensaje exista o no el correo: lo decide la API (HU-01).
            enviado = respuesta["detail"]
    return render(request, "cuentas/recuperar_contrasena.html", {"formulario": formulario, "enviado": enviado})


@publica
@require_http_methods(["GET", "POST"])
def restablecer_contrasena(request, uid, token):
    formulario = RestablecerForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_cuentas.restablecer_contrasena(request, uid, token, formulario.cleaned_data["contrasena"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            # La API cerró todas las sesiones de esa cuenta: esta también.
            cerrar_sesion(request)
            return redirect(f"{reverse('cuentas:ingreso')}?restablecida=1")
    return render(request, "cuentas/restablecer_contrasena.html", {"formulario": formulario})


# Segundo factor (HU-02)

# El QR que se está configurando. Vive en la sesión de este servidor, nunca en el navegador, para
# no generar un secreto nuevo si la persona se equivoca de código o recarga la página.
CLAVE_SECRETO_EN_CONFIGURACION = "segundo_factor_en_configuracion"


@antes_del_segundo_factor
@require_http_methods(["GET", "POST"])
def configurar_segundo_factor(request):
    formulario = CodigoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            datos = api_cuentas.activar_dos_factores(request, formulario.cleaned_data["codigo"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            request.session.pop(CLAVE_SECRETO_EN_CONFIGURACION, None)
            guardar_estado(request, datos)
            # Única vez que se muestran: la API no los vuelve a entregar.
            return render(
                request, "cuentas/codigos_de_respaldo.html", {"codigos": datos["codigos_de_respaldo"]}
            )

    secreto = request.session.get(CLAVE_SECRETO_EN_CONFIGURACION)
    if secreto is None:
        try:
            secreto = api_cuentas.configurar_dos_factores(request)
        except ApiNoDisponible:
            return render(request, "cuentas/configurar_segundo_factor.html", {"error": MENSAJE_API_NO_DISPONIBLE})
        except ErrorDeApi as error:
            if error.estado == 409:
                return redirect("cuentas:verificar-segundo-factor")
            return render(request, "cuentas/configurar_segundo_factor.html", {"error": error.mensaje})
        request.session[CLAVE_SECRETO_EN_CONFIGURACION] = secreto
    return render(
        request, "cuentas/configurar_segundo_factor.html", {"formulario": formulario, "secreto": secreto}
    )


@antes_del_segundo_factor
@require_http_methods(["GET", "POST"])
def verificar_segundo_factor(request):
    if not segundo_factor_pendiente(request):
        return destino_despues_de_entrar(request)
    formulario = CodigoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            estado = api_cuentas.verificar_dos_factores(request, formulario.cleaned_data["codigo"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            guardar_estado(request, estado)
            return destino_despues_de_entrar(request)
    return render(request, "cuentas/verificar_segundo_factor.html", {"formulario": formulario})


@antes_del_segundo_factor
def continuar(request):
    """Después de guardar los códigos de respaldo."""
    return destino_despues_de_entrar(request)
