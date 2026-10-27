from django import forms


class RegistrarVisitanteForm(forms.Form):
    cedula = forms.CharField(label="CC", max_length=20, widget=forms.TextInput(attrs={"inputmode": "numeric"}))
    nombre = forms.CharField(label="Nombre", max_length=120)
    ingresa_con_vehiculo = forms.ChoiceField(
        label="¿El visitante ingresa con vehículo?",
        choices=(("no", "No"), ("si", "Sí")),
        initial="no",
        widget=forms.RadioSelect,
    )
    placa_vehiculo = forms.CharField(label="Placa vehículo", max_length=10, required=False)
    tipo_vehiculo = forms.ChoiceField(
        label="Tipo vehículo",
        choices=(("Auto", "Auto"), ("Moto", "Moto")),
        required=False,
    )
    # Las opciones son los parqueaderos de visitantes libres al cargar la pantalla. Validar contra ellas es la
    # primera barrera; la segunda es la API, que responde 409 si otra visita lo ocupó entre tanto.
    parqueadero = forms.ChoiceField(
        label="Parqueadero de visitantes",
        required=False,
        error_messages={
            "invalid_choice": "Ese parqueadero ya no está libre. Elige otro o registra la visita sin parqueadero."
        },
    )
    apartamento_visitado = forms.ChoiceField(label="Apartamento a visitar")

    def __init__(self, *args, unidades=(), parqueaderos=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["apartamento_visitado"].choices = [("", "Selecciona un apartamento")] + [
            (str(unidad["id"]), unidad["nombre"]) for unidad in unidades
        ]
        self.ofrecer_parqueaderos(parqueaderos)

    def ofrecer_parqueaderos(self, parqueaderos):
        """Cambia las opciones de parqueadero: la primera siempre es «Sin parqueadero»."""
        self.fields["parqueadero"].choices = [("", "Sin parqueadero")] + [
            (str(p["id"]), p["codigo"] + (" · accesible" if p.get("accesible") else "")) for p in parqueaderos
        ]

    def clean(self):
        datos = super().clean()
        ingresa_con_vehiculo = datos.get("ingresa_con_vehiculo") == "si"
        if ingresa_con_vehiculo:
            if not datos.get("placa_vehiculo"):
                self.add_error("placa_vehiculo", "Ingresa la placa del vehículo.")
            if not datos.get("tipo_vehiculo"):
                self.add_error("tipo_vehiculo", "Selecciona Auto o Moto.")
        else:
            datos["placa_vehiculo"] = ""
            datos["tipo_vehiculo"] = ""
            # Sin vehículo no hay puesto: un campo desactivado tampoco viaja, y esto dice lo mismo que el JavaScript.
            datos["parqueadero"] = ""
        datos["ingresa_con_vehiculo"] = ingresa_con_vehiculo
        return datos
