from django import forms
from django.utils import timezone

from .textos import LARGO_MAXIMO


class CampoFecha(forms.DateInput):
    input_type = "date"


class RegistrarForm(forms.Form):
    """Registrar una infracción. No tiene ningún campo de sanción, multa ni restricción: el sistema no sanciona."""

    unidad = forms.ChoiceField(
        label="Vivienda", error_messages={"required": "Elige la vivienda.", "invalid_choice": "Elige una vivienda de la lista."}
    )
    fecha_hecho = forms.DateField(label="Fecha del hecho", widget=CampoFecha)
    descripcion_hecho = forms.CharField(
        label="Qué ocurrió", max_length=LARGO_MAXIMO, widget=forms.Textarea(attrs={"rows": 5, "maxlength": LARGO_MAXIMO})
    )
    # Si nace de un caso, va escondido: la vivienda se elige a mano igual (el caso no la guarda).
    caso = forms.UUIDField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, unidades=(), sugeridas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidad"].choices = [("", "Selecciona una vivienda")] + [
            (str(unidad["id"]), unidad["nombre"]) for unidad in unidades
        ]
        if not self.is_bound and len(sugeridas) == 1:
            self.fields["unidad"].initial = str(sugeridas[0]["id"])

    def clean_fecha_hecho(self):
        fecha = self.cleaned_data["fecha_hecho"]
        if fecha > timezone.localdate():
            raise forms.ValidationError("La fecha del hecho no puede ser futura.")
        return fecha

    def datos_para_api(self):
        datos = self.cleaned_data
        return {
            "unidad": datos["unidad"],
            "fecha_hecho": datos["fecha_hecho"].isoformat(),
            "descripcion_hecho": datos["descripcion_hecho"],
            "caso": str(datos["caso"]) if datos.get("caso") else None,
        }


class CerrarForm(forms.Form):
    comentario = forms.CharField(
        label="Comentario del cierre",
        max_length=LARGO_MAXIMO,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": LARGO_MAXIMO}),
    )


class AnularForm(forms.Form):
    motivo = forms.CharField(
        label="Motivo de la anulación",
        max_length=LARGO_MAXIMO,
        widget=forms.Textarea(attrs={"rows": 3, "maxlength": LARGO_MAXIMO}),
    )
