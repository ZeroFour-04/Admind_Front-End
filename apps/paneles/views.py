from django.shortcuts import render


def inicio(request):
    """Maqueta del inicio de Administración. Las teselas llegan cuando existan los módulos que las alimentan."""
    return render(request, "paneles/inicio.html")
