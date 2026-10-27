"""Cómo se muestra un caso: el nombre de cada estado y prioridad, y su pastilla. Siempre con texto.

Lo usan la lista del residente, el detalle y la pestaña Casos del dashboard, para que el mismo estado
se llame igual en las tres.
"""
from datetime import datetime

from django.utils import timezone
from django.utils.formats import date_format

ESTADOS_VISIBLES = {
    "ABIERTO": ("Por revisar", "am-pastilla--neutro"),
    "EN_REVISION": ("En revisión", "am-pastilla--tramite"),
    "REDIRIGIDO": ("Redirigido", "am-pastilla--info"),
    "CITADO": ("Citado", "am-pastilla--info"),
    "RESUELTO": ("Resuelto", "am-pastilla--confirmado"),
    "RECHAZADO": ("Rechazado", "am-pastilla--error"),
}
PRIORIDADES_VISIBLES = {
    "BAJA": ("Baja", "am-pastilla--neutro"),
    "NORMAL": ("Normal", "am-pastilla--neutro"),
    "ALTA": ("Alta", "am-pastilla--tramite"),
    "URGENTE": ("Urgente", "am-pastilla--error"),
}
ABIERTOS = ("ABIERTO", "EN_REVISION", "REDIRIGIDO", "CITADO")
# Mientras nadie lo redirige, el caso está en manos de la Secretaría.
EN_SECRETARIA = ("ABIERTO", "EN_REVISION")


def caso_para_mostrar(caso):
    """El caso de la API con sus fechas como fechas y con el texto y la pastilla de su estado y prioridad."""
    estado, estado_clase = ESTADOS_VISIBLES.get(caso["estado"], (caso["estado"], "am-pastilla--neutro"))
    prioridad, prioridad_clase = PRIORIDADES_VISIBLES.get(
        caso.get("prioridad"), (caso.get("prioridad", ""), "am-pastilla--neutro")
    )
    cerrado_en = caso.get("cerrado_en")
    creado_en = datetime.fromisoformat(caso["creado_en"])
    return {
        **caso,
        "creado_en": creado_en,
        "creado_el": date_format(timezone.localtime(creado_en), r"l j \d\e F \d\e Y").lower(),
        "cerrado_en": datetime.fromisoformat(cerrado_en) if cerrado_en else None,
        "estado_visible": estado,
        "estado_clase": estado_clase,
        "prioridad_visible": prioridad,
        "prioridad_clase": prioridad_clase,
        "abierto": caso["estado"] in ABIERTOS,
    }
