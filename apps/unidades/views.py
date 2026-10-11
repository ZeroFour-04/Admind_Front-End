"""Unidades del conjunto activo y sus vínculos (HU-08): propietarios, arrendatarios y su histórico."""
from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
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


PLURAL_DE_TIPO = {"apartamento": "apartamentos", "casa": "casas"}


def cargar_unidades(request):
    """(unidades, error): las viviendas del conjunto activo, o ([], el motivo) si la API no las entrega."""
    try:
        return api_unidades.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        return [], api_error.mensaje


def para_el_buscador(unidades, puede_gestionar):
    """Lo que el buscador de la página necesita de cada vivienda. Viaja como JSON, no se pinta fila por fila."""
    filas = []
    for unidad in unidades:
        agrupacion = unidad.get("agrupacion") or {}
        filas.append(
            {
                "id": unidad["id"],
                "nombre": unidad["nombre"],
                "agrupacion": agrupacion.get("nombre", ""),
                "tipo": unidad.get("tipo", "apartamento"),
                "numero": unidad.get("numero", ""),
                "vinculos": unidad.get("vinculos_vigentes", 0),
                "personas": unidad.get("personas", []),
                "url": reverse("unidades:detalle", args=[unidad["id"]]) if puede_gestionar else "",
            }
        )
    return filas


def recuadros_de_agrupaciones(unidades):
    """Un recuadro por agrupación, en el orden de la API, y «Sin agrupar» al final si hay viviendas sueltas."""
    recuadros = {}
    for unidad in unidades:
        agrupacion = unidad.get("agrupacion")
        clave = agrupacion["id"] if agrupacion else ""
        recuadro = recuadros.setdefault(
            clave,
            {
                "nombre": agrupacion["nombre"] if agrupacion else "Sin agrupar",
                "sin_agrupar": agrupacion is None,
                "url": reverse("unidades:agrupacion", args=[clave]) if agrupacion else reverse("unidades:sin-agrupar"),
                "total": 0,
                "sin_vinculos": 0,
                "tipos": set(),
            },
        )
        recuadro["total"] += 1
        recuadro["sin_vinculos"] += 0 if unidad.get("vinculos_vigentes") else 1
        recuadro["tipos"].add(unidad.get("tipo", "apartamento"))
    for recuadro in recuadros.values():
        tipos = recuadro.pop("tipos")
        recuadro["viviendas"] = PLURAL_DE_TIPO[tipos.pop()] if len(tipos) == 1 else "viviendas"
    return sorted(recuadros.values(), key=lambda recuadro: recuadro["sin_agrupar"])


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

    unidades, error = cargar_unidades(request)
    recuadros = recuadros_de_agrupaciones(unidades)
    contexto = {
        "unidades": para_el_buscador(unidades, puede_gestionar),
        "recuadros": recuadros,
        # Si ninguna vivienda tiene agrupación, un solo recuadro «Sin agrupar» no ayuda: va la tabla directa.
        "hay_agrupaciones": any(unidad.get("agrupacion") for unidad in unidades),
        "error": error,
        "formulario": formulario,
        "puede_gestionar": puede_gestionar,
    }
    return render(request, "unidades/lista.html", contexto)


def viviendas_de_agrupacion(request, agrupacion_id=None):
    """Las viviendas de una agrupación (o las que no tienen), con su buscador."""
    puede_gestionar = tiene_permiso(request, "vinculo.gestionar")
    unidades, error = cargar_unidades(request)
    buscada = str(agrupacion_id) if agrupacion_id else ""
    propias = [u for u in unidades if str((u.get("agrupacion") or {}).get("id", "")) == buscada]
    if not propias and not error:
        raise Http404
    if propias and buscada:
        nombre = propias[0]["agrupacion"]["nombre"]
    else:
        nombre = "Sin agrupar" if not agrupacion_id else "Unidades"
    contexto = {
        "nombre": nombre,
        "unidades": para_el_buscador(propias, puede_gestionar),
        "error": error,
        "puede_gestionar": puede_gestionar,
    }
    return render(request, "unidades/agrupacion.html", contexto)


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
