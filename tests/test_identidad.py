"""Pantallas de HU-21: el logo en la barra y el selector, y la pantalla de color y logo."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.conjuntos.forms import TAMANO_MAXIMO_LOGO
from cliente_api.http import ErrorDeApi
from tests.ayudantes import HUELLA, TORRES, cliente_con_sesion

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
CON_LOGO = {**TORRES, "logo": HUELLA}


# Sin logo, el nombre; nunca un espacio roto


def test_sin_logo_la_barra_muestra_el_nombre_y_ninguna_imagen():
    respuesta = cliente_con_sesion().get("/inicio/")

    html = respuesta.content.decode()
    assert "<b>Torres del Río</b>" in html
    assert "<img" not in html


def test_con_logo_la_barra_muestra_el_logo_y_tambien_el_nombre():
    respuesta = cliente_con_sesion(conjunto_activo=CON_LOGO).get("/inicio/")

    html = respuesta.content.decode()
    assert f'src="/conjuntos/logo/{HUELLA}/"' in html
    assert "<b>Torres del Río</b>" in html


def test_el_selector_muestra_el_logo_solo_de_los_conjuntos_que_lo_tienen():
    conjuntos = [
        {**CON_LOGO, "direccion": ""},
        {"id": "5d6e1f7a-0000-4000-8000-000000000002", "nombre": "Mirador", "acento": "vino", "logo": None, "direccion": ""},
    ]
    with mock.patch("cliente_api.cuentas.listar_conjuntos", return_value=conjuntos):
        html = cliente_con_sesion(conjunto_activo=None).get("/conjuntos/").content.decode()

    assert html.count('class="tarjeta-conjunto__logo"') == 1
    assert "Mirador" in html and "Torres del Río" in html


# La imagen pasa por este servidor


def test_el_logo_se_entrega_con_su_tipo_y_se_guarda_en_el_navegador():
    with mock.patch("cliente_api.conjuntos.imagen_del_logo", return_value=(PNG, "image/png")) as imagen:
        respuesta = cliente_con_sesion().get(f"/conjuntos/logo/{HUELLA}/")

    imagen.assert_called_once_with(mock.ANY, HUELLA)
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "image/png"
    assert "immutable" in respuesta["Cache-Control"]
    assert respuesta.content == PNG


def test_si_la_api_no_lo_entrega_o_no_es_una_imagen_responde_404():
    with mock.patch("cliente_api.conjuntos.imagen_del_logo", side_effect=ErrorDeApi(404, None)):
        assert cliente_con_sesion().get(f"/conjuntos/logo/{HUELLA}/").status_code == 404
    with mock.patch("cliente_api.conjuntos.imagen_del_logo", return_value=(b"<script>", "text/html")):
        assert cliente_con_sesion().get(f"/conjuntos/logo/{HUELLA}/").status_code == 404


# Pantalla de color y logo


def test_subir_el_logo_lo_manda_a_la_api_y_actualiza_la_barra():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    archivo = SimpleUploadedFile("logo.png", PNG, content_type="image/png")
    recibido = []

    def subir(request, archivo):
        recibido.append(archivo.read())
        return CON_LOGO

    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.subir_logo", side_effect=subir),
    ):
        respuesta = cliente.post("/conjuntos/identidad/", {"accion": "logo", "archivo": archivo})

    assert recibido == [PNG]
    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/conjuntos/identidad/?guardado=1"
    assert cliente.session["conjunto_activo"]["logo"] == HUELLA


def test_un_logo_demasiado_pesado_no_se_manda_a_la_api():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    archivo = SimpleUploadedFile("logo.png", PNG + b"\x00" * TAMANO_MAXIMO_LOGO, content_type="image/png")
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.subir_logo") as subir,
    ):
        respuesta = cliente.post("/conjuntos/identidad/", {"accion": "logo", "archivo": archivo})

    subir.assert_not_called()
    assert "El logo no puede pesar más de 512 KB." in respuesta.content.decode()


def test_el_rechazo_de_la_api_por_tipo_real_se_muestra_junto_al_archivo():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    archivo = SimpleUploadedFile("logo.png", b"hola", content_type="image/png")
    rechazo = ErrorDeApi(400, {"archivo": ["El archivo no es una imagen PNG, JPG o WebP."]})
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.subir_logo", side_effect=rechazo),
    ):
        respuesta = cliente.post("/conjuntos/identidad/", {"accion": "logo", "archivo": archivo})

    assert respuesta.status_code == 200
    assert "El archivo no es una imagen PNG, JPG o WebP." in respuesta.content.decode()


def test_cambiar_el_color_cambia_el_de_toda_la_pagina():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.cambiar_acento", return_value={**TORRES, "acento": "vino"}) as cambiar,
    ):
        cliente.post("/conjuntos/identidad/", {"accion": "color", "acento": "vino"})
        pagina = cliente.get("/conjuntos/identidad/?guardado=1").content.decode()

    cambiar.assert_called_once_with(mock.ANY, "vino")
    assert '<html lang="es-CO" data-acento="vino">' in pagina
    assert "Cambios guardados." in pagina


def test_sin_conjunto_branding_la_api_responde_403_y_la_pantalla_lo_dice():
    with mock.patch("cliente_api.conjuntos.identidad", side_effect=ErrorDeApi(403, {"detail": "No tienes permiso."})):
        html = cliente_con_sesion().get("/conjuntos/identidad/").content.decode()

    assert "No tienes permiso para hacer esto en el conjunto activo." in html


def test_el_logo_viaja_a_la_api_como_formulario_multipart():
    from cliente_api import conjuntos as api_conjuntos

    archivo = SimpleUploadedFile("logo.png", PNG, content_type="image/png")
    peticion = mock.Mock(session={"token_api": "token-de-prueba"})
    with mock.patch("cliente_api.http.requests.request") as enviar:
        enviar.return_value = mock.Mock(status_code=200, content=b"{}", json=lambda: CON_LOGO)
        api_conjuntos.subir_logo(peticion, archivo)

    argumentos = enviar.call_args.kwargs
    assert enviar.call_args.args[0] == "PUT"
    assert argumentos["files"] == {"archivo": ("logo.png", PNG, "image/png")}
    assert "json" not in argumentos
    assert argumentos["headers"]["Authorization"] == "Token token-de-prueba"
