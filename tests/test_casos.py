"""Formulario y bandeja personal de casos."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

RESIDENTE = ["area.ver", "caso.crear"]
CASO = {
    "id": "6f7a8b9c-0000-4000-8000-000000000001",
    "titulo": "Fuga de agua",
    "cuerpo": "Hay una fuga en el pasillo.",
    "estado": "ABIERTO",
    "prioridad": "NORMAL",
    "motivo_rechazo": "",
    "autor": "Pedro Gómez",
    "apartamento": "Torre 1 - Apto 402",
    "creado_en": "2026-10-12T11:00:00-05:00",
    "foto_id": "7f7a8b9c-0000-4000-8000-000000000001",
}
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


def test_residente_ve_el_boton_crear_caso_y_su_historial():
    with mock.patch("cliente_api.casos.listar", return_value=[CASO]) as listar:
        html = cliente_con_sesion(permisos=RESIDENTE, tipo_usuario="Residente").get("/casos/").content.decode()

    listar.assert_called_once()
    assert ">Crear caso</a>" in html
    assert 'aria-label="Mis solicitudes"' in html
    assert 'href="/solicitudes/">Reservas</a>' in html
    assert '<span class="am-pestana am-es-activa" aria-current="page">Casos</span>' in html
    assert "Fuga de agua" in html
    assert ">En revisión</span>" in html
    assert 'am-pastilla--tramite">En revisión</span>' in html
    assert "Fecha: 12/10/2026 11:00" in html
    assert "Hay una fuga en el pasillo." in html
    assert "Residente: Pedro Gómez" not in html
    assert f'/casos/{CASO["id"]}/fotos/{CASO["foto_id"]}/' in html


def test_residente_abre_el_caso_y_ve_la_razon_de_rechazo():
    caso = {
        **CASO,
        "id": "6f7a8b9c-0000-4000-8000-000000000002",
        "estado": "RECHAZADO",
        "motivo_rechazo": "Falta indicar la ubicación exacta.",
    }
    with mock.patch("cliente_api.casos.listar", return_value=[caso]):
        html = cliente_con_sesion(permisos=RESIDENTE).get("/casos/").content.decode()

    assert "<details" in html and "Falta indicar la ubicación exacta." in html
    assert "Razón del rechazo" in html


def test_secretaria_ve_los_casos_del_conjunto_con_residente_unidad_y_fecha():
    permisos = ["caso.ver_todos", "caso.gestionar"]
    with mock.patch("cliente_api.casos.listar", return_value=[CASO]):
        html = cliente_con_sesion(permisos=permisos, tipo_usuario="Secretaría").get("/casos/").content.decode()

    assert "Fuga de agua" in html
    assert "Residente: Pedro Gómez" in html
    assert "Apartamento: Torre 1 - Apto 402" in html
    assert "12/10/2026 11:00" in html
    assert "Crear caso" not in html
    assert "Rechazar" in html
    assert "Redirigir" in html
    assert 'name="motivo"' in html


def test_secretaria_rechaza_con_motivo_y_regresa_al_listado():
    permisos = ["caso.gestionar"]
    with mock.patch("cliente_api.casos.gestionar", return_value={}) as gestionar:
        respuesta = cliente_con_sesion(permisos=permisos).post(
            f"/casos/{CASO['id']}/rechazar/",
            {"motivo": "Falta indicar la ubicación exacta."},
        )

    assert str(gestionar.call_args.args[1]) == CASO["id"]
    assert gestionar.call_args.args[2:] == ("rechazar", {"motivo": "Falta indicar la ubicación exacta."})
    assert respuesta["Location"] == "/casos/?gestion=rechazar"


def test_secretaria_redirige_a_administracion():
    permisos = ["caso.gestionar"]
    with mock.patch("cliente_api.casos.gestionar", return_value={}) as gestionar:
        respuesta = cliente_con_sesion(permisos=permisos).post(f"/casos/{CASO['id']}/redirigir/")

    assert str(gestionar.call_args.args[1]) == CASO["id"]
    assert gestionar.call_args.args[2:] == ("redirigir", {})
    assert respuesta["Location"] == "/casos/?gestion=redirigir"


def test_el_formulario_muestra_campos_foto_y_botones_solicitados():
    html = cliente_con_sesion(permisos=RESIDENTE).get("/casos/nuevo/").content.decode()

    assert 'enctype="multipart/form-data"' in html
    assert "Título o motivo" in html and "Caso" in html and "Subir una foto o imagen" in html
    assert 'accept=".png,.jpg,.jpeg,.webp,image/png,image/jpeg,image/webp"' in html
    assert ">Cancelar</a>" in html and ">Crear caso</button>" in html


def test_crear_caso_envia_texto_y_foto_y_regresa_a_la_pestana():
    foto = SimpleUploadedFile("evidencia.png", PNG, content_type="image/png")
    with mock.patch("cliente_api.casos.crear", return_value=CASO) as crear:
        respuesta = cliente_con_sesion(permisos=RESIDENTE).post(
            "/casos/nuevo/",
            {"titulo": "Fuga de agua", "caso": "Hay una fuga en el pasillo.", "foto": foto},
        )

    assert crear.call_args.args[1] == {"titulo": "Fuga de agua", "caso": "Hay una fuga en el pasillo."}
    assert crear.call_args.args[2].name == "evidencia.png"
    assert respuesta["Location"] == "/casos/?creado=1"


def test_el_error_de_la_api_se_muestra_y_no_parece_una_creacion_exitosa():
    with mock.patch(
        "cliente_api.casos.crear",
        side_effect=ErrorDeApi(400, {"foto": ["El archivo no es una imagen PNG, JPG o WebP."]}),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE).post(
            "/casos/nuevo/",
            {"titulo": "Daño", "caso": "Texto", "foto": SimpleUploadedFile("mal.png", b"texto")},
        ).content.decode()

    assert "El archivo no es una imagen PNG, JPG o WebP." in html
    assert "Tu caso quedó creado" not in html


def test_no_se_muestra_el_acceso_a_casos_a_quien_no_tiene_permiso():
    with mock.patch("cliente_api.anuncios.listar", return_value=[]):
        html = cliente_con_sesion(permisos=["area.ver"]).get("/anuncios/").content.decode()

    assert ">Casos</a>" not in html


def test_residente_ve_estados_aprobado_y_rechazado_con_sus_colores():
    casos = [
        {
            **CASO,
            "id": "6f7a8b9c-0000-4000-8000-000000000002",
            "estado": "APROBADO",
        },
        {
            **CASO,
            "id": "6f7a8b9c-0000-4000-8000-000000000003",
            "estado": "RECHAZADO",
        },
    ]
    with mock.patch("cliente_api.casos.listar", return_value=casos):
        html = cliente_con_sesion(permisos=RESIDENTE).get("/casos/").content.decode()

    assert 'am-pastilla--confirmado">Aprobado</span>' in html
    assert 'am-pastilla--error">Rechazado</span>' in html


def test_superusuario_ve_casos_de_todos_los_estados_incluido_redirigido():
    casos = [
        {**CASO, "id": "6f7a8b9c-0000-4000-8000-000000000002", "estado": "ABIERTO"},
        {**CASO, "id": "6f7a8b9c-0000-4000-8000-000000000003", "estado": "RECHAZADO"},
        {**CASO, "id": "6f7a8b9c-0000-4000-8000-000000000004", "estado": "REDIRIGIDO"},
    ]
    permisos = ["caso.crear", "caso.ver_todos", "caso.responder", "caso.gestionar"]
    with mock.patch("cliente_api.casos.listar", return_value=casos):
        html = cliente_con_sesion(permisos=permisos, tipo_usuario="Superusuario").get("/casos/").content.decode()

    assert "En revisión" in html
    assert "Rechazado" in html
    assert "Redirigido a Administración" in html
