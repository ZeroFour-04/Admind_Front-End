"""Pantalla «Parqueaderos» de Administración (HU-28), su asignación a una vivienda y «Mi parqueadero» (HU-34). La API se simula: el front muestra, decide ella."""
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
            {"codigo": "V-05", "tipo": "visitantes", "vehiculo": "carro", "accesible": "on", "notas": "Frente a la torre 2"},
        )

    assert crear.call_args.args[1] == {
        "codigo": "V-05",
        "tipo": "visitantes",
        "vehiculo": "carro",
        "accesible": True,
        "notas": "Frente a la torre 2",
    }
    assert respuesta["Location"] == "/parqueaderos/?hecho=creado"


def test_sin_marcar_accesible_viaja_falso():
    with mock.patch("cliente_api.parqueaderos.crear") as crear:
        cliente_con_sesion(permisos=ADMINISTRACION).post("/parqueaderos/", {"codigo": "R-02", "tipo": "residentes", "vehiculo": "moto"})

    assert crear.call_args.args[1]["accesible"] is False
    assert crear.call_args.args[1]["tipo"] == "residentes"
    assert crear.call_args.args[1]["vehiculo"] == "moto"


def test_un_400_de_la_api_cae_en_el_campo_codigo():
    repetido = ErrorDeApi(400, {"codigo": ["Ya existe un parqueadero con ese código en el conjunto."]})
    with (
        mock.patch("cliente_api.parqueaderos.crear", side_effect=repetido),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            "/parqueaderos/", {"codigo": "v-01", "tipo": "visitantes", "vehiculo": "carro"}
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


# HU-34: asignar, reasignar, liberar, historial, «Mi parqueadero» y el tope

CON_ASIGNAR = [*ADMINISTRACION, "parqueadero.asignar"]
R01_ASIGNADO = {**R01, "asignado_a": "Torre 1 – 101"}
TOPE = "Máximo 1 de carro, 1 de moto y 0 de bicicleta por vivienda"
REGLA_DEL_TOPE = {"tipo": "PARQUEADEROS_POR_VIVIENDA", "descripcion": TOPE}
UNIDADES = [
    {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
    {"id": "7a1b2c3d-0000-4000-8000-000000000202", "nombre": "Torre 2 – 202"},
]


def ver_con_asignar(parqueaderos=(V01, R01), reglas=(), permisos=CON_ASIGNAR):
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=list(parqueaderos)),
        mock.patch("cliente_api.reglas.listar", return_value=list(reglas)),
    ):
        return cliente_con_sesion(permisos=permisos).get("/parqueaderos/").content.decode()


def test_hu34_una_fila_de_visitantes_no_tiene_asignar_ni_historial_y_la_de_residentes_si():
    html = ver_con_asignar()

    assert f'href="/parqueaderos/{R01["id"]}/asignar/"' in html and ">Asignar R-01</a>" in html
    assert f'href="/parqueaderos/{R01["id"]}/historial/"' in html
    assert f"/parqueaderos/{V01['id']}/asignar/" not in html
    assert f"/parqueaderos/{V01['id']}/historial/" not in html
    # Sin asignar no hay nada que liberar.
    assert f"/parqueaderos/{R01['id']}/liberar/" not in html


def test_hu34_un_puesto_asignado_dice_a_quien_y_ofrece_reasignar_y_liberar():
    html = ver_con_asignar(parqueaderos=(R01_ASIGNADO,))
    cuerpo = " ".join(html.split())

    assert ">Asignado a Torre 1 – 101</span>" in html
    assert ">Reasignar R-01</a>" in html and ">Asignar R-01</a>" not in html
    assert f'action="/parqueaderos/{R01["id"]}/liberar/"' in html
    assert ">Liberar R-01</button>" in html
    assert "la asignación sigue en el historial" in cuerpo


def test_hu34_sin_el_permiso_de_asignar_no_hay_botones_de_asignacion():
    html = ver_con_asignar(parqueaderos=(R01_ASIGNADO,), permisos=ADMINISTRACION)

    assert ">Asignado a Torre 1 – 101</span>" in html
    assert "/asignar/" not in html and "/historial/" not in html and "/liberar/" not in html
    assert "Tope por vivienda" not in html


def test_hu34_la_pantalla_muestra_el_tope_de_la_regla_o_que_no_hay():
    con_regla = ver_con_asignar(reglas=[REGLA_DEL_TOPE])
    sin_regla = ver_con_asignar(reglas=[])

    assert f"<b>Tope por vivienda:</b> {TOPE}." in con_regla
    assert "el conjunto no lo ha definido, así que no hay tope" in sin_regla
    assert 'href="/reglas/"' in sin_regla


def test_hu34_si_no_se_puede_leer_la_regla_la_pantalla_sigue_funcionando():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01]),
        mock.patch("cliente_api.reglas.listar", side_effect=ErrorDeApi(403, {})),
    ):
        respuesta = cliente_con_sesion(permisos=CON_ASIGNAR).get("/parqueaderos/")

    assert respuesta.status_code == 200 and "R-01" in respuesta.content.decode()


def test_hu34_crear_un_puesto_ofrece_el_vehiculo():
    html = ver_con_asignar()

    assert 'name="vehiculo"' in html
    for vehiculo in ("Carro", "Moto", "Bicicleta"):
        assert f">{vehiculo}</option>" in html


def test_hu34_la_pantalla_de_asignar_ofrece_las_viviendas_del_conjunto():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01, R01]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.reglas.listar", return_value=[REGLA_DEL_TOPE]),
    ):
        html = cliente_con_sesion(permisos=CON_ASIGNAR).get(f"/parqueaderos/{R01['id']}/asignar/").content.decode()

    assert "Asignar el parqueadero R-01" in html
    assert f'<option value="{UNIDADES[0]["id"]}"' in html and "Torre 2 – 202" in html
    assert TOPE in html


def test_hu34_asignar_manda_la_vivienda_y_vuelve_con_el_aviso():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.reglas.listar", return_value=[]),
        mock.patch("cliente_api.parqueaderos.asignar", return_value={"reasignada": False}) as asignar,
    ):
        respuesta = cliente_con_sesion(permisos=CON_ASIGNAR).post(
            f"/parqueaderos/{R01['id']}/asignar/", {"unidad": UNIDADES[0]["id"]}
        )

    assert str(asignar.call_args.args[1]) == R01["id"] and asignar.call_args.args[2] == UNIDADES[0]["id"]
    assert respuesta["Location"] == "/parqueaderos/?hecho=asignado"


def test_hu34_reasignar_avisa_que_la_anterior_quedo_cerrada():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01_ASIGNADO]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.reglas.listar", return_value=[]),
        mock.patch("cliente_api.parqueaderos.asignar", return_value={"reasignada": True}),
    ):
        respuesta = cliente_con_sesion(permisos=CON_ASIGNAR).post(
            f"/parqueaderos/{R01['id']}/asignar/", {"unidad": UNIDADES[1]["id"]}
        )
        aviso = cliente_con_sesion(permisos=CON_ASIGNAR).get("/parqueaderos/?hecho=reasignado").content.decode()

    assert respuesta["Location"] == "/parqueaderos/?hecho=reasignado"
    assert "la asignación anterior quedó cerrada en el historial" in aviso


def test_hu34_el_409_del_tope_se_muestra_en_la_pantalla_de_asignar():
    tope = ErrorDeApi(409, {"detail": "Esta vivienda ya tiene el máximo de parqueaderos de carro que fijó el conjunto (1)."})
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.reglas.listar", return_value=[REGLA_DEL_TOPE]),
        mock.patch("cliente_api.parqueaderos.asignar", side_effect=tope),
    ):
        html = cliente_con_sesion(permisos=CON_ASIGNAR).post(
            f"/parqueaderos/{R01['id']}/asignar/", {"unidad": UNIDADES[0]["id"]}
        ).content.decode()

    assert tope.mensaje in html
    # Conserva lo elegido.
    assert f'<option value="{UNIDADES[0]["id"]}" selected' in html


def test_hu34_sin_elegir_vivienda_no_llama_a_la_api():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.reglas.listar", return_value=[]),
        mock.patch("cliente_api.parqueaderos.asignar") as asignar,
    ):
        html = cliente_con_sesion(permisos=CON_ASIGNAR).post(f"/parqueaderos/{R01['id']}/asignar/", {"unidad": ""}).content.decode()

    asignar.assert_not_called()
    assert "Elige una vivienda." in html


def test_hu34_un_parqueadero_de_visitantes_no_se_asigna_ni_desde_la_direccion():
    with (
        mock.patch("cliente_api.parqueaderos.listar", return_value=[V01]),
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.parqueaderos.asignar") as asignar,
    ):
        cliente = cliente_con_sesion(permisos=CON_ASIGNAR)
        pantalla = cliente.get(f"/parqueaderos/{V01['id']}/asignar/")
        envio = cliente.post(f"/parqueaderos/{V01['id']}/asignar/", {"unidad": UNIDADES[0]["id"]})

    asignar.assert_not_called()
    assert pantalla["Location"] == "/parqueaderos/" and envio["Location"] == "/parqueaderos/"


def test_hu34_sin_el_permiso_de_asignar_no_se_llega_a_asignar_liberar_ni_al_historial():
    with (
        mock.patch("cliente_api.parqueaderos.asignar") as asignar,
        mock.patch("cliente_api.parqueaderos.liberar") as liberar,
    ):
        cliente = cliente_con_sesion(permisos=ADMINISTRACION)
        respuestas = [
            cliente.post(f"/parqueaderos/{R01['id']}/asignar/", {"unidad": UNIDADES[0]["id"]}),
            cliente.post(f"/parqueaderos/{R01['id']}/liberar/"),
            cliente.get(f"/parqueaderos/{R01['id']}/historial/"),
        ]

    asignar.assert_not_called()
    liberar.assert_not_called()
    assert [r["Location"] for r in respuestas] == ["/parqueaderos/"] * 3


def test_hu34_liberar_llama_a_la_api_y_vuelve_con_el_aviso():
    with mock.patch("cliente_api.parqueaderos.liberar") as liberar:
        respuesta = cliente_con_sesion(permisos=CON_ASIGNAR).post(f"/parqueaderos/{R01['id']}/liberar/")

    assert str(liberar.call_args.args[1]) == R01["id"]
    assert respuesta["Location"] == "/parqueaderos/?hecho=liberado"


def test_hu34_el_historial_muestra_cada_asignacion_con_quien_la_registro_y_la_cerro():
    historial = [
        {"id": "a1", "vivienda": "Torre 2 – 202", "vigencia_desde": "2026-10-20", "vigencia_hasta": None,
         "registrado_por": "Laura Gómez", "cerrado_por": None},
        {"id": "a2", "vivienda": "Torre 1 – 101", "vigencia_desde": "2026-09-01", "vigencia_hasta": "2026-10-20",
         "registrado_por": "Camilo Ruiz", "cerrado_por": "Laura Gómez"},
    ]
    with (
        mock.patch("cliente_api.parqueaderos.historial", return_value=historial),
        mock.patch("cliente_api.parqueaderos.listar", return_value=[R01]),
    ):
        html = cliente_con_sesion(permisos=CON_ASIGNAR).get(f"/parqueaderos/{R01['id']}/historial/").content.decode()

    assert "Historial del parqueadero R-01" in html
    for texto in ("Torre 2 – 202", "20/10/2026", "01/09/2026", "Camilo Ruiz", ">Vigente</span>"):
        assert texto in html
    assert html.index("Torre 2 – 202") < html.index("Torre 1 – 101")


def test_hu34_el_residente_ve_mi_parqueadero_sin_botones_y_el_lateral_lo_ofrece():
    puestos = [{"id": R01["id"], "codigo": "R-01", "vehiculo": "moto", "accesible": False, "notas": "",
                "vivienda": "Torre 1 – 101", "desde": "2026-10-20"}]
    with mock.patch("cliente_api.parqueaderos.mios", return_value=puestos):
        cliente = cliente_con_sesion(permisos=["area.ver", "reserva.solicitar"], tipo_usuario="Residente")
        html = cliente.get("/parqueaderos/mios/").content.decode()
        lateral = html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    assert "R-01" in html and "Moto" in html and "Torre 1 – 101" in html and "20/10/2026" in html
    assert "<button" not in html.split("<main", 1)[1] and "/asignar/" not in html
    assert 'href="/parqueaderos/mios/"' in lateral and ">Mi parqueadero</a>" in lateral


def test_hu34_el_residente_sin_puesto_ve_un_estado_vacio_y_al_abrir_parqueaderos_llega_a_los_suyos():
    with mock.patch("cliente_api.parqueaderos.mios", return_value=[]):
        cliente = cliente_con_sesion(permisos=["area.ver"], tipo_usuario="Residente")
        vacio = cliente.get("/parqueaderos/mios/").content.decode()
        redireccion = cliente.get("/parqueaderos/")

    assert "Tu vivienda no tiene parqueadero asignado" in vacio
    assert redireccion["Location"] == "/parqueaderos/mios/"


def test_hu34_no_hay_pantalla_ni_texto_para_quitar_un_puesto_por_mora():
    html = ver_con_asignar(parqueaderos=(R01_ASIGNADO,), reglas=[REGLA_DEL_TOPE])
    texto = html.lower()

    for palabra in ("mora", "sanción", "restring", "suspend", "multa"):
        assert palabra not in texto
    from django.urls import get_resolver

    nombres = {
        patron.name for resolver in get_resolver().url_patterns
        if getattr(resolver, "app_name", "") == "parqueaderos" for patron in resolver.url_patterns
    }
    assert nombres == {"lista", "mios", "desactivar", "asignar", "liberar", "historial"}
