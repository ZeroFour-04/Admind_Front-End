"""La bandeja general de Solicitudes muestra el estado y comentario de las reservas."""
from datetime import date
from unittest import mock

import pytest

from cliente_api.http import ApiNoDisponible, ErrorDeApi
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


GESTION = ["solicitud.bandeja_ver", "reserva.ver_todas", "caso.ver_todos"]
HOY = date(2026, 10, 6)
PENDIENTE = {
    **RESERVA,
    "estado": "APARTADA",
    "estado_nombre": "Apartada",
    "motivo_decision": "",
    "decidida_por": None,
    "decidida_en": None,
    "creada_en": "2026-10-01T08:57:00-05:00",
    "enviada_en": "2026-10-01T09:00:00-05:00",
    "completada": False,
    "pago": {"declarado": False, "declarado_en": None, "declarado_por": None, "comprobantes": []},
}
APROBADA = {
    **PENDIENTE,
    "id": "9a1b2c3d-0000-4000-8000-000000000002",
    "estado": "RESERVADA",
    "estado_nombre": "Reservada",
    "enviada_en": "2026-10-05T16:00:00-05:00",
    "pago": {**PENDIENTE["pago"], "declarado": True},
}
CASO = {
    "id": "c0ffee00-0000-4000-8000-000000000001",
    "titulo": "Fuga de agua",
    "cuerpo": "Hay una fuga en el pasillo.",
    "estado": "ABIERTO",
    "prioridad": "URGENTE",
    "autor": "Lucía Pérez",
    "apartamento": "Torre 2 – 304",
    "creado_en": "2026-10-05T11:00:00-05:00",
    "cerrado_en": None,
}
RESUELTO = {
    **CASO,
    "id": "deadbe00-0000-4000-8000-000000000002",
    "titulo": "Ruido en la noche",
    "estado": "RESUELTO",
    "prioridad": "NORMAL",
    "cerrado_en": "2026-10-05T18:00:00-05:00",
}


def abrir_dashboard(consulta="", permisos=GESTION, reservas=(PENDIENTE, APROBADA), casos=(CASO, RESUELTO)):
    """El dashboard con la API simulada y el día fijo, para que la antigüedad no dependa de cuándo se corre."""
    with (
        mock.patch("cliente_api.reservas.solicitudes_para_bandeja", return_value=list(reservas)) as de_reservas,
        mock.patch("cliente_api.casos.listar", return_value=list(casos)) as de_casos,
        mock.patch("apps.triage.views.timezone.localdate", return_value=HOY),
    ):
        html = cliente_con_sesion(permisos=permisos).get(f"/solicitudes/{consulta}").content.decode()
    return html, de_reservas, de_casos


def test_gestion_ve_el_dashboard_con_tres_pestanas_y_cuantas_hay_pendientes():
    html, _, _ = abrir_dashboard()

    assert "<h1>Dashboard de Gestión de Reservas</h1>" in html
    assert "Maqueta con datos de ejemplo" not in html
    assert 'aria-label="Tipos de solicitud"' in html
    assert '<span class="am-pestana am-es-activa" aria-current="page">Reservas <span class="tablero__cuenta">1<' in html
    assert '<a class="am-pestana" href="/solicitudes/?pestana=casos">Casos <span class="tablero__cuenta">1<' in html
    assert '<a class="am-pestana" href="/solicitudes/?pestana=citas">Citas</a>' in html
    # La pantalla no carga JavaScript: pestañas y filtros son enlaces.
    assert "alpine" not in html.lower()


def test_la_pestana_reservas_es_una_tabla_con_la_fila_enlazada_a_la_tarjeta():
    html, _, _ = abrir_dashboard()

    for columna in ("ID", "Zona", "Día y franja", "Estado", "Residente", "Vivienda", "Solicitada", "Pago"):
        assert f'<th scope="col">{columna}</th>' in html
    assert "Prioridad" not in html  # entre reservas manda el orden de llegada
    enlace = f'/reservas/areas/{RESERVA["area"]["id"]}/solicitudes/#solicitud-{PENDIENTE["id"]}'
    assert f'<a class="tabla-solicitudes__enlace" href="{enlace}">RES-6F7A8B</a>' in html
    assert "Salón comunal" in html and "Pedro Gómez" in html and "Torre 1 – 101" in html
    assert "Sábado 26 de diciembre" in html and "14:00 a 18:00" in html
    assert 'am-pastilla--tramite">En revisión</span>' in html
    assert "01/10/2026" in html and "hace 5 días" in html
    assert 'am-pastilla--neutro">Sin declarar</span>' in html
    # Por defecto, solo las que esperan decisión.
    assert "RES-9A1B2C" not in html
    assert 'class="tablero__opcion tablero__opcion--activa" href="/solicitudes/?pestana=reservas&amp;ver=pendientes"' in html


def test_ver_todas_trae_las_decididas_y_una_franja_que_ya_paso_sale_completada():
    completada = {**APROBADA, "id": "5e5e5e00-0000-4000-8000-000000000003", "completada": True}
    rechazada = {**PENDIENTE, "id": "7d7d7d00-0000-4000-8000-000000000004", "estado": "RECHAZADA"}

    html, _, _ = abrir_dashboard("?ver=todas", reservas=(PENDIENTE, APROBADA, completada, rechazada))

    assert "RES-6F7A8B" in html and "RES-9A1B2C" in html
    assert 'am-pastilla--confirmado">Aprobada</span>' in html
    assert 'am-pastilla--neutro">Completada</span>' in html
    assert 'am-pastilla--error">Rechazada</span>' in html
    assert 'am-pastilla--confirmado">Declarado</span>' in html
    assert "hace 1 día" in html
    assert "No aplica" in html  # una rechazada no tiene pago que declarar


def test_la_pestana_casos_trae_estado_prioridad_y_antiguedad_y_enlaza_al_detalle():
    html, _, de_casos = abrir_dashboard("?pestana=casos")

    assert de_casos.call_args.kwargs == {"orden": "prioridad"}
    assert '<span class="am-pestana am-es-activa" aria-current="page">Casos' in html
    for columna in ("ID", "Asunto", "Estado", "Prioridad", "Residente", "Vivienda", "Creado"):
        assert f'<th scope="col">{columna}</th>' in html
    assert f'<a class="tabla-solicitudes__enlace" href="/casos/{CASO["id"]}/">CAS-C0FFEE</a>' in html
    assert "Fuga de agua" in html and "Lucía Pérez" in html and "Torre 2 – 304" in html
    assert 'am-pastilla--neutro">Por revisar</span>' in html
    assert 'am-pastilla--error">Urgente</span>' in html
    assert "05/10/2026" in html and "hace 1 día" in html
    # Por defecto, solo los abiertos.
    assert "Ruido en la noche" not in html


def test_los_casos_se_pueden_ver_todos_y_por_antiguedad_sin_perder_la_columna():
    html, _, de_casos = abrir_dashboard("?pestana=casos&ver=todos&orden=antiguedad")

    assert de_casos.call_args.kwargs == {"orden": "antiguedad"}
    assert "Ruido en la noche" in html and 'am-pastilla--confirmado">Resuelto</span>' in html
    assert '<th scope="col">Creado</th>' in html and "hace 1 día" in html
    assert 'tablero__opcion--activa" href="/solicitudes/?pestana=casos&amp;ver=todos&amp;orden=antiguedad"' in html
    assert 'href="/solicitudes/?pestana=casos&amp;ver=todos&amp;orden=prioridad"' in html


def test_la_pestana_citas_dice_que_todavia_no_esta_disponible():
    html, _, _ = abrir_dashboard("?pestana=citas")

    assert '<span class="am-pestana am-es-activa" aria-current="page">Citas</span>' in html
    assert "Las citas todavía no están disponibles" in html
    assert "<table" not in html and "<button" not in html.split('class="vista"')[-1]


def test_sin_permiso_de_casos_no_hay_pestana_casos():
    html, _, de_casos = abrir_dashboard("?pestana=casos", permisos=["solicitud.bandeja_ver", "reserva.ver_todas"])

    de_casos.assert_not_called()
    assert "pestana=casos" not in html
    assert '<span class="am-pestana am-es-activa" aria-current="page">Reservas' in html


def test_quien_no_entra_al_dashboard_no_ve_las_solicitudes_de_nadie():
    """Vigilancia ve franjas, pero la bandeja es de quien tiene `solicitud.bandeja_ver`."""
    html, de_reservas, de_casos = abrir_dashboard(permisos=["reserva.ver_todas"])

    de_reservas.assert_not_called()
    de_casos.assert_not_called()
    assert "No tienes acceso a solicitudes de reserva" in html
    assert "Dashboard de Gestión de Reservas" not in html and "Pedro Gómez" not in html


def test_si_la_api_falla_el_dashboard_lo_dice_y_conserva_las_pestanas():
    with (
        mock.patch("cliente_api.reservas.solicitudes_para_bandeja", side_effect=ApiNoDisponible()),
        mock.patch("cliente_api.casos.listar", return_value=[CASO]),
    ):
        html = cliente_con_sesion(permisos=GESTION).get("/solicitudes/").content.decode()

    assert 'role="alert"' in html
    assert 'href="/solicitudes/?pestana=casos">Casos' in html
    assert "<table" not in html


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
        {
            **RESERVA,
            "id": "6f7a8b9c-0000-4000-8000-000000000004",
            "estado": "EN_SOLICITUD",
            "estado_nombre": "En trámite",
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
    assert html.count("Salón comunal") == 4
    assert 'class="am-pastilla am-pastilla--confirmado">Aceptado</span>' in html
    assert 'class="am-pastilla am-pastilla--error">Rechazado</span>' in html
    assert html.count('class="am-pastilla am-pastilla--tramite">En progreso</span>') == 2
    assert 'href="/casos/">Casos</a>' in html
    assert '<span class="am-pestana am-es-activa" aria-current="page">Reservas</span>' in html
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


# HU-22: filtros por pestaña


FILTROS_DE_RESERVAS = [
    {},
    {"estado": "APARTADA"},
    {"area": "3c4d5e6f-0000-4000-8000-000000000001"},
    {"vivienda": "7a1b2c3d-0000-4000-8000-000000000101"},
    {"solicitante": "Pedro"},
    {"desde": "2026-10-01", "hasta": "2026-10-06"},
]
FILTROS_DE_CASOS = [
    {},
    {"estado": "ABIERTO"},
    {"prioridad": "URGENTE"},
    {"solicitante": "Lucía"},
    {"desde": "2026-10-01", "hasta": "2026-10-06"},
]


def con_filtros(pestana, filtros):
    return f"?pestana={pestana}&ver=todas&" + "&".join(f"{clave}={valor}" for clave, valor in filtros.items())


@pytest.mark.parametrize("filtros", FILTROS_DE_RESERVAS)
def test_hu22_con_cualquier_filtro_la_antiguedad_sigue_visible_en_reservas(filtros):
    html, de_reservas, _ = abrir_dashboard(con_filtros("reservas", filtros))

    assert "<th scope=\"col\">Solicitada</th>" in html
    assert "hace 5 días" in html and "hace 1 día" in html
    if filtros:
        de_reservas.assert_called_with(mock.ANY, **filtros)


@pytest.mark.parametrize("filtros", FILTROS_DE_CASOS)
def test_hu22_con_cualquier_filtro_la_antiguedad_sigue_visible_en_casos(filtros):
    html, _, de_casos = abrir_dashboard(con_filtros("casos", filtros).replace("ver=todas", "ver=todos"))

    assert "<th scope=\"col\">Creado</th>" in html
    assert "hace 1 día" in html
    if filtros:
        de_casos.assert_called_with(mock.ANY, orden="prioridad", **filtros)


def test_hu22_la_bandeja_no_tiene_aprobar_responder_ni_exportar():
    for pestana in ("reservas", "casos", "citas"):
        html, _, _ = abrir_dashboard(f"?pestana={pestana}&ver=todas")
        minusculas = html.lower()

        assert not any(palabra in minusculas for palabra in ("aprobar", "responder", "exportar", "descargar"))
        # El único formulario que escribe es el de salir de la sesión, que es de la barra y no de la bandeja.
        assert minusculas.count('method="post"') == 1 and 'action="/salir/"' in minusculas


def test_hu22_cada_pestana_tiene_su_formulario_de_filtros_y_reservas_no_tiene_prioridad():
    reservas, _, _ = abrir_dashboard("?pestana=reservas")
    casos, _, _ = abrir_dashboard("?pestana=casos")

    assert 'name="vivienda"' in reservas and 'name="area"' in reservas and 'name="prioridad"' not in reservas
    assert 'name="prioridad"' in casos and 'name="vivienda"' not in casos
    # Las zonas y viviendas del selector salen de las filas de la bandeja, sin otra petición.
    assert '<option value="3c4d5e6f-0000-4000-8000-000000000001">Salón comunal</option>' in reservas
    assert ">Torre 1 – 101</option>" in reservas


def test_hu22_los_filtros_viajan_en_la_url_y_los_enlaces_los_conservan():
    html, _, _ = abrir_dashboard("?pestana=casos&prioridad=URGENTE&solicitante=Luc%C3%ADa")

    assert 'value="Lucía"' in html and '<option value="URGENTE" selected>Urgente</option>' in html
    assert "prioridad=URGENTE" in html and "Quitar filtros" in html
    # El enlace de «Por antigüedad» no pierde los filtros.
    assert any("orden=antiguedad" in enlace and "prioridad=URGENTE" in enlace for enlace in html.split('href="'))


def test_hu22_con_un_estado_elegido_pendientes_y_todas_desaparecen():
    con_estado, _, _ = abrir_dashboard("?pestana=reservas&estado=RESERVADA")
    sin_estado, _, _ = abrir_dashboard("?pestana=reservas")

    assert "Pendientes" not in con_estado and "Aprobada" in con_estado
    assert "Pendientes" in sin_estado


def test_hu22_un_filtro_invalido_se_muestra_como_error_y_no_como_tabla_vacia():
    def solo_sin_filtros(request, **filtros):
        if filtros:
            raise ErrorDeApi(400, {"desde": ["Introduzca una fecha válida."]})
        return [PENDIENTE]

    with (
        mock.patch("cliente_api.reservas.solicitudes_para_bandeja", side_effect=solo_sin_filtros),
        mock.patch("cliente_api.casos.listar", return_value=[CASO]),
        mock.patch("apps.triage.views.timezone.localdate", return_value=HOY),
    ):
        html = cliente_con_sesion(permisos=GESTION).get("/solicitudes/?pestana=reservas&desde=ayer").content.decode()

    assert "Introduzca una fecha válida." in html
    assert "Ningún resultado" not in html and "Todavía no hay solicitudes" not in html
    assert 'value="ayer"' in html


def test_hu22_sin_resultados_con_filtros_lo_dice_distinto_a_no_haber_nada():
    html, _, _ = abrir_dashboard("?pestana=casos&prioridad=BAJA", casos=())

    assert "Ningún resultado con estos filtros" in html
    assert "Todavía no hay casos" not in html


def test_hu22_las_cuentas_de_las_pestanas_salen_de_la_lista_sin_filtrar():
    sin_filtro, _, _ = abrir_dashboard("?pestana=casos")
    filtrado, _, de_casos = abrir_dashboard("?pestana=casos&estado=RESUELTO")

    assert sin_filtro.count('class="tablero__cuenta"') == filtrado.count('class="tablero__cuenta"')
    assert de_casos.call_count == 2
