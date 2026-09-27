"""Reglas beta de reserva del conjunto activo (HU-10). El alta va en dos pasos y sin JavaScript.

El paso de reglas del asistente (HU-03) usa estas mismas vistas con `en_asistente=True`.
"""
from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.areas.views import cargar_areas
from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import reglas as api_reglas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import FORMULARIO_POR_TIPO, TIPOS_DE_REGLA, ElegirTipoForm, iniciales

AVISO_DE_VERSION = "Al guardar se crea una versión nueva; la anterior queda en el historial."


def con_fechas(regla):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    return {**regla, "vigencia_desde": date.fromisoformat(regla["vigencia_desde"])}


def cargar_reglas(request):
    try:
        return [con_fechas(regla) for regla in api_reglas.listar(request)], None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def lista(request, error_de_accion=None):
    reglas, error = cargar_reglas(request)
    contexto = {"reglas": reglas, "error": error_de_accion or error, "puede_configurar": tiene_permiso(request, "regla.configurar")}
    return render(request, "reglas/lista.html", contexto)


def a_donde_volver(en_asistente):
    return "conjuntos:asistente-reglas" if en_asistente else "reglas:lista"


@require_http_methods(["GET", "POST"])
def nueva(request, en_asistente=False):
    """Paso 1: el área y el tipo. Lleva al formulario del tipo."""
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    areas, error = cargar_areas(request)
    areas = [area for area in areas if area["activo"]]
    formulario = ElegirTipoForm(request.POST or None, areas=areas)
    if request.method == "POST" and formulario.is_valid():
        destino = "conjuntos:asistente-reglas-tipo" if en_asistente else "reglas:nueva-tipo"
        url = reverse(destino, kwargs={"tipo": formulario.cleaned_data["tipo"]})
        return redirect(f"{url}?area={formulario.cleaned_data['area']}")
    contexto = {"formulario": formulario, "error": error, "en_asistente": en_asistente, "paso": 4}
    if en_asistente:
        contexto["reglas"], contexto["error"] = cargar_reglas(request)
    return render(request, "reglas/nueva.html", contexto)


@require_http_methods(["GET", "POST"])
def nueva_tipo(request, tipo, en_asistente=False):
    """Paso 2: los parámetros del tipo y desde cuándo rige."""
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    if tipo not in FORMULARIO_POR_TIPO:
        raise Http404
    area_id = request.POST.get("area") or request.GET.get("area")
    formulario = FORMULARIO_POR_TIPO[tipo](request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        datos = {
            "area": area_id,
            "tipo": tipo,
            "parametros": formulario.parametros(),
            "vigencia_desde": formulario.cleaned_data["vigencia_desde"].isoformat(),
        }
        try:
            api_reglas.crear(request, datos)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(a_donde_volver(en_asistente))
    contexto = {
        "formulario": formulario,
        "tipo_nombre": dict(TIPOS_DE_REGLA)[tipo],
        "area_id": area_id,
        "en_asistente": en_asistente,
        "paso": 4,
    }
    return render(request, "reglas/parametros.html", contexto)


@require_http_methods(["GET", "POST"])
def editar(request, regla_id):
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    try:
        regla = con_fechas(api_reglas.obtener(request, regla_id))
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    clase = FORMULARIO_POR_TIPO[regla["tipo"]]
    formulario = clase(request.POST or None, initial=iniciales(regla["tipo"], regla["parametros"]), con_vigencia=False)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_reglas.editar(request, regla_id, formulario.parametros())
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("reglas:lista")
    contexto = {"formulario": formulario, "regla": regla, "tipo_nombre": regla["tipo_nombre"], "aviso": AVISO_DE_VERSION}
    return render(request, "reglas/parametros.html", contexto)


@require_POST
def retirar(request, regla_id):
    try:
        api_reglas.retirar(request, regla_id)
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    return redirect("reglas:lista")
