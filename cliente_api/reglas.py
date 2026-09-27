"""Endpoints de `Admind_Backend/apps/reglas/`: las reglas beta de reserva del conjunto activo (HU-10)."""
from cliente_api.http import pedir


def listar(request):
    """GET /reglas/ → las reglas vigentes y las que empiezan después, con su descripción en palabras."""
    return pedir(request, "GET", "reglas/")


def crear(request, datos):
    """POST /reglas/ → la regla creada. Exige área, tipo, parámetros y vigencia."""
    return pedir(request, "POST", "reglas/", datos)


def obtener(request, regla_id):
    """GET /reglas/<id>/ → una regla del conjunto activo, o 404."""
    return pedir(request, "GET", f"reglas/{regla_id}/")


def editar(request, regla_id, parametros):
    """PATCH /reglas/<id>/ → la versión nueva. La anterior queda cerrada en el historial."""
    return pedir(request, "PATCH", f"reglas/{regla_id}/", {"parametros": parametros})


def retirar(request, regla_id):
    """POST /reglas/<id>/retirar/ → la regla con su vigencia cerrada hoy."""
    return pedir(request, "POST", f"reglas/{regla_id}/retirar/")
