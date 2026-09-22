from django import forms


class IngresoForm(forms.Form):
    # Los nombres coinciden con los de la API: así un error 400 cae en su campo sin traducir nombres.
    correo = forms.EmailField(label="Correo")
    contrasena = forms.CharField(label="Contraseña", strip=False)


class RecuperarForm(forms.Form):
    correo = forms.EmailField(label="Correo")


class RestablecerForm(forms.Form):
    contrasena = forms.CharField(label="Contraseña nueva", strip=False)
    confirmacion = forms.CharField(label="Escríbela otra vez", strip=False)

    def clean(self):
        datos = super().clean()
        if datos.get("contrasena") and datos.get("contrasena") != datos.get("confirmacion"):
            self.add_error("confirmacion", "Las dos contraseñas no coinciden.")
        return datos


class CodigoForm(forms.Form):
    codigo = forms.CharField(label="Código", max_length=20, strip=True)
