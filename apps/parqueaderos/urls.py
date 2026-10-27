from django.urls import path

from apps.parqueaderos import views

app_name = "parqueaderos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<uuid:parqueadero_id>/desactivar/", views.desactivar, name="desactivar"),
]
