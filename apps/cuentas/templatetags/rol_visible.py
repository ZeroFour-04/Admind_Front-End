"""Cómo se nombra un rol en pantalla.

La API manda «Administrador» (la persona) y el resto de la app habla de «Administración» (el rol y el
área), así que en la barra y en el lateral se muestra siempre «Administración». Lo que viaja en la sesión
no cambia: los permisos y los menús siguen preguntando por «Administrador».
"""
import re

from django import template

register = template.Library()


@register.filter
def rol_visible(texto):
    return re.sub(r"\bAdministrador\b", "Administración", str(texto))
