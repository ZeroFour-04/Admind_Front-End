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


MODOS_DE_USO = [("reserva", "Con reserva"), ("ingreso", "Con ingreso")]


class AreaForm(forms.Form):
    """Los nombres coinciden con los de la API. El modo se elige al crear y no cambia (plan P3)."""

    modo_uso = forms.ChoiceField(label="Cómo se usa", choices=MODOS_DE_USO, initial="reserva", required=False)
    nombre = forms.CharField(label="Nombre", max_length=80)
    descripcion = forms.CharField(label="Descripción", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    hora_apertura = forms.TimeField(label="Abre a las")
    hora_cierre = forms.TimeField(label="Cierra a las")
    duracion_franja_minutos = forms.IntegerField(
        label="Duración de cada franja, en minutos",
        required=False,
        min_value=120,
        max_value=1440,
        help_text="Cada reserva debe durar al menos 2 horas.",
    )
    permanencia_maxima_minutos = forms.IntegerField(
        label="Permanencia máxima, en minutos",
        required=False,
        min_value=15,
        max_value=1440,
    )
    aforo_maximo = forms.IntegerField(label="Aforo máximo", min_value=1, max_value=10000)

    def modo_elegido(self):
        return self.cleaned_data.get("modo_uso") or "reserva"

    def clean(self):
        datos = super().clean()
        apertura, cierre = datos.get("hora_apertura"), datos.get("hora_cierre")
        if apertura and cierre and cierre <= apertura:
            self.add_error("hora_cierre", "La hora de cierre debe ser posterior a la de apertura.")
        campo_propio = "duracion_franja_minutos" if self.modo_elegido() == "reserva" else "permanencia_maxima_minutos"
        if datos.get(campo_propio) is None and campo_propio not in self.errors:
            self.add_error(campo_propio, "Este campo es obligatorio para este modo de uso.")
        return datos

    def datos_para_api(self):
        """Las horas viajan como texto `HH:MM`: el JSON no tiene tipo hora. Solo viaja el campo del modo."""
        datos = dict(self.cleaned_data)
        for campo in ("hora_apertura", "hora_cierre"):
            datos[campo] = datos[campo].strftime("%H:%M")
        datos["modo_uso"] = self.modo_elegido()
        ajeno = "permanencia_maxima_minutos" if datos["modo_uso"] == "reserva" else "duracion_franja_minutos"
        del datos[ajeno]
        return datos


class EditarAreaForm(AreaForm):
    """Con la casilla de mantenimiento. El modo se lee y no se cambia: la API lo rechaza (plan P3)."""

    en_mantenimiento = forms.BooleanField(label="En mantenimiento: no admite solicitudes", required=False)

    def __init__(self, *args, modo_uso="reserva", **kwargs):
        super().__init__(*args, **kwargs)
        self.modo_uso_actual = modo_uso
        del self.fields["modo_uso"]

    def modo_elegido(self):
        return self.modo_uso_actual

    def datos_para_api(self):
        datos = super().datos_para_api()
        del datos["modo_uso"]
        return datos
