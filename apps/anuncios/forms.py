from django import forms

# Los dos alcances de un anuncio (maestro §5.7). No hay campo de destinatario: el alcance
# «persona» no existe.
ALCANCES = [
    ("conjunto", "Todo el conjunto"),
    ("vivienda", "Una vivienda"),
]

# Los mismos topes de la API. Aquí solo ahorran un viaje: quien decide es ella.
MAXIMO_DE_FOTOS = 4
TAMANO_MAXIMO_FOTO = 5 * 1024 * 1024  # bytes


class VariosArchivos(forms.ClearableFileInput):
    allow_multiple_selected = True


class CampoDeFotos(forms.FileField):
    """Un campo que recibe varios archivos. Entrega siempre una lista, vacía si no se eligió ninguno."""

    widget = VariosArchivos

    def clean(self, data, initial=None):
        limpiar_uno = super().clean
        archivos = data if isinstance(data, (list, tuple)) else [data]
        return [limpiar_uno(archivo, initial) for archivo in archivos if archivo]


class AnuncioForm(forms.Form):
    """Los nombres coinciden con los de la API. Solo se ofrecen los alcances que la persona puede usar."""

    titulo = forms.CharField(label="Título", max_length=120)
    cuerpo = forms.CharField(label="Texto del anuncio", max_length=4000, widget=forms.Textarea(attrs={"rows": 6}))
    fotos = CampoDeFotos(label="Fotos", required=False)
    alcance = forms.ChoiceField(label="¿Para quién es?", choices=ALCANCES, initial="conjunto")
    unidad = forms.ChoiceField(label="Vivienda", required=False)

    def __init__(self, *args, alcances, unidades, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alcance"].choices = [opcion for opcion in ALCANCES if opcion[0] in alcances]
        self.fields["alcance"].initial = self.fields["alcance"].choices[0][0]
        self.fields["unidad"].choices = [("", "Elige la vivienda")] + [
            (unidad["id"], unidad["nombre"]) for unidad in unidades
        ]

    def clean_fotos(self):
        # Si de verdad son imágenes lo decide la API, que lee la firma de cada archivo.
        fotos = self.cleaned_data["fotos"]
        if len(fotos) > MAXIMO_DE_FOTOS:
            raise forms.ValidationError(f"Un anuncio lleva hasta {MAXIMO_DE_FOTOS} fotos.")
        for foto in fotos:
            if foto.size > TAMANO_MAXIMO_FOTO:
                raise forms.ValidationError(f"«{foto.name}» pesa más de {TAMANO_MAXIMO_FOTO // (1024 * 1024)} MB.")
        return fotos

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
