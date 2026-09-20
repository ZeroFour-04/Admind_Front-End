from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from cliente_api import cuentas as api_cuentas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import UsuarioForm


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


def detalle(request, usuario_id):
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
    return render(request, "usuarios/detalle.html", {"usuario": usuario, "error": error})


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
