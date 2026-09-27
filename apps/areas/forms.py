from django import forms

# Lista cerrada (HU-09). La valida también la API. Cada opción lleva una línea de ayuda.
CLASIFICACIONES = [
    ("comun", "Común"),
    ("comun_esencial", "Común esencial"),
    ("comun_uso_exclusivo", "Común de uso exclusivo"),
]
AYUDA_POR_CLASIFICACION = {
    "comun": "La puede solicitar cualquier residente, según las reglas del conjunto.",
    "comun_esencial": "Indispensable para el conjunto, como la portería. La mora no restringe su uso.",
    "comun_uso_exclusivo": "Es común, pero su uso se asigna a una unidad, como una terraza o un parqueadero.",
}


class AreaForm(forms.Form):
    """Los nombres coinciden con los de la API. La clasificación no trae ninguna opción marcada."""

    nombre = forms.CharField(label="Nombre", max_length=80)
    descripcion = forms.CharField(label="Descripción", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    clasificacion = forms.ChoiceField(label="Clasificación", choices=CLASIFICACIONES)
    hora_apertura = forms.TimeField(label="Abre a las")
    hora_cierre = forms.TimeField(label="Cierra a las")
    duracion_franja_minutos = forms.IntegerField(label="Duración de cada franja, en minutos", min_value=1, max_value=1440)

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
    """Sin clasificación: no se cambia después de crear el área. Con la casilla de mantenimiento."""

    en_mantenimiento = forms.BooleanField(label="En mantenimiento: no admite solicitudes", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields["clasificacion"]
