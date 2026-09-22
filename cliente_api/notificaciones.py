"""Endpoints de `Admind_Backend/apps/notificaciones/`."""
from cliente_api.http import pedir


def bandeja(request):
    """GET /notificaciones/ → los avisos de la persona en el conjunto activo, el más reciente primero."""
    return pedir(request, "GET", "notificaciones/")
