"""La capa «con vida» (2026-10-30): íconos del lateral, fondo elegible y reglas de estilo que no se rompen. La API se simula."""
import re
from unittest import mock

from django.conf import settings

from tests.ayudantes import TORRES, cliente_con_sesion

CSS = settings.BASE_DIR / "static" / "css"
TOKENS = settings.BASE_DIR / "design-system" / "tokens"
PERMISOS_DEL_MENU = [
    "area.gestionar", "documento.ver", "caso.crear", "infraccion.ver", "ingreso.registrar",
    "pago.ver", "visitante.registrar", "conjunto.editar", "parqueadero.ver",
]


def hojas_nuevas():
    """Las hojas de la capa «con vida» que ya existen: conjuntos.css y reservas.css llegan en planes posteriores."""
    hojas = [CSS / "apariencia.css", CSS / "conjuntos.css", TOKENS / "efectos.css"]
    return [hoja for hoja in hojas if hoja.exists()]


def sin_comentarios(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def reglas(css):
    """(selector, cuerpo) de cada regla de primer nivel, sin comentarios."""
    return re.findall(r"([^{}]+)\{([^{}]*)\}", sin_comentarios(css))


def test_toda_pagina_con_estructura_trae_los_iconos_y_el_script_del_fondo_en_el_head():
    html = cliente_con_sesion().get("/inicio/").content.decode()

    assert 'id="i-inicio"' in html and 'id="i-paleta"' in html
    assert "css/apariencia.css" in html
    assert '<script src="/static/js/apariencia.js"></script>' in html
    assert html.index("js/apariencia.js") < html.index("<body")


def test_el_lateral_pone_un_icono_delante_del_texto_de_cada_enlace_menos_cambiar_de_conjunto():
    html = cliente_con_sesion(permisos=PERMISOS_DEL_MENU).get("/inicio/").content.decode()
    lateral = html.split('<nav class="am-lateral"', 1)[1].split("</nav>", 1)[0]

    enlaces = lateral.count('<a class="am-lateral__item')
    assert enlaces >= 10
    assert lateral.count('<svg class="am-icono"') == enlaces - 1
    assert 'href="/conjuntos/">Cambiar de conjunto</a>' in lateral
    assert re.search(r'aria-current="page"><svg class="am-icono"[^>]*><use href="#i-inicio"></use></svg>Inicio</a>', lateral)


def test_cada_icono_que_usa_el_lateral_existe_en_el_conjunto_de_iconos():
    html = cliente_con_sesion(permisos=PERMISOS_DEL_MENU).get("/inicio/").content.decode()

    usados = set(re.findall(r'<use href="#(i-[\w-]+)"', html))
    definidos = set(re.findall(r'<symbol id="(i-[\w-]+)"', html))
    assert usados and usados <= definidos


def test_la_barra_deja_elegir_el_fondo_con_la_aplicacion_y_en_el_selector_de_conjuntos():
    aplicacion = cliente_con_sesion().get("/inicio/").content.decode()
    with mock.patch("cliente_api.cuentas.listar_conjuntos", return_value=[{**TORRES, "direccion": ""}]):
        selector = cliente_con_sesion().get("/conjuntos/").content.decode()

    for html in (aplicacion, selector):
        assert html.count("data-apariencia") == 1
        for fondo in ("liso", "color", "cristal"):
            assert f'name="fondo" value="{fondo}"' in html


def test_el_fondo_predeterminado_y_los_valores_validos_estan_en_el_script():
    js = (settings.BASE_DIR / "static" / "js" / "apariencia.js").read_text(encoding="utf-8")

    assert 'var FONDOS = ["liso", "color", "cristal"];' in js
    assert 'var PREDETERMINADO = "cristal";' in js


def test_las_hojas_nuevas_no_escriben_colores_en_hex():
    assert len(hojas_nuevas()) >= 2
    for ruta in hojas_nuevas():
        assert not re.findall(r"#[0-9a-fA-F]{3,8}\b", sin_comentarios(ruta.read_text(encoding="utf-8"))), ruta.name


def test_el_acento_no_entra_en_ninguna_regla_de_estado():
    estados = ("am-pastilla--", "aviso-error", "aviso-exito", "aviso-info", "am-alerta", "aviso-legibilidad")
    for ruta in hojas_nuevas():
        for selector, cuerpo in reglas(ruta.read_text(encoding="utf-8")):
            if any(estado in selector for estado in estados):
                assert "--acento" not in cuerpo, f"{ruta.name}: {selector.strip()}"


def test_los_tonos_derivados_se_recalculan_en_cada_elemento_con_acento():
    efectos = sin_comentarios((TOKENS / "efectos.css").read_text(encoding="utf-8"))

    assert ":root,[data-acento]{" in efectos
    for derivado in ("--acento-100", "--acento-200", "--acento-400", "--acento-vecino", "--sombra-suave"):
        assert derivado in efectos
    assert '@import url("tokens/efectos.css");' in (settings.BASE_DIR / "design-system" / "styles.css").read_text(encoding="utf-8")
