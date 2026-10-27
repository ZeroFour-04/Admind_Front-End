from datetime import datetime

from django.shortcuts import render

from cliente_api import notificaciones as api_notificaciones
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi


def bandeja(request):
    """Los avisos de la persona en el conjunto activo. El correo sale del backend y no pasa por aquí."""
    try:
        avisos = api_notificaciones.bandeja(request)
    except ApiNoDisponible:
        avisos, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        avisos, error = [], api_error.mensaje
    else:
        error = None
    avisos = [{**aviso, "creada_en": datetime.fromisoformat(aviso["creada_en"])} for aviso in avisos]
    return render(request, "notificaciones/bandeja.html", {"avisos": avisos, "error": error})
