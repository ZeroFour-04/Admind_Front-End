from django.urls import path

from apps.reportes import views

app_name = "reportes"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("zonas.pdf", views.descargar_zonas, name="zonas"),
    path("pagos.xlsx", views.descargar_pagos, name="pagos"),
]
