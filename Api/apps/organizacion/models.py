import uuid
from django.core.exceptions import ValidationError
from django.db import models


class Sede(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="sedes")
    nombre = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=30, blank=True, null=True)
    responsable = models.CharField(max_length=150, blank=True, null=True)
    es_principal = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "sedes"

    def __str__(self):
        return f"{self.nombre} ({self.ciudad})"


class NodoOrganigrama(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="organigrama")
    nombre_cargo = models.CharField(max_length=150)
    area = models.CharField(max_length=150, blank=True, null=True)
    nivel = models.IntegerField()
    padre = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="hijos")
    perfil_cargo = models.ForeignKey(
        "perfilcargo.PerfilCargo", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="nodos_organigrama",
    )
    orden = models.IntegerField(default=0)
    pos_x = models.FloatField(null=True, blank=True)
    pos_y = models.FloatField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nodos_organigrama"
        ordering = ["nivel", "orden"]


def normalizar_texto(texto: str) -> str:
    """Normaliza texto eliminando acentos, espacios extra y pasando a minúsculas."""
    if not texto:
        return ""
    import unicodedata
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    return " ".join(sin_tildes.lower().strip().split())


class Proceso(models.Model):
    class Tipo(models.TextChoices):
        ESTRATEGICO = "estrategico", "Estratégico"
        MISIONAL = "misional", "Misional"
        APOYO = "apoyo", "Apoyo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="procesos")
    nombre = models.CharField(max_length=150)
    nombre_normalizado = models.CharField(max_length=150, blank=True, default="", db_index=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subprocesos")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "procesos"
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo", "nombre_normalizado"],
                condition=models.Q(padre__isnull=True),
                name="unique_proceso_raiz_empresa_tipo_nombre",
            ),
            models.UniqueConstraint(
                fields=["empresa", "tipo", "padre", "nombre_normalizado"],
                condition=models.Q(padre__isnull=False),
                name="unique_subproceso_empresa_tipo_padre_nombre",
            ),
        ]

    def clean(self):
        super().clean()
        if self.nombre and self.empresa_id:
            norm = normalizar_texto(self.nombre)
            qs = Proceso.objects.filter(
                empresa_id=self.empresa_id,
                tipo=self.tipo,
                padre_id=self.padre_id,
                nombre_normalizado=norm,
            )
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "nombre": "Ya existe un proceso con este nombre para la misma categoría y nivel."
                })

    def save(self, *args, **kwargs):
        self.nombre_normalizado = normalizar_texto(self.nombre)
        super().save(*args, **kwargs)
