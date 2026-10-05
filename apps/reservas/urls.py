from django.urls import path

from apps.reservas import views

app_name = "reservas"

urlpatterns = [
    path("", views.calendario, name="calendario"),
    path("areas/<uuid:area_id>/solicitudes/", views.solicitudes_area, name="solicitudes-area"),
    path("solicitudes/<uuid:solicitud_id>/decision/", views.decidir, name="decidir"),
    path("tomar/", views.tomar, name="tomar"),
    path("solicitudes/<uuid:solicitud_id>/", views.solicitud, name="solicitud"),
    path("solicitudes/<uuid:solicitud_id>/liberar/", views.liberar, name="liberar"),
    path("solicitudes/<uuid:solicitud_id>/enviar/", views.enviar, name="enviar"),
]
