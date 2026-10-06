"""Reglas de reserva del conjunto activo (HU-10): un tablero con cada regla posible, por niveles.

Las reglas alfa son del conjunto; las beta, de un área. Cada una se define una sola vez: lo que
existe se cambia o se quita. El paso de reglas del asistente (HU-03) es este mismo tablero.
"""
from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from apps.areas.views import cargar_areas
from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import reglas as api_reglas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import DIAS_DE_LA_SEMANA, FORMULARIO_POR_TIPO, DiaQueNoAbreForm, iniciales

AVISO_DE_VERSION = "Al guardar se crea una versión nueva; la anterior queda en el historial."
DIAS_QUE_NO_ABRE = "DIAS_QUE_NO_ABRE"


def renglon_para_pantalla(renglon):
    if "dia_semana" in renglon:
        return {"dia": dict(DIAS_DE_LA_SEMANA)[str(renglon["dia_semana"])], "motivo": renglon["motivo"]}
    return {
        "desde": date.fromisoformat(renglon["desde"]),
        "hasta": date.fromisoformat(renglon["hasta"]),
        "motivo": renglon["motivo"],
    }


def con_fechas(regla):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    regla = {**regla, "vigencia_desde": date.fromisoformat(regla["vigencia_desde"])}
    if regla["tipo"] == DIAS_QUE_NO_ABRE:
        regla["renglones"] = [renglon_para_pantalla(renglon) for renglon in regla["parametros"]["renglones"]]
    return regla


def cargar_tablero(request):
    """Cruza el catálogo, las reglas abiertas y las áreas activas: una fila por cada regla posible."""
    try:
        catalogo = api_reglas.catalogo(request)
        reglas = [con_fechas(regla) for regla in api_reglas.listar(request)]
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje
    areas, error = cargar_areas(request)
    definida = {(regla["tipo"], regla["area"]["id"] if regla["area"] else None): regla for regla in reglas}

    def filas(nivel, area_id=None):
        return [
            {**tipo, "regla": definida.get((tipo["tipo"], area_id))} for tipo in catalogo if tipo["nivel"] == nivel
        ]

    tablero = {
        "alfas": filas("alfa"),
        "por_area": [{"area": area, "filas": filas("beta", area["id"])} for area in areas if area["activo"]],
    }
    return tablero, error


def volver_a(request):
    """De vuelta al paso del asistente si de ahí se vino; si no, al tablero (P14)."""
    viene_de = request.POST.get("volver") or request.GET.get("volver")
    return "conjuntos:asistente-reglas" if viene_de == "asistente" else "reglas:lista"


def tipo_del_catalogo(request, tipo):
    """Nombre y descripción del tipo, para encabezar su formulario. Vacío si la API no responde."""
    try:
        return next((entrada for entrada in api_reglas.catalogo(request) if entrada["tipo"] == tipo), {})
    except (ApiNoDisponible, ErrorDeApi):
        return {}


def lista(request, error_de_accion=None, en_asistente=False):
    tablero, error = cargar_tablero(request)
    contexto = {
        "tablero": tablero,
        "error": error_de_accion or error,
        "puede_configurar": tiene_permiso(request, "regla.configurar"),
        "puede_gestionar_areas": tiene_permiso(request, "area.gestionar"),
        "en_asistente": en_asistente,
        "volver": "asistente" if en_asistente else "",
        "paso": 4,
    }
    return render(request, "reglas/lista.html", contexto)


@require_http_methods(["GET", "POST"])
def definir(request, tipo):
    """Define una regla que todavía no existe: sus valores y desde cuándo rige."""
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    if tipo not in FORMULARIO_POR_TIPO:
        raise Http404
    area_id = request.POST.get("area") or request.GET.get("area")
    formulario = FORMULARIO_POR_TIPO[tipo](request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        datos = {
            "tipo": tipo,
            "parametros": formulario.parametros(),
            "vigencia_desde": formulario.cleaned_data["vigencia_desde"].isoformat(),
        }
        if area_id:
            datos["area"] = area_id
        try:
            api_reglas.crear(request, datos)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(volver_a(request))
    contexto = {
        "formulario": formulario,
        "tipo": tipo_del_catalogo(request, tipo),
        "area_id": area_id,
        "volver": request.POST.get("volver") or request.GET.get("volver") or "",
        "paso": 4,
    }
    return render(request, "reglas/parametros.html", contexto)


@require_http_methods(["GET", "POST"])
def editar(request, regla_id):
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    try:
        regla = con_fechas(api_reglas.obtener(request, regla_id))
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    # Los días que no abre se agregan y se quitan de a uno; una regla retirada del catálogo no se edita.
    if regla["tipo"] not in FORMULARIO_POR_TIPO:
        raise Http404
    clase = FORMULARIO_POR_TIPO[regla["tipo"]]
    formulario = clase(request.POST or None, initial=iniciales(regla["tipo"], regla["parametros"]), con_vigencia=False)
    if request.method == "POST" and formulario.is_valid():
        try:
            api_reglas.editar(request, regla_id, formulario.parametros())
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(volver_a(request))
    contexto = {
        "formulario": formulario,
        "regla": regla,
        "tipo": tipo_del_catalogo(request, regla["tipo"]),
        "aviso": AVISO_DE_VERSION,
        "volver": request.POST.get("volver") or request.GET.get("volver") or "",
        "paso": 4,
    }
    return render(request, "reglas/parametros.html", contexto)


@require_POST
def retirar(request, regla_id):
    try:
        api_reglas.retirar(request, regla_id)
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    return redirect(volver_a(request))


def regla_de_dias(request, area_id):
    """La regla abierta de días que no abre de esa área, o None."""
    return next(
        (
            regla for regla in api_reglas.listar(request)
            if regla["tipo"] == DIAS_QUE_NO_ABRE and regla["area"] and regla["area"]["id"] == str(area_id)
        ),
        None,
    )


@require_http_methods(["GET", "POST"])
def agregar_dia(request, area_id):
    """Agrega un día que no abre a un área. La lista completa viaja a la API, que la valida."""
    if not tiene_permiso(request, "regla.configurar"):
        return redirect("reglas:lista")
    formulario = DiaQueNoAbreForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            regla = regla_de_dias(request, area_id)
            if regla is None:
                api_reglas.crear(request, {
                    "area": str(area_id),
                    "tipo": DIAS_QUE_NO_ABRE,
                    "parametros": {"renglones": [formulario.renglon()]},
                    "vigencia_desde": timezone.localdate().isoformat(),
                })
            else:
                renglones = regla["parametros"]["renglones"] + [formulario.renglon()]
                api_reglas.editar(request, regla["id"], {"renglones": renglones})
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(volver_a(request))
    contexto = {
        "formulario": formulario,
        "tipo": tipo_del_catalogo(request, DIAS_QUE_NO_ABRE),
        "volver": request.POST.get("volver") or request.GET.get("volver") or "",
        "paso": 4,
    }
    return render(request, "reglas/dia.html", contexto)


@require_POST
def quitar_dia(request, regla_id, indice):
    """Quita un renglón. Si era el último, retira la regla."""
    try:
        renglones = api_reglas.obtener(request, regla_id)["parametros"]["renglones"]
        restantes = renglones[:indice] + renglones[indice + 1:]
        if restantes:
            api_reglas.editar(request, regla_id, {"renglones": restantes})
        else:
            api_reglas.retirar(request, regla_id)
    except ApiNoDisponible:
        return lista(request, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        return lista(request, error.mensaje)
    return redirect(volver_a(request))
