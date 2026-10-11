"""Pantallas de HU-08: unidades por agrupación, sus vínculos vigentes y el histórico. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

TORRE_1 = {"id": "a1b2c3d4-0000-4000-8000-0000000000a1", "nombre": "Torre 1"}
TORRE_2 = {"id": "a1b2c3d4-0000-4000-8000-0000000000a2", "nombre": "Torre 2"}

APTO = {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – Apto 101", "vinculos_vigentes": 2,
        "tipo": "apartamento", "numero": "101", "piso": 1, "agrupacion": TORRE_1,
        "personas": [
            {"nombre": "Marta Gómez", "documento": "1023456790", "tipo": "propietario", "reside": False},
            {"nombre": "Pedro Gómez", "documento": "1023456791", "tipo": "arrendatario", "reside": True},
        ]}
APTO_102 = {"id": "7a1b2c3d-0000-4000-8000-000000000102", "nombre": "Torre 1 – Apto 102", "vinculos_vigentes": 0,
            "tipo": "apartamento", "numero": "102", "piso": 1, "agrupacion": TORRE_1, "personas": []}
APTO_T2 = {"id": "7a1b2c3d-0000-4000-8000-000000000201", "nombre": "Torre 2 – Apto 101", "vinculos_vigentes": 1,
           "tipo": "apartamento", "numero": "101", "piso": 1, "agrupacion": TORRE_2, "personas": []}
SUELTO = {"id": "7a1b2c3d-0000-4000-8000-000000000999", "nombre": "Portería", "vinculos_vigentes": 0,
          "tipo": "apartamento", "numero": "", "piso": None, "agrupacion": None, "personas": []}

MARTA = {"id": "1b2c3d4e-0000-4000-8000-000000000001", "nombre": "Marta Gómez"}
PEDRO = {"id": "1b2c3d4e-0000-4000-8000-000000000002", "nombre": "Pedro Gómez"}
DETALLE = {
    "id": APTO["id"],
    "nombre": APTO["nombre"],
    "agrupacion": TORRE_1,
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


def abrir_lista(unidades, permisos=ADMINISTRACION):
    with mock.patch("cliente_api.unidades.listar", return_value=unidades):
        return cliente_con_sesion(permisos=permisos).get("/unidades/")


def test_la_lista_muestra_un_recuadro_por_agrupacion_con_cuantas_viviendas_tiene():
    respuesta = abrir_lista([APTO, APTO_102, APTO_T2, SUELTO])
    html = respuesta.content.decode()

    assert [r["nombre"] for r in respuesta.context["recuadros"]] == ["Torre 1", "Torre 2", "Sin agrupar"]
    assert f'href="/unidades/agrupacion/{TORRE_1["id"]}/"' in html
    assert 'href="/unidades/sin-agrupar/"' in html
    torre_1 = respuesta.context["recuadros"][0]
    assert (torre_1["total"], torre_1["sin_vinculos"], torre_1["viviendas"]) == (2, 1, "apartamentos")
    assert "Apartamentos · 1 sin vínculos" in html
    assert "Maqueta" not in html


def test_el_buscador_recibe_las_viviendas_con_sus_personas_y_la_cedula_no_se_imprime():
    respuesta = abrir_lista([APTO, SUELTO])
    html = respuesta.content.decode()

    primera = respuesta.context["unidades"][0]
    assert primera["agrupacion"] == "Torre 1"
    assert primera["url"] == f"/unidades/{APTO['id']}/"
    assert [p["nombre"] for p in primera["personas"]] == ["Marta Gómez", "Pedro Gómez"]
    assert 'id="unidades-datos"' in html and "directorioDeUnidades" in html
    # La cédula viaja en el JSON del buscador para filtrar, pero no sale en la tabla ni en el texto de la página.
    assert "<td>1023456790" not in html and ">1023456790<" not in html


def test_sin_agrupaciones_la_lista_va_directo_a_la_tabla():
    respuesta = abrir_lista([SUELTO])
    html = respuesta.content.decode()

    assert respuesta.context["hay_agrupaciones"] is False
    assert 'class="agrupaciones"' not in html
    assert "hayAgrupaciones: false" in html
    assert "Registrar apartamento" in html


def test_sin_viviendas_la_lista_invita_a_registrarlas():
    html = abrir_lista([]).content.decode()

    assert "Todavía no hay viviendas registradas" in html
    assert 'id="unidades-datos"' not in html


def test_el_lateral_llama_a_la_seccion_unidades():
    html = abrir_lista([APTO]).content.decode()

    assert 'aria-current="page">Unidades</a>' in html
    assert "Apartamentos y parqueaderos" not in html


def test_una_agrupacion_lista_solo_sus_viviendas_y_las_trae_para_buscar():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO, APTO_102, APTO_T2, SUELTO]):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/unidades/agrupacion/{TORRE_1['id']}/")

    html = respuesta.content.decode()
    assert [u["nombre"] for u in respuesta.context["unidades"]] == ["Torre 1 – Apto 101", "Torre 1 – Apto 102"]
    assert "<h1>Torre 1</h1>" in html
    assert 'href="/unidades/"' in html and "Volver a Unidades" in html
    assert "limite: 0" in html


def test_las_viviendas_sin_agrupar_tienen_su_propia_pagina():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO, SUELTO]):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get("/unidades/sin-agrupar/")

    assert [u["nombre"] for u in respuesta.context["unidades"]] == ["Portería"]
    assert "<h1>Sin agrupar</h1>" in respuesta.content.decode()


def test_una_agrupacion_que_no_existe_en_el_conjunto_responde_404():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO]):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/unidades/agrupacion/{TORRE_2['id']}/")

    assert respuesta.status_code == 404


def test_si_la_api_rechaza_el_listado_la_pantalla_dice_el_motivo():
    rechazo = ErrorDeApi(403, {})
    with mock.patch("cliente_api.unidades.listar", side_effect=rechazo):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/unidades/").content.decode()

    assert rechazo.mensaje in html
    assert "Todavía no hay viviendas registradas" not in html


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


def test_el_detalle_vuelve_a_la_agrupacion_de_la_vivienda():
    with (
        mock.patch("cliente_api.unidades.obtener", return_value=DETALLE),
        mock.patch("cliente_api.cuentas.listar_usuarios", return_value=USUARIOS),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/unidades/{APTO['id']}/").content.decode()

    assert f'href="/unidades/agrupacion/{TORRE_1["id"]}/">Volver a Torre 1</a>' in html


def test_una_vivienda_sin_agrupacion_vuelve_a_unidades():
    suelta = {**DETALLE, "agrupacion": None}
    with (
        mock.patch("cliente_api.unidades.obtener", return_value=suelta),
        mock.patch("cliente_api.cuentas.listar_usuarios", return_value=USUARIOS),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/unidades/{APTO['id']}/").content.decode()

    assert 'href="/unidades/">Volver a Unidades</a>' in html


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


def test_sin_vinculo_gestionar_no_hay_formularios_ni_detalle_ni_personas():
    cliente = cliente_con_sesion(permisos=["anuncio.dirigir"])
    sin_personas = {k: v for k, v in APTO.items() if k != "personas"}
    with mock.patch("cliente_api.unidades.listar", return_value=[sin_personas]):
        respuesta = cliente.get("/unidades/")
        html = respuesta.content.decode()

    assert respuesta.context["unidades"][0]["url"] == ""
    assert respuesta.context["unidades"][0]["personas"] == []
    assert "Torre 1" in html
    assert "Registrar apartamento" not in html and "Ver vínculos" not in html
    assert "Propietario" not in html and "o una persona" not in html
    assert cliente.get(f"/unidades/{APTO['id']}/")["Location"] == "/unidades/"
