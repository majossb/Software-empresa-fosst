from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.estandares.models import Estandar, Evaluacion, Respuesta, Apelacion
from apps.auditoria.models import AuditLog


class ApelacionesRFSST03TestCase(TestCase):
    """
    Suite de 15 pruebas unitarias e integrales para el Requerimiento RF-SST-03 / SST-04:
    Apelación de Calificaciones y Observaciones de Auditoría.
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Crear Empresas
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa A S.A.S.",
            nit="900111222-1",
            num_trabajadores=15,
            nivel_riesgo=3,
            capitulo_vigente="I"
        )
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa B S.A.S.",
            nit="900333444-2",
            num_trabajadores=50,
            nivel_riesgo=4,
            capitulo_vigente="II"
        )

        # 2. Crear Usuarios
        self.user_sst_a = Usuario.objects.create(
            username="sst_a",
            email="sst_a@empresa-a.com",
            first_name="Responsable",
            last_name="SST A",
            documento="10001",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a
        )
        self.user_sst_a.set_password("Password123!")
        self.user_sst_a.save()

        self.user_auditor = Usuario.objects.create(
            username="auditor",
            email="auditor@fosst.com",
            first_name="Auditor",
            last_name="SST",
            documento="20002",
            rol=UserRole.AUDITOR,
            empresa=self.empresa_a
        )
        self.user_auditor.set_password("Password123!")
        self.user_auditor.save()

        self.user_sst_b = Usuario.objects.create(
            username="sst_b",
            email="sst_b@empresa-b.com",
            first_name="Responsable",
            last_name="SST B",
            documento="30003",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_b
        )
        self.user_sst_b.set_password("Password123!")
        self.user_sst_b.save()

        # 3. Crear Estándar
        self.estandar_1 = Estandar.objects.create(
            codigo="1.1.1",
            nombre="Asignación de responsable del SG-SST",
            capitulo="I",
            ciclo_phva="Planear",
            puntaje_maximo=Decimal("5.00")
        )

        # 4. Crear Evaluación y Respuesta para Empresa A
        self.evaluacion_a = Evaluacion.objects.create(
            empresa=self.empresa_a,
            anio=2026,
            capitulo="I",
            estado=Evaluacion.Estado.EN_PROGRESO,
            puntaje_total=Decimal("50.00")
        )
        self.respuesta_a = Respuesta.objects.create(
            evaluacion=self.evaluacion_a,
            estandar=self.estandar_1,
            estado=Respuesta.Estado.NO_CUMPLE,
            puntaje=Decimal("0.00"),
            observacion="Falta firma del representante legal en el soporte entregado."
        )

        # 5. Crear Evaluación y Respuesta para Empresa B
        self.evaluacion_b = Evaluacion.objects.create(
            empresa=self.empresa_b,
            anio=2026,
            capitulo="II",
            estado=Evaluacion.Estado.EN_PROGRESO,
            puntaje_total=Decimal("40.00")
        )
        self.respuesta_b = Respuesta.objects.create(
            evaluacion=self.evaluacion_b,
            estandar=self.estandar_1,
            estado=Respuesta.Estado.NO_CUMPLE,
            puntaje=Decimal("0.00"),
            observacion="Observación para Empresa B"
        )

    def test_sst04_01_auditor_observacion_registrada(self):
        """SST04-01: Verificar que la observación de auditoría existe asociada a la respuesta."""
        self.assertIsNotNone(self.respuesta_a.observacion)
        self.assertIn("Falta firma", self.respuesta_a.observacion)

    def test_sst04_02_responsable_sst_ve_observaciones(self):
        """SST04-02: El responsable SST puede visualizar la respuesta con observación."""
        self.client.force_authenticate(user=self.user_sst_a)
        res = self.client.get("/api/estandares/respuestas")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get("estandares", res.data) if isinstance(res.data, dict) else res.data
        item = next((i for i in items if i.get("id") == str(self.respuesta_a.id) or i.get("codigo") == self.estandar_1.codigo), None)
        self.assertIsNotNone(item)

    def test_sst04_03_crear_apelacion_valida(self):
        """SST04-03: Creación exitosa de apelación con motivo válido."""
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "Se adjunta el documento escaneado con la firma requerida del representante legal."
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data.get("data", res.data)
        self.assertEqual(data["estado"], "pendiente")
        self.assertEqual(data["solicitante_email"], self.user_sst_a.email)

    def test_sst04_04_rechazar_motivo_vacio_o_espacios(self):
        """SST04-04: Rechazar creación de apelación si el motivo está vacío o solo contiene espacios."""
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "    "
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("motivo" in res.data or "motivo" in res.data.get("errors", {}))

    def test_sst04_05_respuesta_inexistente(self):
        """SST04-05: Error 400/404 al intentar apelar una respuesta inexistente."""
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "respuesta": "00000000-0000-0000-0000-000000000000",
            "motivo": "Motivo para respuesta inexistente"
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertTrue(res.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_sst04_06_aislamiento_multitenant_creacion(self):
        """SST04-06: Empresa B no puede apelar una respuesta de Empresa A."""
        self.client.force_authenticate(user=self.user_sst_b)
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "Empresa B intentando apelar respuesta de Empresa A"
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertTrue(res.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_sst04_07_persistencia_post_reinicio_sesion(self):
        """SST04-07: La apelación persiste en BD en estado pendiente."""
        apelacion = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Soporte adjunto adecuadamente."
        )
        self.client.force_authenticate(user=self.user_sst_a)
        res = self.client.get(f"/api/apelaciones/{apelacion.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["estado"], "pendiente")

    def test_sst04_08_rechazo_usuario_no_autenticado(self):
        """SST04-08: Peticiones no autenticadas devuelven 401 Unauthorized."""
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "Usuario no autenticado"
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_sst04_09_prevencion_duplicados_activos(self):
        """SST04-09: Prevenir apelaciones duplicadas para la misma respuesta si ya hay una PENDIENTE."""
        Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Primera apelación"
        )
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "Segunda apelación mientras la primera está pendiente"
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sst04_10_resolucion_por_auditor(self):
        """SST04-10: Auditor puede resolver una apelación (aceptar o rechazar)."""
        apelacion = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Revisión de firma"
        )
        self.client.force_authenticate(user=self.user_auditor)
        payload = {
            "decision": "aceptada",
            "respuesta_auditor": "Se verifica que el documento contiene la firma digital válida."
        }
        res = self.client.post(f"/api/apelaciones/{apelacion.id}/resolver/", payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        apelacion.refresh_from_db()
        self.assertEqual(apelacion.estado, Apelacion.Estado.ACEPTADA)
        self.assertEqual(apelacion.respuesta_auditor, payload["respuesta_auditor"])

    def test_sst04_11_audit_log_al_crear(self):
        """SST04-11: Se genera registro en AuditLog al crear una apelación."""
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "respuesta": str(self.respuesta_a.id),
            "motivo": "Prueba de AuditLog en creación"
        }
        res = self.client.post("/api/apelaciones/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        log = AuditLog.objects.filter(accion="CREAR_APELACION", usuario=self.user_sst_a).first()
        self.assertIsNotNone(log)

    def test_sst04_12_audit_log_al_resolver(self):
        """SST04-12: Se genera registro en AuditLog al resolver una apelación."""
        apelacion = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Revisión de auditoría"
        )
        self.client.force_authenticate(user=self.user_auditor)
        payload = {
            "decision": "rechazada",
            "respuesta_auditor": "No cumple con el requisito legal."
        }
        res = self.client.post(f"/api/apelaciones/{apelacion.id}/resolver/", payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        log = AuditLog.objects.filter(accion="RESOLVER_APELACION", usuario=self.user_auditor).first()
        self.assertIsNotNone(log)

    def test_sst04_13_aislamiento_multitenant_listado(self):
        """SST04-13: Empresa B no puede ver apelaciones de Empresa A en el listado."""
        Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Apelación de Empresa A"
        )
        self.client.force_authenticate(user=self.user_sst_b)
        res = self.client.get("/api/apelaciones/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data.get("results", res.data) if isinstance(res.data, dict) else res.data
        self.assertEqual(len(items), 0)

    def test_sst04_14_aislamiento_multitenant_detalle_directo(self):
        """SST04-14: Empresa B recibe 404 al acceder directamente al detalle de apelación de Empresa A."""
        apelacion = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Apelación de Empresa A"
        )
        self.client.force_authenticate(user=self.user_sst_b)
        res = self.client.get(f"/api/apelaciones/{apelacion.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_sst04_15_rechazo_resolucion_por_responsable_sst(self):
        """SST04-15: Usuario Responsable SST no puede resolver apelaciones (devuelve 403)."""
        apelacion = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.user_sst_a,
            motivo="Apelación pendiente"
        )
        self.client.force_authenticate(user=self.user_sst_a)
        payload = {
            "decision": "aceptada",
            "respuesta_auditor": "Auto-aprobación no permitida"
        }
        res = self.client.post(f"/api/apelaciones/{apelacion.id}/resolver/", payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
