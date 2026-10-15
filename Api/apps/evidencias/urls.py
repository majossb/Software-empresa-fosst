from django.urls import path
from .views import (
    EvidenciaListCreateView,
    EvidenciaDeleteView,
    EvidenciaVerificarIntegridadView
)

urlpatterns = [
    path("evidencias/", EvidenciaListCreateView.as_view(), name="evidencia-list-create"),
    path("evidencias/<uuid:evidencia_id>", EvidenciaDeleteView.as_view(), name="evidencia-delete"),
    path("evidencias/<uuid:evidencia_id>/verificar-integridad", EvidenciaVerificarIntegridadView.as_view(), name="evidencia-verificar-integridad"),
]
