from django.urls import path

from apps.visitantes import views

app_name = "visitantes"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<uuid:visitante_id>/salida/", views.salida, name="salida"),
]
