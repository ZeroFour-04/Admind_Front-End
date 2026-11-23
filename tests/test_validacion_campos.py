"""Formato de los campos de personas: documento, nombres, teléfono, cédula y placa (apps/usuarios/validacion.py)."""
import pytest
from django.template.loader import render_to_string

from apps.ingresos.forms import BuscarResidenteForm
from apps.usuarios.forms import BuscarPersonaForm, UsuarioForm
from apps.visitantes.forms import RegistrarVisitanteForm

USUARIO_VALIDO = {
    "rol": "residente",
    "tipo_documento": "CC",
    "numero_documento": "1023456789",
    "nombres": "María José",
    "apellidos": "Núñez-O'Neil",
    "telefono": "3001234567",
    "correo": "maria@correo.com",
    "contrasena": "clave-segura-1",
    "confirmar_contrasena": "clave-segura-1",
}


def errores_de_usuario(**cambios):
    formulario = UsuarioForm({**USUARIO_VALIDO, **cambios})
    formulario.is_valid()
    return formulario.errors


def test_un_usuario_con_datos_validos_pasa():
    assert errores_de_usuario() == {}


@pytest.mark.parametrize("numero", ["10234AB789", "1.023.456", "1023 456", "1023-456"])
def test_la_cedula_no_acepta_letras_ni_simbolos(numero):
    errores = errores_de_usuario(numero_documento=numero)
    assert errores["numero_documento"] == ["En este campo solo se aceptan números, sin puntos ni espacios."]


@pytest.mark.parametrize("numero", ["1234", "123456789012"])
def test_el_documento_tiene_entre_5_y_11_caracteres(numero):
    errores = errores_de_usuario(numero_documento=numero)
    assert errores["numero_documento"] == ["El documento debe tener entre 5 y 11 caracteres."]


def test_el_pasaporte_si_acepta_letras_pero_no_simbolos():
    assert errores_de_usuario(tipo_documento="PAS", numero_documento="AB123456") == {}
    assert "numero_documento" in errores_de_usuario(tipo_documento="PAS", numero_documento="AB-123456")


@pytest.mark.parametrize("campo", ["nombres", "apellidos"])
def test_nombres_y_apellidos_solo_aceptan_letras(campo):
    errores = errores_de_usuario(**{campo: "Ana2"})
    assert errores[campo] == ["En este campo solo se aceptan letras y espacios."]


def test_el_telefono_no_acepta_letras():
    assert "telefono" in errores_de_usuario(telefono="300abc4567")


def test_buscar_persona_tambien_valida_el_documento():
    formulario = BuscarPersonaForm({"tipo_documento": "CC", "numero_documento": "abc12345"})
    assert not formulario.is_valid() and "numero_documento" in formulario.errors


def test_el_ingreso_acepta_letras_y_numeros_pero_no_puntos():
    datos = {"area": "", "acompanantes": "0"}
    assert "numero_documento" not in BuscarResidenteForm({**datos, "numero_documento": "AB123456"}).errors
    assert "numero_documento" in BuscarResidenteForm({**datos, "numero_documento": "1.000.001"}).errors


def test_el_visitante_valida_cedula_nombre_y_placa():
    formulario = RegistrarVisitanteForm(
        {
            "cedula": "12345abc",
            "nombre": "Pedro 3",
            "ingresa_con_vehiculo": "si",
            "placa_vehiculo": "ABC-123",
            "tipo_vehiculo": "Auto",
            "apartamento_visitado": "",
        }
    )
    formulario.is_valid()
    assert formulario.errors["cedula"] == ["En este campo solo se aceptan números, sin puntos ni espacios."]
    assert formulario.errors["nombre"] == ["En este campo solo se aceptan letras y espacios."]
    assert "placa_vehiculo" in formulario.errors


def test_el_campo_lleva_al_navegador_la_regla_y_el_largo():
    formulario = UsuarioForm()
    documento = render_to_string("componentes/campo.html", {"campo": formulario["numero_documento"]})
    nombres = render_to_string("componentes/campo.html", {"campo": formulario["nombres"]})

    assert 'data-solo="documento"' in documento
    assert 'minlength="5"' in documento and 'maxlength="11"' in documento
    assert 'data-solo="letras"' in nombres


def test_todas_las_pantallas_cargan_los_avisos():
    html = render_to_string("base/base.html")
    assert "js/validacion.js" in html
