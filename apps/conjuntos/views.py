from django.shortcuts import render

# Maqueta: cuando se conecte, la lista sale de GET /auth/conjuntos/ y elegir llama a
# POST /auth/conjunto-activo/ (HU-26).
CONJUNTOS_DE_EJEMPLO = [
    {"nombre": "Conjunto Residencial Altos de Manablanca", "direccion": "Calle 9 # 4-50, Facatativá"},
    {"nombre": "Conjunto Residencial Villa del Rosario", "direccion": "Carrera 2 # 15-30, Facatativá"},
]


def selector(request):
    return render(request, "conjuntos/selector.html", {"conjuntos": CONJUNTOS_DE_EJEMPLO})
