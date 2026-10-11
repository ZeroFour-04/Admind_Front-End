"""Zonas comunes (HU-11): el calendario con las franjas de un área, tomar el bloqueo y la solicitud en trámite.

Si una franja está libre o si un bloqueo venció lo decide la API; aquí solo se muestra.
"""
import calendar
import uuid
from datetime import date, datetime, time
from urllib.parse import urlencode

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format, time_format
from django.views.decorators.http import require_GET, require_POST

from apps.areas.views import cargar_areas
from apps.cuentas.sesion import tiene_permiso
from cliente_api import ingresos as api_ingresos
from cliente_api import reservas as api_reservas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import SolicitudForm

# Cómo se ve cada estado de franja: siempre con texto, nunca solo con color.
PASTILLA_POR_ESTADO = {
    "libre": ("Libre", "am-pastilla--confirmado"),
    "en_solicitud": ("En trámite", "am-pastilla--tramite"),
    "apartada": ("Apartada", "am-pastilla--error"),
    "reservada": ("Reservada", "am-pastilla--error"),
    "pasada": ("Ya pasó", "am-pastilla--neutro"),
    "propia": ("Tuya", "am-pastilla--info"),
    "no_disponible": ("No disponible", "am-pastilla--neutro"),
}
# Lo que el panel de confirmación resalta sin impedir el envío (HU-12). «Alta demanda» llega con PB-24.
TEXTO_POR_AVISO = {
    "menos_de_24h": "Empieza en menos de 24 horas.",
    "limite_de_anticipacion": "Es el último día que se puede reservar con la anticipación permitida.",
    "otra_solicitud": "Ya tienes otra solicitud apartada o reservada.",
}
# El aviso del pago (HU-16): se escribe aquí, una sola vez, y las dos pantallas lo reciben por contexto.
AVISO_DEL_DINERO = "AdMind no verifica el dinero: el pago lo declara una persona de la administración."
# Lo decide la API (409 al cuarto). Aquí solo evita ofrecer un formulario que ya no va a funcionar.
MAXIMO_DE_COMPROBANTES = 3
EXTENSION_DE_COMPROBANTE = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}
TEXTO_DEL_AVISO_DE_PAGO = {
    "declarado": "El pago quedó declarado.",
    "retirado": "La declaración del pago quedó retirada.",
}


def _mes_pedido(texto, hoy):
    """`?mes=2026-09` → 1 de septiembre de 2026. Si falta o no se entiende, el mes actual."""
    try:
        anio, mes = (int(parte) for parte in texto.split("-"))
        if not 2000 <= anio <= 2100:
            raise ValueError
        return date(anio, mes, 1)
    except (AttributeError, ValueError):
        return hoy.replace(day=1)


def _dia_pedido(texto, mes):
    """`?dia=2026-09-26`, solo si cae dentro del mes que se está viendo."""
    try:
        dia = date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None
    return dia if (dia.year, dia.month) == (mes.year, mes.month) else None


def _mes_vecino(mes, paso):
    indice = mes.year * 12 + (mes.month - 1) + paso
    return date(indice // 12, indice % 12 + 1, 1)


def url_del_calendario(area_id, dia):
    """Vuelve al calendario con el área y el día a la vista. Ninguno de los dos es un dato personal."""
    consulta = {"area": area_id, "mes": dia.strftime("%Y-%m"), "dia": dia.isoformat()}
    return f"{reverse('reservas:calendario')}?{urlencode(consulta)}"


def cargar_franjas(request, area_id, dia):
    try:
        respuesta = api_reservas.franjas(request, area_id, dia.isoformat())
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje
    franjas = []
    for franja in respuesta["franjas"]:
        texto, clase = PASTILLA_POR_ESTADO[franja["estado"]]
        franjas.append({**franja, "texto": texto, "clase": clase})
    return franjas, None


def cargar_cupos(request):
    """Los cupos de las zonas con ingreso por id de área, o el aviso si no se pudieron consultar.

    Es un dato de más: si la API de ingresos no responde, la tabla sale sin cupos y reservar sigue funcionando.
    """
    try:
        return {zona["area"]["id"]: zona for zona in api_ingresos.zonas(request)}, None
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje


def fila_de_zona(area, cupos):
    """Una zona para la tabla: cómo se usa, cuánto cabe y su estado en una pastilla con texto (plan P18)."""
    fila = {"area": area, "con_ingreso": area["modo_uso"] == "ingreso", "detalle": ""}
    zona = (cupos or {}).get(area["id"])
    if area["en_mantenimiento"]:
        fila["texto"], fila["clase"] = "En mantenimiento", "am-pastilla--tramite"
    elif not fila["con_ingreso"]:
        fila["texto"], fila["clase"] = "Disponible", "am-pastilla--confirmado"
    elif zona is None:
        fila["texto"], fila["clase"] = "Sin información", "am-pastilla--neutro"
    elif not zona["abierta_ahora"]:
        fila["texto"], fila["clase"], fila["detalle"] = "Cerrada", "am-pastilla--neutro", zona["motivo_cierre"]
    elif zona["cupos"] == 0:
        fila["texto"], fila["clase"] = "Sin cupo", "am-pastilla--error"
    else:
        fila["texto"], fila["clase"] = "Abierta", "am-pastilla--confirmado"
    if zona is not None:
        fila["cupos"] = zona["cupos"]
    return fila


def pantalla_del_calendario(request, error=None, solicitud_en_curso=None):
    """El calendario del mes, se arma en el servidor: cambiar de mes, de día o de área es un enlace."""
    hoy = timezone.localdate()
    mes = _mes_pedido(request.GET.get("mes"), hoy)
    dia = _dia_pedido(request.GET.get("dia"), mes)
    if dia and dia < hoy:
        dia = None
    todas, error_de_areas = cargar_areas(request)
    todas = [area for area in todas if area["activo"]]
    # Solo lo que se reserva va al calendario; lo que tiene ingreso se registra en portería.
    areas = [area for area in todas if area["modo_uso"] == "reserva"]
    area = next((area for area in areas if area["id"] == request.GET.get("area")), None)
    cupos, aviso_de_cupos = cargar_cupos(request) if any(a["modo_uso"] == "ingreso" for a in todas) else ({}, None)
    franjas, error_de_franjas = cargar_franjas(request, area["id"], dia) if area and dia else ([], None)
    return render(request, "reservas/calendario.html", {
        "hoy": hoy,
        "mes": mes,
        "semanas": calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(mes.year, mes.month),
        "dia_elegido": dia,
        "mes_anterior": _mes_vecino(mes, -1),
        "mes_siguiente": _mes_vecino(mes, 1),
        "areas": areas,
        "zonas": [fila_de_zona(zona, cupos) for zona in todas],
        "aviso_de_cupos": aviso_de_cupos,
        "area": area,
        "franjas": franjas,
        "error": error or error_de_areas or error_de_franjas,
        "solicitud_en_curso": solicitud_en_curso,
        "puede_solicitar": tiene_permiso(request, "reserva.solicitar"),
    })


def calendario(request):
    return pantalla_del_calendario(request)


def cargar_solicitudes_area(request, area_id):
    try:
        return api_reservas.solicitudes_del_area(request, area_id), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def fechas_del_pago(solicitud):
    """El `pago` de una solicitud como lo pinta la plantilla: con fechas de verdad.

    Si la API no lo trae, el pago se muestra sin declarar y sin comprobantes.
    """
    pago = solicitud.get("pago") or {"declarado": False, "declarado_en": None, "comprobantes": []}
    declarado_en = pago.get("declarado_en")
    return {
        **pago,
        "declarado_en": datetime.fromisoformat(declarado_en) if declarado_en else None,
        "comprobantes": [
            {**comprobante, "subido_en": datetime.fromisoformat(comprobante["subido_en"])}
            for comprobante in pago.get("comprobantes", [])
        ],
    }


def frase_del_pago(solicitud):
    """«la reserva de Laura Gómez (Torre 1 – 101) en Salón comunal, el sábado 17 de octubre de 2026, de 8:00 a. m. a 12:00 p. m.»

    Quien declara confirma el contenido y no la intención (HU-12): de quién, qué área, qué día en letras y
    qué horario. La frase termina en punto porque la hora termina en «a. m.» o «p. m.».
    """
    datos = con_fechas(solicitud)
    unidad = f" ({datos['unidad']['nombre']})" if datos.get("unidad") else ""
    dia = date_format(datos["fecha"], r"l j \d\e F \d\e Y").lower()
    horario = f"de {hora_en_letras(datos['hora_inicio'])} a {hora_en_letras(datos['hora_fin'])}"
    return f"la reserva de {datos['residente']['nombre']}{unidad} en {datos['area']['nombre']}, el {dia}, {horario}"


def para_gestion(solicitud, puede_declarar_pago):
    """La solicitud con lo que su tarjeta necesita del pago. Qué se ofrece lo decide el permiso y la API manda el estado."""
    pago = fechas_del_pago(solicitud)
    ofrece_declarar = (
        puede_declarar_pago and solicitud["estado"] in ("APARTADA", "RESERVADA") and not pago["declarado"]
    )
    return {
        **solicitud,
        "pago": pago,
        "puede_declarar": ofrece_declarar,
        "puede_retirar": puede_declarar_pago and pago["declarado"],
        "frase_del_pago": frase_del_pago(solicitud) if ofrece_declarar else "",
    }


def pantalla_solicitudes_area(request, area_id, error=None):
    solicitudes, error_de_solicitudes = cargar_solicitudes_area(request, area_id)
    areas, error_de_areas = cargar_areas(request)
    area = next((area for area in areas if area["id"] == str(area_id)), None)
    if area is None and not error_de_areas:
        error_de_areas = "No se encontró esta zona común."
    puede_declarar_pago = tiene_permiso(request, "reserva.declarar_pago")
    return render(request, "reservas/solicitudes_area.html", {
        "area": area,
        "solicitudes": [para_gestion(solicitud, puede_declarar_pago) for solicitud in solicitudes],
        "error": error or error_de_areas or error_de_solicitudes,
        "actualizada": request.GET.get("actualizada") == "1",
        "aviso_de_pago": TEXTO_DEL_AVISO_DE_PAGO.get(request.GET.get("pago")),
        "aviso_del_dinero": AVISO_DEL_DINERO,
        "error_de_solicitudes": error_de_solicitudes,
    })


def solicitudes_area(request, area_id):
    return pantalla_solicitudes_area(request, area_id)


@require_POST
def decidir(request, solicitud_id):
    decision = request.POST.get("decision")
    motivo = request.POST.get("motivo", "").strip()
    area_id = request.POST.get("area")
    if decision not in ("RESERVADA", "RECHAZADA") or not motivo:
        return pantalla_solicitudes_area(
            request, area_id, "Selecciona aceptar o rechazar y escribe el motivo de la decisión."
        )
    try:
        api_reservas.decidir(request, solicitud_id, {"decision": decision, "motivo": motivo})
    except ApiNoDisponible:
        return pantalla_solicitudes_area(request, area_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla_solicitudes_area(request, area_id, error.mensaje)
    return redirect(f"{reverse('reservas:solicitudes-area', kwargs={'area_id': area_id})}?actualizada=1")


def area_del_formulario(request):
    """El área a la que vuelve la pantalla: viene en el formulario. Sin un identificador válido no hay a dónde volver."""
    try:
        return uuid.UUID(request.POST.get("area", ""))
    except ValueError:
        raise Http404


def mensaje_del_error(error):
    """Los errores por campo de la API (400) en una frase; si no los trae, el mensaje general."""
    mensajes = [mensaje for lista in error.campos.values() for mensaje in lista]
    return " ".join(mensajes) or error.mensaje


@require_POST
def declarar_pago(request, solicitud_id):
    """«Declarar pago recibido». El archivo, si lo hay, pasa de largo hacia la API: este servidor no lo guarda."""
    area_id = area_del_formulario(request)
    try:
        api_reservas.declarar_pago(request, solicitud_id, request.FILES.get("archivo"))
    except ApiNoDisponible:
        return pantalla_solicitudes_area(request, area_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla_solicitudes_area(request, area_id, mensaje_del_error(error))
    return redirect(f"{reverse('reservas:solicitudes-area', kwargs={'area_id': area_id})}?pago=declarado")


@require_POST
def retirar_pago(request, solicitud_id):
    """«Retirar la declaración»: una declaración hecha por error se corrige con motivo, y queda en la auditoría."""
    area_id = area_del_formulario(request)
    motivo = request.POST.get("motivo", "").strip()
    if not motivo:
        return pantalla_solicitudes_area(request, area_id, "Escribe el motivo para retirar la declaración del pago.")
    try:
        api_reservas.retirar_pago(request, solicitud_id, motivo)
    except ApiNoDisponible:
        return pantalla_solicitudes_area(request, area_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla_solicitudes_area(request, area_id, mensaje_del_error(error))
    return redirect(f"{reverse('reservas:solicitudes-area', kwargs={'area_id': area_id})}?pago=retirado")


@require_GET
def comprobante(request, comprobante_id):
    """El archivo de un comprobante. Lo pide este servidor con el token: el navegador nunca habla con la API."""
    try:
        contenido, tipo = api_reservas.comprobante(request, comprobante_id)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    extension = EXTENSION_DE_COMPROBANTE.get(tipo)
    if extension is None:
        raise Http404
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Content-Disposition"] = f'inline; filename="comprobante.{extension}"'
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta


@require_POST
def tomar(request):
    """«Reservar» sobre una franja libre: toma el bloqueo y abre la solicitud con su cuenta regresiva."""
    datos = {campo: request.POST.get(campo) for campo in ("area", "fecha", "hora_inicio")}
    try:
        solicitud = api_reservas.tomar(request, datos)
    except ApiNoDisponible:
        return pantalla_del_calendario(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        mensajes = [mensaje for lista in error.campos.values() for mensaje in lista]
        return pantalla_del_calendario(request, " ".join(mensajes) or error.mensaje, error.cuerpo.get("solicitud"))
    return redirect("reservas:solicitud", solicitud_id=solicitud["id"])


def hora_en_letras(hora):
    """«2:00 p. m.», como escribe el maestro §5.1. El formato de Django daría «p.m.»."""
    return f"{time_format(hora, 'g:i')} {'a. m.' if hora.hour < 12 else 'p. m.'}"


def con_fechas(solicitud):
    """La API manda fecha y horas como texto; las plantillas las formatean."""
    return {
        **solicitud,
        "fecha": date.fromisoformat(solicitud["fecha"]),
        "hora_inicio": time.fromisoformat(solicitud["hora_inicio"]),
        "hora_fin": time.fromisoformat(solicitud["hora_fin"]),
    }


def solicitud(request, solicitud_id):
    return pantalla_de_la_solicitud(request, solicitud_id)


def pantalla_de_la_solicitud(request, solicitud_id, formulario=None, error_de_envio=None, error_de_pago=None):
    """La solicitud propia. En trámite, con su formulario, su cuenta regresiva y el panel de confirmación;
    en otro estado, qué pasó y el camino de vuelta, y mientras está apartada o reservada, su pago.
    """
    try:
        datos = con_fechas(api_reservas.obtener(request, solicitud_id))
    except ApiNoDisponible:
        return render(request, "reservas/solicitud.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as error:
        return render(request, "reservas/solicitud.html", {"error": error.mensaje})
    segundos = datos["segundos_restantes"]
    unidades = datos["unidades_para_solicitar"]
    motivos = [resultado["motivo"] for resultado in datos.get("evaluacion") or [] if not resultado["cumple"]]
    pago = fechas_del_pago(datos)
    se_paga = datos["estado"] in ("APARTADA", "RESERVADA")
    contexto = {
        "solicitud": datos,
        "en_tramite": datos["estado"] == "EN_SOLICITUD",
        "reloj": f"{segundos // 60}:{segundos % 60:02d}",
        "volver": url_del_calendario(datos["area"]["id"], datos["fecha"]),
        "formulario": formulario or SolicitudForm(unidades=unidades),
        "unidades": unidades,
        "error_de_envio": error_de_envio,
        # El día de la semana en letras es el punto entero de HU-12: se escribe en el servidor.
        "fecha_en_letras": date_format(datos["fecha"], r"l j \d\e F \d\e Y").lower(),
        "horario": f"{hora_en_letras(datos['hora_inicio'])} a {hora_en_letras(datos['hora_fin'])}",
        "avisos": [TEXTO_POR_AVISO[aviso] for aviso in datos.get("avisos", [])],
        # Si las reglas la rechazaron, la lista completa de motivos (HU-13).
        "motivos": motivos,
        # El pago, con menos permisos que gestión: sin nombres y solo con la subida del comprobante (HU-16).
        "pago": pago,
        "muestra_el_pago": se_paga or (datos["estado"] == "RECHAZADA" and pago["declarado"]),
        "puede_subir_comprobante": se_paga and not pago["declarado"] and len(pago["comprobantes"]) < MAXIMO_DE_COMPROBANTES,
        "aviso_del_dinero": AVISO_DEL_DINERO,
        "error_de_pago": error_de_pago,
    }
    return render(request, "reservas/solicitud.html", contexto)


@require_POST
def subir_comprobante(request, solicitud_id):
    """«Subir comprobante»: el residente lo adjunta a su solicitud. No declara el pago: eso lo hace la administración."""
    archivo = request.FILES.get("archivo")
    if archivo is None:
        return pantalla_de_la_solicitud(request, solicitud_id, error_de_pago="Elige el archivo del comprobante.")
    try:
        api_reservas.subir_comprobante(request, solicitud_id, archivo)
    except ApiNoDisponible:
        return pantalla_de_la_solicitud(request, solicitud_id, error_de_pago=MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla_de_la_solicitud(request, solicitud_id, error_de_pago=mensaje_del_error(error))
    return redirect("reservas:solicitud", solicitud_id=solicitud_id)


@require_POST
def enviar(request, solicitud_id):
    """«Enviar solicitud» del panel. Apartada o rechazada por las reglas, la pantalla de la solicitud dice qué pasó."""
    try:
        unidades = api_reservas.obtener(request, solicitud_id)["unidades_para_solicitar"]
    except (ApiNoDisponible, ErrorDeApi):
        unidades = []
    formulario = SolicitudForm(request.POST, unidades=unidades)
    if not formulario.is_valid():
        return pantalla_de_la_solicitud(request, solicitud_id, formulario)
    try:
        api_reservas.enviar(request, solicitud_id, formulario.cleaned_data)
    except ApiNoDisponible:
        return pantalla_de_la_solicitud(request, solicitud_id, formulario, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        if "motivos" not in error.cuerpo:
            # Un campo mal escrito o un 409 (venció, ya no está en trámite): se dice sin perder lo escrito.
            return pantalla_de_la_solicitud(request, solicitud_id, formulario, error.mensaje)
    return redirect("reservas:solicitud", solicitud_id=solicitud_id)


@require_POST
def liberar(request, solicitud_id):
    """«Cancelar» y el `sendBeacon` al salir llegan aquí. Si ya no estaba en trámite, no hay nada que soltar."""
    try:
        datos = api_reservas.liberar(request, solicitud_id)
    except (ApiNoDisponible, ErrorDeApi):
        return redirect("reservas:calendario")
    return redirect(url_del_calendario(datos["area"]["id"], date.fromisoformat(datos["fecha"])))
