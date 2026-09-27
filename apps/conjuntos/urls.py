from django.urls import path, re_path

from apps.reglas import views as vistas_de_reglas

from . import views

app_name = "conjuntos"

urlpatterns = [
    path("", views.selector, name="selector"),
    path("nuevo/", views.nuevo, name="nuevo"),
    path("asistente/datos/", views.datos, name="asistente-datos"),
    path("asistente/administracion/", views.administracion, name="asistente-administracion"),
    path("asistente/areas/", views.areas, name="asistente-areas"),
    # Paso 4: la misma alta de reglas en dos pasos, dentro del asistente (HU-10).
    path("asistente/reglas/", vistas_de_reglas.nueva, {"en_asistente": True}, name="asistente-reglas"),
    path(
        "asistente/reglas/<str:tipo>/",
        vistas_de_reglas.nueva_tipo,
        {"en_asistente": True},
        name="asistente-reglas-tipo",
    ),
    path("asistente/resumen/", views.resumen, name="asistente-resumen"),
    path("identidad/", views.identidad, name="identidad"),
    re_path(r"^logo/(?P<huella>[0-9a-f]{64})/$", views.logo, name="logo"),
]
