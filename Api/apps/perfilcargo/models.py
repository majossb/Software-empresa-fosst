import uuid
from django.db import models
from django.db.models import JSONField, UniqueConstraint


class NivelCriticidad(models.TextChoices):
    BAJO = "bajo", "Bajo"
    MEDIO = "medio", "Medio"
    ALTO = "alto", "Alto"
    CRITICO = "critico", "Crítico"

class CatalogoEPP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'catalogo_epps'

class CatalogoPeligro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tipo = models.CharField(max_length=255)
    clasificacion = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    epps_sugeridos = models.ManyToManyField(CatalogoEPP, db_table='catalogo_peligro_epps')

    class Meta:
        db_table = 'catalogo_peligros'

class TipoCargo(models.TextChoices):
    ADMINISTRATIVO = "administrativo", "Administrativo"
    OPERATIVO = "operativo", "Operativo"
    APOYO = "apoyo", "De Apoyo"
    OTRO = "otro", "Otros de acuerdo al mapa de procesos"


class PerfilCargo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    empresa = models.ForeignKey('empresas.Empresa', on_delete=models.CASCADE, related_name='perfiles_cargo')
    codigo = models.CharField(max_length=255)
    version_actual = models.IntegerField(default=1)
    nombre_cargo = models.CharField(max_length=255)
    area = models.CharField(max_length=255, null=True, blank=True)
    sede = models.ForeignKey('organizacion.Sede', on_delete=models.SET_NULL, null=True, blank=True)
    nodo_organigrama_id = models.CharField(max_length=255, null=True, blank=True)
    proceso_id = models.CharField(max_length=255, null=True, blank=True)

    # --- Fase 3 Brechas v02 (§1.1) ---
    jefe_inmediato = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinados_directos',
        help_text="Dependencia jerárquica asociada directamente a un perfil de cargo, no a persona (§1.1)"
    )
    tipo_cargo = models.CharField(
        max_length=30,
        choices=TipoCargo.choices,
        default=TipoCargo.OPERATIVO,
        help_text="Clasificación del tipo de cargo según el mapa de procesos (§1.1)"
    )
    cargo_critico = models.BooleanField(
        default=False,
        help_text="Indicador binario de criticidad simple. Se evalúa automáticamente si realiza tareas críticas o hay mayor riesgo."
    )

    nivel_riesgo = models.IntegerField(null=True, blank=True)
    proposito = models.TextField(null=True, blank=True)
    educacion = models.TextField(null=True, blank=True)
    experiencia = models.TextField(null=True, blank=True)
    formacion = models.TextField(null=True, blank=True)
    habilidades = models.TextField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # --- Fase 1: criticidad multidimensional (§4.1 — un macro-indicador por dimensión, no uno solo) ---
    criticidad_sst = models.CharField(max_length=20, choices=NivelCriticidad.choices, default=NivelCriticidad.BAJO)
    criticidad_operacional = models.CharField(max_length=20, choices=NivelCriticidad.choices, default=NivelCriticidad.BAJO)
    criticidad_vial = models.CharField(max_length=20, choices=NivelCriticidad.choices, default=NivelCriticidad.BAJO)
    criticidad_ambiental = models.CharField(max_length=20, choices=NivelCriticidad.choices, default=NivelCriticidad.BAJO)
    criticidad_estrategica = models.CharField(max_length=20, choices=NivelCriticidad.choices, default=NivelCriticidad.BAJO)

    # --- Fase 1: suplencia e impacto/naturaleza del cargo (§4.1) ---
    requiere_suplencia = models.BooleanField(default=False)
    impacto_descripcion = models.TextField(null=True, blank=True)
    naturaleza_descripcion = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perfiles_cargo'
        constraints = [
            UniqueConstraint(fields=['empresa', 'codigo'], name='unique_perfil_cargo_codigo')
        ]

class CargoVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='versiones')
    numero_version = models.IntegerField()
    snapshot = JSONField()
    motivo_cambio = models.TextField(null=True, blank=True)
    creado_por = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cargo_versiones'

class CargoFuncion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='funciones')
    descripcion = models.TextField()
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = 'cargo_funciones'

class CargoResponsabilidad(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='responsabilidades')
    descripcion = models.TextField()
    orden = models.IntegerField(default=0)

    class Meta:
        db_table = 'cargo_responsabilidades'

class CargoCompetencia(models.Model):
    class Tipo(models.TextChoices):
        TECNICA = "tecnica", "Técnica"
        BLANDA = "blanda", "Blanda"
        ORGANIZACIONAL = "organizacional", "Organizacional"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='competencias')
    nombre = models.CharField(max_length=255)
    # Campo legado (texto libre) — se conserva por compatibilidad con datos existentes.
    # El requerimiento nuevo se captura en `tipo` + `nivel_requerido` (§4.1, base de la MCC en §9).
    nivel = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, null=True, blank=True)
    nivel_requerido = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="1=Básico, 2=Intermedio, 3=Avanzado, 4=Experto"
    )

    class Meta:
        db_table = 'cargo_competencias'

class CargoIndicador(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='indicadores')
    descripcion = models.TextField()
    meta = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'cargo_indicadores'

class CargoPeligro(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='peligros')
    catalogo_peligro = models.ForeignKey(CatalogoPeligro, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_personalizado = models.CharField(max_length=255, null=True, blank=True)
    clasificacion_personalizada = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'cargo_peligros'

class CargoEPP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='epps')
    catalogo_epp = models.ForeignKey(CatalogoEPP, on_delete=models.SET_NULL, null=True, blank=True)
    nombre_personalizado = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'cargo_epps'


class CargoAptitud(models.Model):
    """Aptitudes físicas/psicológicas requeridas por el cargo (§4.1)."""
    class Tipo(models.TextChoices):
        FISICA = "fisica", "Física"
        PSICOLOGICA = "psicologica", "Psicológica"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='aptitudes')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    nombre = models.CharField(max_length=255)
    requerida = models.BooleanField(default=True)
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'cargo_aptitudes'


class CargoInteraccion(models.Model):
    """Interacciones organizacionales / partes interesadas del cargo (§4.1)."""
    class Tipo(models.TextChoices):
        INTERNO = "interno", "Interno"
        EXTERNO = "externo", "Externo"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='interacciones')
    parte_interesada = models.CharField(max_length=255)
    proceso = models.ForeignKey(
        'organizacion.Proceso', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='interacciones_cargo'
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descripcion = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'cargo_interacciones'


class CargoRestriccion(models.Model):
    """
    Restricciones propias del cargo (no del trabajador) — ej. "no apto para
    alturas", "requiere licencia vigente sin restricciones". No confundir con
    las restricciones médicas del trabajador (expediente laboral, Fase 3):
    MICHC (Fase 4) cruza precisamente estas dos entidades por ser de
    naturaleza distinta (requisito del cargo vs. condición real de la persona).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='restricciones')
    descripcion = models.CharField(max_length=500)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'cargo_restricciones'


class CargoSuplente(models.Model):
    """
    M2M con orden de prioridad entre PerfilCargo (§4.1). `requiere_suplencia`
    en PerfilCargo habilita esta lista.

    Nota de diseño (§11, punto 5 — pregunta abierta aún no resuelta con el
    cliente): esta tabla registra QUIÉN puede suplir, pero todavía no valida
    si el suplente cumple MICHC para el cargo que suple. Esa validación
    cruzada se decide antes de construir la Fase 4 (MICHC) — no asumir un
    comportamiento hasta confirmarlo.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    perfil_cargo = models.ForeignKey(PerfilCargo, on_delete=models.CASCADE, related_name='suplentes')
    cargo_suplente = models.ForeignKey(
        PerfilCargo, on_delete=models.CASCADE, related_name='suple_a'
    )
    orden_prioridad = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = 'cargo_suplentes'
        constraints = [
            UniqueConstraint(fields=['perfil_cargo', 'cargo_suplente'], name='unique_cargo_suplente')
        ]
        ordering = ['orden_prioridad']
