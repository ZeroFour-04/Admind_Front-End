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
    # Conflicto de estado: se muestra el `detail` de la API; esto es solo por si no lo trae.
    409: "No se pudo hacer porque el estado cambió. Recarga la página e intenta de nuevo.",
    429: "Hiciste demasiadas búsquedas. Espera un rato e intenta de nuevo.",
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
        self.cuerpo = cuerpo if isinstance(cuerpo, dict) else {}

        if not isinstance(cuerpo, dict):
            return
        if estado in (400, 409):
            # DRF responde {"campo": ["mensaje", ...]} cuando la entrada no tiene la forma correcta,
            # y {"detail": "..."} cuando el problema es de la operación y no de un campo.
            self.campos = {
                campo: mensajes
                for campo, mensajes in cuerpo.items()
                if campo not in ("non_field_errors", "detail") and isinstance(mensajes, list)
            }
            if "non_field_errors" in cuerpo:
                self.mensaje = " ".join(cuerpo["non_field_errors"])
            elif "detail" in cuerpo:
                self.mensaje = cuerpo["detail"]
        elif estado == 401 and "detail" in cuerpo:
            # El login responde aquí su mensaje genérico, que no revela si el correo existe (HU-01).
            self.mensaje = cuerpo["detail"]


class NoAutenticado(ErrorDeApi):
    """401: credenciales inválidas al entrar, o token vencido después."""


def token_de(request):
    return request.session.get(CLAVE_TOKEN)


def pedir(request, metodo, ruta, datos=None, archivos=None):
    """Llama a la API en nombre del usuario de `request` y devuelve el JSON de la respuesta.

    Con `archivos` ({campo: (nombre, contenido, tipo)}) la petición va como formulario multipart.
    """
    respuesta = enviar(request, metodo, ruta, {"Accept": "application/json"}, datos, archivos)
    return cuerpo_json(respuesta)


def pedir_archivo(request, ruta):
    """Descarga un archivo de la API (por ejemplo, el logo de un conjunto) y devuelve (contenido, tipo)."""
    respuesta = enviar(request, "GET", ruta, {}, None, None)
    if respuesta.status_code >= 400:
        cuerpo_json(respuesta)  # levanta el error que corresponde
    return respuesta.content, respuesta.headers.get("Content-Type", "")


def enviar(request, metodo, ruta, cabeceras, datos, archivos):
    token = token_de(request)
    if token:
        cabeceras["Authorization"] = f"Token {token}"
    cuerpo = {"data": datos, "files": archivos} if archivos else {"json": datos}
    try:
        return requests.request(
            metodo,
            f"{settings.ADMIND_API_URL}/{ruta}",
            headers=cabeceras,
            timeout=settings.ADMIND_API_TIEMPO_ESPERA,
            **cuerpo,
        )
    except requests.RequestException as error:
        raise ApiNoDisponible() from error


def cuerpo_json(respuesta):
    try:
        cuerpo = respuesta.json() if respuesta.content else None
    except ValueError:
        cuerpo = None

    if respuesta.status_code == 401:
        raise NoAutenticado(401, cuerpo)
    if respuesta.status_code >= 400:
        raise ErrorDeApi(respuesta.status_code, cuerpo)
    return cuerpo
