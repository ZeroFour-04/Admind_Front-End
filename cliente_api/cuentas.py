"""Endpoints de `Admind_Backend/apps/cuentas/`."""
from cliente_api.http import pedir


def iniciar_sesion(request, correo, contrasena):
    """POST /auth/login/ → {token, vence_en, conjunto_activo, permisos}."""
    return pedir(request, "POST", "auth/login/", {"correo": correo, "contrasena": contrasena})


def cerrar_sesion(request):
    """POST /auth/logout/ → 204. La API borra la sesión del token."""
    pedir(request, "POST", "auth/logout/")
