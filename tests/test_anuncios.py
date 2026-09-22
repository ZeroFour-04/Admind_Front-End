"""Pantallas de HU-25: el tablón, publicar con alcance y editar el texto. La API se simula."""
from unittest import mock

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

APTO_101 = {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"}
ANUNCIO = {
    "id": "9f8e7d6c-0000-4000-8000-000000000001",
    "titulo": "Corte de agua",
    "cuerpo": "El jueves de 8 a 2.",
    "alcance": "conjunto",
    "unidad": None,
    "autor": "Sara Gómez",
    "publicado_en": "2026-09-22T10:00:00-05:00",
    "editado_en": None,
    "puede_editar": True,
}
SECRETARIA = ["anuncio.publicar", "anuncio.dirigir"]


def publicar(cliente, **datos):
    return cliente.post("/anuncios/nuevo/", {"titulo": "Corte de agua", "cuerpo": "El jueves de 8 a 2.", **datos})


# Formulario de publicación


def test_sin_permisos_de_anuncios_no_se_abre_el_formulario():
    respuesta = cliente_con_sesion(permisos=[]).get("/anuncios/nuevo/")

    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/anuncios/"


def test_el_formulario_no_tiene_destinatario_individual_y_avisa_sobre_las_infracciones():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]):
        html = cliente_con_sesion(permisos=SECRETARIA).get("/anuncios/nuevo/").content.decode()

    assert 'value="conjunto"' in html and 'value="vivienda"' in html
    assert "Torre 1 – 101" in html
    assert 'name="persona"' not in html and 'value="persona"' not in html
    assert "Una infracción no se comunica con un anuncio dirigido." in html


def test_con_anuncio_publicar_y_sin_anuncio_dirigir_no_se_ofrece_la_vivienda():
    with mock.patch("cliente_api.unidades.listar") as unidades:
        html = cliente_con_sesion(permisos=["anuncio.publicar"]).get("/anuncios/nuevo/").content.decode()

    unidades.assert_not_called()
    assert 'value="vivienda"' not in html
    assert 'name="unidad"' not in html


def test_con_solo_anuncio_dirigir_se_ofrece_la_vivienda():
    with mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]):
        html = cliente_con_sesion(permisos=["anuncio.dirigir"]).get("/anuncios/nuevo/").content.decode()

    assert 'value="conjunto"' not in html
    assert 'name="unidad"' in html


def test_a_una_vivienda_sin_elegirla_no_se_manda_a_la_api():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]),
        mock.patch("cliente_api.anuncios.publicar") as publicar_en_api,
    ):
        respuesta = publicar(cliente_con_sesion(permisos=SECRETARIA), alcance="vivienda")

    publicar_en_api.assert_not_called()
    assert "Elige la vivienda a la que va el anuncio." in respuesta.content.decode()


def test_publicar_a_una_vivienda_manda_el_alcance_y_la_unidad():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]),
        mock.patch("cliente_api.anuncios.publicar", return_value=ANUNCIO) as publicar_en_api,
    ):
        respuesta = publicar(cliente_con_sesion(permisos=SECRETARIA), alcance="vivienda", unidad=APTO_101["id"])

    assert publicar_en_api.call_args.args[1] == {
        "titulo": "Corte de agua",
        "cuerpo": "El jueves de 8 a 2.",
        "alcance": "vivienda",
        "unidad": APTO_101["id"],
    }
    assert respuesta["Location"] == "/anuncios/?publicado=1"


def test_publicar_al_conjunto_no_manda_vivienda():
    with (
        mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]),
        mock.patch("cliente_api.anuncios.publicar", return_value=ANUNCIO) as publicar_en_api,
    ):
        publicar(cliente_con_sesion(permisos=SECRETARIA), alcance="conjunto", unidad=APTO_101["id"])

    assert publicar_en_api.call_args.args[1]["unidad"] is None


def test_un_403_de_la_api_se_muestra_en_el_formulario():
    rechazo = ErrorDeApi(403, {"detail": "No tienes permiso para hacer esto."})
    with (
        mock.patch("cliente_api.unidades.listar", return_value=[APTO_101]),
        mock.patch("cliente_api.anuncios.publicar", side_effect=rechazo),
    ):
        respuesta = publicar(cliente_con_sesion(permisos=SECRETARIA), alcance="vivienda", unidad=APTO_101["id"])

    assert "No tienes permiso para hacer esto en el conjunto activo." in respuesta.content.decode()


# Tablón


def test_el_tablon_muestra_a_quien_va_cada_anuncio_y_solo_deja_editar_los_propios():
    anuncios = [
        ANUNCIO,
        {**ANUNCIO, "id": "9f8e7d6c-0000-4000-8000-000000000002", "titulo": "Gas", "alcance": "vivienda",
         "unidad": APTO_101, "puede_editar": False},
    ]
    with mock.patch("cliente_api.anuncios.listar", return_value=anuncios):
        html = cliente_con_sesion(permisos=SECRETARIA).get("/anuncios/").content.decode()

    assert "Para todo el conjunto" in html
    assert "Para la vivienda Torre 1 – 101" in html
    assert html.count("Editar texto") == 1
    assert "Publicar anuncio" in html


def test_un_residente_no_ve_el_boton_de_publicar():
    with mock.patch("cliente_api.anuncios.listar", return_value=[{**ANUNCIO, "puede_editar": False}]):
        html = cliente_con_sesion(permisos=["reserva.solicitar"]).get("/anuncios/").content.decode()

    assert "Publicar anuncio" not in html
    assert "Corte de agua" in html


def test_tablon_vacio():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        html = cliente_con_sesion().get("/anuncios/").content.decode()

    assert "Todavía no hay anuncios" in html


# Edición


def test_editar_manda_solo_el_texto():
    with (
        mock.patch("cliente_api.anuncios.obtener", return_value=ANUNCIO),
        mock.patch("cliente_api.anuncios.editar", return_value=ANUNCIO) as editar,
    ):
        respuesta = cliente_con_sesion(permisos=SECRETARIA).post(
            f"/anuncios/{ANUNCIO['id']}/editar/", {"titulo": "Corte de agua", "cuerpo": "Mejor el viernes."}
        )

    assert editar.call_args.args[2] == {"titulo": "Corte de agua", "cuerpo": "Mejor el viernes."}
    assert respuesta["Location"] == "/anuncios/"


def test_quien_no_lo_publico_no_ve_el_formulario_de_edicion():
    with mock.patch("cliente_api.anuncios.obtener", return_value={**ANUNCIO, "puede_editar": False}):
        html = cliente_con_sesion(permisos=SECRETARIA).get(f"/anuncios/{ANUNCIO['id']}/editar/").content.decode()

    assert "Solo quien publicó el anuncio puede editarlo." in html
    assert "<textarea" not in html


# Bandeja de notificaciones


def test_la_bandeja_muestra_los_avisos_de_la_persona():
    aviso = {
        "id": "1", "titulo": "Corte de agua", "cuerpo": "El jueves.", "origen": "anuncio",
        "referencia": ANUNCIO["id"], "creada_en": "2026-09-22T10:00:00-05:00",
    }
    with mock.patch("cliente_api.notificaciones.bandeja", return_value=[aviso]):
        html = cliente_con_sesion().get("/notificaciones/").content.decode()

    assert "Corte de agua" in html
    assert "Ver en anuncios" in html
