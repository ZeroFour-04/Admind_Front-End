"""Endpoints de `Admind_Backend/apps/reglas/`: las reglas de reserva del conjunto activo, por niveles (HU-10)."""
from cliente_api.http import pedir


def catalogo(request):
    """GET /reglas/catalogo/ → los tipos que se pueden definir, con nivel, nombre y descripción."""
    return pedir(request, "GET", "reglas/catalogo/")


def listar(request):
    """GET /reglas/ → las reglas abiertas, del conjunto y de cada área, con su descripción en palabras."""
    return pedir(request, "GET", "reglas/")


def crear(request, datos):
    """POST /reglas/ → la regla creada. Exige tipo, parámetros y vigencia; el área, solo si la regla es de un área."""
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
