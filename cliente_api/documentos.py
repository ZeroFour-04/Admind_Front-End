"""Endpoints de `Admind_Backend/apps/documentos/`: el reglamento del conjunto activo (HU-33, lo mínimo)."""
from cliente_api.http import pedir, pedir_archivo


def reglamento(request):
    """GET /documentos/reglamento/ → {cargado: false} o {cargado: true, nombre, peso, subido_en, subido_por}."""
    return pedir(request, "GET", "documentos/reglamento/")


def subir_reglamento(request, archivo):
    """PUT /documentos/reglamento/ → los datos del reglamento nuevo, o 400. El anterior se conserva."""
    contenido = (archivo.name, archivo.read(), archivo.content_type)
    return pedir(request, "PUT", "documentos/reglamento/", archivos={"archivo": contenido})


def archivo_del_reglamento(request):
    """GET /documentos/reglamento/archivo/ → (contenido, tipo). 404 si el conjunto no tiene reglamento."""
    return pedir_archivo(request, "documentos/reglamento/archivo/")
