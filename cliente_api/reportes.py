"""Descargas de reportes del conjunto activo desde la API."""
from urllib.parse import urlencode

from cliente_api.http import pedir_archivo


def zonas(request, desde, hasta):
    consulta = urlencode({"desde": desde, "hasta": hasta})
    return pedir_archivo(request, f"api/reportes/zonas.pdf?{consulta}")


def pagos(request, periodo):
    consulta = urlencode({"periodo": periodo})
    return pedir_archivo(request, f"api/reportes/pagos.xlsx?{consulta}")
