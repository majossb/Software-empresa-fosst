"""
apps/common/tests/test_manejo_errores_global.py
Suite de Pruebas Automatizadas para Auditoría y Manejo Global de Errores
FOSST V.I.D.A.
"""
from datetime import timedelta
import secrets

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario, UserRole, TokenActivacion, CodigoOTP
from apps.empresas.models import Empresa


class ManejoErroresGlobalTest(TestCase):
    def setUp(self):
        self.client = APIClient(HTTP_HOST="testserver")
        
        # Empresa y usuario base para pruebas de duplicidad
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa Alpha S.A.S.",
            nit="900111222",
            num_trabajadores=10,
            nivel_riesgo=1,
            capitulo_vigente="I",
            estado=Empresa.Estado.ACTIVA,
        )
        self.usuario_a = Usuario.objects.create(
            username="10001_900111222",
            first_name="Juan",
            last_name="Pérez",
            documento="10001",
            email="juan.alpha@empresa.com",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a,
            activo=False,
            is_active=False,
            email_verificado=False,
        )
        self.usuario_a.set_password("Password123!")
        self.usuario_a.save()

    def test_01_email_already_exists(self):
        """1. Intentar registrar empresa con correo ya existente -> EMAIL_ALREADY_EXISTS"""
        payload = {
            "nombre": "Empresa Beta S.A.S.",
            "nit": "900999888",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "20002",
            "responsable_email": "juan.alpha@empresa.com",  # Ya existe
            "responsable_password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertEqual(res.data["code"], "VALIDATION_ERROR")
        self.assertIn("responsable_email", res.data["errors"])
        self.assertIn("ya está registrado", res.data["errors"]["responsable_email"][0])

    def test_02_nit_already_exists(self):
        """2. Intentar registrar empresa con NIT ya existente -> NIT_ALREADY_EXISTS"""
        payload = {
            "nombre": "Empresa Gamma S.A.S.",
            "nit": "900111222",  # Ya existe
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "20002",
            "responsable_email": "carlos.gamma@empresa.com",
            "responsable_password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertEqual(res.data["code"], "VALIDATION_ERROR")
        self.assertIn("nit", res.data["errors"])
        self.assertIn("ya está registrado", res.data["errors"]["nit"][0])

    def test_03_invalid_document(self):
        """3. Documento con formato inválido (letras/vacío) -> INVALID_DOCUMENT"""
        payload = {
            "nombre": "Empresa Delta S.A.S.",
            "nit": "900555444",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "abc",  # No numérico
            "responsable_email": "carlos.delta@empresa.com",
            "responsable_password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("responsable_documento", res.data["errors"])

    def test_04_invalid_name(self):
        """4. Nombre con números o caracteres inválidos -> INVALID_NAME"""
        payload = {
            "nombre": "Empresa Epsilon S.A.S.",
            "nit": "900666777",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos123",  # Números en nombre
            "responsable_documento": "30003",
            "responsable_email": "carlos.epsilon@empresa.com",
            "responsable_password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("responsable_nombre", res.data["errors"])

    def test_05_invalid_email(self):
        """5. Email mal escrito -> INVALID_EMAIL"""
        payload = {
            "nombre": "Empresa Zeta S.A.S.",
            "nit": "900777888",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "40004",
            "responsable_email": "correo_invalido.com",
            "responsable_password": "Password123!",
            "confirm_password": "Password123!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("responsable_email", res.data["errors"])

    def test_06_invalid_password(self):
        """6. Contraseña que no cumple la política -> INVALID_PASSWORD"""
        payload = {
            "nombre": "Empresa Eta S.A.S.",
            "nit": "900888999",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "50005",
            "responsable_email": "carlos.eta@empresa.com",
            "responsable_password": "123",  # Débil
            "confirm_password": "123",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("responsable_password", res.data["errors"])

    def test_07_password_mismatch(self):
        """7. Confirmación de contraseña no coincide -> PASSWORD_MISMATCH"""
        payload = {
            "nombre": "Empresa Theta S.A.S.",
            "nit": "900123999",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Gómez",
            "responsable_documento": "60006",
            "responsable_email": "carlos.theta@empresa.com",
            "responsable_password": "Password123!",
            "confirm_password": "PasswordDiferente1!",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("confirm_password", res.data["errors"])

    def test_08_required_field_missing(self):
        """8. Falta campo obligatorio -> VALIDATION_ERROR estructurado"""
        payload = {
            "nombre": "",
            "nit": "",
        }
        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertEqual(res.data["code"], "VALIDATION_ERROR")
        self.assertIn("nombre", res.data["errors"])
        self.assertIn("nit", res.data["errors"])

    def test_09_resource_not_found_404(self):
        """9. Endpoint o recurso inexistente en DRF -> RESOURCE_NOT_FOUND amigable"""
        self.client.force_authenticate(user=self.usuario_a)
        res = self.client.get("/api/empresa/00000000-0000-0000-0000-000000000000")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(res.data["success"])
        self.assertEqual(res.data["code"], "RESOURCE_NOT_FOUND")
        self.assertEqual(res.data["message"], "El recurso solicitado no existe.")
        self.assertNotIn("traceback", res.data)
        self.assertNotIn("exception", res.data)



    def test_10_account_not_activated_403(self):
        """10. Intentar login con cuenta no activada -> HTTP 403 amigable"""
        payload = {
            "nit": "900111222",
            "documento": "10001",
            "password": "Password123!",
        }
        res = self.client.post("/api/auth/login/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(res.data["success"])
        self.assertIn("activada", res.data["message"])

    def test_11_invalid_activation_token(self):
        """11. Token de activación inválido -> HTTP 400 amigable"""
        res = self.client.post("/api/auth/activar/", {"token": "token_falso_9999"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("inválido", res.data["message"])

    def test_12_expired_activation_token(self):
        """12. Token de activación expirado -> HTTP 400 amigable"""
        tok = TokenActivacion.objects.create(
            usuario=self.usuario_a,
            token=secrets.token_urlsafe(32),
            expira_en=timezone.now() - timedelta(hours=1),
        )
        res = self.client.post("/api/auth/activar/", {"token": tok.token}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])

    def test_13_invalid_otp(self):
        """13. Código OTP incorrecto -> HTTP 400 amigable"""
        otp = CodigoOTP.crear_para(self.usuario_a, CodigoOTP.Proposito.LOGIN)
        res = self.client.post("/api/auth/verificar-otp/", {
            "usuario_id": str(self.usuario_a.id),
            "codigo": "000000" if otp.codigo != "000000" else "999999",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
        self.assertIn("código", res.data["message"].lower())

    def test_14_not_authenticated_401(self):
        """14. Endpoint protegido sin credenciales -> NOT_AUTHENTICATED"""
        res = self.client.get("/api/auth/me/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(res.data["success"])
        self.assertEqual(res.data["code"], "NOT_AUTHENTICATED")

    def test_15_standard_response_schema_integrity(self):
        """15. Verificación de que NINGÚN error expone tracebacks, SQL ni exceptions"""
        res = self.client.post("/api/empresa/registro", {}, format="json")
        self.assertIn("success", res.data)
        self.assertIn("code", res.data)
        self.assertIn("message", res.data)
        self.assertNotIn("Traceback", str(res.data))
        self.assertNotIn("psycopg2", str(res.data))
        self.assertNotIn("IntegrityError", str(res.data))
        self.assertNotIn("django.db", str(res.data))
