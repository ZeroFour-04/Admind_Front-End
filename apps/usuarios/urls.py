from django.urls import path

from apps.usuarios import views

app_name = "usuarios"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("registrar/", views.registrar, name="registrar"),
    path("<uuid:usuario_id>/eliminar/", views.eliminar, name="eliminar"),
    path("<uuid:usuario_id>/", views.detalle, name="detalle"),
    path("<uuid:usuario_id>/roles/", views.asignar_rol, name="asignar-rol"),
    path("<uuid:usuario_id>/roles/<uuid:asignacion_id>/retirar/", views.retirar_rol, name="retirar-rol"),
]
