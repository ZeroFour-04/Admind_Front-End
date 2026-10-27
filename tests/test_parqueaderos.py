"""Pantalla «Parqueaderos» de Administración (HU-28). La API se simula: el front muestra, decide ella."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ADMINISTRACION = ["parqueadero.ver", "parqueadero.gestionar"]
SOLO_VER = ["parqueadero.ver"]
V01 = {
    "id": "5a1b2c3d-0000-4000-8000-000000000001",
    "codigo": "V-01",
    "tipo": "visitantes",
    "accesible": True,
    "notas": "Junto a la portería",
    "ocupado": False,
}
V02 = {**V01, "id": "5a1b2c3d-0000-4000-8000-000000000002", "codigo": "V-02", "accesible": False, "notas": "", "ocupado": True}
R01 = {**V01, "id": "5a1b2c3d-0000-4000-8000-000000000009", "codigo": "R-01", "tipo": "residentes", "notas": ""}


def ver(permisos=ADMINISTRACION, parqueaderos=(V01, V02, R01), **sesion):
    with mock.patch("cliente_api.parqueaderos.listar", return_value=list(parqueaderos)):
        return cliente_con_sesion(permisos=permisos, **sesion).get("/parqueaderos/")


def test_la_tabla_muestra_cada_puesto_con_una_pastilla_con_texto():
    html = ver().content.decode()

    for valor in ("<th>Código</th>", "<th>Tipo</th>", "<th>Accesible</th>", "<th>Notas</th>", "<th>Estado</th>"):
        assert valor in html
    assert "V-01" in html and "Junto a la portería" in html
    assert html.count(">Libre</span>") == 1
    assert html.count(">Ocupado</span>") == 1
    # Uno de residentes no se ocupa por una visita: no se le pone «Libre».
    assert html.count(">Sin asignar</span>") == 1


def test_sin_parqueaderos_hay_un_estado_vacio_que_invita_a_crear():
    html = ver(parqueaderos=[]).content.decode()

    assert "Todavía no hay parqueaderos" in html
    assert "Crea el primero" in html


def test_administracion_ve_el_formulario_de_creacion_y_el_retiro_nombra_el_codigo():
    html = ver().content.decode()

    assert ">Crear parqueadero</button>" in html
    for campo in ('name="codigo"', 'name="tipo"', 'name="accesible"', 'name="notas"'):
        assert campo in html
    # Quien lo crea no tiene dónde escoger una unidad: no se asigna aquí.
    assert "name=\"unidad\"" not in html and "/asignar" not in html
    cuerpo = " ".join(html.split())
    assert "Vas a retirar el parqueadero <b>V-01</b>." in cuerpo
    assert f'action="/parqueaderos/{V01["id"]}/desactivar/"' in html
    assert ">Retirar V-01</button>" in html


def test_sin_gestionar_se_ve_la_tabla_sin_formulario_ni_botones():
    html = ver(permisos=SOLO_VER).content.decode()

    assert "V-01" in html and ">Libre</span>" in html
    assert "Crear parqueadero" not in html and 'name="codigo"' not in html
    assert "Retirar" not in html and "Acciones" not in html


def test_sin_permiso_de_parqueaderos_redirige_al_inicio():
    for permisos in ([], ["visitante.registrar"]):
        respuesta = cliente_con_sesion(permisos=permisos, tipo_usuario="Vigilancia").get("/parqueaderos/")

        assert respuesta.status_code == 302
        assert respuesta["Location"] == "/inicio/"


def test_crear_manda_codigo_tipo_accesible_y_notas_y_vuelve_con_el_aviso():
    with mock.patch("cliente_api.parqueaderos.crear") as crear:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/parqueaderos/",
            {"codigo": "V-05", "tipo": "visitantes", "accesible": "on", "notas": "Frente a la torre 2"},
        )

    assert crear.call_args.args[1] == {
        "codigo": "V-05",
        "tipo": "visitantes",
        "accesible": True,
        "notas": "Frente a la torre 2",
    }
    assert respuesta["Location"] == "/parqueaderos/?hecho=creado"


def test_sin_marcar_accesible_viaja_falso():
    with mock.patch("cliente_api.parqueaderos.crear") as crear:
        cliente_con_sesion(permisos=ADMINISTRACION).post("/parqueaderos/", {"codigo": "R-02", "tipo": "residentes"})

    assert crear.call_args.args[1]["accesible"] is False
    assert crear.call_args.args[1]["tipo"] == "residentes"


def test_un_400_de_la_api_cae_en_el_campo_codigo():
    repetido = ErrorDeApi(400, {"codigo": ["Ya existe un parqueadero con ese código en el conjunto."]})
    with (
        mock.patch("cliente_api.parqueaderos.crear", side_effect=repetido),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/parqueaderos/", {"codigo": "v-01", "tipo": "visitantes"}
        ).content.decode()

    assert "Ya existe un parqueadero con ese código en el conjunto." in html
    assert 'aria-invalid="true"' in html
    # Conserva lo escrito.
    assert 'value="v-01"' in html


def test_sin_codigo_no_llama_a_la_api():
    with mock.patch("cliente_api.parqueaderos.crear") as crear, mock.patch(
        "cliente_api.parqueaderos.listar", return_value=[]
    ):
        cliente_con_sesion(permisos=ADMINISTRACION).post("/parqueaderos/", {"codigo": "  ", "tipo": "visitantes"})

    crear.assert_not_called()


def test_quien_no_gestiona_no_crea_desde_el_front():
    with mock.patch("cliente_api.parqueaderos.crear") as crear:
        respuesta = cliente_con_sesion(permisos=SOLO_VER).post("/parqueaderos/", {"codigo": "V-09", "tipo": "visitantes"})

    crear.assert_not_called()
    assert respuesta["Location"] == "/parqueaderos/"


def test_retirar_llama_a_la_api_y_vuelve_con_el_aviso():
    with mock.patch("cliente_api.parqueaderos.desactivar") as desactivar:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(f"/parqueaderos/{V01['id']}/desactivar/")

    assert str(desactivar.call_args.args[1]) == V01["id"]
    assert respuesta["Location"] == "/parqueaderos/?hecho=retirado"


def test_el_409_de_ocupado_se_muestra_arriba_de_la_tabla():
    ocupado = ErrorDeApi(
        409, {"detail": "Este parqueadero está ocupado por una visita: registra primero su salida."}
    )
    with (
        mock.patch("cliente_api.parqueaderos.desactivar", side_effect=ocupado),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V02]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/parqueaderos/{V02['id']}/desactivar/"
        ).content.decode()

    assert ocupado.mensaje in html
    assert html.index(ocupado.mensaje) < html.index("<table")


def test_el_aviso_de_la_pantalla_dice_que_quedo_creado_o_retirado():
    with mock.patch("cliente_api.parqueaderos.listar", return_value=[V01]):
        cliente = cliente_con_sesion(permisos=ADMINISTRACION)
        creado = cliente.get("/parqueaderos/?hecho=creado").content.decode()
        retirado = cliente.get("/parqueaderos/?hecho=retirado").content.decode()

    assert "Parqueadero creado." in creado
    assert "Parqueadero retirado." in retirado


def test_la_pantalla_no_carga_javascript_propio():
    html = ver().content.decode()

    assert "alpine" not in html and "visitantes.js" not in html and "reservas.js" not in html


def test_el_lateral_trae_parqueaderos_para_administracion_y_no_para_residente_ni_vigilancia():
    with mock.patch("cliente_api.parqueaderos.listar", return_value=[]):
        administracion = cliente_con_sesion(
            permisos=ADMINISTRACION, tipo_usuario="Administrador"
        ).get("/parqueaderos/").content.decode()
    residente = cliente_con_sesion(permisos=["area.ver", "reserva.solicitar"], tipo_usuario="Residente").get(
        "/inicio/"
    ).content.decode()
    vigilancia = cliente_con_sesion(permisos=["visitante.registrar"], tipo_usuario="Vigilancia").get(
        "/inicio/"
    ).content.decode()

    def lateral(html):
        return html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    assert 'href="/parqueaderos/"' in lateral(administracion)
    assert ">Parqueaderos</a>" in lateral(administracion)
    assert ">Parqueaderos</a>" not in lateral(residente)
    assert ">Parqueaderos</a>" not in lateral(vigilancia)
