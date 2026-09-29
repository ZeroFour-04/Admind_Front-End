from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import cuentas as api_cuentas
from cliente_api import personas as api_personas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AsignarRolForm, BuscarPersonaForm, UsuarioForm, VincularPersonaForm

# El documento buscado pasa al alta por la sesión: nunca por la URL (maestro §5.2, plan P4).
CLAVE_DOCUMENTO_BUSCADO = "documento_buscado"


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


# Registrar persona (HU-07): buscar por documento exacto; si existe, vincularla; si no, darla de alta.


@require_http_methods(["GET", "POST"])
def registrar(request):
    if not tiene_permiso(request, "persona.buscar"):
        return redirect("usuarios:lista")
    busqueda = BuscarPersonaForm(request.POST if request.POST.get("accion") == "buscar" else None)
    vinculo = VincularPersonaForm(request.POST if request.POST.get("accion") == "vincular" else None)
    encontrada = None

    if busqueda.is_bound and busqueda.is_valid():
        try:
            resultado = api_personas.buscar(request, busqueda.cleaned_data)
        except ApiNoDisponible:
            busqueda.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(busqueda, error)
        else:
            if not resultado["encontrada"]:
                request.session[CLAVE_DOCUMENTO_BUSCADO] = busqueda.cleaned_data
                return redirect("usuarios:nuevo")
            encontrada = resultado["persona"]
            vinculo = VincularPersonaForm(initial={"persona": encontrada["id"]})

    if vinculo.is_bound and vinculo.is_valid():
        try:
            api_personas.vincular(request, {**vinculo.cleaned_data, "persona": str(vinculo.cleaned_data["persona"])})
        except ApiNoDisponible:
            vinculo.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(vinculo, error)
        else:
            return redirect("usuarios:lista")

    contexto = {
        "busqueda": busqueda,
        "encontrada": encontrada,
        "vinculo": vinculo,
        "puede_vincular": tiene_permiso(request, "persona.vincular"),
    }
    return render(request, "usuarios/registrar.html", contexto)


# Rol en el conjunto activo (HU-06): uno solo por persona. Los errores de la API se muestran como alerta en el detalle.


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
def cambiar_rol(request, usuario_id, asignacion_id):
    formulario = AsignarRolForm(request.POST)
    if not formulario.is_valid():
        return detalle(request, usuario_id, "Elige uno de los roles del catálogo.")
    try:
        api_cuentas.cambiar_rol(request, usuario_id, asignacion_id, formulario.cleaned_data["rol"])
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


@require_POST
def eliminar(request, usuario_id):
    try:
        api_cuentas.retirar_usuario_del_conjunto(request, usuario_id)
    except ApiNoDisponible:
        return detalle(request, usuario_id, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return detalle(request, usuario_id, error.mensaje)
    return redirect("usuarios:lista")


@require_http_methods(["GET", "POST"])
def nuevo(request):
    # Si viene de una búsqueda sin resultado, el documento se precarga y se borra de la sesión.
    documento = request.session.pop(CLAVE_DOCUMENTO_BUSCADO, None) if request.method == "GET" else None
    formulario = UsuarioForm(request.POST or None, initial=documento or {})
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
