"""Endpoints de `Admind_Backend/apps/parqueaderos/`: el catálogo de parqueaderos del conjunto activo (HU-28)."""
from urllib.parse import urlencode

from cliente_api.http import pedir


def listar(request, tipo=None, libres=False):
    """GET /parqueaderos/[?tipo=&libres=1] → [{id, codigo, tipo, accesible, notas, ocupado}], por código.

    Solo los activos. `tipo` es `visitantes` o `residentes`; con `libres` no vienen los ocupados por una visita.
    `ocupado` dice si lo está, no por quién.
    """
    consulta = {}
    if tipo:
        consulta["tipo"] = tipo
    if libres:
        consulta["libres"] = "1"
    ruta = "parqueaderos/" + (f"?{urlencode(consulta)}" if consulta else "")
    return pedir(request, "GET", ruta)


def crear(request, datos):
    """POST /parqueaderos/ {codigo, tipo, accesible, notas} → el parqueadero creado, o 400 bajo `codigo` si ya existe."""
    return pedir(request, "POST", "parqueaderos/", datos)


def desactivar(request, parqueadero_id):
    """POST /parqueaderos/<id>/desactivar/ → el parqueadero retirado. 409 si una visita sin salida lo ocupa."""
    return pedir(request, "POST", f"parqueaderos/{parqueadero_id}/desactivar/")
