import uuid
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
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "nodos_organigrama"
        ordering = ["nivel", "orden"]


class Proceso(models.Model):
    class Tipo(models.TextChoices):
        ESTRATEGICO = "estrategico", "Estratégico"
        MISIONAL = "misional", "Misional"
        APOYO = "apoyo", "Apoyo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="procesos")
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descripcion = models.TextField(blank=True, null=True)
    padre = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="subprocesos")
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "procesos"
