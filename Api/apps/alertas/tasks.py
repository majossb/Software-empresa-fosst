"""
Tareas Celery para el Motor de Alertas (§5.2).

Ejecuta la revisión periódica diaria de vencimientos (CELERY_BEAT_SCHEDULE).
"""
import logging
from celery import shared_task
from .services import evaluar_reglas_alertas

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def revisar_vencimientos(self):
    """
    Tarea Celery periódica (diaria):
    Recorre todas las ReglaAlerta activas y genera notificaciones en Notificacion
    con deduplicación para evitar saturar al usuario.
    """
    logger.info("Iniciando tarea periódica revisar_vencimientos...")
    total = evaluar_reglas_alertas()
    logger.info("Finalizada tarea revisar_vencimientos. Total alertas generadas: %d", total)
    return {"alertas_generadas": total}
