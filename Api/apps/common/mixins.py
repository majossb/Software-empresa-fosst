from django.utils import timezone
from rest_framework import viewsets

from apps.accounts.models import UserRole


class EmpresaScopedViewSet(viewsets.ModelViewSet):
    """
    Base para TODOS los ViewSets de módulos de negocio.

    - Filtra automáticamente por la empresa del usuario autenticado (multi-tenant):
      un RESPONSABLE o AUDITOR solo ve los datos de su propia empresa.
    - Un ADMIN (superadmin) ve todo, o puede filtrar por ?empresa_id=... si lo necesita.
    - Al crear, asigna la empresa del usuario automáticamente (el cliente no
      puede "crear" datos para otra empresa aunque lo intente en el payload).
    - Si el modelo tiene `deleted_at`, el `destroy()` hace soft-delete en vez
      de borrar la fila (igual que ya hacía tu backend con `deleted_at`).
    """
    empresa_field = "empresa"  # nombre del campo FK a Empresa en el modelo
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs.model, "deleted_at"):
            qs = qs.filter(**{"deleted_at__isnull": True})

        user = self.request.user
        if user.rol == UserRole.ADMIN:
            empresa_id = self.request.query_params.get("empresa_id")
            return qs.filter(**{f"{self.empresa_field}_id": empresa_id}) if empresa_id else qs
        return qs.filter(**{self.empresa_field: user.empresa})

    def perform_create(self, serializer):
        user = self.request.user
        if self.empresa_field in [f.name for f in serializer.Meta.model._meta.fields]:
            serializer.save(**{self.empresa_field: user.empresa})
        else:
            serializer.save()

    def perform_destroy(self, instance):
        if hasattr(instance, "deleted_at"):
            instance.deleted_at = timezone.now()
            instance.save(update_fields=["deleted_at"])
        else:
            instance.delete()
