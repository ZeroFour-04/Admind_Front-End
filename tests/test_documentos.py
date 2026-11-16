"""Pantalla «Documentos» (HU-33): reglamento y manual de convivencia. La API se simula: el front muestra, decide ella."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

RESIDENTE = ["documento.ver"]
ADMINISTRACION = ["documento.ver", "documento.subir", "documento.descargar"]
REGLAMENTO = {
    "tipo": "reglamento", "tipo_nombre": "Reglamento de propiedad horizontal", "cargado": True,
    "id": "9a1b2c3d-0000-4000-8000-000000000001", "nombre": "reglamento-2026.pdf", "peso": 2 * 1024 * 1024,
    "subido_en": "2026-10-06T10:30:00-05:00", "subido_por": "Laura Gómez",
}
SIN_MANUAL = {"tipo": "manual", "tipo_nombre": "Manual de convivencia", "cargado": False}
MANUAL = {
    **REGLAMENTO, "tipo": "manual", "tipo_nombre": "Manual de convivencia",
    "id": "9a1b2c3d-0000-4000-8000-000000000002", "nombre": "manual.pdf", "peso": 300 * 1024,
}
VERSIONES = [
    {"id": "9a1b2c3d-0000-4000-8000-000000000011", "nombre": "reglamento-2026.pdf", "peso": 2048,
     "subido_en": "2026-10-20T09:00:00-05:00", "subido_por": "Laura Gómez", "vigente": True},
    {"id": "9a1b2c3d-0000-4000-8000-000000000012", "nombre": "reglamento.pdf", "peso": 1024,
     "subido_en": "2026-10-06T10:30:00-05:00", "subido_por": "Camilo Ruiz", "vigente": False},
]


def ver(permisos=RESIDENTE, documentos=(REGLAMENTO, SIN_MANUAL), tipo_usuario="Residente", url="/documentos/"):
    with mock.patch("cliente_api.documentos.vigentes", return_value=list(documentos)):
        return cliente_con_sesion(permisos=permisos, tipo_usuario=tipo_usuario).get(url)


def pdf():
    return SimpleUploadedFile("manual.pdf", b"%PDF-1.7 manual", content_type="application/pdf")


def test_hu33_el_residente_ve_las_dos_tarjetas_y_no_ve_subir_ni_versiones():
    html = ver().content.decode()

    assert "Reglamento de propiedad horizontal" in html and "reglamento-2026.pdf" in html
    assert "Manual de convivencia" in html and ">Sin cargar</span>" in html
    assert 'href="/documentos/reglamento/archivo/"' in html and ">Descargar reglamento de propiedad horizontal</a>" in html
    assert "Subir" not in html and "Versiones" not in html and "enctype" not in html


def test_un_documento_cargado_dice_quien_lo_subio_y_cuanto_pesa():
    html = ver(documentos=(REGLAMENTO, MANUAL)).content.decode()

    assert "Laura Gómez" in html and "MB" in html and "KB" in html and "6 de octubre de 2026" in html
    assert 'href="/documentos/manual/archivo/"' in html and "Sin cargar" not in html


def test_administracion_ve_subir_en_cada_tarjeta_y_las_versiones_si_tiene_el_permiso():
    html = ver(permisos=ADMINISTRACION, tipo_usuario="Administrador").content.decode()

    assert 'action="/documentos/reglamento/subir/"' in html and 'action="/documentos/manual/subir/"' in html
    assert "Subir versión nueva" in html and "Subir manual de convivencia" in html
    assert 'href="/documentos/reglamento/versiones/"' in html
    sin_versiones = ver(permisos=["documento.ver", "documento.subir"], tipo_usuario="Administrador").content.decode()
    assert "Subir versión nueva" in sin_versiones and "/versiones/" not in sin_versiones


def test_sin_permiso_de_documentos_redirige_al_inicio():
    respuesta = cliente_con_sesion(permisos=["visitante.registrar"], tipo_usuario="Vigilancia").get("/documentos/")

    assert respuesta.status_code == 302 and respuesta["Location"] == "/inicio/"


def test_el_lateral_trae_documentos_para_quien_los_ve_y_no_para_vigilancia():
    def lateral(html):
        return html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    residente = lateral(ver().content.decode())
    with mock.patch("cliente_api.documentos.vigentes", return_value=[]):
        vigilancia = lateral(
            cliente_con_sesion(permisos=["visitante.registrar"], tipo_usuario="Vigilancia").get("/inicio/").content.decode()
        )

    assert 'href="/documentos/"' in residente and ">Documentos</a>" in residente
    assert ">Documentos</a>" not in vigilancia


def test_subir_manda_el_tipo_y_el_archivo_y_vuelve_con_el_aviso():
    with mock.patch("cliente_api.documentos.subir") as subir:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).post("/documentos/manual/subir/", {"archivo": pdf()})

    assert subir.call_args.args[1] == "manual" and subir.call_args.args[2].name == "manual.pdf"
    assert respuesta["Location"] == "/documentos/?hecho=subido"
    with mock.patch("cliente_api.documentos.vigentes", return_value=[REGLAMENTO, MANUAL]):
        aviso = cliente_con_sesion(permisos=ADMINISTRACION).get("/documentos/?hecho=subido").content.decode()
    assert "la versión anterior se conserva" in aviso


def test_un_archivo_que_no_es_pdf_no_llega_a_la_api():
    texto = SimpleUploadedFile("manual.txt", b"hola", content_type="text/plain")
    with (
        mock.patch("cliente_api.documentos.subir") as subir,
        mock.patch("cliente_api.documentos.vigentes", return_value=[REGLAMENTO, SIN_MANUAL]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post("/documentos/manual/subir/", {"archivo": texto}).content.decode()

    subir.assert_not_called()
    assert "El documento debe ser un archivo PDF." in html


def test_si_la_api_rechaza_el_archivo_el_error_cae_bajo_el_campo():
    rechazo = ErrorDeApi(400, {"archivo": ["El archivo no es un PDF."]})
    with (
        mock.patch("cliente_api.documentos.subir", side_effect=rechazo),
        mock.patch("cliente_api.documentos.vigentes", return_value=[REGLAMENTO, SIN_MANUAL]),
    ):
        html = cliente_con_sesion(permisos=ADMINISTRACION).post("/documentos/manual/subir/", {"archivo": pdf()}).content.decode()

    assert "El archivo no es un PDF." in html and 'aria-invalid="true"' in html


def test_quien_no_sube_no_puede_subir_ni_con_la_direccion():
    with mock.patch("cliente_api.documentos.subir") as subir:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post("/documentos/manual/subir/", {"archivo": pdf()})

    subir.assert_not_called()
    assert respuesta["Location"] == "/documentos/"


def test_un_tipo_que_no_existe_es_404_en_todas_las_rutas():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)

    for ruta in ("actas/archivo/", "actas/versiones/", "actas/subir/"):
        metodo = cliente.post if ruta.endswith("subir/") else cliente.get
        assert metodo(f"/documentos/{ruta}").status_code == 404


def test_descargar_pasa_el_pdf_de_la_api_sin_enlace_directo():
    with mock.patch("cliente_api.documentos.archivo", return_value=(b"%PDF-1.7 x", "application/pdf")) as archivo:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).get("/documentos/manual/archivo/")

    assert archivo.call_args.args[1] == "manual"
    assert (respuesta.status_code, respuesta["Content-Type"], respuesta.content) == (200, "application/pdf", b"%PDF-1.7 x")
    assert 'filename="manual.pdf"' in respuesta["Content-Disposition"]


def test_si_la_api_no_tiene_el_documento_la_descarga_es_404():
    with mock.patch("cliente_api.documentos.archivo", side_effect=ErrorDeApi(404, {})):
        assert cliente_con_sesion(permisos=RESIDENTE).get("/documentos/manual/archivo/").status_code == 404


def test_las_versiones_dicen_cual_es_la_vigente_y_se_descargan_una_a_una():
    with mock.patch("cliente_api.documentos.versiones", return_value=VERSIONES):
        html = cliente_con_sesion(permisos=ADMINISTRACION).get("/documentos/reglamento/versiones/").content.decode()

    assert ">Vigente</span>" in html and ">Archivada</span>" in html
    assert html.index("reglamento-2026.pdf") < html.index("Camilo Ruiz")
    assert f'href="/documentos/reglamento/versiones/{VERSIONES[1]["id"]}/archivo/"' in html
    assert "auditoría" in html


def test_las_versiones_son_solo_para_quien_tiene_documento_descargar():
    with (
        mock.patch("cliente_api.documentos.versiones") as versiones,
        mock.patch("cliente_api.documentos.archivo_de_version") as archivo,
    ):
        cliente = cliente_con_sesion(permisos=["documento.ver", "documento.subir"])
        lista = cliente.get("/documentos/reglamento/versiones/")
        una = cliente.get(f"/documentos/reglamento/versiones/{VERSIONES[1]['id']}/archivo/")

    versiones.assert_not_called()
    archivo.assert_not_called()
    assert lista["Location"] == "/documentos/" and una["Location"] == "/documentos/"


def test_descargar_una_version_archivada_pasa_el_pdf():
    with mock.patch("cliente_api.documentos.archivo_de_version", return_value=(b"%PDF-1.7 viejo", "application/pdf")) as archivo:
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(
            f"/documentos/reglamento/versiones/{VERSIONES[1]['id']}/archivo/"
        )

    assert archivo.call_args.args[1:] == ("reglamento", mock.ANY)
    assert respuesta.content == b"%PDF-1.7 viejo"


def test_el_asistente_sigue_usando_las_funciones_del_reglamento():
    # El paso 6 del asistente no cambió: sigue subiendo y leyendo el reglamento por las mismas tres funciones.
    from cliente_api import documentos

    assert all(callable(getattr(documentos, nombre)) for nombre in ("reglamento", "subir_reglamento", "archivo_del_reglamento"))
