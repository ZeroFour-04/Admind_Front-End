from django import forms


class ParqueaderoForm(forms.Form):
    """Crear un parqueadero. Los nombres coinciden con los de la API. No hay campo de unidad: no se asigna aquí."""

    codigo = forms.CharField(label="Código", max_length=20)
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=(("visitantes", "Visitantes"), ("residentes", "Residentes")),
        initial="visitantes",
    )
    accesible = forms.BooleanField(label="Es accesible", required=False)
    notas = forms.CharField(label="Notas", max_length=200, required=False)

    def datos_para_api(self):
        datos = self.cleaned_data
        return {
            "codigo": datos["codigo"],
            "tipo": datos["tipo"],
            "accesible": datos["accesible"],
            "notas": datos["notas"],
        }
