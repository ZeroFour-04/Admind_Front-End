"""Endpoints de `Admind_Backend/apps/ingresos/`: el ingreso a zonas con aforo del conjunto activo."""
from urllib.parse import urlencode

from cliente_api.http import pedir


def zonas(request):
    """GET /ingresos/zonas/ → por cada zona con ingreso: el área, cuántos hay adentro, los cupos y si abre ahora."""
    return pedir(request, "GET", "ingresos/zonas/")


def buscar_residente(request, numero_documento):
    """POST /ingresos/residentes/buscar/ → quienes viven en el conjunto con ese documento. 404 si no hay ninguno."""
    return pedir(request, "POST", "ingresos/residentes/buscar/", {"numero_documento": numero_documento})


def registrar(request, datos):
    """POST /ingresos/ → el ingreso. 400 con `motivos` si no cumple las reglas."""
    return pedir(request, "POST", "ingresos/", datos)


def listar(request, area=None, fecha=None):
    """GET /ingresos/ → `adentro` y `vencidos_hoy` (ingreso.registrar) y `historial` (ingreso.ver_historico)."""
    filtros = {nombre: valor for nombre, valor in (("area", area), ("fecha", fecha)) if valor}
    return pedir(request, "GET", f"ingresos/?{urlencode(filtros)}" if filtros else "ingresos/")


def registrar_salida(request, ingreso_id):
    """POST /ingresos/<id>/salida/ → el ingreso con su salida. 409 si ya había salido."""
    return pedir(request, "POST", f"ingresos/{ingreso_id}/salida/")
