"""Pantallas de HU-06: el rol del usuario en el conjunto activo (uno solo). La API se simula."""
from unittest import mock

from apps.usuarios.forms import UsuarioForm
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


def test_el_alta_rechaza_un_telefono_corto_y_acepta_un_telefono_valido():
    datos = {
        "rol": "residente",
        "tipo_documento": "CC",
        "numero_documento": "1023456789",
        "nombres": "Carlos",
        "apellidos": "Gómez",
        "correo": "carlos@torres.com",
        "contrasena": "una-clave-larga-2026",
        "confirmar_contrasena": "una-clave-larga-2026",
    }

    invalido = UsuarioForm(data={**datos, "telefono": "323123"})
    valido = UsuarioForm(data={**datos, "telefono": "3001234567"})

    assert not invalido.is_valid()
    assert "telefono" in invalido.errors
    assert valido.is_valid()


def test_con_rol_asignar_se_puede_eliminar_y_cambiar_por_otro_rol():
    with mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES):
        html = cliente_con_sesion(permisos=["rol.asignar", "usuario.gestionar"]).get(DETALLE).content.decode()

    assert "Rol en este conjunto" in html
    assert f'action="{DETALLE}roles/{ASIGNACION}/cambiar/"' in html
    assert "Cambiar rol" in html and "Asignar rol" not in html
    assert "Eliminar usuario" in html
    assert "¿Seguro que quiere eliminar este usuario?" in html
    assert ">Si</button>" in html and ">NO</button>" in html
    assert "Retirar Administración" not in html
    assert '<option value="secretaria">Secretaría</option>' in html
    assert 'value="consejo"' not in html
    assert 'value="administracion"' not in html
    assert 'js/usuarios.js' in html
    assert "Maqueta" not in html


def test_sin_rol_asignar_no_hay_botones():
    with mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES):
        html = cliente_con_sesion(permisos=["usuario.gestionar"]).get(DETALLE).content.decode()

    assert "Administración" in html
    assert "Eliminar usuario" not in html and "Cambiar rol" not in html and "Asignar rol" not in html


def test_sin_rol_en_el_conjunto_se_ofrece_asignar():
    sin_rol = {**ANDRES, "roles": [], "asignaciones": []}
    with mock.patch("cliente_api.cuentas.obtener_usuario", return_value=sin_rol):
        html = cliente_con_sesion(permisos=["rol.asignar", "usuario.gestionar"]).get(DETALLE).content.decode()

    assert f'action="{DETALLE}roles/"' in html and "Asignar rol" in html
    assert "Cambiar rol" not in html


def test_cambiar_el_rol_manda_la_asignacion_y_el_rol_nuevo():
    with mock.patch("cliente_api.cuentas.cambiar_rol") as cambiar:
        respuesta = cliente_con_sesion(permisos=["rol.asignar"]).post(
            f"{DETALLE}roles/{ASIGNACION}/cambiar/", {"rol": "secretaria"}
        )

    assert [str(arg) for arg in cambiar.call_args.args[1:]] == [ANDRES["id"], ASIGNACION, "secretaria"]
    assert respuesta["Location"] == DETALLE


def test_el_409_al_cambiar_el_rol_del_ultimo_administrador_se_muestra_como_alerta():
    ultimo = ErrorDeApi(409, {"detail": "El conjunto no puede quedar sin Administración."})
    with (
        mock.patch("cliente_api.cuentas.cambiar_rol", side_effect=ultimo),
        mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES),
    ):
        html = cliente_con_sesion(permisos=["rol.asignar"]).post(
            f"{DETALLE}roles/{ASIGNACION}/cambiar/", {"rol": "residente"}
        ).content.decode()

    assert 'role="alert">El conjunto no puede quedar sin Administración.' in html


def test_asignar_un_rol_redirige_al_detalle():
    with mock.patch("cliente_api.cuentas.asignar_rol") as asignar:
        respuesta = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}roles/", {"rol": "secretaria"})

    assert [str(arg) for arg in asignar.call_args.args[1:]] == [ANDRES["id"], "secretaria"]
    assert respuesta["Location"] == DETALLE


def test_el_409_del_ultimo_administrador_se_muestra_como_alerta():
    ultimo = ErrorDeApi(409, {"detail": "El conjunto no puede quedar sin Administración."})
    with (
        mock.patch("cliente_api.cuentas.retirar_rol", side_effect=ultimo),
        mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES),
    ):
        html = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}roles/{ASIGNACION}/retirar/").content.decode()

    assert 'role="alert">El conjunto no puede quedar sin Administración.' in html


def test_eliminar_usuario_del_conjunto_redirige_a_la_lista():
    with mock.patch("cliente_api.cuentas.retirar_usuario_del_conjunto") as eliminar:
        respuesta = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}eliminar/")

    eliminar.assert_called_once()
    assert str(eliminar.call_args.args[1]) == ANDRES["id"]
    assert respuesta["Location"] == "/usuarios/"


def test_no_se_elimina_usuario_si_la_api_rechaza_el_ultimo_administrador():
    ultimo = ErrorDeApi(409, {"detail": "El conjunto no puede quedar sin Administración."})
    with (
        mock.patch("cliente_api.cuentas.retirar_usuario_del_conjunto", side_effect=ultimo),
        mock.patch("cliente_api.cuentas.obtener_usuario", return_value=ANDRES),
    ):
        html = cliente_con_sesion(permisos=["rol.asignar"]).post(f"{DETALLE}eliminar/").content.decode()

    assert 'role="alert">El conjunto no puede quedar sin Administración.' in html


# Registrar persona por documento (HU-07)

BUSCADOR = ["persona.buscar", "persona.vincular", "usuario.gestionar"]
CARLOS = {"id": "1b2c3d4e-0000-4000-8000-000000000009", "nombre": "Carlos Gómez", "tiene_cuenta": False,
          "roles_en_el_conjunto": []}


def buscar(cliente, numero="1.023.456.789"):
    return cliente.post("/usuarios/registrar/", {"accion": "buscar", "tipo_documento": "CC", "numero_documento": numero})


def test_la_lista_muestra_el_rol_de_cada_usuario():
    with mock.patch("cliente_api.cuentas.listar_usuarios", return_value=[ANDRES]):
        html = cliente_con_sesion(permisos=BUSCADOR).get("/usuarios/").content.decode()

    assert "<th>Rol</th>" in html
    assert "<td>Administración</td>" in html


def test_la_lista_lleva_a_registrar_persona():
    with mock.patch("cliente_api.cuentas.listar_usuarios", return_value=[]):
        html = cliente_con_sesion(permisos=BUSCADOR).get("/usuarios/").content.decode()

    assert 'href="/usuarios/registrar/"' in html and "Registrar persona" in html
    assert "Maqueta" not in html


def test_encontrada_se_ofrece_vincularla():
    with mock.patch("cliente_api.personas.buscar", return_value={"encontrada": True, "persona": CARLOS}) as api:
        html = buscar(cliente_con_sesion(permisos=BUSCADOR)).content.decode()

    assert api.call_args.args[1] == {"tipo_documento": "CC", "numero_documento": "1.023.456.789"}
    assert "Carlos Gómez" in html and "Sin cuenta" in html
    assert "Vincular al conjunto" in html
    assert f'value="{CARLOS["id"]}"' in html


def test_vincular_manda_la_persona_y_el_rol():
    with mock.patch("cliente_api.personas.vincular") as vincular:
        respuesta = cliente_con_sesion(permisos=BUSCADOR).post(
            "/usuarios/registrar/", {"accion": "vincular", "persona": CARLOS["id"], "rol": "vigilancia"}
        )

    assert vincular.call_args.args[1] == {"persona": CARLOS["id"], "rol": "vigilancia"}
    assert respuesta["Location"] == "/usuarios/"


def test_no_encontrada_lleva_al_alta_con_el_documento_y_sin_ponerlo_en_la_url():
    cliente = cliente_con_sesion(permisos=BUSCADOR)
    with mock.patch("cliente_api.personas.buscar", return_value={"encontrada": False}):
        respuesta = buscar(cliente, "99999999")

    assert respuesta["Location"] == "/usuarios/nuevo/"
    alta = cliente.get(respuesta["Location"]).content.decode()
    assert 'value="99999999"' in alta
    # Se usa una sola vez: al volver a abrir el alta, ya no está.
    assert 'value="99999999"' not in cliente.get("/usuarios/nuevo/").content.decode()


def test_el_documento_nunca_aparece_en_una_url():
    cliente = cliente_con_sesion(permisos=BUSCADOR)
    with mock.patch("cliente_api.personas.buscar", return_value={"encontrada": True, "persona": CARLOS}):
        html = buscar(cliente, "1023456789").content.decode()

    enlaces = [parte.split('"')[0] for parte in html.split('href="')[1:] + html.split('action="')[1:]]
    assert enlaces and not any("1023456789" in enlace for enlace in enlaces)


def test_el_429_se_muestra_como_alerta():
    limite = ErrorDeApi(429, {"detail": "Hiciste demasiadas búsquedas. Espera un rato e intenta de nuevo."})
    with mock.patch("cliente_api.personas.buscar", side_effect=limite):
        html = buscar(cliente_con_sesion(permisos=BUSCADOR)).content.decode()

    assert 'role="alert">Hiciste demasiadas búsquedas. Espera un rato e intenta de nuevo.' in html
