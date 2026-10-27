from django.urls import path

from apps.paneles import views

app_name = "paneles"

urlpatterns = [
    path("", views.inicio, name="inicio"),
]
