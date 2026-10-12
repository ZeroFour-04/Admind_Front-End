from datetime import datetime

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import casos as api_casos
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import CasoForm

TIPOS_DE_FOTO = {"image/png", "image/jpeg", "image/webp"}
ESTADOS_VISIBLES = {
    "ABIERTO": ("En revisión", "am-pastilla--tramite"),
    "EN_REVISION": ("En revisión", "am-pastilla--tramite"),
    "APROBADO": ("Aprobado", "am-pastilla--confirmado"),
    "RECHAZADO": ("Rechazado", "am-pastilla--error"),
    "REDIRIGIDO": ("En revisión", "am-pastilla--tramite"),
}


def lista(request, error_accion=None):
    puede_crear = tiene_permiso(request, "caso.crear")
    puede_ver_todos = tiene_permiso(request, "caso.ver_todos")
    puede_gestionar = tiene_permiso(request, "caso.gestionar")
    puede_responder = tiene_permiso(request, "caso.responder")
    if not puede_crear and not puede_ver_todos:
        return redirect("paneles:inicio")
    try:
        casos = []
        for caso in api_casos.listar(request):
            estado_visible, estado_clase = ESTADOS_VISIBLES.get(
                caso["estado"],
                (caso["estado"], "am-pastilla--neutro"),
            )
            if caso["estado"] == "REDIRIGIDO" and puede_responder:
                estado_visible = "Redirigido a Administración"
            casos.append({
                **caso,
                "creado_en": datetime.fromisoformat(caso["creado_en"]),
                "estado_visible": estado_visible,
                "estado_clase": estado_clase,
            })
    except ApiNoDisponible:
        casos, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        casos, error = [], api_error.mensaje
    else:
        error = error_accion
    return render(request, "casos/lista.html", {
        "casos": casos,
        "error": error,
        "puede_crear": puede_crear,
        "puede_ver_todos": puede_ver_todos,
        "puede_gestionar": puede_gestionar,
        "puede_responder": puede_responder,
        "creado": request.GET.get("creado") == "1",
        "gestion": request.GET.get("gestion"),
    })


def _gestionar(request, caso_id, accion):
    if not tiene_permiso(request, "caso.gestionar"):
        return redirect("casos:lista")
    datos = {"motivo": request.POST.get("motivo", "")} if accion == "rechazar" else {}
    try:
        api_casos.gestionar(request, caso_id, accion, datos)
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as api_error:
        return lista(request, api_error.mensaje)
    return redirect(f"{reverse('casos:lista')}?gestion={accion}")


@require_http_methods(["POST"])
def rechazar(request, caso_id):
    return _gestionar(request, caso_id, "rechazar")


@require_http_methods(["POST"])
def redirigir(request, caso_id):
    return _gestionar(request, caso_id, "redirigir")


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
