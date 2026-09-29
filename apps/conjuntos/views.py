from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.areas import views as vistas_de_areas
from apps.areas.forms import AYUDA_POR_CLASIFICACION, AreaForm
from apps.cuentas.sesion import destino_despues_de_entrar, guardar_estado, tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import conjuntos as api_conjuntos
from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import (
    ACENTOS,
    COLOR_PROPIO_INICIAL,
    OPCIONES_DE_COLOR,
    AcentoForm,
    AdministradorForm,
    ConjuntoForm,
    LogoForm,
)

# Los únicos tipos que la API acepta como logo. Cualquier otra cosa no se le entrega al navegador.
TIPOS_DE_LOGO = {"image/png", "image/jpeg", "image/webp"}


def actualizar_conjunto_activo(request, conjunto):
    """El nombre, el color y la foto de la barra salen de la sesión: se actualizan al cambiarlos."""
    activo = {clave: conjunto.get(clave) for clave in ("id", "nombre", "acento", "color", "logo")}
    guardar_estado(request, {"conjunto_activo": activo})


def color_inicial(conjunto):
    """El acento guardado y, para el selector de color propio, el color guardado o uno de partida."""
    return {"acento": conjunto["acento"], "color": conjunto.get("color") or COLOR_PROPIO_INICIAL}


def nombre_del_color(conjunto):
    nombre = dict(OPCIONES_DE_COLOR).get(conjunto.get("acento"))
    return f"{nombre} ({conjunto['color']})" if conjunto.get("color") else nombre


def puede_cambiar_identidad(request):
    return tiene_permiso(request, "conjunto.branding") or tiene_permiso(request, "conjunto.activar")


@require_http_methods(["GET", "POST"])
def selector(request):
    error = None
    if request.method == "POST":
        try:
            estado = api_cuentas.elegir_conjunto(request, request.POST.get("conjunto"))
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
        else:
            guardar_estado(request, estado)
            return destino_despues_de_entrar(request)

    try:
        conjuntos = api_cuentas.listar_conjuntos(request)
    except ApiNoDisponible:
        conjuntos = []
        error = error or MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        conjuntos = []
        error = error or api_error.mensaje
    contexto = {
        "conjuntos": conjuntos or [],
        "error": error,
        "puede_crear": tiene_permiso(request, "conjunto.crear"),
    }
    return render(request, "conjuntos/selector.html", contexto)


# Asistente de creación (HU-03). Cada paso se guarda apenas se completa: se puede salir y volver.


def cargar_resumen(request):
    """El resumen del conjunto activo, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_conjuntos.resumen(request), None
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje


@require_http_methods(["GET", "POST"])
def nuevo(request):
    """Paso 1 para un conjunto nuevo. Al crearlo, pasa a ser el conjunto activo."""
    formulario = ConjuntoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            respuesta = api_conjuntos.crear(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            guardar_estado(request, respuesta)
            return redirect("conjuntos:asistente-administracion")
    return render(request, "conjuntos/asistente_datos.html", {"formulario": formulario, "acentos": ACENTOS, "paso": 1})


@require_http_methods(["GET", "POST"])
def datos(request):
    """Paso 1 sobre el conjunto activo: corregir sus datos básicos."""
    resumen, error = cargar_resumen(request)
    if resumen is None:
        return render(request, "conjuntos/asistente_datos.html", {"error": error, "paso": 1, "editando": True})

    conjunto = resumen["conjunto"]
    formulario = ConjuntoForm(
        request.POST or None,
        initial={"nombre": conjunto["nombre"], "direccion": conjunto["direccion"], **color_inicial(conjunto)},
    )
    if request.method == "POST" and formulario.is_valid():
        try:
            resumen = api_conjuntos.editar(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            actualizar_conjunto_activo(request, resumen["conjunto"])
            return redirect("conjuntos:asistente-administracion")
    contexto = {"formulario": formulario, "acentos": ACENTOS, "paso": 1, "editando": True}
    return render(request, "conjuntos/asistente_datos.html", contexto)


@require_http_methods(["GET", "POST"])
def administracion(request):
    """Paso 2: quién administra el conjunto. Se puede agregar una cuenta con rol Administración."""
    formulario = AdministradorForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_cuentas.crear_usuario(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("conjuntos:asistente-administracion")
    resumen, error = cargar_resumen(request)
    contexto = {"formulario": formulario, "resumen": resumen, "error": error, "paso": 2}
    return render(request, "conjuntos/asistente_administracion.html", contexto)


@require_http_methods(["GET", "POST"])
def areas(request):
    """Paso 3: el catálogo de áreas comunes del conjunto activo (HU-09), con su alta."""
    formulario = AreaForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid() and vistas_de_areas.crear_desde(request, formulario):
        return redirect("conjuntos:asistente-areas")
    lista_de_areas, error = vistas_de_areas.cargar_areas(request)
    contexto = {
        "formulario": formulario,
        "ayudas": AYUDA_POR_CLASIFICACION,
        "areas": lista_de_areas,
        "error": error,
        "paso": 3,
    }
    return render(request, "conjuntos/asistente_areas.html", contexto)


@require_http_methods(["GET", "POST"])
def resumen(request):
    """Paso 5: revisar y, si ya cumple todo, dejarlo operativo."""
    faltantes = None
    activado = False
    error = None
    if request.method == "POST":
        try:
            api_conjuntos.activar(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje
            faltantes = api_error.cuerpo.get("faltantes")
        else:
            activado = True
    datos_del_resumen, error_al_cargar = cargar_resumen(request)
    contexto = {
        "resumen": datos_del_resumen,
        "error": error or error_al_cargar,
        "faltantes": faltantes,
        "activado": activado,
        "nombre_del_acento": nombre_del_color((datos_del_resumen or {}).get("conjunto", {})),
        "puede_cambiar_identidad": puede_cambiar_identidad(request),
        "paso": 5,
    }
    return render(request, "conjuntos/asistente_resumen.html", contexto)


# Identidad visual (HU-21): el color, uno de los ocho del catálogo o uno propio, y la foto 1:1.


@require_http_methods(["GET", "POST"])
def identidad(request):
    """Color y foto del conjunto activo. Cada formulario de la pantalla manda su `accion`."""
    try:
        conjunto = api_conjuntos.identidad(request)
    except ApiNoDisponible:
        return render(request, "conjuntos/identidad.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as error:
        return render(request, "conjuntos/identidad.html", {"error": error.mensaje})

    accion = request.POST.get("accion")
    color = AcentoForm(request.POST if accion == "color" else None, initial=color_inicial(conjunto))
    logo = LogoForm(request.POST if accion == "logo" else None, request.FILES if accion == "logo" else None)
    # Los errores de quitar el logo se muestran junto al logo.
    formulario = color if accion == "color" else logo
    if accion in ("color", "logo", "quitar_logo") and (accion == "quitar_logo" or formulario.is_valid()):
        try:
            if accion == "color":
                conjunto = api_conjuntos.cambiar_acento(
                    request, color.cleaned_data["acento"], color.cleaned_data.get("color")
                )
            elif accion == "logo":
                conjunto = api_conjuntos.subir_logo(request, logo.cleaned_data["archivo"])
            else:
                conjunto = api_conjuntos.quitar_logo(request)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            actualizar_conjunto_activo(request, conjunto)
            return redirect(f"{reverse('conjuntos:identidad')}?guardado=1")

    contexto = {
        "conjunto": conjunto,
        "color": color,
        "logo": logo,
        "acentos": ACENTOS,
        "guardado": request.GET.get("guardado") == "1",
    }
    return render(request, "conjuntos/identidad.html", contexto)


@require_GET
def logo(request, huella):
    """La imagen del logo. La pide este servidor con el token de la sesión: el navegador no habla con la API.

    La URL lleva la huella de la imagen, así que lo que hay en una URL nunca cambia y el navegador
    lo puede guardar. Si la API no la entrega, 404: la barra y el selector siguen mostrando el nombre.
    """
    try:
        contenido, tipo = api_conjuntos.imagen_del_logo(request, huella)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    if tipo not in TIPOS_DE_LOGO:
        raise Http404
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["Cache-Control"] = "private, max-age=31536000, immutable"
    return respuesta
