"""Los errores de la API que ninguna vista atrapó, convertidos en una página con un mensaje claro.

Una vista que sabe qué hacer con un error de la API lo atrapa y muestra su propio aviso. Lo que se le
escapa llegaría al usuario como un 500 sin explicación; aquí se traduce:

- La API no responde: «El servidor no responde, intenta en un momento.»
- La sesión terminó (401): se cierra la sesión de este servidor y se vuelve al ingreso.
- Sin permiso (403) o no existe (404): la página de «No tienes acceso» o de «No encontramos esa página».
- Cualquier otro: el mensaje que ya trae el error.
"""
import logging

from django.shortcuts import redirect, render

from apps.cuentas.sesion import cerrar_sesion
from cliente_api.http import ApiNoDisponible, ErrorDeApi

logger = logging.getLogger(__name__)

MENSAJE_SIN_RESPUESTA = "El servidor no responde. Intenta de nuevo en un momento."
TITULOS = {
    403: "No tienes acceso a esta página",
    404: "No encontramos esa página",
}
TITULO_GENERAL = "No pudimos completar la acción"


def pagina_de_error(request, estado, titulo, mensaje):
    return render(request, "errores/_pagina.html", {"titulo": titulo, "mensaje": mensaje}, status=estado)


class ErroresDeApiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, excepcion):
        if isinstance(excepcion, ApiNoDisponible):
            logger.warning("La API no respondió: %s", request.path)
            return pagina_de_error(request, 503, "El servidor no responde", MENSAJE_SIN_RESPUESTA)
        if isinstance(excepcion, ErrorDeApi):
            if excepcion.estado == 401:
                cerrar_sesion(request)
                return redirect("cuentas:ingreso")
            estado = excepcion.estado if excepcion.estado in TITULOS else 500 if excepcion.estado >= 500 else 400
            logger.warning("Error %s de la API sin atrapar: %s", excepcion.estado, request.path)
            return pagina_de_error(request, estado, TITULOS.get(estado, TITULO_GENERAL), excepcion.mensaje)
        return None
