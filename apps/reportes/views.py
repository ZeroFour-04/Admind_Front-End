"""Pantalla de reportes y descargas protegidas por `reporte.ver`."""
from datetime import date

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET

from apps.cuentas.sesion import tiene_permiso
from cliente_api import reportes as api_reportes
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi


def opciones(request, error=None):
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    return render(
        request,
        "reportes/inicio.html",
        {
            "error": error,
            "desde": request.GET.get("desde", inicio_mes.isoformat()),
            "hasta": request.GET.get("hasta", hoy.isoformat()),
            "periodo": request.GET.get("periodo", hoy.strftime("%Y-%m")),
        },
    )


def mensaje_de_error(error):
    mensajes = [mensaje for lista in error.campos.values() for mensaje in lista]
    return " ".join(mensajes) or error.mensaje


@require_GET
def inicio(request):
    if not tiene_permiso(request, "reporte.ver"):
        return redirect("paneles:inicio")
    return opciones(request)


@require_GET
def descargar_zonas(request):
    if not tiene_permiso(request, "reporte.ver"):
        return redirect("paneles:inicio")
    desde_texto, hasta_texto = request.GET.get("desde", ""), request.GET.get("hasta", "")
    try:
        desde, hasta = date.fromisoformat(desde_texto), date.fromisoformat(hasta_texto)
    except ValueError:
        return opciones(request, "Selecciona un rango de fechas válido.")
    if desde.isoformat() != desde_texto or hasta.isoformat() != hasta_texto:
        return opciones(request, "Selecciona un rango de fechas válido.")
    if hasta < desde:
        return opciones(request, "La fecha final debe ser igual o posterior a la inicial.")
    try:
        contenido, tipo = api_reportes.zonas(request, desde_texto, hasta_texto)
    except ApiNoDisponible:
        return opciones(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return opciones(request, mensaje_de_error(error))
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Content-Disposition"] = (
        f'attachment; filename="uso-zonas-comunes-{desde_texto}-{hasta_texto}.pdf"'
    )
    return respuesta


@require_GET
def descargar_pagos(request):
    if not tiene_permiso(request, "reporte.ver"):
        return redirect("paneles:inicio")
    periodo = request.GET.get("periodo", "")
    try:
        anio, mes = (int(parte) for parte in periodo.split("-"))
        if len(periodo) != 7 or date(anio, mes, 1).strftime("%Y-%m") != periodo:
            raise ValueError
    except ValueError:
        return opciones(request, "Selecciona un mes válido.")
    try:
        contenido, tipo = api_reportes.pagos(request, periodo)
    except ApiNoDisponible:
        return opciones(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return opciones(request, mensaje_de_error(error))
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Content-Disposition"] = f'attachment; filename="estado-pagos-{periodo}.xlsx"'
    return respuesta
