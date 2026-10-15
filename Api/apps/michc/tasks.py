"""
Tareas Celery para MICHC (§6).
"""
import logging
from celery import shared_task
from .engine import recalcular_habilitacion

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def recalcular_michc_task(self, trabajador_id):
    """Tarea asíncrona para recalcular la evaluación MICHC de un trabajador."""
    logger.info("Iniciando recálculo MICHC asíncrono para trabajador ID: %s", trabajador_id)
    evaluacion = recalcular_habilitacion(trabajador_id)
    if evaluacion:
        return {
            "trabajador_id": str(trabajador_id),
            "estado": evaluacion.estado_habilitacion,
            "semaforo": evaluacion.semaforo,
            "porcentaje": float(evaluacion.porcentaje_cumplimiento)
        }
    return {"error": "Trabajador no encontrado"}
