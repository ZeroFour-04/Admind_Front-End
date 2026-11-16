"""Endpoints de `Admind_Backend/apps/documentos/`: los documentos del conjunto activo, reglamento y manual de convivencia (HU-33)."""
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


# Los documentos por tipo (HU-33): las tres funciones de arriba son el caso `tipo="reglamento"`.


def vigentes(request):
    """GET /documentos/ → [{tipo, tipo_nombre, cargado, id, nombre, peso, subido_en, subido_por}], uno por tipo.

    Sin los datos del archivo si `cargado` es false. En el orden del catálogo: reglamento y manual.
    """
    return pedir(request, "GET", "documentos/")


def subir(request, tipo, archivo):
    """PUT /documentos/<tipo>/ → los datos de la versión nueva, o 400 bajo `archivo`. La anterior queda archivada."""
    contenido = (archivo.name, archivo.read(), archivo.content_type)
    return pedir(request, "PUT", f"documentos/{tipo}/", archivos={"archivo": contenido})


def archivo(request, tipo):
    """GET /documentos/<tipo>/archivo/ → (contenido, tipo MIME) del vigente. 404 si no hay. La API audita cada descarga."""
    return pedir_archivo(request, f"documentos/{tipo}/archivo/")


def versiones(request, tipo):
    """GET /documentos/<tipo>/versiones/ → [{id, nombre, peso, subido_en, subido_por, vigente}], la vigente primero. Pide `documento.descargar`."""
    return pedir(request, "GET", f"documentos/{tipo}/versiones/")


def archivo_de_version(request, tipo, version_id):
    """GET /documentos/<tipo>/versiones/<id>/archivo/ → (contenido, tipo MIME) de esa versión. Pide `documento.descargar`."""
    return pedir_archivo(request, f"documentos/{tipo}/versiones/{version_id}/archivo/")
