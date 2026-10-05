"""El tablón del conjunto activo (HU-25): leer, publicar con alcance y con fotos, y editar el texto."""
from datetime import datetime

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import anuncios as api_anuncios
from cliente_api import unidades as api_unidades
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AnuncioForm, EditarAnuncioForm

# Dos permisos separados: dirigir a una vivienda no viene incluido en publicar. Los exige la API;
# aquí solo sirven para no ofrecer lo que la persona no puede hacer.
PERMISO_POR_ALCANCE = {"conjunto": "anuncio.publicar", "vivienda": "anuncio.dirigir"}

# Los únicos tipos que la API guarda como foto. Cualquier otra cosa no se le entrega al navegador.
TIPOS_DE_FOTO = {"image/png", "image/jpeg", "image/webp"}


def alcances_permitidos(request):
    return [alcance for alcance, permiso in PERMISO_POR_ALCANCE.items() if tiene_permiso(request, permiso)]


def con_fechas(anuncio):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    fechas = {campo: datetime.fromisoformat(anuncio[campo]) for campo in ("publicado_en", "editado_en") if anuncio.get(campo)}
    return {**anuncio, **fechas}


def lista(request):
    try:
        anuncios = [con_fechas(anuncio) for anuncio in api_anuncios.listar(request)]
    except ApiNoDisponible:
        anuncios, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        anuncios, error = [], api_error.mensaje
    else:
        error = None
    contexto = {
        "anuncios": anuncios,
        "error": error,
        "puede_publicar": bool(alcances_permitidos(request)),
        "publicado": request.GET.get("publicado") == "1",
    }
    return render(request, "anuncios/lista.html", contexto)


@require_http_methods(["GET", "POST"])
def nuevo(request):
    alcances = alcances_permitidos(request)
    if not alcances:
        return redirect("anuncios:lista")

    unidades, error = [], None
    if "vivienda" in alcances:
        try:
            unidades = api_unidades.listar(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje

    formulario = AnuncioForm(request.POST or None, request.FILES or None, alcances=alcances, unidades=unidades)
    if request.method == "POST" and formulario.is_valid():
        # Las fotos van aparte de los datos: son archivos, no campos del anuncio.
        datos = dict(formulario.cleaned_data)
        fotos = datos.pop("fotos")
        try:
            api_anuncios.publicar(request, datos, fotos)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as api_error:
            errores_de_la_api_al_formulario(formulario, api_error)
        else:
            return redirect(f"{reverse('anuncios:lista')}?publicado=1")

    contexto = {
        "formulario": formulario,
        "error": error,
        "ofrece_vivienda": "vivienda" in alcances,
        "hay_viviendas": bool(unidades),
    }
    return render(request, "anuncios/nuevo.html", contexto)


@require_http_methods(["GET", "POST"])
def editar(request, anuncio_id):
    try:
        anuncio = con_fechas(api_anuncios.obtener(request, anuncio_id))
    except ApiNoDisponible:
        return render(request, "anuncios/editar.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as api_error:
        return render(request, "anuncios/editar.html", {"error": api_error.mensaje})
    if not anuncio["puede_editar"]:
        return render(request, "anuncios/editar.html", {"error": "Solo quien publicó el anuncio puede editarlo."})

    formulario = EditarAnuncioForm(request.POST or None, initial={"titulo": anuncio["titulo"], "cuerpo": anuncio["cuerpo"]})
    if request.method == "POST" and formulario.is_valid():
        try:
            api_anuncios.editar(request, anuncio_id, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as api_error:
            errores_de_la_api_al_formulario(formulario, api_error)
        else:
            return redirect("anuncios:lista")

    return render(request, "anuncios/editar.html", {"anuncio": anuncio, "formulario": formulario})


@require_GET
def foto(request, anuncio_id, foto_id):
    """La imagen de una foto. La pide este servidor con el token de la sesión: el navegador no habla con la API.

    Las fotos de un anuncio no cambian, así que lo que hay en una URL es siempre lo mismo y el
    navegador lo puede guardar. Si la API no la entrega (no existe o la persona no ve ese anuncio), 404.
    """
    try:
        contenido, tipo = api_anuncios.foto(request, anuncio_id, foto_id)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    if tipo not in TIPOS_DE_FOTO:
        raise Http404
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Cache-Control"] = "private, max-age=31536000, immutable"
    return respuesta
