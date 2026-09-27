"""Endpoints de `Admind_Backend/apps/cuentas/`."""
from cliente_api.http import pedir


def iniciar_sesion(request, correo, contrasena):
    """POST /auth/login/ → {token, vence_en, conjunto_activo, permisos, dos_factores}."""
    return pedir(request, "POST", "auth/login/", {"correo": correo, "contrasena": contrasena})


def cerrar_sesion(request):
    """POST /auth/logout/ → 204. La API borra la sesión del token."""
    pedir(request, "POST", "auth/logout/")


def crear_usuario(request, datos):
    """POST /auth/usuarios/ → crea la persona, su cuenta y su rol en el conjunto activo."""
    return pedir(request, "POST", "auth/usuarios/", datos)


def listar_usuarios(request):
    """GET /auth/usuarios/ → las cuentas con algún rol en el conjunto activo."""
    return pedir(request, "GET", "auth/usuarios/")


def obtener_usuario(request, usuario_id):
    """GET /auth/usuarios/<id>/ → datos completos de una cuenta del conjunto activo."""
    return pedir(request, "GET", f"auth/usuarios/{usuario_id}/")


def asignar_rol(request, usuario_id, rol):
    """POST /auth/usuarios/<id>/roles/ → el usuario con el rol nuevo. 409 si ya lo tiene (HU-06)."""
    return pedir(request, "POST", f"auth/usuarios/{usuario_id}/roles/", {"rol": rol})


def retirar_rol(request, usuario_id, asignacion_id):
    """POST /auth/usuarios/<id>/roles/<asignacion>/retirar/ → el usuario sin ese rol. 409 si es el último administrador."""
    return pedir(request, "POST", f"auth/usuarios/{usuario_id}/roles/{asignacion_id}/retirar/")


def listar_conjuntos(request):
    """GET /auth/conjuntos/ → conjuntos disponibles para el usuario."""
    return pedir(request, "GET", "auth/conjuntos/")


def elegir_conjunto(request, conjunto):
    """POST /auth/conjunto-activo/ → fija el conjunto activo del token y devuelve el estado de la sesión."""
    return pedir(request, "POST", "auth/conjunto-activo/", {"conjunto": conjunto})


# Recuperación de contraseña (HU-01). Sin sesión: se piden sin token.


def solicitar_recuperacion(request, correo):
    """POST /auth/recuperar/ → 202 exista o no la cuenta."""
    return pedir(request, "POST", "auth/recuperar/", {"correo": correo})


def restablecer_contrasena(request, uid, token, contrasena):
    """POST /auth/recuperar/confirmar/ → 204. Cierra las sesiones abiertas de esa cuenta."""
    return pedir(request, "POST", "auth/recuperar/confirmar/", {"uid": uid, "token": token, "contrasena": contrasena})


# Segundo factor (HU-02)


def configurar_dos_factores(request):
    """POST /auth/dos-factores/configurar/ → {qr, clave, enlace}."""
    return pedir(request, "POST", "auth/dos-factores/configurar/")


def activar_dos_factores(request, codigo):
    """POST /auth/dos-factores/activar/ → {codigos_de_respaldo, ...estado de la sesión}."""
    return pedir(request, "POST", "auth/dos-factores/activar/", {"codigo": codigo})


def verificar_dos_factores(request, codigo):
    """POST /auth/dos-factores/verificar/ → estado de la sesión."""
    return pedir(request, "POST", "auth/dos-factores/verificar/", {"codigo": codigo})
