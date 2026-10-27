from django.urls import path

from apps.anuncios import views

app_name = "anuncios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("<uuid:anuncio_id>/editar/", views.editar, name="editar"),
    path("<uuid:anuncio_id>/fotos/<uuid:foto_id>/", views.foto, name="foto"),
]
