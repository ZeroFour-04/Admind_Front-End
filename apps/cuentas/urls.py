from django.urls import path

from apps.cuentas import views

app_name = "cuentas"

urlpatterns = [
    path("", views.ingreso, name="ingreso"),
    path("salir/", views.salir, name="salir"),
    path("perfil/", views.perfil, name="perfil"),
    path("recuperar-contrasena/", views.recuperar_contrasena, name="recuperar-contrasena"),
    path(
        "restablecer-contrasena/<str:uid>/<str:token>/",
        views.restablecer_contrasena,
        name="restablecer-contrasena",
    ),
    path("segundo-factor/configurar/", views.configurar_segundo_factor, name="configurar-segundo-factor"),
    path("segundo-factor/verificar/", views.verificar_segundo_factor, name="verificar-segundo-factor"),
    path("segundo-factor/continuar/", views.continuar, name="continuar"),
]
