from django import forms


class IngresoForm(forms.Form):
    # Los nombres coinciden con los de la API: así un error 400 cae en su campo sin traducir nombres.
    correo = forms.EmailField(label="Correo")
    contrasena = forms.CharField(label="Contraseña", strip=False)
