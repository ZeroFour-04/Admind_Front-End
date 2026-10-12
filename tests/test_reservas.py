"""Pantallas de reservas (HU-11): franjas del día, tomar el bloqueo y la solicitud en trámite. La API se simula."""
from datetime import date
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import URLResolver, get_resolver

from cliente_api.http import ApiNoDisponible, ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {
    "id": "3c4d5e6f-0000-4000-8000-000000000001",
    "nombre": "Salón comunal",
    "hora_apertura": "08:00",
    "hora_cierre": "22:00",
    "modo_uso": "reserva",
    "duracion_franja_minutos": 240,
    "permanencia_maxima_minutos": None,
    "aforo_maximo": 50,
    "en_mantenimiento": False,
    "activo": True,
}
GIMNASIO = {
    **SALON,
    "id": "3c4d5e6f-0000-4000-8000-000000000009",
    "nombre": "Gimnasio",
    "modo_uso": "ingreso",
    "duracion_franja_minutos": None,
    "permanencia_maxima_minutos": 60,
    "aforo_maximo": 30,
}
ZONA_GIMNASIO = {
    "area": GIMNASIO,
    "adentro": 18,
    "cupos": 12,
    "abierta_ahora": True,
    "motivo_cierre": "",
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
    "area": {"id": SALON["id"], "nombre": "Salón comunal", "condiciones_alquiler": ""},
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


def test_el_calendario_no_enlaza_dias_anteriores_a_hoy():
    with (
        mock.patch("apps.reservas.views.timezone.localdate", return_value=date(2026, 10, 5)),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente_con_sesion().get("/reservas/?mes=2026-10").content.decode()

    assert 'href="?area=&amp;mes=2026-10&amp;dia=2026-10-04"' not in html
    assert 'href="?area=&amp;mes=2026-10&amp;dia=2026-10-05"' in html
    assert "no disponible" not in html


def test_al_cambiar_el_area_se_envia_el_formulario_sin_boton_ver_franjas():
    with mock.patch("cliente_api.areas.listar", return_value=[SALON]):
        html = cliente_con_sesion().get("/reservas/?mes=2026-10").content.decode()

    assert 'name="area" data-envio-al-cambiar' in html
    assert "Ver franjas" not in html
    assert 'js/calendario-reservas.js' in html
    assert html.index("selector-area") < html.index('class="am-tarjeta calendario"')


def test_el_calendario_ignora_fecha_pasada_enviada_directamente():
    with (
        mock.patch("apps.reservas.views.timezone.localdate", return_value=date(2026, 10, 5)),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.reservas.franjas") as franjas,
    ):
        html = cliente_con_sesion().get(
            f"/reservas/?area={SALON['id']}&mes=2026-10&dia=2026-10-04"
        ).content.decode()

    franjas.assert_not_called()
    assert "Día elegido:" not in html


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


def test_el_residente_ve_las_condiciones_al_agendar_y_antes_de_enviar():
    condiciones = "No se permiten fiestas después de las 10 p. m.\nDejar limpia la zona."
    html = ver_solicitud(area={**EN_TRAMITE["area"], "condiciones_alquiler": condiciones})

    assert html.count("Reglas de renta de la zona") == 2
    assert html.count("No se permiten fiestas después de las 10 p. m.") == 2
    assert html.count("Dejar limpia la zona.") == 2


@pytest.mark.parametrize("estado,nombre", [("RESERVADA", "Reservada"), ("RECHAZADA", "Rechazada")])
def test_el_residente_ve_las_condiciones_al_consultar_una_decision(estado, nombre):
    condiciones = "No se permiten fiestas después de las 10 p. m."
    html = ver_solicitud(
        estado=estado,
        estado_nombre=nombre,
        area={**EN_TRAMITE["area"], "condiciones_alquiler": condiciones},
    )

    assert "Reglas de renta de la zona" in html
    assert condiciones in html


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


# Cómo se usa cada zona y sus cupos (plan de zonas con ingreso, F6)


def ver_zonas(areas, zonas=None, permisos=RESIDENTE, url="/reservas/"):
    """La pantalla con `zonas` como respuesta de la API de ingresos, o una excepción para simular que no responde."""
    con_zonas = {"side_effect": zonas} if isinstance(zonas, Exception) else {"return_value": zonas or []}
    with (
        mock.patch("cliente_api.areas.listar", return_value=areas),
        mock.patch("cliente_api.ingresos.zonas", **con_zonas),
    ):
        return " ".join(cliente_con_sesion(permisos=permisos).get(url).content.decode().split())


def fila(html, nombre):
    return html.split(f"<td>{nombre}</td>")[1].split("</tr>")[0]


def test_la_tabla_dice_como_se_usa_cada_zona_y_la_de_ingreso_muestra_sus_cupos_sin_reservar():
    html = ver_zonas([SALON, GIMNASIO], [ZONA_GIMNASIO])

    assert "<td>Con reserva</td>" in fila(html, "Salón comunal") and ">Reservar</a>" in fila(html, "Salón comunal")
    gimnasio = fila(html, "Gimnasio")
    assert "<td>Con ingreso</td>" in gimnasio
    assert "12 de 30 libres" in gimnasio and "Abierta" in gimnasio and "puedes quedarte hasta 60 min" in gimnasio
    assert "Reservar" not in gimnasio


def test_sin_cupo_cerrada_y_en_mantenimiento_se_dicen_con_texto():
    sin_cupo = ver_zonas([GIMNASIO], [{**ZONA_GIMNASIO, "adentro": 30, "cupos": 0}])
    cerrada = ver_zonas([GIMNASIO], [{**ZONA_GIMNASIO, "abierta_ahora": False, "motivo_cierre": "Atiende de 05:00 a 22:00."}])
    mantenimiento = ver_zonas([{**GIMNASIO, "en_mantenimiento": True}], [{**ZONA_GIMNASIO, "abierta_ahora": False}])

    assert "Sin cupo" in fila(sin_cupo, "Gimnasio") and "0 de 30 libres" in fila(sin_cupo, "Gimnasio")
    assert "Cerrada" in fila(cerrada, "Gimnasio") and "Atiende de 05:00 a 22:00." in fila(cerrada, "Gimnasio")
    assert "En mantenimiento" in fila(mantenimiento, "Gimnasio") and "Cerrada" not in fila(mantenimiento, "Gimnasio")


def test_el_selector_del_calendario_no_lista_las_zonas_con_ingreso_ni_pinta_sus_franjas():
    with (
        mock.patch("cliente_api.areas.listar", return_value=[SALON, GIMNASIO]),
        mock.patch("cliente_api.ingresos.zonas", return_value=[ZONA_GIMNASIO]),
        mock.patch("cliente_api.reservas.franjas") as franjas,
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).get(f"/reservas/?area={GIMNASIO['id']}&mes=2026-12&dia=2026-12-26").content.decode()

    selector = html.split('<select')[1].split("</select>")[0]
    assert "Salón comunal" in selector and "Gimnasio" not in selector
    assert 'selected' not in selector
    franjas.assert_not_called()


def test_con_la_api_de_ingresos_caida_la_pantalla_carga_y_las_zonas_con_reserva_se_pueden_reservar():
    html = ver_zonas([SALON, GIMNASIO], ApiNoDisponible())

    assert "No pudimos consultar los cupos en este momento." in html
    assert ">Reservar</a>" in fila(html, "Salón comunal")
    assert "Sin información" in fila(html, "Gimnasio")


def test_sin_zonas_con_ingreso_no_se_consulta_la_api_de_ingresos():
    with (
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
        mock.patch("cliente_api.ingresos.zonas") as zonas,
    ):
        cliente_con_sesion(permisos=RESIDENTE).get("/reservas/")

    zonas.assert_not_called()


def test_la_tabla_invita_a_recargar_para_ver_los_cupos_nuevos():
    html = ver_zonas([GIMNASIO], [ZONA_GIMNASIO])

    assert "Los cupos se actualizan al recargar la página." in html and ">Actualizar</a>" in html


# El pago declarado de una reserva y su comprobante (HU-16). El front solo muestra: decide la API.

AVISO_DEL_DINERO = "AdMind no verifica el dinero: el pago lo declara una persona de la administración."
RESIDENTE_ID = "8a9b0c1d-0000-4000-8000-000000000001"
COMPROBANTE_ID = "9c0d1e2f-0000-4000-8000-000000000001"
SIN_PAGO = {"declarado": False, "declarado_en": None, "comprobantes": []}
PAGO_DECLARADO = {
    "declarado": True,
    "declarado_en": "2026-10-12T09:30:00-05:00",
    "declarado_por": "Andrés Gómez",
    "comprobantes": [
        {
            "id": COMPROBANTE_ID,
            "nombre": "transferencia.png",
            "subido_en": "2026-10-11T18:00:00-05:00",
            "del_residente": True,
            "subido_por": "Pedro Gómez",
        },
        {
            "id": "9c0d1e2f-0000-4000-8000-000000000002",
            "nombre": "recibo.pdf",
            "subido_en": "2026-10-12T09:30:00-05:00",
            "del_residente": False,
            "subido_por": "Andrés Gómez",
        },
    ],
}
APARTADA_PARA_GESTION = {
    **EN_TRAMITE,
    "estado": "APARTADA",
    "estado_nombre": "Apartada",
    "residente": {"id": RESIDENTE_ID, "nombre": "Pedro Gómez"},
    "unidad": {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
    "motivo": "Cumpleaños",
    "asistentes": 20,
    "motivo_decision": "",
    "decidida_por": None,
    "decidida_en": None,
    "pago": SIN_PAGO,
}
ADMINISTRACION = ["area.ver", "reserva.ver_todas", "reserva.aprobar", "reserva.rechazar", "reserva.declarar_pago"]
SECRETARIA = ["area.ver", "reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]
FRASE_DEL_PAGO = (
    "Vas a declarar que recibiste el pago de la reserva de Pedro Gómez (Torre 1 – 101) en Salón comunal, "
    "el sábado 26 de diciembre de 2026, de 2:00 p. m. a 6:00 p. m."
)
URL_DE_LA_ZONA = f"/reservas/areas/{SALON['id']}/solicitudes/"


def ver_zona(solicitudes, permisos=ADMINISTRACION, **sesion):
    with (
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=solicitudes),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        return cliente_con_sesion(permisos=permisos, **sesion).get(URL_DE_LA_ZONA).content.decode()


def test_la_regla_de_renta_de_la_zona_se_precarga_al_revisar_una_solicitud():
    condiciones = "No se permiten fiestas después de las 10 p. m."
    area = {**SALON, "condiciones_alquiler": condiciones}
    with (
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=[APARTADA_PARA_GESTION]),
        mock.patch("cliente_api.areas.listar", return_value=[area]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(URL_DE_LA_ZONA).content.decode()

    assert f">{condiciones}</textarea>" in html
    assert "Motivo de la decisión o condiciones del alquiler" in html


def test_la_tarjeta_dice_que_el_dinero_lo_valida_una_persona_y_que_el_pago_no_esta_declarado():
    html = ver_zona([APARTADA_PARA_GESTION])

    assert AVISO_DEL_DINERO in html
    assert 'role="note"' in html
    assert ">Sin pago declarado</span>" in html
    assert "Todavía no hay comprobantes." in html


def test_la_tarjeta_muestra_quien_declaro_cuando_y_cada_comprobante_con_quien_lo_subio():
    html = ver_zona([{**APARTADA_PARA_GESTION, "estado": "RESERVADA", "estado_nombre": "Reservada", "pago": PAGO_DECLARADO}])

    assert ">Pago declarado</span>" in html
    assert "Declarado por Andrés Gómez" in html
    assert "lunes 12 de octubre de 2026" in html and "09:30" in html
    assert f'href="/reservas/comprobantes/{COMPROBANTE_ID}/" target="_blank" rel="noopener">transferencia.png</a>' in html
    assert "subido por Pedro Gómez" in html and "subido por Andrés Gómez" in html
    # Con el pago ya declarado no se ofrece declararlo otra vez.
    assert ">Declarar pago recibido</button>" not in html


def test_administracion_ve_el_formulario_con_la_frase_completa_y_secretaria_no():
    de_administracion = ver_zona([APARTADA_PARA_GESTION])
    de_secretaria = ver_zona([APARTADA_PARA_GESTION], permisos=SECRETARIA, tipo_usuario="Secretaría")

    assert FRASE_DEL_PAGO in de_administracion
    assert ">Declarar pago recibido</button>" in de_administracion
    assert 'enctype="multipart/form-data"' in de_administracion and 'name="archivo"' in de_administracion
    assert f'action="/reservas/solicitudes/{EN_TRAMITE["id"]}/pago/"' in de_administracion
    assert AVISO_DEL_DINERO in de_secretaria and ">Sin pago declarado</span>" in de_secretaria
    assert "Declarar pago recibido" not in de_secretaria and "Vas a declarar" not in de_secretaria
    # La decisión de aprobar o rechazar sigue siendo de las dos.
    assert 'name="decision" value="RESERVADA">Aceptar</button>' in de_secretaria


def test_una_rechazada_con_pago_declarado_lo_conserva_y_no_ofrece_declarar():
    html = ver_zona([{**APARTADA_PARA_GESTION, "estado": "RECHAZADA", "estado_nombre": "Rechazada", "pago": PAGO_DECLARADO}])

    assert ">Pago declarado</span>" in html
    assert ">Retirar la declaración</button>" in html
    assert ">Declarar pago recibido</button>" not in html


def test_las_pantallas_de_gestion_del_pago_no_cargan_javascript():
    html = ver_zona([APARTADA_PARA_GESTION])

    assert "alpine" not in html and "reservas.js" not in html


def test_declarar_con_archivo_lo_manda_a_la_api_y_vuelve_a_la_zona():
    comprobante = SimpleUploadedFile("pago.pdf", b"%PDF-1.7 contenido", content_type="application/pdf")
    recibido = {}

    def como_la_api(request, solicitud_id, archivo):
        # El archivo se cierra al terminar la petición: se lee aquí, mientras la API «lo recibe».
        recibido.update(solicitud=str(solicitud_id), nombre=archivo.name, contenido=archivo.read())

    with mock.patch("cliente_api.reservas.declarar_pago", side_effect=como_la_api):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/", {"area": SALON["id"], "archivo": comprobante}
        )

    assert recibido == {"solicitud": EN_TRAMITE["id"], "nombre": "pago.pdf", "contenido": b"%PDF-1.7 contenido"}
    assert respuesta["Location"] == f"{URL_DE_LA_ZONA}?pago=declarado"


def test_declarar_sin_archivo_tambien_se_puede():
    with mock.patch("cliente_api.reservas.declarar_pago") as declarar:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/", {"area": SALON["id"]}
        )

    assert declarar.call_args.args[2] is None
    assert respuesta.status_code == 302


def test_al_volver_dice_que_el_pago_quedo_declarado():
    with (
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=[APARTADA_PARA_GESTION]),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"{URL_DE_LA_ZONA}?pago=declarado").content.decode()

    assert "El pago quedó declarado." in html


@pytest.mark.parametrize(
    "error, texto",
    [
        (
            ErrorDeApi(400, {"archivo": ["El comprobante debe ser un PDF o una imagen JPG o PNG."]}),
            "El comprobante debe ser un PDF o una imagen JPG o PNG.",
        ),
        (
            ErrorDeApi(409, {"detail": "El pago de esta solicitud ya está declarado."}),
            "El pago de esta solicitud ya está declarado.",
        ),
        (ErrorDeApi(403, {"detail": "No tienes permiso para hacer esto."}), "No tienes permiso para hacer esto"),
    ],
)
def test_un_error_de_la_api_al_declarar_se_muestra_arriba_de_las_tarjetas(error, texto):
    with (
        mock.patch("cliente_api.reservas.declarar_pago", side_effect=error),
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=[APARTADA_PARA_GESTION]),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/", {"area": SALON["id"]}
        ).content.decode()

    assert texto in html
    assert html.index(texto) < html.index('class="am-tarjeta')


def test_retirar_la_declaracion_exige_motivo():
    with (
        mock.patch("cliente_api.reservas.retirar_pago") as retirar,
        mock.patch("cliente_api.reservas.solicitudes_del_area", return_value=[APARTADA_PARA_GESTION]),
        mock.patch("cliente_api.areas.listar", return_value=[SALON]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/retirar/", {"area": SALON["id"], "motivo": "   "}
        ).content.decode()

    retirar.assert_not_called()
    assert "Escribe el motivo para retirar la declaración del pago." in html


def test_retirar_con_motivo_lo_manda_a_la_api_y_vuelve_a_la_zona():
    with mock.patch("cliente_api.reservas.retirar_pago") as retirar:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/retirar/",
            {"area": SALON["id"], "motivo": "Era otra solicitud."},
        )

    assert str(retirar.call_args.args[1]) == EN_TRAMITE["id"]
    assert retirar.call_args.args[2] == "Era otra solicitud."
    assert respuesta["Location"] == f"{URL_DE_LA_ZONA}?pago=retirado"


def test_un_area_que_no_es_un_identificador_no_tiene_a_donde_volver():
    respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
        f"/reservas/solicitudes/{EN_TRAMITE['id']}/pago/", {"area": "no-es-un-uuid"}
    )

    assert respuesta.status_code == 404


def test_la_vista_del_comprobante_devuelve_el_archivo_con_su_tipo():
    with mock.patch("cliente_api.reservas.comprobante", return_value=(b"\x89PNG\r\n\x1a\n", "image/png")) as pedir:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/reservas/comprobantes/{COMPROBANTE_ID}/")

    assert str(pedir.call_args.args[1]) == COMPROBANTE_ID
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "image/png"
    assert respuesta["Content-Disposition"] == 'inline; filename="comprobante.png"'
    assert respuesta["X-Content-Type-Options"] == "nosniff"
    assert respuesta.content == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize(
    "falla, devuelve",
    [
        (ErrorDeApi(404, {"detail": "No encontrado."}), None),
        (ApiNoDisponible(), None),
        (None, (b"<html>no soy un comprobante</html>", "text/html")),
    ],
)
def test_si_la_api_no_lo_entrega_o_no_es_un_comprobante_responde_404(falla, devuelve):
    with mock.patch("cliente_api.reservas.comprobante", side_effect=falla, return_value=devuelve):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/reservas/comprobantes/{COMPROBANTE_ID}/")

    assert respuesta.status_code == 404


# El residente: ve el pago de su solicitud y sube su comprobante, sin poder declararlo (HU-16)


def test_el_detalle_de_una_apartada_dice_que_no_hay_pago_declarado_y_ofrece_subir_el_comprobante():
    html = ver_solicitud(estado="APARTADA", estado_nombre="Apartada", pago=SIN_PAGO)

    assert AVISO_DEL_DINERO in html
    assert ">Sin pago declarado</span>" in html
    assert 'enctype="multipart/form-data"' in html and 'name="archivo"' in html
    assert f'action="/reservas/solicitudes/{EN_TRAMITE["id"]}/comprobantes/"' in html
    assert "Subir el comprobante no confirma el pago: lo declara la administración cuando lo verifique." in html
    assert ">Subir comprobante</button>" in html


def test_la_pantalla_del_residente_no_tiene_ningun_control_para_declarar_el_pago():
    for estado, nombre in (("APARTADA", "Apartada"), ("RESERVADA", "Reservada")):
        html = ver_solicitud(estado=estado, estado_nombre=nombre, pago=SIN_PAGO)

        assert "Declarar pago recibido" not in html and "Retirar la declaración" not in html
        assert "/pago/" not in html
        assert 'name="decision"' not in html
    assert "alpine" not in html


def test_con_el_pago_declarado_el_residente_lo_ve_sin_el_nombre_y_ya_no_sube_mas():
    # La API no manda `declarado_por` al residente; aun si llegara, la plantilla no lo escribe.
    html = ver_solicitud(estado="RESERVADA", estado_nombre="Reservada", pago=PAGO_DECLARADO)

    assert ">Pago declarado</span>" in html
    assert "Pago declarado por la administración" in html and "12 de octubre de 2026" in html
    assert "Andrés" not in html and "Pedro Gómez" not in html
    assert "subido por ti" in html and "subido por la administración" in html
    assert 'name="archivo"' not in html and ">Subir comprobante</button>" not in html


def test_con_el_maximo_de_comprobantes_no_se_ofrece_subir_otro():
    tres = [{**PAGO_DECLARADO["comprobantes"][0], "id": f"9c0d1e2f-0000-4000-8000-00000000010{n}"} for n in range(3)]

    html = ver_solicitud(estado="APARTADA", estado_nombre="Apartada", pago={**SIN_PAGO, "comprobantes": tres})

    assert html.count("transferencia.png</a>") == 3
    assert ">Subir comprobante</button>" not in html


def test_una_rechazada_sin_pago_no_muestra_el_bloque_y_con_pago_declarado_si():
    sin_pago = ver_solicitud(estado="RECHAZADA", estado_nombre="Rechazada", pago=SIN_PAGO)
    con_pago = ver_solicitud(estado="RECHAZADA", estado_nombre="Rechazada", pago=PAGO_DECLARADO)

    assert "Sin pago declarado" not in sin_pago and AVISO_DEL_DINERO not in sin_pago
    assert ">Pago declarado</span>" in con_pago
    assert ">Subir comprobante</button>" not in con_pago


def test_subir_el_comprobante_lo_manda_a_la_api_y_vuelve_a_la_solicitud():
    foto = SimpleUploadedFile("transferencia.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    with mock.patch("cliente_api.reservas.subir_comprobante") as subir:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/comprobantes/", {"archivo": foto}
        )

    assert str(subir.call_args.args[1]) == EN_TRAMITE["id"]
    assert subir.call_args.args[2].name == "transferencia.png"
    assert respuesta["Location"] == f"/reservas/solicitudes/{EN_TRAMITE['id']}/"


@pytest.mark.parametrize(
    "error, texto",
    [
        (ErrorDeApi(400, {"archivo": ["El comprobante no puede pesar más de 5 MB."]}), "El comprobante no puede pesar más de 5 MB."),
        (
            ErrorDeApi(409, {"detail": "El pago ya está declarado por la administración: no se pueden subir más comprobantes."}),
            "El pago ya está declarado por la administración: no se pueden subir más comprobantes.",
        ),
    ],
)
def test_un_error_de_la_api_al_subir_se_muestra_dentro_del_bloque_del_pago(error, texto):
    foto = SimpleUploadedFile("grande.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    apartada = {**EN_TRAMITE, "estado": "APARTADA", "estado_nombre": "Apartada", "pago": SIN_PAGO}
    with (
        mock.patch("cliente_api.reservas.subir_comprobante", side_effect=error),
        mock.patch("cliente_api.reservas.obtener", return_value=apartada),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/comprobantes/", {"archivo": foto}
        ).content.decode()

    assert texto in html
    assert html.index(AVISO_DEL_DINERO) < html.index(texto) < html.index(">Subir comprobante</button>")


def test_subir_sin_elegir_archivo_lo_dice_y_no_llama_a_la_api():
    apartada = {**EN_TRAMITE, "estado": "APARTADA", "estado_nombre": "Apartada", "pago": SIN_PAGO}
    with (
        mock.patch("cliente_api.reservas.subir_comprobante") as subir,
        mock.patch("cliente_api.reservas.obtener", return_value=apartada),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).post(
            f"/reservas/solicitudes/{EN_TRAMITE['id']}/comprobantes/"
        ).content.decode()

    subir.assert_not_called()
    assert "Elige el archivo del comprobante." in html
