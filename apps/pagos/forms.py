from django import forms


class ReportarPagoForm(forms.Form):
    """El residente reporta el pago de un mes con su comprobante. Los nombres coinciden con los de la API.

    Las opciones de vivienda y de mes salen de lo que la API le entrega a esta persona. El `accept` del
    archivo es solo una ayuda del navegador: el tipo y el peso los valida la API por la firma del archivo.
    """

    unidad = forms.ChoiceField(label="Vivienda")
    periodo = forms.ChoiceField(label="Mes")
    archivo = forms.FileField(
        label="Comprobante de pago",
        widget=forms.FileInput(attrs={"accept": ".pdf,image/png,image/jpeg", "class": "am-campo__control campo-archivo"}),
    )

    def __init__(self, *args, viviendas=(), meses=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["unidad"].choices = [(str(v["id"]), v["nombre"]) for v in viviendas]
        self.fields["periodo"].choices = list(meses)
        if len(viviendas) == 1:
            # Con una sola vivienda no hay nada que elegir: va fija.
            self.fields["unidad"].initial = str(viviendas[0]["id"])
