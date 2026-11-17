from unittest import mock

from tests.ayudantes import cliente_con_sesion


def test_la_pantalla_reportes_y_el_menu_solo_salen_con_reporte_ver():
    admin = cliente_con_sesion(permisos=["reporte.ver"]).get("/reportes/")
    with mock.patch("cliente_api.areas.listar", return_value=[]):
        sin_permiso = cliente_con_sesion(permisos=["area.ver"]).get("/areas/")
    sin_acceso = cliente_con_sesion(permisos=["area.ver"]).get("/reportes/")
    lateral_admin = admin.content.decode().split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]
    lateral_sin_permiso = (
        sin_permiso.content.decode().split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]
    )

    assert admin.status_code == 200
    assert "Uso de zonas comunes" in admin.content.decode()
    assert "Estado de pagos del mes" in admin.content.decode()
    assert ">Reportes</a>" in lateral_admin
    assert ">Reportes</a>" not in lateral_sin_permiso
    assert sin_permiso.status_code == 200
    assert sin_acceso.status_code == 302


def test_descargar_pdf_manda_el_rango_y_devuelve_archivo():
    with mock.patch("cliente_api.reportes.zonas", return_value=(b"%PDF", "application/pdf")) as descargar:
        respuesta = cliente_con_sesion(permisos=["reporte.ver"]).get(
            "/reportes/zonas.pdf?desde=2026-11-01&hasta=2026-11-16"
        )

    descargar.assert_called_once()
    assert descargar.call_args.args[1:] == ("2026-11-01", "2026-11-16")
    assert respuesta.status_code == 200 and respuesta.content == b"%PDF"
    assert respuesta["Content-Type"] == "application/pdf"
    assert respuesta["Content-Disposition"] == (
        'attachment; filename="uso-zonas-comunes-2026-11-01-2026-11-16.pdf"'
    )


def test_descargar_excel_manda_el_periodo_y_rechaza_un_mes_invalido():
    with mock.patch(
        "cliente_api.reportes.pagos",
        return_value=(b"PK-xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ) as descargar:
        respuesta = cliente_con_sesion(permisos=["reporte.ver"]).get("/reportes/pagos.xlsx?periodo=2026-11")
        invalida = cliente_con_sesion(permisos=["reporte.ver"]).get("/reportes/pagos.xlsx?periodo=2026-13")

    descargar.assert_called_once()
    assert descargar.call_args.args[1:] == ("2026-11",)
    assert respuesta.status_code == 200 and respuesta.content == b"PK-xlsx"
    assert respuesta["Content-Disposition"] == 'attachment; filename="estado-pagos-2026-11.xlsx"'
    assert invalida.status_code == 200
    assert "Selecciona un mes válido." in invalida.content.decode()
