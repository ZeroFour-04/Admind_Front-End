"""La sesión de este servidor web y el token de la API que guarda adentro."""
from datetime import datetime

from django.shortcuts import redirect

from cliente_api.http import CLAVE_TOKEN, token_de


def publica(vista):
    """Marca una vista que se puede abrir sin haber iniciado sesión."""
    vista.publica = True
    return vista


def abrir_sesion(request, datos_de_ingreso):
    """Guarda el token que entregó la API y hace vencer la sesión a la misma hora que él."""
    # Id de sesión nuevo al entrar: una cookie de sesión anterior al ingreso no sirve después.
    request.session.cycle_key()
    request.session[CLAVE_TOKEN] = datos_de_ingreso["token"]
    request.session.set_expiry(datetime.fromisoformat(datos_de_ingreso["vence_en"]))


def cerrar_sesion(request):
    request.session.flush()


class SesionRequeridaMiddleware:
    """Toda pantalla exige sesión, salvo las marcadas con @publica. Sin sesión, al ingreso."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, vista, args, kwargs):
        if getattr(vista, "publica", False) or token_de(request):
            return None
        return redirect("cuentas:ingreso")
