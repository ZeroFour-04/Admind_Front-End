from django import forms

TAMANO_MAXIMO_FOTO = 5 * 1024 * 1024


class CasoForm(forms.Form):
    titulo = forms.CharField(label="Título o motivo", max_length=120)
    caso = forms.CharField(label="Caso", max_length=4000, widget=forms.Textarea(attrs={"rows": 6}))
    foto = forms.FileField(label="Subir una foto o imagen", required=False)

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto and foto.size > TAMANO_MAXIMO_FOTO:
            raise forms.ValidationError("La imagen pesa más de 5 MB.")
        return foto
