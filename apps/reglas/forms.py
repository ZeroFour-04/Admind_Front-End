"""Un formulario de Django por tipo de regla (HU-10). El catálogo lo valida también la API."""
from datetime import date

from django import forms
from django.utils import timezone

# Catálogo cerrado de tipos (plan D4 a), provisional hasta validarlo contra un reglamento real.
TIPOS_DE_REGLA = [
    ("ANTICIPACION_MINIMA", "Anticipación mínima"),
    ("ANTICIPACION_MAXIMA", "Anticipación máxima"),
    ("CUPO_POR_UNIDAD", "Cupo por apartamento"),
    ("AFORO", "Aforo"),
    ("FRANJA_HORARIA", "Franja horaria"),
    ("DIAS_NO_RESERVABLES", "Días no reservables"),
    ("REQUIERE_PAZ_Y_SALVO", "Requiere paz y salvo"),
]
# De 0 (lunes) a 6 (domingo), igual que en la API.
DIAS_DE_LA_SEMANA = [
    ("0", "Lunes"), ("1", "Martes"), ("2", "Miércoles"), ("3", "Jueves"), ("4", "Viernes"), ("5", "Sábado"), ("6", "Domingo"),
]


class CampoHora(forms.TimeInput):
    input_type = "time"


class CampoFecha(forms.DateInput):
    input_type = "date"


class ElegirTipoForm(forms.Form):
    """Paso 1 del alta: sobre qué área y de qué tipo."""

    area = forms.ChoiceField(label="Área")
    tipo = forms.ChoiceField(label="Tipo de regla", choices=TIPOS_DE_REGLA)

    def __init__(self, *args, areas, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].choices = [("", "Elige el área")] + [(area["id"], area["nombre"]) for area in areas]


class ParametrosForm(forms.Form):
    """Base del paso 2. En el alta lleva la vigencia; al editar no, porque la versión nueva empieza hoy."""

    vigencia_desde = forms.DateField(label="Vigente desde", widget=CampoFecha, initial=lambda: timezone.localdate().isoformat())

    def __init__(self, *args, con_vigencia=True, **kwargs):
        super().__init__(*args, **kwargs)
        if not con_vigencia:
            del self.fields["vigencia_desde"]

    def parametros(self):
        """Los parámetros del tipo, con la forma que espera la API."""
        return {campo: valor for campo, valor in self.cleaned_data.items() if campo != "vigencia_desde"}


class AnticipacionMinimaForm(ParametrosForm):
    horas = forms.IntegerField(label="Horas de anticipación, como mínimo", min_value=0)


class AnticipacionMaximaForm(ParametrosForm):
    dias = forms.IntegerField(label="Días de anticipación, como máximo", min_value=1)


class CupoPorUnidadForm(ParametrosForm):
    reservas = forms.IntegerField(label="Reservas por apartamento", min_value=1)
    dias = forms.IntegerField(label="Cada cuántos días", min_value=1)


class AforoForm(ParametrosForm):
    maximo = forms.IntegerField(label="Máximo de asistentes", min_value=1)


class FranjaHorariaForm(ParametrosForm):
    dias_semana = forms.MultipleChoiceField(
        label="Días permitidos", choices=DIAS_DE_LA_SEMANA, widget=forms.CheckboxSelectMultiple
    )
    desde = forms.TimeField(label="Desde", widget=CampoHora(format="%H:%M"))
    hasta = forms.TimeField(label="Hasta", widget=CampoHora(format="%H:%M"))

    def clean(self):
        datos = super().clean()
        if datos.get("desde") and datos.get("hasta") and datos["hasta"] <= datos["desde"]:
            self.add_error("hasta", "La hora final debe ser posterior a la inicial.")
        return datos

    def parametros(self):
        datos = self.cleaned_data
        return {
            "dias_semana": sorted(int(dia) for dia in datos["dias_semana"]),
            "desde": datos["desde"].strftime("%H:%M"),
            "hasta": datos["hasta"].strftime("%H:%M"),
        }


class DiasNoReservablesForm(ParametrosForm):
    dias_semana = forms.MultipleChoiceField(
        label="Días de la semana", choices=DIAS_DE_LA_SEMANA, widget=forms.CheckboxSelectMultiple, required=False
    )
    fechas = forms.CharField(
        label="Fechas puntuales", required=False, help_text="Con el formato AAAA-MM-DD, separadas por comas."
    )

    def clean_fechas(self):
        texto = self.cleaned_data["fechas"]
        try:
            return [date.fromisoformat(parte.strip()).isoformat() for parte in texto.split(",") if parte.strip()]
        except ValueError:
            raise forms.ValidationError("Escribe cada fecha con el formato AAAA-MM-DD, separadas por comas.") from None

    def clean(self):
        datos = super().clean()
        if not datos.get("dias_semana") and not datos.get("fechas") and "fechas" not in self.errors:
            raise forms.ValidationError("Indica al menos un día de la semana o una fecha.")
        return datos

    def parametros(self):
        datos = self.cleaned_data
        return {"dias_semana": sorted(int(dia) for dia in datos["dias_semana"]), "fechas": datos["fechas"]}


class RequierePazYSalvoForm(ParametrosForm):
    """Sin parámetros. La API la rechaza sobre un área común esencial."""


FORMULARIO_POR_TIPO = {
    "ANTICIPACION_MINIMA": AnticipacionMinimaForm,
    "ANTICIPACION_MAXIMA": AnticipacionMaximaForm,
    "CUPO_POR_UNIDAD": CupoPorUnidadForm,
    "AFORO": AforoForm,
    "FRANJA_HORARIA": FranjaHorariaForm,
    "DIAS_NO_RESERVABLES": DiasNoReservablesForm,
    "REQUIERE_PAZ_Y_SALVO": RequierePazYSalvoForm,
}


def iniciales(tipo, parametros):
    """Los parámetros de la API como valores iniciales del formulario de su tipo."""
    datos = dict(parametros)
    if "dias_semana" in datos:
        datos["dias_semana"] = [str(dia) for dia in datos["dias_semana"]]
    if tipo == "DIAS_NO_RESERVABLES":
        datos["fechas"] = ", ".join(datos["fechas"])
    return datos
