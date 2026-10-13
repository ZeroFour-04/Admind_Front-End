"""Casos: el residente abre y consulta los suyos; gestión los atiende desde el detalle (HU-29)."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile

from cliente_api.http import ErrorDeApi
from tests.ayudantes import cliente_con_sesion

RESIDENTE = ["area.ver", "caso.crear"]
SECRETARIA = ["solicitud.bandeja_ver", "solicitud.priorizar", "caso.ver_todos", "caso.gestionar"]
ADMINISTRACION = ["solicitud.bandeja_ver", "solicitud.priorizar", "caso.ver_todos", "caso.responder"]
CASO = {
    "id": "6f7a8b9c-0000-4000-8000-000000000001",
    "titulo": "Fuga de agua",
    "cuerpo": "Hay una fuga en el pasillo.",
    "estado": "ABIERTO",
    "prioridad": "NORMAL",
    "respuesta": "",
    "motivo_rechazo": "",
    "causal_rechazo": "",
    "causal_rechazo_nombre": "",
    "autor": "Pedro Gómez",
    "apartamento": "Torre 1 - Apto 402",
    "creado_en": "2026-10-12T11:00:00-05:00",
    "cerrado_en": None,
    "foto_id": "7f7a8b9c-0000-4000-8000-000000000001",
}
PARA_GESTION = {**CASO, "justificacion_prioridad": "", "nota_redireccion": "", "cerrado_por": None}
URL = f"/casos/{CASO['id']}/"
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
    assert 'am-pastilla--neutro">Por revisar</span>' in html
    assert "Fecha: 12/10/2026 11:00" in html
    assert "Hay una fuga en el pasillo." in html
    assert "Residente: Pedro Gómez" not in html
    assert f'/casos/{CASO["id"]}/fotos/{CASO["foto_id"]}/' in html
    # El residente consulta; no hay ninguna operación suya sobre el caso.
    assert "<form" not in html.split('class="pila"')[1]


def test_residente_ve_cada_estado_con_su_nombre_y_la_respuesta_o_la_razon():
    casos = [
        {**CASO, "id": "6f7a8b9c-0000-4000-8000-000000000002", "estado": "EN_REVISION"},
        {**CASO, "id": "6f7a8b9c-0000-4000-8000-000000000003", "estado": "REDIRIGIDO"},
        {
            **CASO,
            "id": "6f7a8b9c-0000-4000-8000-000000000004",
            "estado": "RESUELTO",
            "respuesta": "El plomero va mañana a las 8.",
        },
        {
            **CASO,
            "id": "6f7a8b9c-0000-4000-8000-000000000005",
            "estado": "RECHAZADO",
            "motivo_rechazo": "Falta indicar la ubicación exacta.",
            "causal_rechazo_nombre": "Información insuficiente",
        },
    ]
    with mock.patch("cliente_api.casos.listar", return_value=casos):
        html = cliente_con_sesion(permisos=RESIDENTE).get("/casos/").content.decode()

    assert 'am-pastilla--tramite">En revisión</span>' in html
    assert 'am-pastilla--info">Redirigido</span>' in html
    assert 'am-pastilla--confirmado">Resuelto</span>' in html
    assert 'am-pastilla--error">Rechazado</span>' in html
    assert "Respuesta de la administración" in html and "El plomero va mañana a las 8." in html
    assert "<details" in html and "Razón del rechazo" in html
    assert "Información insuficiente. Falta indicar la ubicación exacta." in html


def test_gestion_entra_a_los_casos_por_el_dashboard():
    with mock.patch("cliente_api.casos.listar") as listar:
        de_secretaria = cliente_con_sesion(permisos=SECRETARIA, tipo_usuario="Secretaría").get("/casos/")
        de_superusuario = cliente_con_sesion(
            permisos=[*SECRETARIA, "caso.crear", "caso.responder"], tipo_usuario="Superusuario"
        ).get("/casos/")

    listar.assert_not_called()
    assert de_secretaria["Location"] == "/solicitudes/?pestana=casos"
    assert de_superusuario["Location"] == "/solicitudes/?pestana=casos"


def ver_detalle(caso, permisos, consulta=""):
    with mock.patch("cliente_api.casos.obtener", return_value=caso) as obtener:
        html = cliente_con_sesion(permisos=permisos).get(f"{URL}{consulta}").content.decode()
    assert str(obtener.call_args.args[1]) == CASO["id"]
    return html


def test_el_detalle_muestra_a_gestion_el_caso_con_residente_vivienda_y_nota_interna():
    caso = {**PARA_GESTION, "estado": "REDIRIGIDO", "nota_redireccion": "Ya van tres reportes de lo mismo."}

    html = ver_detalle(caso, ADMINISTRACION)

    assert "<h1>Fuga de agua</h1>" in html and "Maqueta con datos de ejemplo" not in html
    assert "Pedro Gómez" in html and "Torre 1 - Apto 402" in html
    assert "Lunes 12 de octubre de 2026, 11:00" in html
    assert f'/casos/{CASO["id"]}/fotos/{CASO["foto_id"]}/' in html
    assert 'am-pastilla--info">Redirigido</span>' in html and "Prioridad: Normal" in html
    assert "Nota de Secretaría" in html and "Ya van tres reportes de lo mismo." in html
    assert "el residente no la ve" in html
    assert 'href="/solicitudes/?pestana=casos">Volver a los casos</a>' in html


def test_secretaria_clasifica_y_no_ve_como_responder():
    html = ver_detalle(PARA_GESTION, SECRETARIA)

    for accion in ("tomar", "prioridad", "redirigir", "descartar"):
        assert f'action="/casos/{CASO["id"]}/{accion}/"' in html
    assert ">Redirigir al administrador</button>" in html and ">Descartar el caso</button>" in html
    assert '<option value="NO_ES_COMPETENCIA">No es competencia de la administración</option>' in html
    assert '<option value="URGENTE">Urgente</option>' in html
    assert "/responder/" not in html and "/rechazar/" not in html


def test_administracion_responde_un_caso_sin_que_nadie_lo_redirija():
    html = ver_detalle(PARA_GESTION, ADMINISTRACION)

    for accion in ("tomar", "prioridad", "responder", "rechazar"):
        assert f'action="/casos/{CASO["id"]}/{accion}/"' in html
    assert ">Responder y resolver</button>" in html and 'name="respuesta"' in html
    assert "/redirigir/" not in html and "/descartar/" not in html


def test_secretaria_no_tiene_nada_que_hacer_sobre_un_caso_ya_redirigido_salvo_priorizarlo():
    html = ver_detalle({**PARA_GESTION, "estado": "REDIRIGIDO"}, SECRETARIA)

    assert f'action="/casos/{CASO["id"]}/prioridad/"' in html
    for accion in ("tomar", "redirigir", "descartar", "responder", "rechazar"):
        assert f"/{accion}/" not in html


def test_un_caso_cerrado_no_ofrece_ninguna_accion():
    cerrado = {
        **PARA_GESTION,
        "estado": "RESUELTO",
        "respuesta": "El plomero va mañana a las 8.",
        "cerrado_por": "Ana Gómez",
        "cerrado_en": "2026-10-12T15:30:00-05:00",
    }

    html = ver_detalle(cerrado, [*SECRETARIA, "caso.responder"])

    assert "<form" not in html.split('class="caso-detalle"')[1]
    assert "Este caso ya está cerrado: no admite más cambios." in html
    assert "El plomero va mañana a las 8." in html
    assert "Ana Gómez · 12/10/2026 15:30" in html


def gestionar(accion, datos, permisos=SECRETARIA, **simulacion):
    with (
        mock.patch("cliente_api.casos.gestionar", **simulacion) as api,
        mock.patch("cliente_api.casos.obtener", return_value=PARA_GESTION),
    ):
        respuesta = cliente_con_sesion(permisos=permisos).post(f"{URL}{accion}/", datos)
    return respuesta, api


def test_cada_accion_manda_sus_campos_a_la_api_y_vuelve_al_detalle():
    casos = {
        "tomar": ({}, {}),
        "redirigir": ({"nota": " Revisar con el contratista. "}, {"nota": "Revisar con el contratista."}),
        "descartar": (
            {"causal": "DUPLICADO", "motivo": "Ya está reportado."},
            {"causal": "DUPLICADO", "motivo": "Ya está reportado."},
        ),
        "prioridad": (
            {"prioridad": "URGENTE", "justificacion": "Se inunda el sótano."},
            {"prioridad": "URGENTE", "justificacion": "Se inunda el sótano."},
        ),
        "responder": ({"respuesta": "El plomero va mañana."}, {"respuesta": "El plomero va mañana."}),
        "rechazar": ({"motivo": "No es de convivencia."}, {"motivo": "No es de convivencia."}),
    }
    for accion, (enviado, esperado) in casos.items():
        respuesta, api = gestionar(accion, enviado, return_value={})

        assert str(api.call_args.args[1]) == CASO["id"]
        assert api.call_args.args[2:] == (accion, esperado)
        assert respuesta["Location"] == f"{URL}?hecho={accion}"


def test_al_volver_el_detalle_dice_que_se_hizo():
    html = ver_detalle({**PARA_GESTION, "estado": "REDIRIGIDO"}, SECRETARIA, "?hecho=redirigir")

    assert 'role="status">El caso fue redirigido a Administración.</div>' in html


def test_si_la_api_rechaza_la_accion_se_dice_por_que_y_no_se_pierde_lo_escrito():
    sin_justificar = ErrorDeApi(400, {"justificacion": ["La prioridad urgente lleva una justificación escrita."]})
    ya_gestionado = ErrorDeApi(409, {"detail": "El caso ya fue gestionado."})

    urgente, _ = gestionar("prioridad", {"prioridad": "URGENTE", "justificacion": ""}, side_effect=sin_justificar)
    tarde, _ = gestionar(
        "responder", {"respuesta": "El plomero va mañana."}, permisos=ADMINISTRACION, side_effect=ya_gestionado
    )

    assert "La prioridad urgente lleva una justificación escrita." in urgente.content.decode()
    assert "El caso ya fue gestionado." in tarde.content.decode()
    assert ">El plomero va mañana.</textarea>" in tarde.content.decode()


def test_el_detalle_y_las_acciones_son_de_gestion_y_una_accion_inventada_no_existe():
    with mock.patch("cliente_api.casos.obtener") as obtener, mock.patch("cliente_api.casos.gestionar") as api:
        residente = cliente_con_sesion(permisos=RESIDENTE)
        detalle = residente.get(URL)
        accion = residente.post(f"{URL}responder/", {"respuesta": "Me respondo solo."})
        inventada = cliente_con_sesion(permisos=ADMINISTRACION).post(f"{URL}aprobar/")

    obtener.assert_not_called()
    api.assert_not_called()
    assert detalle["Location"] == "/casos/" and accion["Location"] == "/casos/"
    assert inventada.status_code == 404


def test_un_caso_de_otro_conjunto_no_existe():
    with mock.patch("cliente_api.casos.obtener", side_effect=ErrorDeApi(404, {"detail": "No encontrado."})):
        respuesta = cliente_con_sesion(permisos=ADMINISTRACION).get(URL)

    assert respuesta.status_code == 404


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
