"""Parqueaderos del conjunto activo: el catálogo (HU-28) y su asignación a una vivienda (HU-34).

El front no guarda nada: cada pantalla le pide a la API. Qué se puede hacer lo decide ella con el permiso.
Un parqueadero de visitantes no tiene «Asignar» ni «Historial»: no se asigna nunca. Y no hay ninguna pantalla
que quite un puesto por mora ni como sanción; solo se reasigna a otra vivienda o se libera.
"""
from datetime import date

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import parqueaderos as api_parqueaderos
from cliente_api import reglas as api_reglas
from cliente_api import unidades as api_unidades
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import AsignarForm, ParqueaderoForm

TEXTO_DEL_AVISO = {
    "creado": "Parqueadero creado.",
    "retirado": "Parqueadero retirado.",
    "asignado": "Parqueadero asignado.",
    "reasignado": "Parqueadero reasignado: la asignación anterior quedó cerrada en el historial.",
    "liberado": "Parqueadero liberado: quedó sin asignar y el historial se conserva.",
}
TIPO_DE_REGLA_DEL_TOPE = "PARQUEADEROS_POR_VIVIENDA"


def es_residente(request):
    sesion = request.session
    return "Residente" in (sesion.get("roles") or []) or sesion.get("tipo_usuario") == "Residente"


def cargar_parqueaderos(request):
    """Los parqueaderos activos del conjunto, o el mensaje de error para mostrar en su lugar."""
    try:
        return api_parqueaderos.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return [], error.mensaje


def tope_del_conjunto(request):
    """La regla «parqueaderos por vivienda» en palabras, o `None` si el conjunto no la definió (o no se pudo leer)."""
    try:
        reglas = api_reglas.listar(request)
    except (ApiNoDisponible, ErrorDeApi):
        return None
    for regla in reglas:
        if regla["tipo"] == TIPO_DE_REGLA_DEL_TOPE:
            return regla["descripcion"]
    return None


def con_fechas(filas, *campos):
    """Las fechas que la API manda como texto AAAA-MM-DD, como fechas, para que la plantilla las formatee."""
    return [
        {**fila, **{campo: date.fromisoformat(fila[campo]) if fila.get(campo) else None for campo in campos}}
        for fila in filas
    ]


def pantalla(request, formulario=None, error_de_accion=None):
    puede_gestionar = tiene_permiso(request, "parqueadero.gestionar")
    puede_asignar = tiene_permiso(request, "parqueadero.asignar")
    parqueaderos, error = cargar_parqueaderos(request)
    return render(request, "parqueaderos/lista.html", {
        "parqueaderos": parqueaderos,
        "error": error_de_accion or error,
        "puede_gestionar": puede_gestionar,
        "puede_asignar": puede_asignar,
        # Solo quien asigna necesita saber cuánto cabe en una vivienda.
        "tope": tope_del_conjunto(request) if puede_asignar else None,
        "formulario": (formulario or ParqueaderoForm()) if puede_gestionar else None,
        "aviso": TEXTO_DEL_AVISO.get(request.GET.get("hecho")),
    })


@require_http_methods(["GET", "POST"])
def lista(request):
    puede_gestionar = tiene_permiso(request, "parqueadero.gestionar")
    if not (puede_gestionar or tiene_permiso(request, "parqueadero.ver") or tiene_permiso(request, "parqueadero.asignar")):
        # El residente que abre «Parqueaderos» llega a los suyos.
        return redirect("parqueaderos:mios" if es_residente(request) else "paneles:inicio")
    if request.method == "POST":
        if not puede_gestionar:
            return redirect("parqueaderos:lista")
        formulario = ParqueaderoForm(request.POST)
        if formulario.is_valid():
            try:
                api_parqueaderos.crear(request, formulario.datos_para_api())
            except ApiNoDisponible:
                formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
            except ErrorDeApi as error:
                errores_de_la_api_al_formulario(formulario, error)
            else:
                return redirect(f"{reverse('parqueaderos:lista')}?hecho=creado")
        return pantalla(request, formulario)
    return pantalla(request)


@require_POST
def desactivar(request, parqueadero_id):
    """«Confirmar retiro»: el 409 de «ocupado» o «asignado» se muestra arriba de la tabla, con el texto de la API."""
    try:
        api_parqueaderos.desactivar(request, parqueadero_id)
    except ApiNoDisponible:
        return pantalla(request, error_de_accion=MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla(request, error_de_accion=error.mensaje)
    return redirect(f"{reverse('parqueaderos:lista')}?hecho=retirado")


def parqueadero_de_residentes(request, parqueadero_id):
    """El parqueadero de residentes con ese id, o `None`. Uno de visitantes no se encuentra: no se asigna."""
    try:
        residentes = api_parqueaderos.listar(request, tipo="residentes")
    except (ApiNoDisponible, ErrorDeApi):
        return None
    return next((p for p in residentes if p["id"] == str(parqueadero_id) and p["tipo"] == "residentes"), None)


@require_http_methods(["GET", "POST"])
def asignar(request, parqueadero_id):
    """«Asignar» o «Reasignar»: elige la vivienda. La API decide si es una cosa o la otra y respeta el tope."""
    if not tiene_permiso(request, "parqueadero.asignar"):
        return redirect("parqueaderos:lista")
    parqueadero = parqueadero_de_residentes(request, parqueadero_id)
    if parqueadero is None:
        return redirect("parqueaderos:lista")
    try:
        unidades, error = api_unidades.listar(request), None
    except ApiNoDisponible:
        unidades, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        unidades, error = [], falla.mensaje
    formulario = AsignarForm(request.POST or None, unidades=unidades)
    if request.method == "POST" and formulario.is_valid():
        try:
            resultado = api_parqueaderos.asignar(request, parqueadero_id, formulario.cleaned_data["unidad"])
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as falla:
            if falla.estado == 404:
                return redirect("parqueaderos:lista")
            errores_de_la_api_al_formulario(formulario, falla)
        else:
            hecho = "reasignado" if resultado.get("reasignada") else "asignado"
            return redirect(f"{reverse('parqueaderos:lista')}?hecho={hecho}")
    return render(request, "parqueaderos/asignar.html", {
        "parqueadero": parqueadero,
        "formulario": formulario,
        "error": error,
        "tope": tope_del_conjunto(request),
    })


@require_POST
def liberar(request, parqueadero_id):
    """«Confirmar liberación»: cierra la asignación vigente. No pregunta por la mora y no la tiene en cuenta."""
    if not tiene_permiso(request, "parqueadero.asignar"):
        return redirect("parqueaderos:lista")
    try:
        api_parqueaderos.liberar(request, parqueadero_id)
    except ApiNoDisponible:
        return pantalla(request, error_de_accion=MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return pantalla(request, error_de_accion=error.mensaje)
    return redirect(f"{reverse('parqueaderos:lista')}?hecho=liberado")


@require_GET
def historial(request, parqueadero_id):
    """Todas las asignaciones del puesto, la más reciente primero, con quién las registró y quién las cerró."""
    if not tiene_permiso(request, "parqueadero.asignar"):
        return redirect("parqueaderos:lista")
    parqueadero = parqueadero_de_residentes(request, parqueadero_id)
    try:
        filas, error = con_fechas(api_parqueaderos.historial(request, parqueadero_id), "vigencia_desde", "vigencia_hasta"), None
    except ApiNoDisponible:
        filas, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        if falla.estado == 404:
            return redirect("parqueaderos:lista")
        filas, error = [], falla.mensaje
    return render(request, "parqueaderos/historial.html", {"parqueadero": parqueadero, "asignaciones": filas, "error": error})


@require_GET
def mios(request):
    """«Mi parqueadero»: los puestos vigentes de la vivienda de quien entra. Sin permiso y sin botones."""
    try:
        puestos, error = con_fechas(api_parqueaderos.mios(request), "desde"), None
    except ApiNoDisponible:
        puestos, error = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as falla:
        puestos, error = [], falla.mensaje
    return render(request, "parqueaderos/mios.html", {"puestos": puestos, "error": error})
