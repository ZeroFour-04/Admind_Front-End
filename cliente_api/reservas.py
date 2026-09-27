"""Endpoints de `Admind_Backend/apps/reservas/`: franjas y solicitudes de reserva (HU-11)."""
from urllib.parse import urlencode

from cliente_api.http import pedir


def franjas(request, area_id, fecha):
    """GET /reservas/franjas/?area=&fecha= → {area, fecha, franjas: [{hora_inicio, hora_fin, estado}]}."""
    return pedir(request, "GET", f"reservas/franjas/?{urlencode({'area': area_id, 'fecha': fecha})}")


def tomar(request, datos):
    """POST /reservas/solicitudes/ → la solicitud EN_SOLICITUD con 3 minutos. 409 si la franja o la persona ya están ocupadas."""
    return pedir(request, "POST", "reservas/solicitudes/", datos)


def obtener(request, solicitud_id):
    """GET /reservas/solicitudes/<id>/ → una solicitud propia, con segundos_restantes y unidades_para_solicitar."""
    return pedir(request, "GET", f"reservas/solicitudes/{solicitud_id}/")


def liberar(request, solicitud_id):
    """POST /reservas/solicitudes/<id>/liberar/ → la solicitud LIBERADA. 409 si ya no estaba en trámite."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/liberar/")


def mis_solicitudes(request):
    """GET /reservas/solicitudes/ → las solicitudes propias, la más reciente primero."""
    return pedir(request, "GET", "reservas/solicitudes/")
