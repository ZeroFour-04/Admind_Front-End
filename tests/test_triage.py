"""La bandeja general de Solicitudes muestra el estado y comentario de las reservas."""
from unittest import mock

from tests.ayudantes import cliente_con_sesion


RESERVA = {
    "id": "6f7a8b9c-0000-4000-8000-000000000001",
    "area": {"id": "3c4d5e6f-0000-4000-8000-000000000001", "nombre": "Salón comunal"},
    "residente": {"id": "8a9b0c1d-0000-4000-8000-000000000001", "nombre": "Pedro Gómez"},
    "fecha": "2026-12-26",
    "hora_inicio": "14:00",
    "hora_fin": "18:00",
    "estado": "RESERVADA",
    "estado_nombre": "Reservada",
    "unidad": {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
    "motivo": "Celebración familiar",
    "asistentes": 20,
    "observaciones": "",
    "motivo_decision": "Horario confirmado.",
    "decidida_por": {"id": "7b1c2d3e-0000-4000-8000-000000000001", "nombre": "Ana Admin"},
    "decidida_en": "2026-10-05T10:00:00-05:00",
}


def test_pestana_solicitudes_muestra_estado_comentario_y_residente():
    permisos = ["reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]
    with mock.patch("cliente_api.reservas.solicitudes_para_bandeja", return_value=[RESERVA]) as listar:
        html = cliente_con_sesion(permisos=permisos).get("/solicitudes/").content.decode()

    listar.assert_called_once()
    assert "Salón comunal" in html
    assert "Pedro Gómez" in html
    assert "Reservada" in html
    assert "Horario confirmado." in html
    assert "Ana Admin" in html


def test_pestana_solicitudes_muestra_comentario_de_rechazo():
    rechazada = {
        **RESERVA,
        "estado": "RECHAZADA",
        "estado_nombre": "Rechazada",
        "motivo_decision": "Falta la autorización del conjunto.",
    }
    with mock.patch("cliente_api.reservas.solicitudes_para_bandeja", return_value=[rechazada]):
        html = cliente_con_sesion(permisos=["reserva.ver_todas"]).get("/solicitudes/").content.decode()

    assert "Rechazada" in html
    assert "Falta la autorización del conjunto." in html


def test_residente_ve_su_historial_con_estados_y_comentarios():
    propias = [
        {**RESERVA, "estado": "RESERVADA", "estado_nombre": "Reservada"},
        {
            **RESERVA,
            "id": "6f7a8b9c-0000-4000-8000-000000000002",
            "estado": "RECHAZADA",
            "estado_nombre": "Rechazada",
            "motivo_decision": "Falta autorización.",
        },
        {
            **RESERVA,
            "id": "6f7a8b9c-0000-4000-8000-000000000003",
            "estado": "APARTADA",
            "estado_nombre": "Apartada",
            "motivo_decision": "",
        },
    ]
    with (
        mock.patch("cliente_api.reservas.mis_solicitudes", return_value=propias) as propias_api,
        mock.patch("cliente_api.reservas.solicitudes_para_bandeja") as todas_api,
    ):
        html = cliente_con_sesion(permisos=["area.ver", "reserva.solicitar"]).get("/solicitudes/").content.decode()

    propias_api.assert_called_once()
    todas_api.assert_not_called()
    assert html.count("Salón comunal") == 3
    assert ">Aprobada</span>" in html
    assert ">Rechazada</span>" in html
    assert ">En revisión</span>" in html
    assert "Horario confirmado." in html
    assert "Falta autorización." in html
    assert "Ver solicitudes de esta zona" not in html


def test_solicitud_del_residente_muestra_resultado_y_comentario():
    from tests.test_reservas import ver_solicitud

    html = ver_solicitud(
        **{
            "estado": "RECHAZADA",
            "estado_nombre": "Rechazada",
            "motivo_decision": "No se adjuntó el soporte.",
        }
    )

    assert "Tu solicitud fue rechazada." in html
    assert "Comentario de la administración: No se adjuntó el soporte." in html
