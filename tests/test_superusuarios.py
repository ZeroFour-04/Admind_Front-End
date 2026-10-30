"""Pruebas de la creación de Superusuarios desde el selector (HU-06)."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion


def test_el_selector_muestra_crear_superusuario_solo_a_superusuarios():
    cliente_super = cliente_con_sesion(conjunto_activo=None, roles=["Superusuario"], tipo_usuario="Superusuario")
    with mock.patch("cliente_api.cuentas.listar_conjuntos", return_value=[]):
        respuesta_super = cliente_super.get("/conjuntos/")

    assert "Crear superusuario" in respuesta_super.content.decode()

    cliente_admin = cliente_con_sesion(conjunto_activo=None, roles=["Administrador"], tipo_usuario="Administrador")
    with mock.patch("cliente_api.cuentas.listar_conjuntos", return_value=[]):
        respuesta_admin = cliente_admin.get("/conjuntos/")

    assert "Crear superusuario" not in respuesta_admin.content.decode()


def test_administrador_abriendo_pantalla_superusuario_vuelve_al_selector():
    cliente = cliente_con_sesion(conjunto_activo=None, roles=["Administrador"], tipo_usuario="Administrador")
    respuesta = cliente.get("/conjuntos/superusuarios/nuevo/")

    assert respuesta.status_code == 302
    assert respuesta.url == "/conjuntos/"


def test_post_valido_llama_api_sin_rol_y_redirige_a_selector_con_aviso():
    cliente = cliente_con_sesion(conjunto_activo=None, roles=["Superusuario"], tipo_usuario="Superusuario")
    datos = {
        "tipo_documento": "CC",
        "numero_documento": "9876543210",
        "nombres": "Carlos",
        "apellidos": "Ruiz",
        "correo": "carlos@correo.com",
        "telefono": "3001234567",
        "contrasena": "una-clave-larga-2026",
        "confirmar_contrasena": "una-clave-larga-2026",
    }

    with mock.patch("cliente_api.cuentas.crear_superusuario", return_value={"id": "1", "correo": "carlos@correo.com"}) as mock_crear:
        respuesta = cliente.post("/conjuntos/superusuarios/nuevo/", datos)

    assert respuesta.status_code == 302
    assert respuesta.url == "/conjuntos/?superusuario=creado"
    assert mock_crear.called
    _, datos_enviados = mock_crear.call_args[0]
    assert "rol" not in datos_enviados
    assert datos_enviados["numero_documento"] == "9876543210"


def test_error_de_api_con_numero_documento_aparece_en_formulario():
    cliente = cliente_con_sesion(conjunto_activo=None, roles=["Superusuario"], tipo_usuario="Superusuario")
    datos = {
        "tipo_documento": "CC",
        "numero_documento": "9876543210",
        "nombres": "Carlos",
        "apellidos": "Ruiz",
        "correo": "carlos@correo.com",
        "telefono": "3001234567",
        "contrasena": "una-clave-larga-2026",
        "confirmar_contrasena": "una-clave-larga-2026",
    }

    error = ErrorDeApi(400, {"numero_documento": ["Ya existe una persona con este documento."]})
    with mock.patch("cliente_api.cuentas.crear_superusuario", side_effect=error):
        respuesta = cliente.post("/conjuntos/superusuarios/nuevo/", datos)

    assert respuesta.status_code == 200
    assert "Ya existe una persona con este documento." in respuesta.content.decode()
