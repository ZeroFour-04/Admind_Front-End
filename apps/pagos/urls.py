from django.urls import path

from apps.pagos import views

app_name = "pagos"

urlpatterns = [
    path("administracion/", views.administracion, name="administracion"),
    path("administracion/comprobantes/<uuid:comprobante_id>/", views.comprobante, name="comprobante"),
    path("administracion/<uuid:unidad_id>/<str:periodo>/confirmar/", views.confirmar, name="confirmar"),
]
