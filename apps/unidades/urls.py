from django.urls import path

from apps.unidades import views

app_name = "unidades"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("agrupacion/<uuid:agrupacion_id>/", views.viviendas_de_agrupacion, name="agrupacion"),
    path("sin-agrupar/", views.viviendas_de_agrupacion, name="sin-agrupar"),
    path("<uuid:unidad_id>/", views.detalle, name="detalle"),
    path("<uuid:unidad_id>/vinculos/<uuid:vinculo_id>/cerrar/", views.cerrar_vinculo, name="cerrar-vinculo"),
    path("<uuid:unidad_id>/residentes/", views.crear_residente, name="crear-residente"),
]
