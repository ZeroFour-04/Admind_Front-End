from django import forms


class ConjuntoForm(forms.Form):
    nombre = forms.CharField(label="Nombre del conjunto", max_length=80)
    direccion = forms.CharField(label="Dirección", max_length=200, required=False)
