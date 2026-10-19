"""
Servicios de dominio para el Portal Público del Candidato — FOSST V.I.D.A.
Fase E: Autenticación Passwordless (OTP / Magic Link), Postulación Pública y Autoconsulta.
"""
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any, Tuple
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.reclutamiento.models import (
    Candidato,
    PerfilCandidato,
    CandidatoDocumento,
    FuenteReclutamiento,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    TokenAccesoCandidato,
)
from apps.reclutamiento.services.fuentes import obtener_o_crear_fuente_portal
from apps.reclutamiento.services.postulacion import registrar_postulacion, cerrar_postulacion
from apps.reclutamiento.services.transiciones import MotivoRequeridoError


def generar_token_acceso_candidato(
    candidato: Candidato,
    ip_solicitud: Optional[str] = None,
    duracion_minutos: int = 60,
    enviar_email: bool = True,
) -> TokenAccesoCandidato:
    """
    Genera un token criptográfico seguro y un código OTP de 6 dígitos con expiración.
    Envía notificación por correo al candidato de forma asíncrona.
    """
    token_str = secrets.token_urlsafe(32)
    codigo_otp = f"{secrets.randbelow(900000) + 100000}"
    expira_en = timezone.now() + timedelta(minutes=duracion_minutos)

    token_obj = TokenAccesoCandidato.objects.create(
        candidato=candidato,
        token=token_str,
        codigo_otp=codigo_otp,
        expira_en=expira_en,
        ip_solicitud=ip_solicitud,
    )

    if enviar_email and candidato.email:
        try:
            from apps.accounts.tasks import enviar_email_task
            asunto = f"Código de acceso a tu portal de postulación — {candidato.empresa.nombre}"
            cuerpo = (
                f"Hola {candidato.nombres},\n\n"
                f"Tu código OTP para acceder al portal de seguimiento es: {codigo_otp}\n\n"
                f"Este código es válido durante {duracion_minutos} minutos.\n\n"
                f"Equipo de Selección — {candidato.empresa.nombre}"
            )
            enviar_email_task.delay(asunto=asunto, cuerpo=cuerpo, destinatario=candidato.email)
        except Exception:
            # Fallback silencioso si Celery/Resend no está configurado en entorno de pruebas
            pass

    return token_obj


def verificar_otp_candidato(email: str, codigo_otp: str) -> Tuple[Candidato, TokenAccesoCandidato]:
    """
    Valida el código OTP para el correo suministrado y retorna el candidato con token de sesión.
    """
    ahora = timezone.now()
    token_obj = TokenAccesoCandidato.objects.filter(
        candidato__email__iexact=email.strip(),
        codigo_otp=codigo_otp.strip(),
        usado=False,
        expira_en__gte=ahora,
    ).select_related("candidato", "candidato__empresa").first()

    if not token_obj:
        raise ValidationError("El código OTP es inválido o ha expirado.")

    token_obj.usado = True
    token_obj.save(update_fields=["usado"])

    # Generar un nuevo token de sesión con mayor vigencia (ej. 24 horas)
    token_sesion = generar_token_acceso_candidato(
        candidato=token_obj.candidato,
        duracion_minutos=1440,
        enviar_email=False,
    )
    return token_obj.candidato, token_sesion


def verificar_magic_token_candidato(token_str: str) -> Tuple[Candidato, TokenAccesoCandidato]:
    """
    Valida un enlace mágico (Magic Link) y retorna el candidato con token de sesión activo.
    """
    ahora = timezone.now()
    token_obj = TokenAccesoCandidato.objects.filter(
        token=token_str.strip(),
        usado=False,
        expira_en__gte=ahora,
    ).select_related("candidato", "candidato__empresa").first()

    if not token_obj:
        raise ValidationError("El token de acceso es inválido o ha expirado.")

    token_obj.usado = True
    token_obj.save(update_fields=["usado"])

    token_sesion = generar_token_acceso_candidato(
        candidato=token_obj.candidato,
        duracion_minutos=1440,
        enviar_email=False,
    )
    return token_obj.candidato, token_sesion


def _guardar_documento_candidato(candidato, archivo_file, tipo_documento, descripcion=None):
    """Guarda un documento del candidato en el storage central (S3/MinIO) con validación."""
    from apps.common.storage import validate_and_process_file
    from apps.evidencias.models import Archivo

    meta = validate_and_process_file(archivo_file, folder="candidatos", filename=archivo_file.name)
    archivo = Archivo.objects.create(
        nombre=meta["original_name"],
        url=meta["url"] if isinstance(meta["url"], str) else "",
        tipo_mime=meta["mime_type"],
        tamanio_kb=round(meta["size_bytes"] / 1024),
        subido_por=candidato.email,
        sha256_hash=meta["sha256_hash"],
    )
    return CandidatoDocumento.objects.create(
        candidato=candidato,
        archivo=archivo,
        tipo_documento=tipo_documento,
        nombre_descriptivo=descripcion or meta["original_name"],
    )


def _error_documento(exc):
    return str(getattr(exc, "detail", None) or getattr(exc, "message", None) or exc)


@transaction.atomic
def postular_publicamente_candidato(
    vacante: Vacante,
    datos_candidato: Dict[str, Any],
    datos_perfil: Optional[Dict[str, Any]] = None,
    archivo_cv_id: Optional[str] = None,
    ip_solicitud: Optional[str] = None,
) -> Tuple[Postulacion, TokenAccesoCandidato]:
    """
    Procesa la postulación pública de un candidato a una vacante abierta.
    - Cumplimiento estricto de Habeas Data (Ley 1581 de 2012).
    - Unificación en Banco de Talento de la empresa (RN-R10).
    - Creación de Postulación en estado POSTULADO.
    - Emisión de Token de Acceso para autoconsulta.
    """
    if vacante.estado != Vacante.Estado.ABIERTA or not vacante.publicada_en_portal:
        raise ValidationError("La vacante seleccionada no se encuentra abierta para postulaciones públicas.")

    if not datos_candidato.get("autoriza_tratamiento_datos"):
        raise ValidationError("Debe autorizar el tratamiento de datos personales conforme a la Ley 1581 de 2012.")

    empresa = vacante.empresa
    tipo_doc = datos_candidato.get("tipo_documento", Candidato.TipoDocumento.CC)
    documento = str(datos_candidato.get("documento", "")).strip()
    email = str(datos_candidato.get("email", "")).strip().lower()

    if not documento or not email:
        raise ValidationError("Documento y correo electrónico son obligatorios.")

    # Fuente del candidato (por defecto "Portal Web")
    fuente_id = datos_candidato.get("fuente_reclutamiento_id")
    fuente = None
    if fuente_id:
        fuente = FuenteReclutamiento.objects.filter(id=fuente_id, empresa=empresa).first()
    if fuente is None:
        fuente = obtener_o_crear_fuente_portal(empresa)

    # 1. Buscar o crear Candidato en Banco de Talento por documento o email
    candidato = Candidato.objects.filter(
        empresa=empresa,
        tipo_documento=tipo_doc,
        documento=documento,
        deleted_at__isnull=True,
    ).first()

    if not candidato:
        candidato = Candidato.objects.filter(
            empresa=empresa,
            email__iexact=email,
            deleted_at__isnull=True,
        ).first()

    if candidato:
        # Actualizar datos de contacto recientes
        candidato.nombres = datos_candidato.get("nombres", candidato.nombres)
        candidato.apellidos = datos_candidato.get("apellidos", candidato.apellidos)
        candidato.email = email
        candidato.telefono = datos_candidato.get("telefono", candidato.telefono)
        candidato.ciudad = datos_candidato.get("ciudad", candidato.ciudad)
        candidato.direccion = datos_candidato.get("direccion", candidato.direccion)
        candidato.autoriza_tratamiento_datos = True
        candidato.fecha_autorizacion_datos = timezone.now()
        if not candidato.fuente_reclutamiento_id:
            candidato.fuente_reclutamiento = fuente
        candidato.save()
    else:
        candidato = Candidato.objects.create(
            empresa=empresa,
            tipo_documento=tipo_doc,
            documento=documento,
            nombres=datos_candidato.get("nombres", "").strip(),
            apellidos=datos_candidato.get("apellidos", "").strip(),
            email=email,
            telefono=datos_candidato.get("telefono", "").strip(),
            ciudad=datos_candidato.get("ciudad", "").strip(),
            direccion=datos_candidato.get("direccion", "").strip(),
            fuente_reclutamiento=fuente,
            fuente_detalle=datos_candidato.get("fuente_detalle", "Portal Público"),
            autoriza_tratamiento_datos=True,
            fecha_autorizacion_datos=timezone.now(),
        )

    # 2. Actualizar o crear Perfil de Candidato
    perfil, _ = PerfilCandidato.objects.get_or_create(candidato=candidato)
    if datos_perfil:
        for attr, val in datos_perfil.items():
            if hasattr(perfil, attr) and val is not None:
                setattr(perfil, attr, val)
        perfil.save()

    # 3. Vincular documentos (CV + documentos adicionales) en el storage central
    archivo_cv_file = datos_candidato.get("archivo_cv_file")
    if archivo_cv_file:
        try:
            _guardar_documento_candidato(
                candidato,
                archivo_cv_file,
                CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA,
                f"Hoja de Vida — {archivo_cv_file.name}",
            )
        except Exception as exc:
            raise ValidationError(_error_documento(exc))
    elif archivo_cv_id:
        from apps.evidencias.models import Archivo
        archivo = Archivo.objects.filter(id=archivo_cv_id).first()
        if archivo:
            CandidatoDocumento.objects.create(
                candidato=candidato,
                archivo=archivo,
                tipo_documento=CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA,
                nombre_descriptivo="Hoja de Vida — Portal Público",
            )

    # Documentos adicionales (cédula, certificaciones, licencias, etc.)
    for tipo, archivo_extra in datos_candidato.get("documentos_extra") or []:
        try:
            _guardar_documento_candidato(candidato, archivo_extra, tipo)
        except Exception as exc:
            raise ValidationError(_error_documento(exc))

    # 4. Obtener o crear Proceso de Selección para la vacante
    proceso, _ = ProcesoSeleccion.objects.get_or_create(
        empresa=empresa,
        vacante=vacante,
        defaults={
            "requiere_entrevista": True,
            "requiere_evaluacion": True,
            "requiere_validacion_documental": True,
        },
    )

    # 5. Validar que no tenga postulación activa previa en este proceso
    postulacion_existente = Postulacion.objects.filter(
        proceso_seleccion=proceso,
        candidato=candidato,
        deleted_at__isnull=True,
    ).first()

    if postulacion_existente:
        token_acceso = generar_token_acceso_candidato(candidato=candidato, ip_solicitud=ip_solicitud)
        return postulacion_existente, token_acceso

    # 6. Registrar nueva Postulación
    postulacion = registrar_postulacion(
        candidato=candidato,
        proceso_seleccion=proceso,
        fuente=candidato.fuente_reclutamiento,
    )

    # 7. Generar token de acceso para seguimiento
    token_acceso = generar_token_acceso_candidato(
        candidato=candidato,
        ip_solicitud=ip_solicitud,
    )

    return postulacion, token_acceso


@transaction.atomic
def postular_rapido_candidato(
    vacante: Vacante,
    candidato: Candidato,
    ip_solicitud: Optional[str] = None,
) -> Tuple[Postulacion, TokenAccesoCandidato]:
    """
    RN-R10 / 1-Click Apply: Permite a un candidato postularse instantáneamente a otra vacante
    reutilizando su perfil consolidado, Habeas Data previo y su última Hoja de Vida registrada.
    """
    if vacante.estado != Vacante.Estado.ABIERTA or not vacante.publicada_en_portal:
        raise ValidationError("La vacante seleccionada no se encuentra abierta para postulaciones.")

    proceso, _ = ProcesoSeleccion.objects.get_or_create(
        empresa=vacante.empresa,
        vacante=vacante,
        defaults={
            "requiere_entrevista": True,
            "requiere_evaluacion": True,
            "requiere_validacion_documental": True,
        },
    )

    # Validar si ya está postulado
    postulacion_existente = Postulacion.objects.filter(
        proceso_seleccion=proceso,
        candidato=candidato,
        deleted_at__isnull=True,
    ).first()

    if postulacion_existente:
        token_acceso = generar_token_acceso_candidato(candidato=candidato, ip_solicitud=ip_solicitud)
        return postulacion_existente, token_acceso

    postulacion = registrar_postulacion(
        candidato=candidato,
        proceso_seleccion=proceso,
        fuente=candidato.fuente_reclutamiento,
    )

    token_acceso = generar_token_acceso_candidato(
        candidato=candidato,
        ip_solicitud=ip_solicitud,
    )

    return postulacion, token_acceso


@transaction.atomic
def retirar_postulacion_candidato(
    postulacion: Postulacion,
    candidato: Candidato,
    motivo: str = "Retiro voluntario solicitado por el candidato en portal público",
) -> Postulacion:
    """
    RN-R04 / RN-R05: Permite al candidato retirar voluntariamente su postulación.
    """
    if postulacion.candidato_id != candidato.id:
        raise ValidationError("No tiene autorización para retirar esta postulación.")

    if not postulacion.es_activa:
        raise ValidationError("La postulación ya se encuentra finalizada y no puede ser retirada.")

    # El motivo es opcional para el retiro del candidato (RN-R05): si no lo indica,
    # se registra un texto por defecto para satisfacer la trazabilidad.
    motivo_final = (motivo or "").strip() or "Retiro voluntario solicitado por el candidato en el portal"

    return cerrar_postulacion(
        postulacion=postulacion,
        nuevo_estado=Postulacion.Estado.RETIRO_CANDIDATURA,
        motivo=motivo_final,
        datos_adicionales={"origen": "portal_candidato"},
    )
