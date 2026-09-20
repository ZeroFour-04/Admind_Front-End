from django import forms


class UsuarioForm(forms.Form):
    rol = forms.ChoiceField(
        label="Rol en el conjunto",
        choices=[
            ("administracion", "Administración"),
            ("consejo", "Consejo"),
            ("secretaria", "Secretaría"),
            ("vigilancia", "Vigilancia"),
            ("residente", "Residente"),
        ],
    )
    tipo_documento = forms.ChoiceField(
        label="Tipo de documento",
        choices=[
            ("CC", "Cédula de ciudadanía"),
            ("TI", "Tarjeta de identidad"),
            ("CE", "Cédula de extranjería"),
            ("PAS", "Pasaporte"),
            ("PPT", "Permiso por Protección Temporal"),
        ],
    )
    numero_documento = forms.CharField(label="Número de documento", max_length=20)
    nombres = forms.CharField(label="Nombres", max_length=80)
    apellidos = forms.CharField(label="Apellidos", max_length=80)
    telefono = forms.CharField(label="Teléfono", max_length=16, required=False)
    correo = forms.EmailField(label="Correo electrónico")
    contrasena = forms.CharField(label="Contraseña", min_length=8, strip=False, widget=forms.PasswordInput)
    confirmar_contrasena = forms.CharField(
        label="Confirmar contraseña", strip=False, widget=forms.PasswordInput
    )

    def clean(self):
        datos = super().clean()
        if datos.get("contrasena") != datos.get("confirmar_contrasena"):
            self.add_error("confirmar_contrasena", "Las contraseñas no coinciden.")
        datos.pop("confirmar_contrasena", None)
        return datos
