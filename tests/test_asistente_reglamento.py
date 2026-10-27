"""Paso «Reglamento» del asistente (HU-03, HU-33). La API se simula."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from cliente_api.http import ErrorDeApi
from tests.ayudantes import TORRES, cliente_con_sesion

ADMINISTRACION = ["documento.subir", "documento.ver", "documento.descargar", "conjunto.editar", "conjunto.activar"]
SIN_REGLAMENTO = {"cargado": False}
CARGADO = {
    "cargado": True,
    "nombre": "reglamento-2026.pdf",
    "peso": 2 * 1024 * 1024,
    "subido_en": "2026-10-06T10:30:00-05:00",
    "subido_por": "Laura Gómez",
}
REQUISITOS = [
    {"clave": "datos_basicos", "descripcion": "Datos básicos: nombre y dirección", "cumplido": True, "disponible": True},
    {"clave": "reglamento", "descripcion": "Reglamento cargado", "cumplido": True, "disponible": True},
]
RESUMEN = {
    "conjunto": {**TORRES, "direccion": "Calle 9 # 4-50", "color": None, "operativo": False},
    "administradores": [{"id": "1", "nombre": "Laura Gómez"}],
    "requisitos": REQUISITOS,
    "puede_activar": True,
}


def test_subir_el_reglamento_lo_manda_a_la_api_y_vuelve_al_paso():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    archivo = SimpleUploadedFile("reglamento.pdf", b"%PDF-1.7 prueba", content_type="application/pdf")
    with (
        mock.patch("cliente_api.documentos.reglamento", return_value=SIN_REGLAMENTO),
        mock.patch("cliente_api.documentos.subir_reglamento") as subir,
    ):
        respuesta = cliente.post("/conjuntos/asistente/reglamento/", {"archivo": archivo})

    assert subir.call_args.args[1].name == "reglamento.pdf"
    assert respuesta["Location"] == "/conjuntos/asistente/reglamento/?subido=1"


def test_un_archivo_que_no_termina_en_pdf_se_rechaza_sin_llamar_a_la_api():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    archivo = SimpleUploadedFile("reglamento.docx", b"un documento de texto", content_type="application/msword")
    with (
        mock.patch("cliente_api.documentos.reglamento", return_value=SIN_REGLAMENTO),
        mock.patch("cliente_api.documentos.subir_reglamento") as subir,
    ):
        html = cliente.post("/conjuntos/asistente/reglamento/", {"archivo": archivo}).content.decode()

    assert "El reglamento debe ser un archivo PDF." in html
    assert "El conjunto lo necesita para quedar operativo" in html
    subir.assert_not_called()


def test_con_reglamento_cargado_se_ven_sus_datos_y_el_enlace_para_verlo():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with mock.patch("cliente_api.documentos.reglamento", return_value=CARGADO):
        html = cliente.get("/conjuntos/asistente/reglamento/").content.decode()

    assert 'aria-current="step">6. Reglamento' in html
    assert "reglamento-2026.pdf" in html and "Laura Gómez" in html and "martes 6 de octubre de 2026" in html
    assert 'href="/conjuntos/reglamento/archivo/"' in html
    assert "este se conserva" in html


def test_el_pdf_lo_entrega_este_servidor_y_si_la_api_falla_responde_404():
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with mock.patch("cliente_api.documentos.archivo_del_reglamento", return_value=(b"%PDF-1.7", "application/pdf")):
        respuesta = cliente.get("/conjuntos/reglamento/archivo/")
    with mock.patch("cliente_api.documentos.archivo_del_reglamento", side_effect=ErrorDeApi(404, {})):
        sin_archivo = cliente.get("/conjuntos/reglamento/archivo/")
    with mock.patch("cliente_api.documentos.archivo_del_reglamento", return_value=(b"<html>", "text/html")):
        otro_tipo = cliente.get("/conjuntos/reglamento/archivo/")

    assert (respuesta.status_code, respuesta["Content-Type"], respuesta.content) == (200, "application/pdf", b"%PDF-1.7")
    assert respuesta["Content-Disposition"] == 'inline; filename="reglamento.pdf"'
    assert (sin_archivo.status_code, otro_tipo.status_code) == (404, 404)


def test_el_resumen_ya_no_espera_ningun_modulo_y_administracion_deja_operativo():
    """Desde el 2026-10-06 Administración también activa su conjunto (plan del asistente, D1 b)."""
    cliente = cliente_con_sesion(permisos=ADMINISTRACION)
    with mock.patch("cliente_api.conjuntos.resumen", return_value=RESUMEN):
        html = cliente.get("/conjuntos/asistente/resumen/").content.decode()

    assert 'aria-current="step">7. Resumen' in html
    assert "módulo que todavía no existe" not in html and "Módulo en construcción" not in html
    assert 'href="/conjuntos/asistente/reglamento/">Volver' in html
    assert "Dejar operativo" in html
    assert "Eliminar conjunto" not in html


def test_el_boton_eliminar_conjunto_solo_aparece_al_superusuario_en_el_bloque_datos():
    cliente = cliente_con_sesion(roles=["Superusuario"], tipo_usuario="Superusuario")
    with mock.patch("cliente_api.conjuntos.resumen", return_value=RESUMEN):
        html = cliente.get("/conjuntos/asistente/resumen/").content.decode()

    bloque = html.split('<section class="am-tarjeta tarjeta-contenido" aria-labelledby="titulo-datos">', 1)[1]
    bloque = bloque.split("</section>", 1)[0]
    assert "Eliminar conjunto" in bloque
    assert "¿Está seguro de eliminar el conjunto Torres del Río?" in bloque
    assert ">Sí, eliminar</button>" in bloque
    assert 'class="am-btn am-btn--secundario" type="button" data-cerrar-eliminar-conjunto>No</button>' in bloque
    assert "js/conjuntos.js" in html
    assert html.count("Eliminar conjunto") == 1


def test_superusuario_elimina_desde_el_resumen_y_vuelve_al_selector():
    cliente = cliente_con_sesion(roles=["Superusuario"], tipo_usuario="Superusuario")
    with (
        mock.patch("cliente_api.conjuntos.eliminar") as eliminar,
        mock.patch("cliente_api.conjuntos.resumen", return_value=RESUMEN),
    ):
        respuesta = cliente.post("/conjuntos/asistente/resumen/", {"accion": "eliminar"})

    eliminar.assert_called_once_with(mock.ANY)
    assert respuesta.status_code == 302
    assert respuesta["Location"] == "/conjuntos/"
    assert cliente.session["conjunto_activo"] is None
    assert cliente.session["permisos"] == []


def test_no_superusuario_no_puede_invocar_la_eliminacion_desde_el_resumen():
    cliente = cliente_con_sesion(roles=["Administrador"], tipo_usuario="Administrador")
    with (
        mock.patch("cliente_api.conjuntos.eliminar") as eliminar,
        mock.patch("cliente_api.conjuntos.resumen", return_value=RESUMEN),
    ):
        respuesta = cliente.post("/conjuntos/asistente/resumen/", {"accion": "eliminar"})

    eliminar.assert_not_called()
    assert "No tienes permiso para eliminar este conjunto." in respuesta.content.decode()
