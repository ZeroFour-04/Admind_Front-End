"""Endpoints de `Admind_Backend/apps/personas/`: buscar por documento y vincular al conjunto activo (HU-07).

Los dos son POST: el documento viaja en el cuerpo, nunca en la URL (maestro §5.2).
"""
from cliente_api.http import pedir


def buscar(request, datos):
    """POST /personas/buscar/ → {encontrada: false} o {encontrada: true, persona: {id, nombre, tiene_cuenta, roles_en_el_conjunto}}. 429 al pasar el límite."""
    return pedir(request, "POST", "personas/buscar/", datos)


def vincular(request, datos):
    """POST /personas/vincular/ → la persona con su rol nuevo en el conjunto activo. 409 si ya lo tiene."""
    return pedir(request, "POST", "personas/vincular/", datos)
