"""Catálogo de parqueaderos del conjunto activo (HU-28): listar, crear y retirar.

El front no guarda nada: cada pantalla le pide a la API. Qué se puede hacer lo decide ella con el permiso.
"""
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import parqueaderos as api_parqueaderos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import ParqueaderoForm

TEXTO_DEL_AVISO = {"creado": "Parqueadero creado.", "retirado": "Parqueadero retirado."}


def cargar_parqueaderos(request):
    """Los parqueaderos activos del conjunto, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_parqueaderos.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def pantalla(request, formulario=None, error_de_accion=None):
    puede_gestionar = tiene_permiso(request, "parqueadero.gestionar")
    parqueaderos, error = cargar_parqueaderos(request)
    return render(request, "parqueaderos/lista.html", {
        "parqueaderos": parqueaderos,
        "error": error_de_accion or error,
        "puede_gestionar": puede_gestionar,
        "formulario": (formulario or ParqueaderoForm()) if puede_gestionar else None,
        "aviso": TEXTO_DEL_AVISO.get(request.GET.get("hecho")),
    })


@require_http_methods(["GET", "POST"])
def lista(request):
    puede_gestionar = tiene_permiso(request, "parqueadero.gestionar")
    if not puede_gestionar and not tiene_permiso(request, "parqueadero.ver"):
        return redirect("paneles:inicio")
    if request.method == "POST":
        if not puede_gestionar:
            return redirect("parqueaderos:lista")
        formulario = ParqueaderoForm(request.POST)
        if formulario.is_valid():
            try:
                api_parqueaderos.crear(request, formulario.datos_para_api())
            except ApiNoDisponible:
                formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
            except ErrorDeApi as error:
                errores_de_la_api_al_formulario(formulario, error)
            else:
                return redirect(f"{reverse('parqueaderos:lista')}?hecho=creado")
        return pantalla(request, formulario)
    return pantalla(request)


@require_POST
def desactivar(request, parqueadero_id):
    """«Confirmar retiro»: el 409 de «ocupado» se muestra arriba de la tabla, con el texto de la API."""
    try:
        api_parqueaderos.desactivar(request, parqueadero_id)
    except ApiNoDisponible:
        return pantalla(request, error_de_accion=MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla(request, error_de_accion=error.mensaje)
    return redirect(f"{reverse('parqueaderos:lista')}?hecho=retirado")
