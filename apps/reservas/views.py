"""Zonas comunes (HU-11): el calendario con las franjas de un área, tomar el bloqueo y la solicitud en trámite.

Si una franja está libre o si un bloqueo venció lo decide la API; aquí solo se muestra.
"""
import calendar
from datetime import date, time
from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format, time_format
from django.views.decorators.http import require_POST

from apps.areas.views import cargar_areas
from apps.cuentas.sesion import tiene_permiso
from cliente_api import reservas as api_reservas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import SolicitudForm

# Cómo se ve cada estado de franja: siempre con texto, nunca solo con color.
PASTILLA_POR_ESTADO = {
    "libre": ("Libre", "am-pastilla--confirmado"),
    "en_solicitud": ("En trámite", "am-pastilla--tramite"),
    "apartada": ("Apartada", "am-pastilla--tramite"),
    "reservada": ("Reservada", "am-pastilla--neutro"),
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


def pantalla_del_calendario(request, error=None, solicitud_en_curso=None):
    """El calendario del mes, se arma en el servidor: cambiar de mes, de día o de área es un enlace."""
    hoy = timezone.localdate()
    mes = _mes_pedido(request.GET.get("mes"), hoy)
    dia = _dia_pedido(request.GET.get("dia"), mes)
    areas, error_de_areas = cargar_areas(request)
    areas = [area for area in areas if area["activo"]]
    area = next((area for area in areas if area["id"] == request.GET.get("area")), None)
    franjas, error_de_franjas = cargar_franjas(request, area["id"], dia) if area and dia else ([], None)
    return render(request, "reservas/calendario.html", {
        "hoy": hoy,
        "mes": mes,
        "semanas": calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(mes.year, mes.month),
        "dia_elegido": dia,
        "mes_anterior": _mes_vecino(mes, -1),
        "mes_siguiente": _mes_vecino(mes, 1),
        "areas": areas,
        "area": area,
        "franjas": franjas,
        "error": error or error_de_areas or error_de_franjas,
        "solicitud_en_curso": solicitud_en_curso,
        "puede_solicitar": tiene_permiso(request, "reserva.solicitar"),
    })


def calendario(request):
    return pantalla_del_calendario(request)


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


def pantalla_de_la_solicitud(request, solicitud_id, formulario=None, error_de_envio=None):
    """La solicitud propia. En trámite, con su formulario, su cuenta regresiva y el panel de confirmación;
    en otro estado, qué pasó y el camino de vuelta.
    """
    try:
        datos = con_fechas(api_reservas.obtener(request, solicitud_id))
    except ApiNoDisponible:
        return render(request, "reservas/solicitud.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as error:
        return render(request, "reservas/solicitud.html", {"error": error.mensaje})
    segundos = datos["segundos_restantes"]
    unidades = datos["unidades_para_solicitar"]
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
    }
    return render(request, "reservas/solicitud.html", contexto)


@require_POST
def liberar(request, solicitud_id):
    """«Cancelar» y el `sendBeacon` al salir llegan aquí. Si ya no estaba en trámite, no hay nada que soltar."""
    try:
        datos = api_reservas.liberar(request, solicitud_id)
    except (ApiNoDisponible, ErrorDeApi):
        return redirect("reservas:calendario")
    return redirect(url_del_calendario(datos["area"]["id"], date.fromisoformat(datos["fecha"])))
