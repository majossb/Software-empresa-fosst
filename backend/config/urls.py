from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/empresas/", include("apps.empresas.urls")),
    path("api/empresa/", include("apps.empresas.urls_empresa")),
    path("api/planes/", include("apps.planes.urls")),
    path("api/modulo0/", include("apps.organizacion.urls")),
    path("api/modulo0/", include("apps.empresas.urls_modulo0")),
    path("api/modulo1/", include("apps.perfilcargo.urls")),
    path("api/", include("apps.estandares.urls")),
    path("api/", include("apps.hallazgos.urls")),
    path("api/", include("apps.evidencias.urls")),
    path("api/", include("apps.informes.urls")),
    path("api/dashboard/", include("apps.dashboard.urls")),
    path("api/", include("apps.capacitaciones.urls")),
    path("api/", include("apps.calendario.urls")),
    # Fase 2 — HBSEO
    path("api/hbseo/", include("apps.hbseo.urls")),
    # Fase 3 — Gestión Humana y Motor de Alertas
    path("api/gestion-humana/", include("apps.gestion_humana.urls")),
    path("api/alertas/", include("apps.alertas.urls")),
    # Fase 4 — MICHC
    path("api/michc/", include("apps.michc.urls")),
    # Fase 5 — Formación y Desarrollo (MCC)
    path("api/formacion/", include("apps.formacion.urls")),
    # Módulo — Reclutamiento y Selección
    path("api/reclutamiento/", include("apps.reclutamiento.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

# Servir archivos subidos (incluyendo logotipos)
if settings.DEBUG or not settings.DEBUG: # Servir siempre localmente para desarrollo/pruebas
    import os
    urlpatterns += static("/uploads/", document_root=os.path.join(settings.BASE_DIR, "uploads"))

