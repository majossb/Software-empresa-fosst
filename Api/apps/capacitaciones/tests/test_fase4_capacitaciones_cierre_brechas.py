"""
Pruebas de la Fase 4: Capacitaciones que cierran brechas (§9 y HBSEO).

Criterio de Aceptación:
"Listo cuando: se puede recorrer en pantalla el ciclo completo:
brecha detectada → programar capacitación desde ella → registrar asistencia y certificados →
reevaluar → brecha subsanada y trabajador habilitado."
"""
from datetime import date, timedelta
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import (
    Trabajador,
    Capacitacion,
    ParticipanteCapacitacion,
    AfiliacionTrabajador,
)
from apps.gestion_humana.models import ExamenMedicoOcupacional
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from apps.formacion.models import (
    CursoFormacion,
    CargoRequisitoFormacion,
    RegistroFormacion,
    EvaluacionCompetencia,
)
from apps.hbseo.models import Brecha, BrechaEvento, BrechaAccion
from apps.michc.models import EvaluacionHabilitacion
from apps.michc.engine import recalcular_habilitacion


def _crear_empresa(nit="900999111-2"):
    return Empresa.objects.create(
        nombre="Empresa Fase 4 SAS",
        nit=nit,
        num_trabajadores=30,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa):
    return Usuario.objects.create_user(
        username="responsable_fase4",
        password="ClaveSegura123!",
        email="resp_fase4@test.com",
        documento="1098765433",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


def _crear_perfil(empresa, nombre="Inspector de Seguridad"):
    return PerfilCargo.objects.create(
        empresa=empresa,
        codigo="PC-INS-01",
        nombre_cargo=nombre,
        educacion="Tecnólogo en SST",
        experiencia="12 meses",
        criticidad_sst="alto",
        criticidad_vial="bajo",
        version_actual=1,
    )


def _crear_trabajador(empresa, perfil, nombre="Laura Morales", documento="1012345678"):
    return Trabajador.objects.create(
        empresa=empresa,
        perfil_cargo=perfil,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
        tipo_contrato="indefinido",
        fecha_ingreso=date.today() - timedelta(days=90),
    )


@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class Fase4CapacitacionesCierreBrechasTests(TestCase):
    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.perfil = _crear_perfil(self.empresa)
        self.trabajador = _crear_trabajador(self.empresa, self.perfil)
        self.today = date.today()

        # Requisitos médicos y de afiliación base cumplidos
        ExamenMedicoOcupacional.objects.create(
            trabajador=self.trabajador,
            tipo="ingreso",
            fecha_examen=self.today - timedelta(days=20),
            fecha_vencimiento=self.today + timedelta(days=345),
            concepto_aptitud="apto",
            presenta_restricciones=False,
        )
        AfiliacionTrabajador.objects.create(
            trabajador=self.trabajador,
            tipo="arl",
            entidad_nombre="Sura ARL",
        )

        self.curso_alturas = CursoFormacion.objects.create(
            empresa=self.empresa,
            nombre="Trabajo Seguro en Alturas",
            categoria=CursoFormacion.Categoria.TECNICA,
            vigencia_meses=12,
            requiere_certificado=True,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_ciclo_completo_brecha_curso_vencido_capacitacion_asistencia_y_subsanacion(self):
        """
        Ciclo completo para formación:
        1. Curso obligatorio se vence -> MICHC baja, se detecta brecha en HBSEO.
        2. Endpoint 'sugerir-participantes' sugiere al trabajador con razón curso vencido.
        3. Se programa capacitación ligada a la brecha y al curso.
        4. Se inscribe al trabajador y se registra su asistencia.
        5. Se finaliza la capacitación -> crea RegistroFormacion vigente, cierra la brecha a 'subsanada',
           genera BrechaEvento y el trabajador queda 'habilitado' (100%) en MICHC.
        """
        # Exigir curso obligatorio en el perfil
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=self.curso_alturas,
            obligatorio=True,
            vigencia_meses=12,
        )

        # 1. Curso vencido
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso_alturas,
            fecha_realizacion=self.today - timedelta(days=400),
            fecha_vencimiento=self.today - timedelta(days=35),
            origen="carga_manual",
        )
        eval_inicial = recalcular_habilitacion(self.trabajador.id)
        self.assertLess(eval_inicial.porcentaje_cumplimiento, 100.0)

        # Buscar la brecha generada
        brecha = Brecha.objects.filter(
            trabajador=self.trabajador,
            clasificacion="incumplimiento",
            origenes__modulo_origen="formacion",
        ).latest("fecha_deteccion")
        self.assertEqual(brecha.estado, Brecha.Estado.DETECTADA)

        # 2. Sugerir participantes
        res_sug = self.client.get(f"/api/capacitaciones/sugerir-participantes?curso_id={self.curso_alturas.id}&brecha_ids={brecha.id}")
        self.assertEqual(res_sug.status_code, status.HTTP_200_OK)
        sugeridos = res_sug.data
        self.assertTrue(any(s["trabajador_id"] == str(self.trabajador.id) for s in sugeridos))

        # 3. Programar capacitación ligada a la brecha y al curso
        payload_cap = {
            "tema": "Re-entrenamiento en Alturas 2026",
            "objetivo": "Cerrar brecha de certificación vencida para habilitación operativa",
            "curso": str(self.curso_alturas.id),
            "brechas": [str(brecha.id)],
            "proveedor": "Centro de Entrenamiento Alturas SAS",
            "fecha": (self.today + timedelta(days=2)).isoformat(),
            "horas_duracion": 8,
            "tiene_certificado": True,
            "estado": "programada",
        }
        res_crear = self.client.post("/api/capacitaciones", payload_cap, format="json")
        self.assertEqual(res_crear.status_code, status.HTTP_201_CREATED)
        cap_id = res_crear.data["id"]

        # 4. Inscribir trabajador
        res_insc = self.client.post(
            f"/api/capacitaciones/{cap_id}/inscribir-participantes",
            {"trabajadores_ids": [str(self.trabajador.id)]},
            format="json"
        )
        self.assertEqual(res_insc.status_code, status.HTTP_200_OK)
        self.assertEqual(res_insc.data["total_participantes"], 1)

        # Registrar asistencia
        res_asist = self.client.post(
            f"/api/capacitaciones/{cap_id}/registrar-asistencia",
            {
                "participantes": [
                    {
                        "trabajador_id": str(self.trabajador.id),
                        "asistio": True,
                        "certificado_url": "https://storage.empresa.com/cert-123.pdf",
                        "observaciones": "Completó prácticas y teoría con 100%"
                    }
                ]
            },
            format="json"
        )
        self.assertEqual(res_asist.status_code, status.HTTP_200_OK)

        # 5. Finalizar capacitación
        res_fin = self.client.post(f"/api/capacitaciones/{cap_id}/finalizar", {}, format="json")
        self.assertEqual(res_fin.status_code, status.HTTP_200_OK)
        self.assertEqual(res_fin.data["estado"], "realizada")

        # Verificar que se creó el nuevo RegistroFormacion vigente
        nuevo_reg = (
            RegistroFormacion.objects.filter(trabajador=self.trabajador, curso=self.curso_alturas)
            .order_by("-fecha_realizacion", "-created_at")
            .first()
        )
        self.assertIsNotNone(nuevo_reg)
        self.assertEqual(nuevo_reg.estado_derivado, "vigente")

        # Verificar que la Brecha pasó a SUBSANADA
        brecha.refresh_from_db()
        self.assertEqual(brecha.estado, Brecha.Estado.SUBSANADA)

        # Verificar trazabilidad en BrechaEvento
        evento_cierre = brecha.eventos.filter(tipo_evento=BrechaEvento.TipoEvento.CAMBIO_ESTADO).latest("created_at")
        self.assertIn("subsanada", evento_cierre.descripcion.lower())

        # Verificar que el trabajador quedó HABILITADO (100% verde)
        eval_final = EvaluacionHabilitacion.objects.get(trabajador=self.trabajador)
        self.assertEqual(eval_final.porcentaje_cumplimiento, 100.0)
        self.assertEqual(eval_final.semaforo, "verde")
        self.assertEqual(eval_final.estado_habilitacion, "habilitado")
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_operativo, "habilitado")

    def test_ciclo_competencia_reevaluacion_satisfactoria_cierra_brecha(self):
        """
        Ciclo completo para competencia:
        1. Trabajador tiene brecha en competencia -> Brecha detectada en HBSEO.
        2. Capacitación programada ligada a la competencia y a la brecha.
        3. En la asistencia se evalúa alcanzando el nivel requerido (L4).
        4. Al finalizar la capacitación, se genera EvaluacionCompetencia y la brecha se subsana.
        """
        comp = CargoCompetencia.objects.create(
            perfil_cargo=self.perfil,
            nombre="Inspección Vehicular Avanzada",
            tipo="tecnica",
            nivel_requerido=4,
        )
        # Evaluación inicial deficiente
        eval_comp_ini = EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=comp,
            nivel_alcanzado=2,
            evaluado_por=self.usuario,
            fecha_evaluacion=self.today - timedelta(days=20),
            metodo="observacion_directa",
        )
        recalcular_habilitacion(self.trabajador.id)
        brecha = Brecha.objects.filter(
            trabajador=self.trabajador,
            clasificacion="incumplimiento",
            origenes__modulo_origen="formacion",
        ).latest("fecha_deteccion")

        # Capacitación de la competencia
        cap = Capacitacion.objects.create(
            empresa=self.empresa,
            tema="Taller Teórico-Práctico de Inspección Vehicular",
            competencia=comp,
            fecha=self.today,
            estado=Capacitacion.Estado.PROGRAMADA,
        )
        cap.brechas.add(brecha)

        # Inscribir y registrar asistencia con nivel_alcanzado = 4 (cumple)
        ParticipanteCapacitacion.objects.create(
            capacitacion=cap,
            trabajador=self.trabajador,
            asistio=True,
            nivel_alcanzado=4,
        )

        res_fin = self.client.post(f"/api/capacitaciones/{cap.id}/finalizar", {}, format="json")
        self.assertEqual(res_fin.status_code, status.HTTP_200_OK)

        # Verificar que se creó la reevaluación de competencia
        eval_reeval = (
            EvaluacionCompetencia.objects.filter(trabajador=self.trabajador, cargo_competencia=comp)
            .order_by("-fecha_evaluacion", "-created_at")
            .first()
        )
        self.assertEqual(eval_reeval.nivel_alcanzado, 4)
        self.assertEqual(eval_reeval.brecha_calculada, 0)

        # Brecha subsanada
        brecha.refresh_from_db()
        self.assertEqual(brecha.estado, Brecha.Estado.SUBSANADA)

    def test_competencia_reevaluacion_insuficiente_mantiene_brecha_y_crea_accion(self):
        """
        Si tras la capacitación la reevaluación aún no alcanza el nivel requerido:
        - La brecha NO se cierra (sigue abierta).
        - Se crea una BrechaAccion sugerida para programar nuevo refuerzo.
        """
        comp = CargoCompetencia.objects.create(
            perfil_cargo=self.perfil,
            nombre="Investigación de Accidentes",
            tipo="tecnica",
            nivel_requerido=4,
        )
        eval_comp_ini = EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=comp,
            nivel_alcanzado=1,
            evaluado_por=self.usuario,
            fecha_evaluacion=self.today - timedelta(days=15),
            metodo="prueba_tecnica",
        )
        recalcular_habilitacion(self.trabajador.id)
        brecha = Brecha.objects.filter(
            trabajador=self.trabajador,
            origenes__modulo_origen="formacion",
        ).latest("fecha_deteccion")

        cap = Capacitacion.objects.create(
            empresa=self.empresa,
            tema="Seminario de Investigación de Accidentes",
            competencia=comp,
            fecha=self.today,
            estado=Capacitacion.Estado.PROGRAMADA,
        )
        cap.brechas.add(brecha)

        # Trabajador asiste pero solo alcanza nivel 2 (aún le faltan 2 niveles para L4)
        ParticipanteCapacitacion.objects.create(
            capacitacion=cap,
            trabajador=self.trabajador,
            asistio=True,
            nivel_alcanzado=2,
        )

        res_fin = self.client.post(f"/api/capacitaciones/{cap.id}/finalizar", {}, format="json")
        self.assertEqual(res_fin.status_code, status.HTTP_200_OK)

        # La brecha NO debe estar subsanada
        brecha.refresh_from_db()
        self.assertNotEqual(brecha.estado, Brecha.Estado.SUBSANADA)

        # Debe haberse creado una acción programada de seguimiento
        acciones = BrechaAccion.objects.filter(brecha=brecha)
        self.assertTrue(acciones.exists())
        self.assertIn("refuerzo", acciones.latest("created_at").descripcion.lower())
