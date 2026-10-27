"""Contraste de los ocho acentos del catálogo (HU-21, maestro §6.3).

Con un catálogo cerrado no hay colores que calcular al guardar: el conjunto guarda un slug y la
paleta de cada acento ya está en design-system/tokens/. Esta prueba lee esos archivos y
comprueba, por luminancia, que el texto que va sobre cada color se lee.
"""
import re

import pytest
from django.conf import settings

from apps.conjuntos.forms import ACENTOS

TOKENS = settings.BASE_DIR / "design-system" / "tokens"
CONTRASTE_MINIMO = 4.5  # WCAG AA para texto normal


def variables(css):
    return dict(re.findall(r"--([\w-]+)\s*:\s*([^;}]+)", css))


PALETA = variables((TOKENS / "paleta.css").read_text(encoding="utf-8"))
COLORES = (TOKENS / "colores.css").read_text(encoding="utf-8")


def resolver(valor):
    """Sigue los var(--x) hasta llegar al hex de la paleta."""
    valor = valor.strip()
    alias = re.fullmatch(r"var\(--([\w-]+)\)", valor)
    return resolver(PALETA[alias.group(1)]) if alias else valor


def acento(slug):
    bloque = re.search(r'\[data-acento="' + slug + r'"\]\{([^}]*)\}', COLORES)
    assert bloque, f"colores.css no tiene el bloque del acento {slug}"
    return {nombre: resolver(valor) for nombre, valor in variables(bloque.group(1)).items()}


def raiz(nombre):
    return resolver(variables(COLORES.split("}")[0])[nombre])


def luminancia(hex_):
    def lineal(canal):
        canal /= 255
        return canal / 12.92 if canal <= 0.04045 else ((canal + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * lineal(r) + 0.7152 * lineal(g) + 0.0722 * lineal(b)


def contraste(uno, otro):
    claro, oscuro = sorted((luminancia(uno), luminancia(otro)), reverse=True)
    return (claro + 0.05) / (oscuro + 0.05)


def texto_por_luminancia(fondo):
    """El texto que se lee mejor sobre el fondo: el blanco de la tinta o el más oscuro de la interfaz."""
    return max((raiz("acento-tinta"), raiz("texto-fuerte")), key=lambda texto: contraste(texto, fondo))


SLUGS = [slug for slug, _ in ACENTOS]


def test_el_catalogo_tiene_ocho_acentos_y_cada_uno_su_bloque_de_color():
    assert len(SLUGS) == 8
    for slug in SLUGS:
        assert set(acento(slug)) >= {"acento-50", "acento-600", "acento-700", "acento-900"}


@pytest.mark.parametrize("slug", SLUGS)
def test_el_texto_del_boton_se_lee_sobre_el_acento_y_su_hover(slug):
    colores = acento(slug)
    tinta = raiz("acento-tinta")

    assert contraste(tinta, colores["acento-600"]) >= CONTRASTE_MINIMO
    assert contraste(tinta, colores["acento-700"]) >= CONTRASTE_MINIMO


@pytest.mark.parametrize("slug", SLUGS)
def test_el_texto_de_la_navegacion_activa_se_lee_sobre_el_fondo_suave(slug):
    colores = acento(slug)

    assert contraste(colores["acento-900"], colores["acento-50"]) >= CONTRASTE_MINIMO


@pytest.mark.parametrize("slug", SLUGS)
def test_el_color_del_texto_sobre_el_acento_es_el_que_da_la_luminancia(slug):
    # La tinta es fija (blanca) para los ocho. Si un acento nuevo fuera muy claro, esta prueba
    # diría que ahí el texto tiene que ser oscuro.
    assert texto_por_luminancia(acento(slug)["acento-600"]) == raiz("acento-tinta")


def test_un_color_muy_claro_pediria_texto_oscuro():
    assert texto_por_luminancia("#FAF0DF") == raiz("texto-fuerte")


# Color propio (HU-21): su paleta se calcula, no está en los tokens


@pytest.mark.parametrize("color", ["#1a8fe3", "#7a3cc2", "#e34b1a", "#fff8c4", "#101010", "#00ff00"])
def test_la_rampa_de_un_color_propio_mantiene_legible_la_navegacion_activa(color):
    from apps.conjuntos.colores import rampa

    tonos = rampa(color)

    assert tonos["acento-600"] == color
    assert contraste(tonos["acento-900"].upper(), tonos["acento-50"].upper()) >= CONTRASTE_MINIMO


def test_un_color_propio_claro_se_marca_como_poco_legible_y_uno_oscuro_no():
    from apps.conjuntos.colores import poco_legible

    assert poco_legible("#fff8c4")
    assert poco_legible("#1a8fe3")  # un azul medio: 3.5:1
    assert not poco_legible("#0b4f8a")
    assert not poco_legible("no-es-un-color")


def test_un_color_que_no_es_hex_nunca_llega_al_style():
    from apps.conjuntos.templatetags.conjuntos import atributos_de_acento

    assert atributos_de_acento({"acento": "personalizado", "color": "red;background:url(x)"}) == ' data-acento="personalizado"'
    assert atributos_de_acento({"acento": "vino", "color": None}) == ' data-acento="vino"'
    assert atributos_de_acento(None) == ""


@pytest.mark.parametrize(
    ("nombre", "esperado"),
    [("Torres del Río", "TR"), ("Mirador", "M"), ("Conjunto de la Sabana", "CS"), ("", "?")],
)
def test_las_iniciales_saltan_las_palabras_de_union(nombre, esperado):
    from apps.conjuntos.templatetags.conjuntos import iniciales

    assert iniciales(nombre) == esperado
