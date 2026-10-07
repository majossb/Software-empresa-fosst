import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def enviar_email_task(
    self,
    subject=None,
    body=None,
    destinatario=None,
    asunto=None,
    cuerpo=None,
    html_body=None,
    html_message=None,
    html_cuerpo=None,
    from_email=None,
):
    """
    Tarea Celery asíncrona para envío de correos utilizando el backend SMTP nativo de Django.
    Soporta argumentos posicionales y nombrados (subject/asunto, body/cuerpo, destinatario).
    """
    email_subject = subject or asunto or ""
    email_body = body or cuerpo or ""
    email_html = html_body or html_message or html_cuerpo
    target_email = destinatario

    if not target_email:
        logger.warning("[enviar_email_task] Se intentó enviar un correo sin destinatario.")
        return {"status": "skipped", "reason": "no_recipient"}

    sender = from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "DiagnostISST <no-reply@diagnostisst.com>")

    try:
        msg = EmailMultiAlternatives(
            subject=email_subject,
            body=email_body,
            from_email=sender,
            to=[target_email],
        )
        if email_html:
            msg.attach_alternative(email_html, "text/html")

        msg.send(fail_silently=False)
        logger.info("[enviar_email_task] Correo enviado exitosamente vía SMTP a %s (Asunto: %s)", target_email, email_subject)
        return {"status": "sent", "to": target_email, "subject": email_subject}
    except Exception as exc:
        logger.error("[enviar_email_task] Error al enviar correo SMTP a %s: %s", target_email, str(exc))
        raise self.retry(exc=exc)


# ── Tareas de respaldo automático ────────────────────────────────────────────

@shared_task(name="apps.accounts.tasks.backup_database")
def backup_database():
    """
    Tarea Celery periódica (Celery Beat) para generar un respaldo automático de la base de datos.
    Se ejecuta diariamente a las 2:00 AM (hora Colombia / America/Bogota).
    El archivo de respaldo se almacena en la carpeta backups/ en la raíz del proyecto.
    """
    import os
    from datetime import datetime
    from pathlib import Path
    from django.core.management import call_command
    from django.conf import settings as django_settings

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        env_name = getattr(django_settings, "ENVIRONMENT", "development").lower()
        base_dir = Path(django_settings.BASE_DIR).parent
        backup_dir = base_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        filename = f"backup_{env_name}_{timestamp}.json"

        call_command("backup_db", filename=filename, quiet=True)

        backup_path = backup_dir / filename
        size_mb = backup_path.stat().st_size / (1024 * 1024) if backup_path.exists() else 0
        logger.info(
            "[backup_database] Respaldo automático generado exitosamente: %s (%.2f MB)",
            backup_path,
            size_mb,
        )
        return {"status": "ok", "file": str(backup_path), "size_mb": round(size_mb, 2)}
    except Exception as exc:
        logger.error("[backup_database] Error al generar respaldo automático: %s", str(exc))
        raise


@shared_task(name="apps.accounts.tasks.limpiar_backups_antiguos")
def limpiar_backups_antiguos(dias_retencion: int = 30):
    """
    Tarea Celery periódica (Celery Beat) para eliminar respaldos con más de `dias_retencion` días.
    Se ejecuta cada domingo a las 3:00 AM (hora Colombia / America/Bogota).
    Solo elimina archivos con extensión .json dentro de la carpeta backups/.
    """
    import os
    from datetime import datetime, timedelta
    from pathlib import Path
    from django.conf import settings as django_settings

    try:
        base_dir = Path(django_settings.BASE_DIR).parent
        backup_dir = base_dir / "backups"

        if not backup_dir.exists():
            logger.info("[limpiar_backups_antiguos] La carpeta backups/ no existe. Nada que limpiar.")
            return {"status": "ok", "eliminados": 0}

        umbral = datetime.now() - timedelta(days=dias_retencion)
        eliminados = 0

        for archivo in backup_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(archivo.stat().st_mtime)
                if mtime < umbral:
                    archivo.unlink()
                    eliminados += 1
                    logger.info("[limpiar_backups_antiguos] Eliminado backup antiguo: %s (modificado: %s)", archivo.name, mtime.date())
            except Exception as e:
                logger.warning("[limpiar_backups_antiguos] No se pudo eliminar %s: %s", archivo, str(e))

        logger.info(
            "[limpiar_backups_antiguos] Limpieza completada: %d archivo(s) eliminado(s) (retención: %d días).",
            eliminados,
            dias_retencion,
        )
        return {"status": "ok", "eliminados": eliminados, "dias_retencion": dias_retencion}
    except Exception as exc:
        logger.error("[limpiar_backups_antiguos] Error durante la limpieza: %s", str(exc))
        raise