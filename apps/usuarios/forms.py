from django import forms


# Los roles de conjunto del catálogo (maestro §5.3). No se crean ni se editan desde la interfaz.
ROLES_DE_CONJUNTO = [
    ("administracion", "Administración"),
    ("consejo", "Consejo"),
    ("secretaria", "Secretaría"),
    ("vigilancia", "Vigilancia"),
    ("residente", "Residente"),
]


class AsignarRolForm(forms.Form):
    """Solo ofrece los roles de conjunto que la persona todavía no tiene (HU-06)."""

    rol = forms.ChoiceField(label="Rol")

    def __init__(self, *args, roles_actuales=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].choices = [opcion for opcion in ROLES_DE_CONJUNTO if opcion[0] not in roles_actuales]


TIPOS_DE_DOCUMENTO = [
    ("CC", "Cédula de ciudadanía"),
    ("TI", "Tarjeta de identidad"),
    ("CE", "Cédula de extranjería"),
    ("PAS", "Pasaporte"),
    ("PPT", "Permiso por Protección Temporal"),
]


class BuscarPersonaForm(forms.Form):
    """Paso 1 de registrar persona (HU-07): el documento exacto. Viaja por POST, nunca en la URL."""

    tipo_documento = forms.ChoiceField(label="Tipo de documento", choices=TIPOS_DE_DOCUMENTO)
    numero_documento = forms.CharField(label="Número de documento", max_length=20)


class VincularPersonaForm(forms.Form):
    persona = forms.UUIDField(widget=forms.HiddenInput)
    rol = forms.ChoiceField(label="Rol en el conjunto", choices=ROLES_DE_CONJUNTO)


class UsuarioForm(forms.Form):
    rol = forms.ChoiceField(label="Rol en el conjunto", choices=ROLES_DE_CONJUNTO)
    tipo_documento = forms.ChoiceField(label="Tipo de documento", choices=TIPOS_DE_DOCUMENTO)
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
