"""La sesión de este servidor web y lo que guarda adentro: el token de la API y el estado de la sesión."""
from datetime import datetime

from django.shortcuts import redirect

from cliente_api.http import CLAVE_TOKEN, token_de

CLAVE_CONJUNTO_ACTIVO = "conjunto_activo"
CLAVE_PERMISOS = "permisos"
CLAVE_ROLES = "roles"
CLAVE_DOS_FACTORES = "dos_factores"
CLAVE_TIPO_USUARIO = "tipo_usuario"


def publica(vista):
    """Marca una vista que se puede abrir sin haber iniciado sesión."""
    vista.publica = True
    return vista


def antes_del_segundo_factor(vista):
    """Marca una vista que se puede abrir con el segundo factor pendiente (HU-02)."""
    vista.antes_del_segundo_factor = True
    return vista


def abrir_sesion(request, datos_de_ingreso):
    """Guarda el token que entregó la API y hace vencer la sesión a la misma hora que él."""
    # Id de sesión nuevo al entrar: una cookie de sesión anterior al ingreso no sirve después.
    request.session.cycle_key()
    request.session[CLAVE_TOKEN] = datos_de_ingreso["token"]
    guardar_estado(request, datos_de_ingreso)
    request.session.set_expiry(datetime.fromisoformat(datos_de_ingreso["vence_en"]))


def cerrar_sesion(request):
    request.session.flush()


def guardar_estado(request, estado):
    """Copia el estado de la sesión que devuelve la API: conjunto activo, permisos y segundo factor.

    La API sigue siendo quien decide en cada petición; esto solo le sirve a las pantallas para
    saber qué mostrar.
    """
    for clave in (CLAVE_CONJUNTO_ACTIVO, CLAVE_PERMISOS, CLAVE_ROLES, CLAVE_TIPO_USUARIO, CLAVE_DOS_FACTORES):
        if clave in estado:
            request.session[clave] = estado[clave]
    request.session.modified = True


def tiene_permiso(request, permiso):
    return permiso in request.session.get(CLAVE_PERMISOS, [])


def segundo_factor_pendiente(request):
    estado = request.session.get(CLAVE_DOS_FACTORES) or {}
    return bool(estado.get("requerido")) and not estado.get("verificado")


def destino_despues_de_entrar(request):
    """A dónde va quien acaba de entrar o de verificar el segundo factor."""
    if segundo_factor_pendiente(request):
        configurado = (request.session.get(CLAVE_DOS_FACTORES) or {}).get("configurado")
        return redirect("cuentas:verificar-segundo-factor" if configurado else "cuentas:configurar-segundo-factor")
    # Con un solo conjunto la API ya lo eligió: entra directo, sin selector (HU-26).
    if request.session.get(CLAVE_CONJUNTO_ACTIVO):
        return redirect("paneles:inicio")
    return redirect("conjuntos:selector")


class SesionRequeridaMiddleware:
    """Toda pantalla exige sesión, salvo las marcadas con @publica. Sin sesión, al ingreso.

    Con el segundo factor pendiente, solo se abren las pantallas para completarlo.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, vista, args, kwargs):
        if getattr(vista, "publica", False):
            return None
        if not token_de(request):
            return redirect("cuentas:ingreso")
        if segundo_factor_pendiente(request) and not getattr(vista, "antes_del_segundo_factor", False):
            return destino_despues_de_entrar(request)
        return None
