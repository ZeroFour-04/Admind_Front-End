"""Registro de infracciones del conjunto activo (HU-30): lista, formulario, detalle, cierre y anulación.

El sistema no sanciona. El front muestra y manda: qué se puede hacer lo decide la API con el permiso, y aquí solo
se esconden los botones. No hay pantalla para sancionar, multar ni restringir, ni para borrar un registro.
"""
from datetime import date, datetime

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import casos as api_casos
from cliente_api import infracciones as api_infracciones
from cliente_api import unidades as api_unidades
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AnularForm, CerrarForm, RegistrarForm
from .textos import AVISO_DE_R11

TEXTO_DEL_AVISO = {
    "registrado": "Infracción registrada y comunicada a quienes tienen un vínculo con la vivienda.",
    "cerrado": "Registro cerrado: la comunicación original no cambió.",
    "anulado": "Registro anulado: sigue en la lista, tachado y con su motivo.",
}


def con_fechas(registro):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    fecha = {"fecha_hecho": date.fromisoformat(registro["fecha_hecho"])}
    momentos = {
        campo: datetime.fromisoformat(registro[campo])
        for campo in ("registrado_en", "fecha_notificacion", "cierre_fecha", "anulado_en")
        if registro.get(campo)
    }
    return {**registro, **fecha, **momentos}


def sin_permiso(request, permiso):
    return None if tiene_permiso(request, permiso) else redirect("paneles:inicio")


@require_GET
def lista(request):
    if (salida := sin_permiso(request, "infraccion.ver")) is not None:
        return salida
    try:
        registros, error = [con_fechas(r) for r in api_infracciones.listar(request)], None
    except ApiNoDisponible:
        registros, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        registros, error = [], falla.mensaje
    return render(request, "infracciones/lista.html", {
        "registros": registros,
        "error": error,
        "puede_registrar": tiene_permiso(request, "infraccion.registrar"),
        "aviso": TEXTO_DEL_AVISO.get(request.GET.get("hecho")),
        "aviso_de_r11": AVISO_DE_R11,
    })


def cargar_unidades(request):
    try:
        return api_unidades.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        return [], falla.mensaje


def viviendas_del_autor(request, caso_id, unidades):
    """Las viviendas del residente que abrió el caso, para sugerirlas. El caso no guarda la vivienda (P7)."""
    if not caso_id:
        return []
    try:
        caso = api_casos.obtener(request, caso_id)
    except (ApiNoDisponible, ErrorDeApi):
        return []
    nombres = {nombre.strip() for nombre in (caso.get("apartamento") or "").split(",") if nombre.strip()}
    return [unidad for unidad in unidades if unidad["nombre"] in nombres]


@require_http_methods(["GET", "POST"])
def nueva(request):
    if (salida := sin_permiso(request, "infraccion.registrar")) is not None:
        return salida
    caso_id = request.POST.get("caso") or request.GET.get("caso") or ""
    unidades, error = cargar_unidades(request)
    sugeridas = viviendas_del_autor(request, caso_id, unidades)
    if request.method == "POST":
        formulario = RegistrarForm(request.POST, unidades=unidades)
        if formulario.is_valid():
            try:
                api_infracciones.registrar(request, formulario.datos_para_api())
            except ApiNoDisponible:
                formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
            except ErrorDeApi as falla:
                errores_de_la_api_al_formulario(formulario, falla)
            else:
                return redirect(f"{reverse('infracciones:lista')}?hecho=registrado")
    else:
        formulario = RegistrarForm(unidades=unidades, sugeridas=sugeridas, initial={"caso": caso_id or None})
    return render(request, "infracciones/nueva.html", {
        "formulario": formulario,
        "error": error,
        "sugeridas": sugeridas,
        "nace_de_un_caso": bool(caso_id),
        "aviso_de_r11": AVISO_DE_R11,
    })


def pantalla_del_detalle(request, registro_id, formulario_de_cierre=None, formulario_de_anulacion=None, error=None):
    try:
        registro = con_fechas(api_infracciones.obtener(request, registro_id))
    except ApiNoDisponible:
        return render(request, "infracciones/detalle.html", {"error": MENSAJE_API_NO_DISPONIBLE, "aviso_de_r11": AVISO_DE_R11})
    except ErrorDeApi as falla:
        if falla.estado == 404:
            raise Http404
        return render(request, "infracciones/detalle.html", {"error": falla.mensaje, "aviso_de_r11": AVISO_DE_R11})
    puede_cerrar = tiene_permiso(request, "infraccion.cerrar") and registro["abierto"]
    puede_anular = tiene_permiso(request, "infraccion.anular") and not registro["anulado"]
    return render(request, "infracciones/detalle.html", {
        "registro": registro,
        "error": error,
        "formulario_de_cierre": (formulario_de_cierre or CerrarForm()) if puede_cerrar else None,
        "formulario_de_anulacion": (formulario_de_anulacion or AnularForm()) if puede_anular else None,
        "aviso_de_r11": AVISO_DE_R11,
    })


@require_GET
def detalle(request, registro_id):
    if (salida := sin_permiso(request, "infraccion.ver")) is not None:
        return salida
    return pantalla_del_detalle(request, registro_id)


@require_POST
def cerrar(request, registro_id):
    if (salida := sin_permiso(request, "infraccion.cerrar")) is not None:
        return salida
    formulario = CerrarForm(request.POST)
    if formulario.is_valid():
        try:
            api_infracciones.cerrar(request, registro_id, formulario.cleaned_data["comentario"])
        except ApiNoDisponible:
            return pantalla_del_detalle(request, registro_id, formulario, error=MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as falla:
            return pantalla_del_detalle(request, registro_id, formulario, error=falla.mensaje)
        return redirect(f"{reverse('infracciones:detalle', args=[registro_id])}?hecho=cerrado")
    return pantalla_del_detalle(request, registro_id, formulario)


@require_POST
def anular(request, registro_id):
    if (salida := sin_permiso(request, "infraccion.anular")) is not None:
        return salida
    formulario = AnularForm(request.POST)
    if formulario.is_valid():
        try:
            api_infracciones.anular(request, registro_id, formulario.cleaned_data["motivo"])
        except ApiNoDisponible:
            return pantalla_del_detalle(request, registro_id, formulario_de_anulacion=formulario, error=MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as falla:
            return pantalla_del_detalle(request, registro_id, formulario_de_anulacion=formulario, error=falla.mensaje)
        return redirect(f"{reverse('infracciones:detalle', args=[registro_id])}?hecho=anulado")
    return pantalla_del_detalle(request, registro_id, formulario_de_anulacion=formulario)
