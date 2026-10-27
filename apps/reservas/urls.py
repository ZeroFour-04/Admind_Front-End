from django.urls import path

from apps.reservas import views

app_name = "reservas"

urlpatterns = [
    path("", views.calendario, name="calendario"),
    path("areas/<uuid:area_id>/solicitudes/", views.solicitudes_area, name="solicitudes-area"),
    path("solicitudes/<uuid:solicitud_id>/decision/", views.decidir, name="decidir"),
    path("solicitudes/<uuid:solicitud_id>/descarte/", views.descartar, name="descartar"),
    path("solicitudes/<uuid:solicitud_id>/pago/", views.declarar_pago, name="declarar-pago"),
    path("solicitudes/<uuid:solicitud_id>/pago/retirar/", views.retirar_pago, name="retirar-pago"),
    path("solicitudes/<uuid:solicitud_id>/comprobantes/", views.subir_comprobante, name="subir-comprobante"),
    path("comprobantes/<uuid:comprobante_id>/", views.comprobante, name="comprobante"),
    path("tomar/", views.tomar, name="tomar"),
    path("solicitudes/<uuid:solicitud_id>/", views.solicitud, name="solicitud"),
    path("solicitudes/<uuid:solicitud_id>/liberar/", views.liberar, name="liberar"),
    path("solicitudes/<uuid:solicitud_id>/enviar/", views.enviar, name="enviar"),
]
