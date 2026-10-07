import uuid
from django.db import models


class Empresa(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        ACTIVA = "activa", "Activa"
        SUSPENDIDA = "suspendida", "Suspendida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    nit = models.CharField(max_length=30, unique=True)
    num_trabajadores = models.PositiveIntegerField()
    nivel_riesgo = models.PositiveSmallIntegerField()
    capitulo_vigente = models.CharField(max_length=10)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    representante_legal = models.CharField(max_length=255, blank=True)
    arl = models.CharField(max_length=100, blank=True)
    sector_economico = models.CharField(max_length=150, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    logo_url = models.CharField(max_length=500, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    ciiu_codigo = models.CharField(max_length=20, null=True, blank=True)
    ciiu_descripcion = models.TextField(null=True, blank=True)
    ciiu_768_principal = models.CharField(max_length=20, null=True, blank=True)
    ciiu_768_secundarios = models.JSONField(null=True, blank=True)
    ciiu_768_metadata = models.JSONField(null=True, blank=True)
    mision = models.TextField(null=True, blank=True)
    vision = models.TextField(null=True, blank=True)
    valores = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = "empresas"

    def __str__(self):
        return f"{self.nombre} ({self.nit})"


class AuditorEmpresa(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auditor = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.CASCADE,
        related_name="auditorias_asignadas",
        db_column="auditor_id"
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="auditores",
        db_column="empresa_id"
    )
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, default="activo")

    class Meta:
        db_table = "auditores_empresas"

    def __str__(self):
        return f"Auditor {self.auditor} en {self.empresa}"


class SolicitudEliminacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        APROBADA = "aprobada", "Aprobada"
        RECHAZADA = "rechazada", "Rechazada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="solicitudes_eliminacion",
        db_column="empresa_id"
    )
    solicitante = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.CASCADE,
        related_name="solicitudes_creadas",
        db_column="solicitante_id"
    )
    aprobador = models.ForeignKey(
        "accounts.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="solicitudes_aprobadas",
        db_column="aprobador_id"
    )
    tabla = models.CharField(max_length=100)
    registro_id = models.CharField(max_length=100)
    motivo = models.TextField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "solicitudes_eliminacion"

    def __str__(self):
        return f"Eliminación de {self.tabla} ({self.registro_id}) - {self.estado}"


class TransicionCapitulo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="transiciones_capitulo")
    evaluacion = models.ForeignKey("estandares.Evaluacion", on_delete=models.SET_NULL, null=True, blank=True, related_name="transiciones")
    capitulo_anterior = models.CharField(max_length=10)
    capitulo_nuevo = models.CharField(max_length=10)
    usuario = models.ForeignKey("accounts.Usuario", on_delete=models.PROTECT, related_name="transiciones_realizadas")
    motivo = models.TextField(blank=True, default="")
    contexto_anterior = models.JSONField(default=dict)
    contexto_nuevo = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "transiciones_capitulo"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transición {self.capitulo_anterior} -> {self.capitulo_nuevo} ({self.empresa.nombre})"


