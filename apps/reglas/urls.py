from django.urls import path

from apps.reglas import views

app_name = "reglas"

urlpatterns = [
    path("", views.lista, name="lista"),
]
