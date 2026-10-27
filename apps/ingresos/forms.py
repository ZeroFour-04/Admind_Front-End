from django import forms


def opciones_de_zonas(zonas):
    return [("", "Elige la zona")] + [(zona["area"]["id"], zona["area"]["nombre"]) for zona in zonas]


class BuscarResidenteForm(forms.Form):
    """Primer paso: la zona, el documento de quien entra y cuántos lo acompañan."""

    area = forms.ChoiceField(label="Zona")
    numero_documento = forms.CharField(
        label="Número de documento del residente",
        max_length=30,
        widget=forms.TextInput(attrs={"inputmode": "numeric", "autocomplete": "off"}),
    )
    acompanantes = forms.IntegerField(label="Acompañantes que entran con la persona", min_value=0, max_value=50, initial=0)

    def __init__(self, *args, zonas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].choices = opciones_de_zonas(zonas)


class ConfirmarIngresoForm(BuscarResidenteForm):
    """Segundo paso: quién es y a nombre de qué vivienda entra. `residente` es «persona:vivienda»."""

    residente = forms.ChoiceField(label="Residente y vivienda", widget=forms.RadioSelect)

    def __init__(self, *args, residentes=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["residente"].choices = [
            (f"{residente['persona']}:{unidad['id']}", f"{residente['nombre']} · {unidad['nombre']}")
            for residente in residentes
            for unidad in residente["unidades"]
        ]

    def persona_y_vivienda(self):
        persona, vivienda = self.cleaned_data["residente"].split(":")
        return persona, vivienda


class FiltroDeHistorialForm(forms.Form):
    """El historial es de un día y, si se quiere, de una sola zona."""

    area = forms.ChoiceField(label="Zona", required=False)
    fecha = forms.DateField(label="Día", required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, zonas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].choices = [("", "Todas las zonas")] + opciones_de_zonas(zonas)[1:]
