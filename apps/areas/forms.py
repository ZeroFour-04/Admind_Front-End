from django import forms

class AreaForm(forms.Form):
    """Los nombres coinciden con los de la API."""

    nombre = forms.CharField(label="Nombre", max_length=80)
    descripcion = forms.CharField(label="Descripción", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    hora_apertura = forms.TimeField(label="Abre a las")
    hora_cierre = forms.TimeField(label="Cierra a las")
    duracion_franja_minutos = forms.IntegerField(
        label="Duración de cada franja, en minutos",
        min_value=120,
        max_value=1440,
        help_text="Cada reserva debe durar al menos 2 horas.",
    )

    def clean(self):
        datos = super().clean()
        apertura, cierre = datos.get("hora_apertura"), datos.get("hora_cierre")
        if apertura and cierre and cierre <= apertura:
            self.add_error("hora_cierre", "La hora de cierre debe ser posterior a la de apertura.")
        return datos

    def datos_para_api(self):
        """Las horas viajan como texto `HH:MM`: el JSON no tiene tipo hora."""
        datos = dict(self.cleaned_data)
        for campo in ("hora_apertura", "hora_cierre"):
            datos[campo] = datos[campo].strftime("%H:%M")
        return datos


class EditarAreaForm(AreaForm):
    """Con la casilla de mantenimiento."""

    en_mantenimiento = forms.BooleanField(label="En mantenimiento: no admite solicitudes", required=False)
