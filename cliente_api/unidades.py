"""Endpoints de `Admind_Backend/apps/unidades/`."""
from cliente_api.http import pedir


def listar(request):
    """GET /unidades/ → [{id, nombre}] de las viviendas del conjunto activo."""
    return pedir(request, "GET", "unidades/")
