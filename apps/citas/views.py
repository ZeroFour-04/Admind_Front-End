import calendar
from datetime import date
from urllib.parse import urlencode

from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import citas as api_citas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import DIAS, HorarioCitasForm


def formulario_con_horario(datos):
    inicial = {"modo": "por_dia"}
    por_dia = {dia["dia"]: dia for dia in datos} if isinstance(datos, list) else {}
    for dia, _ in DIAS:
        configuracion = por_dia.get(dia)
        if configuracion:
            inicial[f"dia_{dia}_activo"] = configuracion["activo"]
            inicial[f"dia_{dia}_hora_inicio"] = configuracion["hora_inicio"]
            inicial[f"dia_{dia}_hora_fin"] = configuracion["hora_fin"]
            inicial[f"dia_{dia}_descanso_inicio"] = configuracion["descanso_inicio"]
            inicial[f"dia_{dia}_descanso_fin"] = configuracion["descanso_fin"]
    return HorarioCitasForm(initial=inicial)


def cargar_horario(request):
    try:
        respuesta = api_citas.horario(request)
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje
    return respuesta, None


def pagina(request, formulario=None, error=None):
    horario_guardado, error_de_carga = cargar_horario(request)
    dias_guardados = horario_guardado["dias"] if horario_guardado else []
    formulario = formulario or formulario_con_horario(dias_guardados)
    dias_formulario = [
        {
            "nombre": nombre,
            "activo": formulario[f"dia_{dia}_activo"],
            "campos": [
                formulario[f"dia_{dia}_{campo}"]
                for campo in ("hora_inicio", "hora_fin", "descanso_inicio", "descanso_fin")
            ],
        }
        for dia, nombre in DIAS
    ]
    dias_resumen = [
        {
            "nombre": nombre,
            "configuracion": next((dia for dia in dias_guardados if dia["dia"] == numero), None),
        }
        for numero, nombre in DIAS
    ]
    tiene_horario = bool(horario_guardado and horario_guardado["id"])
    editando = bool(formulario.is_bound or request.GET.get("editar") == "1" or not tiene_horario)
    return render(request, "citas/horario.html", {
        "formulario": formulario,
        "error": error or error_de_carga,
        "guardado": request.GET.get("guardado") == "1",
        "dias": dias_formulario,
        "dias_resumen": dias_resumen,
        "tiene_horario": tiene_horario,
        "editando": editando,
    })


@require_http_methods(["GET", "POST"])
def horario(request):
    if not tiene_permiso(request, "cita.gestionar_horario"):
        return redirect("paneles:inicio")
    if request.method == "GET":
        return pagina(request)

    formulario = HorarioCitasForm(request.POST)
    if formulario.is_valid():
        try:
            api_citas.guardar_horario(request, formulario.horario_para_api())
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect(f"{reverse('citas:horario')}?guardado=1")
    return pagina(request, formulario)


DIAS_SEMANA = (
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
)


def _mes_pedido(texto, hoy):
    try:
        anio, mes = (int(parte) for parte in texto.split("-"))
        return date(anio, mes, 1)
    except (AttributeError, ValueError):
        return hoy.replace(day=1)


def _dia_pedido(texto, mes):
    try:
        dia = date.fromisoformat(texto)
    except (TypeError, ValueError):
        return None
    return dia if (dia.year, dia.month) == (mes.year, mes.month) else None


def _mes_vecino(mes, paso):
    indice = mes.year * 12 + mes.month - 1 + paso
    return date(indice // 12, indice % 12 + 1, 1)


def _horario_resumen(datos):
    dias = {dia["dia"]: dia for dia in datos.get("dias", [])}
    return [
        {"nombre": nombre, "configuracion": dias.get(numero)}
        for numero, nombre in enumerate(DIAS_SEMANA)
    ]


def _agenda_datos(request, dia):
    try:
        return api_citas.agenda(request, dia.isoformat() if dia else None), None
    except ApiNoDisponible:
        return None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as error:
        return None, error.mensaje


@require_http_methods(["GET", "POST"])
def agenda(request):
    if not tiene_permiso(request, "cita.agendar_propia"):
        return redirect("paneles:inicio")

    hoy = timezone.localdate()
    mes = _mes_pedido(request.GET.get("mes"), hoy)
    dia = _dia_pedido(request.GET.get("dia"), mes)
    if dia and dia < hoy:
        dia = None

    if request.method == "POST":
        fecha = request.POST.get("fecha", "")
        try:
            cita = api_citas.agendar(request, {
                "fecha": fecha,
                "hora_inicio": request.POST.get("hora_inicio", ""),
            })
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as error_api:
            error = error_api.mensaje
        else:
            cita_fecha = date.fromisoformat(cita["fecha"])
            consulta = urlencode({
                "mes": cita_fecha.strftime("%Y-%m"),
                "dia": cita_fecha.isoformat(),
                "agendada": "1",
            })
            return redirect(f"{reverse('citas:agenda')}?{consulta}")
    else:
        error = None

    datos, error_de_carga = _agenda_datos(request, dia)
    datos = datos or {"horario": {"dias": []}, "franjas": [], "cita_propia": None}
    franjas = []
    for franja in datos["franjas"]:
        franjas.append({
            **franja,
            "texto": {
                "libre": "Disponible",
                "ocupada": "Ocupada",
                "pasada": "Ya pasó",
                "propia": "Tuya",
            }[franja["estado"]],
            "clase": {
                "libre": "am-pastilla--confirmado",
                "ocupada": "am-pastilla--error",
                "pasada": "am-pastilla--neutro",
                "propia": "am-pastilla--info",
            }[franja["estado"]],
        })
    return render(request, "citas/agenda.html", {
        "hoy": hoy,
        "mes": mes,
        "semanas": calendar.Calendar(firstweekday=calendar.MONDAY).monthdatescalendar(mes.year, mes.month),
        "dia_elegido": dia,
        "mes_anterior": _mes_vecino(mes, -1),
        "mes_siguiente": _mes_vecino(mes, 1),
        "horario": _horario_resumen(datos["horario"]),
        "cita_propia": datos["cita_propia"],
        "franjas": franjas,
        "error": error or error_de_carga,
        "agendada": request.GET.get("agendada") == "1",
    })
