"""
Tests de la Matriz Inteligente de Cumplimiento y Habilitación del Cargo (MICHC) — §6.

Cubren:
  - Recálculo de trabajador sin cargo (0% / rojo)
  - Recálculo de trabajador con cumplimiento total (100% / verde / habilitado)
  - Recálculo con examen médico vencido o faltante
  - RN-15: Incompatibilidad médica o no apto genera automáticamente brecha en HBSEO
  - RN-13: Actualización automática de estado_operativo en Trabajador
  - Re-versionamiento de cargo dispara recálculo para sus trabajadores
  - Aislamiento multi-tenant
"""
import uuid
from datetime import date, timedelta
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.perfilcargo.models import PerfilCargo, CargoVersion
from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion
from apps.hbseo.models import Brecha
from apps.michc.models import EvaluacionHabilitacion, DetalleCumplimientoRequisito
from apps.michc.engine import recalcular_habilitacion


def _crear_empresa(nit="900555666-7"):
    return Empresa.objects.create(
        nombre="Empresa MICHC SAS",
        nit=nit,
        num_trabajadores=20,
        nivel_riesgo=4,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable_michc"):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="1000000005",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


def _crear_perfil(empresa, codigo="PC-TEC-01", nombre="Técnico de Alturas", criticidad_sst="alto"):
    return PerfilCargo.objects.create(
        empresa=empresa,
        codigo=codigo,
        nombre_cargo=nombre,
        educacion="Técnico en Mantenimiento o afines",
        experiencia="12 meses de experiencia en mantenimiento",
        criticidad_sst=criticidad_sst,
        criticidad_vial="bajo",
        version_actual=1,
    )


def _crear_trabajador(empresa, perfil=None, nombre="Julián Gómez", documento="1000000055"):
    return Trabajador.objects.create(
        empresa=empresa,
        perfil_cargo=perfil,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="indefinido",
        fecha_ingreso=date.today() - timedelta(days=90),
    )


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class MICHCEngineTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.perfil = _crear_perfil(self.empresa)
        self.trabajador = _crear_trabajador(self.empresa, self.perfil)
        self.today = date.today()

    def test_trabajador_sin_cargo_asignado(self):
        """Un trabajador sin cargo asignado queda en 0% / rojo / pendiente_documental."""
        trabajador_sin_cargo = _crear_trabajador(self.empresa, perfil=None, nombre="Sin Cargo", documento="1000000099")
        evaluacion = recalcular_habilitacion(trabajador_sin_cargo.id)

        self.assertEqual(evaluacion.porcentaje_cumplimiento, 0.0)
        self.assertEqual(evaluacion.semaforo, "rojo")
        self.assertEqual(evaluacion.estado_habilitacion, "pendiente_documental")
        self.assertEqual(trabajador_sin_cargo.estado_operativo, "pendiente_documental")

    def test_cumplimiento_total_habilitado_100_verde(self):
        """
        Trabajador con examen médico vigente apto y afiliaciones a seguridad social
        obtiene 100% / verde / habilitado.
        """
        # Crear examen médico apto
        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="ingreso",
            fecha_examen=self.today - timedelta(days=30),
            fecha_vencimiento=self.today + timedelta(days=335),
            concepto_aptitud="apto",
            presenta_restricciones=False,
        )
        # Crear afiliación
        AfiliacionTrabajador.objects.create(
            trabajador=self.trabajador,
            tipo="arl",
            entidad_nombre="Sura ARL",
        )

        evaluacion = recalcular_habilitacion(self.trabajador.id)

        self.assertEqual(evaluacion.porcentaje_cumplimiento, 100.0)
        self.assertEqual(evaluacion.semaforo, "verde")
        self.assertEqual(evaluacion.estado_habilitacion, "habilitado")
        self.assertEqual(evaluacion.compatibilidad, "compatible")
        
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_operativo, "habilitado")

    def test_examen_medico_vencido_baja_cumplimiento(self):
        """Si el examen médico está vencido, no cumple el requisito y el semáforo cae."""
        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="ingreso",
            fecha_examen=self.today - timedelta(days=400),
            fecha_vencimiento=self.today - timedelta(days=35),  # Vencido
            concepto_aptitud="apto",
        )
        AfiliacionTrabajador.objects.create(
            trabajador=self.trabajador,
            tipo="eps",
            entidad_nombre="Sanitas EPS",
        )

        evaluacion = recalcular_habilitacion(self.trabajador.id)

        self.assertLess(evaluacion.porcentaje_cumplimiento, 100.0)
        self.assertIn(evaluacion.semaforo, ["amarillo", "rojo"])

        # Verificar detalle
        req_medico = evaluacion.detalles_requisitos.filter(tipo_requisito="aptitud_medica").first()
        self.assertIsNotNone(req_medico)
        self.assertEqual(req_medico.cumple, "no")
        self.assertIn("vencido", req_medico.observacion)

    def test_rn15_incompatibilidad_medica_dispara_brecha_hbseo(self):
        """
        RN-15: Si el trabajador tiene restricciones médicas que colisionan con el cargo
        (ej. cargo de alturas y restricción de alturas) o concepto NO APTO:
        - MICHC calcula compatibilidad = 'incompatible_temporal' y estado = 'no_apto'
        - Se dispara automáticamente el registro de una Brecha en HBSEO.
        """
        conteo_brechas_antes = Brecha.objects.filter(empresa=self.empresa).count()

        # Examen con restricción específica para alturas en cargo de alturas
        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="periodico",
            fecha_examen=self.today - timedelta(days=10),
            fecha_vencimiento=self.today + timedelta(days=355),
            concepto_aptitud="apto_con_restricciones",
            presenta_restricciones=True,
            descripcion_restricciones="Restricción severa para trabajo en alturas y vértigo",
        )
        AfiliacionTrabajador.objects.create(
            trabajador=self.trabajador,
            tipo="arl",
            entidad_nombre="Positiva ARL",
        )

        evaluacion = recalcular_habilitacion(self.trabajador.id)

        self.assertEqual(evaluacion.compatibilidad, "incompatible_temporal")
        self.assertEqual(evaluacion.estado_habilitacion, "no_apto")
        
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_operativo, "no_apto")

        # RN-15: Debe haberse registrado una Brecha en HBSEO
        conteo_brechas_despues = Brecha.objects.filter(empresa=self.empresa).count()
        self.assertEqual(conteo_brechas_despues, conteo_brechas_antes + 1)

        brecha = Brecha.objects.filter(trabajador=self.trabajador, clasificacion="incumplimiento").latest("created_at")
        self.assertEqual(brecha.empresa, self.empresa)
        self.assertIn("Incompatibilidad detectada en MICHC", brecha.origenes.first().descripcion)

    def test_reversionamiento_cargo_recalcula_trabajadores(self):
        """
        RN-11 / §4.2: La creación de una nueva versión de cargo dispara el recálculo
        de habilitación para todos los trabajadores asociados.
        """
        with self.captureOnCommitCallbacks(execute=True):
            CargoVersion.objects.create(
                perfil_cargo=self.perfil,
                numero_version=2,
                snapshot={"nombre_cargo": "Técnico de Alturas v2"},
                motivo_cambio="Actualización anual de requisitos",
            )

        # La evaluación debe existir y haber sido calculada
        evaluacion = EvaluacionHabilitacion.objects.filter(trabajador=self.trabajador).first()
        self.assertIsNotNone(evaluacion)

    def test_endpoint_matriz_michc_y_resumen(self):
        """Prueba de endpoints API de consulta y resumen de la matriz."""
        recalcular_habilitacion(self.trabajador.id)

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        # Listado de matriz
        res_list = client.get("/api/michc/matriz/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(res_list.data["results"] if "results" in res_list.data else res_list.data), 1)

        # Resumen métrico
        res_resumen = client.get("/api/michc/matriz/resumen/")
        self.assertEqual(res_resumen.status_code, status.HTTP_200_OK)
        self.assertIn("total_evaluaciones", res_resumen.data)
        self.assertIn("por_semaforo", res_resumen.data)

    def test_aislamiento_multitenant_michc(self):
        """Empresa A no puede ver ni recalcular evaluaciones de Empresa B."""
        otra_empresa = _crear_empresa(nit="900333444-9")
        otro_perfil = _crear_perfil(otra_empresa, codigo="PC-OTRO-01", nombre="Otro Cargo")
        otro_trabajador = _crear_trabajador(otra_empresa, otro_perfil, "Trabajador Ajeno", "987654321")
        eval_ajena = recalcular_habilitacion(otro_trabajador.id)

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        # Consulta directa
        res = client.get(f"/api/michc/matriz/{eval_ajena.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
