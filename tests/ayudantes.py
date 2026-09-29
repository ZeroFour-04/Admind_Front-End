"""Lo que comparten las pruebas de pantallas: un navegador con sesión abierta, sin API de verdad."""
from django.test import Client

TORRES = {"id": "5d6e1f7a-0000-4000-8000-000000000001", "nombre": "Torres del Río", "acento": "azul", "logo": None}
HUELLA = "a" * 64


def cliente_con_sesion(permisos=(), conjunto_activo=TORRES, tipo_usuario="Administrador", roles=None):
    """Como si hubiera iniciado sesión: token guardado, conjunto activo y permisos en la sesión."""
    cliente = Client()
    sesion = cliente.session
    sesion["token_api"] = "token-de-prueba"
    sesion["conjunto_activo"] = dict(conjunto_activo) if conjunto_activo else None
    sesion["permisos"] = list(permisos)
    sesion["roles"] = list(roles if roles is not None else [tipo_usuario])
    sesion["tipo_usuario"] = tipo_usuario
    sesion["dos_factores"] = {"requerido": False, "verificado": False, "configurado": False}
    sesion.save()
    return cliente
