from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.cuentas.sesion import destino_despues_de_entrar, guardar_estado, tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import conjuntos as api_conjuntos
from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import ACENTOS, AdministradorForm, ConjuntoForm


@require_http_methods(["GET", "POST"])
def selector(request):
    error = None
    if request.method == "POST":
        try:
            estado = api_cuentas.elegir_conjunto(request, request.POST.get("conjunto"))
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
        else:
            guardar_estado(request, estado)
            return destino_despues_de_entrar(request)

    try:
        conjuntos = api_cuentas.listar_conjuntos(request)
    except ApiNoDisponible:
        conjuntos = []
        error = error or MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        conjuntos = []
        error = error or api_error.mensaje
    contexto = {
        "conjuntos": conjuntos or [],
        "error": error,
        "puede_crear": tiene_permiso(request, "conjunto.crear"),
    }
    return render(request, "conjuntos/selector.html", contexto)


# Asistente de creación (HU-03). Cada paso se guarda apenas se completa: se puede salir y volver.


def cargar_resumen(request):
    """El resumen del conjunto activo, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_conjuntos.resumen(request), None
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje


@require_http_methods(["GET", "POST"])
def nuevo(request):
    """Paso 1 para un conjunto nuevo. Al crearlo, pasa a ser el conjunto activo."""
    formulario = ConjuntoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            respuesta = api_conjuntos.crear(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            guardar_estado(request, respuesta)
            return redirect("conjuntos:asistente-administracion")
    return render(request, "conjuntos/asistente_datos.html", {"formulario": formulario, "acentos": ACENTOS, "paso": 1})


@require_http_methods(["GET", "POST"])
def datos(request):
    """Paso 1 sobre el conjunto activo: corregir sus datos básicos."""
    resumen, error = cargar_resumen(request)
    if resumen is None:
        return render(request, "conjuntos/asistente_datos.html", {"error": error, "paso": 1, "editando": True})

    conjunto = resumen["conjunto"]
    formulario = ConjuntoForm(
        request.POST or None,
        initial={"nombre": conjunto["nombre"], "direccion": conjunto["direccion"], "acento": conjunto["acento"]},
    )
    if request.method == "POST" and formulario.is_valid():
        try:
            resumen = api_conjuntos.editar(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            # El nombre y el color de la barra salen de la sesión: se actualizan aquí.
            activo = {clave: resumen["conjunto"][clave] for clave in ("id", "nombre", "acento")}
            guardar_estado(request, {"conjunto_activo": activo})
            return redirect("conjuntos:asistente-administracion")
    contexto = {"formulario": formulario, "acentos": ACENTOS, "paso": 1, "editando": True}
    return render(request, "conjuntos/asistente_datos.html", contexto)


@require_http_methods(["GET", "POST"])
def administracion(request):
    """Paso 2: quién administra el conjunto. Se puede agregar una cuenta con rol Administración."""
    formulario = AdministradorForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_cuentas.crear_usuario(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("conjuntos:asistente-administracion")
    resumen, error = cargar_resumen(request)
    contexto = {"formulario": formulario, "resumen": resumen, "error": error, "paso": 2}
    return render(request, "conjuntos/asistente_administracion.html", contexto)


@require_http_methods(["GET", "POST"])
def resumen(request):
    """Paso 3: revisar y, si ya cumple todo, dejarlo operativo."""
    faltantes = None
    activado = False
    error = None
    if request.method == "POST":
        try:
            api_conjuntos.activar(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
            faltantes = api_error.cuerpo.get("faltantes")
        else:
            activado = True
    datos_del_resumen, error_al_cargar = cargar_resumen(request)
    contexto = {
        "resumen": datos_del_resumen,
        "error": error or error_al_cargar,
        "faltantes": faltantes,
        "activado": activado,
        "nombre_del_acento": dict(ACENTOS).get((datos_del_resumen or {}).get("conjunto", {}).get("acento")),
        "paso": 3,
    }
    return render(request, "conjuntos/asistente_resumen.html", contexto)
