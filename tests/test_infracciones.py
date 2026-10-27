"""Registro de infracciones (HU-30): lista, formulario, detalle, cierre y anulación. La API se simula.

El sistema no sanciona: aquí se comprueba también lo que NO existe en las pantallas.
"""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

ADMINISTRACION = ["infraccion.ver", "infraccion.registrar", "infraccion.cerrar", "caso.ver_todos"]
SUPERUSUARIO = [*ADMINISTRACION, "infraccion.anular"]
FRASE_DE_R11 = "No es una sanción ni reemplaza el procedimiento del art. 59 de la Ley 675."
UNIDADES = [
    {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"},
    {"id": "7a1b2c3d-0000-4000-8000-000000000202", "nombre": "Torre 2 – 202"},
]
ABIERTO = {
    "id": "8a1b2c3d-0000-4000-8000-000000000001", "unidad": UNIDADES[0]["id"], "vivienda": "Torre 1 – 101", "caso": None,
    "descripcion_hecho": "Música a alto volumen pasada la medianoche", "fecha_hecho": "2026-10-20",
    "registrado_por": "Laura Gómez", "registrado_en": "2026-10-21T09:00:00-05:00",
    "fecha_notificacion": "2026-10-21T09:00:01-05:00", "abierto": True, "cierre_fecha": None, "cierre_comentario": None,
    "cerrado_por": None, "anulado": False, "anulacion_motivo": "", "anulado_por": None, "anulado_en": None,
}
CERRADO = {
    **ABIERTO, "id": "8a1b2c3d-0000-4000-8000-000000000002", "vivienda": "Torre 2 – 202", "abierto": False,
    "cierre_fecha": "2026-10-23T10:00:00-05:00", "cierre_comentario": "Se habló con el arrendatario", "cerrado_por": "Laura Gómez",
}
ANULADO = {
    **ABIERTO, "id": "8a1b2c3d-0000-4000-8000-000000000003", "vivienda": "Torre 3 – 303", "abierto": False, "anulado": True,
    "anulacion_motivo": "Vivienda equivocada", "anulado_por": "Sonia Gómez", "anulado_en": "2026-10-22T08:00:00-05:00",
}


def ver(url="/infracciones/", permisos=ADMINISTRACION, registros=(ABIERTO, CERRADO, ANULADO)):
    with mock.patch("cliente_api.infracciones.listar", return_value=list(registros)):
        return cliente_con_sesion(permisos=permisos).get(url)


def detalle(registro, permisos=ADMINISTRACION):
    with mock.patch("cliente_api.infracciones.obtener", return_value=registro):
        return cliente_con_sesion(permisos=permisos).get(f"/infracciones/{registro['id']}/").content.decode()


def test_la_lista_muestra_cada_registro_con_su_estado_y_el_anulado_tachado():
    html = ver().content.decode()

    for texto in ("Torre 1 – 101", "Música a alto volumen", "20/10/2026", "21/10/2026 09:00"):
        assert texto in html
    assert ">Abierto</span>" in html and ">Cerrado</span>" in html and ">Anulado</span>" in html
    assert "<s>Torre 3 – 303</s>" in html and "Motivo: Vivienda equivocada" in html
    assert f'href="/infracciones/{ABIERTO["id"]}/"' in html


def test_hu30_el_aviso_de_r11_esta_en_la_lista_el_formulario_y_el_detalle():
    with mock.patch("cliente_api.unidades.listar", return_value=UNIDADES):
        formulario = cliente_con_sesion(permisos=ADMINISTRACION).get("/infracciones/nueva/").content.decode()

    for html in (ver().content.decode(), formulario, detalle(ABIERTO), detalle(ANULADO)):
        assert FRASE_DE_R11 in html and 'id="aviso-de-r11"' in html


def test_la_lista_vacia_invita_a_registrar_solo_a_quien_puede():
    con_permiso = ver(registros=[]).content.decode()
    sin_permiso = ver(registros=[], permisos=["infraccion.ver"]).content.decode()

    assert "Todavía no hay infracciones registradas" in con_permiso and ">Registrar infracción</a>" in con_permiso
    assert "Registrar infracción" not in sin_permiso


def test_sin_permiso_de_ver_redirige_al_inicio_en_todas_las_pantallas():
    cliente = cliente_con_sesion(permisos=["caso.crear"], tipo_usuario="Residente")

    for ruta in ("/infracciones/", "/infracciones/nueva/", f"/infracciones/{ABIERTO['id']}/"):
        assert cliente.get(ruta)["Location"] == "/inicio/"
    with mock.patch("cliente_api.infracciones.cerrar") as cerrar, mock.patch("cliente_api.infracciones.anular") as anular:
        assert cliente.post(f"/infracciones/{ABIERTO['id']}/cierre/", {"comentario": "x"})["Location"] == "/inicio/"
        assert cliente.post(f"/infracciones/{ABIERTO['id']}/anulacion/", {"motivo": "x"})["Location"] == "/inicio/"
    cerrar.assert_not_called()
    anular.assert_not_called()


def test_el_lateral_trae_infracciones_solo_para_quien_las_ve():
    def lateral(html):
        return html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    with mock.patch("cliente_api.infracciones.listar", return_value=[]):
        administracion = lateral(cliente_con_sesion(permisos=ADMINISTRACION).get("/infracciones/").content.decode())
    secretaria = lateral(cliente_con_sesion(permisos=["caso.ver_todos"], tipo_usuario="Secretaría").get("/inicio/").content.decode())

    assert 'href="/infracciones/"' in administracion and ">Infracciones</a>" in administracion
    assert ">Infracciones</a>" not in secretaria


# El formulario


def test_hu30_el_formulario_no_tiene_ningun_campo_de_sancion_multa_ni_restriccion():
    with mock.patch("cliente_api.unidades.listar", return_value=UNIDADES):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/infracciones/nueva/").content.decode()

    for campo in ('name="unidad"', 'name="fecha_hecho"', 'name="descripcion_hecho"', 'name="caso"'):
        assert campo in html
    nombres = {parte.split('"')[0] for parte in html.split('name="')[1:]}
    assert not [n for n in nombres if any(p in n for p in ("sancion", "multa", "restric", "monto", "valor"))]
    texto = html.lower()
    for palabra in ("multa", "restricción", "restriccion", "sancionar"):
        assert palabra not in texto
    assert ">Registrar y comunicar</button>" in html


def test_registrar_manda_los_datos_a_la_api_y_vuelve_con_el_aviso():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.infracciones.registrar") as registrar,
    ):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/infracciones/nueva/", {
            "unidad": UNIDADES[0]["id"], "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido", "caso": "",
        })

    assert registrar.call_args.args[1] == {
        "unidad": UNIDADES[0]["id"], "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido", "caso": None,
    }
    assert respuesta["Location"] == "/infracciones/?hecho=registrado"
    with mock.patch("cliente_api.infracciones.listar", return_value=[ABIERTO]):
        aviso = cliente_con_sesion(permisos=ADMINISTRACION).get("/infracciones/?hecho=registrado").content.decode()
    assert "comunicada a quienes tienen un vínculo con la vivienda" in aviso


def test_la_infraccion_que_nace_de_un_caso_sugiere_las_viviendas_de_su_autor():
    caso = {"id": "c1b2c3d4-0000-4000-8000-000000000001", "apartamento": "Torre 2 – 202"}
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.casos.obtener", return_value=caso) as obtener,
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/infracciones/nueva/?caso={caso['id']}").content.decode()

    assert str(obtener.call_args.args[1]) == caso["id"]
    assert "Este registro nace de un caso." in html and "<b>Torre 2 – 202</b>" in html
    assert f'<option value="{UNIDADES[1]["id"]}" selected' in html
    assert f'value="{caso["id"]}"' in html


def test_el_caso_viaja_con_el_registro_pero_la_vivienda_se_elige_a_mano():
    caso_id = "c1b2c3d4-0000-4000-8000-000000000001"
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.casos.obtener", side_effect=ErrorDeApi(404, {})),
        mock.patch("cliente_api.infracciones.registrar") as registrar,
    ):
        cliente_con_sesion(permisos=ADMINISTRACION).post("/infracciones/nueva/", {
            "unidad": UNIDADES[0]["id"], "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido", "caso": caso_id,
        })

    assert registrar.call_args.args[1]["caso"] == caso_id


def test_sin_vinculos_vigentes_el_error_de_la_api_cae_en_la_vivienda_y_conserva_lo_escrito():
    sin_destino = ErrorDeApi(400, {"unidad": ["La vivienda no tiene a quién comunicarle."]})
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.infracciones.registrar", side_effect=sin_destino),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post("/infracciones/nueva/", {
            "unidad": UNIDADES[0]["id"], "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido fuerte", "caso": "",
        }).content.decode()

    assert "La vivienda no tiene a quién comunicarle." in html and "Ruido fuerte" in html


def test_una_fecha_futura_o_sin_vivienda_no_llegan_a_la_api():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=UNIDADES),
        mock.patch("cliente_api.infracciones.registrar") as registrar,
    ):
        cliente = cliente_con_sesion(permisos=ADMINISTRACION)
        futura = cliente.post("/infracciones/nueva/", {
            "unidad": UNIDADES[0]["id"], "fecha_hecho": "2999-01-01", "descripcion_hecho": "Ruido", "caso": "",
        }).content.decode()
        sin_vivienda = cliente.post("/infracciones/nueva/", {
            "unidad": "", "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido", "caso": "",
        }).content.decode()

    registrar.assert_not_called()
    assert "La fecha del hecho no puede ser futura." in futura and "Elige la vivienda." in sin_vivienda


def test_quien_solo_ve_no_registra():
    with mock.patch("cliente_api.infracciones.registrar") as registrar:
        respuesta = cliente_con_sesion(permisos=["infraccion.ver"]).post("/infracciones/nueva/", {
            "unidad": UNIDADES[0]["id"], "fecha_hecho": "2026-10-20", "descripcion_hecho": "Ruido",
        })

    registrar.assert_not_called()
    assert respuesta["Location"] == "/inicio/"


# El detalle, el cierre y la anulación


def test_el_detalle_abierto_ofrece_cerrar_y_no_ofrece_borrar_ni_anular_a_la_administracion():
    html = detalle(ABIERTO)

    assert "Cerrar el registro" in html and ">Cerrar registro</button>" in html
    assert "Anular" not in html and "Eliminar" not in html and "Borrar" not in html
    assert "Cerrar avisa a la vivienda" in html


def test_el_superusuario_ve_ademas_la_anulacion_con_motivo():
    html = detalle(ABIERTO, permisos=SUPERUSUARIO)

    assert 'action="/infracciones/' + ABIERTO["id"] + '/anulacion/"' in html
    assert ">Anular registro</button>" in html and "Motivo de la anulación" in html


def test_un_registro_cerrado_muestra_el_cierre_y_ya_no_se_puede_cerrar():
    html = detalle(CERRADO, permisos=SUPERUSUARIO)

    assert "Se habló con el arrendatario" in html and "23/10/2026 10:00" in html
    assert "Cerrar el registro" not in html and ">Anular registro</button>" in html


def test_un_registro_anulado_se_ve_tachado_con_su_motivo_y_sin_acciones():
    html = detalle(ANULADO, permisos=SUPERUSUARIO)

    assert "<s>Torre 3 – 303</s>" in html and "Vivienda equivocada" in html and "Sonia Gómez" in html
    assert "Cerrar registro" not in html and "Anular registro" not in html


def test_cerrar_manda_el_comentario_y_vuelve_con_el_aviso():
    with mock.patch("cliente_api.infracciones.cerrar") as cerrar:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/infracciones/{ABIERTO['id']}/cierre/", {"comentario": "Resuelto"}
        )

    assert str(cerrar.call_args.args[1]) == ABIERTO["id"] and cerrar.call_args.args[2] == "Resuelto"
    assert respuesta["Location"] == f"/infracciones/{ABIERTO['id']}/?hecho=cerrado"


def test_cerrar_sin_comentario_no_llega_a_la_api():
    with mock.patch("cliente_api.infracciones.cerrar") as cerrar, mock.patch(
        "cliente_api.infracciones.obtener", return_value=ABIERTO
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/infracciones/{ABIERTO['id']}/cierre/", {"comentario": "  "}
        ).content.decode()

    cerrar.assert_not_called()
    assert "Este campo es obligatorio." in html


def test_el_409_de_ya_cerrado_se_muestra_en_el_detalle():
    ya_cerrado = ErrorDeApi(409, {"detail": "Este registro ya está cerrado."})
    with (
        mock.patch("cliente_api.infracciones.cerrar", side_effect=ya_cerrado),
        mock.patch("cliente_api.infracciones.obtener", return_value=CERRADO),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/infracciones/{CERRADO['id']}/cierre/", {"comentario": "Otra vez"}
        ).content.decode()

    assert "Este registro ya está cerrado." in html


def test_anular_manda_el_motivo_y_la_administracion_no_llega_a_anular():
    with mock.patch("cliente_api.infracciones.anular") as anular:
        super_ = cliente_con_sesion(permisos=SUPERUSUARIO).post(
            f"/infracciones/{ABIERTO['id']}/anulacion/", {"motivo": "Error de vivienda"}
        )
        admin = cliente_con_sesion(permisos=ADMINISTRACION).post(
            f"/infracciones/{ABIERTO['id']}/anulacion/", {"motivo": "Quiero borrarlo"}
        )

    assert anular.call_count == 1 and anular.call_args.args[2] == "Error de vivienda"
    assert super_["Location"] == f"/infracciones/{ABIERTO['id']}/?hecho=anulado"
    assert admin["Location"] == "/inicio/"


def test_un_registro_que_no_existe_es_404():
    with mock.patch("cliente_api.infracciones.obtener", side_effect=ErrorDeApi(404, {})):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/infracciones/{ABIERTO['id']}/")

    assert respuesta.status_code == 404


# Desde el caso


def test_hu30_el_detalle_del_caso_ofrece_registrar_la_infraccion_con_el_permiso():
    caso = {
        "id": "c1b2c3d4-0000-4000-8000-000000000001", "titulo": "Ruido", "cuerpo": "Fiesta", "estado": "REDIRIGIDO",
        "estado_nombre": "Redirigido", "prioridad": "NORMAL", "prioridad_nombre": "Normal", "autor": "Pedro Gómez",
        "apartamento": "Torre 1 – 101", "creado_en": "2026-10-20T10:00:00-05:00", "abierto": True, "respuesta": "",
        "motivo_rechazo": "", "causal_rechazo": "", "causal_rechazo_nombre": "", "foto_id": None,
        "justificacion_prioridad": "", "nota_redireccion": "", "cerrado_por": None, "cerrado_en": None,
    }
    with mock.patch("cliente_api.casos.obtener", return_value=caso):
        con_permiso = cliente_con_sesion(permisos=ADMINISTRACION).get(f"/casos/{caso['id']}/").content.decode()
        sin_permiso = cliente_con_sesion(permisos=["caso.ver_todos"]).get(f"/casos/{caso['id']}/").content.decode()

    assert f'href="/infracciones/nueva/?caso={caso["id"]}"' in con_permiso and ">Registrar infracción</a>" in con_permiso
    assert "Registrar infracción" not in sin_permiso


def test_ninguna_ruta_del_front_sanciona_ni_borra():
    from django.urls import get_resolver

    nombres = {
        patron.name for resolver in get_resolver().url_patterns
        if getattr(resolver, "app_name", "") == "infracciones" for patron in resolver.url_patterns
    }

    assert nombres == {"lista", "nueva", "detalle", "cerrar", "anular"}
