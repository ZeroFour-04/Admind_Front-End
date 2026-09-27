"""Apartamentos del conjunto activo y sus vínculos (HU-08): propietarios, arrendatarios y su histórico."""
from datetime import date

from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import cuentas as api_cuentas
from cliente_api import unidades as api_unidades
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import CerrarVinculoForm, UnidadForm, VinculoForm


def con_fechas(vinculo):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    fechas = {
        campo: date.fromisoformat(vinculo[campo]) for campo in ("vigencia_desde", "vigencia_hasta") if vinculo.get(campo)
    }
    return {**vinculo, **fechas}


@require_http_methods(["GET", "POST"])
def lista(request):
    puede_gestionar = tiene_permiso(request, "vinculo.gestionar")
    formulario = UnidadForm(request.POST or None)
    if request.method == "POST" and puede_gestionar and formulario.is_valid():
        try:
            unidad = api_unidades.crear(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("unidades:detalle", unidad_id=unidad["id"])

    try:
        unidades, error = api_unidades.listar(request), None
    except ApiNoDisponible:
        unidades, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        unidades, error = [], api_error.mensaje
    contexto = {"unidades": unidades, "error": error, "formulario": formulario, "puede_gestionar": puede_gestionar}
    return render(request, "unidades/lista.html", contexto)


def personas_del_conjunto(request):
    """[(persona_id, nombre)] de las cuentas con rol en el conjunto activo."""
    try:
        usuarios = api_cuentas.listar_usuarios(request)
    except (ApiNoDisponible, ErrorDeApi):
        return []
    return [(usuario["persona"], usuario["nombre"]) for usuario in usuarios]


@require_http_methods(["GET", "POST"])
def detalle(request, unidad_id):
    if not tiene_permiso(request, "vinculo.gestionar"):
        return redirect("unidades:lista")
    formulario = VinculoForm(request.POST or None, personas=personas_del_conjunto(request))
    if request.method == "POST" and formulario.is_valid():
        try:
            api_unidades.registrar_vinculo(request, unidad_id, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("unidades:detalle", unidad_id=unidad_id)
    return pantalla_de_detalle(request, unidad_id, formulario)


def pantalla_de_detalle(request, unidad_id, formulario, error_de_accion=None):
    try:
        unidad, error = api_unidades.obtener(request, unidad_id), None
    except ApiNoDisponible:
        unidad, error = None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        unidad, error = None, api_error.mensaje
    if unidad:
        unidad = {
            **unidad,
            "vigentes": [con_fechas(v) for v in unidad["vigentes"]],
            "historicos": [con_fechas(v) for v in unidad["historicos"]],
        }
    contexto = {
        "unidad": unidad,
        "error": error_de_accion or error,
        "formulario": formulario,
        "cierre": CerrarVinculoForm(),
    }
    return render(request, "unidades/detalle.html", contexto)


@require_POST
def cerrar_vinculo(request, unidad_id, vinculo_id):
    cierre = CerrarVinculoForm(request.POST)
    formulario = VinculoForm(personas=personas_del_conjunto(request))
    if not cierre.is_valid():
        return pantalla_de_detalle(request, unidad_id, formulario, "Escribe una fecha válida para cerrar el vínculo.")
    try:
        api_unidades.cerrar_vinculo(request, unidad_id, vinculo_id, cierre.datos_para_api())
    except ApiNoDisponible:
        return pantalla_de_detalle(request, unidad_id, formulario, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        mensaje = " ".join(sum(error.campos.values(), [])) or error.mensaje
        return pantalla_de_detalle(request, unidad_id, formulario, mensaje)
    return redirect("unidades:detalle", unidad_id=unidad_id)
