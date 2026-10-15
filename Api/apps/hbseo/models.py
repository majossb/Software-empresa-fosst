"""
HBSEO — Modelos del Historial de Brechas, Subsanaciones y Evolución Organizacional.

Diseño (§7.1 de la especificación):
  - Brecha: registro central, recibe de TODOS los módulos (SST, MICHC, Formación, etc.)
  - BrechaOrigen: tabla puente N:M via GenericFK — una brecha puede tener múltiples orígenes
  - BrechaEvento: línea de tiempo (trazabilidad)
  - BrechaAccion: próximas acciones programadas

RN-16: Toda brecha requiere al menos un BrechaOrigen con referencia trazable.
RN-17: Todo cambio de estado genera un BrechaEvento.
"""
import uuid
from datetime import datetime

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Brecha(models.Model):
    """
    Registro central del HBSEO. Cada brecha es una condición detectada que requiere
    seguimiento hasta su cierre.

    Las brechas se crean exclusivamente via hbseo.services.registrar_o_vincular_brecha(),
    nunca por endpoint directo — esto garantiza trazabilidad (RN-16).
    """

    class Clasificacion(models.TextChoices):
        INCUMPLIMIENTO = "incumplimiento", "Incumplimiento"
        RESTRICCION = "restriccion", "Restricción"
        OBSERVACION = "observacion", "Observación"
        HALLAZGO = "hallazgo", "Hallazgo"
        OPORTUNIDAD_MEJORA = "oportunidad_mejora", "Oportunidad de mejora"
        NO_CONFORMIDAD = "no_conformidad", "No conformidad"
        RIESGO_EMERGENTE = "riesgo_emergente", "Riesgo emergente"

    class Estado(models.TextChoices):
        DETECTADA = "detectada", "Detectada"
        EN_TRATAMIENTO = "en_tratamiento", "En tratamiento"
        CONTROLADA = "controlada", "Controlada"
        SUBSANADA = "subsanada", "Subsanada"
        CERRADA = "cerrada", "Cerrada"

    class NivelAtencion(models.TextChoices):
        BAJO = "bajo", "Bajo"
        MEDIO = "medio", "Medio"
        ALTO = "alto", "Alto"
        CRITICO = "critico", "Crítico"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(
        max_length=20, unique=True, editable=False,
        help_text="Código auto-generado: BR-YYYY-NNNNNN",
    )
    empresa = models.ForeignKey(
        "empresas.Empresa", on_delete=models.CASCADE, related_name="brechas",
    )
    sede = models.ForeignKey(
        "organizacion.Sede", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="brechas",
    )
    proceso = models.ForeignKey(
        "organizacion.Proceso", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="brechas",
    )
    area = models.CharField(max_length=255, blank=True)
    # FK al trabajador afectado (si aplica) — facilita búsqueda de brechas por trabajador
    # y deduplicación (misma condición + mismo trabajador = misma brecha).
    trabajador = models.ForeignKey(
        "capacitaciones.Trabajador", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="brechas",
    )

    clasificacion = models.CharField(max_length=30, choices=Clasificacion.choices)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DETECTADA)
    detectado_por = models.CharField(
        max_length=255,
        help_text="Usuario o 'sistema' + nombre del motor (ej. 'Sistema (MICHC)')",
    )
    fecha_deteccion = models.DateTimeField(auto_now_add=True)

    # Textos generados por IA (inmutables una vez generados — §8)
    descripcion_automatica = models.TextField(
        blank=True,
        help_text="Generada por IA — qué ocurrió / dónde / qué requisito afecta",
    )
    interpretacion_ia = models.TextField(blank=True)
    recomendacion_automatica = models.TextField(blank=True)

    # Texto editable por el usuario — separado del generado por IA (§8)
    descripcion_complementaria = models.TextField(
        blank=True,
        help_text="Editable por la empresa — complementa la descripción automática",
    )

    nivel_atencion = models.CharField(
        max_length=10, choices=NivelAtencion.choices, default=NivelAtencion.MEDIO,
    )
    responsable_seguimiento = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="brechas_asignadas",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "brechas"
        ordering = ["-fecha_deteccion"]
        indexes = [
            models.Index(fields=["empresa", "estado"]),
            models.Index(fields=["empresa", "clasificacion"]),
            models.Index(fields=["trabajador", "estado"]),
        ]

    def __str__(self):
        return f"{self.codigo} — {self.get_clasificacion_display()} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = self._generar_codigo()
        super().save(*args, **kwargs)

    def _generar_codigo(self):
        """Genera código secuencial: BR-YYYY-NNNNNN."""
        year = datetime.now().year
        prefix = f"BR-{year}-"
        ultimo = (
            Brecha.objects.filter(codigo__startswith=prefix)
            .order_by("-codigo")
            .values_list("codigo", flat=True)
            .first()
        )
        if ultimo:
            try:
                seq = int(ultimo.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:06d}"


class BrechaOrigen(models.Model):
    """
    Tabla puente N:M entre Brecha y los registros que la originan.

    Usa GenericForeignKey para apuntar a cualquier modelo del sistema
    (EvaluacionHabilitacion, Hallazgo, EvaluacionCompetencia, ExamenMedico, etc.).

    RN-16: Toda brecha DEBE tener al menos un BrechaOrigen con referencia válida.
    """

    class ModuloOrigen(models.TextChoices):
        GESTION_HUMANA = "gestion_humana", "Gestión Humana"
        MICHC = "michc", "MICHC"
        FORMACION = "formacion", "Formación y Desarrollo"
        SST = "sst", "SST"
        PESV = "pesv", "PESV"
        AMBIENTAL = "ambiental", "Gestión Ambiental"
        AUDITORIAS = "auditorias", "Auditorías"
        INDICADORES = "indicadores", "Indicadores"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brecha = models.ForeignKey(Brecha, on_delete=models.CASCADE, related_name="origenes")
    modulo_origen = models.CharField(max_length=30, choices=ModuloOrigen.choices)

    # GenericForeignKey — referencia al registro real que originó la brecha
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=255)  # UUID como string
    referencia = GenericForeignKey("content_type", "object_id")

    es_origen_principal = models.BooleanField(
        default=False,
        help_text="Cuál de los orígenes fue el que disparó la creación de la brecha",
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción del aporte de este origen a la brecha",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "brecha_origenes"
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def __str__(self):
        return f"Origen {self.get_modulo_origen_display()} → {self.brecha.codigo}"


class BrechaEvento(models.Model):
    """
    Línea de tiempo de la brecha — "Trazabilidad de la Brecha" en el prototipo.

    RN-17: Todo cambio de estado genera automáticamente un BrechaEvento
    (implementado via signal post_save en Brecha).
    """

    class TipoEvento(models.TextChoices):
        DETECCION = "deteccion", "Detección"
        DESCRIPCION_REGISTRADA = "descripcion_registrada", "Descripción registrada"
        MEDIDA_CONTROL = "medida_control", "Medida de control"
        CAMBIO_ESTADO = "cambio_estado", "Cambio de estado"
        PROXIMA_ACCION = "proxima_accion", "Próxima acción"
        ORIGEN_VINCULADO = "origen_vinculado", "Origen vinculado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brecha = models.ForeignKey(Brecha, on_delete=models.CASCADE, related_name="eventos")
    tipo_evento = models.CharField(max_length=30, choices=TipoEvento.choices)
    descripcion = models.TextField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="eventos_brecha",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "brecha_eventos"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.brecha.codigo} — {self.get_tipo_evento_display()} ({self.created_at})"


class BrechaAccion(models.Model):
    """Panel "Próximas acciones" del prototipo."""

    class Estado(models.TextChoices):
        PROGRAMADA = "programada", "Programada"
        COMPLETADA = "completada", "Completada"
        VENCIDA = "vencida", "Vencida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brecha = models.ForeignKey(Brecha, on_delete=models.CASCADE, related_name="acciones")
    descripcion = models.TextField()
    fecha_programada = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADA)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "brecha_acciones"
        ordering = ["fecha_programada"]

    def __str__(self):
        return f"{self.brecha.codigo} — {self.descripcion[:50]} ({self.get_estado_display()})"
