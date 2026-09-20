"""Endpoints de `Admind_Backend/apps/cuentas/`."""
from cliente_api.http import pedir


def iniciar_sesion(request, correo, contrasena):
    """POST /auth/login/ → {token, vence_en, conjunto_activo, permisos}."""
    return pedir(request, "POST", "auth/login/", {"correo": correo, "contrasena": contrasena})


def cerrar_sesion(request):
    """POST /auth/logout/ → 204. La API borra la sesión del token."""
    pedir(request, "POST", "auth/logout/")


def crear_usuario(request, datos):
    """POST /auth/usuarios/ → crea la persona y su cuenta de acceso."""
    return pedir(request, "POST", "auth/usuarios/", datos)


def listar_usuarios(request):
    """GET /auth/usuarios/ → lista las cuentas del conjunto activo."""
    return pedir(request, "GET", "auth/usuarios/")


def obtener_usuario(request, usuario_id):
    """GET /auth/usuarios/<id>/ → datos completos de una cuenta."""
    return pedir(request, "GET", f"auth/usuarios/{usuario_id}/")


def listar_conjuntos(request):
    """GET /auth/conjuntos/ → conjuntos disponibles para el usuario."""
    return pedir(request, "GET", "auth/conjuntos/")


def crear_conjunto(request, datos):
    """POST /auth/conjuntos/ → crea un conjunto."""
    return pedir(request, "POST", "auth/conjuntos/", datos)


def elegir_conjunto(request, conjunto):
    """POST /auth/conjunto-activo/ → fija el conjunto activo del token."""
    return pedir(request, "POST", "auth/conjunto-activo/", {"conjunto": conjunto})
