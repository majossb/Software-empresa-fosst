import uuid
from django.conf import settings
from django.db import models


class Informe(models.Model):
    class Tipo(models.TextChoices):
        AUDITORIA = "auditoria", "Auditoría"
        REVISION_ALTA_DIRECCION = "revision_alta_direccion", "Revisión por la alta dirección"
        EJECUTIVO = "ejecutivo", "Ejecutivo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    evaluacion = models.ForeignKey("estandares.Evaluacion", on_delete=models.CASCADE, related_name="informes")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    contenido_json = models.JSONField(null=True, blank=True)
    fecha_elaboracion = models.DateTimeField(auto_now_add=True)

    # Trazabilidad de Firma Responsable SST
    firmado_responsable = models.BooleanField(default=False)
    firma_responsable_data = models.TextField(null=True, blank=True, help_text="Imagen base64 de la firma gráfica")
    firma_responsable_fecha = models.DateTimeField(null=True, blank=True)
    firma_responsable_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="informes_firmados_responsable"
    )

    # Trazabilidad de Firma Alta Dirección
    firmado_direccion = models.BooleanField(default=False)
    firma_direccion_data = models.TextField(null=True, blank=True, help_text="Imagen base64 de la firma gráfica")
    firma_direccion_fecha = models.DateTimeField(null=True, blank=True)
    firma_direccion_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="informes_firmados_direccion"
    )

    hash_documento = models.CharField(max_length=64, null=True, blank=True, help_text="Hash SHA-256 del documento firmado")
    archivo = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="informes"
    )
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "informes"
