from django.urls import path

from apps.reservas import views

app_name = "reservas"

urlpatterns = [
    path("", views.calendario, name="calendario"),
]
