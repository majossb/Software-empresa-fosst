"""
Management command para sembrar datos de prueba completos y realistas en FOSST V.I.D.A.

Crea:
  - Perfiles de cargo multidimensionales con competencias
  - Trabajadores en diferentes escenarios (Habilitado Verde, Observación Amarillo, Incompatible Rojo con Brecha HBSEO, Novedad Activa, Brechas de Competencia)
  - Exámenes médicos ocupacionales, licencias de conducción, novedades laborales
  - Evaluaciones de competencias (MCC)
  - Recálculo de la Matriz MICHC y generación de alertas
"""
import uuid
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario
from apps.perfilcargo.models import (
    PerfilCargo, CargoCompetencia, NivelCriticidad
)
from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.gestion_humana.models import (
    ExamenMedicoOcupacional, LicenciaConduccion, NovedadLaboral
)
from apps.formacion.models import EvaluacionCompetencia
from apps.michc.engine import recalcular_habilitacion
from apps.alertas.services import evaluar_reglas_alertas
from django.core.management import call_command


class Command(BaseCommand):
    help = "Siembra datos de prueba completos para probar la lógica de FOSST V.I.D.A."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Sembrando datos de prueba en FOSST V.I.D.A..."))

        # 1. Obtener o crear Empresa Demo
        empresa = Empresa.objects.first()
        if not empresa:
            empresa = Empresa.objects.create(
                nombre="Empresa Demo FOSST SAS",
                nit="900123456-1",
                num_trabajadores=25,
                nivel_riesgo=4,
                capitulo_vigente="I",
            )
            self.stdout.write(self.style.SUCCESS(f"Empresa creada: {empresa.nombre}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Usando empresa existente: {empresa.nombre} ({empresa.nit})"))

        usuario_resp = Usuario.objects.filter(empresa=empresa, rol="RESPONSABLE").first()
        today = date.today()

        with transaction.atomic():
            # 2. Sembrar Reglas de Alerta
            call_command("seed_reglas_alerta")
            self.stdout.write("  -> Reglas de alerta estándar verificadas.")

            # 3. Crear Perfiles de Cargo
            perfil_alturas, _ = PerfilCargo.objects.get_or_create(
                empresa=empresa,
                codigo="PC-TEC-ALT",
                defaults={
                    "nombre_cargo": "Técnico Especialista de Alturas y Redes",
                    "area": "Operaciones / Mantenimiento",
                    "nivel_riesgo": 5,
                    "proposito": "Mantenimiento preventivo y correctivo en infraestructuras elevadas y torres de telecomunicación.",
                    "educacion": "Tecnólogo en Electricidad, Telecomunicaciones o afines.",
                    "experiencia": "24 meses en trabajo seguro en alturas.",
                    "criticidad_sst": NivelCriticidad.CRITICO,
                    "criticidad_operacional": NivelCriticidad.ALTO,
                    "criticidad_vial": NivelCriticidad.BAJO,
                    "criticidad_ambiental": NivelCriticidad.MEDIO,
                    "criticidad_estrategica": NivelCriticidad.MEDIO,
                    "requiere_suplencia": True,
                    "version_actual": 1,
                }
            )

            perfil_conductor, _ = PerfilCargo.objects.get_or_create(
                empresa=empresa,
                codigo="PC-COND-PES",
                defaults={
                    "nombre_cargo": "Conductor de Transporte Pesado y Carga",
                    "area": "Logística y Distribución",
                    "nivel_riesgo": 4,
                    "proposito": "Transporte nacional de insumos, materiales y equipos pesados cumpliendo el PESV.",
                    "educacion": "Bachiller Académico.",
                    "experiencia": "36 meses de conducción de tractocamión o vehículos articulados.",
                    "criticidad_sst": NivelCriticidad.ALTO,
                    "criticidad_operacional": NivelCriticidad.ALTO,
                    "criticidad_vial": NivelCriticidad.CRITICO,
                    "criticidad_ambiental": NivelCriticidad.BAJO,
                    "criticidad_estrategica": NivelCriticidad.MEDIO,
                    "requiere_suplencia": False,
                    "version_actual": 1,
                }
            )

            perfil_admin, _ = PerfilCargo.objects.get_or_create(
                empresa=empresa,
                codigo="PC-ADM-SST",
                defaults={
                    "nombre_cargo": "Analista de Gestión Humana y SST",
                    "area": "Administración",
                    "nivel_riesgo": 1,
                    "proposito": "Administración del personal, archivo documental y seguimiento a estándares mínimos.",
                    "educacion": "Profesional en Administración, Psicología o Ingeniería Industrial.",
                    "experiencia": "12 meses en áreas de talento humano o SST.",
                    "criticidad_sst": NivelCriticidad.BAJO,
                    "criticidad_operacional": NivelCriticidad.MEDIO,
                    "criticidad_vial": NivelCriticidad.BAJO,
                    "criticidad_ambiental": NivelCriticidad.BAJO,
                    "criticidad_estrategica": NivelCriticidad.ALTO,
                    "requiere_suplencia": False,
                    "version_actual": 1,
                }
            )
            self.stdout.write("  -> Perfiles de cargo multidimensionales listos.")

            # 4. Competencias por Cargo
            comp_alt_1, _ = CargoCompetencia.objects.get_or_create(
                perfil_cargo=perfil_alturas,
                nombre="Rescate y Maniobras Seguras en Alturas",
                defaults={"tipo": "tecnica", "nivel_requerido": 4, "nivel": 4}
            )
            comp_alt_2, _ = CargoCompetencia.objects.get_or_create(
                perfil_cargo=perfil_alturas,
                nombre="Uso e Inspección de EPP Contra Caídas",
                defaults={"tipo": "tecnica", "nivel_requerido": 3, "nivel": 3}
            )
            comp_alt_3, _ = CargoCompetencia.objects.get_or_create(
                perfil_cargo=perfil_alturas,
                nombre="Toma de Decisiones Bajo Presión",
                defaults={"tipo": "blanda", "nivel_requerido": 3, "nivel": 3}
            )

            comp_cond_1, _ = CargoCompetencia.objects.get_or_create(
                perfil_cargo=perfil_conductor,
                nombre="Manejo Defensivo y Seguridad Vial PESV",
                defaults={"tipo": "tecnica", "nivel_requerido": 4, "nivel": 4}
            )
            comp_cond_2, _ = CargoCompetencia.objects.get_or_create(
                perfil_cargo=perfil_conductor,
                nombre="Mecánica Básica y Revisión Preoperacional",
                defaults={"tipo": "tecnica", "nivel_requerido": 3, "nivel": 3}
            )
            self.stdout.write("  -> Competencias de cargo registradas.")

            # 5. Crear Trabajadores en Escenarios Clave

            # Escenario A: 100% VERDE / HABILITADO
            t1, _ = Trabajador.objects.get_or_create(
                documento="1010203040",
                empresa=empresa,
                defaults={
                    "nombre": "Carlos Andrés Pérez Mora",
                    "perfil_cargo": perfil_alturas,
                    "tipo_vinculacion": "dependiente",
                    "tipo_contrato": "indefinido",
                    "fecha_ingreso": today - timedelta(days=200),
                    "remuneracion_monto": "3500000",
                    "remuneracion_tipo": "mensual",
                }
            )
            ExamenMedicoOcupacional.objects.get_or_create(
                trabajador=t1,
                tipo="periodico",
                defaults={
                    "fecha_examen": today - timedelta(days=30),
                    "fecha_vencimiento": today + timedelta(days=335),
                    "concepto_aptitud": "apto",
                    "presenta_restricciones": False,
                    "medico_evaluador": "Dr. Fernando Ruiz (Lic. SST 45892)",
                }
            )
            AfiliacionTrabajador.objects.get_or_create(
                trabajador=t1, tipo="arl", defaults={"entidad_nombre": "Sura ARL"}
            )
            AfiliacionTrabajador.objects.get_or_create(
                trabajador=t1, tipo="eps", defaults={"entidad_nombre": "Sanitas EPS"}
            )

            # Escenario B: AMARILLO / OBSERVACIONES (Examen vencido)
            t2, _ = Trabajador.objects.get_or_create(
                documento="1020304050",
                empresa=empresa,
                defaults={
                    "nombre": "Laura Marcela Gómez Arias",
                    "perfil_cargo": perfil_admin,
                    "tipo_vinculacion": "dependiente",
                    "tipo_contrato": "fijo",
                    "fecha_ingreso": today - timedelta(days=330),
                    "fecha_fin_contrato": today + timedelta(days=35),
                    "remuneracion_monto": "2800000",
                }
            )
            ExamenMedicoOcupacional.objects.get_or_create(
                trabajador=t2,
                tipo="ingreso",
                defaults={
                    "fecha_examen": today - timedelta(days=390),
                    "fecha_vencimiento": today - timedelta(days=25), # Vencido hace 25 días
                    "concepto_aptitud": "apto",
                    "presenta_restricciones": False,
                    "medico_evaluador": "Dra. Claudia Meza (Lic. SST 11203)",
                }
            )
            AfiliacionTrabajador.objects.get_or_create(
                trabajador=t2, tipo="arl", defaults={"entidad_nombre": "Positiva ARL"}
            )

            # Escenario C: ROJO / INCOMPATIBLE (RN-15 Dispara Brecha HBSEO)
            t3, _ = Trabajador.objects.get_or_create(
                documento="1030405060",
                empresa=empresa,
                defaults={
                    "nombre": "Juan Camilo Rodríguez Ortiz",
                    "perfil_cargo": perfil_alturas,
                    "tipo_vinculacion": "dependiente",
                    "tipo_contrato": "indefinido",
                    "fecha_ingreso": today - timedelta(days=150),
                    "remuneracion_monto": "3200000",
                }
            )
            ExamenMedicoOcupacional.objects.get_or_create(
                trabajador=t3,
                tipo="periodico",
                defaults={
                    "fecha_examen": today - timedelta(days=15),
                    "fecha_vencimiento": today + timedelta(days=350),
                    "concepto_aptitud": "apto_con_restricciones",
                    "presenta_restricciones": True,
                    "descripcion_restricciones": "Restricción severa para trabajo en alturas por cuadro de vértigo periférico recurrente.",
                    "medico_evaluador": "Dr. Fernando Ruiz (Lic. SST 45892)",
                }
            )
            AfiliacionTrabajador.objects.get_or_create(
                trabajador=t3, tipo="arl", defaults={"entidad_nombre": "Sura ARL"}
            )

            # Escenario D: NOVEDAD LABORAL ACTIVA (Incapacidad / Vacaciones)
            t4, _ = Trabajador.objects.get_or_create(
                documento="1040506070",
                empresa=empresa,
                defaults={
                    "nombre": "María Alejandra Fernández Silva",
                    "perfil_cargo": perfil_admin,
                    "tipo_vinculacion": "dependiente",
                    "tipo_contrato": "indefinido",
                    "fecha_ingreso": today - timedelta(days=400),
                    "remuneracion_monto": "2900000",
                }
            )
            NovedadLaboral.objects.get_or_create(
                trabajador=t4,
                tipo="incapacidad",
                defaults={
                    "fecha_inicio": today - timedelta(days=5),
                    "fecha_fin": today + timedelta(days=10),
                    "dias": 15,
                    "observaciones": "Incapacidad médica por intervención quirúrgica ambulatoria.",
                }
            )
            ExamenMedicoOcupacional.objects.get_or_create(
                trabajador=t4,
                tipo="ingreso",
                defaults={
                    "fecha_examen": today - timedelta(days=390),
                    "fecha_vencimiento": today + timedelta(days=100),
                    "concepto_aptitud": "apto",
                }
            )

            # Escenario E: CONDUCTOR CON LICENCIA Y EVALUACIÓN DE COMPETENCIA MCC
            t5, _ = Trabajador.objects.get_or_create(
                documento="1050607080",
                empresa=empresa,
                defaults={
                    "nombre": "Diego Fernando Sánchez Torres",
                    "perfil_cargo": perfil_conductor,
                    "tipo_vinculacion": "dependiente",
                    "tipo_contrato": "indefinido",
                    "fecha_ingreso": today - timedelta(days=90),
                    "remuneracion_monto": "3800000",
                }
            )
            LicenciaConduccion.objects.get_or_create(
                trabajador=t5,
                categoria="C2",
                defaults={
                    "fecha_expedicion": today - timedelta(days=365),
                    "fecha_vencimiento": today + timedelta(days=400),
                    "presenta_restricciones": False,
                }
            )
            ExamenMedicoOcupacional.objects.get_or_create(
                trabajador=t5,
                tipo="ingreso",
                defaults={
                    "fecha_examen": today - timedelta(days=80),
                    "fecha_vencimiento": today + timedelta(days=285),
                    "concepto_aptitud": "apto",
                }
            )
            AfiliacionTrabajador.objects.get_or_create(
                trabajador=t5, tipo="arl", defaults={"entidad_nombre": "Sura ARL"}
            )
            # Evaluación con brecha: Requerido L4 vs Alcanzado L2 -> Brecha = 2 (dispara HBSEO)
            EvaluacionCompetencia.objects.get_or_create(
                trabajador=t5,
                cargo_competencia=comp_cond_1,
                defaults={
                    "nivel_alcanzado": 2,
                    "fecha_evaluacion": today - timedelta(days=10),
                    "metodo": "prueba_tecnica",
                    "observacion": "Requiere reentrenamiento en frenado de emergencia y maniobras en terreno mojado.",
                    "evaluado_por": usuario_resp,
                }
            )
            # Evaluación sin brecha: Requerido L3 vs Alcanzado L3 -> Brecha = 0
            EvaluacionCompetencia.objects.get_or_create(
                trabajador=t5,
                cargo_competencia=comp_cond_2,
                defaults={
                    "nivel_alcanzado": 3,
                    "fecha_evaluacion": today - timedelta(days=10),
                    "metodo": "observacion_directa",
                    "observacion": "Excelente dominio en inspección preoperacional de tractocamión.",
                    "evaluado_por": usuario_resp,
                }
            )
            self.stdout.write("  -> 5 trabajadores de prueba creados en escenarios representativos.")

        # 6. Recalcular la Matriz MICHC para todos los trabajadores
        self.stdout.write("  -> Ejecutando motor de reconciliación MICHC...")
        for t in [t1, t2, t3, t4, t5]:
            evaluacion = recalcular_habilitacion(t.id)
            self.stdout.write(f"     * {t.nombre}: {evaluacion.porcentaje_cumplimiento}% | Semáforo: {evaluacion.semaforo.upper()} | Estado: {evaluacion.estado_habilitacion}")

        # 7. Evaluar Reglas de Alerta
        self.stdout.write("  -> Evaluando motor de alertas preventivas...")
        alertas_generadas = evaluar_reglas_alertas(empresa)
        self.stdout.write(f"     * Alertas preventivas generadas: {alertas_generadas}")

        self.stdout.write(self.style.SUCCESS("\n[OK] Datos de prueba sembrados exitosamente!"))
        self.stdout.write("Ya puedes abrir el frontend y ver todas las matrices, expedientes y brechas con datos reales.")
