"""Pantallas de HU-06: roles del usuario en el conjunto activo. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ANDRES = {
    "id": "0a1b2c3d-0000-4000-8000-000000000001",
    "nombre": "Andrés Gómez",
    "correo": "admin@torres.com",
    "tipo_documento": "CC",
    "documento": "1023456789",
    "telefono": "",
    "activo": True,
    "roles": ["Administración"],
    "persona": "1b2c3d4e-0000-4000-8000-000000000001",
    "asignaciones": [
        {"id": "2c3d4e5f-0000-4000-8000-000000000001", "rol": "administracion", "nombre": "Administración",
         "desde": "2026-09-01"},
    ],
}
DETALLE = f"/usuarios/{ANDRES['id']}/"
ASIGNACION = ANDRES["asignaciones"][0]["id"]


def test_con_rol_asignar_se_puede_retirar_y_solo_se_ofrecen_los_roles_que_no_tiene():
    with mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES):
        html = cliente_con_sesion(permisos=["rol.asignar", "usuario.gestionar"]).get(DETALLE).content.decode()

    assert "Roles en este conjunto" in html
    assert "Retirar Administración" in html
    assert '<option value="consejo">Consejo</option>' in html
    assert 'value="administracion"' not in html
    assert "Maqueta" not in html


def test_sin_rol_asignar_no_hay_botones():
    with mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES):
        html = cliente_con_sesion(permisos=["usuario.gestionar"]).get(DETALLE).content.decode()

    assert "Administración" in html
    assert "Retirar" not in html and "Asignar rol" not in html


def test_asignar_un_rol_redirige_al_detalle():
    with mock.patch("cliente_api.cuentas.asignar_rol") as asignar:
        respuesta = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}roles/", {"rol": "consejo"})

    assert [str(arg) for arg in asignar.call_args.args[1:]] == [ANDRES["id"], "consejo"]
    assert respuesta["Location"] == DETALLE


def test_el_409_del_ultimo_administrador_se_muestra_como_alerta():
    ultimo = ErrorDeApi(409, {"detail": "El conjunto no puede quedar sin Administración."})
    with (
        mock.patch("cliente_api.cuentas.retirar_rol", side_effect=ultimo),
        mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES),
    ):
        html = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}roles/{ASIGNACION}/retirar/").content.decode()

    assert 'role="alert">El conjunto no puede quedar sin Administración.' in html
