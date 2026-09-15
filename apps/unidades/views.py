from django.shortcuts import render


def lista(request):
    """Maqueta de apartamentos y parqueaderos. Sin datos: muestra su estado vacío."""
    return render(request, "unidades/lista.html")
