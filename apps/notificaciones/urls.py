from django.urls import path

from apps.notificaciones import views

app_name = "notificaciones"

urlpatterns = [
    path("", views.bandeja, name="bandeja"),
]
