"""Endpoints de `Admind_Backend/apps/infracciones/`: el registro de infracciones del conjunto activo (HU-30).

El sistema no sanciona: aquí no hay función que imponga una sanción, una multa o una restricción de uso.
"""
from cliente_api.http import pedir


def listar(request):
    """GET /infracciones/ → los registros del conjunto: primero los abiertos, y luego el más reciente.

    Cada uno trae `id`, `unidad`, `vivienda`, `caso`, `descripcion_hecho`, `fecha_hecho`, `registrado_por`,
    `registrado_en`, `fecha_notificacion`, `abierto`, `cierre_fecha`, `cierre_comentario`, `cerrado_por`,
    `anulado`, `anulacion_motivo`, `anulado_por` y `anulado_en`. Los anulados siguen en la lista.
    """
    return pedir(request, "GET", "infracciones/")


def obtener(request, registro_id):
    """GET /infracciones/<id>/ → un registro, o 404 si no existe en el conjunto activo."""
    return pedir(request, "GET", f"infracciones/{registro_id}/")


def registrar(request, datos):
    """POST /infracciones/ {unidad, descripcion_hecho, fecha_hecho, caso?} → el registro, ya comunicado.

    400 bajo `unidad` si la vivienda no tiene propietario ni arrendatario vigentes: sin comunicación no hay registro.
    """
    return pedir(request, "POST", "infracciones/", datos)


def cerrar(request, registro_id, comentario):
    """POST /infracciones/<id>/cierre/ {comentario} → el registro cerrado. 409 si ya estaba cerrado o anulado."""
    return pedir(request, "POST", f"infracciones/{registro_id}/cierre/", {"comentario": comentario})


def anular(request, registro_id, motivo):
    """POST /infracciones/<id>/anulacion/ {motivo} → el registro anulado. Solo el Superusuario; 403 para el resto."""
    return pedir(request, "POST", f"infracciones/{registro_id}/anulacion/", {"motivo": motivo})
