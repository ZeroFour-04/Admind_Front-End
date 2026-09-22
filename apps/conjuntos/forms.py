from django import forms

from apps.usuarios.forms import UsuarioForm

# Catálogo cerrado de acentos (maestro §6.3). Lo valida también la API.
ACENTOS = [
    ("verde", "Verde"),
    ("azul", "Azul"),
    ("indigo", "Índigo"),
    ("purpura", "Púrpura"),
    ("vino", "Vino"),
    ("terracota", "Terracota"),
    ("ocre", "Ocre"),
    ("pizarra", "Pizarra"),
]


class ConjuntoForm(forms.Form):
    """Paso 1 del asistente: datos básicos. Los nombres coinciden con los de la API."""

    nombre = forms.CharField(label="Nombre del conjunto", max_length=80)
    direccion = forms.CharField(label="Dirección", max_length=200, required=False)
    acento = forms.ChoiceField(label="Color del conjunto", choices=ACENTOS, initial="verde")


class AdministradorForm(UsuarioForm):
    """Paso 2 del asistente: la cuenta de quien administra. El rol es siempre Administración."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["rol"]
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "am-campo__control"

    def clean(self):
        datos = super().clean()
        datos["rol"] = "administracion"
        return datos
