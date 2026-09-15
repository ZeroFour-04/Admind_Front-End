from django.urls import path

from apps.cuentas import views

app_name = "cuentas"

urlpatterns = [
    path("", views.ingreso, name="ingreso"),
    path("salir/", views.salir, name="salir"),
    path("recuperar-contrasena/", views.recuperar_contrasena, name="recuperar-contrasena"),
]
