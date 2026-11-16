from django.urls import path

from apps.infracciones import views

app_name = "infracciones"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nueva/", views.nueva, name="nueva"),
    path("<uuid:registro_id>/", views.detalle, name="detalle"),
    path("<uuid:registro_id>/cierre/", views.cerrar, name="cerrar"),
    path("<uuid:registro_id>/anulacion/", views.anular, name="anular"),
]
