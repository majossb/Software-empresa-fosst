"""
Modelos de Reclutamiento y Selección — FOSST V.I.D.A.
Fases A, B y C: Banco de Talento, Candidato, PerfilCandidato, FuenteReclutamiento,
Vacante, ProcesoSeleccion, Postulacion, PostulacionEvento, Entrevista, Evaluacion,
ValidacionDocumental, CandidatoDocumento, TokenAccesoCandidato.
"""
import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class FuenteReclutamiento(models.Model):
    """
    Catálogo configurable de fuentes de atracción de talento por empresa.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="fuentes_reclutamiento",
    )
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, default="")
    activo = models.BooleanField(default=True)
    es_sistema = models.BooleanField(default=False, help_text="Valores semilla por defecto")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_fuentes"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "nombre"],
                name="unique_fuente_nombre_por_empresa",
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre})"


class Candidato(models.Model):
    """
    Persona física registrada en el Banco de Talento de la empresa (RN-R10).
    Registro único por empresa independiente de las postulaciones que realice.
    """
    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de Ciudadanía"
        CE = "CE", "Cédula de Extranjería"
        PA = "PA", "Pasaporte"
        PEP = "PEP", "Permiso Especial de Permanencia"
        PPT = "PPT", "Permiso por Protección Temporal"
        OTRO = "OTRO", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="candidatos",
    )
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.CC,
    )
    documento = models.CharField(max_length=50)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    email = models.EmailField()
    telefono = models.CharField(max_length=50, blank=True, default="")
    ciudad = models.CharField(max_length=100, blank=True, default="")
    direccion = models.CharField(max_length=255, blank=True, default="")
    fuente_reclutamiento = models.ForeignKey(
        FuenteReclutamiento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="candidatos",
    )
    fuente_detalle = models.CharField(max_length=255, blank=True, default="")
    autoriza_tratamiento_datos = models.BooleanField(
        default=False,
        help_text="Consentimiento de Habeas Data según Ley 1581 de 2012",
    )
    fecha_autorizacion_datos = models.DateTimeField(null=True, blank=True)
    etiquetas = models.JSONField(default=list, blank=True, help_text="Etiquetas de habilidades/búsqueda")
    notas_internas = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reclutamiento_candidatos"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "tipo_documento", "documento"],
                condition=Q(deleted_at__isnull=True),
                name="unique_candidato_documento_empresa",
            ),
            models.UniqueConstraint(
                fields=["empresa", "email"],
                condition=Q(deleted_at__isnull=True),
                name="unique_candidato_email_empresa",
            ),
        ]

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return f"{self.nombre_completo} ({self.tipo_documento} {self.documento})"


class PerfilCandidato(models.Model):
    """
    Datos estructurados de trayectoria profesional, formación y competencias del candidato.
    """
    class NivelEducativo(models.TextChoices):
        PRIMARIA = "primaria", "Primaria"
        BACHILLERATO = "bachillerato", "Bachillerato / Secundaria"
        TECNICO = "tecnico", "Técnico Laboral / Profesional"
        TECNOLOGO = "tecnologo", "Tecnólogo"
        UNIVERSITARIO = "universitario", "Profesional / Universitario"
        ESPECIALIZACION = "especializacion", "Especialización"
        MAESTRIA = "maestria", "Maestría"
        DOCTORADO = "doctorado", "Doctorado"
        OTRO = "otro", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidato = models.OneToOneField(
        Candidato,
        on_delete=models.CASCADE,
        related_name="perfil",
    )
    titulo_profesional = models.CharField(max_length=255, blank=True, default="")
    nivel_educativo = models.CharField(
        max_length=50,
        choices=NivelEducativo.choices,
        blank=True,
        default="",
    )
    resumen_profesional = models.TextField(blank=True, default="")
    anios_experiencia = models.DecimalField(max_digits=4, decimal_places=1, default=0.0)
    experiencia_laboral = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de objetos: {empresa, cargo, fecha_inicio, fecha_fin, actual, funciones}",
    )
    formacion_academica = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de objetos: {institucion, titulo, nivel, anio_graduacion, en_curso}",
    )
    certificaciones = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de certificaciones y licencias (p. ej. Alturas, SST, CONTE)",
    )
    competencias = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de competencias técnicas y blandas",
    )
    aspiracion_salarial = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    disponibilidad_viaje = models.BooleanField(default=False)
    disponibilidad_traslado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_perfiles_candidato"

    def __str__(self):
        return f"Perfil de {self.candidato.nombre_completo}"


class Vacante(models.Model):
    """
    Requerimiento / necesidad de personal ligada a un PerfilCargo (Módulo 1) y Sede.
    """
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        ABIERTA = "abierta", "Abierta / Publicada"
        PAUSADA = "pausada", "Pausada"
        CERRADA = "cerrada", "Cerrada"
        CUBIERTA = "cubierta", "Cubierta"

    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        REMOTA = "remoto", "Remoto"
        HIBRIDA = "hibrido", "Híbrido"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="vacantes",
    )
    perfil_cargo = models.ForeignKey(
        "perfilcargo.PerfilCargo",
        on_delete=models.CASCADE,
        related_name="vacantes",
    )
    sede = models.ForeignKey(
        "organizacion.Sede",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vacantes",
    )
    codigo = models.CharField(max_length=50, unique=True, editable=False)
    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    descripcion_publica = models.TextField(blank=True, default="")
    numero_cupos = models.PositiveIntegerField(default=1)
    numero_seleccionados = models.PositiveIntegerField(default=0)
    tipo_contrato = models.CharField(max_length=100, blank=True, default="")
    modalidad = models.CharField(
        max_length=30,
        choices=Modalidad.choices,
        default=Modalidad.PRESENCIAL,
    )
    rango_salarial_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    rango_salarial_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    mostrar_salario_publico = models.BooleanField(default=True)
    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    fecha_apertura = models.DateField(null=True, blank=True)
    fecha_cierre_estimada = models.DateField(null=True, blank=True)
    fecha_cierre_real = models.DateField(null=True, blank=True)
    publicada_en_portal = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reclutamiento_vacantes"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.codigo:
            anio = timezone.now().year
            count = Vacante.objects.filter(empresa=self.empresa, created_at__year=anio).count() + 1
            self.codigo = f"VAC-{anio}-{count:04d}"
        if not self.slug:
            base_slug = slugify(f"{self.titulo}-{self.codigo}")
            self.slug = base_slug
        super().save(*args, **kwargs)

    @property
    def cupos_disponibles(self):
        return max(0, self.numero_cupos - self.numero_seleccionados)

    @property
    def esta_cubierta(self):
        return self.numero_seleccionados >= self.numero_cupos

    def __str__(self):
        return f"{self.codigo} — {self.titulo} ({self.get_estado_display()})"


class ProcesoSeleccion(models.Model):
    """
    Contenedor de la convocatoria concreta para una Vacante.
    Configura las etapas obligatorias y criterios de evaluación.
    """
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        EN_PAUSA = "en_pausa", "En Pausa"
        FINALIZADO = "finalizado", "Finalizado"
        CANCELADO = "cancelado", "Cancelado"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="procesos_seleccion",
    )
    vacante = models.OneToOneField(
        Vacante,
        on_delete=models.CASCADE,
        related_name="proceso_seleccion",
    )
    codigo = models.CharField(max_length=50, unique=True, editable=False)
    responsable_rh = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="procesos_seleccion_liderados",
    )
    requiere_entrevista = models.BooleanField(
        default=True,
        help_text="RN-R03: Etapa de entrevista obligatoria para este proceso",
    )
    requiere_evaluacion = models.BooleanField(
        default=True,
        help_text="RN-R03: Etapa de evaluación técnica/psicotécnica obligatoria",
    )
    requiere_validacion_documental = models.BooleanField(
        default=True,
        help_text="RN-R03: Etapa de validación documental y de referencias obligatoria",
    )
    requisitos_obligatorios = models.JSONField(
        default=list,
        blank=True,
        help_text="Requisitos excluyentes tomados del PerfilCargo o definidos en la convocatoria",
    )
    requisitos_deseables = models.JSONField(
        default=list,
        blank=True,
        help_text="Requisitos adicionales valorables",
    )
    criterios_evaluacion = models.JSONField(
        default=dict,
        blank=True,
        help_text="Pesos o escalas de calificación por etapa",
    )
    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.ACTIVO,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_procesos_seleccion"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.codigo:
            anio = timezone.now().year
            count = ProcesoSeleccion.objects.filter(empresa=self.empresa, created_at__year=anio).count() + 1
            self.codigo = f"PROC-{anio}-{count:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} — {self.vacante.titulo}"


class Postulacion(models.Model):
    """
    Relación viva entre un Candidato y un ProcesoSeleccion.
    El estado pertenece a la Postulación, nunca al Candidato.
    Transiciones controladas exclusivamente via services.postulacion (RN-R01).
    """
    class Estado(models.TextChoices):
        POSTULADO = "postulado", "Postulado"
        EN_REVISION = "en_revision", "En Revisión"
        PRESELECCIONADO = "preseleccionado", "Preseleccionado"
        EN_ENTREVISTA = "en_entrevista", "En Entrevista"
        EN_EVALUACION = "en_evaluacion", "En Evaluación"
        EN_VALIDACION = "en_validacion", "En Validación Documental"
        SELECCIONADO = "seleccionado", "Seleccionado"
        NO_SELECCIONADO = "no_seleccionado", "No Seleccionado"
        RETIRO_CANDIDATURA = "retiro_candidatura", "Retiro de Candidatura"
        NO_CONTINUO = "no_continuo", "No Continuó en Proceso"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="postulaciones",
    )
    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name="postulaciones",
    )
    proceso_seleccion = models.ForeignKey(
        ProcesoSeleccion,
        on_delete=models.CASCADE,
        related_name="postulaciones",
    )
    estado = models.CharField(
        max_length=30,
        choices=Estado.choices,
        default=Estado.POSTULADO,
        db_index=True,
    )
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    puntuacion_general = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Calificación global ponderada sobre 100",
    )
    calificacion_requisitos = models.JSONField(
        default=dict,
        blank=True,
        help_text="Cumplimiento detallado de requisitos obligatorios y deseables",
    )
    etapas_completadas = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de etapas superadas (entrevista, evaluacion, validacion_documental)",
    )
    motivo_cierre = models.TextField(
        blank=True,
        default="",
        help_text="RN-R04: Motivo obligatorio para estados de cierre",
    )
    es_excepcion = models.BooleanField(
        default=False,
        help_text="RN-R09: Si la transición actual fue autorizada por excepción",
    )
    justificacion_excepcion = models.TextField(blank=True, default="")
    autorizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="postulaciones_autorizadas",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "reclutamiento_postulaciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["proceso_seleccion", "candidato"],
                condition=Q(deleted_at__isnull=True),
                name="unique_postulacion_candidato_proceso",
            )
        ]

    @property
    def es_activa(self):
        return self.estado not in [
            self.Estado.SELECCIONADO,
            self.Estado.NO_SELECCIONADO,
            self.Estado.RETIRO_CANDIDATURA,
            self.Estado.NO_CONTINUO,
        ]

    def __str__(self):
        return f"{self.candidato.nombre_completo} → {self.proceso_seleccion.vacante.titulo} [{self.get_estado_display()}]"


class PostulacionEvento(models.Model):
    """
    Línea de tiempo inmutable de trazabilidad de cada transición de estado (RN-R08).
    Sigue el patrón de hbseo.BrechaEvento y AuditLog.
    """
    class TipoEvento(models.TextChoices):
        POSTULACION_REGISTRADA = "postulacion_registrada", "Postulación Registrada"
        CAMBIO_ESTADO = "cambio_estado", "Cambio de Estado"
        EVALUACION_REQUISITOS = "evaluacion_requisitos", "Evaluación de Requisitos"
        ENTREVISTA_REGISTRADA = "entrevista_registrada", "Entrevista Registrada"
        PRUEBA_REGISTRADA = "prueba_registrada", "Prueba / Evaluación Registrada"
        VALIDACION_REGISTRADA = "validacion_registrada", "Validación Documental Registrada"
        DECISION_SELECCION = "decision_seleccion", "Decisión Final de Selección"
        CIERRE_POSTULACION = "cierre_postulacion", "Cierre de Postulación"
        REAPERTURA_EXCEPCIONAL = "reapertura_excepcional", "Reapertura Excepcional"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    tipo_evento = models.CharField(
        max_length=40,
        choices=TipoEvento.choices,
        default=TipoEvento.CAMBIO_ESTADO,
    )
    estado_anterior = models.CharField(max_length=30, blank=True, default="")
    estado_nuevo = models.CharField(max_length=30)
    descripcion = models.TextField()
    motivo = models.TextField(blank=True, default="")
    es_excepcion = models.BooleanField(default=False)
    justificacion_excepcion = models.TextField(blank=True, default="")
    datos_capturados = models.JSONField(default=dict, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_postulacion",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reclutamiento_postulacion_eventos"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.postulacion.candidato.nombre_completo}: {self.estado_anterior} → {self.estado_nuevo} ({self.created_at})"


class Entrevista(models.Model):
    """
    Subordinada a Postulacion: Registro y calificación de entrevistas realizadas en el proceso.
    """
    class TipoEntrevista(models.TextChoices):
        INICIAL_RH = "inicial_rh", "Inicial / Recursos Humanos"
        TECNICA = "tecnica", "Técnica / Competencias"
        JEFE_INMEDIATO = "jefe_inmediato", "Jefe Inmediato"
        GERENCIAL = "gerencial", "Gerencial / Alta Dirección"
        OTRA = "otra", "Otra"

    class Modalidad(models.TextChoices):
        PRESENCIAL = "presencial", "Presencial"
        VIRTUAL = "virtual", "Virtual / Videollamada"
        TELEFONICA = "telefonica", "Telefónica"

    class Estado(models.TextChoices):
        PROGRAMADA = "programada", "Programada"
        REALIZADA = "realizada", "Realizada"
        CANCELADA = "cancelada", "Cancelada"
        REPROGRAMADA = "reprogramada", "Reprogramada"
        NO_ASISTIO = "no_asistio", "No Asistió"

    class Concepto(models.TextChoices):
        FAVORABLE = "favorable", "Favorable / Aprobado"
        DESFAVORABLE = "desfavorable", "Desfavorable / No Aprobado"
        CON_RESERVAS = "con_reservas", "Favorable con Reservas"
        PENDIENTE = "pendiente", "Pendiente de Concepto"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="entrevistas_candidatos",
    )
    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="entrevistas",
    )
    tipo_entrevista = models.CharField(
        max_length=30,
        choices=TipoEntrevista.choices,
        default=TipoEntrevista.INICIAL_RH,
    )
    modalidad = models.CharField(
        max_length=20,
        choices=Modalidad.choices,
        default=Modalidad.VIRTUAL,
    )
    fecha_programada = models.DateTimeField()
    entrevistador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entrevistas_asignadas",
    )
    enlace_reunion = models.URLField(blank=True, default="")
    lugar = models.CharField(max_length=255, blank=True, default="")
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROGRAMADA,
    )
    calificacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Puntuación obtenida sobre 100",
    )
    concepto = models.CharField(
        max_length=20,
        choices=Concepto.choices,
        default=Concepto.PENDIENTE,
    )
    observaciones = models.TextField(blank=True, default="")
    aspectos_evaluados = models.JSONField(
        default=dict,
        blank=True,
        help_text="Evaluación por competencias: {liderazgo: 4, comunicacion: 5, etc.}",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_entrevistas"
        ordering = ["-fecha_programada"]

    def __str__(self):
        return f"{self.get_tipo_entrevista_display()} — {self.postulacion.candidato.nombre_completo} ({self.get_estado_display()})"


class Evaluacion(models.Model):
    """
    Subordinada a Postulacion: Pruebas técnicas, psicotécnicas, operativas y médicas aplicadas.
    """
    class TipoEvaluacion(models.TextChoices):
        TECNICA = "tecnica", "Prueba Técnica / Conocimientos"
        PSICOTECNICA = "psicotecnica", "Prueba Psicotécnica"
        CONOCIMIENTOS_SST = "conocimientos_sst", "Evaluación Específica SST / GTC 45"
        OPERATIVA_PRACTICA = "operativa_practica", "Prueba Práctica / Operativa"
        MEDICA_PREINGRESO = "medica_preingreso", "Concepto Médico Preingreso"
        OTRA = "otra", "Otra Prueba"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente / Asignada"
        EN_CURSO = "en_curso", "En Curso"
        APROBADA = "aprobada", "Aprobada"
        NO_APROBADA = "no_aprobada", "No Aprobada"
        ANULADA = "anulada", "Anulada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="evaluaciones_candidatos",
    )
    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="evaluaciones",
    )
    tipo_evaluacion = models.CharField(
        max_length=30,
        choices=TipoEvaluacion.choices,
        default=TipoEvaluacion.TECNICA,
    )
    nombre_prueba = models.CharField(max_length=255)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_realizacion = models.DateTimeField(null=True, blank=True)
    evaluador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluaciones_a_cargo",
    )
    puntaje_obtenido = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    puntaje_maximo = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.0,
    )
    porcentaje_aprobacion = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.0,
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    concepto = models.TextField(blank=True, default="")
    archivo_informe = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluaciones_informe",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_evaluaciones"
        ordering = ["-created_at"]

    @property
    def porcentaje_obtenido(self):
        if self.puntaje_obtenido is not None and self.puntaje_maximo > 0:
            return round((self.puntaje_obtenido / self.puntaje_maximo) * 100, 2)
        return None

    def __str__(self):
        return f"{self.nombre_prueba} — {self.postulacion.candidato.nombre_completo} ({self.get_estado_display()})"


class ValidacionDocumental(models.Model):
    """
    Subordinada a Postulacion: Verificación de referencias laborales, títulos y certificaciones.
    """
    class TipoVerificacion(models.TextChoices):
        REFERENCIA_LABORAL = "referencia_laboral", "Referencia Laboral"
        REFERENCIA_PERSONAL = "referencia_personal", "Referencia Personal"
        TITULO_ACADEMICO = "titulo_academico", "Título Académico"
        LICENCIA_CONDUCCION = "licencia_conduccion", "Licencia de Conducción (RUNT)"
        LICENCIA_SST = "licencia_sst", "Licencia SST (Secretaría de Salud)"
        CERTIFICACION_ALTURAS = "certificacion_alturas", "Certificación Alturas (MinTrabajo)"
        ANTECEDENTES = "antecedentes", "Antecedentes Judiciales / Procuraduría / Contraloría"
        OTRO = "otro", "Otro Documento"

    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        VERIFICADO_CONFORME = "verificado_conforme", "Verificado Conforme / Válido"
        VERIFICADO_CON_INCONSISTENCIAS = "verificado_con_inconsistencias", "Con Inconsistencias"
        NO_PUDO_VERIFICARSE = "no_pudo_verificarse", "No Pudo Verificarse"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey(
        "empresas.Empresa",
        on_delete=models.CASCADE,
        related_name="validaciones_documentales_candidatos",
    )
    postulacion = models.ForeignKey(
        Postulacion,
        on_delete=models.CASCADE,
        related_name="validaciones_documentales",
    )
    tipo_verificacion = models.CharField(
        max_length=40,
        choices=TipoVerificacion.choices,
        default=TipoVerificacion.REFERENCIA_LABORAL,
    )
    entidad_o_contacto = models.CharField(max_length=255)
    telefono_contacto = models.CharField(max_length=50, blank=True, default="")
    verificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validaciones_realizadas",
    )
    fecha_verificacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=35,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
    )
    detalles_verificacion = models.TextField(blank=True, default="")
    soporte_archivo = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="validaciones_soporte",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reclutamiento_validaciones_documentales"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_tipo_verificacion_display()} — {self.entidad_o_contacto} ({self.get_estado_display()})"


class CandidatoDocumento(models.Model):
    """
    Tabla puente que asocia documentos del candidato reutilizando el modelo Archivo (evidencias).
    """
    class TipoDocumento(models.TextChoices):
        HOJA_DE_VIDA = "hoja_de_vida", "Hoja de Vida"
        CERTIFICACION_LABORAL = "certificacion_laboral", "Certificación Laboral"
        CERTIFICACION_ACADEMICA = "certificacion_academica", "Certificación Académica"
        LICENCIA_CONDUCCION = "licencia_conduccion", "Licencia de Conducción"
        LICENCIA_SST = "licencia_sst", "Licencia SST"
        CERTIFICACION_ALTURAS = "certificacion_alturas", "Certificación Trabajo en Alturas"
        CEDULA = "cedula", "Documento de Identidad"
        OTRO = "otro", "Otro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name="documentos",
    )
    archivo = models.ForeignKey(
        "evidencias.Archivo",
        on_delete=models.CASCADE,
        related_name="documentos_candidato",
    )
    tipo_documento = models.CharField(
        max_length=50,
        choices=TipoDocumento.choices,
        default=TipoDocumento.HOJA_DE_VIDA,
    )
    nombre_descriptivo = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reclutamiento_candidatos_documentos"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_tipo_documento_display()} — {self.candidato.nombre_completo}"


class TokenAccesoCandidato(models.Model):
    """
    Token criptográfico / OTP para acceso passwordless al portal del candidato (Opción A).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    candidato = models.ForeignKey(
        Candidato,
        on_delete=models.CASCADE,
        related_name="tokens_acceso",
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    codigo_otp = models.CharField(max_length=6, blank=True, default="")
    expira_en = models.DateTimeField()
    usado = models.BooleanField(default=False)
    ip_solicitud = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reclutamiento_tokens_candidato"
        ordering = ["-created_at"]

    def esta_vigente(self):
        return not self.usado and timezone.now() <= self.expira_en

    def __str__(self):
        return f"Token para {self.candidato.email} (Vigente: {self.esta_vigente()})"


class AsignacionRolProceso(models.Model):
    """
    Asignación de roles funcionales específicos por Proceso de Selección (MODULOS v02 §2.1):
    - SELECCIONADOR: Gestiona vacante, preselección, validaciones y decisión final.
    - ENTREVISTADOR: Programación y diligenciamiento de entrevistas asignadas.
    - EVALUADOR: Asignación y registro de evaluaciones/pruebas asignadas.
    - ADMIN: Acceso completo y control de excepciones/reapertura.
    """
    class RolReclutamiento(models.TextChoices):
        SELECCIONADOR = "seleccionador", "Seleccionador / RH"
        ENTREVISTADOR = "entrevistador", "Entrevistador"
        EVALUADOR = "evaluador", "Evaluador"
        ADMIN = "admin", "Administrador de Selección"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    proceso_seleccion = models.ForeignKey(
        ProcesoSeleccion,
        on_delete=models.CASCADE,
        related_name="asignaciones_rol",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roles_reclutamiento",
    )
    rol = models.CharField(max_length=30, choices=RolReclutamiento.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reclutamiento_asignaciones_rol"
        unique_together = [("proceso_seleccion", "usuario", "rol")]

    def __str__(self):
        return f"{self.usuario} — {self.get_rol_display()} en {self.proceso_seleccion.codigo}"

