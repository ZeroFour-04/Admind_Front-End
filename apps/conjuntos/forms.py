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


# El mismo límite de la API, que es la que decide. Aquí solo evita mandarle un archivo que va a rechazar.
TAMANO_MAXIMO_LOGO = 512 * 1024  # bytes


class ConjuntoForm(forms.Form):
    """Paso 1 del asistente: datos básicos. Los nombres coinciden con los de la API."""

    nombre = forms.CharField(label="Nombre del conjunto", max_length=80)
    direccion = forms.CharField(label="Dirección", max_length=200, required=False)
    acento = forms.ChoiceField(label="Color del conjunto", choices=ACENTOS, initial="verde")


class AcentoForm(forms.Form):
    """Identidad visual (HU-21): el color es uno de los ocho del catálogo, sin selector libre."""

    acento = forms.ChoiceField(label="Color del conjunto", choices=ACENTOS)


class LogoForm(forms.Form):
    archivo = forms.FileField(label="Archivo del logo")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.size > TAMANO_MAXIMO_LOGO:
            raise forms.ValidationError(f"El logo no puede pesar más de {TAMANO_MAXIMO_LOGO // 1024} KB.")
        return archivo


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
