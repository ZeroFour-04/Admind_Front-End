from django import forms

TAMANO_MAXIMO = 10 * 1024 * 1024  # bytes, igual que en la API


class DocumentoForm(forms.Form):
    """Una versión nueva de un documento. Que de verdad sea un PDF lo decide la API, por la firma del archivo."""

    archivo = forms.FileField(label="Archivo PDF")

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.size > TAMANO_MAXIMO:
            raise forms.ValidationError(f"El documento no puede pesar más de {TAMANO_MAXIMO // (1024 * 1024)} MB.")
        if not archivo.name.lower().endswith(".pdf"):
            raise forms.ValidationError("El documento debe ser un archivo PDF.")
        return archivo
