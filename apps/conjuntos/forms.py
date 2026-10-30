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

# Si el color del conjunto no está entre los ocho, se elige uno propio con el selector del navegador.
PERSONALIZADO = "personalizado"
OPCIONES_DE_COLOR = [*ACENTOS, (PERSONALIZADO, "Personalizado")]
# Lo que muestra el selector de color propio mientras no se haya elegido ninguno: el verde del catálogo.
COLOR_PROPIO_INICIAL = "#0e6b5a"


# El mismo límite de la API, que es la que decide. Aquí solo evita mandarle un archivo que va a rechazar.
TAMANO_MAXIMO_LOGO = 512 * 1024  # bytes


class ColorDelConjuntoForm(forms.Form):
    """El acento y, si es el personalizado, su color. Los nombres coinciden con los de la API."""

    acento = forms.ChoiceField(label="Color del conjunto", choices=OPCIONES_DE_COLOR, initial="verde")
    color = forms.RegexField(
        label="Color propio",
        regex=r"^#[0-9a-fA-F]{6}$",
        required=False,
        initial=COLOR_PROPIO_INICIAL,
        error_messages={"invalid": "Elige un color válido."},
    )

    def clean(self):
        datos = super().clean()
        if datos.get("acento") == PERSONALIZADO:
            if not datos.get("color"):
                self.add_error("color", "Elige el color del conjunto.")
        else:
            # El selector de color siempre manda un valor: con un acento del catálogo no se usa.
            datos.pop("color", None)
        return datos


class ConjuntoForm(ColorDelConjuntoForm):
    """Paso 1 del asistente: datos básicos."""

    nombre = forms.CharField(label="Nombre del conjunto", max_length=30)
    direccion = forms.CharField(label="Dirección", max_length=200, required=False)

    field_order = ["nombre", "direccion", "acento", "color"]


class AcentoForm(ColorDelConjuntoForm):
    """Identidad visual (HU-21): uno de los ocho del catálogo o un color propio."""


class LogoForm(forms.Form):
    """La foto del conjunto. Llega ya cuadrada (1:1) si el navegador la recortó; si no, la API la rechaza."""

    archivo = forms.FileField(label="Foto del conjunto")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.size > TAMANO_MAXIMO_LOGO:
            raise forms.ValidationError(f"La foto no puede pesar más de {TAMANO_MAXIMO_LOGO // 1024} KB.")
        return archivo


# El mismo límite de la API, que es la que decide. Aquí solo evita mandarle un archivo que va a rechazar.
TAMANO_MAXIMO_REGLAMENTO = 10 * 1024 * 1024  # bytes


class ReglamentoForm(forms.Form):
    """El reglamento del conjunto. Que de verdad sea un PDF lo decide la API, por la firma del archivo."""

    archivo = forms.FileField(label="Reglamento, en PDF")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.size > TAMANO_MAXIMO_REGLAMENTO:
            megas = TAMANO_MAXIMO_REGLAMENTO // (1024 * 1024)
            raise forms.ValidationError(f"El reglamento no puede pesar más de {megas} MB.")
        if not archivo.name.lower().endswith(".pdf"):
            raise forms.ValidationError("El reglamento debe ser un archivo PDF.")
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

class SuperusuarioForm(UsuarioForm):
    """La cuenta de otro Superusuario desde el selector (2026-10-30). Sin rol: la API fija el de plataforma."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["rol"]
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "am-campo__control"
