from django import forms

# Los dos alcances de un anuncio (maestro §5.7). No hay campo de destinatario: el alcance
# «persona» no existe.
ALCANCES = [
    ("conjunto", "Todo el conjunto"),
    ("vivienda", "Una vivienda"),
]


class AnuncioForm(forms.Form):
    """Los nombres coinciden con los de la API. Solo se ofrecen los alcances que la persona puede usar."""

    titulo = forms.CharField(label="Título", max_length=120)
    cuerpo = forms.CharField(label="Texto del anuncio", max_length=4000, widget=forms.Textarea(attrs={"rows": 6}))
    alcance = forms.ChoiceField(label="¿Para quién es?", choices=ALCANCES, initial="conjunto")
    unidad = forms.ChoiceField(label="Vivienda", required=False)

    def __init__(self, *args, alcances, unidades, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alcance"].choices = [opcion for opcion in ALCANCES if opcion[0] in alcances]
        self.fields["alcance"].initial = self.fields["alcance"].choices[0][0]
        self.fields["unidad"].choices = [("", "Elige la vivienda")] + [
            (unidad["id"], unidad["nombre"]) for unidad in unidades
        ]

    def clean(self):
        datos = super().clean()
        if datos.get("alcance") == "vivienda":
            if not datos.get("unidad"):
                self.add_error("unidad", "Elige la vivienda a la que va el anuncio.")
        else:
            datos["unidad"] = None
        return datos


class EditarAnuncioForm(forms.Form):
    """Solo el texto: el alcance no cambia después de publicar, porque el aviso ya salió."""

    titulo = forms.CharField(label="Título", max_length=120)
    cuerpo = forms.CharField(label="Texto del anuncio", max_length=4000, widget=forms.Textarea(attrs={"rows": 6}))
