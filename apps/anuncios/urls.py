from django.urls import path

from apps.anuncios import views

app_name = "anuncios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<uuid:anuncio_id>/editar/", views.editar, name="editar"),
]
