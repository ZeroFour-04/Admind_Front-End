from django.urls import include, path

urlpatterns = [
    path("", include("apps.cuentas.urls")),
    path("conjuntos/", include("apps.conjuntos.urls")),
    path("inicio/", include("apps.paneles.urls")),
    path("reservas/", include("apps.reservas.urls")),
    path("reglas/", include("apps.reglas.urls")),
    path("anuncios/", include("apps.anuncios.urls")),
    path("areas/", include("apps.areas.urls")),
    path("notificaciones/", include("apps.notificaciones.urls")),
    path("solicitudes/", include("apps.triage.urls")),
    path("unidades/", include("apps.unidades.urls")),
    path("usuarios/", include("apps.usuarios.urls")),
    path("visitantes/", include("apps.visitantes.urls")),
]
