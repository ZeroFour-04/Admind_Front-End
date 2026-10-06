from django.urls import path

from apps.reglas import views

app_name = "reglas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("definir/<str:tipo>/", views.definir, name="definir"),
    path("<uuid:regla_id>/editar/", views.editar, name="editar"),
    path("<uuid:regla_id>/retirar/", views.retirar, name="retirar"),
    path("dias/<uuid:area_id>/agregar/", views.agregar_dia, name="agregar-dia"),
    path("<uuid:regla_id>/dias/<int:indice>/quitar/", views.quitar_dia, name="quitar-dia"),
]
