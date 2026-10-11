"""Unidades del conjunto activo y sus vínculos (HU-08): propietarios, arrendatarios y su histórico."""
from datetime import date

from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from cliente_api import cuentas as api_cuentas
from cliente_api import unidades as api_unidades
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi

from .forms import CerrarVinculoForm, NuevoResidenteForm, UnidadForm, VinculoForm


def con_fechas(vinculo):
    """La API manda las fechas como texto ISO; las plantillas las formatean como fecha."""
    fechas = {
        campo: date.fromisoformat(vinculo[campo]) for campo in ("vigencia_desde", "vigencia_hasta") if vinculo.get(campo)
    }
    return {**vinculo, **fechas}


PLURAL_DE_TIPO = {"apartamento": "apartamentos", "casa": "casas"}


def cargar_unidades(request):
    """(unidades, error): las viviendas del conjunto activo, o ([], el motivo) si la API no las entrega."""
    try:
        return api_unidades.listar(request), None
    except ApiNoDisponible:
        return [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        return [], api_error.mensaje


def para_el_buscador(unidades, puede_gestionar):
    """Lo que el buscador de la página necesita de cada vivienda. Viaja como JSON, no se pinta fila por fila."""
    filas = []
    for unidad in unidades:
        agrupacion = unidad.get("agrupacion") or {}
        filas.append(
            {
                "id": unidad["id"],
                "nombre": unidad["nombre"],
                "agrupacion": agrupacion.get("nombre", ""),
                "tipo": unidad.get("tipo", "apartamento"),
                "numero": unidad.get("numero", ""),
                "vinculos": unidad.get("vinculos_vigentes", 0),
                "personas": unidad.get("personas", []),
                "url": reverse("unidades:detalle", args=[unidad["id"]]) if puede_gestionar else "",
            }
        )
    return filas


def recuadros_de_agrupaciones(unidades):
    """Un recuadro por agrupación, en el orden de la API, y «Sin agrupar» al final si hay viviendas sueltas."""
    recuadros = {}
    for unidad in unidades:
        agrupacion = unidad.get("agrupacion")
        clave = agrupacion["id"] if agrupacion else ""
        recuadro = recuadros.setdefault(
            clave,
            {
                "nombre": agrupacion["nombre"] if agrupacion else "Sin agrupar",
                "sin_agrupar": agrupacion is None,
                "url": reverse("unidades:agrupacion", args=[clave]) if agrupacion else reverse("unidades:sin-agrupar"),
                "total": 0,
                "sin_vinculos": 0,
                "tipos": set(),
            },
        )
        recuadro["total"] += 1
        recuadro["sin_vinculos"] += 0 if unidad.get("vinculos_vigentes") else 1
        recuadro["tipos"].add(unidad.get("tipo", "apartamento"))
    for recuadro in recuadros.values():
        tipos = recuadro.pop("tipos")
        recuadro["viviendas"] = PLURAL_DE_TIPO[tipos.pop()] if len(tipos) == 1 else "viviendas"
    return sorted(recuadros.values(), key=lambda recuadro: recuadro["sin_agrupar"])


@require_http_methods(["GET", "POST"])
def lista(request):
    puede_gestionar = tiene_permiso(request, "vinculo.gestionar")
    formulario = UnidadForm(request.POST or None)
    if request.method == "POST" and puede_gestionar and formulario.is_valid():
        try:
            unidad = api_unidades.crear(request, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("unidades:detalle", unidad_id=unidad["id"])

    unidades, error = cargar_unidades(request)
    recuadros = recuadros_de_agrupaciones(unidades)
    contexto = {
        "unidades": para_el_buscador(unidades, puede_gestionar),
        "recuadros": recuadros,
        # Si ninguna vivienda tiene agrupación, un solo recuadro «Sin agrupar» no ayuda: va la tabla directa.
        "hay_agrupaciones": any(unidad.get("agrupacion") for unidad in unidades),
        "error": error,
        "formulario": formulario,
        "puede_gestionar": puede_gestionar,
    }
    return render(request, "unidades/lista.html", contexto)


def viviendas_de_agrupacion(request, agrupacion_id=None):
    """Las viviendas de una agrupación (o las que no tienen), con su buscador."""
    puede_gestionar = tiene_permiso(request, "vinculo.gestionar")
    unidades, error = cargar_unidades(request)
    buscada = str(agrupacion_id) if agrupacion_id else ""
    propias = [u for u in unidades if str((u.get("agrupacion") or {}).get("id", "")) == buscada]
    if not propias and not error:
        raise Http404
    if propias and buscada:
        nombre = propias[0]["agrupacion"]["nombre"]
    else:
        nombre = "Sin agrupar" if not agrupacion_id else "Unidades"
    contexto = {
        "nombre": nombre,
        "unidades": para_el_buscador(propias, puede_gestionar),
        "error": error,
        "puede_gestionar": puede_gestionar,
    }
    return render(request, "unidades/agrupacion.html", contexto)


# El residente recién creado pasa a la pantalla por la sesión, no por la URL: se usa una sola vez.
CLAVE_RESIDENTE_CREADO = "residente_creado"
# Los campos del alta no comparten id con el formulario del vínculo, que está en la misma página.
AUTO_ID_RESIDENTE = "residente_%s"
# Desde la vivienda solo se crean residentes: el rol lo pone la vista, el formulario ni lo tiene.
ROL_DEL_ALTA = "residente"


def usuarios_del_conjunto(request):
    """Las cuentas con rol en el conjunto activo; sin ellas (la API no responde) el selector queda vacío."""
    try:
        return api_cuentas.listar_usuarios(request)
    except (ApiNoDisponible, ErrorDeApi):
        return []


def personas_de(usuarios):
    """[(persona_id, nombre)]: las opciones que acepta el formulario del vínculo."""
    return [(usuario["persona"], usuario["nombre"]) for usuario in usuarios]


def para_el_selector(usuarios):
    """Lo que el buscador de personas necesita de cada cuenta. El documento va para poder buscar por él; la
    pantalla no lo imprime."""
    return [
        {
            "id": usuario["persona"],
            "nombre": usuario["nombre"],
            "correo": usuario.get("correo", ""),
            "documento": usuario.get("documento", ""),
        }
        for usuario in usuarios
    ]


@require_http_methods(["GET", "POST"])
def detalle(request, unidad_id):
    if not tiene_permiso(request, "vinculo.gestionar"):
        return redirect("unidades:lista")
    usuarios = usuarios_del_conjunto(request)
    # Quien acaba de crear a un residente lo encuentra ya elegido en el formulario del vínculo.
    creado = request.session.pop(CLAVE_RESIDENTE_CREADO, None) if request.method == "GET" else None
    inicial = {"persona": creado["persona"]} if creado and creado["persona"] else {}
    formulario = VinculoForm(request.POST or None, initial=inicial, personas=personas_de(usuarios))
    if request.method == "POST" and formulario.is_valid():
        try:
            api_unidades.registrar_vinculo(request, unidad_id, formulario.cleaned_data)
        except ApiNoDisponible:
            formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(formulario, error)
        else:
            return redirect("unidades:detalle", unidad_id=unidad_id)
    return pantalla_de_detalle(request, unidad_id, formulario, usuarios, creado=creado)


def pantalla_de_detalle(request, unidad_id, formulario, usuarios, error_de_accion=None, residente=None, creado=None):
    try:
        unidad, error = api_unidades.obtener(request, unidad_id), None
    except ApiNoDisponible:
        unidad, error = None, MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        unidad, error = None, api_error.mensaje
    if unidad:
        unidad = {
            **unidad,
            "vigentes": [con_fechas(v) for v in unidad["vigentes"]],
            "historicos": [con_fechas(v) for v in unidad["historicos"]],
        }
    contexto = {
        "unidad": unidad,
        "error": error_de_accion or error,
        "formulario": formulario,
        "cierre": CerrarVinculoForm(),
        "personas": para_el_selector(usuarios),
        # Crear a alguien es de quien gestiona usuarios; el vínculo, de quien gestiona vínculos.
        "puede_crear_residente": tiene_permiso(request, "usuario.gestionar"),
        "residente": residente or NuevoResidenteForm(auto_id=AUTO_ID_RESIDENTE),
        # Con errores en el alta, la pantalla vuelve con el modal abierto.
        "abrir_alta": residente is not None,
        "residente_creado": creado["nombre"] if creado else None,
    }
    return render(request, "unidades/detalle.html", contexto)


@require_POST
def crear_residente(request, unidad_id):
    """Crea la cuenta de un residente desde la vivienda y lo deja elegido en el formulario del vínculo."""
    if not (tiene_permiso(request, "vinculo.gestionar") and tiene_permiso(request, "usuario.gestionar")):
        return redirect("unidades:lista")
    residente = NuevoResidenteForm(request.POST, auto_id=AUTO_ID_RESIDENTE)
    usuarios = usuarios_del_conjunto(request)
    if residente.is_valid():
        datos = residente.cleaned_data
        try:
            nuevo = api_cuentas.crear_usuario(request, {**datos, "rol": ROL_DEL_ALTA})
        except ApiNoDisponible:
            residente.add_error(None, MENSAJE_API_NO_DISPONIBLE)
        except ErrorDeApi as error:
            errores_de_la_api_al_formulario(residente, error)
        else:
            try:
                persona = api_cuentas.obtener_usuario(request, nuevo["id"])["persona"]
            except (ApiNoDisponible, ErrorDeApi):
                persona = None  # quedó creado: aparece en la lista, solo que no llega elegido
            request.session[CLAVE_RESIDENTE_CREADO] = {
                "persona": persona,
                "nombre": f"{datos['nombres']} {datos['apellidos']}",
            }
            return redirect("unidades:detalle", unidad_id=unidad_id)
    formulario = VinculoForm(personas=personas_de(usuarios))
    return pantalla_de_detalle(request, unidad_id, formulario, usuarios, residente=residente)


@require_POST
def cerrar_vinculo(request, unidad_id, vinculo_id):
    cierre = CerrarVinculoForm(request.POST)
    usuarios = usuarios_del_conjunto(request)
    formulario = VinculoForm(personas=personas_de(usuarios))
    if not cierre.is_valid():
        return pantalla_de_detalle(
            request, unidad_id, formulario, usuarios, "Escribe una fecha válida para cerrar el vínculo."
        )
    try:
        api_unidades.cerrar_vinculo(request, unidad_id, vinculo_id, cierre.datos_para_api())
    except ApiNoDisponible:
        return pantalla_de_detalle(request, unidad_id, formulario, usuarios, MENSAJE_API_NO_DISPONIBLE)
    except ErrorDeApi as error:
        mensaje = " ".join(sum(error.campos.values(), [])) or error.mensaje
        return pantalla_de_detalle(request, unidad_id, formulario, usuarios, mensaje)
    return redirect("unidades:detalle", unidad_id=unidad_id)
