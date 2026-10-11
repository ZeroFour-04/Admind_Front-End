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


def test_pestana_solicitudes_muestra_zonas_comunes_con_solo_la_accion_solicitudes():
    permisos = ["area.ver", "reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]
    areas = [
        {
            "id": RESERVA["area"]["id"],
            "nombre": "Salón comunal",
            "hora_apertura": "08:00",
            "hora_cierre": "22:00",
            "duracion_franja_minutos": 240,
            "aforo_maximo": 50,
            "activo": True,
            "en_mantenimiento": False,
        }
    ]
    with mock.patch("cliente_api.areas.listar", return_value=areas) as listar:
        html = cliente_con_sesion(permisos=permisos).get("/solicitudes/").content.decode()

    listar.assert_called_once()
    assert "Salón comunal" in html
    assert "08:00 a 22:00" in html
    assert "aforo 50" in html
    assert html.count(f'href="/reservas/areas/{RESERVA["area"]["id"]}/solicitudes/"') == 1
    assert ">Editar</a>" not in html
    assert ">Desactivar</button>" not in html
    assert "Pedro Gómez" not in html


def test_administracion_secretaria_y_superusuario_ven_todas_las_zonas_con_su_accion():
    areas = [
        {
            "id": RESERVA["area"]["id"],
            "nombre": "Salón comunal",
            "hora_apertura": "08:00",
            "hora_cierre": "22:00",
            "duracion_franja_minutos": 240,
            "aforo_maximo": 50,
            "activo": True,
            "en_mantenimiento": False,
        },
        {
            "id": "3c4d5e6f-0000-4000-8000-000000000002",
            "nombre": "Piscina",
            "hora_apertura": "06:00",
            "hora_cierre": "20:00",
            "duracion_franja_minutos": 120,
            "aforo_maximo": 30,
            "activo": True,
            "en_mantenimiento": True,
        },
    ]
    roles_y_permisos = [
        ("Administrador", ["reserva.ver_todas", "reserva.aprobar", "reserva.rechazar"]),
        ("Secretaría", ["reserva.ver_todas"]),
        ("Superusuario", ["reserva.ver_todas"]),
    ]

    for rol, permisos in roles_y_permisos:
        with mock.patch("cliente_api.areas.listar", return_value=areas):
            html = cliente_con_sesion(permisos=permisos, tipo_usuario=rol).get("/solicitudes/").content.decode()

        assert "Salón comunal" in html and "Piscina" in html
        assert html.count('href="/reservas/areas/') == 2
        assert html.count(">En mantenimiento</span>") == 1
        assert html.count(">Disponible</span>") == 1
        assert ">Editar</a>" not in html
        assert ">Desactivar</button>" not in html


def test_pestana_solicitudes_muestra_estado_vacio_si_no_hay_areas():
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        html = cliente_con_sesion(permisos=["area.ver", "reserva.ver_todas"]).get("/solicitudes/").content.decode()

    assert "Todavía no hay zonas comunes" in html


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


def test_el_historial_enlaza_al_detalle_y_dice_si_el_pago_esta_declarado():
    declarado = {"declarado": True, "declarado_en": "2026-10-12T09:30:00-05:00", "comprobantes": []}
    propias = [
        {**RESERVA, "estado": "APARTADA", "estado_nombre": "Apartada", "motivo_decision": ""},
        {
            **RESERVA,
            "id": "6f7a8b9c-0000-4000-8000-000000000002",
            "estado": "RESERVADA",
            "estado_nombre": "Reservada",
            "pago": declarado,
        },
        {
            **RESERVA,
            "id": "6f7a8b9c-0000-4000-8000-000000000003",
            "estado": "RECHAZADA",
            "estado_nombre": "Rechazada",
            "pago": declarado,
        },
    ]
    with mock.patch("cliente_api.reservas.mis_solicitudes", return_value=propias):
        html = cliente_con_sesion(permisos=["area.ver", "reserva.solicitar"]).get("/solicitudes/").content.decode()

    for solicitud in propias:
        assert f'href="/reservas/solicitudes/{solicitud["id"]}/"' in html
    assert html.count(">Ver solicitud</a>") == 3
    # La pastilla del pago solo va en las que siguen en pie.
    assert html.count(">Sin pago declarado</span>") == 1
    assert html.count(">Pago declarado</span>") == 1
    assert "Declarar pago recibido" not in html and "/pago/" not in html


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
