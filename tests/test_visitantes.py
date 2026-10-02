from unittest import mock

from tests.ayudantes import cliente_con_sesion

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
            "Usuarios", "Apartamentos y parqueaderos",
        )
        if f">{texto}</a>" in lateral
    ]

    assert opciones == ["Inicio", "Zonas comunes", "Reglas", "Anuncios", "Visitante"]


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
