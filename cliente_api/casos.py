"""Endpoints de `Admind_Backend/apps/casos/`: los casos, sus imágenes y el ciclo de cada uno (HU-29)."""
from urllib.parse import urlencode

from cliente_api.http import pedir, pedir_archivo


def listar(request, orden=None):
    """GET /casos/ → los casos propios, o todos los del conjunto para gestión.

    Para gestión vienen primero los abiertos, por prioridad y luego antigüedad; con
    `orden="antiguedad"` la prioridad no cuenta.
    """
    consulta = f"?{urlencode({'orden': orden})}" if orden else ""
    return pedir(request, "GET", f"casos/{consulta}")


def obtener(request, caso_id):
    """GET /casos/<id>/ → un caso. El de otra persona o de otro conjunto responde 404."""
    return pedir(request, "GET", f"casos/{caso_id}/")


def crear(request, datos, foto=None):
    """POST /casos/ → un caso y su imagen opcional."""
    archivos = {"foto": (foto.name, foto.read(), foto.content_type)} if foto else None
    return pedir(request, "POST", "casos/", datos, archivos=archivos)


def gestionar(request, caso_id, accion, datos=None):
    """POST /casos/<id>/<accion>/ → el caso después de la operación. 409 si su estado ya no la permite.

    `accion` es `tomar`, `prioridad`, `redirigir`, `descartar` (Secretaría), `responder` o `rechazar`
    (Administración).
    """
    return pedir(request, "POST", f"casos/{caso_id}/{accion}/", datos or {})


def foto(request, caso_id, foto_id):
    """GET /casos/<id>/fotos/<foto_id>/ → imagen visible para quien puede consultar el caso."""
    return pedir_archivo(request, f"casos/{caso_id}/fotos/{foto_id}/")
