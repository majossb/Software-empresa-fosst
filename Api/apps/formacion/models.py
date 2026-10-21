"""
Modelos de Formación y Desarrollo — Matriz de Competencias del Cargo (MCC) — §9.

- EvaluacionCompetencia: registro de evaluación periódica del nivel alcanzado
  por un trabajador en una competencia específica del cargo (Nivel 1 a 4).
  Calcula automáticamente la brecha respecto al nivel requerido.
"""
import uuid
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.common.competencias import NIVEL_MINIMO, NIVEL_MAXIMO


class EvaluacionCompetencia(models.Model):
    class MetodoEvaluacion(models.TextChoices):
        OBSERVACION = "observacion_directa", "Observación Directa en Puesto"
        PRUEBA_TECNICA = "prueba_tecnica", "Prueba Técnica / Conocimiento"
        EVALUACION_360 = "evaluacion_360", "Evaluación 360° / Jefe Directo"
        CERTIFICACION = "certificacion", "Certificación / Título Acreditado"
        ENTREVISTA = "entrevista", "Entrevista por Competencias"
        AUTOEVALUACION = "autoevaluacion", "Autoevaluación"

    class RolEvaluador(models.TextChoices):
        GESTION_HUMANA = "gestion_humana", "Gestión Humana"
        JEFE_INMEDIATO = "jefe_inmediato", "Jefe inmediato"
        AUTOEVALUACION = "autoevaluacion", "Autoevaluación"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador",
        on_delete=models.CASCADE,
        related_name="evaluaciones_competencias"
    )
    cargo_competencia = models.ForeignKey(
        "perfilcargo.CargoCompetencia",
        on_delete=models.CASCADE,
        related_name="evaluaciones"
    )
    nivel_alcanzado = models.IntegerField(
        validators=[MinValueValidator(NIVEL_MINIMO), MaxValueValidator(NIVEL_MAXIMO)],
        help_text="Nivel alcanzado (1: Básico, 2: En desarrollo, 3: Autónomo, 4: Dominio avanzado, 5: Referente)"
    )
    brecha_calculada = models.IntegerField(
        default=0,
        help_text="Brecha negativa (Nivel Requerido - Nivel Alcanzado). 0 si cumple o supera."
    )
    evaluado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competencias_evaluadas"
    )
    rol_evaluador = models.CharField(
        max_length=30,
        choices=RolEvaluador.choices,
        default=RolEvaluador.GESTION_HUMANA,
        help_text="Rol con el cual se realizó la evaluación"
    )
    fecha_evaluacion = models.DateField()
    metodo = models.CharField(
        max_length=40,
        choices=MetodoEvaluacion.choices,
        default=MetodoEvaluacion.EVALUACION_360
    )
    observacion = models.TextField(blank=True, null=True)
    soporte_archivo = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluaciones_competencias"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "evaluaciones_competencias_mcc"
        ordering = ["-fecha_evaluacion", "-created_at"]
        indexes = [
            models.Index(fields=["trabajador", "fecha_evaluacion"]),
            models.Index(fields=["cargo_competencia", "nivel_alcanzado"]),
        ]

    def __str__(self):
        req = self.cargo_competencia.nivel_requerido or self.cargo_competencia.nivel or 1
        return f"{self.trabajador.nombre} — {self.cargo_competencia.nombre} (Req: L{req} / Alc: L{self.nivel_alcanzado})"

    def save(self, *args, **kwargs):
        # Calcular brecha automáticamente
        req = self.cargo_competencia.nivel_requerido or self.cargo_competencia.nivel or 1
        self.brecha_calculada = max(0, req - self.nivel_alcanzado)
        super().save(*args, **kwargs)


class CursoFormacion(models.Model):
    """
    Catálogo de formación y certificaciones de la empresa.
    """
    class Categoria(models.TextChoices):
        SST = "sst", "SST"
        VIAL = "vial", "Seguridad Vial"
        TECNICA = "tecnica", "Técnica"
        BRIGADA = "brigada", "Brigada de Emergencia"
        OTRA = "otra", "Otra"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="cursos_formacion"
    )
    nombre = models.CharField(max_length=255)
    categoria = models.CharField(
        max_length=30,
        choices=Categoria.choices,
        default=Categoria.SST
    )
    vigencia_meses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Vigencia estándar en meses (nula si el certificado no vence)"
    )
    requiere_certificado = models.BooleanField(
        default=True,
        help_text="Indica si se exige adjuntar soporte o certificado"
    )
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cursos_formacion"
        ordering = ["categoria", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["empresa", "nombre"], name="uq_curso_formacion_empresa_nombre")
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_categoria_display()})"


class CargoRequisitoFormacion(models.Model):
    """
    Requisito de formación y certificación asociado al perfil de un cargo.
    Extensión del Perfil del Cargo (§9).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(
        "perfilcargo.PerfilCargo",
        on_delete=models.CASCADE,
        related_name="requisitos_formacion"
    )
    curso = models.ForeignKey(
        CursoFormacion,
        on_delete=models.CASCADE,
        related_name="requisitos_cargo"
    )
    obligatorio = models.BooleanField(
        default=True,
        help_text="Indica si este curso es obligatorio para ejercer el cargo"
    )
    vigencia_meses = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Vigencia exigida por el cargo en meses (hereda la del catálogo, editable)"
    )
    grupo_alternativo = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Identificador de alternativas (ej. 'sst_responsable'). Cumplir cualquiera del grupo basta."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cargo_requisitos_formacion"
        constraints = [
            models.UniqueConstraint(fields=["perfil_cargo", "curso"], name="uq_cargo_requisito_formacion")
        ]
        ordering = ["-obligatorio", "curso__nombre"]

    def __str__(self):
        return f"{self.perfil_cargo.nombre_cargo} -> {self.curso.nombre} ({'Obligatorio' if self.obligatorio else 'Opcional'})"

    def save(self, *args, **kwargs):
        # Heredar vigencia del curso si no se especificó una propia del cargo
        if self.vigencia_meses is None and self.curso and self.curso.vigencia_meses is not None:
            self.vigencia_meses = self.curso.vigencia_meses
        super().save(*args, **kwargs)


class RegistroFormacion(models.Model):
    """
    Registro individual de un curso o certificación realizado por un trabajador.
    """
    class Origen(models.TextChoices):
        CAPACITACION_INTERNA = "capacitacion_interna", "Capacitación interna"
        PROVEEDOR_EXTERNO = "proveedor_externo", "Proveedor externo"
        CARGA_MANUAL = "carga_manual", "Carga manual"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador",
        on_delete=models.CASCADE,
        related_name="registros_formacion"
    )
    curso = models.ForeignKey(
        CursoFormacion,
        on_delete=models.CASCADE,
        related_name="registros_trabajadores"
    )
    fecha_realizacion = models.DateField()
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de vencimiento calculada o definida manualmente"
    )
    soporte = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registros_formacion"
    )
    origen = models.CharField(
        max_length=30,
        choices=Origen.choices,
        default=Origen.CARGA_MANUAL
    )
    entidad_emisora = models.CharField(max_length=200, blank=True, null=True)
    horas_duracion = models.PositiveIntegerField(null=True, blank=True)
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "registros_formacion_trabajador"
        ordering = ["-fecha_realizacion", "-created_at"]
        indexes = [
            models.Index(fields=["trabajador", "curso"]),
            models.Index(fields=["fecha_vencimiento"]),
        ]

    def __str__(self):
        return f"{self.trabajador.nombre} — {self.curso.nombre} ({self.fecha_realizacion})"

    def save(self, *args, **kwargs):
        # Auto-cálculo de fecha_vencimiento si no se especificó
        if not self.fecha_vencimiento and self.fecha_realizacion:
            vigencia = None
            if self.trabajador and self.trabajador.perfil_cargo:
                req = CargoRequisitoFormacion.objects.filter(
                    perfil_cargo=self.trabajador.perfil_cargo,
                    curso=self.curso
                ).first()
                if req and req.vigencia_meses is not None:
                    vigencia = req.vigencia_meses
            if vigencia is None and self.curso and self.curso.vigencia_meses is not None:
                vigencia = self.curso.vigencia_meses

            if vigencia:
                from dateutil.relativedelta import relativedelta
                self.fecha_vencimiento = self.fecha_realizacion + relativedelta(months=vigencia)
        super().save(*args, **kwargs)

    @property
    def estado_derivado(self):
        """Estado derivado: vigente / por_vencer / vencido."""
        if not self.fecha_vencimiento:
            return "vigente"
        from django.utils import timezone
        from datetime import timedelta
        today = timezone.now().date()
        if self.fecha_vencimiento < today:
            return "vencido"
        if self.fecha_vencimiento <= today + timedelta(days=30):
            return "por_vencer"
        return "vigente"

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        from django.utils import timezone
        today = timezone.now().date()
        return (self.fecha_vencimiento - today).days


def poblar_catalogo_formacion_semilla(empresa):
    """
    Crea el catálogo semilla de formación para una empresa si aún no existe.
    Semilla definida según especificación:
    - Trabajo seguro en alturas (técnica, 12 meses)
    - Curso SST 50 horas (SST, 36 meses)
    - Curso SST 20 horas (SST, 36 meses)
    - Manejo defensivo (vial, 24 meses)
    - Primeros auxilios (brigada, 12 meses)
    - Brigadas de emergencia (brigada, 12 meses)
    - Auditor interno (otra, no vence)
    - Curso PESV (vial, 24 meses)
    """
    cursos_semilla = [
        {"nombre": "Trabajo seguro en alturas", "categoria": CursoFormacion.Categoria.TECNICA, "vigencia_meses": 12, "requiere_certificado": True},
        {"nombre": "Curso SST 50 horas", "categoria": CursoFormacion.Categoria.SST, "vigencia_meses": 36, "requiere_certificado": True},
        {"nombre": "Curso SST 20 horas", "categoria": CursoFormacion.Categoria.SST, "vigencia_meses": 36, "requiere_certificado": True},
        {"nombre": "Manejo defensivo", "categoria": CursoFormacion.Categoria.VIAL, "vigencia_meses": 24, "requiere_certificado": True},
        {"nombre": "Primeros auxilios", "categoria": CursoFormacion.Categoria.BRIGADA, "vigencia_meses": 12, "requiere_certificado": True},
        {"nombre": "Brigadas de emergencia", "categoria": CursoFormacion.Categoria.BRIGADA, "vigencia_meses": 12, "requiere_certificado": True},
        {"nombre": "Auditor interno", "categoria": CursoFormacion.Categoria.OTRA, "vigencia_meses": None, "requiere_certificado": True},
        {"nombre": "Curso PESV", "categoria": CursoFormacion.Categoria.VIAL, "vigencia_meses": 24, "requiere_certificado": True},
    ]
    creados = []
    for item in cursos_semilla:
        curso, created = CursoFormacion.objects.get_or_create(
            empresa=empresa,
            nombre=item["nombre"],
            defaults=item
        )
        if created:
            creados.append(curso)
    return creados
