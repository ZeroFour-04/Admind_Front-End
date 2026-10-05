"""Pantallas de reservas (HU-11): franjas del día, tomar el bloqueo y la solicitud en trámite. La API se simula."""
from unittest import mock

from django.urls import URLResolver, get_resolver

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {
    "id": "3c4d5e6f-0000-4000-8000-000000000001",
    "nombre": "Salón comunal",
    "hora_apertura": "08:00",
    "hora_cierre": "22:00",
    "activo": True,
}
FRANJAS = {
    "area": {"id": SALON["id"], "nombre": "Salón comunal"},
    "fecha": "2026-12-26",
    "franjas": [
        {"hora_inicio": "08:00", "hora_fin": "12:00", "estado": "libre"},
        {"hora_inicio": "12:00", "hora_fin": "16:00", "estado": "en_solicitud"},
        {"hora_inicio": "16:00", "hora_fin": "20:00", "estado": "apartada"},
        {"hora_inicio": "20:00", "hora_fin": "22:00", "estado": "reservada"},
    ],
}
EN_TRAMITE = {
    "id": "6f7a8b9c-0000-4000-8000-000000000001",
    "area": {"id": SALON["id"], "nombre": "Salón comunal"},
    "fecha": "2026-12-26",
    "hora_inicio": "14:00",
    "hora_fin": "18:00",
    "estado": "EN_SOLICITUD",
    "estado_nombre": "En trámite",
    "bloqueo_vence_en": "2026-12-20T10:03:00-05:00",
    "segundos_restantes": 154,
    "motivo_liberacion": "",
    "unidad": None,
    "motivo": "",
    "asistentes": None,
    "observaciones": "",
    "creada_en": "2026-12-20T10:00:00-05:00",
    "enviada_en": None,
    "unidades_para_solicitar": [{"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"}],
}
RESIDENTE = ["area.ver", "reserva.solicitar"]
DIA = f"/reservas/?area={SALON['id']}&mes=2026-12&dia=2026-12-26"


def ver_franjas(permisos=RESIDENTE):
    with (
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.reservas.franjas", return_value=FRANJAS) as franjas,
    ):
        html = cliente_con_sesion(permisos=permisos).get(DIA).content.decode()
    return html, franjas


def test_las_franjas_muestran_su_estado_en_texto():
    html, franjas = ver_franjas()

    assert franjas.call_args.args[1:] == (SALON["id"], "2026-12-26")
    assert "Horario para reservas: 08:00 a 22:00." in html
    for texto in ("Libre", "En trámite", "Apartada", "Reservada"):
        assert f"{texto}</span>" in html
    assert 'class="am-pastilla am-pastilla--error">Apartada</span>' in html
    assert 'class="am-pastilla am-pastilla--error">Reservada</span>' in html
    assert "sábado 26 de diciembre de 2026" in html
    assert html.count(">Reservar</button>") == 1
    assert "Maqueta" not in html


def test_sin_reserva_solicitar_no_se_ofrece_reservar():
    html, _ = ver_franjas(permisos=["area.ver", "reserva.ver_todas"])

    assert "Libre</span>" in html
    assert "Reservar</button>" not in html


def test_bandeja_muestra_solicitud_del_residente_y_acciones_con_motivo():
    solicitud_enviada = {
        **EN_TRAMITE,
        "estado": "APARTADA",
        "estado_nombre": "Apartada",
        "residente": {"id": "8a9b0c1d-0000-4000-8000-000000000001", "nombre": "Pedro Gómez"},
        "unidad": {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
        "motivo": "Cumpleaños",
        "asistentes": 20,
        "observaciones": "Celebración familiar",
        "motivo_decision": "",
        "decidida_por": None,
        "decidida_en": None,
    }
    permisos = ["area.ver", "reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]
    with (
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=[solicitud_enviada]) as listar,
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente_con_sesion(permisos=permisos).get(
            f"/reservas/areas/{SALON['id']}/solicitudes/"
        ).content.decode()

    assert str(listar.call_args.args[1]) == SALON["id"]
    assert "Pedro Gómez" in html and "Cumpleaños" in html and "Celebración familiar" in html
    assert 'name="motivo"' in html
    assert 'name="decision" value="RESERVADA">Aceptar</button>' in html
    assert 'name="decision" value="RECHAZADA">Rechazar</button>' in html


def test_decidir_solicitud_envia_motivo_y_regresa_a_la_zona():
    id_solicitud = EN_TRAMITE["id"]
    motivo = "Se verificó la disponibilidad."
    with mock.patch("cliente_api.reservas.decidir") as decidir:
        respuesta = cliente_con_sesion(permisos=["reserva.aprobar"]).post(
            f"/reservas/solicitudes/{id_solicitud}/decision/",
            {"area": SALON["id"], "decision": "RESERVADA", "motivo": motivo},
        )

    assert str(decidir.call_args.args[1]) == id_solicitud
    assert decidir.call_args.args[2] == {"decision": "RESERVADA", "motivo": motivo}
    assert respuesta["Location"] == f"/reservas/areas/{SALON['id']}/solicitudes/?actualizada=1"


def test_reservar_toma_el_bloqueo_y_abre_la_solicitud():
    with mock.patch("cliente_api.reservas.tomar", return_value=EN_TRAMITE) as tomar:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(
            f"/reservas/tomar/?area={SALON['id']}&mes=2026-12&dia=2026-12-26",
            {"area": SALON["id"], "fecha": "2026-12-26", "hora_inicio": "08:00"},
        )

    assert tomar.call_args.args[1] == {"area": SALON["id"], "fecha": "2026-12-26", "hora_inicio": "08:00"}
    assert respuesta["Location"] == f"/reservas/solicitudes/{EN_TRAMITE['id']}/"


def test_un_409_se_muestra_como_alerta_sobre_las_franjas():
    ocupada = ErrorDeApi(409, {"detail": "Otra persona está tramitando esta franja en este momento."})
    with (
        mock.patch("cliente_api.reservas.tomar", side_effect=ocupada),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.reservas.franjas", return_value=FRANJAS),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).post(
            f"/reservas/tomar/?area={SALON['id']}&mes=2026-12&dia=2026-12-26",
            {"area": SALON["id"], "fecha": "2026-12-26", "hora_inicio": "08:00"},
        ).content.decode()

    assert 'role="alert">\n    <p>Otra persona está tramitando esta franja en este momento.</p>' in html
    assert html.index("Otra persona está tramitando") < html.index('class="franjas"')


def test_la_solicitud_en_tramite_trae_la_cuenta_regresiva_y_el_boton_cancelar():
    with mock.patch("cliente_api.reservas.obtener", return_value=EN_TRAMITE):
        html = cliente_con_sesion(permisos=RESIDENTE).get(f"/reservas/solicitudes/{EN_TRAMITE['id']}/").content.decode()

    assert f"solicitudDeReserva(154, '/reservas/solicitudes/{EN_TRAMITE['id']}/liberar/')" in html
    assert ">2:34</span>" in html
    assert ">Cancelar</button>" in html
    assert "js/vendor/alpine.min.js" in html and "defer" in html


def test_una_solicitud_que_ya_no_esta_en_tramite_lo_dice_y_no_carga_javascript():
    vencida = {**EN_TRAMITE, "estado": "EXPIRADA", "estado_nombre": "Expirada", "segundos_restantes": 0}
    with mock.patch("cliente_api.reservas.obtener", return_value=vencida):
        html = cliente_con_sesion(permisos=RESIDENTE).get(f"/reservas/solicitudes/{EN_TRAMITE['id']}/").content.decode()

    assert "Se venció el tiempo sin enviar la solicitud. La franja quedó libre." in html
    assert "Volver al calendario" in html
    assert "alpine.min.js" not in html


def test_liberar_llama_a_la_api_y_vuelve_al_dia_de_la_franja():
    liberada = {**EN_TRAMITE, "estado": "LIBERADA"}
    with mock.patch("cliente_api.reservas.liberar", return_value=liberada) as liberar:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(f"/reservas/solicitudes/{EN_TRAMITE['id']}/liberar/")

    assert str(liberar.call_args.args[1]) == EN_TRAMITE["id"]
    assert respuesta["Location"] == f"/reservas/?area={SALON['id']}&mes=2026-12&dia=2026-12-26"


def test_las_pantallas_sin_javascript_no_cargan_alpine():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        html = cliente_con_sesion().get("/anuncios/").content.decode()

    assert "alpine" not in html


# Confirmación del contenido (HU-12). Lo que depende del navegador va al guion manual.


def ver_solicitud(**cambios):
    with mock.patch("cliente_api.reservas.obtener", return_value={**EN_TRAMITE, **cambios}):
        return cliente_con_sesion(permisos=RESIDENTE).get(f"/reservas/solicitudes/{EN_TRAMITE['id']}/").content.decode()


def test_el_panel_dice_el_area_el_dia_de_la_semana_en_letras_la_fecha_y_el_horario():
    html = ver_solicitud()

    assert "Vas a solicitar el <b>Salón comunal</b> para el <b>sábado 26 de diciembre de 2026</b>" in html
    assert "de <b>2:00 p. m. a 6:00 p. m.</b>, para <b x-text=\"asistentes\"></b> asistentes." in html
    assert ">Corregir</button>" in html and ">Enviar solicitud</button>" in html


def test_los_avisos_se_muestran_con_texto_y_no_deshabilitan_el_envio():
    html = ver_solicitud(avisos=["menos_de_24h", "limite_de_anticipacion", "otra_solicitud"])

    assert "Empieza en menos de 24 horas." in html
    assert "Es el último día que se puede reservar con la anticipación permitida." in html
    assert "Ya tienes otra solicitud apartada o reservada." in html
    assert '<button class="am-btn am-btn--primario" type="submit" :disabled="vencido">Enviar solicitud</button>' in html


def test_revisar_no_pide_nada_al_servidor():
    html = ver_solicitud()

    assert '<button class="am-btn am-btn--primario" type="button" @click="revisar($el.form)"' in html
    assert not any("revisar" in ruta for ruta in rutas_del_front(get_resolver().url_patterns))


def rutas_del_front(patrones, prefijo=""):
    for patron in patrones:
        if isinstance(patron, URLResolver):
            yield from rutas_del_front(patron.url_patterns, prefijo + str(patron.pattern))
        else:
            yield prefijo + str(patron.pattern)


def test_con_una_sola_unidad_va_fija_y_con_varias_se_elige():
    una = ver_solicitud()
    varias = ver_solicitud(unidades_para_solicitar=[
        {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
        {"id": "7a1b2c3d-0000-4000-8000-000000000102", "nombre": "Torre 1 – 102"},
    ])

    assert "A nombre de Torre 1 – 101." in una and '<select class="am-campo__control" id="id_unidad"' not in una
    assert '<select class="am-campo__control" id="id_unidad"' in varias


def test_sin_unidades_para_solicitar_no_hay_formulario():
    html = ver_solicitud(unidades_para_solicitar=[])

    assert "Para reservar necesitas vivir en un apartamento del conjunto." in html
    assert 'name="motivo"' not in html


# Envío (HU-13)

ENVIO = {"unidad": "7a1b2c3d-0000-4000-8000-000000000101", "motivo": "Cumpleaños", "asistentes": "40", "observaciones": ""}
URL_ENVIO = f"/reservas/solicitudes/{EN_TRAMITE['id']}/enviar/"


def test_enviar_manda_la_solicitud_a_la_api_y_vuelve_a_la_solicitud():
    with (
        mock.patch("cliente_api.reservas.obtener", return_value=EN_TRAMITE),
        mock.patch("cliente_api.reservas.enviar", return_value={**EN_TRAMITE, "estado": "APARTADA"}) as enviar,
    ):
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(URL_ENVIO, ENVIO)

    assert enviar.call_args.args[2] == {**ENVIO, "asistentes": 40}
    assert respuesta["Location"] == f"/reservas/solicitudes/{EN_TRAMITE['id']}/"
    assert f'action="{URL_ENVIO}"' in ver_solicitud()


def test_apartada_dice_que_la_administracion_la_revisara():
    html = ver_solicitud(estado="APARTADA", estado_nombre="Apartada", segundos_restantes=0)

    assert "Tu solicitud quedó apartada. La administración la revisará y te avisará." in html


def test_rechazada_por_las_reglas_muestra_todos_los_motivos_y_el_camino_al_calendario():
    evaluacion = [
        {"id": None, "tipo": "RESIDE", "cumple": True, "motivo": ""},
        {"id": "r1", "tipo": "AFORO", "cumple": False, "motivo": "Esta área admite máximo 25 asistentes y la solicitud dice 40."},
        {"id": "r2", "tipo": "DIAS_NO_RESERVABLES", "cumple": False, "motivo": "Esta área no se reserva ese día."},
    ]
    rechazo = ErrorDeApi(400, {"detail": "La solicitud no cumple las reglas del conjunto.", "motivos": ["..."]})
    with (
        mock.patch("cliente_api.reservas.obtener", return_value=EN_TRAMITE),
        mock.patch("cliente_api.reservas.enviar", side_effect=rechazo),
    ):
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(URL_ENVIO, ENVIO)
    html = ver_solicitud(estado="LIBERADA", estado_nombre="Liberada", motivo_liberacion="reglas",
                         segundos_restantes=0, evaluacion=evaluacion)

    assert respuesta["Location"] == f"/reservas/solicitudes/{EN_TRAMITE['id']}/"
    assert "La solicitud no cumple las reglas del conjunto:" in html
    assert "Esta área admite máximo 25 asistentes y la solicitud dice 40." in html
    assert "Esta área no se reserva ese día." in html
    assert "La franja quedó libre." in html and "Volver al calendario" in html


def test_un_409_al_enviar_se_muestra_con_su_mensaje():
    vencida = ErrorDeApi(409, {"detail": "Se venció el tiempo. La franja quedó libre."})
    with (
        mock.patch("cliente_api.reservas.obtener",
                   side_effect=[EN_TRAMITE, {**EN_TRAMITE, "estado": "EXPIRADA", "estado_nombre": "Expirada", "segundos_restantes": 0}]),
        mock.patch("cliente_api.reservas.enviar", side_effect=vencida),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).post(URL_ENVIO, ENVIO).content.decode()

    assert 'role="alert">Se venció el tiempo. La franja quedó libre.</div>' in html
