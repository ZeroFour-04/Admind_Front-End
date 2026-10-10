"""Pantallas de HU-10: el tablero de reglas por niveles, los días que no abre y la edición versionada. La API se simula."""
from unittest import mock

import pytest

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {
    "id": "3c4d5e6f-0000-4000-8000-000000000001", "nombre": "Salón comunal", "activo": True,
    "hora_apertura": "08:00", "hora_cierre": "22:00", "modo_uso": "reserva", "duracion_franja_minutos": 240,
    "permanencia_maxima_minutos": None, "aforo_maximo": 50,
}
GIMNASIO = {
    **SALON, "id": "3c4d5e6f-0000-4000-8000-000000000009", "nombre": "Gimnasio", "modo_uso": "ingreso",
    "duracion_franja_minutos": None, "permanencia_maxima_minutos": 60, "aforo_maximo": 3,
}
CATALOGO = [
    {"tipo": "ANTICIPACION_MAXIMA", "nivel": "alfa", "nombre": "Anticipación máxima", "modos": ["reserva"],
     "descripcion": "Hasta cuántos días hacia adelante se puede reservar.", "nota": ""},
    {"tipo": "ACOMPANANTES", "nivel": "alfa", "nombre": "Acompañantes", "modos": ["ingreso"],
     "descripcion": "Cuántos acompañantes puede tener adentro una misma vivienda a la vez.", "nota": ""},
    {"tipo": "DIAS_QUE_NO_ABRE", "nivel": "beta", "nombre": "Días que no abre", "modos": ["reserva", "ingreso"],
     "descripcion": "Días de la semana, fechas o periodos en que el área no presta servicio.", "nota": ""},
    {"tipo": "CUPO_POR_UNIDAD", "nivel": "beta", "nombre": "Límite de reservas por apartamento", "modos": ["reserva"],
     "descripcion": "Cuántas reservas de esta área puede tener un mismo apartamento en un periodo.", "nota": ""},
]
MAXIMA = {
    "id": "4d5e6f7a-0000-4000-8000-000000000001", "area": None, "nivel": "alfa",
    "tipo": "ANTICIPACION_MAXIMA", "tipo_nombre": "Anticipación máxima", "parametros": {"dias": 30},
    "descripcion": "Se solicita con máximo 30 días de anticipación", "vigencia_desde": "2026-10-06",
    "vigencia_hasta": None, "reemplaza": None, "creada_por": "Laura Gómez", "creada_en": "2026-10-06T10:00:00-05:00",
}
DIAS = {
    **MAXIMA, "id": "4d5e6f7a-0000-4000-8000-000000000002", "nivel": "beta",
    "area": {"id": SALON["id"], "nombre": "Salón comunal"}, "tipo": "DIAS_QUE_NO_ABRE", "tipo_nombre": "Días que no abre",
    "parametros": {"renglones": [{"dia_semana": 0, "motivo": "Limpieza"}]}, "descripcion": "No abre los lunes (Limpieza)",
}
ADMINISTRACION = ["regla.ver", "regla.configurar", "area.ver", "area.gestionar"]
CAMPOS_POR_TIPO = {
    "ANTICIPACION_MINIMA": ["horas"],
    "ANTICIPACION_MAXIMA": ["dias"],
    "CUPO_POR_UNIDAD": ["reservas", "dias"],
    "ACOMPANANTES": ["maximo"],
    "REQUIERE_PAZ_Y_SALVO": [],
}
PISO = {"desde": "2026-11-01", "hasta": "2026-11-30", "motivo": "Cambio del piso"}


def tablero(reglas, permisos=ADMINISTRACION, url="/reglas/", areas=(SALON,)):
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.listar", return_value=reglas),
        mock.patch("cliente_api.areas.listar", return_value=list(areas)),
    ):
        return cliente_con_sesion(permisos=permisos).get(url).content.decode()


def test_el_tablero_muestra_cada_regla_posible_con_su_descripcion_y_su_estado():
    html = tablero([MAXIMA, DIAS])

    assert "Reglas del conjunto</h2>" in html and "Salón comunal</h2>" in html
    assert "Hasta cuántos días hacia adelante se puede reservar." in html
    assert "Se solicita con máximo 30 días de anticipación" in html and "Cambiar" in html
    assert "Lunes: Limpieza" in html and "Agregar día" in html
    assert "Sin definir" in html and f"/reglas/definir/CUPO_POR_UNIDAD/?area={SALON['id']}" in html
    assert "con aforo de 50 personas" in html and "Maqueta" not in html


def test_el_tablero_avisa_las_reservas_que_caen_en_un_dia_que_no_abre():
    sin_reservas = tablero([DIAS])
    con_una = tablero([{**DIAS, "reservas_afectadas": 1}])
    con_tres = tablero([{**DIAS, "reservas_afectadas": 3}])

    assert "en estos días" not in sin_reservas
    assert "1 reserva ya apartada cae en estos días." in con_una
    assert "3 reservas ya apartadas caen en estos días." in con_tres
    assert f'href="/reservas/areas/{SALON["id"]}/solicitudes/">Revisarlas</a>' in con_tres


def test_sin_regla_configurar_no_hay_acciones():
    html = tablero([MAXIMA, DIAS], permisos=["regla.ver", "area.ver"])

    assert "Se solicita con máximo 30 días de anticipación" in html and "Lunes: Limpieza" in html
    assert "Sin definir" in html
    # Con el cierre de la etiqueta: «Cambiar de conjunto» está en la barra superior de toda pantalla.
    acciones = (">Definir</a>", ">Cambiar</a>", ">Quitar</button>", ">Agregar día</a>", "Cambiar horario o aforo")
    assert not any(accion in html for accion in acciones)


@pytest.mark.parametrize("tipo", sorted(CAMPOS_POR_TIPO))
def test_cada_tipo_muestra_sus_campos(tipo):
    with mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(
            f"/reglas/definir/{tipo}/?area={SALON['id']}"
        ).content.decode()

    for campo in CAMPOS_POR_TIPO[tipo]:
        assert f'name="{campo}"' in html
    otros = {campo for campos in CAMPOS_POR_TIPO.values() for campo in campos} - set(CAMPOS_POR_TIPO[tipo])
    assert not any(f'name="{campo}"' in html for campo in otros)
    assert 'name="vigencia_desde"' in html
    assert f'name="area" value="{SALON["id"]}"' in html


def test_definir_una_regla_del_conjunto_no_manda_area():
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", return_value=MAXIMA) as crear,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/ANTICIPACION_MAXIMA/", {"dias": "30", "vigencia_desde": "2026-10-06"}
        )

    assert crear.call_args.args[1] == {
        "tipo": "ANTICIPACION_MAXIMA", "parametros": {"dias": 30}, "vigencia_desde": "2026-10-06"
    }
    assert respuesta["Location"] == "/reglas/"


def test_definir_una_regla_de_un_area_manda_el_area():
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", return_value=MAXIMA) as crear,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/CUPO_POR_UNIDAD/",
            {"area": SALON["id"], "reservas": "2", "dias": "30", "vigencia_desde": "2026-10-06"},
        )

    assert crear.call_args.args[1] == {
        "area": SALON["id"], "tipo": "CUPO_POR_UNIDAD", "parametros": {"reservas": 2, "dias": 30},
        "vigencia_desde": "2026-10-06",
    }
    assert respuesta["Location"] == "/reglas/"


def test_un_400_de_la_api_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"dias": ["Debe ser mayor o igual a 1."]})
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", side_effect=rechazo),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/ANTICIPACION_MAXIMA/", {"dias": "5", "vigencia_desde": "2026-10-06"}
        ).content.decode()

    assert 'id="id_dias-error">Debe ser mayor o igual a 1.' in html


def test_un_409_de_la_api_se_muestra_arriba_del_formulario():
    rechazo = ErrorDeApi(409, {"detail": "Esta regla ya está definida. Cámbiala o retírala."})
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", side_effect=rechazo),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/ANTICIPACION_MAXIMA/", {"dias": "30", "vigencia_desde": "2026-10-06"}
        ).content.decode()

    assert '<div class="aviso-error" role="alert">' in html
    assert "Esta regla ya está definida. Cámbiala o retírala." in html


def test_editar_avisa_la_version_nueva_y_manda_solo_los_parametros():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.obtener", return_value=MAXIMA),
        mock.patch("cliente_api.reglas.editar") as editar,
    ):
        html = cliente.get(f"/reglas/{MAXIMA['id']}/editar/").content.decode()
        respuesta = cliente.post(f"/reglas/{MAXIMA['id']}/editar/", {"dias": "15"})

    assert "Al guardar se crea una versión nueva; la anterior queda en el historial." in html
    assert "Hasta cuántos días hacia adelante se puede reservar." in html
    assert 'value="30"' in html and 'name="vigencia_desde"' not in html
    assert editar.call_args.args[2] == {"dias": 15}
    assert respuesta["Location"] == "/reglas/"


def test_los_dias_que_no_abre_no_se_editan_como_las_demas_reglas():
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.obtener", return_value=DIAS),
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/reglas/{DIAS['id']}/editar/")

    assert respuesta.status_code == 404


def test_agregar_un_dia_crea_la_regla_si_no_existia_y_la_cambia_si_ya_existia():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    url = f"/reglas/dias/{SALON['id']}/agregar/"
    lunes = {"clase": "dia_semana", "dia_semana": "0", "motivo": "Limpieza"}
    periodo = {"clase": "periodo", "desde": PISO["desde"], "hasta": PISO["hasta"], "motivo": PISO["motivo"]}

    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.listar", return_value=[MAXIMA]),
        mock.patch("cliente_api.reglas.crear", return_value=DIAS) as crear,
        mock.patch("cliente_api.reglas.editar") as editar,
    ):
        html = cliente.get(url).content.decode()
        primera = cliente.post(url, lunes)
    assert 'name="clase"' in html and 'name="motivo"' in html and "Agregar día" in html
    assert crear.call_args.args[1]["area"] == SALON["id"]
    assert crear.call_args.args[1]["tipo"] == "DIAS_QUE_NO_ABRE"
    assert crear.call_args.args[1]["parametros"] == {"renglones": [{"dia_semana": 0, "motivo": "Limpieza"}]}
    assert not editar.called and primera["Location"] == "/reglas/"

    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.listar", return_value=[MAXIMA, DIAS]),
        mock.patch("cliente_api.reglas.crear") as crear,
        mock.patch("cliente_api.reglas.editar") as editar,
    ):
        segunda = cliente.post(url, periodo)
    assert editar.call_args.args[1:] == (DIAS["id"], {"renglones": [{"dia_semana": 0, "motivo": "Limpieza"}, PISO]})
    assert not crear.called and segunda["Location"] == "/reglas/"


def test_una_fecha_suelta_es_un_periodo_de_un_dia_y_el_error_de_la_api_se_muestra():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    url = f"/reglas/dias/{SALON['id']}/agregar/"
    navidad = {"clase": "periodo", "desde": "2026-12-25", "motivo": "Navidad"}
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.listar", return_value=[]),
        mock.patch("cliente_api.reglas.crear", return_value=DIAS) as crear,
    ):
        cliente.post(url, navidad)
        sin_motivo = cliente.post(url, {"clase": "dia_semana", "dia_semana": "0"}).content.decode()
    assert crear.call_count == 1
    assert crear.call_args.args[1]["parametros"] == {
        "renglones": [{"desde": "2026-12-25", "hasta": "2026-12-25", "motivo": "Navidad"}]
    }
    assert 'id="id_motivo-error"' in sin_motivo

    rechazo = ErrorDeApi(400, {"renglones": ["Los lunes ya están en la lista."]})
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.listar", return_value=[DIAS]),
        mock.patch("cliente_api.reglas.editar", side_effect=rechazo),
    ):
        html = cliente.post(url, {"clase": "dia_semana", "dia_semana": "0", "motivo": "Aseo"}).content.decode()
    assert "Los lunes ya están en la lista." in html


def test_quitar_un_dia_manda_los_que_quedan():
    con_dos = {**DIAS, "parametros": {"renglones": [{"dia_semana": 0, "motivo": "Limpieza"}, PISO]}}
    with (
        mock.patch("cliente_api.reglas.obtener", return_value=con_dos),
        mock.patch("cliente_api.reglas.editar") as editar,
        mock.patch("cliente_api.reglas.retirar") as retirar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(f"/reglas/{DIAS['id']}/dias/0/quitar/")

    assert editar.call_args.args[2] == {"renglones": [PISO]}
    assert not retirar.called and respuesta["Location"] == "/reglas/"


def test_quitar_el_ultimo_dia_retira_la_regla():
    with (
        mock.patch("cliente_api.reglas.obtener", return_value=DIAS),
        mock.patch("cliente_api.reglas.editar") as editar,
        mock.patch("cliente_api.reglas.retirar") as retirar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(f"/reglas/{DIAS['id']}/dias/0/quitar/")

    retirar.assert_called_once()
    assert not editar.called and respuesta["Location"] == "/reglas/"


def test_el_paso_de_reglas_del_asistente_es_el_mismo_tablero():
    permisos = ADMINISTRACION + ["conjunto.editar"]
    html = tablero([MAXIMA, DIAS], permisos=permisos, url="/conjuntos/asistente/reglas/")
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", return_value=MAXIMA),
        mock.patch("cliente_api.reglas.retirar"),
    ):
        cliente = cliente_con_sesion(permisos=permisos)
        formulario = cliente.get("/reglas/definir/CUPO_POR_UNIDAD/?volver=asistente").content.decode()
        guardada = cliente.post(
            "/reglas/definir/ANTICIPACION_MAXIMA/", {"dias": "30", "vigencia_desde": "2026-10-06", "volver": "asistente"}
        )
        retirada = cliente.post(f"/reglas/{MAXIMA['id']}/retirar/", {"volver": "asistente"})

    assert 'aria-current="step">5. Reglas' in html
    assert "Reglas del conjunto</h2>" in html and "Lunes: Limpieza" in html
    assert f"/reglas/{MAXIMA['id']}/editar/?volver=asistente" in html
    assert f"/reglas/dias/{SALON['id']}/agregar/?volver=asistente" in html
    assert f"/reglas/definir/CUPO_POR_UNIDAD/?area={SALON['id']}&amp;volver=asistente" in html
    assert 'name="volver" value="asistente"' in html
    assert 'aria-current="step">5. Reglas' in formulario and 'name="volver" value="asistente"' in formulario
    assert guardada["Location"] == "/conjuntos/asistente/reglas/"
    assert retirada["Location"] == "/conjuntos/asistente/reglas/"


# Modo de uso y acompañantes (plan de zonas con ingreso, F5)


def test_un_area_con_ingreso_no_muestra_el_limite_de_reservas_y_dice_como_se_usa():
    html = tablero([], areas=(SALON, GIMNASIO))
    gimnasio = html.split("Gimnasio</h2>")[1]
    salon = html.split("Salón comunal</h2>")[1].split("Gimnasio</h2>")[0]

    assert "Límite de reservas por apartamento" in salon
    assert "Límite de reservas por apartamento" not in gimnasio
    assert "Días que no abre" in gimnasio
    assert "permanencia máxima de 60 minutos y aforo de 3 personas adentro a la vez" in gimnasio


def test_acompanantes_sale_entre_las_reglas_del_conjunto_y_se_define_con_su_formulario():
    html = tablero([], areas=(SALON,))
    conjunto = html.split("Reglas del conjunto</h2>")[1].split("Salón comunal</h2>")[0]

    assert "Acompañantes" in conjunto and "/reglas/definir/ACOMPANANTES/" in conjunto

    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear") as crear,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/ACOMPANANTES/", {"maximo": "0", "vigencia_desde": "2026-10-08"}
        )

    assert crear.call_args.args[1] == {"tipo": "ACOMPANANTES", "parametros": {"maximo": 0}, "vigencia_desde": "2026-10-08"}
    assert respuesta["Location"] == "/reglas/"


def test_acompanantes_acepta_cero_y_rechaza_un_maximo_negativo():
    from apps.reglas.forms import AcompanantesForm

    assert AcompanantesForm(data={"maximo": "0", "vigencia_desde": "2026-10-08"}).is_valid()
    assert not AcompanantesForm(data={"maximo": "-1", "vigencia_desde": "2026-10-08"}).is_valid()


def test_un_400_de_la_api_sobre_acompanantes_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"maximo": ["Debe ser mayor o igual a 0."]})
    with (
        mock.patch("cliente_api.reglas.catalogo", return_value=CATALOGO),
        mock.patch("cliente_api.reglas.crear", side_effect=rechazo),
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/reglas/definir/ACOMPANANTES/", {"maximo": "2", "vigencia_desde": "2026-10-08"}
        )

    assert "id_maximo-error" in respuesta.content.decode()
