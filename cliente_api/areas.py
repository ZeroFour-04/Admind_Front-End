"""Endpoints de `Admind_Backend/apps/areas/`: el catálogo de áreas comunes del conjunto activo (HU-09)."""
from cliente_api.http import pedir


def listar(request):
    """GET /areas/ → las áreas del conjunto activo. Quien no gestiona solo recibe las activas."""
    return pedir(request, "GET", "areas/")


def crear(request, datos):
    """POST /areas/ → el área creada. La clasificación es obligatoria."""
    return pedir(request, "POST", "areas/", datos)


def obtener(request, area_id):
    """GET /areas/<id>/ → un área del conjunto activo, o 404."""
    return pedir(request, "GET", f"areas/{area_id}/")


def editar(request, area_id, datos):
    """PATCH /areas/<id>/ → el área con nombre, descripción, horario o mantenimiento nuevos."""
    return pedir(request, "PATCH", f"areas/{area_id}/", datos)


def desactivar(request, area_id):
    """POST /areas/<id>/desactivar/ → el área inactiva. No se borra."""
    return pedir(request, "POST", f"areas/{area_id}/desactivar/")
