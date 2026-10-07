from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def notificar_acceso_inusual(usuario, ip, user_agent):
    """Envío asíncrono recomendado vía Celery (ver apps/accounts/tasks.py)."""
    from apps.accounts.tasks import enviar_email_task

    contexto = {"usuario": usuario, "ip": ip, "user_agent": user_agent}
    cuerpo = render_to_string("emails/acceso_inusual.txt", contexto)
    enviar_email_task.delay(
        asunto="Nuevo acceso detectado en tu cuenta DiagnostISST",
        cuerpo=cuerpo,
        destinatario=usuario.email,
    )
