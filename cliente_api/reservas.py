"""Endpoints de `Admind_Backend/apps/reservas/`: franjas y solicitudes de reserva (HU-11)."""
from urllib.parse import urlencode

from cliente_api.http import pedir, pedir_archivo


def franjas(request, area_id, fecha):
    """GET /reservas/franjas/?area=&fecha= → {area, fecha, franjas: [{hora_inicio, hora_fin, estado}]}."""
    return pedir(request, "GET", f"reservas/franjas/?{urlencode({'area': area_id, 'fecha': fecha})}")


def tomar(request, datos):
    """POST /reservas/solicitudes/ → la solicitud EN_SOLICITUD con 3 minutos. 409 si la franja o la persona ya están ocupadas."""
    return pedir(request, "POST", "reservas/solicitudes/", datos)


def obtener(request, solicitud_id):
    """GET /reservas/solicitudes/<id>/ → una solicitud propia, con segundos_restantes y unidades_para_solicitar."""
    return pedir(request, "GET", f"reservas/solicitudes/{solicitud_id}/")


def liberar(request, solicitud_id):
    """POST /reservas/solicitudes/<id>/liberar/ → la solicitud LIBERADA. 409 si ya no estaba en trámite."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/liberar/")


def enviar(request, solicitud_id, datos):
    """POST /reservas/solicitudes/<id>/enviar/ → la solicitud APARTADA, o 400 con todos los `motivos` (la franja queda libre)."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/enviar/", datos)


def mis_solicitudes(request):
    """GET /reservas/solicitudes/ → las solicitudes propias, la más reciente primero."""
    return pedir(request, "GET", "reservas/solicitudes/")


def solicitudes_del_area(request, area_id):
    """GET /reservas/areas/<id>/solicitudes/ → solicitudes enviadas de una zona e historial de decisiones."""
    return pedir(request, "GET", f"reservas/areas/{area_id}/solicitudes/")


def solicitudes_para_bandeja(request, **filtros):
    """GET /reservas/bandeja/ → reservas enviadas, aceptadas o rechazadas del conjunto activo.

    Los `filtros` (`estado`, `area`, `vivienda`, `desde`, `hasta`, `solicitante`) reducen las filas sin
    cambiar el orden por antigüedad; la API los valida y responde 400 si no sirven.
    """
    parametros = {clave: valor for clave, valor in filtros.items() if valor}
    consulta = f"?{urlencode(parametros)}" if parametros else ""
    return pedir(request, "GET", f"reservas/bandeja/{consulta}")


def decidir(request, solicitud_id, datos):
    """POST /reservas/solicitudes/<id>/decision/ → Administración acepta o rechaza una solicitud apartada.

    Aceptar lleva `motivo`. Rechazar lleva `categoria`, y con la categoría `OTRO` también `motivo`.
    """
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/decision/", datos)


def descartar(request, solicitud_id, datos):
    """POST /reservas/solicitudes/<id>/descarte/ → Secretaría descarta con `causal` y `comentario`. 409 si ya se decidió."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/descarte/", datos)


def declarar_pago(request, solicitud_id, archivo=None):
    """POST /reservas/solicitudes/<id>/pago/ → la solicitud con `pago.declarado` y `pago.declarado_por`.

    El `archivo` es el comprobante, opcional. 400 bajo `archivo` si no es PDF, JPG ni PNG o pesa más de 5 MB;
    409 si la solicitud no está apartada ni reservada, si el pago ya estaba declarado o si ya hay 3 comprobantes.
    """
    archivos = {"archivo": (archivo.name, archivo.read(), archivo.content_type)} if archivo else None
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/pago/", archivos=archivos)


def retirar_pago(request, solicitud_id, motivo):
    """POST /reservas/solicitudes/<id>/pago/retirar/ → la solicitud con el pago sin declarar. 409 si no estaba declarado."""
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/pago/retirar/", {"motivo": motivo})


def subir_comprobante(request, solicitud_id, archivo):
    """POST /reservas/solicitudes/<id>/comprobantes/ → la solicitud propia con el comprobante en `pago`.

    Subirlo no declara el pago. 400 bajo `archivo` (tipo o peso); 409 si el pago ya está declarado, si la solicitud
    ya no admite comprobantes o si ya tiene 3; 404 si la solicitud no es de quien pide.
    """
    contenido = (archivo.name, archivo.read(), archivo.content_type)
    return pedir(request, "POST", f"reservas/solicitudes/{solicitud_id}/comprobantes/", archivos={"archivo": contenido})


def comprobante(request, comprobante_id):
    """GET /reservas/comprobantes/<id>/ → (contenido, tipo). 404 si no existe o la persona no puede verlo."""
    return pedir_archivo(request, f"reservas/comprobantes/{comprobante_id}/")
