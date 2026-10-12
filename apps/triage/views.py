from django.shortcuts import render

from apps.cuentas.sesion import tiene_permiso
from cliente_api import areas as api_areas
from cliente_api import reservas as api_reservas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

ESTADO_PARA_RESIDENTE = {
    "APARTADA": "En progreso",
    "RESERVADA": "Aceptado",
    "RECHAZADA": "Rechazado",
    "EN_SOLICITUD": "En progreso",
    "CANCELADA": "Cancelada",
    "EXPIRADA": "Expirada",
    "LIBERADA": "Liberada",
}


def bandeja(request):
    """Gestión elige una zona para revisar sus solicitudes; el residente ve su historial."""
    puede_ver_reservas = any(
        tiene_permiso(request, permiso)
        for permiso in ("reserva.ver_todas", "reserva.aprobar", "reserva.rechazar")
    )
    es_residente = not puede_ver_reservas and tiene_permiso(request, "reserva.solicitar")
    solicitudes, areas, error = [], [], None
    if puede_ver_reservas:
        try:
            areas = api_areas.listar(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
    elif es_residente:
        try:
            solicitudes = api_reservas.mis_solicitudes(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje

    solicitudes = [
        {
            **solicitud,
            "estado_visible": (
                ESTADO_PARA_RESIDENTE.get(solicitud["estado"], solicitud["estado_nombre"])
                if es_residente
                else solicitud["estado_nombre"]
            ),
        }
        for solicitud in solicitudes
    ]
    return render(request, "triage/bandeja.html", {
        "solicitudes": solicitudes,
        "areas": areas,
        "error": error,
        "puede_ver_reservas": puede_ver_reservas,
        "es_residente": es_residente,
    })
