"""Pantallas de HU-21: la foto en la barra y el selector, y la pantalla de color y foto."""
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from apps.conjuntos.forms import TAMANO_MAXIMO_LOGO
from cliente_api.http import ErrorDeApi
from tests.ayudantes import HUELLA, TORRES, cliente_con_sesion

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
CON_LOGO = {**TORRES, "logo": HUELLA}
MARCADOR = 'foto-conjunto--vacia" aria-hidden="true">TR</span>'


# Sin foto, un marcador con las iniciales; nunca un espacio roto


def test_sin_foto_la_barra_muestra_las_iniciales_y_el_nombre_sin_ninguna_imagen():
    respuesta = cliente_con_sesion().get("/inicio/")

    html = respuesta.content.decode()
    assert "<b>Torres del Río</b>" in html
    assert MARCADOR in html
    assert "<img" not in html


def test_la_barra_muestra_el_tipo_de_usuario_y_el_enlace_al_perfil():
    html = cliente_con_sesion(tipo_usuario="Administrador").get("/inicio/").content.decode()

    assert "Administrador" in html
    assert 'href="/perfil/" aria-label="Ver perfil del usuario"' in html


def test_la_barra_trae_el_boton_que_abre_el_lateral_en_pantallas_angostas():
    html = cliente_con_sesion().get("/inicio/").content.decode()

    assert 'aria-controls="menu-lateral" aria-expanded="false" data-abrir-menu' in html
    assert '<nav class="am-lateral" id="menu-lateral"' in html
    assert "js/lateral.js" in html


def test_el_lateral_trae_en_el_pie_lo_que_la_barra_oculta_en_pantallas_angostas():
    html = cliente_con_sesion(tipo_usuario="Secretaría").get("/inicio/").content.decode()
    pie = html.split('<div class="am-lateral__pie">', 1)[1].split("</div>", 1)[0]

    assert '<header class="am-barra am-barra--con-menu">' in html
    assert ">Secretaría</span>" in pie
    assert 'href="/conjuntos/">Cambiar de conjunto</a>' in pie


@pytest.mark.parametrize("rol", ["Superusuario", "Administrador", "Secretaría"])
def test_el_lateral_muestra_usuarios_y_apartamentos_solo_a_roles_autorizados(rol):
    html = cliente_con_sesion(roles=[rol], tipo_usuario=rol).get("/inicio/").content.decode()

    assert ">Usuarios</a>" in html
    assert ">Apartamentos y parqueaderos</a>" in html


@pytest.mark.parametrize("rol", ["Residente", "Vigilancia"])
def test_el_lateral_oculta_usuarios_y_apartamentos_a_los_demas_roles(rol):
    html = cliente_con_sesion(roles=[rol], tipo_usuario=rol).get("/inicio/").content.decode()

    assert ">Usuarios</a>" not in html
    assert ">Apartamentos y parqueaderos</a>" not in html


def test_con_foto_la_barra_muestra_la_foto_y_tambien_el_nombre():
    respuesta = cliente_con_sesion(conjunto_activo=CON_LOGO).get("/inicio/")

    html = respuesta.content.decode()
    assert f'src="/conjuntos/logo/{HUELLA}/"' in html
    assert "<b>Torres del Río</b>" in html
    assert "foto-conjunto--vacia" not in html


def test_el_selector_muestra_la_foto_o_el_marcador_de_cada_conjunto():
    conjuntos = [
        {**CON_LOGO, "direccion": ""},
        {"id": "5d6e1f7a-0000-4000-8000-000000000002", "nombre": "Mirador", "acento": "vino", "logo": None, "direccion": ""},
    ]
    with mock.patch("cliente_api.cuentas.listar_conjuntos", return_value=conjuntos):
        html = cliente_con_sesion(conjunto_activo=None).get("/conjuntos/").content.decode()

    assert html.count('class="foto-conjunto foto-conjunto--tarjeta"') == 1
    assert 'foto-conjunto--tarjeta foto-conjunto--vacia" aria-hidden="true">M</span>' in html
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
    assert "La foto no puede pesar más de 512 KB." in respuesta.content.decode()


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

    cambiar.assert_called_once_with(mock.ANY, "vino", None)
    assert '<html lang="es-CO" data-acento="vino">' in pagina
    assert "Cambios guardados." in pagina


# Color propio


PROPIO = {**TORRES, "acento": "personalizado", "color": "#1a8fe3"}


def test_un_color_propio_se_manda_con_el_acento_personalizado_y_pinta_toda_la_pagina():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.cambiar_acento", return_value=PROPIO) as cambiar,
    ):
        cliente.post("/conjuntos/identidad/", {"accion": "color", "acento": "personalizado", "color": "#1a8fe3"})
        pagina = cliente.get("/conjuntos/identidad/").content.decode()

    cambiar.assert_called_once_with(mock.ANY, "personalizado", "#1a8fe3")
    assert cliente.session["conjunto_activo"]["color"] == "#1a8fe3"
    # Sin bloque en colores.css: los tonos van en línea sobre el mismo elemento.
    assert '<html lang="es-CO" data-acento="personalizado" style="--acento-50:#e8f4fc;--acento-600:#1a8fe3;' in pagina


def test_con_un_acento_del_catalogo_no_se_manda_el_color_del_selector():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.cambiar_acento", return_value=TORRES) as cambiar,
    ):
        # El selector de color del navegador siempre manda su valor, aunque no se haya elegido.
        cliente.post("/conjuntos/identidad/", {"accion": "color", "acento": "ocre", "color": "#1a8fe3"})

    cambiar.assert_called_once_with(mock.ANY, "ocre", None)


def test_personalizado_sin_color_no_se_manda_a_la_api():
    cliente = cliente_con_sesion(permisos=["conjunto.branding"])
    with (
        mock.patch("cliente_api.conjuntos.identidad", return_value=TORRES),
        mock.patch("cliente_api.conjuntos.cambiar_acento") as cambiar,
    ):
        respuesta = cliente.post("/conjuntos/identidad/", {"accion": "color", "acento": "personalizado", "color": ""})

    cambiar.assert_not_called()
    assert "Elige el color del conjunto." in respuesta.content.decode()


def test_un_color_muy_claro_se_guarda_y_solo_se_advierte():
    claro = {**TORRES, "acento": "personalizado", "color": "#fff8c4"}
    with mock.patch("cliente_api.conjuntos.identidad", return_value=claro):
        html = cliente_con_sesion(conjunto_activo=claro, permisos=["conjunto.branding"]).get("/conjuntos/identidad/").content.decode()

    assert "el texto blanco de los botones se lee con dificultad" in html
    assert '<span x-text="contraste">1.1</span>' in html
    aviso = html.split('class="aviso-legibilidad"')[1].split(">")[0]
    assert "display:none" not in aviso


def test_un_color_propio_oscuro_no_muestra_la_advertencia():
    oscuro = {**TORRES, "acento": "personalizado", "color": "#0b4f8a"}
    with mock.patch("cliente_api.conjuntos.identidad", return_value=oscuro):
        html = cliente_con_sesion(permisos=["conjunto.branding"]).get("/conjuntos/identidad/").content.decode()

    aviso = html.split('class="aviso-legibilidad"')[1].split(">")[0]
    assert "display:none" in aviso


def test_el_asistente_crea_el_conjunto_con_un_color_propio():
    cliente = cliente_con_sesion(permisos=["conjunto.crear"])
    datos = {"nombre": "Mirador", "direccion": "", "acento": "personalizado", "color": "#7a3cc2"}
    with mock.patch("cliente_api.conjuntos.crear", return_value={"conjunto_activo": PROPIO}) as crear:
        cliente.post("/conjuntos/nuevo/", datos)

    assert crear.call_args.args[1] == datos


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


# Ícono de la pestaña del navegador


def test_sin_foto_la_pestana_usa_el_icono_de_admind():
    html = cliente_con_sesion().get("/inicio/").content.decode()

    assert 'rel="icon" href="/static/img/favicon.ico"' in html
    assert "/conjuntos/logo/" not in html.split("</head>")[0]


def test_con_foto_la_pestana_usa_la_foto_del_conjunto():
    head = cliente_con_sesion(conjunto_activo=CON_LOGO).get("/inicio/").content.decode().split("</head>")[0]

    assert f'rel="icon" href="/conjuntos/logo/{HUELLA}/"' in head
    assert "/static/img/favicon" not in head


def test_sin_sesion_la_pestana_usa_el_icono_de_admind():
    html = Client().get("/").content.decode()

    assert 'rel="icon" href="/static/img/favicon.ico"' in html
