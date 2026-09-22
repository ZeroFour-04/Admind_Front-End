"""Endpoints de `Admind_Backend/apps/conjuntos/`: el asistente de creación (HU-03)."""
from cliente_api.http import pedir


def crear(request, datos):
    """POST /conjuntos/ → {conjunto, ...estado de la sesión}. El conjunto nuevo queda como activo."""
    return pedir(request, "POST", "conjuntos/", datos)


def resumen(request):
    """GET /conjuntos/actual/ → {conjunto, administradores, requisitos, puede_activar} del conjunto activo."""
    return pedir(request, "GET", "conjuntos/actual/")


def editar(request, datos):
    """PATCH /conjuntos/actual/ → el resumen actualizado."""
    return pedir(request, "PATCH", "conjuntos/actual/", datos)


def activar(request):
    """POST /conjuntos/actual/activar/ → el resumen, o 400 con los requisitos que faltan."""
    return pedir(request, "POST", "conjuntos/actual/activar/")
