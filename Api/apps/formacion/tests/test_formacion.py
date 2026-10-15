"""
Tests de Formación y Desarrollo — Matriz de Competencias del Cargo (MCC) — §9.

Cubren:
  - Cálculo automático de brecha (brecha_calculada = max(0, requerido - alcanzado))
  - Registro automático en HBSEO cuando hay brecha > 0
  - Omisión de registro en HBSEO cuando no hay brecha (cumple o supera)
  - Disparo de recálculo en MICHC tras evaluar competencia
  - Endpoint de matriz de competencias del trabajador
  - Aislamiento multi-tenant
"""
import uuid
from datetime import date, timedelta
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from apps.hbseo.models import Brecha
from apps.michc.models import EvaluacionHabilitacion
from apps.formacion.models import EvaluacionCompetencia


def _crear_empresa(nit="900777888-9"):
    return Empresa.objects.create(
        nombre="Empresa Formación SAS",
        nit=nit,
        num_trabajadores=25,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable_formacion"):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="1000000008",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


def _crear_perfil(empresa, codigo="PC-OP-01", nombre="Operario de Planta"):
    return PerfilCargo.objects.create(
        empresa=empresa,
        codigo=codigo,
        nombre_cargo=nombre,
        educacion="Bachiller / Técnico",
        experiencia="6 meses",
        version_actual=1,
    )


def _crear_competencia(perfil, nombre="Operación de Maquinaria", tipo="tecnica", nivel_requerido=3):
    return CargoCompetencia.objects.create(
        perfil_cargo=perfil,
        nombre=nombre,
        tipo=tipo,
        nivel_requerido=nivel_requerido,
        nivel=nivel_requerido,
    )


def _crear_trabajador(empresa, perfil=None, nombre="Andrés Castro", documento="1000000088"):
    return Trabajador.objects.create(
        empresa=empresa,
        perfil_cargo=perfil,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="indefinido",
        fecha_ingreso=date.today() - timedelta(days=120),
    )


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class FormacionCompetenciasTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.perfil = _crear_perfil(self.empresa)
        self.competencia_tecnica = _crear_competencia(self.perfil, nombre="Manejo de Montacargas", nivel_requerido=3)
        self.competencia_blanda = _crear_competencia(self.perfil, nombre="Trabajo en Equipo", tipo="blanda", nivel_requerido=2)
        self.trabajador = _crear_trabajador(self.empresa, self.perfil)
        self.today = date.today()

    def test_evaluacion_con_brecha_genera_brecha_en_hbseo(self):
        """
        Una evaluación con nivel alcanzado menor al requerido genera brecha calculada
        y registra automáticamente la brecha en HBSEO.
        """
        conteo_brechas_antes = Brecha.objects.filter(empresa=self.empresa).count()

        with self.captureOnCommitCallbacks(execute=True):
            evaluacion = EvaluacionCompetencia.objects.create(
                trabajador=self.trabajador,
                cargo_competencia=self.competencia_tecnica,
                nivel_alcanzado=1,  # Requerido = 3 -> Brecha = 2
                evaluado_por=self.usuario,
                fecha_evaluacion=self.today,
                metodo="prueba_tecnica",
            )

        self.assertEqual(evaluacion.brecha_calculada, 2)

        # Debe haberse registrado en HBSEO
        conteo_brechas_despues = Brecha.objects.filter(empresa=self.empresa).count()
        self.assertEqual(conteo_brechas_despues, conteo_brechas_antes + 1)

        brecha = Brecha.objects.filter(trabajador=self.trabajador, clasificacion="incumplimiento").latest("created_at")
        self.assertEqual(brecha.empresa, self.empresa)
        self.assertIn("Manejo de Montacargas", brecha.origenes.first().descripcion)

    def test_evaluacion_sin_brecha_no_genera_hbseo(self):
        """Si el nivel alcanzado cumple o supera el requerido, la brecha es 0 y NO crea registro en HBSEO."""
        conteo_brechas_antes = Brecha.objects.filter(empresa=self.empresa).count()

        with self.captureOnCommitCallbacks(execute=True):
            evaluacion = EvaluacionCompetencia.objects.create(
                trabajador=self.trabajador,
                cargo_competencia=self.competencia_tecnica,
                nivel_alcanzado=3,  # Requerido = 3 -> Brecha = 0
                evaluado_por=self.usuario,
                fecha_evaluacion=self.today,
                metodo="certificacion",
            )

        self.assertEqual(evaluacion.brecha_calculada, 0)
        self.assertEqual(Brecha.objects.filter(empresa=self.empresa).count(), conteo_brechas_antes)

    def test_matriz_competencias_trabajador_endpoint(self):
        """El endpoint matriz-trabajador devuelve todas las competencias del cargo y su estado de evaluación."""
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=self.competencia_tecnica,
            nivel_alcanzado=2,
            evaluado_por=self.usuario,
            fecha_evaluacion=self.today,
        )

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        res = client.get(f"/api/formacion/evaluaciones/matriz-trabajador/{self.trabajador.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data

        self.assertEqual(data["trabajador"]["nombre"], "Andrés Castro")
        self.assertEqual(len(data["competencias"]), 2)

        comp_tecnica = next(c for c in data["competencias"] if c["nombre"] == "Manejo de Montacargas")
        self.assertEqual(comp_tecnica["nivel_requerido"], 3)
        self.assertEqual(comp_tecnica["nivel_alcanzado"], 2)
        self.assertEqual(comp_tecnica["brecha"], 1)
        self.assertFalse(comp_tecnica["cumple"])

        comp_blanda = next(c for c in data["competencias"] if c["nombre"] == "Trabajo en Equipo")
        self.assertEqual(comp_blanda["nivel_alcanzado"], 0)
        self.assertEqual(comp_blanda["brecha"], 2)

    def test_resumen_metricas_formacion(self):
        """Endpoint de resumen métrico de competencias."""
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=self.competencia_tecnica,
            nivel_alcanzado=1,
            fecha_evaluacion=self.today,
        )
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=self.competencia_blanda,
            nivel_alcanzado=2,
            fecha_evaluacion=self.today,
        )

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        res = client.get("/api/formacion/evaluaciones/resumen/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["total_evaluaciones"], 2)
        self.assertEqual(res.data["evaluaciones_con_brecha"], 1)
        self.assertEqual(res.data["evaluaciones_optimas"], 1)

    def test_aislamiento_multitenant_formacion(self):
        """Empresa A no puede consultar evaluaciones de Empresa B."""
        otra_empresa = _crear_empresa(nit="900444333-1")
        otro_perfil = _crear_perfil(otra_empresa, codigo="PC-OTRA-01", nombre="Otro")
        otro_trabajador = _crear_trabajador(otra_empresa, otro_perfil, "Trabajador Ajeno", "123456789")

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        res = client.get(f"/api/formacion/evaluaciones/matriz-trabajador/{otro_trabajador.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
