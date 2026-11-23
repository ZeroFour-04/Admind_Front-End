"""Reglas de formato de los campos de personas, compartidas por todos los formularios del front.

Cada campo lleva `data-solo` (la clase de caracteres que acepta) y su largo en `minlength` y `maxlength`.
`static/js/validacion.js` lee esos atributos y avisa en rojo mientras se escribe; el formulario de Django
repite la misma regla al enviar, y la API la vuelve a comprobar.
"""
import re

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

DOCUMENTO_MINIMO = 5
DOCUMENTO_MAXIMO = 11
# El pasaporte es el único documento colombiano que lleva letras.
TIPOS_CON_LETRAS = {"PAS"}

SOLO_DIGITOS = re.compile(r"^[0-9]+$")
SOLO_LETRAS_Y_DIGITOS = re.compile(r"^[A-Za-z0-9]+$")
SOLO_LETRAS = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$")
PLACA = re.compile(r"^[A-Za-z0-9]{5,7}$")

MENSAJE_DIGITOS = "En este campo solo se aceptan números, sin puntos ni espacios."
MENSAJE_LETRAS_Y_DIGITOS = "En este campo solo se aceptan letras y números, sin espacios ni símbolos."
MENSAJE_LETRAS = "En este campo solo se aceptan letras y espacios."
MENSAJE_PLACA = "La placa solo acepta letras y números, sin espacios ni guiones (5 a 7 caracteres)."
MENSAJE_LARGO_DOCUMENTO = f"El documento debe tener entre {DOCUMENTO_MINIMO} y {DOCUMENTO_MAXIMO} caracteres."


def validar_documento(tipo, numero):
    """Lanza ValidationError si el número no sirve para ese tipo de documento."""
    patron, mensaje = (
        (SOLO_LETRAS_Y_DIGITOS, MENSAJE_LETRAS_Y_DIGITOS) if tipo in TIPOS_CON_LETRAS else (SOLO_DIGITOS, MENSAJE_DIGITOS)
    )
    if not patron.match(numero):
        raise ValidationError(mensaje)
    if not DOCUMENTO_MINIMO <= len(numero) <= DOCUMENTO_MAXIMO:
        raise ValidationError(MENSAJE_LARGO_DOCUMENTO)


def campo_documento(label="Número de documento", *, con_letras=False):
    """El número de documento. Con `tipo_documento` en el mismo formulario, el JavaScript decide si acepta
    letras según el tipo elegido; el formulario lo comprueba en `limpiar_documento`."""
    return forms.CharField(
        label=label,
        min_length=DOCUMENTO_MINIMO,
        max_length=DOCUMENTO_MAXIMO,
        error_messages={"min_length": MENSAJE_LARGO_DOCUMENTO, "max_length": MENSAJE_LARGO_DOCUMENTO},
        validators=[RegexValidator(SOLO_LETRAS_Y_DIGITOS, MENSAJE_LETRAS_Y_DIGITOS)] if con_letras else [],
        widget=forms.TextInput(
            attrs={
                "data-solo": "documento" if not con_letras else "alfanumerico",
                "inputmode": "text" if con_letras else "numeric",
                "autocomplete": "off",
            }
        ),
    )


def limpiar_documento(formulario, datos):
    """Para el `clean()` de un formulario con `tipo_documento` y `numero_documento`."""
    numero = datos.get("numero_documento")
    if numero:
        try:
            validar_documento(datos.get("tipo_documento"), numero)
        except ValidationError as error:
            formulario.add_error("numero_documento", error)
    return datos


def campo_cedula(label="CC"):
    """Una cédula sin tipo para elegir: solo números."""
    return forms.RegexField(
        label=label,
        regex=SOLO_DIGITOS,
        min_length=DOCUMENTO_MINIMO,
        max_length=DOCUMENTO_MAXIMO,
        error_messages={
            "invalid": MENSAJE_DIGITOS,
            "min_length": MENSAJE_LARGO_DOCUMENTO,
            "max_length": MENSAJE_LARGO_DOCUMENTO,
        },
        widget=forms.TextInput(attrs={"data-solo": "digitos", "inputmode": "numeric", "autocomplete": "off"}),
    )


def campo_letras(label, max_length, **kwargs):
    """Nombres y apellidos: letras (con tildes y ñ), espacios, guion y apóstrofo."""
    return forms.RegexField(
        label=label,
        regex=SOLO_LETRAS,
        min_length=2,
        max_length=max_length,
        error_messages={"invalid": MENSAJE_LETRAS, "min_length": "Escribe al menos 2 letras."},
        widget=forms.TextInput(attrs={"data-solo": "letras"}),
        **kwargs,
    )


def campo_placa(label="Placa vehículo", **kwargs):
    return forms.RegexField(
        label=label,
        regex=PLACA,
        max_length=7,
        error_messages={"invalid": MENSAJE_PLACA},
        widget=forms.TextInput(attrs={"data-solo": "alfanumerico", "autocomplete": "off"}),
        **kwargs,
    )
