import calendar
from datetime import date

from django.shortcuts import render
from django.utils import timezone


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


def calendario(request):
    """
    Maqueta del calendario de zonas comunes. Se arma en el servidor: cambiar de mes o elegir
    un día es un enlace y una recarga, sin JavaScript. Todavía no muestra franjas: la
    disponibilidad la decidirá la API (HU-11).
    """
    hoy = timezone.localdate()
    mes = _mes_pedido(request.GET.get("mes"), hoy)
    return render(request, "reservas/calendario.html", {
        "hoy": hoy,
        "mes": mes,
        "semanas": calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(mes.year, mes.month),
        "dia_elegido": _dia_pedido(request.GET.get("dia"), mes),
        "mes_anterior": _mes_vecino(mes, -1),
        "mes_siguiente": _mes_vecino(mes, 1),
    })
