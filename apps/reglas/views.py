from datetime import date

from django.shortcuts import render

# Maqueta: tipos tomados del catálogo de reglas beta del maestro §5.10, con valores de ejemplo.
REGLAS_DE_EJEMPLO = [
    {"tipo": "Anticipación máxima", "area": "Salón comunal", "valor": "60 días", "desde": date(2026, 9, 1)},
    {"tipo": "Duración máxima", "area": "Salón comunal", "valor": "6 horas", "desde": date(2026, 9, 1)},
    {"tipo": "Cupo por unidad", "area": "Salón comunal", "valor": "2 reservas cada 30 días", "desde": date(2026, 9, 1)},
    {"tipo": "Aforo", "area": "Piscina", "valor": "25 personas", "desde": date(2026, 9, 7)},
    {"tipo": "Franja horaria permitida", "area": "Gimnasio", "valor": "De 5:00 a. m. a 10:00 p. m.", "desde": date(2026, 9, 7)},
]


def lista(request):
    return render(request, "reglas/lista.html", {"reglas": REGLAS_DE_EJEMPLO})
