"""
Comando para sembrar las reglas de alerta estándar del sistema (§5.2).
"""
from django.core.management.base import BaseCommand
from apps.alertas.models import ReglaAlerta
from apps.calendario.models import Notificacion


REGLAS_ESTANDAR = [
    {
        "codigo": "VENC_CONTRATO_60D",
        "nombre": "Vencimiento de Contrato a Término Fijo / Obra (60 días)",
        "modelo_origen": "Trabajador",
        "campo_fecha": "fecha_fin_contrato",
        "dias_anticipacion": 60,
        "nivel_criticidad": Notificacion.Nivel.IMPORTANTE,
        "mensaje_template": "El contrato de {trabajador} (Doc: {documento}) vence en {dias} días (Fecha: {fecha}). Cargo: {cargo}.",
        "roles_destinatarios": ["RESPONSABLE", "ALTA_DIRECCION"],
    },
    {
        "codigo": "VENC_PRUEBA_20D",
        "nombre": "Finalización de Periodo de Prueba (20 días)",
        "modelo_origen": "Trabajador",
        "campo_fecha": "fecha_fin_periodo_prueba",
        "dias_anticipacion": 20,
        "nivel_criticidad": Notificacion.Nivel.NORMAL,
        "mensaje_template": "El periodo de prueba de {trabajador} finaliza en {dias} días ({fecha}). Definir continuidad.",
        "roles_destinatarios": ["RESPONSABLE"],
    },
    {
        "codigo": "VENC_EXAMEN_MEDICO_30D",
        "nombre": "Vencimiento de Examen Médico Ocupacional (30 días)",
        "modelo_origen": "ExamenMedicoOcupacional",
        "campo_fecha": "fecha_vencimiento",
        "dias_anticipacion": 30,
        "nivel_criticidad": Notificacion.Nivel.IMPORTANTE,
        "mensaje_template": "El examen médico ocupacional ({tipo}) de {trabajador} vence en {dias} días ({fecha}). Programar valoración periódica.",
        "roles_destinatarios": ["RESPONSABLE"],
    },
    {
        "codigo": "VENC_LICENCIA_CONDUCCION_30D",
        "nombre": "Vencimiento de Licencia de Conducción (30 días)",
        "modelo_origen": "LicenciaConduccion",
        "campo_fecha": "fecha_vencimiento",
        "dias_anticipacion": 30,
        "nivel_criticidad": Notificacion.Nivel.IMPORTANTE,
        "mensaje_template": "La licencia de conducción ({tipo}) de {trabajador} vence en {dias} días ({fecha}). Solicitar renovación.",
        "roles_destinatarios": ["RESPONSABLE"],
    },
    {
        "codigo": "VENC_AFILIACION_15D",
        "nombre": "Vencimiento / Renovación de Afiliación a Seguridad Social (15 días)",
        "modelo_origen": "AfiliacionTrabajador",
        "campo_fecha": "fecha_vencimiento",
        "tipo_handler": "exacta",
        "dias_anticipacion": 15,
        "nivel_criticidad": Notificacion.Nivel.CRITICO,
        "mensaje_template": "La afiliación a {tipo} del trabajador {trabajador} requiere validación o vence en {dias} días ({fecha}).",
        "roles_destinatarios": ["RESPONSABLE"],
    },
    # -----------------------------------------------------------------------
    # Fase 5 — Alertas de Formación & Competencias
    # -----------------------------------------------------------------------
    {
        "codigo": "FORM_CURSO_POR_VENCER_30D",
        "nombre": "Curso Obligatorio por Vencer (30 días)",
        "modelo_origen": "RegistroFormacion",
        "campo_fecha": "fecha_vencimiento",
        "tipo_handler": "exacta",
        "dias_anticipacion": 30,
        "nivel_criticidad": Notificacion.Nivel.IMPORTANTE,
        "mensaje_template": (
            "El certificado de '{curso}' de {trabajador} vence en {dias} días ({fecha}). "
            "Cargo: {cargo}."
        ),
        "roles_destinatarios": ["RESPONSABLE"],
    },
    {
        "codigo": "FORM_CURSO_VENCIDO",
        "nombre": "Curso Obligatorio Vencido",
        "modelo_origen": "RegistroFormacion",
        "campo_fecha": "fecha_vencimiento",
        "tipo_handler": "vencido_rango",
        "dias_anticipacion": 0,
        "nivel_criticidad": Notificacion.Nivel.CRITICO,
        "mensaje_template": (
            "El certificado de '{curso}' de {trabajador} (Doc: {documento}) está VENCIDO "
            "(venció: {fecha}). Cargo: {cargo}. Renovar urgente."
        ),
        "roles_destinatarios": ["RESPONSABLE", "ALTA_DIRECCION"],
    },
    {
        "codigo": "FORM_CURSO_SIN_REGISTRAR",
        "nombre": "Curso Obligatorio Sin Registrar",
        "modelo_origen": "RegistroFormacion",
        "campo_fecha": "",
        "tipo_handler": "sin_registrar",
        "dias_anticipacion": 0,
        "nivel_criticidad": Notificacion.Nivel.IMPORTANTE,
        "mensaje_template": (
            "El trabajador {trabajador} (Cargo: {cargo}) no registra el curso obligatorio '{curso}'."
        ),
        "roles_destinatarios": ["RESPONSABLE"],
    },
    {
        "codigo": "FORM_EVALUACION_COMPETENCIA_PENDIENTE",
        "nombre": "Evaluación de Competencia Pendiente o con Brecha",
        "modelo_origen": "EvaluacionCompetencia",
        "campo_fecha": "",
        "tipo_handler": "evaluacion_pendiente",
        "dias_anticipacion": 0,
        "nivel_criticidad": Notificacion.Nivel.NORMAL,
        "mensaje_template": (
            "El trabajador {trabajador} (Cargo: {cargo}) tiene una brecha en la competencia "
            "'{competencia}' y requiere capacitación."
        ),
        "roles_destinatarios": ["RESPONSABLE"],
    },
]



class Command(BaseCommand):
    help = "Siembra las reglas de alerta estándar del sistema"

    def handle(self, *args, **options):
        creadas = 0
        actualizadas = 0
        for data in REGLAS_ESTANDAR:
            regla, created = ReglaAlerta.objects.update_or_create(
                codigo=data["codigo"],
                empresa__isnull=True,
                defaults={
                    "nombre": data["nombre"],
                    "modelo_origen": data["modelo_origen"],
                    "campo_fecha": data["campo_fecha"],
                    "tipo_handler": data.get("tipo_handler", ReglaAlerta.TipoHandler.EXACTA),
                    "dias_anticipacion": data["dias_anticipacion"],
                    "nivel_criticidad": data["nivel_criticidad"],
                    "mensaje_template": data["mensaje_template"],
                    "roles_destinatarios": data["roles_destinatarios"],
                    "activa": True,
                },
            )
            if created:
                creadas += 1
            else:
                actualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(f"Reglas de alerta sembradas: {creadas} creadas, {actualizadas} actualizadas.")
        )
