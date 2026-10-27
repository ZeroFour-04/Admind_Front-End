from django.urls import path

from apps.ingresos import views

app_name = "ingresos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("registrar/", views.registrar, name="registrar"),
    path("<uuid:ingreso_id>/salida/", views.salida, name="salida"),
]
