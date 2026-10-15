import hashlib
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Usuario, UserRole
from apps.empresas.models import Empresa
from apps.planes.models import Plan, Suscripcion
from apps.estandares.models import Estandar, Evaluacion, Respuesta
from apps.evidencias.models import Archivo, Evidencia
from apps.planes.decorators import verificar_acceso_plan


class Fase1IntegridadSeguridadTest(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Test Fase 1",
            nit="900123456-1",
            sector_economico="Tecnología",
            nivel_riesgo=1,
            num_trabajadores=10,
        )

        self.user_responsable = Usuario.objects.create_user(
            username="responsable_fase1",
            email="responsable@fase1.com",
            password="Password123!",
            first_name="Responsable",
            last_name="Test",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa,
        )

        self.user_admin = Usuario.objects.create_user(
            username="admin_fase1",
            email="admin@fase1.com",
            password="Password123!",
            first_name="Admin",
            last_name="Test",
            rol=UserRole.ADMIN,
        )

        self.client = APIClient()

    def test_evidencia_soft_delete_y_hash(self):
        """Verifica que la evidencia implemente soft-delete (deleted_at) y cálculo de hash SHA-256."""
        evaluacion = Evaluacion.objects.create(empresa=self.empresa, anio=2026, capitulo="II")
        estandar = Estandar.objects.create(
            codigo="1.1.1",
            nombre="Estándar Test",
            capitulo="II",
            ciclo_phva="Planear",
            puntaje_maximo=4.0,
        )
        respuesta = Respuesta.objects.create(evaluacion=evaluacion, estandar=estandar, estado="cumple")

        archivo_hash = hashlib.sha256(b"contenido de prueba").hexdigest()
        archivo = Archivo.objects.create(
            nombre="prueba.pdf",
            url="/media/evidencias/prueba.pdf",
            tipo_mime="application/pdf",
            tamanio_kb=15,
            subido_por=str(self.user_responsable.id),
            sha256_hash=archivo_hash,
        )

        evidencia = Evidencia.objects.create(
            respuesta=respuesta,
            archivo=archivo,
            descripcion="Evidencia de prueba",
        )

        self.assertIsNone(evidencia.deleted_at)
        self.assertEqual(evidencia.archivo.sha256_hash, archivo_hash)

        # Soft delete
        evidencia.delete()
        evidencia.refresh_from_db()
        self.assertIsNotNone(evidencia.deleted_at)
        self.assertTrue(Evidencia.all_objects.filter(id=evidencia.id).exists())
        self.assertFalse(Evidencia.objects.filter(id=evidencia.id).exists())

    def test_gating_por_plan_permitido_y_bloqueado(self):
        """Verifica el bloqueo HTTP 403 cuando el plan no incluye la característica."""
        plan_basico = Plan.objects.create(
            nombre="Plan Básico",
            precio_mensual=100,
            precio_anual=1000,
            max_usuarios=2,
            max_evidencias_mb=100,
            tiene_auditoria=False,
            tiene_informes=False,
            tiene_calendario=False,
        )
        Suscripcion.objects.create(
            empresa=self.empresa,
            plan=plan_basico,
            estado=Suscripcion.Estado.ACTIVA,
            fecha_inicio=timezone.now(),
        )

        # Caso bloqueado para usuario responsable con plan básico
        permitido, mensaje = verificar_acceso_plan(self.user_responsable, "tiene_informes")
        self.assertFalse(permitido)
        self.assertIn("no incluye la funcionalidad de Informes", mensaje)

        # Caso permitido para Superadministrador
        permitido_admin, _ = verificar_acceso_plan(self.user_admin, "tiene_informes")
        self.assertTrue(permitido_admin)

        # Upgrade de plan
        plan_pro = Plan.objects.create(
            nombre="Plan Pro",
            precio_mensual=200,
            precio_anual=2000,
            max_usuarios=10,
            max_evidencias_mb=500,
            tiene_auditoria=True,
            tiene_informes=True,
            tiene_calendario=True,
        )
        Suscripcion.objects.create(
            empresa=self.empresa,
            plan=plan_pro,
            estado=Suscripcion.Estado.ACTIVA,
            fecha_inicio=timezone.now(),
        )

        permitido_upgraded, _ = verificar_acceso_plan(self.user_responsable, "tiene_informes")
        self.assertTrue(permitido_upgraded)
