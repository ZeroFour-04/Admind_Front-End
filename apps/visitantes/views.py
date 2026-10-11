"""La minuta de portería: registrar el ingreso con su parqueadero, ver las visitas y registrar su salida (HU-27, HU-28).

El front muestra lo que la API le dijo hace un momento; la verdad la tiene la base. Por eso, si el
parqueadero que el vigilante veía libre ya no lo está, la API responde 409 y aquí se explica sin perder lo escrito.
"""
from datetime import datetime

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from apps.visitantes.forms import RegistrarVisitanteForm
from cliente_api import parqueaderos as api_parqueaderos
from cliente_api import unidades as api_unidades
from cliente_api import visitantes as api_visitantes
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi


def quien_es(request):
    """`(es_vigilante, puede_ver_historico)`: cada uno ve una pantalla distinta."""
    roles = request.session.get("roles", [])
    es_vigilante = roles == ["Vigilancia"] or (
        not roles and request.session.get("tipo_usuario") == "Vigilancia"
    )
    return es_vigilante, tiene_permiso(request, "visitante.ver_historico")


def cargar(consulta):
    """Llama a la API y devuelve `(datos, error)`: el mensaje para mostrar en lugar de los datos."""
    try:
        return consulta(), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        return [], api_error.mensaje


def parqueaderos_libres(request):
    """Los puestos de visitantes libres ahora mismo. Si no se pueden consultar, no se ofrece ninguno."""
    return cargar(lambda: api_parqueaderos.listar(request, tipo="visitantes", libres=True))


def preparar_formulario(request, datos=None):
    """El formulario de ingreso con los apartamentos y los parqueaderos libres de este momento."""
    unidades, error = cargar(lambda: api_unidades.listar(request))
    libres, error_de_parqueaderos = parqueaderos_libres(request)
    formulario = RegistrarVisitanteForm(datos, unidades=unidades, parqueaderos=libres)
    return formulario, error or error_de_parqueaderos


def con_fechas(visitante):
    """La API manda las fechas como texto; las plantillas las formatean."""
    salida = visitante.get("hora_salida")
    return {
        **visitante,
        "hora_entrada": datetime.fromisoformat(visitante["hora_entrada"]),
        "hora_salida": datetime.fromisoformat(salida) if salida else None,
    }


def pantalla(request, es_vigilante, puede_ver_historico, formulario, error):
    visitantes, error_visitantes = cargar(lambda: api_visitantes.listar(request))
    return render(
        request,
        "visitantes/lista.html",
        {
            "formulario": formulario,
            "error": error or error_visitantes,
            "registrado": request.GET.get("registrado") == "1",
            "salio": request.GET.get("salida") == "1",
            "visitantes": [con_fechas(visitante) for visitante in visitantes],
            "es_vigilante": es_vigilante,
            "puede_ver_historico": puede_ver_historico,
            # Sin libres, el formulario lo dice y la visita se registra sin parqueadero (plan P7).
            "hay_parqueaderos_libres": bool(formulario and len(formulario.fields["parqueadero"].choices) > 1),
        },
    )


@require_http_methods(["GET", "POST"])
def lista(request):
    es_vigilante, puede_ver_historico = quien_es(request)
    if not es_vigilante and not puede_ver_historico:
        return redirect("paneles:inicio")

    formulario, error = None, None
    if es_vigilante:
        formulario, error = preparar_formulario(request, request.POST or None)
        if request.method == "POST" and not tiene_permiso(request, "visitante.registrar"):
            return redirect("paneles:inicio")
        if request.method == "POST" and formulario.is_valid():
            datos = dict(formulario.cleaned_data)
            # `parqueadero` solo viaja si se eligió uno.
            if not datos.get("parqueadero"):
                datos.pop("parqueadero", None)
            try:
                api_visitantes.registrar(request, datos)
            except ApiNoDisponible:
                formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
            except ErrorDeApi as api_error:
                errores_de_la_api_al_formulario(formulario, api_error)
                if api_error.estado == 409:
                    # Otra visita se llevó el puesto: se vuelven a pedir los libres y lo escrito se conserva.
                    libres, _ = parqueaderos_libres(request)
                    formulario.ofrecer_parqueaderos(libres)
            else:
                return redirect(f"{reverse('visitantes:lista')}?registrado=1")

    return pantalla(request, es_vigilante, puede_ver_historico, formulario, error)


@require_POST
def salida(request, visitante_id):
    """«Registrar salida», ya confirmada con el nombre, la placa y el parqueadero que se libera.

    Un 409 («ya salió») se muestra como aviso y no rompe la pantalla.
    """
    es_vigilante, puede_ver_historico = quien_es(request)
    if not es_vigilante or not tiene_permiso(request, "visitante.registrar"):
        return redirect("paneles:inicio")
    try:
        api_visitantes.registrar_salida(request, visitante_id)
    except ApiNoDisponible:
        error = MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        error = api_error.mensaje
    else:
        return redirect(f"{reverse('visitantes:lista')}?salida=1")
    formulario, error_de_carga = preparar_formulario(request)
    return pantalla(request, es_vigilante, puede_ver_historico, formulario, error or error_de_carga)
