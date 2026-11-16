"""Casos (HU-29): el residente abre y consulta los suyos; gestión los atiende desde el detalle.

La lista de gestión es la pestaña Casos del dashboard (`apps/triage`). Aquí solo se muestra: qué
operación admite un caso y quién puede hacerla lo decide la API.
"""
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import casos as api_casos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import CasoForm
from .presentacion import EN_SECRETARIA, PRIORIDADES_VISIBLES, caso_para_mostrar

TIPOS_DE_FOTO = {"image/png", "image/jpeg", "image/webp"}
# Las mismas claves que la API. Sin «otro»: lo que no cabe aquí se redirige al administrador.
CAUSALES_DE_DESCARTE = (
    ("NO_ES_COMPETENCIA", "No es competencia de la administración"),
    ("DUPLICADO", "Caso duplicado"),
    ("INFORMACION_INSUFICIENTE", "Información insuficiente"),
)
# Cada acción del detalle: qué campos del formulario viajan a la API y qué se dice al volver.
ACCIONES = {
    "tomar": ((), "El caso quedó en revisión."),
    "prioridad": (("prioridad", "justificacion"), "La prioridad quedó guardada."),
    "redirigir": (("nota",), "El caso fue redirigido a Administración."),
    "descartar": (("causal", "motivo"), "El caso fue descartado y el residente podrá ver la razón."),
    "responder": (("respuesta",), "La respuesta quedó enviada y el caso, resuelto."),
    "rechazar": (("motivo",), "El caso fue rechazado y el residente podrá ver la razón."),
}


def url_del_dashboard():
    return f"{reverse('triage:bandeja')}?pestana=casos"


def lista(request):
    """Los casos propios. Gestión los ve en la pestaña Casos del dashboard, con su tabla."""
    puede_crear = tiene_permiso(request, "caso.crear")
    if tiene_permiso(request, "caso.ver_todos") and tiene_permiso(request, "solicitud.bandeja_ver"):
        return redirect(url_del_dashboard())
    if not puede_crear:
        return redirect("paneles:inicio")
    try:
        casos = [caso_para_mostrar(caso) for caso in api_casos.listar(request)]
        error = None
    except ApiNoDisponible:
        casos, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        casos, error = [], api_error.mensaje
    return render(request, "casos/lista.html", {
        "casos": casos,
        "error": error,
        "puede_crear": puede_crear,
        "creado": request.GET.get("creado") == "1",
    })


def acciones_para(request, caso):
    """Qué formularios se ofrecen. No es lo que impide la acción: eso lo hace la API con 403 o 409."""
    gestiona = tiene_permiso(request, "caso.gestionar")
    responde = tiene_permiso(request, "caso.responder")
    abierto = caso["abierto"]
    en_secretaria = caso["estado"] in EN_SECRETARIA
    return {
        "tomar": caso["estado"] == "ABIERTO" and (gestiona or responde),
        "prioridad": abierto and tiene_permiso(request, "solicitud.priorizar"),
        "redirigir": en_secretaria and gestiona,
        "descartar": en_secretaria and gestiona,
        "responder": abierto and responde,
        "rechazar": abierto and responde,
    }


def pantalla_del_detalle(request, caso_id, error=None, escrito=None):
    try:
        caso = caso_para_mostrar(api_casos.obtener(request, caso_id))
    except ApiNoDisponible:
        return render(request, "casos/detalle.html", {"error": MENSAJE_API_NO_DISPONIBLE})
    except ErrorDeApi as api_error:
        if api_error.estado == 404:
            raise Http404
        return render(request, "casos/detalle.html", {"error": api_error.mensaje})
    acciones = acciones_para(request, caso)
    hecho = ACCIONES.get(request.GET.get("hecho"))
    return render(request, "casos/detalle.html", {
        "caso": caso,
        "error": error,
        # Lo que la persona había escrito cuando la acción falló: no se pierde.
        "escrito": escrito or {},
        "aviso": hecho[1] if hecho else None,
        "acciones": acciones,
        "hay_acciones": any(acciones.values()),
        # Administración abre la infracción desde el caso; el registro se llena a mano (el caso no guarda la vivienda).
        "puede_registrar_infraccion": tiene_permiso(request, "infraccion.registrar"),
        "prioridades": [(clave, nombre) for clave, (nombre, _) in PRIORIDADES_VISIBLES.items()],
        "causales": CAUSALES_DE_DESCARTE,
        "volver": url_del_dashboard(),
    })


@require_GET
def detalle(request, caso_id):
    """El caso para gestión, con las acciones de su rol. El residente consulta los suyos en la lista."""
    if not tiene_permiso(request, "caso.ver_todos"):
        return redirect("casos:lista")
    return pantalla_del_detalle(request, caso_id)


def mensaje_del_error(error):
    """Los errores por campo de la API (400) en una frase; si no los trae, el mensaje general."""
    mensajes = [mensaje for lista_de_campo in error.campos.values() for mensaje in lista_de_campo]
    return " ".join(mensajes) or error.mensaje


@require_POST
def gestionar(request, caso_id, accion):
    """Una operación sobre el caso: se manda a la API tal cual y se vuelve al detalle."""
    if accion not in ACCIONES:
        raise Http404
    if not tiene_permiso(request, "caso.ver_todos"):
        return redirect("casos:lista")
    campos, _ = ACCIONES[accion]
    datos = {campo: request.POST.get(campo, "").strip() for campo in campos}
    try:
        api_casos.gestionar(request, caso_id, accion, datos)
    except ApiNoDisponible:
        return pantalla_del_detalle(request, caso_id, MENSAJE_API_NO_DISPONIBLE, datos)
    except ErrorDeApi as api_error:
        return pantalla_del_detalle(request, caso_id, mensaje_del_error(api_error), datos)
    return redirect(f"{reverse('casos:detalle', kwargs={'caso_id': caso_id})}?hecho={accion}")


@require_http_methods(["GET", "POST"])
def nuevo(request):
    if not tiene_permiso(request, "caso.crear"):
        return redirect("casos:lista")
    formulario = CasoForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and formulario.is_valid():
        datos = {
            "titulo": formulario.cleaned_data["titulo"],
            "caso": formulario.cleaned_data["caso"],
        }
        try:
            api_casos.crear(request, datos, formulario.cleaned_data["foto"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(f"{reverse('casos:lista')}?creado=1")
    return render(request, "casos/nuevo.html", {"formulario": formulario})


@require_GET
def foto(request, caso_id, foto_id):
    try:
        contenido, tipo = api_casos.foto(request, caso_id, foto_id)
    except (ApiNoDisponible, ErrorDeApi):
        raise Http404
    if tipo not in TIPOS_DE_FOTO:
        raise Http404
    respuesta = HttpResponse(contenido, content_type=tipo)
    respuesta["X-Content-Type-Options"] = "nosniff"
    respuesta["Cache-Control"] = "private, max-age=3600"
    return respuesta
