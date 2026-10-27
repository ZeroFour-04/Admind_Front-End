from unittest import mock

import pytest

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion


@pytest.fixture(autouse=True)
def parqueaderos_libres_por_defecto():
    """La pantalla de portería ahora pide los parqueaderos libres (HU-28): sin esto llamaría a la API de verdad."""
    with mock.patch("cliente_api.parqueaderos.listar", return_value=[]) as listar:
        yield listar


ADMINISTRACION = ["visitante.ver_historico"]
VIGILANCIA = ["visitante.registrar"]
UNIDADES = [{"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"}]
VISITANTE = {
    "id": "9e1f7a8b-0000-4000-8000-000000000001",
    "nombre": "María Pérez",
    "cedula": "123456789",
    "placa_vehiculo": "ABC123",
    "tipo_vehiculo": "Automóvil",
    "hora_entrada": "2026-10-01T14:30:00-05:00",
    "apartamento_visitado": "Torre 1 – 101",
}


def test_administracion_y_superusuario_ven_el_enlace_visitantes():
    for rol in ("Administrador", "Superusuario"):
        html = cliente_con_sesion(permisos=ADMINISTRACION, tipo_usuario=rol).get("/inicio/").content.decode()

        assert ">Visitantes</a>" in html
        assert ">Visitante</a>" not in html


def test_vigilancia_ve_el_enlace_visitante():
    html = cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia").get("/inicio/").content.decode()

    assert ">Visitante</a>" in html
    assert ">Visitantes</a>" not in html


def test_vigilancia_solo_ve_las_secciones_permitidas_en_el_lateral():
    html = cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia").get("/inicio/").content.decode()
    lateral = html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]
    opciones = [
        texto
        for texto in (
            "Inicio", "Zonas comunes", "Áreas comunes", "Reglas", "Anuncios",
            "Notificaciones", "Solicitudes", "Visitante", "Visitantes", "Conjunto",
            "Usuarios", "Unidades",
        )
        if f">{texto}</a>" in lateral
    ]

    assert opciones == ["Inicio", "Zonas comunes", "Anuncios", "Visitante"]


def test_administracion_y_superusuario_ven_el_historial_sin_formulario():
    with mock.patch("cliente_api.visitantes.listar", return_value=[VISITANTE]):
        paginas = [
            cliente_con_sesion(
                permisos=ADMINISTRACION, tipo_usuario=rol
            ).get("/visitantes/").content.decode()
            for rol in ("Administrador", "Superusuario")
        ]

    for html in paginas:
        for valor in (
            "Historial de visitantes", "CC", "Nombre", "Placa vehículo", "Tipo vehículo",
            "Hora ingreso", "Apartamento a visitar", "María Pérez", "123456789", "ABC123",
            "Torre 1 – 101",
        ):
            assert valor in html
        assert "Registrar ingreso" not in html


def test_solo_vigilancia_ve_el_formulario_de_registro():
    with mock.patch("cliente_api.unidades.listar", return_value=UNIDADES), mock.patch(
        "cliente_api.visitantes.listar", return_value=[]
    ):
        html_vigilancia = cliente_con_sesion(
            permisos=VIGILANCIA, tipo_usuario="Vigilancia"
        ).get("/visitantes/").content.decode()
        html_administracion = cliente_con_sesion(
            permisos=ADMINISTRACION, tipo_usuario="Administrador"
        ).get("/visitantes/").content.decode()

    assert "Registrar ingreso" in html_vigilancia
    assert "La hora de ingreso se asigna automáticamente con la hora de Colombia." in html_vigilancia
    assert '<option value="7a1b2c3d-0000-4000-8000-000000000101">Torre 1 – 101</option>' in html_vigilancia
    assert "Registrar ingreso" not in html_administracion


def test_vigilancia_envia_el_formulario_a_registro_y_no_envia_la_hora():
    with mock.patch("cliente_api.unidades.listar", return_value=UNIDADES), mock.patch(
        "cliente_api.visitantes.registrar"
    ) as registrar:
        respuesta = cliente_con_sesion(
            permisos=VIGILANCIA, tipo_usuario="Vigilancia"
        ).post(
            "/visitantes/",
            {
                "cedula": "123456789",
                "nombre": "María Pérez",
                "ingresa_con_vehiculo": "si",
                "placa_vehiculo": "ABC123",
                "tipo_vehiculo": "Auto",
                "apartamento_visitado": UNIDADES[0]["id"],
            },
        )

    assert registrar.call_args.args[1] == {
        "cedula": "123456789",
        "nombre": "María Pérez",
        "ingresa_con_vehiculo": True,
        "placa_vehiculo": "ABC123",
        "tipo_vehiculo": "Auto",
        "apartamento_visitado": UNIDADES[0]["id"],
    }
    assert respuesta["Location"] == "/visitantes/?registrado=1"


def test_vigilancia_ve_la_hora_de_ingreso_en_horario_colombiano():
    with mock.patch("cliente_api.unidades.listar", return_value=UNIDADES), mock.patch(
        "cliente_api.visitantes.listar", return_value=[VISITANTE]
    ):
        html = cliente_con_sesion(
            permisos=VIGILANCIA, tipo_usuario="Vigilancia"
        ).get("/visitantes/").content.decode()

    assert "01/10/2026 14:30" in html


# El parqueadero de visitantes y la salida (HU-28). El front muestra; decide la API.

V01 = {
    "id": "5a1b2c3d-0000-4000-8000-000000000001",
    "codigo": "V-01",
    "tipo": "visitantes",
    "accesible": True,
    "notas": "",
    "ocupado": False,
}
V03 = {**V01, "id": "5a1b2c3d-0000-4000-8000-000000000003", "codigo": "V-03", "accesible": False}
CON_PARQUEADERO = {
    **VISITANTE,
    "id": "9e1f7a8b-0000-4000-8000-000000000002",
    "nombre": "Carlos Ruiz",
    "placa_vehiculo": "XYZ789",
    "parqueadero": "V-01",
    "hora_salida": None,
}
YA_SALIO = {
    **VISITANTE,
    "id": "9e1f7a8b-0000-4000-8000-000000000003",
    "parqueadero": "V-02",
    "hora_salida": "2026-10-01T16:45:00-05:00",
}
CARRO_EN_V01 = {
    "cedula": "123456789",
    "nombre": "María Pérez",
    "ingresa_con_vehiculo": "si",
    "placa_vehiculo": "ABC123",
    "tipo_vehiculo": "Auto",
    "apartamento_visitado": UNIDADES[0]["id"],
}


def portero():
    return cliente_con_sesion(permisos=VIGILANCIA, tipo_usuario="Vigilancia")


def ver_porteria(libres, visitantes=()):
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.listar", return_value=libres) as pedir_libres,
        mock.patch("cliente_api.visitantes.listar", return_value=list(visitantes)),
    ):
        html = portero().get("/visitantes/").content.decode()
    return html, pedir_libres


def test_el_formulario_ofrece_los_parqueaderos_libres_de_visitantes_y_sin_parqueadero():
    html, pedir_libres = ver_porteria([V01, V03])

    assert pedir_libres.call_args.kwargs == {"tipo": "visitantes", "libres": True}
    assert '<option value="">Sin parqueadero</option>' in html
    assert f'<option value="{V01["id"]}">V-01 · accesible</option>' in html
    assert f'<option value="{V03["id"]}">V-03</option>' in html
    assert "No hay parqueaderos de visitantes libres" not in html


def test_sin_parqueaderos_libres_el_formulario_lo_dice_y_no_ofrece_el_campo():
    html, _ = ver_porteria([])

    assert "No hay parqueaderos de visitantes libres. La visita se registra sin parqueadero." in html
    assert 'name="parqueadero"' not in html


def test_sin_libres_la_visita_se_registra_sin_parqueadero():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.visitantes.registrar") as registrar,
    ):
        respuesta = portero().post("/visitantes/", CARRO_EN_V01)

    assert "parqueadero" not in registrar.call_args.args[1]
    assert respuesta["Location"] == "/visitantes/?registrado=1"


def test_elegir_un_parqueadero_lo_manda_a_la_api():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01, V03]),
        mock.patch("cliente_api.visitantes.registrar") as registrar,
    ):
        respuesta = portero().post("/visitantes/", {**CARRO_EN_V01, "parqueadero": V01["id"]})

    assert registrar.call_args.args[1]["parqueadero"] == V01["id"]
    assert respuesta["Location"] == "/visitantes/?registrado=1"


def test_sin_vehiculo_el_parqueadero_no_viaja_aunque_el_navegador_lo_mande():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01]),
        mock.patch("cliente_api.visitantes.registrar") as registrar,
    ):
        portero().post(
            "/visitantes/",
            {**CARRO_EN_V01, "ingresa_con_vehiculo": "no", "placa_vehiculo": "", "parqueadero": V01["id"]},
        )

    assert registrar.call_args.args[1]["placa_vehiculo"] == ""
    assert "parqueadero" not in registrar.call_args.args[1]


def test_un_409_se_muestra_arriba_conserva_lo_escrito_y_vuelve_a_pedir_los_libres():
    ocupado = ErrorDeApi(
        409, {"detail": "Ese parqueadero se acaba de ocupar. Elige otro o registra la visita sin parqueadero."}
    )
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.listar", side_effect=[[V01, V03], [V03]]) as pedir_libres,
        mock.patch("cliente_api.visitantes.registrar", side_effect=ocupado),
        mock.patch("cliente_api.visitantes.listar", return_value=[]),
    ):
        respuesta = portero().post("/visitantes/", {**CARRO_EN_V01, "parqueadero": V01["id"]})
        html = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert pedir_libres.call_count == 2
    assert ocupado.mensaje in html
    assert html.index(ocupado.mensaje) < html.index('name="cedula"')
    # Conserva lo escrito y ya no ofrece el que se ocupó.
    assert 'value="123456789"' in html and 'value="María Pérez"' in html and 'value="ABC123"' in html
    assert f'<option value="{V03["id"]}">V-03</option>' in html
    assert V01["id"] not in html


def test_un_parqueadero_que_ya_no_esta_en_la_lista_se_rechaza_con_su_mensaje_sin_llamar_a_la_api():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V03]),
        mock.patch("cliente_api.visitantes.registrar") as registrar,
        mock.patch("cliente_api.visitantes.listar", return_value=[]),
    ):
        html = portero().post("/visitantes/", {**CARRO_EN_V01, "parqueadero": V01["id"]}).content.decode()

    registrar.assert_not_called()
    assert "Ese parqueadero ya no está libre. Elige otro o registra la visita sin parqueadero." in html


def test_la_tabla_muestra_el_parqueadero_y_la_salida():
    html, _ = ver_porteria([], [CON_PARQUEADERO, YA_SALIO])

    assert "<th>Parqueadero</th>" in html and "<th>Salida</th>" in html
    assert "<td>V-01</td>" in html and "<td>V-02</td>" in html
    assert "01/10/2026 16:45" in html
    # La que ya salió no tiene botón; la que sigue adentro sí.
    assert html.count(">Registrar salida</summary>") == 1


def test_la_confirmacion_de_la_salida_nombra_al_visitante_la_placa_y_el_parqueadero_que_se_libera():
    html, _ = ver_porteria([], [CON_PARQUEADERO])

    assert f'action="/visitantes/{CON_PARQUEADERO["id"]}/salida/"' in html
    cuerpo = " ".join(html.split())
    assert "Vas a registrar la salida de <b>Carlos Ruiz</b>, con el vehículo de placa <b>XYZ789</b>." in cuerpo
    assert "Se libera el parqueadero <b>V-01</b>." in cuerpo
    assert ">Confirmar salida de Carlos Ruiz</button>" in html


def test_la_confirmacion_de_una_visita_sin_vehiculo_ni_parqueadero_no_inventa_datos():
    sin_vehiculo = {**CON_PARQUEADERO, "placa_vehiculo": "", "parqueadero": None}

    cuerpo = " ".join(ver_porteria([], [sin_vehiculo])[0].split())

    assert "Vas a registrar la salida de <b>Carlos Ruiz</b>." in cuerpo
    assert "No ocupa parqueadero." in cuerpo
    assert "con el vehículo" not in cuerpo


def test_el_boton_de_salida_solo_lo_ve_vigilancia():
    with mock.patch("cliente_api.visitantes.listar", return_value=[CON_PARQUEADERO]):
        html = cliente_con_sesion(
            permisos=ADMINISTRACION, tipo_usuario="Administrador"
        ).get("/visitantes/").content.decode()

    assert "Carlos Ruiz" in html and "V-01" in html
    assert "Registrar salida" not in html and "/salida/" not in html
    assert "Sin salida" in html


def test_registrar_la_salida_llama_a_la_api_y_vuelve_a_la_lista():
    with mock.patch("cliente_api.visitantes.registrar_salida") as registrar_salida:
        respuesta = portero().post(f"/visitantes/{CON_PARQUEADERO['id']}/salida/")

    assert str(registrar_salida.call_args.args[1]) == CON_PARQUEADERO["id"]
    assert respuesta["Location"] == "/visitantes/?salida=1"


def test_un_409_de_la_salida_se_muestra_como_aviso_y_no_rompe_la_pantalla():
    ya_salio = ErrorDeApi(409, {"detail": "Este visitante ya salió."})
    with (
        mock.patch("cliente_api.visitantes.registrar_salida", side_effect=ya_salio),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.visitantes.listar", return_value=[CON_PARQUEADERO]),
    ):
        respuesta = portero().post(f"/visitantes/{CON_PARQUEADERO['id']}/salida/")
        html = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert "Este visitante ya salió." in html
    assert "Registrar ingreso" in html and "Carlos Ruiz" in html


def test_la_pantalla_dice_que_la_salida_quedo_registrada():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.visitantes.listar", return_value=[]),
    ):
        html = portero().get("/visitantes/?salida=1").content.decode()

    assert "Salida registrada." in html


def test_quien_no_es_vigilancia_no_registra_salidas_desde_el_front():
    with mock.patch("cliente_api.visitantes.registrar_salida") as registrar_salida:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION, tipo_usuario="Administrador").post(
            f"/visitantes/{CON_PARQUEADERO['id']}/salida/"
        )

    registrar_salida.assert_not_called()
    assert respuesta["Location"] == "/inicio/"
