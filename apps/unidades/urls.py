from django.urls import path

from apps.unidades import views

app_name = "unidades"

urlpatterns = [
    path("", views.lista, name="lista"),
]
