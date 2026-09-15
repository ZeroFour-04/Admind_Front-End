from django.urls import include, path

urlpatterns = [
    path("", include("apps.cuentas.urls")),
    path("conjuntos/", include("apps.conjuntos.urls")),
    path("inicio/", include("apps.paneles.urls")),
    path("reservas/", include("apps.reservas.urls")),
    path("reglas/", include("apps.reglas.urls")),
    path("anuncios/", include("apps.anuncios.urls")),
    path("solicitudes/", include("apps.triage.urls")),
    path("unidades/", include("apps.unidades.urls")),
]
