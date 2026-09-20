from django.urls import path

from apps.usuarios import views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<uuid:usuario_id>/", views.detalle, name="detalle"),
]
