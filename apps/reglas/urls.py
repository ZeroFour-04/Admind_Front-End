from django.urls import path

from apps.reglas import views

app_name = "reglas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nueva/", views.nueva, name="nueva"),
    path("nueva/<str:tipo>/", views.nueva_tipo, name="nueva-tipo"),
    path("<uuid:regla_id>/editar/", views.editar, name="editar"),
    path("<uuid:regla_id>/retirar/", views.retirar, name="retirar"),
]
