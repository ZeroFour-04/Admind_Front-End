from django.urls import path

from apps.reservas import views

app_name = "reservas"

urlpatterns = [
    path("", views.calendario, name="calendario"),
    path("tomar/", views.tomar, name="tomar"),
    path("solicitudes/<uuid:solicitud_id>/", views.solicitud, name="solicitud"),
    path("solicitudes/<uuid:solicitud_id>/liberar/", views.liberar, name="liberar"),
]
