"""Los documentos del conjunto (HU-33): el reglamento y el manual de convivencia.

El front no guarda nada ni toca el archivo: lo pide a la API con el token de la sesión y se lo pasa al navegador.
Qué se puede hacer lo decide la API con el permiso; aquí solo se muestran o se esconden los botones.
"""
from datetime import datetime

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import documentos as api_documentos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import DocumentoForm

TIPOS = ("reglamento", "manual")


def tipo_valido(tipo):
    """Un tipo que no está en el catálogo es un 404, igual que en la API."""
    if tipo not in TIPOS:
        raise Http404
    return tipo


def con_fecha(fila):
    """La fecha de la API llega como texto: se convierte para escribirla con el día en letras."""
    if fila.get("subido_en"):
        return {**fila, "subido_en": datetime.fromisoformat(fila["subido_en"])}
    return fila


def pantalla(request, formulario_de=None, tipo_con_formulario=None, error_de_accion=None):
    puede_subir = tiene_permiso(request, "documento.subir")
    try:
        documentos, error = [con_fecha(fila) for fila in api_documentos.vigentes(request)], None
    except ApiNoDisponible:
        documentos, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        documentos, error = [], falla.mensaje
    for documento in documentos:
        # Solo el formulario del tipo que se acaba de enviar trae lo escrito y sus errores.
        documento["formulario"] = formulario_de if documento["tipo"] == tipo_con_formulario else DocumentoForm()
    return render(request, "documentos/lista.html", {
        "documentos": documentos,
        "error": error_de_accion or error,
        "puede_subir": puede_subir,
        "puede_ver_versiones": tiene_permiso(request, "documento.descargar"),
        "aviso": "Documento subido: la versión anterior se conserva en las versiones." if request.GET.get("hecho") == "subido" else None,
    })


@require_GET
def lista(request):
    if not (tiene_permiso(request, "documento.ver") or tiene_permiso(request, "documento.subir")):
        return redirect("paneles:inicio")
    return pantalla(request)


@require_POST
def subir(request, tipo):
    tipo = tipo_valido(tipo)
    if not tiene_permiso(request, "documento.subir"):
        return redirect("documentos:lista")
    formulario = DocumentoForm(request.POST, request.FILES)
    if formulario.is_valid():
        try:
            api_documentos.subir(request, tipo, formulario.cleaned_data["archivo"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as falla:
            errores_de_la_api_al_formulario(formulario, falla)
        else:
            return redirect(f"{reverse('documentos:lista')}?hecho=subido")
    return pantalla(request, formulario, tipo)


def como_pdf(contenido, tipo_mime, nombre):
    if tipo_mime != "application/pdf":
        raise Http404
    respuesta = HttpResponse(contenido, content_type="application/pdf")
    respuesta["Content-Disposition"] = f'inline; filename="{nombre}.pdf"'
    return respuesta


@require_GET
def archivo(request, tipo):
    """El PDF vigente. Lo pide este servidor con el token de la sesión: el navegador no habla con la API."""
    tipo = tipo_valido(tipo)
    try:
        contenido, tipo_mime = api_documentos.archivo(request, tipo)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    return como_pdf(contenido, tipo_mime, tipo)


@require_GET
def versiones(request, tipo):
    """Todas las versiones de un tipo, la vigente primero. Solo para quien tiene `documento.descargar`."""
    tipo = tipo_valido(tipo)
    if not tiene_permiso(request, "documento.descargar"):
        return redirect("documentos:lista")
    try:
        filas, error = [con_fecha(fila) for fila in api_documentos.versiones(request, tipo)], None
    except ApiNoDisponible:
        filas, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        filas, error = [], falla.mensaje
    return render(request, "documentos/versiones.html", {"tipo": tipo, "versiones": filas, "error": error})


@require_GET
def archivo_de_version(request, tipo, version_id):
    tipo = tipo_valido(tipo)
    if not tiene_permiso(request, "documento.descargar"):
        return redirect("documentos:lista")
    try:
        contenido, tipo_mime = api_documentos.archivo_de_version(request, tipo, version_id)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    return como_pdf(contenido, tipo_mime, tipo)
