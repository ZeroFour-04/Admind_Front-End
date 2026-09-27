from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso

from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AsignarRolForm, UsuarioForm


def lista(request):
    try:
        usuarios = api_cuentas.listar_usuarios(request)
    except ApiNoDisponible:
        usuarios = []
        error = MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        usuarios = []
        error = api_error.mensaje
    else:
        error = None
    return render(request, "usuarios/lista.html", {"usuarios": usuarios or [], "error": error})


def detalle(request, usuario_id, error_de_accion=None):
    try:
        usuario = api_cuentas.obtener_usuario(request, usuario_id)
    except ApiNoDisponible:
        usuario = None
        error = MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        usuario = None
        error = api_error.mensaje
    else:
        error = None
    roles_actuales = [asignacion["rol"] for asignacion in (usuario or {}).get("asignaciones", [])]
    contexto = {
        "usuario": usuario,
        "error": error_de_accion or error,
        "puede_asignar": tiene_permiso(request, "rol.asignar"),
        "asignar": AsignarRolForm(roles_actuales=roles_actuales),
    }
    return render(request, "usuarios/detalle.html", contexto)


# Roles en el conjunto activo (HU-06). Los errores de la API se muestran como alerta en el detalle.


@require_POST
def asignar_rol(request, usuario_id):
    # Sin roles_actuales ofrece todo el catálogo: si ya lo tiene, lo dice la API con un 409.
    formulario = AsignarRolForm(request.POST)
    if not formulario.is_valid():
        return detalle(request, usuario_id, "Elige uno de los roles del catálogo.")
    try:
        api_cuentas.asignar_rol(request, usuario_id, formulario.cleaned_data["rol"])
    except ApiNoDisponible:
        return detalle(request, usuario_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return detalle(request, usuario_id, error.mensaje)
    return redirect("usuarios:detalle", usuario_id=usuario_id)


@require_POST
def retirar_rol(request, usuario_id, asignacion_id):
    try:
        api_cuentas.retirar_rol(request, usuario_id, asignacion_id)
    except ApiNoDisponible:
        return detalle(request, usuario_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return detalle(request, usuario_id, error.mensaje)
    return redirect("usuarios:detalle", usuario_id=usuario_id)


@require_http_methods(["GET", "POST"])
def nuevo(request):
    formulario = UsuarioForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_cuentas.crear_usuario(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            for campo, mensajes in error.campos.items():
                formulario.add_error(campo if campo in formulario.fields else None, mensajes)
            if not error.campos:
                formulario.add_error(None, error.mensaje)
        else:
            return redirect("usuarios:lista")

    return render(request, "usuarios/nuevo.html", {"formulario": formulario})
