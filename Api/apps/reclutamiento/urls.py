"""
Rutas URL para el módulo de Reclutamiento y Selección — FOSST V.I.D.A.
Fase D: Endpoints REST para RH y Administración.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.reclutamiento.views import (
    FuenteReclutamientoViewSet,
    CandidatoViewSet,
    VacanteViewSet,
    ProcesoSeleccionViewSet,
    PostulacionViewSet,
    EntrevistaViewSet,
    EvaluacionViewSet,
    ValidacionDocumentalViewSet,
)

from apps.reclutamiento.portal_views import (
    VacantesPublicasListView,
    VacantePublicaDetailView,
    PostularPublicamenteView,
    SolicitarAccesoOTPView,
    VerificarOTPView,
    MisPostulacionesView,
    RetirarPostulacionView,
    MiPerfilCandidatoView,
    PostularRapidoView,
    BuscarPerfilPrevioView,
)

router = DefaultRouter()
router.register(r"fuentes", FuenteReclutamientoViewSet, basename="reclutamiento-fuente")
router.register(r"candidatos", CandidatoViewSet, basename="reclutamiento-candidato")
router.register(r"vacantes", VacanteViewSet, basename="reclutamiento-vacante")
router.register(r"procesos", ProcesoSeleccionViewSet, basename="reclutamiento-proceso")
router.register(r"postulaciones", PostulacionViewSet, basename="reclutamiento-postulacion")
router.register(r"entrevistas", EntrevistaViewSet, basename="reclutamiento-entrevista")
router.register(r"evaluaciones", EvaluacionViewSet, basename="reclutamiento-evaluacion")
router.register(r"validaciones", ValidacionDocumentalViewSet, basename="reclutamiento-validacion")

urlpatterns = [
    # Portal Público del Candidato (Fase E)
    path("portal/vacantes/", VacantesPublicasListView.as_view(), name="portal-vacantes-list"),
    path("portal/vacantes/<str:slug_or_id>/", VacantePublicaDetailView.as_view(), name="portal-vacantes-detail"),
    path("portal/vacantes/<str:slug_or_id>/postular/", PostularPublicamenteView.as_view(), name="portal-vacantes-postular"),
    path("portal/vacantes/<str:slug_or_id>/postular-rapido/", PostularRapidoView.as_view(), name="portal-vacantes-postular-rapido"),
    path("portal/auth/solicitar-acceso/", SolicitarAccesoOTPView.as_view(), name="portal-solicitar-acceso"),
    path("portal/auth/verificar-otp/", VerificarOTPView.as_view(), name="portal-verificar-otp"),
    path("portal/auth/buscar-perfil-previo/", BuscarPerfilPrevioView.as_view(), name="portal-buscar-perfil-previo"),
    path("portal/mi-perfil/", MiPerfilCandidatoView.as_view(), name="portal-mi-perfil"),
    path("portal/mis-postulaciones/", MisPostulacionesView.as_view(), name="portal-mis-postulaciones"),
    path("portal/mis-postulaciones/<uuid:pk>/retirar/", RetirarPostulacionView.as_view(), name="portal-retirar-postulacion"),

    # Endpoints Internos RH (Fase D)
    path("", include(router.urls)),
]
