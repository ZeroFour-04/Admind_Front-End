"""La pantalla Solicitudes. Gestión ve el dashboard con una pestaña por tipo; el residente, su historial.

Las tres solicitudes no son una sola cosa: cada pestaña le pide las filas a su módulo. Aquí solo se
preparan para mostrarse (nombre del estado, pastilla, antigüedad). Qué puede hacer cada rol lo
resuelve la API.
"""
from datetime import date, datetime, time
from urllib.parse import urlencode

from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format

from apps.casos.presentacion import ESTADOS_VISIBLES, PRIORIDADES_VISIBLES, caso_para_mostrar
from apps.cuentas.sesion import tiene_permiso
from cliente_api import casos as api_casos
from cliente_api import reservas as api_reservas
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

ESTADO_PARA_RESIDENTE = {
    "APARTADA": "En progreso",
    "RESERVADA": "Aceptado",
    "RECHAZADA": "Rechazado",
    "EN_SOLICITUD": "En progreso",
    "CANCELADA": "Cancelada",
    "EXPIRADA": "Expirada",
    "LIBERADA": "Liberada",
}

TITULO_DEL_DASHBOARD = "Dashboard de Gestión de Reservas"
PESTANAS = ("reservas", "casos", "citas")

# Cómo se ve en la tabla cada estado de una reserva: siempre con texto, nunca solo con color.
ESTADO_DE_RESERVA = {
    "APARTADA": ("En revisión", "am-pastilla--tramite"),
    "RESERVADA": ("Aprobada", "am-pastilla--confirmado"),
    "RECHAZADA": ("Rechazada", "am-pastilla--error"),
    "CANCELADA": ("Cancelada", "am-pastilla--neutro"),
}
# Una reserva aprobada cuya franja ya terminó. La API lo dice con `completada`; no es un estado guardado.
RESERVA_COMPLETADA = ("Completada", "am-pastilla--neutro")

FILTROS = {
    "reservas": (("pendientes", "Pendientes"), ("todas", "Todas")),
    "casos": (("abiertos", "Abiertos"), ("todos", "Todos")),
}
ORDENES_DE_CASOS = (("prioridad", "Por prioridad"), ("antiguedad", "Por antigüedad"))

# Los filtros de cada pestaña (HU-22). Viajan en la URL; la API los valida y filtra, el front no interpreta nada.
FILTROS_DE_URL = {
    "reservas": ("estado", "area", "vivienda", "desde", "hasta", "solicitante"),
    "casos": ("estado", "prioridad", "desde", "hasta", "solicitante"),
}
ESTADOS_DE_RESERVA_FILTRABLES = ("APARTADA", "RESERVADA", "RECHAZADA")


def codigo(prefijo, identificador):
    """El ID que se lee en la tabla: `RES-3C4D5E`. Sale del identificador real; no es un consecutivo."""
    return f"{prefijo}-{str(identificador)[:6].upper()}"


def hace_cuanto(momento, hoy):
    """«hoy», «hace 1 día», «hace 5 días»: cuánto lleva esperando una solicitud."""
    dias = (hoy - timezone.localtime(momento).date()).days
    if dias <= 0:
        return "hoy"
    return "hace 1 día" if dias == 1 else f"hace {dias} días"


def fila_de_reserva(solicitud, hoy):
    estado, clase = RESERVA_COMPLETADA if solicitud.get("completada") else ESTADO_DE_RESERVA.get(
        solicitud["estado"], (solicitud["estado_nombre"], "am-pastilla--neutro")
    )
    enviada = datetime.fromisoformat(solicitud["enviada_en"] or solicitud["creada_en"])
    zona = reverse("reservas:solicitudes-area", kwargs={"area_id": solicitud["area"]["id"]})
    fecha = date.fromisoformat(solicitud["fecha"])
    return {
        "codigo": codigo("RES", solicitud["id"]),
        "url": f"{zona}#solicitud-{solicitud['id']}",
        "zona": solicitud["area"]["nombre"],
        # Con el día de la semana en letras: es lo que atrapa una fecha mal elegida.
        "dia": date_format(fecha, r"l j \d\e F").lower(),
        "hora_inicio": time.fromisoformat(solicitud["hora_inicio"]),
        "hora_fin": time.fromisoformat(solicitud["hora_fin"]),
        "area_id": solicitud["area"]["id"],
        "unidad_id": solicitud["unidad"]["id"] if solicitud.get("unidad") else "",
        "estado": estado,
        "estado_clase": clase,
        "pendiente": solicitud["estado"] == "APARTADA",
        "residente": solicitud["residente"]["nombre"],
        "vivienda": solicitud["unidad"]["nombre"] if solicitud.get("unidad") else "",
        "enviada": enviada,
        "antiguedad": hace_cuanto(enviada, hoy),
        "con_pago": solicitud["estado"] in ("APARTADA", "RESERVADA"),
        "pago_declarado": solicitud["pago"]["declarado"],
    }


def fila_de_caso(caso, hoy):
    caso = caso_para_mostrar(caso)
    return {
        **caso,
        "codigo": codigo("CAS", caso["id"]),
        "url": reverse("casos:detalle", kwargs={"caso_id": caso["id"]}),
        "antiguedad": hace_cuanto(caso["creado_en"], hoy),
    }


def pedir_filas(pedir, preparar, hoy):
    """Las filas de una pestaña ya listas para la tabla, el error para mostrar y los errores de los filtros.

    Un 400 es un filtro que no sirve (una fecha mal escrita): se muestra como error del formulario y no
    como una tabla vacía, que diría que no hay nada.
    """
    try:
        return [preparar(fila, hoy) for fila in pedir()], None, []
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE, []
    except ErrorDeApi as error:
        if error.estado == 400:
            return [], None, [mensaje for mensajes in error.campos.values() for mensaje in mensajes] or [error.mensaje]
        return [], error.mensaje, []


def filtros_de(request, pestana):
    """Los filtros de la URL que existen para esa pestaña, sin los vacíos."""
    leidos = {nombre: request.GET.get(nombre, "").strip() for nombre in FILTROS_DE_URL.get(pestana, ())}
    return {nombre: valor for nombre, valor in leidos.items() if valor}


def opciones_unicas(filas, id_de, nombre_de):
    """Los pares (id, nombre) distintos de las filas, por nombre."""
    vistos = {id_de(fila): nombre_de(fila) for fila in filas if id_de(fila)}
    return sorted(vistos.items(), key=lambda par: par[1])


def campos_del_formulario(pestana, filtros, sin_filtrar):
    """Los campos del formulario de filtros de la pestaña, con lo que ya eligió quien lo llena.

    Las zonas y viviendas salen de las filas sin filtrar: no hace falta otro permiso ni otra petición.
    """
    def campo(nombre, etiqueta, tipo, opciones=()):
        return {"nombre": nombre, "etiqueta": etiqueta, "tipo": tipo, "valor": filtros.get(nombre, ""), "opciones": opciones}

    if pestana == "reservas":
        estados = [(clave, ESTADO_DE_RESERVA[clave][0]) for clave in ESTADOS_DE_RESERVA_FILTRABLES]
        zonas = opciones_unicas(sin_filtrar, lambda fila: fila["area_id"], lambda fila: fila["zona"])
        viviendas = opciones_unicas(sin_filtrar, lambda fila: fila["unidad_id"], lambda fila: fila["vivienda"])
        return [
            campo("estado", "Estado", "select", estados),
            campo("area", "Zona", "select", zonas),
            campo("vivienda", "Vivienda", "select", viviendas),
            campo("solicitante", "Residente", "text"),
            campo("desde", "Enviada desde", "date"),
            campo("hasta", "Enviada hasta", "date"),
        ]
    return [
        campo("estado", "Estado", "select", [(clave, nombre) for clave, (nombre, _) in ESTADOS_VISIBLES.items()]),
        campo("prioridad", "Prioridad", "select", [(clave, nombre) for clave, (nombre, _) in PRIORIDADES_VISIBLES.items()]),
        campo("solicitante", "Residente", "text"),
        campo("desde", "Creado desde", "date"),
        campo("hasta", "Creado hasta", "date"),
    ]


def url_del_dashboard(pestana, **consulta):
    consulta = {clave: valor for clave, valor in consulta.items() if valor}
    return f"{reverse('triage:bandeja')}?{urlencode({'pestana': pestana, **consulta})}"


def elegido(request, nombre, opciones):
    """El valor de un filtro de la URL si es uno de los que existen; si no, el primero."""
    valor = request.GET.get(nombre)
    return valor if valor in dict(opciones) else opciones[0][0]


def dashboard(request):
    """Una pestaña por tipo de solicitud, cada una con su tabla. La pestaña y los filtros viajan en la URL."""
    hoy = timezone.localdate()
    ve_casos = tiene_permiso(request, "caso.ver_todos")
    disponibles = [pestana for pestana in PESTANAS if pestana != "casos" or ve_casos]
    pestana = request.GET.get("pestana")
    if pestana not in disponibles:
        pestana = "reservas"
    orden = elegido(request, "orden", ORDENES_DE_CASOS)

    filtros = filtros_de(request, pestana)
    # Las dos listas sin filtrar se piden siempre: las cuentas de las pestañas y las opciones de zona y
    # vivienda salen de ahí. La pestaña activa pide además la suya con los filtros, si hay.
    reservas, error_de_reservas, _ = pedir_filas(
        lambda: api_reservas.solicitudes_para_bandeja(request), fila_de_reserva, hoy
    )
    casos, error_de_casos = [], None
    if ve_casos:
        casos, error_de_casos, _ = pedir_filas(lambda: api_casos.listar(request, orden=orden), fila_de_caso, hoy)
    pendientes = {
        "reservas": sum(fila["pendiente"] for fila in reservas),
        "casos": sum(fila["abierto"] for fila in casos),
    }

    sin_filtrar = reservas
    errores_de_filtros = []
    if filtros and pestana == "reservas":
        reservas, error_de_reservas, errores_de_filtros = pedir_filas(
            lambda: api_reservas.solicitudes_para_bandeja(request, **filtros), fila_de_reserva, hoy
        )
    elif filtros and pestana == "casos":
        casos, error_de_casos, errores_de_filtros = pedir_filas(
            lambda: api_casos.listar(request, orden=orden, **filtros), fila_de_caso, hoy
        )

    filas, error, ver, filtros_de_vista = [], None, None, []
    # Con un estado elegido «Pendientes / Todas» desaparece: se contradirían.
    if pestana in FILTROS and "estado" not in filtros:
        ver = elegido(request, "ver", FILTROS[pestana])
        extra = {"orden": orden} if pestana == "casos" else {}
        filtros_de_vista = [
            {
                "nombre": nombre,
                "activo": clave == ver,
                "url": url_del_dashboard(pestana, ver=clave, **extra, **filtros),
            }
            for clave, nombre in FILTROS[pestana]
        ]
    if pestana == "reservas":
        error = error_de_reservas
        filas = [fila for fila in reservas if ver in (None, "todas") or fila["pendiente"]]
    elif pestana == "casos":
        error = error_de_casos
        filas = [fila for fila in casos if ver in (None, "todos") or fila["abierto"]]

    nombres = {"reservas": "Reservas", "casos": "Casos", "citas": "Citas"}
    ordenes = []
    if pestana == "casos":
        ordenes = [
            {"nombre": nombre, "activo": clave == orden, "url": url_del_dashboard("casos", ver=ver, orden=clave, **filtros)}
            for clave, nombre in ORDENES_DE_CASOS
        ]
    return render(request, "triage/bandeja.html", {
        "dashboard": True,
        "titulo": TITULO_DEL_DASHBOARD,
        "pestana": pestana,
        "pestanas": [
            {
                "nombre": nombres[clave],
                "activa": clave == pestana,
                "pendientes": pendientes.get(clave),
                "url": url_del_dashboard(clave),
            }
            for clave in disponibles
        ],
        "filtros": filtros_de_vista,
        "formulario": campos_del_formulario(pestana, filtros, sin_filtrar) if pestana in FILTROS_DE_URL else [],
        "hay_filtros": bool(filtros),
        "errores_de_filtros": errores_de_filtros,
        "quitar_filtros": url_del_dashboard(pestana, ver=ver, orden=orden if pestana == "casos" else None),
        "ordenes": ordenes,
        "orden": orden,
        "ver": ver,
        "filas": filas,
        "error": error,
    })


def bandeja(request):
    """Quien entra al dashboard (`solicitud.bandeja_ver`) ve las pestañas; el residente, su historial."""
    if tiene_permiso(request, "solicitud.bandeja_ver"):
        return dashboard(request)

    es_residente = tiene_permiso(request, "reserva.solicitar")
    solicitudes, error = [], None
    if es_residente:
        try:
            solicitudes = api_reservas.mis_solicitudes(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje

    solicitudes = [
        {
            **solicitud,
            "estado_visible": ESTADO_PARA_RESIDENTE.get(solicitud["estado"], solicitud["estado_nombre"]),
        }
        for solicitud in solicitudes
    ]
    return render(request, "triage/bandeja.html", {
        "dashboard": False,
        "titulo": "Solicitudes",
        "solicitudes": solicitudes,
        "error": error,
        "es_residente": es_residente,
    })
