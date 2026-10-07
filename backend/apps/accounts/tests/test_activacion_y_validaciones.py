from django.test import TestCase, override_settings
from django.core import mail
from rest_framework.test import APIClient
from rest_framework import status
from django.core.exceptions import ValidationError

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, TokenActivacion
from apps.accounts.validators import validar_politica_password, validar_nombre_persona, validar_telefono


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ActivacionCuentaYValidacionesTest(TestCase):
    """
    Pruebas automatizadas para el flujo completo de Activación Obligatoria de Cuenta
    y Auditoría de Validaciones (Nombres en español, contraseñas, teléfonos, login previo/posterior).
    """

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

    def test_01_flujo_registro_empresa_cuenta_pendiente_activacion(self):
        """1. Registro de empresa crea usuario inactivo (pendiente activación) y envía correo de activación"""
        payload = {
            "nombre": "Empresa Test Activacion S.A.S.",
            "nit": "900888777",
            "num_trabajadores": 12,
            "nivel_riesgo": 2,
            "responsable_nombre": "María José Bonilla",
            "responsable_documento": "1077123456",
            "responsable_email": "majo.activacion@test.com",
            "responsable_password": "Password123!",
        }

        res = self.client.post("/api/empresa/registro", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("activar la cuenta", res.data["message"])

        # Verificar usuario en DB (debe estar INACTIVO)
        usuario = Usuario.objects.get(email="majo.activacion@test.com")
        self.assertFalse(usuario.activo)
        self.assertFalse(usuario.is_active)
        self.assertFalse(usuario.email_verificado)

        # Verificar envío de correo con token hacia el frontend
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["majo.activacion@test.com"])
        self.assertIn("http://localhost:5173/activar-cuenta?token=", sent_email.body)

    def test_02_login_bloqueado_antes_de_activacion(self):
        """2. Intento de login antes de la activación devuelve HTTP 403 Forbidden"""
        self.test_01_flujo_registro_empresa_cuenta_pendiente_activacion()

        res_login = self.client.post("/api/auth/login/", {
            "nit": "900888777",
            "documento": "1077123456",
            "password": "Password123!",
        }, format="json")

        self.assertEqual(res_login.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Tu cuenta aún no ha sido activada", res_login.data["message"])

    def test_03_activacion_exitosa_y_login_posterior(self):
        """3. Al activar la cuenta mediante token, el usuario pasa a activo y el login funciona normalmente"""
        self.test_01_flujo_registro_empresa_cuenta_pendiente_activacion()
        mail.outbox = []

        usuario = Usuario.objects.get(email="majo.activacion@test.com")
        token_obj = TokenActivacion.objects.get(usuario=usuario)

        # Activar cuenta vía API
        res_activar = self.client.post("/api/auth/activar/", {
            "token": token_obj.token
        }, format="json")

        self.assertEqual(res_activar.status_code, status.HTTP_200_OK)
        self.assertIn("Cuenta activada correctamente", res_activar.data["message"])

        # Verificar que el usuario ahora está ACTIVO
        usuario.refresh_from_db()
        self.assertTrue(usuario.activo)
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.email_verificado)

        # Ahora el login debe funcionar y generar OTP (HTTP 200 OK)
        res_login = self.client.post("/api/auth/login/", {
            "nit": "900888777",
            "documento": "1077123456",
            "password": "Password123!",
        }, format="json")

        self.assertEqual(res_login.status_code, status.HTTP_200_OK)
        self.assertIn("usuario_id", res_login.data)

    def test_04_validaciones_politica_password_unica(self):
        """4. Pruebas de la Política Única de Seguridad de Contraseñas (8+ chars, mayúscula, minúscula, número, especial)"""
        # Contraseña válida
        validar_politica_password("Password123!")

        # Menos de 8 caracteres
        with self.assertRaises(ValidationError):
            validar_politica_password("Pass1!")

        # Sin mayúscula
        with self.assertRaises(ValidationError):
            validar_politica_password("password123!")

        # Sin minúscula
        with self.assertRaises(ValidationError):
            validar_politica_password("PASSWORD123!")

        # Sin número
        with self.assertRaises(ValidationError):
            validar_politica_password("PasswordSafe!")

    def test_06_backend_confirm_password_validation(self):
        """6. Verificación explícita en Backend: password vs confirm_password/confirmPassword"""
        from apps.empresas.serializers import RegistroEmpresaSerializer

        # Mismatch
        data_mismatch = {
            "nombre": "Empresa Mismatch",
            "nit": "900777111",
            "num_trabajadores": 5,
            "nivel_riesgo": 1,
            "responsable_nombre": "Carlos Perez",
            "responsable_documento": "554433",
            "responsable_email": "carlos.mismatch@test.com",
            "responsable_password": "Password123!",
            "confirm_password": "PasswordMismatch!",
        }
        ser_bad = RegistroEmpresaSerializer(data=data_mismatch)
        self.assertFalse(ser_bad.is_valid())
        self.assertIn("confirm_password", ser_bad.errors)

        # Match
        data_match = {**data_mismatch, "confirm_password": "Password123!"}
        ser_ok = RegistroEmpresaSerializer(data=data_match)
        self.assertTrue(ser_ok.is_valid())

    def test_07_token_activacion_edge_cases(self):
        """7. Verificación de seguridad de tokens: Inválido, Expirado, Reutilizado y Aislamiento"""
        self.test_01_flujo_registro_empresa_cuenta_pendiente_activacion()
        usuario_a = Usuario.objects.get(email="majo.activacion@test.com")
        token_obj_a = TokenActivacion.objects.get(usuario=usuario_a)

        # A. Token inexistente / inválido -> Rechazo 400
        res_invalid = self.client.post("/api/auth/activar/", {"token": "token_inventado_12345"}, format="json")
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("inválido", res_invalid.data["message"])

        # B. Token expirado -> Rechazo 400
        from django.utils import timezone
        from datetime import timedelta
        token_obj_a.expira_en = timezone.now() - timedelta(hours=1)
        token_obj_a.save()

        res_expired = self.client.post("/api/auth/activar/", {"token": token_obj_a.token}, format="json")
        self.assertEqual(res_expired.status_code, status.HTTP_400_BAD_REQUEST)

        # Restablecer vigencia para probar reutilización
        token_obj_a.expira_en = timezone.now() + timedelta(hours=24)
        token_obj_a.usado = False
        token_obj_a.save()

        # C. Activar exitosamente primera vez
        res_first = self.client.post("/api/auth/activar/", {"token": token_obj_a.token}, format="json")
        self.assertEqual(res_first.status_code, status.HTTP_200_OK)

        # D. Token reutilizado -> Rechazo 400
        res_reused = self.client.post("/api/auth/activar/", {"token": token_obj_a.token}, format="json")
        self.assertEqual(res_reused.status_code, status.HTTP_400_BAD_REQUEST)
