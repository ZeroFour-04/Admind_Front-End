from django import forms
from django.utils import timezone

from apps.usuarios.forms import UsuarioForm

TIPOS_DE_VINCULO = [("propietario", "Propietario"), ("arrendatario", "Arrendatario")]


class UnidadForm(forms.Form):
    nombre = forms.CharField(label="Nombre del apartamento", max_length=40)


class VinculoForm(forms.Form):
    """Las personas salen de los usuarios del conjunto activo: solo se vincula a quien ya tiene un rol aquí."""

    persona = forms.ChoiceField(label="Persona")
    tipo = forms.ChoiceField(label="Tipo de vínculo", choices=TIPOS_DE_VINCULO)
    reside = forms.BooleanField(label="Vive en la unidad", required=False)

    def __init__(self, *args, personas, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["persona"].choices = [("", "Elige a la persona")] + personas


class NuevoResidenteForm(UsuarioForm):
    """Crear a un residente desde la vivienda. Es el alta de Usuarios sin el campo «rol»: el rol no viaja en
    el formulario, lo pone la vista, y desde aquí solo se crean residentes."""

    rol = None


class CerrarVinculoForm(forms.Form):
    # Es el primer día sin el vínculo, el mismo criterio de la API (plan P5).
    vigencia_hasta = forms.DateField(label="Primer día sin el vínculo", initial=timezone.localdate)

    def datos_para_api(self):
        return {"vigencia_hasta": self.cleaned_data["vigencia_hasta"].isoformat()}
