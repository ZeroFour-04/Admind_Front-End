from django import forms

# Valores de partida de las áreas más comunes. No son reglas de nadie: se cambian antes de guardar.
PLANTILLAS_DE_AREA = {
    "salon": {"nombre": "Salón comunal", "hora_apertura": "08:00", "hora_cierre": "22:00",
              "duracion_franja_minutos": 240, "aforo_maximo": 50},
    "bbq": {"nombre": "BBQ", "hora_apertura": "10:00", "hora_cierre": "22:00",
            "duracion_franja_minutos": 240, "aforo_maximo": 15},
    "cancha": {"nombre": "Cancha múltiple", "hora_apertura": "06:00", "hora_cierre": "22:00",
               "duracion_franja_minutos": 120, "aforo_maximo": 20},
}


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
    aforo_maximo = forms.IntegerField(label="Aforo máximo", min_value=1, max_value=10000)

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
