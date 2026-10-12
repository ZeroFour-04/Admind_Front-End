"""Endpoints de `Admind_Backend/apps/casos/`: casos propios y sus imágenes."""
from cliente_api.http import pedir, pedir_archivo


def listar(request):
    """GET /casos/ → los casos propios o todos los del conjunto, según permisos."""
    return pedir(request, "GET", "casos/")


def crear(request, datos, foto=None):
    """POST /casos/ → un caso y su imagen opcional."""
    archivos = {"foto": (foto.name, foto.read(), foto.content_type)} if foto else None
    return pedir(request, "POST", "casos/", datos, archivos=archivos)


def gestionar(request, caso_id, accion, datos=None):
    """POST /casos/<id>/<accion>/ → rechaza o redirige un caso pendiente."""
    return pedir(request, "POST", f"casos/{caso_id}/{accion}/", datos or {})


def foto(request, caso_id, foto_id):
    """GET /casos/<id>/fotos/<foto_id>/ → imagen visible para quien puede consultar el caso."""
    return pedir_archivo(request, f"casos/{caso_id}/fotos/{foto_id}/")
