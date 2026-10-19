"""
Notificaciones de resultados del proceso de Reclutamiento & Selección.
Envío no bloqueante vía Celery/SMTP; nunca revierte la transición de estado.
"""
import logging

from django.db import transaction

logger = logging.getLogger(__name__)

ASUNTOS = {
    "seleccionado": "¡Felicitaciones! Fuiste seleccionado(a) para {vacante}",
    "no_seleccionado": "Resultado de tu proceso para {vacante}",
    "no_continuo": "Tu proceso para {vacante} no continuó",
    "retiro": "Confirmación de retiro — {vacante}",
    "falta_documentos": "Documentación pendiente — {vacante}",
}


def _enviar(asunto: str, cuerpo: str, email: str):
    try:
        from apps.accounts.tasks import enviar_email_task

        enviar_email_task.delay(asunto=asunto, cuerpo=cuerpo, destinatario=email)
    except Exception as exc:  # pragma: no cover - depende de broker
        logger.error("[reclutamiento.notificaciones] No se pudo encolar correo a %s: %s", email, exc)


def notificar_resultado(postulacion, tipo: str, motivo: str = ""):
    """
    Notifica al candidato el resultado de su postulación.
    Se ejecuta después del commit para no enviar correos si la transacción falla.
    """
    candidato = getattr(postulacion, "candidato", None)
    if not candidato or not candidato.email:
        return

    try:
        vacante = postulacion.proceso_seleccion.vacante
        empresa = postulacion.empresa
    except Exception:
        return

    nombre = candidato.nombres or "candidato"
    asunto = ASUNTOS.get(tipo, "Actualización de tu postulación — {vacante}").format(vacante=vacante.titulo)

    if tipo == "seleccionado":
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Nos complace informarte que has sido SELECCIONADO(A) para la vacante "
            f"'{vacante.titulo}' ({vacante.codigo}) en {empresa.nombre}.\n\n"
            f"El equipo de Gestión Humana se pondrá en contacto contigo para continuar con el "
            f"proceso de vinculación.\n\n"
            f"¡Felicitaciones!\nEquipo de Selección — {empresa.nombre}"
        )
    elif tipo == "no_seleccionado":
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Agradecemos tu participación en el proceso para '{vacante.titulo}'.\n"
            f"En esta ocasión tu candidatura no continuó.\n\n"
            f"Motivo: {motivo or 'No especificado'}\n\n"
            f"Tu perfil permanece en nuestro Banco de Talento para futuras oportunidades.\n\n"
            f"Equipo de Selección — {empresa.nombre}"
        )
    elif tipo == "no_continuo":
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Tu proceso para la vacante '{vacante.titulo}' no continuó.\n\n"
            f"Motivo: {motivo or 'No especificado'}\n\n"
            f"Tu perfil permanece en nuestro Banco de Talento.\n\n"
            f"Equipo de Selección — {empresa.nombre}"
        )
    elif tipo == "retiro":
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Confirmamos el retiro de tu candidatura para la vacante '{vacante.titulo}'.\n\n"
            f"Tu perfil permanece en nuestro Banco de Talento para futuras oportunidades.\n\n"
            f"Equipo de Selección — {empresa.nombre}"
        )
    elif tipo == "falta_documentos":
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Tu proceso para la vacante '{vacante.titulo}' no puede continuar porque no se recibió "
            f"la documentación requerida.\n\n"
            f"Detalle: {motivo or 'Documentación incompleta'}\n\n"
            f"Equipo de Selección — {empresa.nombre}"
        )
    else:
        cuerpo = (
            f"Hola {nombre},\n\n"
            f"Hay una actualización en tu proceso para la vacante '{vacante.titulo}'.\n\n"
            f"Equipo de Selección — {empresa.nombre}"
        )

    email = candidato.email
    transaction.on_commit(lambda: _enviar(asunto, cuerpo, email))
