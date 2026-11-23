"""Lleva al <input> de componentes/campo.html las reglas de formato que lee static/js/validacion.js."""
from django import template
from django.utils.html import format_html_join

register = template.Library()


@register.simple_tag
def atributos_de_validacion(campo):
    """` data-solo="…"` y `minlength="…"` del campo, si los tiene. El maxlength ya lo pone la plantilla."""
    atributos = []
    solo = campo.field.widget.attrs.get("data-solo")
    if solo:
        atributos.append(("data-solo", solo))
    minimo = getattr(campo.field, "min_length", None)
    if minimo:
        atributos.append(("minlength", minimo))
    return format_html_join("", ' {}="{}"', atributos)
