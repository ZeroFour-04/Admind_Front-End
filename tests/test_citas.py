from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

PERMISO_HORARIO = ["cita.gestionar_horario"]
PERMISO_AGENDAR = ["cita.agendar_propia"]


def horario_vacio():
    return {
        "id": None,
        "dias": [
            {
                "dia": dia,
                "activo": False,
                "hora_inicio": None,
                "hora_fin": None,
                "descanso_inicio": None,
                "descanso_fin": None,
            }
            for dia in range(7)
        ],
    }


def horario_guardado():
    datos = horario_vacio()
    datos["id"] = "cita-horario-1"
    datos["dias"][0] = {
        "dia": 0,
        "activo": True,
        "hora_inicio": "08:00",
        "hora_fin": "17:00",
        "descanso_inicio": "12:00",
        "descanso_fin": "14:00",
    }
    datos["dias"][2] = {
        "dia": 2,
        "activo": True,
        "hora_inicio": "09:30",
        "hora_fin": "16:00",
        "descanso_inicio": None,
        "descanso_fin": None,
    }
    return datos


def respuesta_agenda(fecha=None):
    franjas = []
    if fecha:
        franjas = [
            {"hora_inicio": "08:00:00", "hora_fin": "10:00:00", "estado": "libre"},
            {"hora_inicio": "10:00:00", "hora_fin": "12:00:00", "estado": "ocupada"},
        ]
    return {
        "horario": horario_guardado(),
        "franjas": franjas,
        "cita_propia": None,
    }


def test_la_pagina_muestra_las_opciones_de_horario_y_descanso():
    with mock.patch("cliente_api.citas.horario", return_value=horario_vacio()):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).get("/citas/")

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Horario de atención" in html
    assert "Mismo horario de lunes a viernes" in html
    assert "Mismo horario en un rango de días" in html
    assert "Configurar un horario diferente para cada día" in html
    assert "Inicio del almuerzo o descanso" in html
    assert 'type="time"' in html
    assert 'name="hora_inicio"' in html
    assert 'name="dia_6_descanso_fin"' in html


def test_un_horario_guardado_se_muestra_como_resumen_y_ofrece_editar():
    with mock.patch("cliente_api.citas.horario", return_value=horario_guardado()):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).get("/citas/")

    html = respuesta.content.decode()
    assert "Lunes" in html and "08:00 a 17:00" in html
    assert "Almuerzo o descanso: 12:00 a 14:00" in html
    assert "Miércoles" in html and "09:30 a 16:00" in html
    assert 'href="/citas/?editar=1">Editar horario</a>' in html
    assert '<form method="post" class="citas-formulario">' not in html


def test_editar_horario_abre_el_formulario_completo_con_los_valores_guardados():
    with mock.patch("cliente_api.citas.horario", return_value=horario_guardado()):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).get("/citas/?editar=1")

    html = respuesta.content.decode()
    assert 'name="dia_0_hora_inicio"' in html and 'value="08:00"' in html
    assert 'name="dia_0_descanso_fin"' in html and 'value="14:00"' in html
    assert 'name="dia_2_hora_inicio"' in html and 'value="09:30"' in html
    assert "Guardar cambios" in html
    assert 'href="/citas/">Cancelar edición</a>' in html


def test_el_horario_de_lunes_a_viernes_aplica_el_mismo_descanso():
    datos = {
        "modo": "lunes_viernes",
        "hora_inicio": "08:00",
        "hora_fin": "17:00",
        "descanso_inicio": "12:00",
        "descanso_fin": "14:00",
    }
    with (
        mock.patch("cliente_api.citas.horario", return_value=horario_vacio()),
        mock.patch("cliente_api.citas.guardar_horario", return_value=horario_vacio()) as guardar,
    ):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).post("/citas/", datos)

    horario = guardar.call_args.args[1]["dias"]
    assert respuesta["Location"] == "/citas/?guardado=1"
    assert [dia["activo"] for dia in horario] == [True, True, True, True, True, False, False]
    assert horario[0]["descanso_inicio"] == "12:00"
    assert horario[4]["hora_fin"] == "17:00"
    assert horario[5]["hora_inicio"] is None


def test_el_rango_incluye_los_dos_dias_y_rechaza_un_rango_invertido():
    base = {
        "modo": "rango",
        "dia_inicio": "1",
        "dia_fin": "3",
        "hora_inicio": "09:00",
        "hora_fin": "16:00",
        "descanso_inicio": "",
        "descanso_fin": "",
    }
    with (
        mock.patch("cliente_api.citas.horario", return_value=horario_vacio()),
        mock.patch("cliente_api.citas.guardar_horario", return_value=horario_vacio()) as guardar,
    ):
        cliente_con_sesion(permisos=PERMISO_HORARIO).post("/citas/", base)
        invertido = cliente_con_sesion(permisos=PERMISO_HORARIO).post(
            "/citas/", {**base, "dia_inicio": "5", "dia_fin": "2"}
        )

    assert [dia["activo"] for dia in guardar.call_args.args[1]["dias"]] == [
        False, True, True, True, False, False, False
    ]
    assert "El día final debe ser igual o posterior al inicial." in invertido.content.decode()
    guardar.assert_called_once()


def test_el_horario_por_dia_permite_horas_diferentes():
    datos = {
        "modo": "por_dia",
        "dia_0_activo": "on",
        "dia_0_hora_inicio": "08:00",
        "dia_0_hora_fin": "17:00",
        "dia_0_descanso_inicio": "12:00",
        "dia_0_descanso_fin": "14:00",
        "dia_2_activo": "on",
        "dia_2_hora_inicio": "10:00",
        "dia_2_hora_fin": "15:00",
    }
    with (
        mock.patch("cliente_api.citas.horario", return_value=horario_vacio()),
        mock.patch("cliente_api.citas.guardar_horario", return_value=horario_vacio()) as guardar,
    ):
        cliente_con_sesion(permisos=PERMISO_HORARIO).post("/citas/", datos)

    horario = guardar.call_args.args[1]["dias"]
    assert horario[0]["hora_inicio"] == "08:00"
    assert horario[0]["descanso_fin"] == "14:00"
    assert horario[1]["activo"] is False
    assert horario[2]["hora_inicio"] == "10:00"
    assert horario[2]["descanso_inicio"] is None


def test_no_guarda_un_descanso_que_se_sale_del_horario():
    datos = {
        "modo": "lunes_viernes",
        "hora_inicio": "08:00",
        "hora_fin": "17:00",
        "descanso_inicio": "16:00",
        "descanso_fin": "18:00",
    }
    with (
        mock.patch("cliente_api.citas.horario", return_value=horario_vacio()),
        mock.patch("cliente_api.citas.guardar_horario") as guardar,
    ):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).post("/citas/", datos)

    assert "El descanso debe quedar dentro del horario de atención." in respuesta.content.decode()
    guardar.assert_not_called()


def test_la_pagina_exige_permiso_de_administracion():
    respuesta = cliente_con_sesion(permisos=[]).get("/citas/")

    assert respuesta["Location"] == "/inicio/"


def test_muestra_el_error_de_api_al_guardar():
    datos = {
        "modo": "lunes_viernes",
        "hora_inicio": "08:00",
        "hora_fin": "17:00",
        "descanso_inicio": "",
        "descanso_fin": "",
    }
    rechazo = ErrorDeApi(400, {"detail": "No se pudo guardar el horario."})
    with (
        mock.patch("cliente_api.citas.horario", return_value=horario_vacio()),
        mock.patch("cliente_api.citas.guardar_horario", side_effect=rechazo),
    ):
        respuesta = cliente_con_sesion(permisos=PERMISO_HORARIO).post("/citas/", datos)

    assert "No se pudo guardar el horario." in respuesta.content.decode()


def test_residente_ve_horario_semanal_y_calendario_de_citas():
    with mock.patch("cliente_api.citas.agenda", return_value=respuesta_agenda()):
        respuesta = cliente_con_sesion(permisos=PERMISO_AGENDAR).get("/citas/agenda/")

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert "Horario de atención de Administración" in html
    assert 'href="/citas/agenda/">Citas</a>' in html
    assert "Almuerzo o descanso: 12:00 a 14:00" in html
    assert "Mes anterior" in html and "Mes siguiente" in html
    assert "Elige un día en el calendario" in html


def test_el_calendario_no_limita_la_anticipacion_a_un_numero_fijo_de_anios():
    with mock.patch("cliente_api.citas.agenda", return_value=respuesta_agenda()):
        respuesta = cliente_con_sesion(permisos=PERMISO_AGENDAR).get("/citas/agenda/?mes=2101-05")

    assert respuesta.status_code == 200
    assert "2101" in respuesta.content.decode()


def test_al_elegir_un_dia_muestra_franjas_de_dos_horas_y_permite_agendar():
    with mock.patch("cliente_api.citas.agenda", return_value=respuesta_agenda("2026-11-02")):
        respuesta = cliente_con_sesion(permisos=PERMISO_AGENDAR).get(
            "/citas/agenda/?mes=2026-11&dia=2026-11-02"
        )

    html = respuesta.content.decode()
    assert "08:00 a 10:00" in html
    assert "Cada cita dura dos horas" in html
    assert "Agendar cita" in html
    assert "Ocupada" in html


def test_agendar_cita_envia_la_fecha_y_la_hora_a_la_api():
    datos = {"fecha": "2026-11-02", "hora_inicio": "08:00"}
    cita = {"fecha": datos["fecha"], "hora_inicio": "08:00", "hora_fin": "10:00"}
    with mock.patch("cliente_api.citas.agendar", return_value=cita) as agendar:
        respuesta = cliente_con_sesion(permisos=PERMISO_AGENDAR).post(
            "/citas/agenda/?mes=2026-11&dia=2026-11-02",
            datos,
        )

    assert agendar.call_args.args[1] == datos
    assert respuesta["Location"] == "/citas/agenda/?mes=2026-11&dia=2026-11-02&agendada=1"


def test_la_pagina_de_agenda_exige_permiso_de_residente():
    respuesta = cliente_con_sesion(permisos=[]).get("/citas/agenda/")

    assert respuesta["Location"] == "/inicio/"
