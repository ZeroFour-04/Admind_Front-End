from django.urls import path

from apps.triage import views

app_name = "triage"

urlpatterns = [
    path("", views.bandeja, name="bandeja"),
]
