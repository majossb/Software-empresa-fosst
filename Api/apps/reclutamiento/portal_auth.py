"""
Autenticación y Permisos para el Portal del Candidato — FOSST V.I.D.A.
Fase E: Autenticación por token de portador (Bearer / X-Candidate-Token).
"""
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission

from apps.reclutamiento.models import TokenAccesoCandidato, Candidato


class CandidateTokenAuthentication(BaseAuthentication):
    """
    Autentica solicitudes en los endpoints del portal mediante tokens generados por OTP/Magic Link.
    Soporta Header 'Authorization: Bearer <token>' o 'X-Candidate-Token: <token>'.
    """
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization") or request.headers.get("X-Candidate-Token")
        if not auth_header:
            return None

        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:].strip()
        else:
            token_str = auth_header.strip()

        if not token_str:
            return None

        ahora = timezone.now()
        token_obj = TokenAccesoCandidato.objects.filter(
            token=token_str,
            expira_en__gte=ahora,
        ).select_related("candidato", "candidato__empresa").first()

        if not token_obj:
            raise AuthenticationFailed("Token de acceso de candidato inválido o expirado.")

        # Establece request.candidato para facilitar el acceso en las vistas
        request.candidato = token_obj.candidato
        # Retorna el candidato como principal para que request.user sea el candidato en estos endpoints
        return (token_obj.candidato, token_obj)


class IsAuthenticatedCandidate(BasePermission):
    """
    Permite acceso solo a candidatos autenticados mediante CandidateTokenAuthentication.
    """
    def has_permission(self, request, view):
        candidato = getattr(request, "candidato", None)
        if candidato and isinstance(candidato, Candidato):
            return True
        return isinstance(getattr(request, "user", None), Candidato)
