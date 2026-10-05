from datetime import datetime

from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.cuentas.sesion import tiene_permiso
from apps.cuentas.views import errores_de_la_api_al_formulario
from apps.visitantes.forms import RegistrarVisitanteForm
from cliente_api import unidades as api_unidades
from cliente_api import visitantes as api_visitantes
from cliente_api.http import MENSAJE_API_NO_DISPONIBLE, ApiNoDisponible, ErrorDeApi


@require_http_methods(["GET", "POST"])
def lista(request):
    roles = request.session.get("roles", [])
    es_vigilante = roles == ["Vigilancia"] or (
        not roles and request.session.get("tipo_usuario") == "Vigilancia"
    )
    puede_ver_historico = tiene_permiso(request, "visitante.ver_historico")
    if not es_vigilante and not puede_ver_historico:
        return redirect("paneles:inicio")

    unidades = []
    formulario = None
    error = None
    if es_vigilante:
        try:
            unidades = api_unidades.listar(request)
        except ApiNoDisponible:
            error = MENSAJE_API_NO_DISPONIBLE
        except ErrorDeApi as api_error:
            error = api_error.mensaje

        formulario = RegistrarVisitanteForm(request.POST or None, unidades=unidades)
        if request.method == "POST" and not tiene_permiso(request, "visitante.registrar"):
            return redirect("paneles:inicio")
        if request.method == "POST" and formulario.is_valid():
            try:
                api_visitantes.registrar(request, formulario.cleaned_data)
            except ApiNoDisponible:
                formulario.add_error(None, MENSAJE_API_NO_DISPONIBLE)
            except ErrorDeApi as api_error:
                errores_de_la_api_al_formulario(formulario, api_error)
            else:
                return redirect(f"{reverse('visitantes:lista')}?registrado=1")

    try:
        visitantes = api_visitantes.listar(request)
        error_visitantes = None
    except ApiNoDisponible:
        visitantes, error_visitantes = [], MENSAJE_API_NO_DISPONIBLE
    except ErrorDeApi as api_error:
        visitantes, error_visitantes = [], api_error.mensaje

    visitantes = [
        {**visitante, "hora_entrada": datetime.fromisoformat(visitante["hora_entrada"])}
        for visitante in visitantes
    ]

    return render(
        request,
        "visitantes/lista.html",
        {
            "formulario": formulario,
            "unidades": unidades,
            "error": error or error_visitantes,
            "registrado": request.GET.get("registrado") == "1",
            "visitantes": visitantes,
            "es_vigilante": es_vigilante,
            "puede_ver_historico": puede_ver_historico,
        },
    )
