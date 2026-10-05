"""Catálogo de áreas comunes del conjunto activo (HU-09): listar, crear, editar y desactivar."""
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import areas as api_areas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AreaForm, EditarAreaForm


def cargar_areas(request):
    """Las áreas del conjunto activo, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_areas.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def crear_desde(request, formulario):
    """Manda el formulario a la API. Devuelve True si el área quedó creada."""
    try:
        api_areas.crear(request, formulario.datos_para_api())
    except ApiNoDisponible:
        formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        errores_de_la_api_al_formulario(formulario, error)
    else:
        return True
    return False


def lista(request, error_de_accion=None):
    areas, error = cargar_areas(request)
    contexto = {
        "areas": areas,
        "error": error_de_accion or error,
        "puede_gestionar": tiene_permiso(request, "area.gestionar"),
        "creada": request.GET.get("creada") == "1",
    }
    return render(request, "areas/lista.html", contexto)


@require_http_methods(["GET", "POST"])
def nueva(request):
    if not tiene_permiso(request, "area.gestionar"):
        return redirect("areas:lista")
    formulario = AreaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid() and crear_desde(request, formulario):
        return redirect(f"{reverse('areas:lista')}?creada=1")
    return render(request, "areas/nueva.html", {"formulario": formulario})


@require_http_methods(["GET", "POST"])
def editar(request, area_id):
    if not tiene_permiso(request, "area.gestionar"):
        return redirect("areas:lista")
    try:
        area = api_areas.obtener(request, area_id)
    except ApiNoDisponible:
        return render(request, "areas/editar.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as error:
        return render(request, "areas/editar.html", {"error": error.mensaje})

    campos = ("nombre", "descripcion", "hora_apertura", "hora_cierre", "duracion_franja_minutos", "en_mantenimiento")
    formulario = EditarAreaForm(request.POST or None, initial={campo: area[campo] for campo in campos})
    if request.method == "POST" and formulario.is_valid():
        try:
            api_areas.editar(request, area_id, formulario.datos_para_api())
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("areas:lista")
    return render(request, "areas/editar.html", {"area": area, "formulario": formulario})


@require_POST
def desactivar(request, area_id):
    try:
        api_areas.desactivar(request, area_id)
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    return redirect("areas:lista")
