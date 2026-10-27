from unittest import mock

from tests.ayudantes import cliente_con_sesion

PERFIL = {
    "id": "0a1b2c3d-0000-4000-8000-000000000001",
    "nombre": "Andrés Gómez",
    "correo": "admin@torres.com",
    "tipo_documento": "CC",
    "documento": "1023456789",
    "telefono": "",
    "activo": True,
    "roles": ["Administración"],
    "asignaciones": [],
}


def test_el_perfil_muestra_datos_del_usuario_y_roles_sin_contrasena():
    cliente = cliente_con_sesion()
    with mock.patch("cliente_api.cuentas.obtener_perfil", return_value=PERFIL) as obtener_perfil:
        respuesta = cliente.get("/perfil/")

    html = respuesta.content.decode()
    obtener_perfil.assert_called_once()
    assert respuesta.status_code == 200
    assert "Mi perfil" in html
    assert "Andrés Gómez" in html
    assert "admin@torres.com" in html
    assert "Administración" in html
    assert "Contraseña" not in html
