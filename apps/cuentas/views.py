from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.forms import IngresoForm
from apps.cuentas.sesion import abrir_sesion, cerrar_sesion, publica
from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi, token_de


@publica
@require_http_methods(["GET", "POST"])
def ingreso(request):
    # Quien ya tiene sesión no pide un segundo token: sigue donde iba.
    if token_de(request):
        return redirect("conjuntos:selector")

    formulario = IngresoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            datos = api_cuentas.iniciar_sesion(request, **formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            for campo, mensajes in error.campos.items():
                formulario.add_error(campo if campo in formulario.fields else None, mensajes)
            if not error.campos:
                formulario.add_error(None, error.mensaje)
        else:
            abrir_sesion(request, datos)
            return redirect("conjuntos:selector")

    return render(request, "cuentas/ingreso.html", {"formulario": formulario})


@require_POST
def salir(request):
    try:
        api_cuentas.cerrar_sesion(request)
    except (ApiNoDisponible, ErrorDeApi):
        # Si el token ya venció o la API no responde, la sesión de este lado se cierra igual.
        pass
    cerrar_sesion(request)
    return redirect("cuentas:ingreso")


@publica
def recuperar_contrasena(request):
    """Maqueta: la recuperación por correo todavía no existe en la API (HU-01)."""
    return render(request, "cuentas/recuperar_contrasena.html")
