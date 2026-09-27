"""Pantallas de HU-08: apartamentos, sus vínculos vigentes y el histórico. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

APTO = {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101", "vinculos_vigentes": 2}
MARTA = {"id": "1b2c3d4e-0000-4000-8000-000000000001", "nombre": "Marta Gómez"}
PEDRO = {"id": "1b2c3d4e-0000-4000-8000-000000000002", "nombre": "Pedro Gómez"}
DETALLE = {
    "id": APTO["id"],
    "nombre": APTO["nombre"],
    "vigentes": [
        {"id": "5e6f7a8b-0000-4000-8000-000000000001", "persona": MARTA, "tipo": "propietario",
         "tipo_nombre": "Propietario", "reside": False, "vigencia_desde": "2026-01-15", "vigencia_hasta": None},
    ],
    "historicos": [
        {"id": "5e6f7a8b-0000-4000-8000-000000000002", "persona": PEDRO, "tipo": "arrendatario",
         "tipo_nombre": "Arrendatario", "reside": True, "vigencia_desde": "2025-02-01", "vigencia_hasta": "2026-09-27"},
    ],
}
USUARIOS = [{"id": "u1", "persona": MARTA["id"], "nombre": MARTA["nombre"]},
            {"id": "u2", "persona": PEDRO["id"], "nombre": PEDRO["nombre"]}]
ADMINISTRACION = ["vinculo.gestionar", "usuario.gestionar"]


def test_la_lista_muestra_cuantos_vinculos_vigentes_tiene_cada_apartamento():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/unidades/").content.decode()

    assert "Torre 1 – 101" in html
    assert '<td class="am-col-num am-num">2</td>' in html
    assert "Registrar apartamento" in html
    assert "Maqueta" not in html


def test_registrar_un_apartamento_lleva_a_su_detalle():
    with mock.patch("cliente_api.unidades.crear", return_value=APTO) as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/unidades/", {"nombre": "Torre 1 – 101"})

    assert crear.call_args.args[1] == {"nombre": "Torre 1 – 101"}
    assert respuesta["Location"] == f"/unidades/{APTO['id']}/"


def test_el_detalle_separa_vigentes_de_historicos():
    with (
        mock.patch("cliente_api.unidades.obtener", return_value=DETALLE),
        mock.patch("cliente_api.cuentas.listar_usuarios", return_value=USUARIOS),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/unidades/{APTO['id']}/").content.decode()

    vigentes, historicos = html.split('id="titulo-historicos"')
    assert "Marta Gómez" in vigentes and "No vive aquí" in vigentes and "Cerrar vínculo" in vigentes
    assert "Pedro Gómez" in historicos and "Vive aquí" in historicos
    assert f'<option value="{PEDRO["id"]}">Pedro Gómez</option>' in html


def test_agregar_un_vinculo_manda_la_persona_el_tipo_y_si_reside():
    with (
        mock.patch("cliente_api.unidades.obtener", return_value=DETALLE),
        mock.patch("cliente_api.cuentas.listar_usuarios", return_value=USUARIOS),
        mock.patch("cliente_api.unidades.registrar_vinculo") as registrar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/unidades/{APTO['id']}/", {"persona": PEDRO["id"], "tipo": "arrendatario", "reside": "on"}
        )

    assert registrar.call_args.args[2] == {"persona": PEDRO["id"], "tipo": "arrendatario", "reside": True}
    assert respuesta["Location"] == f"/unidades/{APTO['id']}/"


def test_un_vinculo_duplicado_se_muestra():
    duplicado = ErrorDeApi(409, {"detail": "Esta persona ya tiene un vínculo vigente de ese tipo con la unidad."})
    with (
        mock.patch("cliente_api.unidades.obtener", return_value=DETALLE),
        mock.patch("cliente_api.cuentas.listar_usuarios", return_value=USUARIOS),
        mock.patch("cliente_api.unidades.registrar_vinculo", side_effect=duplicado),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/unidades/{APTO['id']}/", {"persona": MARTA["id"], "tipo": "propietario"}
        ).content.decode()

    assert "Esta persona ya tiene un vínculo vigente de ese tipo con la unidad." in html


def test_cerrar_un_vinculo_manda_la_fecha():
    vinculo_id = DETALLE["vigentes"][0]["id"]
    with mock.patch("cliente_api.unidades.cerrar_vinculo") as cerrar:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/unidades/{APTO['id']}/vinculos/{vinculo_id}/cerrar/", {"vigencia_hasta": "2026-09-27"}
        )

    assert cerrar.call_args.args[3] == {"vigencia_hasta": "2026-09-27"}
    assert respuesta["Location"] == f"/unidades/{APTO['id']}/"


def test_sin_vinculo_gestionar_no_hay_formularios_ni_detalle():
    cliente = cliente_con_sesion(permisos=["anuncio.dirigir"])
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO]):
        html = cliente.get("/unidades/").content.decode()

    assert "Torre 1 – 101" in html
    assert "Registrar apartamento" not in html and "Ver vínculos" not in html
    assert cliente.get(f"/unidades/{APTO['id']}/")["Location"] == "/unidades/"
