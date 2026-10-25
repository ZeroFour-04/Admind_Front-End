"""Endpoints de `Admind_Backend/apps/parqueaderos/`: el catálogo del conjunto activo (HU-28) y su asignación (HU-34)."""
from urllib.parse import urlencode

from cliente_api.http import pedir


def listar(request, tipo=None, libres=False):
    """GET /parqueaderos/[?tipo=&libres=1] → [{id, codigo, tipo, vehiculo, accesible, notas, ocupado, asignado_a}], por código.

    Solo los activos. `tipo` es `visitantes` o `residentes`; con `libres` no vienen los ocupados por una visita.
    `ocupado` dice si lo está, no por quién. `asignado_a` es la vivienda de un puesto de residentes, o null si está sin asignar.
    """
    consulta = {}
    if tipo:
        consulta["tipo"] = tipo
    if libres:
        consulta["libres"] = "1"
    ruta = "parqueaderos/" + (f"?{urlencode(consulta)}" if consulta else "")
    return pedir(request, "GET", ruta)


def crear(request, datos):
    """POST /parqueaderos/ {codigo, tipo, vehiculo, accesible, notas} → el parqueadero creado, o 400 bajo `codigo` si ya existe."""
    return pedir(request, "POST", "parqueaderos/", datos)


def desactivar(request, parqueadero_id):
    """POST /parqueaderos/<id>/desactivar/ → el parqueadero retirado. 409 si una visita sin salida lo ocupa o si está asignado a una vivienda."""
    return pedir(request, "POST", f"parqueaderos/{parqueadero_id}/desactivar/")


def asignar(request, parqueadero_id, unidad_id):
    """POST /parqueaderos/<id>/asignacion/ {unidad} → la asignación, con `reasignada` si cerró la anterior.

    201 si estaba libre, 200 si lo reasigna. 404 si no es de residentes, 400 bajo `unidad` si la vivienda no existe,
    409 si ya es de esa vivienda o si la vivienda llegó al tope por vehículo que fijó el conjunto.
    """
    return pedir(request, "POST", f"parqueaderos/{parqueadero_id}/asignacion/", {"unidad": str(unidad_id)})


def liberar(request, parqueadero_id):
    """POST /parqueaderos/<id>/liberacion/ → la asignación cerrada hoy. 409 si ya estaba sin asignar."""
    return pedir(request, "POST", f"parqueaderos/{parqueadero_id}/liberacion/")


def historial(request, parqueadero_id):
    """GET /parqueaderos/<id>/asignaciones/ → [{id, vivienda, vigencia_desde, vigencia_hasta, registrado_por, cerrado_por}].

    Del más reciente al más viejo. `vigencia_hasta` y `cerrado_por` son null en la que sigue vigente.
    """
    return pedir(request, "GET", f"parqueaderos/{parqueadero_id}/asignaciones/")


def mios(request):
    """GET /parqueaderos/mios/ → [{id, codigo, vehiculo, accesible, notas, vivienda, desde}] de las viviendas de quien pregunta.

    No pide permiso: cada persona ve solo los puestos vigentes de sus propios vínculos.
    """
    return pedir(request, "GET", "parqueaderos/mios/")
