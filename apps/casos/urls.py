from django.urls import path

from apps.casos import views

app_name = "casos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<uuid:caso_id>/rechazar/", views.rechazar, name="rechazar"),
    path("<uuid:caso_id>/redirigir/", views.redirigir, name="redirigir"),
    path("<uuid:caso_id>/fotos/<uuid:foto_id>/", views.foto, name="foto"),
]
