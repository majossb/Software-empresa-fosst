"""
Servicio del Motor Genérico de Alertas (§5.2).

Evalúa las reglas activas de vencimiento contra los modelos de datos,
formatea los mensajes y genera notificaciones con deduplicación diaria.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from apps.accounts.models import Usuario
from apps.calendario.models import Notificacion
from .models import ReglaAlerta

logger = logging.getLogger(__name__)


def evaluar_reglas_alertas(empresa=None, fecha_referencia=None) -> int:
    """
    Recorre todas las ReglaAlerta activas y genera Notificaciones
    con deduplicación (no enviar la misma alerta el mismo día).

    RN-14: Las alertas quedan registradas en Notificacion (fuente única).

    Args:
        empresa: Empresa opcional para filtrar evaluación
        fecha_referencia: date opcional (por defecto hoy)

    Returns:
        total_notificaciones_creadas (int)
    """
    if fecha_referencia is None:
        fecha_referencia = timezone.localdate()

    from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
    from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion

    MODEL_MAP = {
        "Trabajador": Trabajador,
        "ExamenMedicoOcupacional": ExamenMedicoOcupacional,
        "LicenciaConduccion": LicenciaConduccion,
        "AfiliacionTrabajador": AfiliacionTrabajador,
    }

    reglas_qs = ReglaAlerta.objects.filter(activa=True)
    if empresa:
        from django.db.models import Q
        reglas_qs = reglas_qs.filter(Q(empresa=empresa) | Q(empresa__isnull=True))

    notificaciones_creadas = 0

    for regla in reglas_qs:
        model_cls = MODEL_MAP.get(regla.modelo_origen)
        if not model_cls:
            logger.warning("Modelo origen '%s' no encontrado en MODEL_MAP", regla.modelo_origen)
            continue

        target_date = fecha_referencia + timedelta(days=regla.dias_anticipacion)

        # Construir filtro
        filter_kwargs = {
            f"{regla.campo_fecha}": target_date
        }

        # Filtrar solo registros activos
        if hasattr(model_cls, "activo"):
            filter_kwargs["activo"] = True
        if hasattr(model_cls, "deleted_at"):
            filter_kwargs["deleted_at__isnull"] = True
        if regla.modelo_origen in ["ExamenMedicoOcupacional", "LicenciaConduccion", "AfiliacionTrabajador"]:
            filter_kwargs["trabajador__activo"] = True
            filter_kwargs["trabajador__deleted_at__isnull"] = True

        if empresa and hasattr(model_cls, "empresa"):
            filter_kwargs["empresa"] = empresa
        elif empresa and hasattr(model_cls, "trabajador"):
            filter_kwargs["trabajador__empresa"] = empresa

        try:
            records = model_cls.objects.filter(**filter_kwargs)
            if regla.modelo_origen in ["ExamenMedicoOcupacional", "LicenciaConduccion", "AfiliacionTrabajador"]:
                records = records.select_related("trabajador__empresa")
            elif regla.modelo_origen == "Trabajador":
                records = records.select_related("empresa")
        except Exception as e:
            logger.error("Error consultando registros para regla %s: %s", regla.codigo, e)
            continue

        for item in records:
            # Obtener trabajador y empresa
            if hasattr(item, "trabajador"):
                trabajador = item.trabajador
                empresa_obj = item.trabajador.empresa
            else:
                trabajador = item
                empresa_obj = item.empresa

            # Renderizar mensaje
            try:
                mensaje = regla.mensaje_template.format(
                    trabajador=trabajador.nombre,
                    documento=trabajador.documento,
                    fecha=target_date.strftime("%Y-%m-%d"),
                    dias=regla.dias_anticipacion,
                    cargo=trabajador.cargo or "No especificado",
                    tipo=getattr(item, "tipo", getattr(item, "categoria", "")),
                )
            except Exception as e:
                mensaje = f"Alerta {regla.nombre} para {trabajador.nombre} (Fecha: {target_date})"

            # Destinatarios según roles
            roles_upper = [r.upper() for r in (regla.roles_destinatarios or ["RESPONSABLE"])]
            destinatarios = Usuario.objects.filter(
                empresa=empresa_obj,
                rol__in=roles_upper,
                activo=True
            )

            # Deduplicación: no crear la misma notificación si ya existe hoy
            inicio_dia = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

            for usuario in destinatarios:
                alerta_existente = Notificacion.objects.filter(
                    empresa=empresa_obj,
                    usuario=usuario,
                    mensaje=mensaje,
                    created_at__gte=inicio_dia
                ).exists()

                if not alerta_existente:
                    Notificacion.objects.create(
                        empresa=empresa_obj,
                        usuario=usuario,
                        tipo=Notificacion.Tipo.ALERTA,
                        nivel=regla.nivel_criticidad,
                        mensaje=mensaje,
                    )
                    notificaciones_creadas += 1

    logger.info("Motor de alertas: %d notificaciones generadas para fecha %s", notificaciones_creadas, fecha_referencia)
    return notificaciones_creadas
