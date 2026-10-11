"""Un formulario de Django por tipo de regla (HU-10). El catálogo lo valida también la API."""
from django import forms
from django.utils import timezone

# De 0 (lunes) a 6 (domingo), igual que en la API.
DIAS_DE_LA_SEMANA = [
    ("0", "Lunes"), ("1", "Martes"), ("2", "Miércoles"), ("3", "Jueves"), ("4", "Viernes"), ("5", "Sábado"), ("6", "Domingo"),
]


class CampoFecha(forms.DateInput):
    input_type = "date"


class ParametrosForm(forms.Form):
    """Base de los valores de una regla. Al definirla lleva la vigencia; al editar no, porque la versión nueva empieza hoy."""

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


class AcompanantesForm(ParametrosForm):
    maximo = forms.IntegerField(
        label="Máximo de acompañantes por vivienda a la vez",
        min_value=0,
        help_text="Con 0 no se permiten acompañantes. Cada acompañante ocupa un puesto del aforo.",
    )


class RequierePazYSalvoForm(ParametrosForm):
    """Sin parámetros."""


class DiaLimiteDePagoForm(ParametrosForm):
    """El día del mes hasta el que se paga la administración sin entrar en mora (HU-35)."""

    dia = forms.IntegerField(
        label="Día límite de pago",
        min_value=1,
        max_value=28,
        help_text="Hasta el 28, para que exista en todos los meses.",
    )


class UnaReservaPorDiaForm(ParametrosForm):
    """Sin parámetros: definirla la activa."""


class SinFranjasSeguidasForm(ParametrosForm):
    """Sin parámetros: definirla la activa."""


class DiaQueNoAbreForm(forms.Form):
    """Un renglón de «Días que no abre»: un día de la semana, o una fecha o periodo, con su motivo."""

    CLASES = [("dia_semana", "Un día de la semana, todas las semanas"), ("periodo", "Una fecha o un periodo")]

    clase = forms.ChoiceField(label="Qué no abre", choices=CLASES, widget=forms.RadioSelect, initial="dia_semana")
    dia_semana = forms.ChoiceField(label="Día de la semana", choices=DIAS_DE_LA_SEMANA, required=False)
    desde = forms.DateField(label="Desde", widget=CampoFecha, required=False)
    hasta = forms.DateField(label="Hasta", widget=CampoFecha, required=False, help_text="Vacío si es un solo día.")
    motivo = forms.CharField(
        label="Motivo", max_length=120, help_text="Es lo que lee el residente: limpieza, reparación, Navidad."
    )

    def clean(self):
        datos = super().clean()
        if datos.get("clase") == "dia_semana" and not datos.get("dia_semana"):
            self.add_error("dia_semana", "Elige el día.")
        if datos.get("clase") == "periodo":
            if not datos.get("desde"):
                self.add_error("desde", "Indica la fecha.")
            elif datos.get("hasta") and datos["hasta"] < datos["desde"]:
                self.add_error("hasta", "La fecha final no puede ser anterior a la inicial.")
        return datos

    def renglon(self):
        """El renglón con la forma que espera la API."""
        datos = self.cleaned_data
        if datos["clase"] == "dia_semana":
            return {"dia_semana": int(datos["dia_semana"]), "motivo": datos["motivo"]}
        hasta = datos["hasta"] or datos["desde"]
        return {"desde": datos["desde"].isoformat(), "hasta": hasta.isoformat(), "motivo": datos["motivo"]}


FORMULARIO_POR_TIPO = {
    "ANTICIPACION_MINIMA": AnticipacionMinimaForm,
    "ANTICIPACION_MAXIMA": AnticipacionMaximaForm,
    "REQUIERE_PAZ_Y_SALVO": RequierePazYSalvoForm,
    "DIA_LIMITE_DE_PAGO": DiaLimiteDePagoForm,
    "CUPO_POR_UNIDAD": CupoPorUnidadForm,
    "ACOMPANANTES": AcompanantesForm,
    "UNA_RESERVA_POR_DIA": UnaReservaPorDiaForm,
    "SIN_FRANJAS_SEGUIDAS": SinFranjasSeguidasForm,
}


def iniciales(tipo, parametros):
    """Los parámetros de la API como valores iniciales del formulario de su tipo."""
    return dict(parametros)
