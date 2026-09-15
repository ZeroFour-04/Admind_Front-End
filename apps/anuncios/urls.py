from django.urls import path

from apps.anuncios import views

app_name = "anuncios"

urlpatterns = [
    path("", views.lista, name="lista"),
]
