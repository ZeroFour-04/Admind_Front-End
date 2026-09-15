"""Ayudante común para hablar con la API: dirección, identidad y traducción de errores."""
import requests
from django.conf import settings

# Dónde guarda la sesión de este servidor el token que entregó la API al iniciar sesión.
CLAVE_TOKEN = "token_api"

MENSAJE_API_NO_DISPONIBLE = (
    "No hay conexión con el servidor de AdMind. Revisa que esté encendido e intenta de nuevo."
)
MENSAJES_POR_ESTADO = {
    401: "Tu sesión terminó. Inicia sesión de nuevo.",
    403: "No tienes permiso para hacer esto en el conjunto activo.",
    # Sin más detalle: un 404 no confirma si el recurso existe en otro conjunto (maestro §5.4).
    404: "No encontrado.",
}
MENSAJE_ERROR_GENERAL = "El servidor de AdMind no pudo atender la petición. Intenta de nuevo en unos minutos."


class ApiNoDisponible(Exception):
    """La API no respondió: está apagada, la dirección está mal o se agotó el tiempo."""


class ErrorDeApi(Exception):
    """La API respondió con un error. Trae el texto para mostrar y, si los hay, los errores por campo."""

    def __init__(self, estado, cuerpo):
        super().__init__(estado)
        self.estado = estado
        self.mensaje = MENSAJES_POR_ESTADO.get(estado, MENSAJE_ERROR_GENERAL)
        self.campos = {}

        if not isinstance(cuerpo, dict):
            return
        if estado == 400:
            # DRF responde {"campo": ["mensaje", ...]} cuando la entrada no tiene la forma correcta.
            self.campos = {campo: mensajes for campo, mensajes in cuerpo.items() if campo != "non_field_errors"}
            if "non_field_errors" in cuerpo:
                self.mensaje = " ".join(cuerpo["non_field_errors"])
        elif estado == 401 and "detail" in cuerpo:
            # El login responde aquí su mensaje genérico, que no revela si el correo existe (HU-01).
            self.mensaje = cuerpo["detail"]


class NoAutenticado(ErrorDeApi):
    """401: credenciales inválidas al entrar, o token vencido después."""


def token_de(request):
    return request.session.get(CLAVE_TOKEN)


def pedir(request, metodo, ruta, datos=None):
    """Llama a la API en nombre del usuario de `request` y devuelve el JSON de la respuesta."""
    cabeceras = {"Accept": "application/json"}
    token = token_de(request)
    if token:
        cabeceras["Authorization"] = f"Token {token}"

    try:
        respuesta = requests.request(
            metodo,
            f"{settings.ADMIND_API_URL}/{ruta}",
            json=datos,
            headers=cabeceras,
            timeout=settings.ADMIND_API_TIEMPO_ESPERA,
        )
    except requests.RequestException as error:
        raise ApiNoDisponible() from error

    try:
        cuerpo = respuesta.json() if respuesta.content else None
    except ValueError:
        cuerpo = None

    if respuesta.status_code == 401:
        raise NoAutenticado(401, cuerpo)
    if respuesta.status_code >= 400:
        raise ErrorDeApi(respuesta.status_code, cuerpo)
    return cuerpo
