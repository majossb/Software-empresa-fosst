from datetime import datetime
from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from apps.accounts.models import Usuario, UserRole
from apps.empresas.models import Empresa, TransicionCapitulo
from apps.auditoria.models import AuditLog

from apps.empresas.views import clasificar_capitulo
from apps.estandares.models import Estandar, Evaluacion, Respuesta
from apps.evidencias.models import Evidencia, Archivo



class TransicionCapituloRFUSR03TestCase(TestCase):
    """
    Suite de 19 pruebas automatizadas para RF-USR-03 — Transición de Capítulo sin Reinicio.
    Verifica comportamiento de backend, transacciones atómicas, no-persistencia pre-confirmación,
    conservación de Evaluacion.id = X, cero DELETE en respuestas/evidencias y aislamiento multi-tenant.
    """

    def setUp(self):
        self.client = APIClient()

        # Empresa A (Inicialmente Capítulo I: 5 trabajadores, riesgo 1)
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa A Test SST",
            nit="900111222-1",
            num_trabajadores=5,
            nivel_riesgo=1,
            capitulo_vigente="I",
        )
        self.user_a = Usuario.objects.create(
            username="user_a_test",
            email="resp_a@test.com",
            first_name="Responsable",
            last_name="A",
            documento="10001",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a,
            is_active=True,
        )
        self.user_a.set_password("Password123!")
        self.user_a.save()

        # Empresa B (Para prueba multi-tenant)
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa B Test SST",
            nit="900333444-2",
            num_trabajadores=20,
            nivel_riesgo=2,
            capitulo_vigente="II",
        )
        self.user_b = Usuario.objects.create(
            username="user_b_test",
            email="resp_b@test.com",
            first_name="Responsable",
            last_name="B",
            documento="10002",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_b,
            is_active=True,
        )
        self.user_b.set_password("Password123!")
        self.user_b.save()


        # Crear Estándares de prueba para Capítulo I y III
        self.est_cap1_1 = Estandar.objects.create(
            codigo="I.1.1",
            nombre="Asignación de responsable SST",
            capitulo="I",
            ciclo_phva="Planear",
            puntaje_maximo=Decimal("5.0"),
            obligatorio=True,
        )
        self.est_cap1_2 = Estandar.objects.create(
            codigo="I.1.2",
            nombre="Afiliación al Sistema de Seguridad Social",
            capitulo="I",
            ciclo_phva="Planear",
            puntaje_maximo=Decimal("5.0"),
            obligatorio=True,
        )
        self.est_cap3_1 = Estandar.objects.create(
            codigo="III.1.1",
            nombre="Política de SST firmada",
            capitulo="III",
            ciclo_phva="Planear",
            puntaje_maximo=Decimal("2.5"),
            obligatorio=True,
        )
        self.est_cap3_2 = Estandar.objects.create(
            codigo="III.1.2",
            nombre="Objetivos de SST",
            capitulo="III",
            ciclo_phva="Planear",
            puntaje_maximo=Decimal("2.5"),
            obligatorio=True,
        )

        # Crear Evaluación activa año actual para Empresa A en Capítulo I
        self.anio_actual = datetime.now().year
        self.evaluacion_a = Evaluacion.objects.create(
            empresa=self.empresa_a,
            anio=self.anio_actual,
            capitulo="I",
            puntaje_total=Decimal("10.0"),
        )

        # Respuestas iniciales bajo Capítulo I
        self.resp_a_1 = Respuesta.objects.create(
            evaluacion=self.evaluacion_a,
            estandar=self.est_cap1_1,
            estado="cumple",
            puntaje=Decimal("5.0"),
            observacion="Cumple con soporte",
        )
        self.resp_a_2 = Respuesta.objects.create(
            evaluacion=self.evaluacion_a,
            estandar=self.est_cap1_2,
            estado="cumple",
            puntaje=Decimal("5.0"),
            observacion="Afiliación al día",
        )

        # Evidencia asociada a la respuesta 1
        self.archivo_1 = Archivo.objects.create(
            nombre="soporte_afiliacion.pdf",
            url="http://localhost:8000/media/soporte_afiliacion.pdf",
            tipo_mime="application/pdf",
            tamanio_kb=100,
            subido_por="Responsable A",
        )
        self.evidencia_1 = Evidencia.objects.create(
            respuesta=self.resp_a_1,
            archivo=self.archivo_1,
            descripcion="Soporte de afiliación",
        )


    # ── Test 01: Detección y No-Persistencia Pre-Confirmación ─────────────
    def test_01_deteccion_transicion_retorna_codigo_requires_confirmation_y_no_persiste(self):
        self.client.force_authenticate(user=self.user_a)
        # Intentar modificar contexto para que pase de 5 a 60 trabajadores (Cap I -> Cap III)
        response = self.client.put(
            "/api/modulo0/contexto",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data.get("success"))
        self.assertEqual(response.data.get("code"), "CHAPTER_CHANGE_REQUIRES_CONFIRMATION")
        self.assertEqual(response.data["data"]["capitulo_anterior"], "I")
        self.assertEqual(response.data["data"]["capitulo_nuevo"], "III")

        # VERIFICACIÓN CRÍTICA EN BD: La empresa NO debió ser modificada
        empresa_db = Empresa.objects.get(id=self.empresa_a.id)
        self.assertEqual(empresa_db.num_trabajadores, 5)
        self.assertEqual(empresa_db.capitulo_vigente, "I")

    # ── Test 02: Confirmación Atómica de Transición ──────────────────────
    def test_02_confirmacion_transicion_actualiza_empresa_y_evaluacion_atomicamente(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/modulo0/transicion-capitulo",
            {
                "num_trabajadores": 60,
                "nivel_riesgo": 1,
                "motivo": "Crecimiento de la empresa",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertIn("Capítulo I -> Capítulo III", response.data.get("message"))

        # Verificar actualización en BD de la empresa
        empresa_db = Empresa.objects.get(id=self.empresa_a.id)
        self.assertEqual(empresa_db.num_trabajadores, 60)
        self.assertEqual(empresa_db.capitulo_vigente, "III")

        # Verificar actualización del capítulo en la evaluación
        evaluacion_db = Evaluacion.objects.get(id=self.evaluacion_a.id)
        self.assertEqual(evaluacion_db.capitulo, "III")

    # ── Test 03: Evaluacion.id = X se conserva exactamente igual ─────────
    def test_03_evaluacion_id_se_conserva_exactamente_igual_antes_y_despues(self):
        id_original = self.evaluacion_a.id
        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )
        evaluacion_post = Evaluacion.objects.get(empresa=self.empresa_a, anio=self.anio_actual)
        self.assertEqual(evaluacion_post.id, id_original)

    # ── Test 04: Cero DELETE en respuestas ────────────────────────────────
    def test_04_respuestas_historicas_no_se_eliminan_count_pre_y_post_igual(self):
        count_pre = Respuesta.objects.filter(evaluacion=self.evaluacion_a).count()
        self.assertEqual(count_pre, 2)

        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        count_post = Respuesta.objects.filter(evaluacion=self.evaluacion_a).count()
        self.assertEqual(count_post, 2)

    # ── Test 05: Cero DELETE en evidencias ────────────────────────────────
    def test_05_evidencias_no_se_eliminan_post_transicion(self):
        count_pre = Evidencia.objects.filter(respuesta__evaluacion=self.evaluacion_a).count()
        self.assertEqual(count_pre, 1)

        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        count_post = Evidencia.objects.filter(respuesta__evaluacion=self.evaluacion_a).count()
        self.assertEqual(count_post, 1)

    # ── Test 06: Transición al mismo capítulo es rechazada ────────────────
    def test_06_transicion_mismo_capitulo_retorna_error(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 5, "nivel_riesgo": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data.get("code"), "SAME_CHAPTER_TRANSITION_INVALID")

    # ── Test 07: Recálculo de puntaje total filtra por capítulo vigente ──
    def test_07_recalculo_puntaje_total_evaluacion_filtra_solo_capitulo_vigente(self):
        self.client.force_authenticate(user=self.user_a)
        # Realizar transición de Cap I a Cap III
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        # Responder a un estándar de Capítulo III
        response = self.client.put(
            f"/api/estandares/respuesta/{self.est_cap3_1.id}",
            {"estado": "cumple", "observacion": "Cumple política Cap III"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # El puntaje total de la evaluación debe incluir SOLO el estándar de Cap III (2.5), NO los de Cap I (10.0)
        evaluacion_db = Evaluacion.objects.get(id=self.evaluacion_a.id)
        self.assertEqual(evaluacion_db.puntaje_total, Decimal("2.5"))

    # ── Test 08: Respuestas Históricas Endpoint ───────────────────────────
    def test_08_endpoint_respuestas_historicas_devuelve_etiquetas_capitulo_correctas(self):
        self.client.force_authenticate(user=self.user_a)
        # Transición a Cap III
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        # Consultar respuestas históricas
        response = self.client.get("/api/evaluaciones/actual/respuestas-historicas")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        respuestas = response.data.get("respuestas")
        self.assertEqual(len(respuestas), 2)

        # Cada respuesta debe tener su etiqueta de capítulo
        for r in respuestas:
            self.assertEqual(r["capitulo_estandar"], "I")
            self.assertFalse(r["es_capitulo_vigente"])

    # ── Test 09: Historial Inmutable de Transiciones ──────────────────────
    def test_09_endpoint_historial_transiciones_registra_evento_inmutable(self):
        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {
                "num_trabajadores": 60,
                "nivel_riesgo": 1,
                "motivo": "Motivo justificado de cambio",
            },
            format="json",
        )

        response = self.client.get("/api/modulo0/historial-transiciones")
        self.assertEqual(response.status_code, 200)
        data = response.data
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["capitulo_anterior"], "I")
        self.assertEqual(data[0]["capitulo_nuevo"], "III")
        self.assertEqual(data[0]["motivo"], "Motivo justificado de cambio")

    # ── Test 10: AuditLog Registrado ──────────────────────────────────────
    def test_10_audit_log_registra_accion_transicion_capitulo(self):
        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        log = AuditLog.objects.filter(empresa=self.empresa_a, accion="TRANSICION_CAPITULO").first()
        self.assertIsNotNone(log)
        self.assertEqual(log.valores_anteriores["capitulo_vigente"], "I")
        self.assertEqual(log.valores_nuevos["capitulo_vigente"], "III")

    # ── Test 11: Aislamiento Multi-Tenant en Historial ────────────────────
    def test_11_multitenant_aislamiento_empresa_no_puede_ver_transiciones_de_otra(self):
        # Transición de Empresa A
        self.client.force_authenticate(user=self.user_a)
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        # Autenticar como Empresa B y consultar historial
        self.client.force_authenticate(user=self.user_b)
        response = self.client.get("/api/modulo0/historial-transiciones")
        self.assertEqual(response.status_code, 200)
        # Empresa B no debe ver las transiciones de Empresa A
        self.assertEqual(len(response.data), 0)

    # ── Test 12–15: Reglas de Clasificación Normativa ─────────────────────
    def test_12_clasificacion_capitulo_I_menos_10_trabajadores_riesgo_1_a_3(self):
        self.assertEqual(clasificar_capitulo(5, 1), "I")
        self.assertEqual(clasificar_capitulo(10, 3), "I")

    def test_13_clasificacion_capitulo_II_11_a_50_trabajadores_riesgo_1_a_3(self):
        self.assertEqual(clasificar_capitulo(11, 1), "II")
        self.assertEqual(clasificar_capitulo(50, 3), "II")

    def test_14_clasificacion_capitulo_III_mas_50_trabajadores(self):
        self.assertEqual(clasificar_capitulo(51, 1), "III")
        self.assertEqual(clasificar_capitulo(100, 2), "III")

    def test_15_clasificacion_capitulo_III_riesgo_4_o_5_cualquier_numero(self):
        self.assertEqual(clasificar_capitulo(3, 4), "III")
        self.assertEqual(clasificar_capitulo(8, 5), "III")

    # ── Test 16: Transición Inversa Preserva Respuestas ───────────────────
    def test_16_transicion_inversa_capitulo_III_a_I_preserva_respuestas(self):
        # Configurar Empresa B en Cap III (70 trab, riesgo 1)
        self.empresa_b.num_trabajadores = 70
        self.empresa_b.capitulo_vigente = "III"
        self.empresa_b.save()

        eval_b = Evaluacion.objects.create(empresa=self.empresa_b, anio=self.anio_actual, capitulo="III")
        Respuesta.objects.create(evaluacion=eval_b, estandar=self.est_cap3_1, estado="cumple", puntaje=Decimal("2.5"))

        self.client.force_authenticate(user=self.user_b)
        # Transición inversa: reducir a 5 trabajadores (Cap III -> Cap I)
        response = self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 5, "nivel_riesgo": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # Confirmar que la respuesta de Cap III sigue viva en BD
        self.assertTrue(Respuesta.objects.filter(evaluacion=eval_b, estandar=self.est_cap3_1).exists())

    # ── Test 17: EstandaresConRespuestasView Estado Inicial ───────────────
    def test_17_estandares_con_respuestas_view_muestra_sin_respuesta_para_nuevos_estandares(self):
        self.client.force_authenticate(user=self.user_a)
        # Transición a Cap III
        self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )

        response = self.client.get("/api/estandares/respuestas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["capitulo"], "III")
        estandares = response.data["estandares"]
        self.assertTrue(all(e["estado"] == "sin_respuesta" for e in estandares))

    # ── Test 18: Modificación de Contexto Sin Cambio de Capítulo ──────────
    def test_18_actualizar_contexto_sin_cambio_de_capitulo_persiste_directamente(self):
        self.client.force_authenticate(user=self.user_a)
        # Pasar de 5 a 8 trabajadores (sigue en Capítulo I)
        response = self.client.put(
            "/api/modulo0/contexto",
            {"num_trabajadores": 8, "ciudad": "Cali"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        empresa_db = Empresa.objects.get(id=self.empresa_a.id)
        self.assertEqual(empresa_db.num_trabajadores, 8)
        self.assertEqual(empresa_db.ciudad, "Cali")
        self.assertEqual(empresa_db.capitulo_vigente, "I")

    # ── Test 19: Seguridad — Sin Autenticación Retorna 401 ────────────────
    def test_19_transicion_sin_autenticacion_retorna_401(self):
        response = self.client.post(
            "/api/modulo0/transicion-capitulo",
            {"num_trabajadores": 60, "nivel_riesgo": 1},
            format="json",
        )
        self.assertIn(response.status_code, [401, 403])
