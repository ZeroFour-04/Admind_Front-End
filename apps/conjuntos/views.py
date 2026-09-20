from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from apps.cuentas.sesion import guardar_conjunto_activo
from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import ConjuntoForm


@require_http_methods(["GET", "POST"])
def selector(request):
    if request.method == "POST":
        try:
            datos = api_cuentas.elegir_conjunto(request, request.POST.get("conjunto"))
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
        else:
            guardar_conjunto_activo(request, datos.get("conjunto_activo"))
            return redirect("paneles:inicio")
    else:
        error = None

    try:
        conjuntos = api_cuentas.listar_conjuntos(request)
    except ApiNoDisponible:
        conjuntos = []
        error = error or MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        conjuntos = []
        error = error or api_error.mensaje
    return render(request, "conjuntos/selector.html", {"conjuntos": conjuntos or [], "error": error})


@require_http_methods(["GET", "POST"])
def nuevo(request):
    formulario = ConjuntoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_cuentas.crear_conjunto(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            for campo, mensajes in error.campos.items():
                formulario.add_error(campo if campo in formulario.fields else None, mensajes)
            if not error.campos:
                formulario.add_error(None, error.mensaje)
        else:
            return redirect("conjuntos:selector")
    return render(request, "conjuntos/nuevo.html", {"formulario": formulario})
