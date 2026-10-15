from django.test import TestCase, override_settings
from django.core import mail
from django.core.management import call_command
from rest_framework.test import APIClient
from rest_framework import status
from io import StringIO

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, CodigoOTP
from apps.reclutamiento.models import Candidato, ProcesoSeleccion
from apps.accounts.tasks import enviar_email_task
from apps.seguridad.notificaciones import notificar_acceso_inusual
from apps.reclutamiento.services.portal import generar_token_acceso_candidato


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SMTPMultiTenantEmailTest(TestCase):
    """
    Suite de pruebas para validar la migración de Resend API a SMTP Nativo Django,
    asincronía con Celery, destinatarios dinámicos y aislamiento multi-tenancy estricto.
    """

    def setUp(self):
        self.client = APIClient()
        mail.outbox = []

        # Crear Empresa A y Usuario A
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa A de Prueba S.A.S.",
            nit="900100200",
            num_trabajadores=10,
            nivel_riesgo=1,
            capitulo_vigente="I",
        )
        self.usuario_a = Usuario.objects.create(
            username="1001_900100200",
            first_name="Usuario",
            last_name="Empresa A",
            documento="1001",
            email="usuario_a@empresaA.test",
            rol="RESPONSABLE",
            empresa=self.empresa_a,
            activo=True,
            is_active=True,
        )
        self.usuario_a.set_password("Password123!")
        self.usuario_a.save()

        # Crear Empresa B y Usuario B
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa B de Prueba S.A.S.",
            nit="900300400",
            num_trabajadores=25,
            nivel_riesgo=3,
            capitulo_vigente="II",
        )
        self.usuario_b = Usuario.objects.create(
            username="2002_900300400",
            first_name="Usuario",
            last_name="Empresa B",
            documento="2002",
            email="usuario_b@empresaB.test",
            rol="RESPONSABLE",
            empresa=self.empresa_b,
            activo=True,
            is_active=True,
        )
        self.usuario_b.set_password("Password123!")
        self.usuario_b.save()

    def test_01_flujo_login_otp_usuario_a(self):
        """1. OTP de Login para Usuario A debe enviarse a usuario_a@empresaA.test vía Celery/SMTP"""
        mail.outbox = []
        res = self.client.post("/api/auth/login/", {
            "nit": self.empresa_a.nit,
            "documento": self.usuario_a.documento,
            "password": "Password123!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["usuario_a@empresaA.test"])
        self.assertIn("código de verificación", sent_email.subject.lower())
        self.assertNotIn("usuario_b@empresaB.test", sent_email.to)

    def test_02_flujo_login_otp_usuario_b(self):
        """2. OTP de Login para Usuario B debe enviarse a usuario_b@empresaB.test vía Celery/SMTP"""
        mail.outbox = []
        res = self.client.post("/api/auth/login/", {
            "nit": self.empresa_b.nit,
            "documento": self.usuario_b.documento,
            "password": "Password123!",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["usuario_b@empresaB.test"])
        self.assertNotIn("usuario_a@empresaA.test", sent_email.to)

    def test_03_flujo_reset_password_usuario_a(self):
        """3. Solicitud de reset password para Usuario A se envía a usuario_a@empresaA.test"""
        mail.outbox = []
        res = self.client.post("/api/auth/password/solicitar-reset/", {
            "email": "usuario_a@empresaA.test"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["usuario_a@empresaA.test"])
        self.assertIn("http://localhost:5173/reset-password?token=", sent_email.body)
        self.assertNotIn(":8000/reset-password", sent_email.body)

        # Extraer token y probar flujo completo de reseteo + ciclo de vida de token único
        token_str = sent_email.body.split("token=")[1].split()[0]

        # 3a. Cambiar contraseña exitosamente
        res_confirm = self.client.post("/api/auth/password/confirmar-reset/", {
            "token": token_str,
            "password": "NewPassword123!"
        }, format="json")
        self.assertEqual(res_confirm.status_code, status.HTTP_200_OK)

        # 3b. Verificar que la nueva contraseña funciona en el usuario
        self.usuario_a.refresh_from_db()
        self.assertTrue(self.usuario_a.check_password("NewPassword123!"))

        # 3c. Reutilizar el mismo token debe ser rechazado (token de uso único)
        res_reuse = self.client.post("/api/auth/password/confirmar-reset/", {
            "token": token_str,
            "password": "AnotherPassword123!"
        }, format="json")
        self.assertEqual(res_reuse.status_code, status.HTTP_400_BAD_REQUEST)

    def test_04_flujo_reset_password_usuario_b(self):
        """4. Solicitud de reset password para Usuario B se envía a usuario_b@empresaB.test"""
        mail.outbox = []
        res = self.client.post("/api/auth/password/solicitar-reset/", {
            "email": "usuario_b@empresaB.test"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ["usuario_b@empresaB.test"])

    def test_05_aislamiento_multitenant_estricto(self):
        """5. Verificación explícita: A nunca recibe correos de B, B nunca recibe correos de A"""
        mail.outbox = []
        
        # Disparar alertas de acceso para ambos usuarios
        notificar_acceso_inusual(self.usuario_a, "192.168.1.100", "Mozilla/5.0")
        notificar_acceso_inusual(self.usuario_b, "10.0.0.50", "Chrome/110")

        self.assertEqual(len(mail.outbox), 2)
        recipientes = [msg.to[0] for msg in mail.outbox]
        self.assertIn("usuario_a@empresaA.test", recipientes)
        self.assertIn("usuario_b@empresaB.test", recipientes)

        # Confirmar que cada mensaje fue dirigido al email exacto de su propio tenant
        msg_a = next(m for m in mail.outbox if m.to == ["usuario_a@empresaA.test"])
        msg_b = next(m for m in mail.outbox if m.to == ["usuario_b@empresaB.test"])
        
        self.assertIn(self.usuario_a.first_name, msg_a.body)
        self.assertIn(self.usuario_b.first_name, msg_b.body)

    def test_06_flujo_otp_candidato_reclutamiento(self):
        """6. OTP de Candidatos se envía dinámicamente al correo del candidato"""
        mail.outbox = []
        candidato = Candidato.objects.create(
            empresa=self.empresa_a,
            nombres="Carlos",
            apellidos="Candidato",
            documento="998877",
            email="candidato_carlos@test.com",
        )

        token_obj = generar_token_acceso_candidato(candidato=candidato, ip_solicitud="127.0.0.1")
        self.assertIsNotNone(token_obj)
        self.assertEqual(len(mail.outbox), 1)
        
        sent_msg = mail.outbox[0]
        self.assertEqual(sent_msg.to, ["candidato_carlos@test.com"])
        self.assertIn("Código de acceso a tu portal", sent_msg.subject)

    def test_07_tarea_celery_enviar_email_task_smtp(self):
        """7. Tarea Celery enviar_email_task envía correctamente vía SMTP (locmem en testing)"""
        mail.outbox = []
        result = enviar_email_task(
            subject="Asunto de Prueba",
            body="Texto plano de contenido",
            destinatario="destino_directo@test.com",
            html_message="<h1>HTML Contenido</h1>"
        )
        self.assertEqual(result["status"], "sent")
        self.assertEqual(len(mail.outbox), 1)
        
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["destino_directo@test.com"])
        self.assertEqual(msg.subject, "Asunto de Prueba")
        self.assertEqual(msg.body, "Texto plano de contenido")
        self.assertEqual(len(msg.alternatives), 1)
        self.assertEqual(msg.alternatives[0][1], "text/html")

    def test_08_comando_test_email(self):
        """8. Comando de gestión python manage.py test_email correo@dominio.com"""
        out = StringIO()
        call_command("test_email", "admin_prueba@test.com", stdout=out)
        output_str = out.getvalue()
        
        self.assertIn("SMTP CONFIGURADO", output_str)
        self.assertIn("CONEXIÓN EXITOSA", output_str)
        self.assertIn("CORREO ENVIADO", output_str)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["admin_prueba@test.com"])
