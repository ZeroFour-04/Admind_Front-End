from django.urls import path

from apps.areas import views

app_name = "areas"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("reportes/agendas.xlsx", views.reporte_agendas, name="reporte-agendas"),
    path("reportes/uso.pdf", views.reporte_uso, name="reporte-uso"),
    path("nueva/", views.nueva, name="nueva"),
    path("<uuid:area_id>/editar/", views.editar, name="editar"),
    path("<uuid:area_id>/desactivar/", views.desactivar, name="desactivar"),
]
