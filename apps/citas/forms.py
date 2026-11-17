from django import forms


DIAS = (
    (0, "Lunes"),
    (1, "Martes"),
    (2, "Miércoles"),
    (3, "Jueves"),
    (4, "Viernes"),
    (5, "Sábado"),
    (6, "Domingo"),
)
MODOS = (
    ("lunes_viernes", "Mismo horario de lunes a viernes"),
    ("rango", "Mismo horario en un rango de días"),
    ("por_dia", "Configurar un horario diferente para cada día"),
)


def campo_de_hora():
    return forms.TimeField(
        required=False,
        input_formats=["%H:%M"],
        widget=forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
    )


class HorarioCitasForm(forms.Form):
    modo = forms.ChoiceField(
        label="Cómo quieres definir el horario",
        choices=MODOS,
        widget=forms.RadioSelect,
    )
    dia_inicio = forms.ChoiceField(label="Desde", choices=DIAS, required=False)
    dia_fin = forms.ChoiceField(label="Hasta", choices=DIAS, required=False)
    hora_inicio = campo_de_hora()
    hora_inicio.label = "Abre"
    hora_fin = campo_de_hora()
    hora_fin.label = "Cierra"
    descanso_inicio = campo_de_hora()
    descanso_inicio.label = "Inicio del almuerzo o descanso"
    descanso_fin = campo_de_hora()
    descanso_fin.label = "Fin del almuerzo o descanso"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for dia, nombre in DIAS:
            self.fields[f"dia_{dia}_activo"] = forms.BooleanField(
                label=f"{nombre}: atiende",
                required=False,
            )
            for campo, etiqueta in (
                ("hora_inicio", "Abre"),
                ("hora_fin", "Cierra"),
                ("descanso_inicio", "Inicio de almuerzo o descanso"),
                ("descanso_fin", "Fin de almuerzo o descanso"),
            ):
                self.fields[f"dia_{dia}_{campo}"] = campo_de_hora()
                self.fields[f"dia_{dia}_{campo}"].label = etiqueta

    def clean(self):
        datos = super().clean()
        modo = datos.get("modo")
        if modo in ("lunes_viernes", "rango"):
            self._validar_horario(
                datos,
                "hora_inicio",
                "hora_fin",
                "descanso_inicio",
                "descanso_fin",
            )
        if modo == "rango":
            if not datos.get("dia_inicio"):
                self.add_error("dia_inicio", "Elige el primer día del rango.")
            if not datos.get("dia_fin"):
                self.add_error("dia_fin", "Elige el último día del rango.")
            if datos.get("dia_inicio") and datos.get("dia_fin") and int(datos["dia_inicio"]) > int(datos["dia_fin"]):
                self.add_error("dia_fin", "El día final debe ser igual o posterior al inicial.")
        if modo == "por_dia":
            for dia, _ in DIAS:
                if datos.get(f"dia_{dia}_activo"):
                    self._validar_horario(
                        datos,
                        f"dia_{dia}_hora_inicio",
                        f"dia_{dia}_hora_fin",
                        f"dia_{dia}_descanso_inicio",
                        f"dia_{dia}_descanso_fin",
                    )
        return datos

    def _validar_horario(self, datos, inicio_key, fin_key, descanso_inicio_key, descanso_fin_key):
        inicio = datos.get(inicio_key)
        fin = datos.get(fin_key)
        descanso_inicio = datos.get(descanso_inicio_key)
        descanso_fin = datos.get(descanso_fin_key)

        if inicio is None:
            self.add_error(inicio_key, "Indica a qué hora empieza la atención.")
        if fin is None:
            self.add_error(fin_key, "Indica a qué hora termina la atención.")
        if inicio is not None and fin is not None and inicio >= fin:
            self.add_error(fin_key, "La hora de cierre debe ser posterior a la de inicio.")
        if (descanso_inicio is None) != (descanso_fin is None):
            self.add_error(
                descanso_inicio_key if descanso_inicio is None else descanso_fin_key,
                "Indica las dos horas del descanso o deja ambas vacías.",
            )
        if inicio is not None and fin is not None and descanso_inicio is not None and descanso_fin is not None:
            if descanso_inicio < inicio or descanso_fin > fin or descanso_inicio >= descanso_fin:
                self.add_error(descanso_fin_key, "El descanso debe quedar dentro del horario de atención.")

    def horario_para_api(self):
        datos = self.cleaned_data
        if datos["modo"] == "por_dia":
            dias = []
            for dia, _ in DIAS:
                activo = datos[f"dia_{dia}_activo"]
                dias.append({
                    "dia": dia,
                    "activo": activo,
                    "hora_inicio": self._hora(datos, f"dia_{dia}_hora_inicio") if activo else None,
                    "hora_fin": self._hora(datos, f"dia_{dia}_hora_fin") if activo else None,
                    "descanso_inicio": self._hora(datos, f"dia_{dia}_descanso_inicio") if activo else None,
                    "descanso_fin": self._hora(datos, f"dia_{dia}_descanso_fin") if activo else None,
                })
            return {"dias": dias}

        if datos["modo"] == "lunes_viernes":
            dias_activos = range(5)
        else:
            dias_activos = range(int(datos["dia_inicio"]), int(datos["dia_fin"]) + 1)
        inicio = datos["hora_inicio"].strftime("%H:%M")
        fin = datos["hora_fin"].strftime("%H:%M")
        descanso_inicio = self._hora(datos, "descanso_inicio")
        descanso_fin = self._hora(datos, "descanso_fin")
        dias = [
            {
                "dia": dia,
                "activo": dia in dias_activos,
                "hora_inicio": inicio if dia in dias_activos else None,
                "hora_fin": fin if dia in dias_activos else None,
                "descanso_inicio": descanso_inicio if dia in dias_activos else None,
                "descanso_fin": descanso_fin if dia in dias_activos else None,
            }
            for dia, _ in DIAS
        ]
        return {"dias": dias}

    @staticmethod
    def _hora(datos, campo):
        return datos[campo].strftime("%H:%M") if datos.get(campo) else None
