"""
Tests del Motor Genérico de Alertas (§5.2).

Cubren:
  - Generación de notificaciones por vencimiento de contrato (60 días)
  - Generación de notificaciones por vencimiento de examen médico y licencia
  - Deduplicación diaria (no reenviar misma alerta en el mismo día)
  - Reglas inactivas omitidas
  - Aislamiento multi-tenant
"""
from datetime import date, timedelta
from django.test import TestCase, override_settings

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.calendario.models import Notificacion
from apps.gestion_humana.models import ExamenMedicoOcupacional, LicenciaConduccion
from apps.alertas.models import ReglaAlerta
from apps.alertas.services import evaluar_reglas_alertas


def _crear_empresa(nit="900111222-3"):
    return Empresa.objects.create(
        nombre="Empresa Alertas SAS",
        nit=nit,
        num_trabajadores=15,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable_alertas", rol=UserRole.RESPONSABLE):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="1000000003",
        rol=rol,
        empresa=empresa,
    )


def _crear_trabajador(empresa, nombre="Carlos Ruiz", documento="1000000020"):
    return Trabajador.objects.create(
        empresa=empresa,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="fijo",
        fecha_ingreso=date.today() - timedelta(days=300),
    )


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class MotorAlertasTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.trabajador = _crear_trabajador(self.empresa)
        self.today = date.today()

        # Crear regla de prueba para contrato
        self.regla_contrato = ReglaAlerta.objects.create(
            codigo="TEST_VENC_CONTRATO_60D",
            nombre="Vencimiento de Contrato (60 días)",
            modelo_origen="Trabajador",
            campo_fecha="fecha_fin_contrato",
            dias_anticipacion=60,
            nivel_criticidad=Notificacion.Nivel.IMPORTANTE,
            mensaje_template="El contrato de {trabajador} vence en {dias} días ({fecha}).",
            roles_destinatarios=["RESPONSABLE"],
            activa=True,
        )

    def test_evaluacion_regla_contrato_genera_notificacion(self):
        """Un trabajador con contrato a vencer en 60 días genera Notificacion para el RESPONSABLE."""
        self.trabajador.fecha_fin_contrato = self.today + timedelta(days=60)
        self.trabajador.save()

        notificaciones_antes = Notificacion.objects.count()
        total_generadas = evaluar_reglas_alertas(fecha_referencia=self.today)

        self.assertEqual(total_generadas, 1)
        self.assertEqual(Notificacion.objects.count(), notificaciones_antes + 1)

        notif = Notificacion.objects.latest("created_at")
        self.assertEqual(notif.empresa, self.empresa)
        self.assertEqual(notif.usuario, self.usuario)
        self.assertIn("Carlos Ruiz", notif.mensaje)
        self.assertIn("60 días", notif.mensaje)

    def test_deduplicacion_misma_alerta_mismo_dia(self):
        """Ejecutar la evaluación dos veces en el mismo día no duplica la notificación."""
        self.trabajador.fecha_fin_contrato = self.today + timedelta(days=60)
        self.trabajador.save()

        primera_ejecucion = evaluar_reglas_alertas(fecha_referencia=self.today)
        self.assertEqual(primera_ejecucion, 1)

        segunda_ejecucion = evaluar_reglas_alertas(fecha_referencia=self.today)
        self.assertEqual(segunda_ejecucion, 0)
        self.assertEqual(Notificacion.objects.count(), 1)

    def test_alerta_examen_medico(self):
        """Examen médico a vencer en 30 días genera notificación."""
        ReglaAlerta.objects.create(
            codigo="TEST_VENC_EXAMEN_30D",
            nombre="Vencimiento Examen Médico (30 días)",
            modelo_origen="ExamenMedicoOcupacional",
            campo_fecha="fecha_vencimiento",
            dias_anticipacion=30,
            nivel_criticidad=Notificacion.Nivel.IMPORTANTE,
            mensaje_template="Examen de {trabajador} vence en {dias} días.",
            roles_destinatarios=["RESPONSABLE"],
            activa=True,
        )

        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="periodico",
            fecha_examen=self.today - timedelta(days=335),
            fecha_vencimiento=self.today + timedelta(days=30),
        )

        total = evaluar_reglas_alertas(fecha_referencia=self.today)
        self.assertEqual(total, 1)
        notif = Notificacion.objects.latest("created_at")
        self.assertIn("Examen de Carlos Ruiz", notif.mensaje)

    def test_alerta_licencia_conduccion(self):
        """Licencia de conducción a vencer en 30 días genera notificación."""
        ReglaAlerta.objects.create(
            codigo="TEST_VENC_LICENCIA_30D",
            nombre="Vencimiento Licencia (30 días)",
            modelo_origen="LicenciaConduccion",
            campo_fecha="fecha_vencimiento",
            dias_anticipacion=30,
            nivel_criticidad=Notificacion.Nivel.IMPORTANTE,
            mensaje_template="Licencia ({tipo}) de {trabajador} vence en {dias} días.",
            roles_destinatarios=["RESPONSABLE"],
            activa=True,
        )

        LicenciaConduccion.objects.create(
            trabajador=self.trabajador,
            categoria="C1",
            fecha_vencimiento=self.today + timedelta(days=30),
        )

        total = evaluar_reglas_alertas(fecha_referencia=self.today)
        self.assertEqual(total, 1)
        notif = Notificacion.objects.latest("created_at")
        self.assertIn("Licencia (C1) de Carlos Ruiz", notif.mensaje)

    def test_regla_inactiva_no_genera_alerta(self):
        """Una regla con activa=False no genera notificaciones."""
        self.regla_contrato.activa = False
        self.regla_contrato.save()

        self.trabajador.fecha_fin_contrato = self.today + timedelta(days=60)
        self.trabajador.save()

        total = evaluar_reglas_alertas(fecha_referencia=self.today)
        self.assertEqual(total, 0)
        self.assertEqual(Notificacion.objects.count(), 0)

    def test_aislamiento_multitenant_alertas(self):
        """Las alertas se asignan únicamente a los usuarios de la empresa correspondiente."""
        otra_empresa = _crear_empresa(nit="900999888-4")
        otro_usuario = _crear_usuario(otra_empresa, username="responsable_otra")
        otro_trabajador = _crear_trabajador(otra_empresa, nombre="Ana Gómez", documento="2000000050")

        self.trabajador.fecha_fin_contrato = self.today + timedelta(days=60)
        self.trabajador.save()

        otro_trabajador.fecha_fin_contrato = self.today + timedelta(days=60)
        otro_trabajador.save()

        evaluar_reglas_alertas(fecha_referencia=self.today)

        notifs_empresa1 = Notificacion.objects.filter(empresa=self.empresa)
        notifs_empresa2 = Notificacion.objects.filter(empresa=otra_empresa)

        self.assertEqual(notifs_empresa1.count(), 1)
        self.assertEqual(notifs_empresa2.count(), 1)
        self.assertEqual(notifs_empresa1.first().usuario, self.usuario)
        self.assertEqual(notifs_empresa2.first().usuario, otro_usuario)
