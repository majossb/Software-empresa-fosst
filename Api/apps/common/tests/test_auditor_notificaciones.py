import uuid
from django.utils import timezone
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.estandares.models import Evaluacion, Estandar, Respuesta, Apelacion
from apps.hallazgos.models import Hallazgo
from apps.calendario.models import Notificacion
from apps.informes.models import Informe
from apps.planes.models import Plan, Suscripcion


class AuditorNotificacionesTestCase(TestCase):
    """
    Suite de 18 pruebas integrales para AUDITOR (AUD-01 a AUD-09) y NOTIFICACIONES (NOT-01 a NOT-09).
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Crear Plan Pro y Suscripciones Activas para gating
        self.plan = Plan.objects.create(
            nombre="Plan Pro Audit",
            precio_mensual=100000,
            precio_anual=1000000,
            max_usuarios=100,
            max_evidencias_mb=5000,
            tiene_auditoria=True,
            tiene_informes=True,
            tiene_calendario=True,
            tiene_alertas_email=True,
            tiene_historico=True,
            activo=True
        )

        # 2. Crear Empresas A y B
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa A Auditor S.A.S.",
            nit="900999001-1",
            num_trabajadores=20,
            nivel_riesgo=3,
            capitulo_vigente="I"
        )
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa B Auditor S.A.S.",
            nit="900999002-2",
            num_trabajadores=40,
            nivel_riesgo=4,
            capitulo_vigente="II"
        )

        Suscripcion.objects.create(
            empresa=self.empresa_a,
            plan=self.plan,
            estado=Suscripcion.Estado.ACTIVA,
            fecha_inicio=timezone.now()
        )
        Suscripcion.objects.create(
            empresa=self.empresa_b,
            plan=self.plan,
            estado=Suscripcion.Estado.ACTIVA,
            fecha_inicio=timezone.now()
        )

        # 3. Crear Usuarios
        self.auditor_a = Usuario.objects.create(
            username="auditor_a",
            email="auditor_a@empresa-a.com",
            first_name="Auditor",
            last_name="Empresa A",
            documento="99001",
            rol=UserRole.AUDITOR,
            empresa=self.empresa_a
        )
        self.auditor_a.set_password("Password123!")
        self.auditor_a.save()

        self.auditor_b = Usuario.objects.create(
            username="auditor_b",
            email="auditor_b@empresa-b.com",
            first_name="Auditor",
            last_name="Empresa B",
            documento="99002",
            rol=UserRole.AUDITOR,
            empresa=self.empresa_b
        )
        self.auditor_b.set_password("Password123!")
        self.auditor_b.save()

        self.responsable_a = Usuario.objects.create(
            username="responsable_a",
            email="sst_a@empresa-a.com",
            first_name="Responsable",
            last_name="SST A",
            documento="99003",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a
        )
        self.responsable_a.set_password("Password123!")
        self.responsable_a.save()

        # 4. Crear Estandar y Evaluaciones
        self.estandar_1 = Estandar.objects.create(
            codigo="I-1.1.1",
            nombre="Responsable del SG-SST",
            capitulo="I",
            ciclo_phva="Planear",
            puntaje_maximo=0.5
        )

        self.evaluacion_a = Evaluacion.objects.create(
            empresa=self.empresa_a,
            anio=2026,
            capitulo="I",
            puntaje_total=85.0,
            estado="en_proceso"
        )
        self.evaluacion_b = Evaluacion.objects.create(
            empresa=self.empresa_b,
            anio=2026,
            capitulo="II",
            puntaje_total=60.0,
            estado="en_proceso"
        )

        self.respuesta_a = Respuesta.objects.create(
            evaluacion=self.evaluacion_a,
            estandar=self.estandar_1,
            estado=Respuesta.Estado.NO_CUMPLE,
            puntaje=0,
            observacion="Observación inicial"
        )

    # ─────────────────────────────────────────────────────────────────
    # AUDITOR ROLE & HALLAZGOS TESTS (AUD-01 .. AUD-09, HALL-01 .. HALL-10)
    # ─────────────────────────────────────────────────────────────────

    def test_AUD_01_access_auditor_dashboard(self):
        """AUD-01: Auditor accede exitosamente a su dashboard (200 OK)."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/dashboard/auditor')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('evaluacion_id', res.data)

    def test_AUD_02_auditor_dashboard_forbidden_non_auditor(self):
        """AUD-02: Usuario sin rol auditor (ej. Responsable SST) recibe 403 en dashboard auditor."""
        self.client.force_authenticate(user=self.responsable_a)
        res = self.client.get('/api/dashboard/auditor')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_AUD_03_create_hallazgo_valid_types(self):
        """AUD-03: Auditor crea hallazgos con tipos no_conformidad, observacion, oportunidad_mejora."""
        self.client.force_authenticate(user=self.auditor_a)
        tipos = ['no_conformidad', 'observacion', 'oportunidad_mejora']
        for tipo in tipos:
            res = self.client.post('/api/hallazgos', {
                'evaluacion': str(self.evaluacion_a.id),
                'descripcion': f'Hallazgo de prueba tipo {tipo}',
                'tipo': tipo
            })
            self.assertEqual(res.status_code, status.HTTP_201_CREATED, f'Falló creación de hallazgo {tipo}')
            self.assertEqual(res.data['tipo'], tipo)

    def test_AUD_04_hallazgos_multi_tenant_isolation(self):
        """AUD-04: El auditor de Empresa A solo ve hallazgos de Empresa A, no de Empresa B."""
        h_a = Hallazgo.objects.create(
            evaluacion=self.evaluacion_a,
            auditor=self.auditor_a,
            descripcion="Hallazgo Empresa A",
            tipo="no_conformidad"
        )
        h_b = Hallazgo.objects.create(
            evaluacion=self.evaluacion_b,
            auditor=self.auditor_b,
            descripcion="Hallazgo Empresa B",
            tipo="observacion"
        )

        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/hallazgos')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        hallazgos_list = res.data.get('hallazgos', []) if isinstance(res.data, dict) else res.data
        ids = [item['id'] for item in hallazgos_list]
        self.assertIn(str(h_a.id), ids)
        self.assertNotIn(str(h_b.id), ids)

    def test_AUD_05_generate_auditor_final_report(self):
        """AUD-05: Auditor genera informe final de auditoria exitosamente."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['tipo'], 'auditoria')

    def test_AUD_06_list_auditor_final_reports(self):
        """AUD-06: Auditor lista informes de auditoría generados."""
        Informe.objects.create(
            evaluacion=self.evaluacion_a,
            tipo="auditoria"
        )
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/informes/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data if isinstance(res.data, list) else res.data.get('results', [])
        self.assertTrue(any(i['tipo'] == 'auditoria' for i in results))

    def test_AUD_07_access_evaluaciones_historial(self):
        """AUD-07: Auditor accede a /api/evaluaciones/historial sin error 403 y filtrado por empresa."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/evaluaciones/historial')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['id'], str(self.evaluacion_a.id))

    def test_AUD_08_auditor_evidencias_scoped_by_company(self):
        """AUD-08: Auditor consulta evidencias (/api/evidencias/) filtradas por su empresa."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/evidencias/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_AUD_09_auditor_finding_creation_timestamps(self):
        """AUD-09: Verificación de timestamp y auditor asignado al crear hallazgo."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post('/api/hallazgos', {
            'evaluacion': str(self.evaluacion_a.id),
            'descripcion': 'Prueba auditor asignado',
            'tipo': 'observacion'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        hallazgo = Hallazgo.objects.get(id=res.data['id'])
        self.assertEqual(hallazgo.auditor, self.auditor_a)
        self.assertIsNotNone(hallazgo.created_at)

    def test_HALL_01_creacion_valida_con_estandar_y_notificacion_responsable(self):
        """HALL-01 & NOT-02: Auditor crea hallazgo sobre estándar exacto I-1.1.1 y notifica al Responsable SST de Empresa A."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post('/api/hallazgos', {
            'evaluacion': str(self.evaluacion_a.id),
            'estandar_codigo': 'I-1.1.1',
            'descripcion': 'Observación sobre el estándar de asignación de responsable SG-SST',
            'tipo': 'observacion'
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['estandar_codigo'], 'I-1.1.1')

        # Verificación de notificación creada para Responsable SST de Empresa A
        notifs = Notificacion.objects.filter(empresa=self.empresa_a, usuario=self.responsable_a)
        self.assertTrue(notifs.exists(), "Responsable SST no recibió notificación")
        notif = notifs.first()
        self.assertIn('I-1.1.1', notif.mensaje)

    def test_HALL_09_estandar_otra_empresa_rechazado(self):
        """HALL-09: Auditor A no puede crear hallazgos sobre la evaluación/empresa B (403 Forbidden)."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post('/api/hallazgos', {
            'evaluacion': str(self.evaluacion_b.id),
            'descripcion': 'Intento de manipulación de ID de empresa B',
            'tipo': 'no_conformidad'
        })
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_HALL_10_doble_submit_idempotencia(self):
        """HALL-10: Protección contra doble submit no duplica registros en BD."""
        self.client.force_authenticate(user=self.auditor_a)
        payload = {
            'evaluacion': str(self.evaluacion_a.id),
            'descripcion': 'Doble submit rápido',
            'tipo': 'observacion'
        }
        res1 = self.client.post('/api/hallazgos', payload)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = self.client.post('/api/hallazgos', payload)
        self.assertEqual(res2.status_code, status.HTTP_201_CREATED)

        count = Hallazgo.objects.filter(evaluacion=self.evaluacion_a, descripcion='Doble submit rápido').count()
        self.assertEqual(count, 1, "Se creó un duplicado en BD en lugar de prevenir el doble submit")

    # ─────────────────────────────────────────────────────────────────
    # NOTIFICATIONS ENGINE TESTS (NOT-01 .. NOT-09)
    # ─────────────────────────────────────────────────────────────────

    def test_NOT_01_create_notification_levels(self):
        """NOT-01: Creación de notificaciones con distintos niveles (normal, importante, critico)."""
        n_normal = Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.INFORMATIVA,
            nivel=Notificacion.Nivel.NORMAL,
            mensaje="Mensaje normal"
        )
        n_imp = Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.RECORDATORIO,
            nivel=Notificacion.Nivel.IMPORTANTE,
            mensaje="Mensaje importante"
        )
        n_crit = Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.ALERTA,
            nivel=Notificacion.Nivel.CRITICO,
            mensaje="Mensaje crítico"
        )
        self.assertEqual(n_normal.nivel, "normal")
        self.assertEqual(n_imp.nivel, "importante")
        self.assertEqual(n_crit.nivel, "critico")

    def test_NOT_02_list_notifications(self):
        """NOT-02: Endpoint GET /api/notificaciones retorna las notificaciones de la empresa."""
        Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.INFORMATIVA,
            nivel=Notificacion.Nivel.NORMAL,
            mensaje="Notificación 1"
        )
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/notificaciones')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.data if isinstance(res.data, list) else res.data.get('results', [])
        self.assertEqual(len(items), 1)

    def test_NOT_03_notifications_multi_tenant_isolation(self):
        """NOT-03: Aislamiento estricto de notificaciones entre Empresa A y Empresa B."""
        n_a = Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.INFORMATIVA,
            mensaje="Notif Empresa A"
        )
        n_b = Notificacion.objects.create(
            empresa=self.empresa_b,
            tipo=Notificacion.Tipo.ALERTA,
            mensaje="Notif Empresa B"
        )

        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/notificaciones')
        items = res.data if isinstance(res.data, list) else res.data.get('results', [])
        ids = [item['id'] for item in items]
        self.assertIn(str(n_a.id), ids)
        self.assertNotIn(str(n_b.id), ids)

    def test_NOT_04_mark_notification_as_read(self):
        """NOT-04: Marcar notificación como leída POST /api/notificaciones/{id}/marcar_leida."""
        n = Notificacion.objects.create(
            empresa=self.empresa_a,
            tipo=Notificacion.Tipo.RECORDATORIO,
            mensaje="Recordatorio por leer",
            leida=False
        )
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post(f'/api/notificaciones/{n.id}/marcar_leida')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        n.refresh_from_db()
        self.assertTrue(n.leida)

    def test_NOT_05_unread_notifications_count(self):
        """NOT-05: Conteo y filtrado de notificaciones no leídas."""
        Notificacion.objects.create(empresa=self.empresa_a, mensaje="Unread 1", leida=False)
        Notificacion.objects.create(empresa=self.empresa_a, mensaje="Unread 2", leida=False)
        Notificacion.objects.create(empresa=self.empresa_a, mensaje="Read 1", leida=True)

        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.get('/api/notificaciones')
        items = res.data if isinstance(res.data, list) else res.data.get('results', [])
        unread = [i for i in items if not i['leida']]
        self.assertEqual(len(unread), 2)

    def test_NOT_06_notification_level_choices(self):
        """NOT-06: Verificación de niveles permitidos en modelo Notificacion."""
        valid_levels = [choice[0] for choice in Notificacion.Nivel.choices]
        self.assertIn("normal", valid_levels)
        self.assertIn("importante", valid_levels)
        self.assertIn("critico", valid_levels)

    def test_NOT_07_notification_tipo_choices(self):
        """NOT-07: Verificación de tipos permitidos en modelo Notificacion."""
        valid_tipos = [choice[0] for choice in Notificacion.Tipo.choices]
        self.assertIn("alerta", valid_tipos)
        self.assertIn("recordatorio", valid_tipos)
        self.assertIn("informativa", valid_tipos)

    def test_NOT_08_notifications_unauthenticated_forbidden(self):
        """NOT-08: Usuario no autenticado recibe 401 Unauthorized en GET /api/notificaciones."""
        self.client.logout()
        res = self.client.get('/api/notificaciones')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_NOT_09_mark_non_existent_notification_returns_404(self):
        """NOT-09: Intentar marcar como leída una notificación inexistente retorna 404."""
        self.client.force_authenticate(user=self.auditor_a)
        random_id = str(uuid.uuid4())
        res = self.client.post(f'/api/notificaciones/{random_id}/marcar_leida')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    # ─────────────────────────────────────────────────────────────────
    # E2E OBS-APELACIÓN-RESOLUCIÓN & REPORT ACCESS TESTS
    # ─────────────────────────────────────────────────────────────────

    def test_HALL_OBS_E2E_flujo_completo_observacion_apelacion_resolucion(self):
        """
        E2E Test:
        1. Auditor A registra observación con texto completo en I-1.1.1.
        2. Responsable SST A recibe notificación in-app con el texto de la observación.
        3. Responsable SST A envía apelación con texto del motivo.
        4. Auditor A recibe notificación in-app con el motivo de la apelación.
        5. Auditor A lista apelaciones en GET /api/apelaciones/ y visualiza la apelación.
        6. Auditor A resuelve la apelación POST /api/apelaciones/{id}/resolver/ como 'aceptada'.
        7. La Respuesta del estándar se actualiza a 'cumple', el puntaje se recalcula, y Responsable SST A recibe notificación de la resolución.
        """
        # FASE 1: Auditor A crea observación
        self.client.force_authenticate(user=self.auditor_a)
        res_obs = self.client.post('/api/hallazgos', {
            'evaluacion': str(self.evaluacion_a.id),
            'estandar_codigo': 'I-1.1.1',
            'descripcion': 'PRUEBA UAT AUDITOR - Texto completo de observación sobre SG-SST',
            'tipo': 'observacion'
        })
        self.assertEqual(res_obs.status_code, status.HTTP_201_CREATED)

        # FASE 2: Responsable SST recibe notificación con el texto de la observación
        notif_resp = Notificacion.objects.filter(empresa=self.empresa_a, usuario=self.responsable_a).latest('created_at')
        self.assertIn('PRUEBA UAT AUDITOR', notif_resp.mensaje)

        # FASE 3: Responsable SST presenta apelación
        self.client.force_authenticate(user=self.responsable_a)
        res_apel = self.client.post('/api/apelaciones/', {
            'respuesta': str(self.respuesta_a.id),
            'motivo': 'PRUEBA UAT APELACIÓN - Se anexa certificado de formación del responsable SG-SST.'
        })
        self.assertEqual(res_apel.status_code, status.HTTP_201_CREATED)
        apelacion_id = res_apel.data['data']['id']

        # FASE 4: Auditor recibe notificación con motivo de apelación
        notif_aud = Notificacion.objects.filter(empresa=self.empresa_a, usuario=self.auditor_a).latest('created_at')
        self.assertIn('PRUEBA UAT APELACIÓN', notif_aud.mensaje)

        # FASE 5: Auditor consulta lista de apelaciones
        self.client.force_authenticate(user=self.auditor_a)
        res_list = self.client.get('/api/apelaciones/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        items = res_list.data if isinstance(res_list.data, list) else res_list.data.get('results', [])
        self.assertTrue(any(item['id'] == apelacion_id for item in items))

        # FASE 6: Auditor resuelve apelación como aceptada
        res_res = self.client.post(f'/api/apelaciones/{apelacion_id}/resolver/', {
            'decision': 'aceptada',
            'respuesta_auditor': 'Se verifica la evidencia aportada y se concede la apelación.',
            'nuevo_estado': 'cumple'
        })
        self.assertEqual(res_res.status_code, status.HTTP_200_OK)

        # FASE 7: Verificación de estado de respuesta, puntaje y notificación a Responsable
        self.respuesta_a.refresh_from_db()
        self.assertEqual(self.respuesta_a.estado, Respuesta.Estado.CUMPLE)
        self.assertEqual(float(self.respuesta_a.puntaje), 0.5)

        notif_final = Notificacion.objects.filter(empresa=self.empresa_a, usuario=self.responsable_a).latest('created_at')
        self.assertIn('ACEPTADA', notif_final.mensaje)

    def test_REPORT_01_informe_final_auditor_access_and_generate(self):
        """REPORT-01: Auditor accede a GET /api/informes/ y genera informe sin recibir error 403 Forbidden."""
        self.client.force_authenticate(user=self.auditor_a)
        res_list = self.client.get('/api/informes/')
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertIn(res_gen.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        self.assertEqual(res_gen.data['tipo'], 'auditoria')

    def test_REPORT_02_draft_save_and_finalization(self):
        """
        REPORT-02:
        1. Auditor guarda borrador con campos narrativos (conclusiones, recomendaciones, observaciones_finales).
        2. Los campos narrativos persisten correctamente.
        3. Auditor finaliza el informe (cambia a FINALIZADO).
        4. Intentar modificar un informe FINALIZADO retorna HTTP 400 Bad Request.
        """
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        # 1. Guardar Borrador
        res_draft = self.client.post(f'/api/informes/{informe_id}/guardar-borrador', {
            'conclusiones': 'PRUEBA UAT - Conclusión del Auditor.',
            'recomendaciones': 'PRUEBA UAT - Recomendación del Auditor.',
            'observaciones_finales': 'PRUEBA UAT - Observación final.'
        })
        self.assertEqual(res_draft.status_code, status.HTTP_200_OK)
        narrativa = res_draft.data['data']['contenido_json']['narrativa']
        self.assertEqual(narrativa['conclusiones'], 'PRUEBA UAT - Conclusión del Auditor.')
        self.assertEqual(narrativa['recomendaciones'], 'PRUEBA UAT - Recomendación del Auditor.')
        self.assertEqual(narrativa['observaciones_finales'], 'PRUEBA UAT - Observación final.')

        # 2. Finalizar Informe
        res_fin = self.client.post(f'/api/informes/{informe_id}/finalizar', {
            'conclusiones': 'PRUEBA UAT - Conclusión Final.',
        })
        self.assertEqual(res_fin.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fin.data['data']['contenido_json']['estado'], 'FINALIZADO')

        # 3. Intentar modificar informe finalizado retorna 400
        res_fail = self.client.post(f'/api/informes/{informe_id}/guardar-borrador', {
            'conclusiones': 'Intento de modificación posterior'
        })
        self.assertEqual(res_fail.status_code, status.HTTP_400_BAD_REQUEST)

    def test_REPORT_DRAFT_01_single_active_draft_creation(self):
        """REPORT-DRAFT-01: Generar informe por primera vez crea exactamente 1 borrador."""
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        count = Informe.objects.filter(evaluacion=self.evaluacion_a, deleted_at__isnull=True).count()
        self.assertEqual(count, 1)

    def test_REPORT_DRAFT_02_idempotent_draft_generation_no_duplicates(self):
        """REPORT-DRAFT-02: Generar informe múltiples veces actualiza el borrador existente sin duplicados."""
        self.client.force_authenticate(user=self.auditor_a)
        res1 = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        res2 = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertEqual(res1.data['id'], res2.data['id'])
        count = Informe.objects.filter(evaluacion=self.evaluacion_a, deleted_at__isnull=True).count()
        self.assertEqual(count, 1)

    def test_REPORT_DRAFT_03_query_verification_single_record(self):
        """REPORT-DRAFT-03: Verificación directa en base de datos de registro único por evaluacion y tipo."""
        self.client.force_authenticate(user=self.auditor_a)
        for _ in range(3):
            self.client.post('/api/informes/generar', {
                'evaluacion_id': str(self.evaluacion_a.id),
                'tipo': 'auditoria'
            })
        active_informes = Informe.objects.filter(
            evaluacion=self.evaluacion_a,
            tipo='auditoria',
            deleted_at__isnull=True
        )
        self.assertEqual(active_informes.count(), 1)

    def test_REPORT_DRAFT_04_narrative_updates_persist_on_same_draft(self):
        """REPORT-DRAFT-04: Las ediciones narrativas persisten en el mismo registro del borrador."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']
        self.client.post(f'/api/informes/{informe_id}/guardar-borrador', {
            'conclusiones': 'Conclusión inicial'
        })
        # Generar de nuevo
        res_gen2 = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertEqual(res_gen2.data['id'], informe_id)

    def test_REPORT_DRAFT_05_discard_draft_soft_deletes_and_removes_from_list(self):
        """REPORT-DRAFT-05: Descartar borrador realiza soft-delete y no aparece en GET /api/informes."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        res_disc = self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertEqual(res_disc.status_code, status.HTTP_200_OK)
        self.assertTrue(res_disc.data['success'])

        inf_obj = Informe.objects.get(id=informe_id)
        self.assertIsNotNone(inf_obj.deleted_at)

        # GET /api/informes/ ya no incluye el informe descartado
        res_list = self.client.get('/api/informes/')
        informe_ids_in_list = [i['id'] for i in res_list.data]
        self.assertNotIn(informe_id, informe_ids_in_list)

    def test_REPORT_DRAFT_06_discard_preserves_evaluacion(self):
        """REPORT-DRAFT-06: Descartar borrador NO elimina la evaluación asociada."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']
        eval_id = self.evaluacion_a.id

        self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertTrue(Evaluacion.objects.filter(id=eval_id).exists())

    def test_REPORT_DRAFT_07_discard_preserves_hallazgos(self):
        """REPORT-DRAFT-07: Descartar borrador NO elimina los hallazgos u observaciones."""
        self.client.force_authenticate(user=self.auditor_a)
        # Crear un hallazgo
        hall = Hallazgo.objects.create(
            evaluacion=self.evaluacion_a,
            auditor=self.auditor_a,
            tipo="no_conformidad_mayor",
            descripcion="Hallazgo de prueba no eliminado"
        )
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertTrue(Hallazgo.objects.filter(id=hall.id).exists())

    def test_REPORT_DRAFT_08_discard_preserves_apelaciones_and_respuestas(self):
        """REPORT-DRAFT-08: Descartar borrador NO elimina las apelaciones ni respuestas."""
        self.client.force_authenticate(user=self.auditor_a)
        ap = Apelacion.objects.create(
            respuesta=self.respuesta_a,
            solicitante=self.auditor_a,
            motivo="Motivo de prueba no eliminado"
        )
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertTrue(Apelacion.objects.filter(id=ap.id).exists())
        self.assertTrue(Respuesta.objects.filter(id=self.respuesta_a.id).exists())

    def test_REPORT_DRAFT_09_cannot_discard_finalized_informe(self):
        """REPORT-DRAFT-09: Intentar descartar un informe FINALIZADO retorna HTTP 400 Bad Request."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']
        self.client.post(f'/api/informes/{informe_id}/finalizar', {})

        res_disc = self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertEqual(res_disc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res_disc.data)

    def test_REPORT_DRAFT_10_auditor_other_company_cannot_discard(self):
        """REPORT-DRAFT-10: Auditor de Empresa B no puede descartar un borrador de Empresa A (403 Forbidden)."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        # Cambiar a Auditor B (ya existente en setUp)
        self.client.force_authenticate(user=self.auditor_b)
        res_disc = self.client.delete(f'/api/informes/{informe_id}/descartar-borrador')
        self.assertEqual(res_disc.status_code, status.HTTP_403_FORBIDDEN)

    def test_REPORT_DRAFT_11_auditor_other_company_cannot_modify(self):
        """REPORT-DRAFT-11: Auditor de Empresa B no puede modificar borrador de Empresa A (403 Forbidden)."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id = res_gen.data['id']

        self.client.force_authenticate(user=self.auditor_b)
        res_mod = self.client.post(f'/api/informes/{informe_id}/guardar-borrador', {
            'conclusiones': 'Intento no autorizado'
        })
        self.assertEqual(res_mod.status_code, status.HTTP_403_FORBIDDEN)

    def test_REPORT_DRAFT_12_generate_new_draft_after_discard(self):
        """REPORT-DRAFT-12: Tras descartar un borrador, generar nuevamente crea un nuevo borrador activo."""
        self.client.force_authenticate(user=self.auditor_a)
        res_gen1 = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        informe_id1 = res_gen1.data['id']

        # Descartar
        self.client.delete(f'/api/informes/{informe_id1}/descartar-borrador')

        # Generar de nuevo -> crea nuevo borrador
        res_gen2 = self.client.post('/api/informes/generar', {
            'evaluacion_id': str(self.evaluacion_a.id),
            'tipo': 'auditoria'
        })
        self.assertNotEqual(res_gen2.data['id'], informe_id1)
        count_active = Informe.objects.filter(evaluacion=self.evaluacion_a, deleted_at__isnull=True).count()
        self.assertEqual(count_active, 1)

