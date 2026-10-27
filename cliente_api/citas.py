"""Endpoints de configuración de citas del backend."""
from urllib.parse import urlencode

from cliente_api.http import pedir


def horario(request):
    """GET /citas/horario/ → configuración semanal del conjunto activo."""
    return pedir(request, "GET", "citas/horario/")


def guardar_horario(request, datos):
    """PUT /citas/horario/ → guarda la configuración semanal completa."""
    return pedir(request, "PUT", "citas/horario/", datos)


def agenda(request, fecha=None):
    """GET /citas/agenda/ → horario semanal, cita propia y franjas disponibles de una fecha opcional."""
    consulta = f"?{urlencode({'fecha': fecha})}" if fecha else ""
    return pedir(request, "GET", f"citas/agenda/{consulta}")


def agendar(request, datos):
    """POST /citas/agenda/ → agenda una franja futura de dos horas."""
    return pedir(request, "POST", "citas/agenda/", datos)


def bandeja(request):
    """GET /citas/bandeja/ → citas del conjunto activo para Administración."""
    return pedir(request, "GET", "citas/bandeja/")
