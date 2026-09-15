from django.urls import path

from apps.conjuntos import views

app_name = "conjuntos"

urlpatterns = [
    path("", views.selector, name="selector"),
]
