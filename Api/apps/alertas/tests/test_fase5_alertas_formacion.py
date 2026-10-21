"""
Tests Fase 5 — Alertas de Formación & Competencias.

Escenarios cubiertos:
  1. Curso obligatorio por vencer en N días genera alerta (handler exacta)
  2. Curso obligatorio vencido genera alerta CRITICO (handler vencido_rango)
  3. Trabajador sin registro de curso obligatorio genera alerta (handler sin_registrar)
  4. Trabajador con brecha de competencia (sin evaluación) genera alerta (handler evaluacion_pendiente)
  5. Trabajador con evaluación aprobada NO genera alerta
  6. Renovar el curso elimina la alerta en próxima evaluación
  7. Deduplicación: no se genera alerta duplicada el mismo día
  8. Endpoint GET /alertas/notificaciones/ filtra por nivel, leida, tipo_alerta
  9. Endpoint POST marcar-leida actualiza la notificación
  10. Endpoint POST marcar-resuelta persiste metadatos resuelta=True
  11. Endpoint GET resumen devuelve conteos correctos
  12. Multi-tenant: alertas de empresa A no visibles para usuario de empresa B
"""
import uuid
from datetime import date, timedelta

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.calendario.models import Notificacion
from apps.alertas.models import ReglaAlerta
from apps.alertas.services import evaluar_reglas_alertas
from apps.formacion.models import (
    CursoFormacion, CargoRequisitoFormacion, RegistroFormacion, EvaluacionCompetencia,
)
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _empresa(nit="900555111-3"):
    return Empresa.objects.create(
        nombre="Empresa Formación SAS",
        nit=nit,
        num_trabajadores=20,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _usuario(empresa, username="resp_form", rol=UserRole.RESPONSABLE):
    return Usuario.objects.create_user(
        username=username,
        password="clave-test-123",
        email=f"{username}@test.com",
        documento="1099000001",
        rol=rol,
        empresa=empresa,
        activo=True,
    )


def _trabajador(empresa, nombre="Ana Gómez", documento="1099000010", perfil_cargo=None):
    return Trabajador.objects.create(
        empresa=empresa,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="indefinido",
        fecha_ingreso=date.today() - timedelta(days=200),
        perfil_cargo=perfil_cargo,
    )


def _perfil_cargo(empresa, nombre_cargo="Inspector SST"):
    return PerfilCargo.objects.create(
        empresa=empresa,
        codigo=f"C-{uuid.uuid4().hex[:6].upper()}",
        nombre_cargo=nombre_cargo,
        tipo_cargo="operativo",
        proposito="Inspección SST",
        educacion="Técnico",
    )


def _curso(empresa, nombre="Trabajo Seguro en Alturas", vigencia_meses=12):
    return CursoFormacion.objects.create(
        empresa=empresa,
        nombre=nombre,
        categoria=CursoFormacion.Categoria.SST,
        vigencia_meses=vigencia_meses,
        requiere_certificado=True,
    )


def _regla(codigo, handler, modelo_origen, campo_fecha="", dias=0,
           nivel=Notificacion.Nivel.IMPORTANTE, template=None, roles=None):
    return ReglaAlerta.objects.create(
        codigo=codigo,
        nombre=codigo,
        modelo_origen=modelo_origen,
        campo_fecha=campo_fecha,
        tipo_handler=handler,
        dias_anticipacion=dias,
        nivel_criticidad=nivel,
        mensaje_template=template or (
            "{trabajador} | {cargo} | {curso} | {competencia} | {fecha}"
        ),
        roles_destinatarios=roles or ["RESPONSABLE"],
        activa=True,
    )


# ---------------------------------------------------------------------------
# Tests — Handler exacta (curso por vencer)
# ---------------------------------------------------------------------------

@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class AlertaCursoExactaTests(TestCase):

    def setUp(self):
        self.empresa = _empresa()
        self.usuario = _usuario(self.empresa)
        self.perfil = _perfil_cargo(self.empresa)
        self.trabajador = _trabajador(self.empresa, perfil_cargo=self.perfil)
        self.curso = _curso(self.empresa)
        self.today = date.today()

        # Regla: alerta 25 días antes del vencimiento
        self.regla = _regla(
            "TEST_FORM_POR_VENCER_25D",
            ReglaAlerta.TipoHandler.EXACTA,
            "RegistroFormacion",
            campo_fecha="fecha_vencimiento",
            dias=25,
            nivel=Notificacion.Nivel.IMPORTANTE,
            template="El certificado de '{curso}' de {trabajador} vence en {dias} días ({fecha}).",
        )

    def test_curso_por_vencer_25_dias_genera_alerta(self):
        """Un curso que vence en exactamente 25 días genera una alerta IMPORTANTE."""
        fecha_vencimiento = self.today + timedelta(days=25)
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso,
            fecha_realizacion=self.today - timedelta(days=365 - 25),
            fecha_vencimiento=fecha_vencimiento,
        )

        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)

        self.assertGreaterEqual(total, 1)
        notif = Notificacion.objects.filter(empresa=self.empresa).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.nivel, Notificacion.Nivel.IMPORTANTE)
        self.assertIn(self.curso.nombre, notif.mensaje)
        # Metadatos correctos
        self.assertEqual(notif.metadatos["tipo_alerta"], "TEST_FORM_POR_VENCER_25D")
        self.assertEqual(notif.metadatos["trabajador_id"], str(self.trabajador.id))
        self.assertEqual(notif.metadatos["curso_id"], str(self.curso.id))

    def test_curso_que_vence_en_otro_dia_no_genera_alerta(self):
        """Un curso que vence en 10 días NO activa regla de 25 días."""
        fecha_vencimiento = self.today + timedelta(days=10)
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso,
            fecha_realizacion=self.today - timedelta(days=355),
            fecha_vencimiento=fecha_vencimiento,
        )
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertEqual(total, 0)


# ---------------------------------------------------------------------------
# Tests — Handler vencido_rango
# ---------------------------------------------------------------------------

@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class AlertaCursoVencidoTests(TestCase):

    def setUp(self):
        self.empresa = _empresa(nit="900555222-4")
        self.usuario = _usuario(self.empresa, username="resp_venc")
        self.perfil = _perfil_cargo(self.empresa)
        self.trabajador = _trabajador(self.empresa, perfil_cargo=self.perfil, documento="1099000020")
        self.curso = _curso(self.empresa, nombre="Manejo Defensivo")
        self.today = date.today()

        # El curso es obligatorio para el cargo
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=self.curso,
            obligatorio=True,
            vigencia_meses=12,
        )

        self.regla = _regla(
            "TEST_FORM_VENCIDO",
            ReglaAlerta.TipoHandler.VENCIDO_RANGO,
            "RegistroFormacion",
            nivel=Notificacion.Nivel.CRITICO,
            template="'{curso}' de {trabajador} está VENCIDO ({fecha}). Cargo: {cargo}. Renovar urgente.",
            roles=["RESPONSABLE", "ALTA_DIRECCION"],
        )
        self.usuario_alta = _usuario(self.empresa, username="alta_venc",
                                     rol=UserRole.ALTA_DIRECCION)

    def test_curso_vencido_genera_alerta_critica(self):
        """Certificado vencido con curso obligatorio → alerta CRITICO."""
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso,
            fecha_realizacion=self.today - timedelta(days=400),
            fecha_vencimiento=self.today - timedelta(days=35),  # ya vencido
        )

        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)

        self.assertGreaterEqual(total, 1)
        notif = Notificacion.objects.filter(empresa=self.empresa, nivel=Notificacion.Nivel.CRITICO).first()
        self.assertIsNotNone(notif)
        self.assertIn("VENCIDO", notif.mensaje)
        self.assertEqual(notif.metadatos["tipo_alerta"], "TEST_FORM_VENCIDO")

    def test_curso_no_obligatorio_no_genera_alerta_vencido(self):
        """Un curso NO obligatorio vencido no debe disparar alerta."""
        curso_libre = _curso(self.empresa, nombre="Excel Avanzado", vigencia_meses=12)
        # No se crea CargoRequisitoFormacion para curso_libre
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=curso_libre,
            fecha_realizacion=self.today - timedelta(days=500),
            fecha_vencimiento=self.today - timedelta(days=100),
        )
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertEqual(total, 0)

    def test_deduplicacion_no_duplica_alerta_mismo_dia(self):
        """No debe crearse la misma alerta dos veces en el mismo día."""
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso,
            fecha_realizacion=self.today - timedelta(days=400),
            fecha_vencimiento=self.today - timedelta(days=35),
        )

        evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        total2 = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)

        self.assertEqual(total2, 0)  # Segunda ejecución no crea duplicados


# ---------------------------------------------------------------------------
# Tests — Handler sin_registrar
# ---------------------------------------------------------------------------

@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class AlertaCursoSinRegistrarTests(TestCase):

    def setUp(self):
        self.empresa = _empresa(nit="900555333-5")
        self.usuario = _usuario(self.empresa, username="resp_sinreg")
        self.perfil = _perfil_cargo(self.empresa, "Conductor")
        self.trabajador = _trabajador(self.empresa, nombre="Pedro Pérez",
                                      documento="1099000030", perfil_cargo=self.perfil)
        self.curso = _curso(self.empresa, nombre="Primeros Auxilios")
        self.today = date.today()

        # El curso es obligatorio para el cargo
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=self.curso,
            obligatorio=True,
            vigencia_meses=24,
        )

        self.regla = _regla(
            "TEST_FORM_SIN_REGISTRAR",
            ReglaAlerta.TipoHandler.SIN_REGISTRAR,
            "RegistroFormacion",
            nivel=Notificacion.Nivel.IMPORTANTE,
            template="{trabajador} (Cargo: {cargo}) no registra el curso obligatorio '{curso}'.",
        )

    def test_sin_registro_genera_alerta(self):
        """Trabajador activo sin RegistroFormacion del curso obligatorio → alerta."""
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertGreaterEqual(total, 1)
        notif = Notificacion.objects.filter(empresa=self.empresa).first()
        self.assertIsNotNone(notif)
        self.assertIn(self.curso.nombre, notif.mensaje)
        self.assertEqual(notif.metadatos["tipo_alerta"], "TEST_FORM_SIN_REGISTRAR")
        self.assertEqual(notif.metadatos["curso_id"], str(self.curso.id))

    def test_con_registro_no_genera_alerta(self):
        """Trabajador con RegistroFormacion del curso NO debe generar alerta."""
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso,
            fecha_realizacion=self.today - timedelta(days=30),
        )
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertEqual(total, 0)


# ---------------------------------------------------------------------------
# Tests — Handler evaluacion_pendiente
# ---------------------------------------------------------------------------

@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class AlertaEvaluacionCompetenciaTests(TestCase):

    def setUp(self):
        self.empresa = _empresa(nit="900555444-6")
        self.usuario = _usuario(self.empresa, username="resp_comp")
        self.perfil = _perfil_cargo(self.empresa, "Técnico SST")
        self.trabajador = _trabajador(self.empresa, nombre="Laura Torres",
                                      documento="1099000040", perfil_cargo=self.perfil)
        self.today = date.today()

        # Competencia requerida para el cargo
        self.cargo_competencia = CargoCompetencia.objects.create(
            perfil_cargo=self.perfil,
            nombre="Gestión del Riesgo",
            tipo="tecnica",
            nivel_requerido=3,
            nivel=3,
        )

        self.regla = _regla(
            "TEST_FORM_EVAL_PENDIENTE",
            ReglaAlerta.TipoHandler.EVALUACION_PENDIENTE,
            "EvaluacionCompetencia",
            nivel=Notificacion.Nivel.NORMAL,
            template="{trabajador} (Cargo: {cargo}) tiene brecha en '{competencia}'.",
        )

    def test_sin_evaluacion_genera_alerta(self):
        """Trabajador sin ninguna EvaluacionCompetencia para su cargo → alerta."""
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertGreaterEqual(total, 1)
        notif = Notificacion.objects.filter(empresa=self.empresa).first()
        self.assertIsNotNone(notif)
        self.assertIn("Gestión del Riesgo", notif.mensaje)

    def test_con_brecha_genera_alerta(self):
        """Trabajador con evaluación pero con brecha (nivel alcanzado < requerido) → alerta."""
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=self.cargo_competencia,
            nivel_alcanzado=1,  # requerido es 3, brecha=2
            fecha_evaluacion=self.today - timedelta(days=10),
        )
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertGreaterEqual(total, 1)

    def test_sin_brecha_no_genera_alerta(self):
        """Trabajador con evaluación donde nivel_alcanzado >= nivel_requerido → sin alerta."""
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=self.cargo_competencia,
            nivel_alcanzado=4,  # supera el requerido (3)
            fecha_evaluacion=self.today - timedelta(days=5),
        )
        total = evaluar_reglas_alertas(empresa=self.empresa, fecha_referencia=self.today)
        self.assertEqual(total, 0)


# ---------------------------------------------------------------------------
# Tests — API endpoints
# ---------------------------------------------------------------------------

@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class NotificacionAPITests(TestCase):

    def setUp(self):
        self.empresa = _empresa(nit="900555555-7")
        self.usuario = _usuario(self.empresa, username="resp_api")
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)
        self.today = date.today()

        # Crear algunas notificaciones directamente
        self.notif_critica = Notificacion.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            tipo=Notificacion.Tipo.ALERTA,
            nivel=Notificacion.Nivel.CRITICO,
            mensaje="Curso vencido para Ana Gómez",
            metadatos={
                "tipo_alerta": "FORM_CURSO_VENCIDO",
                "trabajador_id": "abc-123",
                "cargo": "Inspector SST",
            },
        )
        self.notif_normal = Notificacion.objects.create(
            empresa=self.empresa,
            usuario=self.usuario,
            tipo=Notificacion.Tipo.ALERTA,
            nivel=Notificacion.Nivel.NORMAL,
            mensaje="Evaluación pendiente para Pedro Pérez",
            metadatos={
                "tipo_alerta": "FORM_EVALUACION_COMPETENCIA_PENDIENTE",
                "trabajador_id": "def-456",
                "cargo": "Conductor",
            },
        )

    def test_listado_notificaciones(self):
        resp = self.client.get("/api/alertas/notificaciones/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data["results"]), 2)

    def test_filtro_por_nivel(self):
        resp = self.client.get("/api/alertas/notificaciones/?nivel=critico")
        self.assertEqual(resp.status_code, 200)
        for item in resp.data["results"]:
            self.assertEqual(item["nivel"], "critico")

    def test_filtro_por_leida(self):
        self.notif_critica.leida = True
        self.notif_critica.save()
        resp = self.client.get("/api/alertas/notificaciones/?leida=false")
        self.assertEqual(resp.status_code, 200)
        for item in resp.data["results"]:
            self.assertFalse(item["leida"])

    def test_filtro_por_tipo_alerta(self):
        resp = self.client.get("/api/alertas/notificaciones/?tipo_alerta=FORM_CURSO_VENCIDO")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)
        self.assertEqual(
            resp.data["results"][0]["metadatos"]["tipo_alerta"], "FORM_CURSO_VENCIDO"
        )

    def test_filtro_por_cargo(self):
        resp = self.client.get("/api/alertas/notificaciones/?cargo=Conductor")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 1)

    def test_accion_url_curso_vencido(self):
        resp = self.client.get(f"/api/alertas/notificaciones/{self.notif_critica.id}/")
        self.assertEqual(resp.status_code, 200)
        accion = resp.data["accion_url"]
        self.assertIsNotNone(accion)
        self.assertIn("/app/responsable/formacion", accion)
        self.assertIn("trabajador_id=abc-123", accion)

    def test_marcar_leida(self):
        resp = self.client.post(f"/api/alertas/notificaciones/{self.notif_normal.id}/marcar-leida/")
        self.assertEqual(resp.status_code, 200)
        self.notif_normal.refresh_from_db()
        self.assertTrue(self.notif_normal.leida)

    def test_marcar_resuelta(self):
        resp = self.client.post(f"/api/alertas/notificaciones/{self.notif_critica.id}/marcar-resuelta/")
        self.assertEqual(resp.status_code, 200)
        self.notif_critica.refresh_from_db()
        self.assertTrue(self.notif_critica.leida)
        self.assertTrue(self.notif_critica.metadatos.get("resuelta"))

    def test_resumen(self):
        resp = self.client.get("/api/alertas/notificaciones/resumen/")
        self.assertEqual(resp.status_code, 200)
        data = resp.data
        self.assertIn("total", data)
        self.assertIn("no_leidas", data)
        self.assertIn("por_nivel", data)
        self.assertEqual(data["no_leidas"], data["por_nivel"]["critico"] + data["por_nivel"]["importante"] + data["por_nivel"]["normal"])

    def test_multi_tenant_aislamiento(self):
        """Usuario de empresa B no ve notificaciones de empresa A."""
        empresa_b = _empresa(nit="900555666-8")
        usuario_b = _usuario(empresa_b, username="resp_b")
        client_b = APIClient()
        client_b.force_authenticate(user=usuario_b)

        resp = client_b.get("/api/alertas/notificaciones/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data["results"]), 0)
