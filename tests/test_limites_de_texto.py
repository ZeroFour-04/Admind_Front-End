"""Límites de texto: nombre del conjunto, nombres y apellidos hasta 30 caracteres y teléfono hasta 10."""
from django.template.loader import render_to_string

from apps.conjuntos.forms import ConjuntoForm
from apps.usuarios.forms import UsuarioForm

DATOS_DE_USUARIO = {
    "rol": "residente",
    "tipo_documento": "CC",
    "numero_documento": "1023456789",
    "nombres": "Carlos",
    "apellidos": "Gómez",
    "telefono": "3001234567",
    "correo": "carlos@torres.com",
    "contrasena": "una-clave-larga-2026",
    "confirmar_contrasena": "una-clave-larga-2026",
}


def test_el_nombre_del_conjunto_admite_30_caracteres_y_rechaza_31():
    valido = ConjuntoForm(data={"nombre": "C" * 30, "acento": "verde"})
    largo = ConjuntoForm(data={"nombre": "C" * 31, "acento": "verde"})

    assert valido.is_valid()
    assert not largo.is_valid()
    assert "nombre" in largo.errors


def test_nombres_y_apellidos_admiten_30_caracteres_y_rechazan_31():
    valido = UsuarioForm(data={**DATOS_DE_USUARIO, "nombres": "N" * 30, "apellidos": "A" * 30})
    nombres_largos = UsuarioForm(data={**DATOS_DE_USUARIO, "nombres": "N" * 31})
    apellidos_largos = UsuarioForm(data={**DATOS_DE_USUARIO, "apellidos": "A" * 31})

    assert valido.is_valid()
    assert "nombres" in nombres_largos.errors
    assert "apellidos" in apellidos_largos.errors


def test_el_telefono_admite_10_caracteres_y_rechaza_11():
    valido = UsuarioForm(data={**DATOS_DE_USUARIO, "telefono": "3001234567"})
    largo = UsuarioForm(data={**DATOS_DE_USUARIO, "telefono": "30012345678"})

    assert valido.is_valid()
    assert "telefono" in largo.errors


def test_el_campo_del_formulario_trae_el_limite_en_el_navegador():
    formulario = UsuarioForm()

    html = {
        nombre: render_to_string("componentes/campo.html", {"campo": formulario[nombre]})
        for nombre in ("nombres", "apellidos", "telefono")
    }

    assert 'maxlength="30"' in html["nombres"]
    assert 'maxlength="30"' in html["apellidos"]
    assert 'maxlength="10"' in html["telefono"]
    assert 'maxlength="30"' in render_to_string(
        "componentes/campo.html", {"campo": ConjuntoForm()["nombre"]}
    )
