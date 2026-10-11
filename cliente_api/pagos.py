"""Endpoints de `Admind_Backend/apps/pagos/`: el pago de la administración por vivienda y mes (HU-35)."""
from urllib.parse import urlencode

from cliente_api.http import pedir, pedir_archivo


def listar(request, periodo=None, buscar=""):
    """GET /pagos/administracion/[?periodo=AAAA-MM&buscar=] → {periodo, filas}, para quien tiene `pago.ver`.

    Cada fila: {unidad: {id, nombre}, personas: [{nombre, tipo}], estado, reportado_por, reportado_en,
    confirmado_por, confirmado_en, comprobante: {id, nombre, subido_en} | null}. `estado` es `sin_reporte`,
    `reportado` o `confirmado`. Sin periodo, el mes actual. El filtro lo aplica el servidor y ninguna fila
    trae el documento. 400 bajo `periodo` si está mal escrito.
    """
    consulta = {}
    if periodo:
        consulta["periodo"] = periodo
    if buscar:
        consulta["buscar"] = buscar
    ruta = "pagos/administracion/" + (f"?{urlencode(consulta)}" if consulta else "")
    return pedir(request, "GET", ruta)


def confirmar(request, unidad_id, periodo, confirmado):
    """POST /pagos/administracion/<unidad>/<AAAA-MM>/confirmacion/ {confirmado} → la fila. Solo con `pago.confirmar`.

    Poner o quitar el check es idempotente. 404 si la vivienda no es del conjunto activo.
    """
    return pedir(
        request, "POST", f"pagos/administracion/{unidad_id}/{periodo}/confirmacion/", {"confirmado": bool(confirmado)}
    )


def mios(request):
    """GET /pagos/administracion/mios/ → por cada vivienda propia, sus últimos 6 periodos, el más reciente primero.

    [{unidad: {id, nombre}, periodos: [{periodo: AAAA-MM, estado, reportado_por, reportado_en, confirmado_por,
    confirmado_en, comprobante}]}]. Con `pago.reportar`.
    """
    return pedir(request, "GET", "pagos/administracion/mios/")


def reportar(request, unidad_id, periodo, archivo):
    """POST /pagos/administracion/reportes/ (multipart: unidad, periodo, archivo) → el periodo reportado.

    400 bajo `archivo` (tipo o peso) o `periodo` (fuera de los últimos 12 meses y el siguiente); 404 si la
    vivienda no es de quien pide; 409 si el mes ya está confirmado.
    """
    contenido = (archivo.name, archivo.read(), archivo.content_type)
    return pedir(
        request,
        "POST",
        "pagos/administracion/reportes/",
        {"unidad": str(unidad_id), "periodo": periodo},
        archivos={"archivo": contenido},
    )


def comprobante(request, comprobante_id):
    """GET /pagos/administracion/comprobantes/<id>/ → (contenido, tipo). 404 si no existe o la persona no puede verlo."""
    return pedir_archivo(request, f"pagos/administracion/comprobantes/{comprobante_id}/")
