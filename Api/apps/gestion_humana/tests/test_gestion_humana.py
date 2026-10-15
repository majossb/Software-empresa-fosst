"""
Tests de Gestión Humana y Administración Laboral (§5).

Cubren:
  - Jerarquía determinista de precedencia de novedades solapadas
  - Recálculo automático de estado_contractual via signals (post_save / post_delete)
  - Periodo de prueba vs. estado activo
  - Trabajador retirado
  - Confirmación de diseño: ExamenMedico con restricciones no genera brecha directa
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
from apps.hbseo.models import Brecha
from apps.gestion_humana.models import NovedadLaboral, ExamenMedicoOcupacional, LicenciaConduccion
from apps.gestion_humana.services import recalcular_estado_contractual


def _crear_empresa(nit="900123456-1"):
    return Empresa.objects.create(
        nombre="Empresa Test SAS",
        nit=nit,
        num_trabajadores=10,
        nivel_riesgo=2,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable_gh"):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="1000000002",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


def _crear_trabajador(empresa, nombre="Pedro Pérez", documento="1000000010"):
    return Trabajador.objects.create(
        empresa=empresa,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="fijo",
        fecha_ingreso=date.today() - timedelta(days=60),
    )


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class NovedadLaboralPrecedenciaTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.trabajador = _crear_trabajador(self.empresa)
        self.today = date.today()

    def test_novedad_vacaciones_actualiza_estado(self):
        """Una novedad de vacaciones activa cambia el estado contractual a 'vacaciones'."""
        with self.captureOnCommitCallbacks(execute=True):
            NovedadLaboral.objects.create(
                trabajador=self.trabajador,
                tipo="vacaciones",
                fecha_inicio=self.today - timedelta(days=2),
                fecha_fin=self.today + timedelta(days=10),
            )

        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_contractual, "vacaciones")

    def test_jerarquia_incapacidad_prevalece_sobre_vacaciones(self):
        """
        Jerarquía de precedencia: Si un trabajador tiene vacaciones vigentes
        y entra en incapacidad médica simultánea, el estado DEBE ser 'incapacidad'.
        """
        NovedadLaboral.objects.create(
            trabajador=self.trabajador,
            tipo="vacaciones",
            fecha_inicio=self.today - timedelta(days=5),
            fecha_fin=self.today + timedelta(days=10),
        )

        with self.captureOnCommitCallbacks(execute=True):
            NovedadLaboral.objects.create(
                trabajador=self.trabajador,
                tipo="incapacidad",
                fecha_inicio=self.today - timedelta(days=1),
                fecha_fin=self.today + timedelta(days=3),
            )

        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_contractual, "incapacidad")

    def test_jerarquia_suspension_prevalece_sobre_licencia(self):
        """Suspensión disciplinaria prevalece sobre licencia."""
        NovedadLaboral.objects.create(
            trabajador=self.trabajador,
            tipo="licencia",
            fecha_inicio=self.today - timedelta(days=2),
            fecha_fin=self.today + timedelta(days=5),
        )

        with self.captureOnCommitCallbacks(execute=True):
            NovedadLaboral.objects.create(
                trabajador=self.trabajador,
                tipo="suspension",
                fecha_inicio=self.today,
                fecha_fin=self.today + timedelta(days=3),
            )

        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_contractual, "suspendido")

    def test_eliminacion_novedad_restaura_estado(self):
        """Eliminar la única novedad activa regresa el estado a 'activo'."""
        novedad = NovedadLaboral.objects.create(
            trabajador=self.trabajador,
            tipo="vacaciones",
            fecha_inicio=self.today - timedelta(days=1),
            fecha_fin=self.today + timedelta(days=5),
        )
        recalcular_estado_contractual(self.trabajador)
        self.assertEqual(self.trabajador.estado_contractual, "vacaciones")

        with self.captureOnCommitCallbacks(execute=True):
            novedad.delete()

        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_contractual, "activo")

    def test_periodo_prueba_contractual(self):
        """Si no hay novedades activas pero está dentro de fechas de prueba, estado es 'periodo_prueba'."""
        self.trabajador.fecha_inicio_periodo_prueba = self.today - timedelta(days=10)
        self.trabajador.fecha_fin_periodo_prueba = self.today + timedelta(days=20)
        self.trabajador.save()

        estado = recalcular_estado_contractual(self.trabajador)
        self.assertEqual(estado, "periodo_prueba")

    def test_trabajador_retirado(self):
        """Trabajador con fecha_retiro anterior o igual a hoy queda como 'retirado'."""
        self.trabajador.fecha_retiro = self.today - timedelta(days=1)
        self.trabajador.save()

        estado = recalcular_estado_contractual(self.trabajador)
        self.assertEqual(estado, "retirado")


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ExamenMedicoYLicenciaTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.trabajador = _crear_trabajador(self.empresa)
        self.today = date.today()

    def test_examen_con_restriccion_no_genera_brecha_hbseo_directa(self):
        """
        Confirmación de diseño: Guardar un examen médico con restricciones
        registra el examen en el expediente pero NO genera una brecha en HBSEO
        de manera directa (se delega a MICHC en Fase 4 para validar si colisiona con el cargo).
        """
        conteo_brechas_antes = Brecha.objects.count()

        examen = ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="periodico",
            fecha_examen=self.today,
            concepto_aptitud="apto_con_restricciones",
            presenta_restricciones=True,
            descripcion_restricciones="Evitar manipulación de cargas > 15kg",
        )

        self.assertIsNotNone(examen.pk)
        # No se crearon brechas directas no reconciliadas
        self.assertEqual(Brecha.objects.count(), conteo_brechas_antes)

    def test_licencia_conduccion_registro(self):
        """Registro de licencia de conducción en el expediente."""
        licencia = LicenciaConduccion.objects.create(
            trabajador=self.trabajador,
            categoria="C2",
            fecha_vencimiento=self.today + timedelta(days=365),
            presenta_restricciones=True,
            descripcion_restricciones="Requiere lentes correctivos",
        )
        self.assertEqual(self.trabajador.licencias_conduccion.count(), 1)
        self.assertEqual(licencia.categoria, "C2")

    def test_expediente_unificado_endpoint(self):
        """Consulta del expediente unificado del trabajador via API."""
        NovedadLaboral.objects.create(
            trabajador=self.trabajador,
            tipo="vacaciones",
            fecha_inicio=self.today,
            fecha_fin=self.today + timedelta(days=5),
        )
        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="ingreso",
            fecha_examen=self.today - timedelta(days=30),
        )
        LicenciaConduccion.objects.create(
            trabajador=self.trabajador,
            categoria="B1",
            fecha_vencimiento=self.today + timedelta(days=100),
        )

        client = APIClient()
        client.force_authenticate(user=self.usuario)

        response = client.get(f"/api/gestion-humana/expediente/{self.trabajador.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(len(data["novedades"]), 1)
        self.assertEqual(len(data["examenes_medicos"]), 1)
        self.assertEqual(len(data["licencias_conduccion"]), 1)
        self.assertEqual(data["trabajador"]["nombre"], "Pedro Pérez")

    def test_descargar_plantilla_importacion(self):
        """Prueba descarga de plantilla oficial de importación masiva."""
        client = APIClient()
        client.force_authenticate(user=self.usuario)
        response = client.get("/api/gestion-humana/plantilla-importacion/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    def test_importar_trabajadores_masivo_csv(self):
        """Prueba importación masiva desde archivo CSV."""
        from io import BytesIO
        csv_content = (
            "documento,nombre,apellidos,email,cargo,tipo_contrato,fecha_ingreso,salario\n"
            "10055,Maria,Lopez,maria@test.com,Auxiliar,indefinido,2026-01-15,1500000\n"
            "10056,Juan,Torres,juan.t@test.com,Operario,fijo,2026-02-01,1800000\n"
        ).encode("utf-8")

        f = BytesIO(csv_content)
        f.name = "trabajadores.csv"

        client = APIClient()
        client.force_authenticate(user=self.usuario)
        response = client.post("/api/gestion-humana/importar-masivo/", {"archivo": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("creadas"), 2)


