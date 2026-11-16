from django.urls import path

from apps.parqueaderos import views

app_name = "parqueaderos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("mios/", views.mios, name="mios"),
    path("<uuid:parqueadero_id>/desactivar/", views.desactivar, name="desactivar"),
    path("<uuid:parqueadero_id>/asignar/", views.asignar, name="asignar"),
    path("<uuid:parqueadero_id>/liberar/", views.liberar, name="liberar"),
    path("<uuid:parqueadero_id>/historial/", views.historial, name="historial"),
]
