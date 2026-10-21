import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Trabajador(models.Model):
    class TipoVinculacion(models.TextChoices):
        DEPENDIENTE = "dependiente", "Dependiente"
        INDEPENDIENTE = "independiente", "Independiente"
        CONTRATISTA = "contratista", "Contratista"

    class TipoContrato(models.TextChoices):
        FIJO = "fijo", "Término fijo"
        INDEFINIDO = "indefinido", "Término indefinido"
        OBRA_LABOR = "obra_labor", "Por obra o labor"
        PRESTACION_SERVICIOS = "prestacion_servicios", "Prestación de servicios"
        APRENDIZAJE = "aprendizaje", "Contrato de aprendizaje"

    class EstadoContractual(models.TextChoices):
        ACTIVO = "activo", "Activo"
        PERIODO_PRUEBA = "periodo_prueba", "Periodo de prueba"
        VACACIONES = "vacaciones", "Vacaciones"
        LICENCIA = "licencia", "Licencia"
        INCAPACIDAD = "incapacidad", "Incapacidad médica"
        SUSPENDIDO = "suspendido", "Suspendido"
        RETIRADO = "retirado", "Retirado"

    class EstadoOperativo(models.TextChoices):
        HABILITADO = "habilitado", "Habilitado"
        RESTRINGIDO = "restringido", "Restringido"
        PENDIENTE_DOCUMENTAL = "pendiente_documental", "Pendiente documental"
        NO_APTO = "no_apto", "No apto"

    class RemuneracionTipo(models.TextChoices):
        SALARIO = "salario", "Salario"
        HONORARIOS = "honorarios", "Honorarios"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="trabajadores")
    sede = models.ForeignKey("organizacion.Sede", on_delete=models.SET_NULL, null=True, blank=True, related_name="trabajadores")
    perfil_cargo = models.ForeignKey(
        "perfilcargo.PerfilCargo", on_delete=models.SET_NULL, null=True, blank=True, related_name="trabajadores"
    )
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trabajador",
        help_text="Usuario del sistema vinculado a este trabajador (opcional)"
    )
    nombre = models.CharField(max_length=150)
    documento = models.CharField(max_length=30)
    tipo_vinculacion = models.CharField(max_length=20, choices=TipoVinculacion.choices)
    cargo = models.CharField(max_length=150, blank=True, null=True)
    fecha_ingreso = models.DateTimeField(null=True, blank=True)

    # --- Fase 3: Vinculación Laboral y Estados Derivados (§5) ---
    tipo_contrato = models.CharField(
        max_length=30, choices=TipoContrato.choices, null=True, blank=True,
    )
    fecha_fin_contrato = models.DateField(null=True, blank=True)
    tiene_prorroga = models.BooleanField(default=False)
    fecha_inicio_prorroga = models.DateField(null=True, blank=True)
    fecha_fin_prorroga = models.DateField(null=True, blank=True)

    # Periodo de prueba
    fecha_inicio_periodo_prueba = models.DateField(null=True, blank=True)
    fecha_fin_periodo_prueba = models.DateField(null=True, blank=True)

    # RN-13: Estados derivados (no editables directamente por API)
    estado_contractual = models.CharField(
        max_length=30, choices=EstadoContractual.choices, default=EstadoContractual.ACTIVO,
        help_text="Derivado automáticamente de NovedadLaboral con jerarquía de precedencia",
    )
    estado_operativo = models.CharField(
        max_length=30, choices=EstadoOperativo.choices, default=EstadoOperativo.PENDIENTE_DOCUMENTAL,
        help_text="Derivado automáticamente de MICHC",
    )

    # Remuneración (RN-12: mismo campo, UI decide label según tipo_contrato)
    remuneracion_monto = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    remuneracion_tipo = models.CharField(
        max_length=20, choices=RemuneracionTipo.choices, default=RemuneracionTipo.SALARIO,
    )
    fecha_retiro = models.DateField(null=True, blank=True)

    activo = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trabajadores"
        constraints = [
            models.UniqueConstraint(fields=["empresa", "documento"], name="uq_trabajador_empresa_documento")
        ]

    def resolver_usuario(self):
        """Retorna el Usuario asociado explícitamente o por coincidencia de documento en la misma empresa."""
        if self.usuario:
            return self.usuario
        from apps.accounts.models import Usuario
        return Usuario.objects.filter(empresa=self.empresa, documento=self.documento, activo=True).first()


class AfiliacionTrabajador(models.Model):
    class Tipo(models.TextChoices):
        EPS = "eps", "EPS"
        ARL = "arl", "ARL"
        PENSION = "pension", "Pensión"
        CAJA = "caja", "Caja de compensación"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="afiliaciones")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    entidad_nombre = models.CharField(max_length=150)
    numero_afiliacion = models.CharField(max_length=50, blank=True, null=True)
    fecha_afiliacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, default="activa")
    archivo = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="afiliaciones"
    )
    fecha_vencimiento = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "afiliaciones_trabajador"


class PlanillaSeguridad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="planillas")
    periodo = models.CharField(max_length=7)  # YYYY-MM
    tipo_carga = models.CharField(max_length=20)  # directa, contratista
    archivo = models.ForeignKey(
        "evidencias.Archivo", on_delete=models.SET_NULL, null=True, blank=True, related_name="planillas"
    )
    monto_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    estado_pago = models.CharField(max_length=20, default="pendiente")
    fecha_pago = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "planillas_seguridad_social"


class Capacitacion(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADA = "programada", "Programada"
        REALIZADA = "realizada", "Realizada"
        CANCELADA = "cancelada", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey("empresas.Empresa", on_delete=models.CASCADE, related_name="capacitaciones")
    tema = models.CharField(max_length=200)
    objetivo = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Objetivo de la capacitación en una línea",
    )
    curso = models.ForeignKey(
        "formacion.CursoFormacion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capacitaciones",
        help_text="Curso del catálogo que cubre esta capacitación (opcional)",
    )
    competencia = models.ForeignKey(
        "perfilcargo.CargoCompetencia",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capacitaciones",
        help_text="Competencia del cargo que desarrolla esta capacitación (opcional)",
    )
    brechas = models.ManyToManyField(
        "hbseo.Brecha",
        blank=True,
        related_name="capacitaciones",
        help_text="Brechas de HBSEO que busca cerrar esta capacitación",
    )
    proveedor = models.CharField(max_length=150, blank=True, null=True)
    fecha = models.DateTimeField()
    horas_duracion = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Horas de duración estimadas o realizadas",
    )
    num_asistentes = models.IntegerField(default=0)
    tiene_certificado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADA)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "capacitaciones"
        ordering = ["-fecha", "-created_at"]

    def __str__(self):
        return f"{self.tema} ({self.get_estado_display()} - {self.fecha.strftime('%Y-%m-%d') if self.fecha else ''})"


class ParticipanteCapacitacion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    capacitacion = models.ForeignKey(Capacitacion, on_delete=models.CASCADE, related_name="participantes")
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name="participaciones")
    asistio = models.BooleanField(default=False)
    certificado_url = models.URLField(blank=True, null=True)
    soporte = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participaciones_capacitacion",
    )
    nota_evaluacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calificación obtenida en evaluación de conocimiento (si aplica)",
    )
    nivel_alcanzado = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Nivel alcanzado en la reevaluación de competencia (1..5)",
    )
    observaciones = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "participantes_capacitacion"
        constraints = [
            models.UniqueConstraint(fields=["capacitacion", "trabajador"], name="uq_participante_capacitacion")
        ]
