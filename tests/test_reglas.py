"""Pantallas de HU-10: reglas beta de reserva, alta en dos pasos y edición versionada. La API se simula."""
from unittest import mock

import pytest

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {"id": "3c4d5e6f-0000-4000-8000-000000000001", "nombre": "Salón comunal", "activo": True}
AFORO = {
    "id": "4d5e6f7a-0000-4000-8000-000000000001",
    "area": {"id": SALON["id"], "nombre": "Salón comunal"},
    "tipo": "AFORO",
    "tipo_nombre": "Aforo",
    "parametros": {"maximo": 25},
    "descripcion": "Máximo 25 asistentes",
    "vigencia_desde": "2026-09-27",
    "vigencia_hasta": None,
    "reemplaza": None,
    "creada_por": "Laura Gómez",
    "creada_en": "2026-09-27T10:00:00-05:00",
}
ADMINISTRACION = ["regla.ver", "regla.configurar", "area.gestionar"]
CAMPOS_POR_TIPO = {
    "ANTICIPACION_MINIMA": ["horas"],
    "ANTICIPACION_MAXIMA": ["dias"],
    "CUPO_POR_UNIDAD": ["reservas", "dias"],
    "AFORO": ["maximo"],
    "FRANJA_HORARIA": ["dias_semana", "desde", "hasta"],
    "DIAS_NO_RESERVABLES": ["dias_semana", "fechas"],
    "REQUIERE_PAZ_Y_SALVO": [],
}


def test_la_lista_agrupa_por_area_y_muestra_la_regla_en_palabras():
    with mock.patch("cliente_api.reglas.listar", return_value=[AFORO]):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/reglas/").content.decode()

    assert "<h2" in html and "Salón comunal</h2>" in html
    assert "Máximo 25 asistentes" in html and "Laura Gómez" in html
    assert "Editar" in html and "Retirar" in html
    assert "Maqueta" not in html and "Duración máxima" not in html


def test_sin_regla_configurar_no_hay_acciones():
    with mock.patch("cliente_api.reglas.listar", return_value=[AFORO]):
        html = cliente_con_sesion(permisos=["regla.ver"]).get("/reglas/").content.decode()

    assert "Máximo 25 asistentes" in html
    assert "Agregar regla" not in html and "Editar" not in html and "Retirar" not in html


def test_el_paso_1_lleva_al_formulario_del_tipo_con_el_area():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON]):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/reglas/nueva/", {"area": SALON["id"], "tipo": "AFORO"})

    assert respuesta["Location"] == f"/reglas/nueva/AFORO/?area={SALON['id']}"


@pytest.mark.parametrize("tipo", sorted(CAMPOS_POR_TIPO))
def test_cada_tipo_muestra_sus_campos(tipo):
    html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/reglas/nueva/{tipo}/?area={SALON['id']}").content.decode()

    for campo in CAMPOS_POR_TIPO[tipo]:
        assert f'name="{campo}"' in html
    otros = {campo for campos in CAMPOS_POR_TIPO.values() for campo in campos} - set(CAMPOS_POR_TIPO[tipo])
    assert not any(f'name="{campo}"' in html for campo in otros)
    assert 'name="vigencia_desde"' in html
    assert f'name="area" value="{SALON["id"]}"' in html


def test_guardar_manda_area_tipo_parametros_y_vigencia():
    with mock.patch("cliente_api.reglas.crear", return_value=AFORO) as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/nueva/FRANJA_HORARIA/",
            {"area": SALON["id"], "dias_semana": ["6", "5"], "desde": "10:00", "hasta": "18:00", "vigencia_desde": "2026-10-01"},
        )

    assert crear.call_args.args[1] == {
        "area": SALON["id"],
        "tipo": "FRANJA_HORARIA",
        "parametros": {"dias_semana": [5, 6], "desde": "10:00", "hasta": "18:00"},
        "vigencia_desde": "2026-10-01",
    }
    assert respuesta["Location"] == "/reglas/"


def test_el_400_de_la_api_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"parametros": ["Un área común esencial no se puede restringir por mora."]})
    with mock.patch("cliente_api.reglas.crear", side_effect=rechazo):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/nueva/REQUIERE_PAZ_Y_SALVO/", {"area": SALON["id"], "vigencia_desde": "2026-10-01"}
        ).content.decode()
    assert "Un área común esencial no se puede restringir por mora." in html

    rechazo = ErrorDeApi(400, {"maximo": ["Debe ser mayor o igual a 1."]})
    with mock.patch("cliente_api.reglas.crear", side_effect=rechazo):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/nueva/AFORO/", {"area": SALON["id"], "maximo": "5", "vigencia_desde": "2026-10-01"}
        ).content.decode()
    assert 'id="id_maximo-error">Debe ser mayor o igual a 1.' in html


def test_editar_avisa_la_version_nueva_y_manda_solo_los_parametros():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with mock.patch("cliente_api.reglas.obtener", return_value=AFORO):
        html = cliente.get(f"/reglas/{AFORO['id']}/editar/").content.decode()
    with (
        mock.patch("cliente_api.reglas.obtener", return_value=AFORO),
        mock.patch("cliente_api.reglas.editar") as editar,
    ):
        respuesta = cliente.post(f"/reglas/{AFORO['id']}/editar/", {"maximo": "30"})

    assert "Al guardar se crea una versión nueva; la anterior queda en el historial." in html
    assert 'value="25"' in html and 'name="vigencia_desde"' not in html
    assert editar.call_args.args[2] == {"maximo": 30}
    assert respuesta["Location"] == "/reglas/"


def test_el_paso_4_del_asistente_usa_la_misma_alta():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION + ["conjunto.editar"])
    with (
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.reglas.listar", return_value=[AFORO]),
    ):
        html = cliente.get("/conjuntos/asistente/reglas/").content.decode()
        respuesta = cliente.post("/conjuntos/asistente/reglas/", {"area": SALON["id"], "tipo": "AFORO"})
    with mock.patch("cliente_api.reglas.crear", return_value=AFORO):
        guardada = cliente.post(
            "/conjuntos/asistente/reglas/AFORO/", {"area": SALON["id"], "maximo": "25", "vigencia_desde": "2026-10-01"}
        )

    assert 'aria-current="step">4. Reglas' in html
    assert "Salón comunal: Máximo 25 asistentes" in html
    assert respuesta["Location"] == f"/conjuntos/asistente/reglas/AFORO/?area={SALON['id']}"
    assert guardada["Location"] == "/conjuntos/asistente/reglas/"
