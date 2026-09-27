"""Pantallas de reservas (HU-11): franjas del día, tomar el bloqueo y la solicitud en trámite. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

SALON = {"id": "3c4d5e6f-0000-4000-8000-000000000001", "nombre": "Salón comunal", "activo": True}
FRANJAS = {
    "area": {"id": SALON["id"], "nombre": "Salón comunal"},
    "fecha": "2026-12-26",
    "franjas": [
        {"hora_inicio": "08:00", "hora_fin": "12:00", "estado": "libre"},
        {"hora_inicio": "12:00", "hora_fin": "16:00", "estado": "en_solicitud"},
        {"hora_inicio": "16:00", "hora_fin": "20:00", "estado": "apartada"},
        {"hora_inicio": "20:00", "hora_fin": "22:00", "estado": "propia"},
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
    for texto in ("Libre", "En trámite", "Apartada", "Tuya"):
        assert f"{texto}</span>" in html
    assert "sábado 26 de diciembre de 2026" in html
    assert html.count(">Reservar</button>") == 1
    assert "Maqueta" not in html


def test_sin_reserva_solicitar_no_se_ofrece_reservar():
    html, _ = ver_franjas(permisos=["area.ver", "reserva.ver_todas"])

    assert "Libre</span>" in html
    assert "Reservar</button>" not in html


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
