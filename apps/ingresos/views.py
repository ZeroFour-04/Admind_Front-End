"""Ingreso a zonas con aforo: la pantalla de Vigilancia y el historial de Administración.

Quién puede entrar, cuántos caben y cuándo se cumple el tiempo lo decide la API; aquí solo se muestra y se
pide. Las pantallas deciden qué mostrar con el permiso, no con el nombre del rol. Registrar es en dos pasos
y sin JavaScript: buscar (documento y acompañantes) y confirmar (nombre y vivienda a la vista).
"""
from datetime import datetime

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.reservas.views import fila_de_zona
from cliente_api import ingresos as api_ingresos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import BuscarResidenteForm, ConfirmarIngresoForm, FiltroDeHistorialForm

# Ley 1581: el texto lo da la verificación legal (abiertas 12.10 b). Mientras no llegue, la pantalla lo dice y no lo inventa.
AVISO_DE_FINALIDAD = "Aviso de finalidad pendiente de la verificación legal."

# Cómo se ve el estado de un ingreso: siempre con texto, nunca solo con color.
PASTILLA_POR_ESTADO = {
    "ADENTRO": "am-pastilla--info",
    "SALIO": "am-pastilla--neutro",
    "VENCIDO": "am-pastilla--tramite",
}


def con_horas(ingreso):
    """La API manda las horas como texto ISO; las plantillas las formatean como hora."""
    horas = {
        campo: datetime.fromisoformat(ingreso[campo]) if ingreso[campo] else None
        for campo in ("entrada_en", "salida_prevista_en", "salida_en")
    }
    return {**ingreso, **horas, "clase": PASTILLA_POR_ESTADO[ingreso["estado"]]}


def cargar_zonas(request):
    """Las zonas con ingreso y sus cupos, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_ingresos.zonas(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def cargar_listas(request, filtro):
    """Quién está adentro y a quién se le cumplió el tiempo (registra) y el historial (ver_historico)."""
    try:
        area = filtro.cleaned_data.get("area") if filtro.is_bound and filtro.is_valid() else None
        fecha = filtro.cleaned_data.get("fecha") if filtro.is_bound and filtro.is_valid() else None
        listas = api_ingresos.listar(request, area, fecha.isoformat() if fecha else None)
    except ApiNoDisponible:
        return {}, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return {}, error.mensaje
    return {clave: [con_horas(ingreso) for ingreso in ingresos] for clave, ingresos in listas.items()}, None


def pantalla(request, formulario=None, residentes=None, motivos=None, error=None, exito=None):
    registra = tiene_permiso(request, "ingreso.registrar")
    historico = tiene_permiso(request, "ingreso.ver_historico")
    zonas, error_de_zonas = cargar_zonas(request)
    filtro = FiltroDeHistorialForm(request.GET or None, zonas=zonas)
    listas, error_de_listas = cargar_listas(request, filtro)
    if formulario is None and registra:
        formulario = BuscarResidenteForm(zonas=zonas)
    return render(request, "ingresos/lista.html", {
        "registra": registra,
        "historico": historico,
        "cupos": [fila_de_zona(zona["area"], {zona["area"]["id"]: zona}) for zona in zonas],
        "formulario": formulario,
        "residentes": residentes,
        "motivos": motivos,
        "filtro": filtro,
        "adentro": listas.get("adentro", []),
        "vencidos_hoy": listas.get("vencidos_hoy", []),
        "historial": listas.get("historial", []),
        "aviso_de_finalidad": AVISO_DE_FINALIDAD,
        "error": error or error_de_zonas or error_de_listas,
        "exito": exito,
    })


def lista(request):
    if not (tiene_permiso(request, "ingreso.registrar") or tiene_permiso(request, "ingreso.ver_historico")):
        return redirect("paneles:inicio")
    exito = {"registrado": "Ingreso registrado.", "salio": "Salida registrada."}.get(request.GET.get("hecho"))
    return pantalla(request, exito=exito)


def buscar(request, formulario):
    """Los residentes con ese documento, o None si no hay ninguno (el error queda en el formulario)."""
    try:
        return api_ingresos.buscar_residente(request, formulario.cleaned_data["numero_documento"])
    except ApiNoDisponible:
        formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        if error.estado == 404:
            formulario.add_error("numero_documento", "No encontrado: ese documento no es de un residente del conjunto.")
        else:
            formulario.add_error(None, error.mensaje)
    return None


@require_http_methods(["POST"])
def registrar(request):
    """Paso 1 (`paso=buscar`): busca al residente. Paso 2 (`paso=registrar`): lo registra con la vivienda elegida."""
    if not tiene_permiso(request, "ingreso.registrar"):
        return redirect("paneles:inicio")
    zonas, error_de_zonas = cargar_zonas(request)
    if request.POST.get("paso") != "registrar":
        formulario = BuscarResidenteForm(request.POST, zonas=zonas)
        residentes = buscar(request, formulario) if formulario.is_valid() else None
        if residentes is None:
            return pantalla(request, formulario, error=error_de_zonas)
        confirmar = ConfirmarIngresoForm(
            initial={**formulario.cleaned_data, "residente": _unica_opcion(residentes)}, zonas=zonas, residentes=residentes
        )
        return pantalla(request, confirmar, residentes)

    # Se vuelve a buscar con el documento que sigue en el formulario: la API decide quién vive en el conjunto.
    primero = BuscarResidenteForm(request.POST, zonas=zonas)
    residentes = buscar(request, primero) if primero.is_valid() else None
    if residentes is None:
        return pantalla(request, primero, error=error_de_zonas)
    formulario = ConfirmarIngresoForm(request.POST, zonas=zonas, residentes=residentes)
    if not formulario.is_valid():
        return pantalla(request, formulario, residentes)
    persona, vivienda = formulario.persona_y_vivienda()
    datos = {
        "area": formulario.cleaned_data["area"],
        "persona": persona,
        "unidad": vivienda,
        "acompanantes": formulario.cleaned_data["acompanantes"],
    }
    try:
        api_ingresos.registrar(request, datos)
    except ApiNoDisponible:
        formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        motivos = error.cuerpo.get("motivos") if error.estado == 400 else None
        if not motivos:
            formulario.add_error(None, error.mensaje)
        else:
            return pantalla(request, formulario, residentes, motivos=motivos)
    else:
        return redirect(f"{reverse('ingresos:lista')}?hecho=registrado")
    return pantalla(request, formulario, residentes)


def _unica_opcion(residentes):
    """Con una sola vivienda posible, ya viene elegida; con varias, la elige quien registra."""
    opciones = [f"{r['persona']}:{u['id']}" for r in residentes for u in r["unidades"]]
    return opciones[0] if len(opciones) == 1 else None


@require_POST
def salida(request, ingreso_id):
    if not tiene_permiso(request, "ingreso.registrar"):
        return redirect("paneles:inicio")
    try:
        api_ingresos.registrar_salida(request, ingreso_id)
    except ApiNoDisponible:
        return pantalla(request, error=MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla(request, error=error.mensaje)
    return redirect(f"{reverse('ingresos:lista')}?hecho=salio")
