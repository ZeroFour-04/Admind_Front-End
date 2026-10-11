"""Pago de la administración (HU-35): la tabla de gestión, «Mis pagos» del residente y el comprobante.

La vista no decide permisos: usa los de la sesión para elegir la pantalla, y la API es la que niega.
El archivo no se guarda aquí: pasa del navegador a la API y de la API al navegador.
"""
from datetime import date, datetime
from urllib.parse import urlencode

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import pagos as api_pagos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import ReportarPagoForm

# El aviso del dinero se escribe aquí, una sola vez; las dos pantallas lo reciben por contexto (criterio 3).
AVISO_DEL_DINERO = "AdMind no verifica el dinero: el pago lo confirma una persona de la administración."
EXTENSION_DE_COMPROBANTE = {"application/pdf": "pdf", "image/png": "png", "image/jpeg": "jpg"}
PASTILLA_POR_ESTADO = {
    "sin_reporte": ("Sin reporte", "am-pastilla--neutro"),
    "reportado": ("Reportado", "am-pastilla--tramite"),
    "confirmado": ("Confirmado", "am-pastilla--confirmado"),
}


def mes_en_letras(periodo):
    """«2026-10» → «octubre de 2026»."""
    anio, mes = (int(parte) for parte in periodo.split("-"))
    return date_format(date(anio, mes, 1), r"F \d\e Y").lower()


def mes_vecino(periodo, paso):
    """El mes anterior o siguiente, como «AAAA-MM», para los enlaces de la tabla."""
    anio, mes = (int(parte) for parte in periodo.split("-"))
    indice = anio * 12 + (mes - 1) + paso
    return f"{indice // 12:04d}-{indice % 12 + 1:02d}"


def con_fechas_del_pago(datos):
    """Un pago de la API con su pastilla y sus fechas de verdad para la plantilla."""
    etiqueta, clase = PASTILLA_POR_ESTADO[datos["estado"]]
    comprobante = datos.get("comprobante")
    return {
        **datos,
        "etiqueta": etiqueta,
        "clase": clase,
        "reportado_en": datetime.fromisoformat(datos["reportado_en"]) if datos.get("reportado_en") else None,
        "confirmado_en": datetime.fromisoformat(datos["confirmado_en"]) if datos.get("confirmado_en") else None,
        "comprobante": (
            {**comprobante, "subido_en": datetime.fromisoformat(comprobante["subido_en"])} if comprobante else None
        ),
    }


def mensaje_del_error(error):
    """Los errores por campo de la API (400) en una frase; si no los trae, el mensaje general."""
    mensajes = [mensaje for lista in error.campos.values() for mensaje in lista]
    return " ".join(mensajes) or error.mensaje


@require_http_methods(["GET", "POST"])
def administracion(request):
    """`/pagos/administracion/`: la tabla para quien gestiona y «Mis pagos» para quien solo reporta."""
    if tiene_permiso(request, "pago.ver"):
        if request.method == "POST":
            return redirect("pagos:administracion")
        return tabla_de_gestion(request, request.GET.get("periodo", ""), request.GET.get("buscar", "").strip())
    if tiene_permiso(request, "pago.reportar"):
        return reportar(request) if request.method == "POST" else mis_pagos(request)
    return redirect("paneles:inicio")


def tabla_de_gestion(request, periodo="", buscar="", error_de_accion=None):
    """La tabla del mes. La búsqueda la hace el servidor: aquí solo se pasa lo escrito."""
    error, filas, resuelto = None, [], None
    try:
        datos = api_pagos.listar(request, periodo or None, buscar)
        resuelto = datos["periodo"]
        filas = [con_fechas_del_pago(fila) for fila in datos["filas"]]
    except ApiNoDisponible:
        error = MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        error = mensaje_del_error(api_error)
    if resuelto is None:
        # Sin respuesta de la API se muestra el mes pedido, o el de hoy si no era un mes.
        try:
            mes_en_letras(periodo)
            resuelto = periodo
        except (ValueError, AttributeError):
            resuelto = timezone.localdate().strftime("%Y-%m")
    return render(request, "pagos/gestion.html", {
        "periodo": resuelto,
        "mes": mes_en_letras(resuelto),
        "mes_anterior": mes_vecino(resuelto, -1),
        "mes_siguiente": mes_vecino(resuelto, 1),
        "buscar": buscar,
        "filas": filas,
        "error": error_de_accion or error,
        "aviso_del_dinero": AVISO_DEL_DINERO,
        "puede_confirmar": tiene_permiso(request, "pago.confirmar"),
    })


@require_POST
def confirmar(request, unidad_id, periodo):
    """El check de una vivienda y un mes. Vuelve a la misma URL, con el mismo mes y la misma búsqueda."""
    buscar = request.POST.get("buscar", "").strip()
    confirmado = request.POST.get("confirmado") == "1"
    try:
        api_pagos.confirmar(request, unidad_id, periodo, confirmado)
    except ApiNoDisponible:
        return tabla_de_gestion(request, periodo, buscar, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return tabla_de_gestion(request, periodo, buscar, mensaje_del_error(error))
    consulta = {"periodo": periodo, **({"buscar": buscar} if buscar else {})}
    return redirect(f"{reverse('pagos:administracion')}?{urlencode(consulta)}")


def cargar_viviendas(request):
    """Las viviendas del residente con sus meses, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_pagos.mios(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def meses_de(viviendas):
    """Los meses que se pueden elegir al reportar: los que la API le muestra a esta persona."""
    return [(p["periodo"], mes_en_letras(p["periodo"])) for p in viviendas[0]["periodos"]] if viviendas else []


def mis_pagos(request, formulario=None, error=None, viviendas=None, error_de_carga=None):
    """Los últimos meses de cada vivienda del residente y el formulario para reportar un pago."""
    if viviendas is None:
        viviendas, error_de_carga = cargar_viviendas(request)
    tarjetas = [
        {
            "unidad": vivienda["unidad"],
            "periodos": [
                {**con_fechas_del_pago(p), "periodo": p["periodo"], "mes": mes_en_letras(p["periodo"])}
                for p in vivienda["periodos"]
            ],
        }
        for vivienda in viviendas
    ]
    if formulario is None and tarjetas:
        formulario = ReportarPagoForm(viviendas=[v["unidad"] for v in viviendas], meses=meses_de(viviendas))
    return render(request, "pagos/mis_pagos.html", {
        "tarjetas": tarjetas,
        "formulario": formulario,
        "una_sola_vivienda": len(tarjetas) == 1,
        "error": error or error_de_carga,
        "reportado": request.GET.get("reportado") == "1",
        "aviso_del_dinero": AVISO_DEL_DINERO,
    })


def reportar(request):
    """«Subir comprobante»: los 400 caen en su campo y el 409 va arriba del formulario."""
    viviendas, error_de_carga = cargar_viviendas(request)
    formulario = ReportarPagoForm(
        request.POST, request.FILES, viviendas=[v["unidad"] for v in viviendas], meses=meses_de(viviendas)
    )
    if formulario.is_valid():
        datos = formulario.cleaned_data
        try:
            api_pagos.reportar(request, datos["unidad"], datos["periodo"], datos["archivo"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as api_error:
            errores_de_la_api_al_formulario(formulario, api_error)
        else:
            return redirect(f"{reverse('pagos:administracion')}?reportado=1")
    return mis_pagos(request, formulario, viviendas=viviendas, error_de_carga=error_de_carga)


@require_GET
def comprobante(request, comprobante_id):
    """El archivo de un comprobante. Lo pide este servidor con el token: el navegador nunca habla con la API."""
    try:
        contenido, tipo = api_pagos.comprobante(request, comprobante_id)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    extension = EXTENSION_DE_COMPROBANTE.get(tipo)
    if extension is None:
        raise Http404
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Content-Disposition"] = f'inline; filename="comprobante.{extension}"'
    respuesta["X-Content-Type-Options"] = "nosniff"
    return respuesta
