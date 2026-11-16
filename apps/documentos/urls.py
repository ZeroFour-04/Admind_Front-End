from django.urls import path

from apps.documentos import views

app_name = "documentos"

urlpatterns = [
    path("", views.lista, name="lista"),
    path("<str:tipo>/subir/", views.subir, name="subir"),
    path("<str:tipo>/archivo/", views.archivo, name="archivo"),
    path("<str:tipo>/versiones/", views.versiones, name="versiones"),
    path("<str:tipo>/versiones/<uuid:version_id>/archivo/", views.archivo_de_version, name="archivo-de-version"),
]
