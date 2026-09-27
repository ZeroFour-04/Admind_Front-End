from django import forms


class SolicitudForm(forms.Form):
    """Lo que llena la persona durante los 3 minutos (HU-12, HU-13). Los nombres coinciden con los de la API."""

    unidad = forms.ChoiceField(label="Apartamento")
    motivo = forms.CharField(label="Motivo", max_length=200)
    asistentes = forms.IntegerField(label="Asistentes", min_value=1)
    observaciones = forms.CharField(label="Observaciones", max_length=1000, required=False, widget=forms.Textarea)

    def __init__(self, *args, unidades, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidad"].choices = [(unidad["id"], unidad["nombre"]) for unidad in unidades]
        # Con una sola unidad no hay nada que elegir: va fija.
        if len(unidades) == 1:
            self.fields["unidad"].initial = unidades[0]["id"]
