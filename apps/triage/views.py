from django.shortcuts import render


def bandeja(request):
    """Maqueta de la bandeja de solicitudes (HU-22). Sin datos: muestra su estado vacío."""
    return render(request, "triage/bandeja.html")
