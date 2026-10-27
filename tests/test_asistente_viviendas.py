"""Paso «Viviendas» del asistente (HU-39). La API se simula."""
import json
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ADMINISTRACION = ["vinculo.gestionar", "conjunto.editar"]
UNA_TORRE = {
    "tipo_vivienda": "apartamento",
    "etiqueta": "Torre",
    "patron": "piso_consecutivo",
    "primer_piso": 1,
    "agrupaciones": [{"nombre": "1", "pisos": 10, "por_piso": 4}],
}
SIN_VIVIENDAS = {"agrupaciones": [], "sin_agrupar": 0, "total": 0}
PREVIA = {
    "tipo_vivienda": "apartamento", "total": 40, "nuevas": 40, "repetidas": 0,
    "agrupaciones": [{"nombre": "Torre 1", "existe": False, "viviendas": 40, "nuevas": 40,
                      "primera": "Torre 1 – Apto 101", "ultima": "Torre 1 – Apto 1004"}],
}


def test_ver_como_queda_muestra_lo_que_calcula_la_api_y_no_crea_nada():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with (
        mock.patch("cliente_api.unidades.agrupaciones", return_value=SIN_VIVIENDAS),
        mock.patch("cliente_api.unidades.previsualizar_estructura", return_value=PREVIA) as previsualizar,
        mock.patch("cliente_api.unidades.generar_estructura") as generar,
    ):
        datos = {"accion": "previsualizar", "especificacion": json.dumps(UNA_TORRE)}
        html = cliente.post("/conjuntos/asistente/viviendas/", datos).content.decode()

    assert previsualizar.call_args.args[1] == UNA_TORRE
    assert "conjunto" not in previsualizar.call_args.args[1]
    assert "2. Viviendas" in html and "Torre 1 – Apto 1004" in html and "Crear 40 viviendas" in html
    generar.assert_not_called()


def test_crear_manda_la_descripcion_a_la_api_y_vuelve_al_paso():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with (
        mock.patch("cliente_api.unidades.generar_estructura", return_value=PREVIA) as generar,
        mock.patch("cliente_api.unidades.previsualizar_estructura") as previsualizar,
    ):
        datos = {"accion": "crear", "especificacion": json.dumps(UNA_TORRE)}
        respuesta = cliente.post("/conjuntos/asistente/viviendas/", datos)

    assert generar.call_args.args[1] == UNA_TORRE
    assert respuesta["Location"] == "/conjuntos/asistente/viviendas/?creadas=40"
    previsualizar.assert_not_called()


def test_una_descripcion_ilegible_se_avisa_y_no_llega_a_la_api():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with (
        mock.patch("cliente_api.unidades.agrupaciones", return_value=SIN_VIVIENDAS),
        mock.patch("cliente_api.unidades.previsualizar_estructura") as previsualizar,
        mock.patch("cliente_api.unidades.generar_estructura") as generar,
    ):
        datos = {"accion": "crear", "especificacion": "esto no es JSON"}
        html = cliente.post("/conjuntos/asistente/viviendas/", datos).content.decode()

    assert "No se pudo leer la descripción del conjunto. Vuelve a llenarla." in html
    previsualizar.assert_not_called()
    generar.assert_not_called()


def test_un_409_de_la_vista_previa_se_muestra():
    rechazo = ErrorDeApi(409, {"detail": "«Torre 1» ya existe y es de otro tipo de vivienda."})
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with (
        mock.patch("cliente_api.unidades.agrupaciones", return_value=SIN_VIVIENDAS),
        mock.patch("cliente_api.unidades.previsualizar_estructura", side_effect=rechazo),
    ):
        datos = {"accion": "previsualizar", "especificacion": json.dumps(UNA_TORRE)}
        html = cliente.post("/conjuntos/asistente/viviendas/", datos).content.decode()

    assert "«Torre 1» ya existe y es de otro tipo de vivienda." in html
    assert "Así va a quedar" not in html
