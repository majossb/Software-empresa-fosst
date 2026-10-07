import uuid
from django.db import models
from apps.common.models import SoftDeleteModel


class Archivo(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    url = models.URLField()
    tipo_mime = models.CharField(max_length=100)
    tamanio_kb = models.IntegerField()
    subido_por = models.CharField(max_length=150)
    sha256_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "archivos"


class Evidencia(SoftDeleteModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    respuesta = models.ForeignKey("estandares.Respuesta", on_delete=models.CASCADE, related_name="evidencias")
    archivo = models.ForeignKey(Archivo, on_delete=models.CASCADE, related_name="evidencias")
    descripcion = models.TextField(blank=True, null=True)
    fecha_ocurrencia = models.DateTimeField(null=True, blank=True)
    responsable = models.CharField(max_length=150, blank=True, null=True)
    firma = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "evidencias"
