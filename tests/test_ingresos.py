"""Pantalla de ingreso a zonas (plan de zonas con ingreso, F7): Vigilancia registra, Administración consulta. La API se simula."""
from unittest import mock

from cliente_api.http import ApiNoDisponible, ErrorDeApi
from tests.ayudantes import cliente_con_sesion

GIMNASIO = {
    "id": "3c4d5e6f-0000-4000-8000-000000000009",
    "nombre": "Gimnasio",
    "descripcion": "",
    "hora_apertura": "05:00",
    "hora_cierre": "22:00",
    "modo_uso": "ingreso",
    "duracion_franja_minutos": None,
    "permanencia_maxima_minutos": 60,
    "aforo_maximo": 3,
    "en_mantenimiento": False,
    "activo": True,
}
ZONA = {"area": GIMNASIO, "adentro": 1, "cupos": 2, "abierta_ahora": True, "motivo_cierre": ""}
PEDRO = "5a5a5a5a-0000-4000-8000-000000000001"
TORRE_101 = "6b6b6b6b-0000-4000-8000-000000000101"
TORRE_102 = "6b6b6b6b-0000-4000-8000-000000000102"
RESIDENTE = {
    "persona": PEDRO,
    "nombre": "Pedro Gómez",
    "unidades": [{"id": TORRE_101, "nombre": "Torre 1 – 101"}],
}
INGRESO = {
    "id": "7c7c7c7c-0000-4000-8000-000000000001",
    "area": {"id": GIMNASIO["id"], "nombre": "Gimnasio"},
    "persona": {"id": PEDRO, "nombre": "Pedro Gómez"},
    "unidad": {"id": TORRE_101, "nombre": "Torre 1 – 101"},
    "acompanantes": 1,
    "estado": "ADENTRO",
    "estado_nombre": "Adentro",
    "entrada_en": "2026-10-08T10:00:00-05:00",
    "salida_prevista_en": "2026-10-08T11:00:00-05:00",
    "salida_en": None,
    "registrado_por": "Vigilante Gómez",
    "salida_registrada_por": None,
}
VENCIDO = {
    **INGRESO,
    "id": "7c7c7c7c-0000-4000-8000-000000000002",
    "persona": {"id": "x", "nombre": "Lucía Gómez"},
    "estado": "VENCIDO",
    "estado_nombre": "Se cumplió el tiempo",
    "salida_en": "2026-10-08T09:30:00-05:00",
}
VIGILANCIA = ["visitante.registrar", "reserva.ver_todas", "ingreso.registrar"]
ADMINISTRACION = ["area.ver", "area.gestionar", "ingreso.ver_historico"]
DATOS_DE_BUSQUEDA = {"paso": "buscar", "area": GIMNASIO["id"], "numero_documento": "1.000.000.001", "acompanantes": "1"}


def pantalla(permisos, listas, url="/ingresos/", tipo_usuario="Vigilancia", zonas=(ZONA,)):
    with (
        mock.patch("cliente_api.ingresos.zonas", return_value=list(zonas)),
        mock.patch("cliente_api.ingresos.listar", return_value=listas) as listar,
    ):
        respuesta = cliente_con_sesion(permisos=permisos, tipo_usuario=tipo_usuario).get(url)
    return respuesta, listar


def texto(respuesta):
    return " ".join(respuesta.content.decode().split())


def enviar_formulario(datos, residentes=(RESIDENTE,), registrar=None, permisos=VIGILANCIA):
    efectos = {"return_value": INGRESO} if registrar is None else registrar
    with (
        mock.patch("cliente_api.ingresos.zonas", return_value=[ZONA]),
        mock.patch("cliente_api.ingresos.listar", return_value={"adentro": [], "vencidos_hoy": []}),
        mock.patch("cliente_api.ingresos.buscar_residente", return_value=list(residentes)) as buscar,
        mock.patch("cliente_api.ingresos.registrar", **efectos) as api_registrar,
    ):
        respuesta = cliente_con_sesion(permisos=permisos, tipo_usuario="Vigilancia").post("/ingresos/registrar/", datos)
    return respuesta, buscar, api_registrar


# Quién ve qué


def test_vigilancia_ve_su_pantalla_con_cupos_formulario_adentro_y_vencidos():
    respuesta, _ = pantalla(VIGILANCIA, {"adentro": [INGRESO], "vencidos_hoy": [VENCIDO]})
    html = texto(respuesta)

    assert respuesta.status_code == 200
    assert "Ingreso a zonas" in html and "Cupos por zona" in html and "2 de 3 libres" in html
    assert "Registrar una entrada" in html and "Buscar residente" in html
    assert "Adentro ahora" in html and "Pedro Gómez" in html and "Registrar salida" in html
    assert "Se les cumplió el tiempo hoy" in html and "Lucía Gómez" in html and "09:30" in html
    assert "Historial de ingresos" not in html


def test_el_aviso_de_finalidad_esta_junto_al_formulario_y_no_se_inventa_su_texto():
    respuesta, _ = pantalla(VIGILANCIA, {"adentro": [], "vencidos_hoy": []})
    html = texto(respuesta)

    assert "Aviso de finalidad pendiente de la verificación legal." in html
    assert html.index("Aviso de finalidad") < html.index("Buscar residente")


def test_un_residente_es_devuelto_al_inicio():
    for permisos, tipo in (([ "area.ver", "reserva.solicitar"], "Residente"), (["area.ver"], "Secretaría")):
        respuesta = cliente_con_sesion(permisos=permisos, tipo_usuario=tipo).get("/ingresos/")

        assert respuesta.status_code == 302 and respuesta["Location"] == "/inicio/"


def test_administracion_ve_el_historial_sin_formulario():
    respuesta, listar = pantalla(ADMINISTRACION, {"historial": [{**INGRESO, "estado": "SALIO", "estado_nombre": "Salió", "salida_en": "2026-10-08T10:40:00-05:00"}]}, tipo_usuario="Administrador")
    html = texto(respuesta)

    assert "Historial de ingresos" in html and "Pedro Gómez" in html and "Torre 1 – 101" in html and "Salió" in html
    assert "Registrar una entrada" not in html and "Registrar salida" not in html and "Adentro ahora" not in html
    assert "Cupos por zona" in html
    listar.assert_called_once_with(mock.ANY, None, None)


def test_el_historial_se_filtra_por_zona_y_por_fecha():
    _, listar = pantalla(
        ADMINISTRACION, {"historial": []}, url=f"/ingresos/?area={GIMNASIO['id']}&fecha=2026-10-07", tipo_usuario="Administrador"
    )

    listar.assert_called_once_with(mock.ANY, GIMNASIO["id"], "2026-10-07")


# Registrar en dos pasos


def test_buscar_un_documento_muestra_nombre_y_vivienda_antes_de_registrar():
    respuesta, buscar, api_registrar = enviar_formulario(DATOS_DE_BUSQUEDA)
    html = texto(respuesta)

    assert buscar.call_args.args[1] == "1.000.000.001"
    assert "Pedro Gómez · Torre 1 – 101" in html and "Registrar entrada" in html
    assert f'value="{PEDRO}:{TORRE_101}" id="id_residente_0" required checked' in html
    api_registrar.assert_not_called()


def test_con_dos_viviendas_el_vigilante_elige_a_nombre_de_cual_entra():
    dos = {**RESIDENTE, "unidades": [{"id": TORRE_101, "nombre": "Torre 1 – 101"}, {"id": TORRE_102, "nombre": "Torre 1 – 102"}]}
    respuesta, _, _ = enviar_formulario(DATOS_DE_BUSQUEDA, residentes=[dos])
    html = texto(respuesta)

    assert "Pedro Gómez · Torre 1 – 101" in html and "Pedro Gómez · Torre 1 – 102" in html
    assert "checked" not in html.split("Confirma quién entra")[1].split("Registrar entrada")[0]


def test_no_encontrado_sale_junto_al_campo_del_documento():
    rechazo = ErrorDeApi(404, {"detail": "No encontrado."})
    with (
        mock.patch("cliente_api.ingresos.zonas", return_value=[ZONA]),
        mock.patch("cliente_api.ingresos.listar", return_value={"adentro": [], "vencidos_hoy": []}),
        mock.patch("cliente_api.ingresos.buscar_residente", side_effect=rechazo),
    ):
        respuesta = cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia").post(
            "/ingresos/registrar/", DATOS_DE_BUSQUEDA
        )

    html = respuesta.content.decode()
    assert 'id="id_numero_documento-error">No encontrado' in html
    assert 'value="1.000.000.001"' in html


def test_confirmar_manda_el_ingreso_a_la_api_y_vuelve_a_la_pantalla():
    datos = {**DATOS_DE_BUSQUEDA, "paso": "registrar", "residente": f"{PEDRO}:{TORRE_101}"}
    respuesta, _, api_registrar = enviar_formulario(datos)

    assert api_registrar.call_args.args[1] == {
        "area": GIMNASIO["id"], "persona": PEDRO, "unidad": TORRE_101, "acompanantes": 1
    }
    assert "conjunto" not in api_registrar.call_args.args[1]
    assert respuesta["Location"] == "/ingresos/?hecho=registrado"


def test_un_registro_rechazado_muestra_todos_los_motivos_y_conserva_lo_escrito():
    datos = {**DATOS_DE_BUSQUEDA, "paso": "registrar", "residente": f"{PEDRO}:{TORRE_101}"}
    rechazo = ErrorDeApi(400, {"motivos": ["Entran 2 y en esta zona quedan 1 puestos libres de 3.", "La zona atiende de 05:00 a 22:00."]})
    respuesta, _, _ = enviar_formulario(datos, registrar={"side_effect": rechazo})
    html = texto(respuesta)

    assert "Entran 2 y en esta zona quedan 1 puestos libres de 3." in html
    assert "La zona atiende de 05:00 a 22:00." in html
    assert 'name="numero_documento" value="1.000.000.001"' in html and 'name="acompanantes" value="1"' in html
    assert "Pedro Gómez · Torre 1 – 101" in html


def test_un_409_al_registrar_se_muestra_con_su_mensaje():
    datos = {**DATOS_DE_BUSQUEDA, "paso": "registrar", "residente": f"{PEDRO}:{TORRE_101}"}
    rechazo = ErrorDeApi(409, {"detail": "Esta zona no es con ingreso."})
    respuesta, _, _ = enviar_formulario(datos, registrar={"side_effect": rechazo})

    assert "Esta zona no es con ingreso." in respuesta.content.decode()


def test_con_la_api_caida_el_formulario_lo_dice():
    datos = {**DATOS_DE_BUSQUEDA, "paso": "registrar", "residente": f"{PEDRO}:{TORRE_101}"}
    respuesta, _, _ = enviar_formulario(datos, registrar={"side_effect": ApiNoDisponible()})

    assert "No hay conexión con el servidor de AdMind" in respuesta.content.decode()


def test_solo_quien_registra_puede_enviar_el_formulario():
    respuesta, _, api_registrar = enviar_formulario(DATOS_DE_BUSQUEDA, permisos=ADMINISTRACION)

    assert respuesta["Location"] == "/inicio/"
    api_registrar.assert_not_called()


# La salida


def test_registrar_salida_llama_a_la_api_y_vuelve_a_la_pantalla():
    with mock.patch("cliente_api.ingresos.registrar_salida", return_value=INGRESO) as salida:
        respuesta = cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia").post(
            f"/ingresos/{INGRESO['id']}/salida/"
        )

    assert str(salida.call_args.args[1]) == INGRESO["id"]
    assert respuesta["Location"] == "/ingresos/?hecho=salio"


def test_una_salida_repetida_muestra_el_409_de_la_api():
    rechazo = ErrorDeApi(409, {"detail": "Esta persona ya salió."})
    with (
        mock.patch("cliente_api.ingresos.registrar_salida", side_effect=rechazo),
        mock.patch("cliente_api.ingresos.zonas", return_value=[ZONA]),
        mock.patch("cliente_api.ingresos.listar", return_value={"adentro": [], "vencidos_hoy": []}),
    ):
        respuesta = cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia").post(
            f"/ingresos/{INGRESO['id']}/salida/"
        )

    assert "Esta persona ya salió." in respuesta.content.decode()


def test_administracion_no_puede_registrar_salidas():
    with mock.patch("cliente_api.ingresos.registrar_salida") as salida:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION, tipo_usuario="Administrador").post(
            f"/ingresos/{INGRESO['id']}/salida/"
        )

    assert respuesta["Location"] == "/inicio/"
    salida.assert_not_called()


# El menú


def lateral(permisos, tipo_usuario):
    html = cliente_con_sesion(permisos=permisos, tipo_usuario=tipo_usuario).get("/inicio/").content.decode()
    return html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]


def test_vigilancia_gana_ingreso_a_zonas_y_conserva_el_resto_de_su_menu():
    menu = lateral(VIGILANCIA, "Vigilancia")

    assert ">Ingreso a zonas</a>" in menu
    assert ">Zonas comunes</a>" in menu and ">Anuncios</a>" in menu


def test_vigilancia_no_ve_reglas_en_el_menu_y_administracion_si():
    assert ">Reglas</a>" not in lateral(VIGILANCIA, "Vigilancia")
    assert ">Reglas</a>" in lateral(ADMINISTRACION, "Administrador")


def test_administracion_ve_ingresos_y_un_residente_ninguno_de_los_dos():
    administracion = lateral(ADMINISTRACION, "Administrador")
    residente = lateral(["area.ver", "reserva.solicitar"], "Residente")

    assert ">Ingresos</a>" in administracion and ">Ingreso a zonas</a>" not in administracion
    assert ">Ingresos</a>" not in residente and ">Ingreso a zonas</a>" not in residente
