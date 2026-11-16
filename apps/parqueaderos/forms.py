from django import forms


class ParqueaderoForm(forms.Form):
    """Crear un parqueadero. Los nombres coinciden con los de la API. No hay campo de unidad: se crea libre y se asigna después."""

    codigo = forms.CharField(label="Código", max_length=20)
    tipo = forms.ChoiceField(
        label="Tipo",
        choices=(("visitantes", "Visitantes"), ("residentes", "Residentes")),
        initial="visitantes",
    )
    # Para qué vehículo es el puesto: con él se cuenta el tope por vivienda de los de residentes (HU-34).
    vehiculo = forms.ChoiceField(
        label="Vehículo",
        choices=(("carro", "Carro"), ("moto", "Moto"), ("bicicleta", "Bicicleta")),
        initial="carro",
    )
    accesible = forms.BooleanField(label="Es accesible", required=False)
    notas = forms.CharField(label="Notas", max_length=200, required=False)

    def datos_para_api(self):
        datos = self.cleaned_data
        return {
            "codigo": datos["codigo"],
            "tipo": datos["tipo"],
            "vehiculo": datos["vehiculo"],
            "accesible": datos["accesible"],
            "notas": datos["notas"],
        }


class AsignarForm(forms.Form):
    """Elegir la vivienda de un parqueadero de residentes. Las opciones son las viviendas del conjunto activo."""

    unidad = forms.ChoiceField(
        label="Vivienda",
        error_messages={"invalid_choice": "Elige una vivienda de la lista.", "required": "Elige una vivienda."},
    )

    def __init__(self, *args, unidades=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidad"].choices = [("", "Selecciona una vivienda")] + [
            (str(unidad["id"]), unidad["nombre"]) for unidad in unidades
        ]
