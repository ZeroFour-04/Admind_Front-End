from django.urls import path

from apps.unidades import views

app_name = "unidades"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<uuid:unidad_id>/", views.detalle, name="detalle"),
    path("<uuid:unidad_id>/vinculos/<uuid:vinculo_id>/cerrar/", views.cerrar_vinculo, name="cerrar-vinculo"),
]
