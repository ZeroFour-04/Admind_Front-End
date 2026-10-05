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


def enviar(request, solicitud_id, datos):
    """POST /reservas/solicitudes/<id>/enviar/ → la solicitud APARTADA, o 400 con todos los `motivos` (la franja queda libre)."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/enviar/", datos)


def mis_solicitudes(request):
    """GET /reservas/solicitudes/ → las solicitudes propias, la más reciente primero."""
    return pedir(request, "GET", "reservas/solicitudes/")


def solicitudes_del_area(request, area_id):
    """GET /reservas/areas/<id>/solicitudes/ → solicitudes enviadas de una zona e historial de decisiones."""
    return pedir(request, "GET", f"reservas/areas/{area_id}/solicitudes/")


def solicitudes_para_bandeja(request):
    """GET /reservas/bandeja/ → reservas enviadas, aceptadas o rechazadas del conjunto activo."""
    return pedir(request, "GET", "reservas/bandeja/")


def decidir(request, solicitud_id, datos):
    """POST /reservas/solicitudes/<id>/decision/ → acepta o rechaza una solicitud con motivo."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/decision/", datos)
