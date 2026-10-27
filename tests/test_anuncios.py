"""Pantallas de HU-25: el tablón, publicar con alcance y con fotos, y editar el texto. La API se simula."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.anuncios.forms import MAXIMO_DE_FOTOS, TAMANO_MAXIMO_FOTO
from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

APTO_101 = {"id": "7a1b2c3d-0000-4000-8000-000000000101", "nombre": "Torre 1 – 101"}
# Basta la firma de cada formato: el front no abre la imagen, solo la pasa.
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
FOTO_1 = "5b6c7d8e-0000-4000-8000-0000000000f1"
FOTO_2 = "5b6c7d8e-0000-4000-8000-0000000000f2"
ANUNCIO = {
    "id": "9f8e7d6c-0000-4000-8000-000000000001",
    "titulo": "Corte de agua",
    "cuerpo": "El jueves de 8 a 2.",
    "fotos": [],
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


def foto(nombre="fuga.png", contenido=PNG, tipo="image/png"):
    return SimpleUploadedFile(nombre, contenido, content_type=tipo)


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


# Publicar con fotos


def test_el_formulario_ofrece_subir_varias_fotos_y_advierte_sobre_los_datos_personales():
    html = cliente_con_sesion(permisos=["anuncio.publicar"]).get("/anuncios/nuevo/").content.decode()

    assert 'enctype="multipart/form-data"' in html
    assert 'type="file" id="id_fotos" name="fotos"' in html
    assert " multiple" in html
    assert "Hasta 4 fotos PNG, JPG o WebP, de hasta 5 MB cada una." in html
    assert "Una foto donde se reconoce a una persona es un dato personal" in html


def test_publicar_con_fotos_las_manda_aparte_de_los_datos():
    recibidas = []

    def publicar_en_api(request, datos, fotos):
        # Se leen aquí porque al terminar la petición los archivos ya están cerrados.
        recibidas.extend((archivo.name, archivo.read(), archivo.content_type) for archivo in fotos)
        return ANUNCIO

    with mock.patch("cliente_api.anuncios.publicar", side_effect=publicar_en_api) as api:
        respuesta = publicar(
            cliente_con_sesion(permisos=["anuncio.publicar"]),
            alcance="conjunto",
            fotos=[foto("fuga.png"), foto("llave.jpg", JPG, "image/jpeg")],
        )

    assert api.call_args.args[1] == {
        "titulo": "Corte de agua",
        "cuerpo": "El jueves de 8 a 2.",
        "alcance": "conjunto",
        "unidad": None,
    }
    assert recibidas == [("fuga.png", PNG, "image/png"), ("llave.jpg", JPG, "image/jpeg")]
    assert respuesta["Location"] == "/anuncios/?publicado=1"


def test_publicar_sin_fotos_manda_la_lista_vacia():
    with mock.patch("cliente_api.anuncios.publicar", return_value=ANUNCIO) as api:
        publicar(cliente_con_sesion(permisos=["anuncio.publicar"]), alcance="conjunto")

    assert api.call_args.args[2] == []


def test_con_mas_fotos_que_el_tope_no_se_manda_a_la_api():
    fotos = [foto(f"foto-{numero}.png") for numero in range(MAXIMO_DE_FOTOS + 1)]
    with mock.patch("cliente_api.anuncios.publicar") as api:
        respuesta = publicar(cliente_con_sesion(permisos=["anuncio.publicar"]), alcance="conjunto", fotos=fotos)

    api.assert_not_called()
    assert "Un anuncio lleva hasta 4 fotos." in respuesta.content.decode()


def test_una_foto_demasiado_pesada_no_se_manda_a_la_api():
    pesada = foto("grande.png", PNG + b"\x00" * TAMANO_MAXIMO_FOTO)
    with mock.patch("cliente_api.anuncios.publicar") as api:
        respuesta = publicar(cliente_con_sesion(permisos=["anuncio.publicar"]), alcance="conjunto", fotos=[pesada])

    api.assert_not_called()
    assert "«grande.png» pesa más de 5 MB." in respuesta.content.decode()


def test_el_rechazo_de_la_api_por_una_foto_se_muestra_junto_al_campo():
    rechazo = ErrorDeApi(400, {"fotos": ["La foto 1 no es una imagen PNG, JPG o WebP."]})
    with mock.patch("cliente_api.anuncios.publicar", side_effect=rechazo):
        respuesta = publicar(
            cliente_con_sesion(permisos=["anuncio.publicar"]),
            alcance="conjunto",
            fotos=[foto("notas.png", b"hola, no soy una imagen")],
        )

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert '<span class="am-campo__error" id="id_fotos-error">La foto 1 no es una imagen PNG, JPG o WebP.</span>' in html


def test_el_anuncio_viaja_en_json_sin_fotos_y_como_formulario_multipart_con_fotos():
    from cliente_api import anuncios as api_anuncios

    datos = {"titulo": "Corte de agua", "cuerpo": "El jueves de 8 a 2.", "alcance": "conjunto", "unidad": None}
    peticion = mock.Mock(session={"token_api": "token-de-prueba"})
    with mock.patch("cliente_api.http.requests.request") as enviar:
        enviar.return_value = mock.Mock(status_code=201, content=b"{}", json=lambda: ANUNCIO)
        api_anuncios.publicar(peticion, datos)
        solo_texto = enviar.call_args.kwargs
        api_anuncios.publicar(peticion, datos, [foto("fuga.png"), foto("llave.jpg", JPG, "image/jpeg")])
        con_fotos = enviar.call_args.kwargs

    assert solo_texto["json"] == datos and "files" not in solo_texto
    assert con_fotos["data"] == datos and "json" not in con_fotos
    assert con_fotos["files"] == [
        ("fotos", ("fuga.png", PNG, "image/png")),
        ("fotos", ("llave.jpg", JPG, "image/jpeg")),
    ]


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


# Fotos en el tablón


def test_el_tablon_muestra_una_miniatura_por_foto_que_abre_la_foto_completa():
    con_fotos = {**ANUNCIO, "fotos": [FOTO_1, FOTO_2]}
    sin_fotos = {**ANUNCIO, "id": "9f8e7d6c-0000-4000-8000-000000000002", "titulo": "Gas"}
    with mock.patch("cliente_api.anuncios.listar", return_value=[con_fotos, sin_fotos]):
        html = cliente_con_sesion().get("/anuncios/").content.decode()

    url = f"/anuncios/{ANUNCIO['id']}/fotos/{FOTO_1}/"
    assert f'href="{url}" target="_blank" rel="noopener"' in html
    assert f'<img src="{url}" alt="Foto 1 de 2 del anuncio Corte de agua"' in html
    assert 'alt="Foto 2 de 2 del anuncio Corte de agua"' in html
    # Una sola galería: el anuncio sin fotos no pinta la suya.
    assert html.count('class="fotos-anuncio"') == 1


def test_la_foto_se_entrega_con_el_tipo_de_la_api_y_cache_privada():
    with mock.patch("cliente_api.anuncios.foto", return_value=(JPG, "image/jpeg")) as pedir_foto:
        respuesta = cliente_con_sesion().get(f"/anuncios/{ANUNCIO['id']}/fotos/{FOTO_1}/")

    assert respuesta.status_code == 200
    assert respuesta.content == JPG
    assert respuesta["Content-Type"] == "image/jpeg"
    assert respuesta["Cache-Control"] == "private, max-age=31536000, immutable"
    assert [str(argumento) for argumento in pedir_foto.call_args.args[1:]] == [ANUNCIO["id"], FOTO_1]


def test_la_foto_que_la_api_no_entrega_o_que_no_es_imagen_responde_404():
    url = f"/anuncios/{ANUNCIO['id']}/fotos/{FOTO_1}/"
    with mock.patch("cliente_api.anuncios.foto", side_effect=ErrorDeApi(404, {"detail": "No encontrado."})):
        assert cliente_con_sesion().get(url).status_code == 404
    with mock.patch("cliente_api.anuncios.foto", return_value=(b"<script>", "text/html")):
        assert cliente_con_sesion().get(url).status_code == 404


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


def test_editar_muestra_las_fotos_y_no_deja_cambiarlas():
    with mock.patch("cliente_api.anuncios.obtener", return_value={**ANUNCIO, "fotos": [FOTO_1]}):
        html = cliente_con_sesion(permisos=SECRETARIA).get(f"/anuncios/{ANUNCIO['id']}/editar/").content.decode()

    assert f'<img src="/anuncios/{ANUNCIO["id"]}/fotos/{FOTO_1}/" alt="Foto 1 de 1 del anuncio Corte de agua"' in html
    assert "a quién va y las fotos no se cambian" in html
    assert 'type="file"' not in html


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
