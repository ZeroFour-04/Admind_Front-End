"""Endpoints de `Admind_Backend/apps/unidades/`: unidades del conjunto activo, sus vínculos (HU-08) y su estructura (HU-39)."""
from cliente_api.http import pedir


def listar(request):
    """GET /unidades/ → [{id, nombre, vinculos_vigentes}] de las viviendas del conjunto activo."""
    return pedir(request, "GET", "unidades/")


def crear(request, datos):
    """POST /unidades/ → la unidad creada. El nombre no se repite en el conjunto."""
    return pedir(request, "POST", "unidades/", datos)


def obtener(request, unidad_id):
    """GET /unidades/<id>/ → {id, nombre, vigentes, historicos}, o 404."""
    return pedir(request, "GET", f"unidades/{unidad_id}/")


def registrar_vinculo(request, unidad_id, datos):
    """POST /unidades/<id>/vinculos/ → el vínculo creado. 409 si ya hay uno vigente igual."""
    return pedir(request, "POST", f"unidades/{unidad_id}/vinculos/", datos)


def cerrar_vinculo(request, unidad_id, vinculo_id, datos):
    """POST /unidades/<id>/vinculos/<id>/cerrar/ → el detalle de la unidad. El vínculo pasa al histórico."""
    return pedir(request, "POST", f"unidades/{unidad_id}/vinculos/{vinculo_id}/cerrar/", datos)


def agrupaciones(request):
    """GET /unidades/agrupaciones/ → {agrupaciones: [{id, nombre_completo, tipo_vivienda, viviendas}], sin_agrupar, total}."""
    return pedir(request, "GET", "unidades/agrupaciones/")


def previsualizar_estructura(request, descripcion):
    """POST /unidades/estructura/previsualizar/ → lo que se crearía. No guarda nada."""
    return pedir(request, "POST", "unidades/estructura/previsualizar/", descripcion)


def generar_estructura(request, descripcion):
    """POST /unidades/estructura/ → crea las viviendas descritas. Las que ya existen se omiten."""
    return pedir(request, "POST", "unidades/estructura/", descripcion)
