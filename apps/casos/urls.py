from django.urls import path

from apps.casos import views

app_name = "casos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<uuid:caso_id>/", views.detalle, name="detalle"),
    path("<uuid:caso_id>/fotos/<uuid:foto_id>/", views.foto, name="foto"),
    # tomar, prioridad, redirigir, descartar, responder o rechazar: las mismas palabras que usa la API.
    path("<uuid:caso_id>/<slug:accion>/", views.gestionar, name="gestionar"),
]
