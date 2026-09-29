"""Etiquetas para pintar la identidad del conjunto (HU-21 y HU-26): su color y su marcador sin foto."""
from django import template
from django.utils.html import format_html

from apps.conjuntos import colores
from apps.conjuntos.forms import COLOR_PROPIO_INICIAL

register = template.Library()

# Palabras que no cuentan para las iniciales: "Torres del Río" es TR, no TDR.
PALABRAS_DE_UNION = {"de", "del", "la", "las", "el", "los", "y"}


@register.simple_tag
def atributos_de_acento(conjunto):
    """data-acento del conjunto y, si su color es propio, las variables --acento-* en línea.

    Los ocho del catálogo se pintan con los bloques [data-acento] de colores.css. El propio no
    tiene bloque: sus tonos van en el style del mismo elemento y ganan sobre los de :root.
    """
    acento = (conjunto or {}).get("acento")
    if not acento:
        return ""
    color = conjunto.get("color")
    if acento == "personalizado" and colores.es_hex(color):
        estilo = ";".join(f"--{nombre}:{valor}" for nombre, valor in colores.rampa(color).items())
        return format_html(' data-acento="{}" style="{}"', acento, estilo)
    return format_html(' data-acento="{}"', acento)


@register.filter
def iniciales(nombre):
    """Hasta dos iniciales del nombre, para el marcador del conjunto sin foto."""
    palabras = [palabra for palabra in (nombre or "").split() if palabra.lower() not in PALABRAS_DE_UNION]
    return "".join(palabra[0] for palabra in palabras[:2]).upper() or "?"


@register.filter
def color_seguro(color):
    """El color si es un hex válido; si no, el de partida. Así un valor raro nunca llega a un style."""
    return color if colores.es_hex(color) else COLOR_PROPIO_INICIAL


@register.filter
def poco_legible(color):
    return colores.poco_legible(color)


@register.filter
def contraste_con_blanco(color):
    return f"{colores.contraste_con_blanco(color):.1f}" if colores.es_hex(color) else ""
