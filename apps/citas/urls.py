from django.urls import path

from apps.citas import views

app_name = "citas"

urlpatterns = [
    path("", views.horario, name="horario"),
    path("agenda/", views.agenda, name="agenda"),
]
