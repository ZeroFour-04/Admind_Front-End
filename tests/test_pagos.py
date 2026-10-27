"""Pagos de la administración (HU-35): la tabla de gestión, «Mis pagos» y el comprobante. La API se simula."""
from unittest import mock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.pagos.views import mes_en_letras, mes_vecino
from cliente_api.http import ApiNoDisponible, ErrorDeApi
from tests.ayudantes import cliente_con_sesion

AVISO = "AdMind no verifica el dinero: el pago lo confirma una persona de la administración."
GESTION = ["pago.ver", "pago.confirmar"]
SECRETARIA = ["pago.ver"]
RESIDENTE = ["pago.reportar"]
U101 = "7a1b2c3d-0000-4000-8000-000000000101"
U102 = "7a1b2c3d-0000-4000-8000-000000000102"
COMPROBANTE = "9c0d1e2f-0000-4000-8000-000000000001"
CEDULA = "1023456789"
FILA_REPORTADA = {
    "unidad": {"id": U101, "nombre": "Torre 1 – 101"},
    # La API no manda documentos. Si uno llegara, la plantilla no lo imprime.
    "personas": [{"nombre": "Laura Gómez", "tipo": "propietario", "numero_documento": CEDULA}],
    "estado": "reportado",
    "reportado_por": "Laura Gómez",
    "reportado_en": "2026-10-05T10:00:00-05:00",
    "confirmado_por": None,
    "confirmado_en": None,
    "comprobante": {"id": COMPROBANTE, "nombre": "transferencia.pdf", "subido_en": "2026-10-05T10:00:00-05:00"},
}
FILA_SIN_REPORTE = {
    "unidad": {"id": U102, "nombre": "Torre 1 – 102"},
    "personas": [{"nombre": "Lucía Torres", "tipo": "arrendatario"}],
    "estado": "sin_reporte",
    "reportado_por": None,
    "reportado_en": None,
    "confirmado_por": None,
    "confirmado_en": None,
    "comprobante": None,
}
FILA_CONFIRMADA = {
    **FILA_REPORTADA,
    "estado": "confirmado",
    "confirmado_por": "Andrés Ruiz",
    "confirmado_en": "2026-10-06T09:30:00-05:00",
}


def pedir_tabla(filas, permisos=GESTION, url="/pagos/administracion/?periodo=2026-10", periodo="2026-10", **sesion):
    with mock.patch("cliente_api.pagos.listar", return_value={"periodo": periodo, "filas": list(filas)}) as listar:
        html = cliente_con_sesion(permisos=permisos, **sesion).get(url).content.decode()
    return html, listar


# Los meses


def test_los_enlaces_de_mes_cruzan_el_cambio_de_anio():
    assert mes_vecino("2026-01", -1) == "2025-12"
    assert mes_vecino("2026-12", 1) == "2027-01"
    assert mes_vecino("2026-10", 0) == "2026-10"
    assert mes_en_letras("2026-10") == "octubre de 2026"


# La tabla de gestión


def test_la_tabla_dice_que_el_dinero_lo_confirma_una_persona_y_muestra_el_mes_en_letras():
    html, _ = pedir_tabla([FILA_REPORTADA, FILA_SIN_REPORTE])

    assert AVISO in html and 'role="note"' in html
    assert "<h2>Octubre de 2026</h2>" in html
    assert ">Mes anterior</a>" in html and 'href="?periodo=2026-09"' in html
    assert ">Mes siguiente</a>" in html and 'href="?periodo=2026-11"' in html
    assert ">Reportado</span>" in html and ">Sin reporte</span>" in html
    assert "Torre 1 – 101" in html and "Laura Gómez" in html and "propietario" in html
    assert f'href="/pagos/administracion/comprobantes/{COMPROBANTE}/" target="_blank" rel="noopener">transferencia.pdf</a>' in html


def test_en_la_pagina_no_aparece_ninguna_cedula():
    html, _ = pedir_tabla([FILA_REPORTADA, FILA_SIN_REPORTE, FILA_CONFIRMADA])

    assert CEDULA not in html


def test_el_buscador_manda_buscar_y_periodo_a_la_api_y_conserva_lo_escrito():
    html, listar = pedir_tabla(
        [FILA_REPORTADA], url="/pagos/administracion/?periodo=2026-10&buscar=g%C3%B3mez"
    )

    assert listar.call_args.args[1:] == ("2026-10", "gómez")
    assert 'name="buscar" value="gómez"' in html
    assert 'name="periodo" value="2026-10"' in html
    assert ">Quitar búsqueda</a>" in html and 'href="?periodo=2026-10"' in html
    assert "Buscar por nombre, cédula o apartamento" in html


def test_sin_busqueda_no_hay_enlace_para_quitarla():
    html, listar = pedir_tabla([FILA_REPORTADA])

    assert listar.call_args.args[1:] == ("2026-10", "")
    assert "Quitar búsqueda" not in html


def test_si_ninguna_vivienda_coincide_la_tabla_lo_dice():
    html, _ = pedir_tabla([], url="/pagos/administracion/?periodo=2026-10&buscar=zzz")

    assert "Ninguna vivienda coincide con lo que buscaste" in html
    assert "<table" not in html


def test_administracion_ve_los_checks_con_la_vivienda_en_su_etiqueta_y_secretaria_no():
    de_administracion, _ = pedir_tabla([FILA_REPORTADA, FILA_CONFIRMADA])
    de_secretaria, _ = pedir_tabla([FILA_REPORTADA, FILA_CONFIRMADA], permisos=SECRETARIA, tipo_usuario="Secretaría")

    assert de_administracion.count('type="checkbox"') == 2
    assert "Pagado: Torre 1 – 101" in de_administracion
    assert f'action="/pagos/administracion/{U101}/2026-10/confirmar/"' in de_administracion
    assert 'checked' in de_administracion
    assert 'type="checkbox"' not in de_secretaria and "/confirmar/" not in de_secretaria
    # Secretaría ve el estado y quién confirmó, sin poder cambiarlo.
    assert ">Confirmado</span>" in de_secretaria and "Andrés Ruiz" in de_secretaria


def test_el_check_funciona_sin_javascript_y_con_alpine():
    de_administracion, _ = pedir_tabla([FILA_REPORTADA])
    de_secretaria, _ = pedir_tabla([FILA_REPORTADA], permisos=SECRETARIA)

    assert "<noscript>" in de_administracion and ">Guardar</button>" in de_administracion
    assert "x-data" in de_administracion and "js/vendor/alpine.min.js" in de_administracion
    assert "alpine" not in de_secretaria


def test_el_check_sin_marcar_envia_marcar_y_el_marcado_envia_quitar():
    html, _ = pedir_tabla([FILA_REPORTADA, FILA_CONFIRMADA])
    cuerpo = " ".join(html.split())

    assert cuerpo.count('name="confirmado" value="1"') == 1
    assert cuerpo.count('name="confirmado" value="0"') == 1


def test_marcar_manda_confirmado_y_vuelve_al_mismo_mes_y_a_la_misma_busqueda():
    with mock.patch("cliente_api.pagos.confirmar") as confirmar:
        respuesta = cliente_con_sesion(permisos=GESTION).post(
            f"/pagos/administracion/{U101}/2026-10/confirmar/", {"buscar": "gómez", "confirmado": "1"}
        )

    assert str(confirmar.call_args.args[1]) == U101
    assert confirmar.call_args.args[2:] == ("2026-10", True)
    assert respuesta["Location"] == "/pagos/administracion/?periodo=2026-10&buscar=g%C3%B3mez"


def test_quitar_el_check_manda_falso_y_sin_busqueda_vuelve_solo_al_mes():
    with mock.patch("cliente_api.pagos.confirmar") as confirmar:
        respuesta = cliente_con_sesion(permisos=GESTION).post(
            f"/pagos/administracion/{U101}/2026-09/confirmar/", {"confirmado": "0"}
        )

    assert confirmar.call_args.args[2:] == ("2026-09", False)
    assert respuesta["Location"] == "/pagos/administracion/?periodo=2026-09"


def test_un_error_al_marcar_se_muestra_arriba_de_la_tabla():
    prohibido = ErrorDeApi(403, {"detail": "No tienes permiso para hacer esto."})
    with (
        mock.patch("cliente_api.pagos.confirmar", side_effect=prohibido),
        mock.patch("cliente_api.pagos.listar", return_value={"periodo": "2026-10", "filas": [FILA_REPORTADA]}),
    ):
        html = cliente_con_sesion(permisos=SECRETARIA).post(
            f"/pagos/administracion/{U101}/2026-10/confirmar/", {"confirmado": "1"}
        ).content.decode()

    assert prohibido.mensaje in html
    assert html.index(prohibido.mensaje) < html.index("<table")


def test_un_periodo_mal_escrito_en_la_url_se_muestra_sin_romper_la_pantalla():
    malo = ErrorDeApi(400, {"periodo": ["El periodo va como AAAA-MM, por ejemplo 2026-10."]})
    with mock.patch("cliente_api.pagos.listar", side_effect=malo):
        respuesta = cliente_con_sesion(permisos=GESTION).get("/pagos/administracion/?periodo=octubre")

    assert respuesta.status_code == 200
    assert "El periodo va como AAAA-MM" in respuesta.content.decode()


def test_con_la_api_caida_la_tabla_dice_que_no_hay_conexion():
    with mock.patch("cliente_api.pagos.listar", side_effect=ApiNoDisponible()):
        html = cliente_con_sesion(permisos=GESTION).get("/pagos/administracion/").content.decode()

    assert "No hay conexión con el servidor de AdMind" in html


# «Mis pagos» del residente

MESES = ["2026-10", "2026-09", "2026-08", "2026-07", "2026-06", "2026-05"]


def mios(*, confirmado=None, viviendas=1):
    def periodo(texto):
        base = {
            "periodo": texto, "estado": "sin_reporte", "reportado_por": None, "reportado_en": None,
            "confirmado_por": None, "confirmado_en": None, "comprobante": None,
        }
        if texto == "2026-10":
            return {**base, "estado": "reportado", "reportado_por": "Laura Gómez",
                    "reportado_en": "2026-10-05T10:00:00-05:00",
                    "comprobante": {"id": COMPROBANTE, "nombre": "transferencia.pdf", "subido_en": "2026-10-05T10:00:00-05:00"}}
        if texto == "2026-09" and confirmado:
            return {**base, "estado": "confirmado", "confirmado_por": "Andrés Ruiz",
                    "confirmado_en": "2026-09-08T09:00:00-05:00"}
        return base

    unidades = [(U101, "Torre 1 – 101"), (U102, "Torre 1 – 102")][:viviendas]
    return [{"unidad": {"id": u, "nombre": n}, "periodos": [periodo(m) for m in MESES]} for u, n in unidades]


def ver_mis_pagos(datos, url="/pagos/administracion/", permisos=RESIDENTE):
    with mock.patch("cliente_api.pagos.mios", return_value=datos):
        return cliente_con_sesion(permisos=permisos, tipo_usuario="Residente").get(url).content.decode()


def test_el_residente_ve_sus_meses_y_el_aviso_y_no_la_tabla_de_gestion():
    with mock.patch("cliente_api.pagos.listar") as listar:
        html = ver_mis_pagos(mios(confirmado=True))

    listar.assert_not_called()
    assert AVISO in html and "Mis pagos de administración" in html
    assert "Torre 1 – 101" in html
    for mes in ("Octubre de 2026", "Septiembre de 2026", "Mayo de 2026"):
        assert mes in html
    assert ">Reportado</span>" in html and ">Confirmado</span>" in html and ">Sin reporte</span>" in html
    assert "Andrés Ruiz" in html and "transferencia.pdf" in html
    assert "Buscar por nombre, cédula o apartamento" not in html and 'type="checkbox"' not in html


def test_con_una_sola_vivienda_el_campo_vivienda_no_se_muestra_y_con_dos_si():
    una = ver_mis_pagos(mios())
    dos = ver_mis_pagos(mios(viviendas=2))

    assert f'type="hidden" name="unidad" value="{U101}"' in una
    assert 'for="id_unidad"' not in una
    assert 'for="id_unidad"' in dos and "Torre 1 – 102" in dos


def test_el_formulario_ofrece_los_meses_que_la_api_le_muestra_y_dice_que_subir_no_confirma():
    html = ver_mis_pagos(mios())

    for mes in MESES:
        assert f'<option value="{mes}"' in html
    assert 'enctype="multipart/form-data"' in html
    assert 'accept=".pdf,image/png,image/jpeg"' in html
    assert "Subir el comprobante no confirma el pago: lo confirma la administración cuando lo verifique." in html
    assert ">Subir comprobante</button>" in html


def test_reportar_manda_la_vivienda_el_periodo_y_el_archivo_a_la_api():
    recibido = {}

    def como_la_api(request, unidad_id, periodo, archivo):
        # El archivo se cierra al terminar la petición: se lee mientras la API «lo recibe».
        recibido.update(unidad=str(unidad_id), periodo=periodo, nombre=archivo.name, contenido=archivo.read())

    foto = SimpleUploadedFile("transferencia.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    with (
        mock.patch("cliente_api.pagos.mios", return_value=mios()),
        mock.patch("cliente_api.pagos.reportar", side_effect=como_la_api),
    ):
        respuesta = cliente_con_sesion(permisos=RESIDENTE, tipo_usuario="Residente").post(
            "/pagos/administracion/", {"unidad": U101, "periodo": "2026-10", "archivo": foto}
        )

    assert recibido == {"unidad": U101, "periodo": "2026-10", "nombre": "transferencia.png", "contenido": b"\x89PNG\r\n\x1a\n"}
    assert respuesta["Location"] == "/pagos/administracion/?reportado=1"


def test_al_volver_dice_que_el_comprobante_quedo_reportado():
    html = ver_mis_pagos(mios(), url="/pagos/administracion/?reportado=1")

    assert "Tu comprobante quedó reportado." in html


def test_un_400_de_la_api_sobre_el_archivo_cae_en_su_campo():
    rechazo = ErrorDeApi(400, {"archivo": ["El comprobante debe ser un PDF o una imagen JPG o PNG."]})
    texto = SimpleUploadedFile("virus.pdf", b"esto no es un pdf", content_type="application/pdf")
    with (
        mock.patch("cliente_api.pagos.mios", return_value=mios()),
        mock.patch("cliente_api.pagos.reportar", side_effect=rechazo),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE, tipo_usuario="Residente").post(
            "/pagos/administracion/", {"unidad": U101, "periodo": "2026-10", "archivo": texto}
        ).content.decode()

    assert "El comprobante debe ser un PDF o una imagen JPG o PNG." in html
    # Cae en el campo del archivo: después de su etiqueta y antes del botón.
    assert html.index("Comprobante de pago") < html.index("El comprobante debe ser un PDF") < html.index(
        ">Subir comprobante</button>"
    )


def test_el_409_de_mes_confirmado_va_arriba_del_formulario():
    ya = ErrorDeApi(409, {"detail": "Ese mes ya está confirmado por la administración."})
    foto = SimpleUploadedFile("p.pdf", b"%PDF-1.7", content_type="application/pdf")
    with (
        mock.patch("cliente_api.pagos.mios", return_value=mios()),
        mock.patch("cliente_api.pagos.reportar", side_effect=ya),
    ):
        html = cliente_con_sesion(permisos=RESIDENTE, tipo_usuario="Residente").post(
            "/pagos/administracion/", {"unidad": U101, "periodo": "2026-10", "archivo": foto}
        ).content.decode()

    assert "Ese mes ya está confirmado por la administración." in html
    assert html.index("Ese mes ya está confirmado") < html.index("Reportar un pago</h2>") + 200


def test_sin_archivo_no_se_llama_a_la_api():
    with (
        mock.patch("cliente_api.pagos.mios", return_value=mios()),
        mock.patch("cliente_api.pagos.reportar") as reportar,
    ):
        html = cliente_con_sesion(permisos=RESIDENTE, tipo_usuario="Residente").post(
            "/pagos/administracion/", {"unidad": U101, "periodo": "2026-10"}
        ).content.decode()

    reportar.assert_not_called()
    assert "Subir comprobante" in html


def test_sin_vivienda_registrada_hay_un_estado_vacio_y_ningun_formulario():
    html = ver_mis_pagos([])

    assert "No tienes una vivienda registrada" in html
    assert "Habla con la administración" in html
    assert 'type="file"' not in html


# El comprobante y el menú


def test_la_vista_del_comprobante_devuelve_el_archivo_con_su_tipo_y_un_404_de_la_api_es_un_404():
    with mock.patch("cliente_api.pagos.comprobante", return_value=(b"%PDF-1.7", "application/pdf")):
        respuesta = cliente_con_sesion(permisos=RESIDENTE).get(f"/pagos/administracion/comprobantes/{COMPROBANTE}/")
    with mock.patch("cliente_api.pagos.comprobante", side_effect=ErrorDeApi(404, {"detail": "No encontrado."})):
        no_es_suyo = cliente_con_sesion(permisos=RESIDENTE).get(f"/pagos/administracion/comprobantes/{COMPROBANTE}/")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta["Content-Disposition"] == 'inline; filename="comprobante.pdf"'
    assert respuesta["X-Content-Type-Options"] == "nosniff"
    assert respuesta.content == b"%PDF-1.7"
    assert no_es_suyo.status_code == 404


def test_un_tipo_que_no_es_comprobante_se_responde_404():
    with mock.patch("cliente_api.pagos.comprobante", return_value=(b"<html></html>", "text/html")):
        respuesta = cliente_con_sesion(permisos=GESTION).get(f"/pagos/administracion/comprobantes/{COMPROBANTE}/")

    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    ("permisos", "tipo", "ve_pagos"),
    [
        (GESTION, "Administrador", True),
        (SECRETARIA, "Secretaría", True),
        (RESIDENTE, "Residente", True),
        (["visitante.registrar"], "Vigilancia", False),
        (["area.ver"], "Residente", False),
    ],
)
def test_el_item_pagos_del_lateral_sale_segun_el_permiso(permisos, tipo, ve_pagos):
    html = cliente_con_sesion(permisos=permisos, tipo_usuario=tipo).get("/inicio/").content.decode()
    lateral = html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    assert (">Pagos</a>" in lateral) is ve_pagos


def test_quien_no_tiene_permisos_de_pagos_vuelve_al_inicio():
    respuesta = cliente_con_sesion(permisos=["visitante.registrar"], tipo_usuario="Vigilancia").get(
        "/pagos/administracion/"
    )

    assert respuesta.status_code == 302 and respuesta["Location"] == "/inicio/"
