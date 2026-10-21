"""
Pruebas de la Fase 3: Integración de Formación y Competencias en MICHC y HBSEO.

Criterio de Aceptación Clave:
"Listo cuando: vencer un curso obligatorio baja el porcentaje del trabajador,
cambia su estado operativo y deja una brecha visible; renovarlo lo revierte."
"""
from datetime import date, timedelta
from django.test import TestCase, override_settings

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador, AfiliacionTrabajador
from apps.gestion_humana.models import ExamenMedicoOcupacional
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from apps.formacion.models import (
    CursoFormacion,
    CargoRequisitoFormacion,
    RegistroFormacion,
    EvaluacionCompetencia,
)
from apps.hbseo.models import Brecha
from apps.michc.models import EvaluacionHabilitacion, DetalleCumplimientoRequisito
from apps.michc.engine import recalcular_habilitacion


def _crear_empresa(nit="900888999-1"):
    return Empresa.objects.create(
        nombre="Empresa Fase 3 SAS",
        nit=nit,
        num_trabajadores=30,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa):
    return Usuario.objects.create_user(
        username="responsable_fase3",
        password="ClaveSegura123!",
        email="resp_fase3@test.com",
        documento="1098765432",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


def _crear_perfil(empresa, nombre="Supervisor de Seguridad"):
    return PerfilCargo.objects.create(
        empresa=empresa,
        codigo="PC-SUP-01",
        nombre_cargo=nombre,
        educacion="Profesional en SST o afines",
        experiencia="24 meses en supervisión de campo",
        criticidad_sst="medio",
        criticidad_vial="bajo",
        version_actual=1,
    )


def _crear_trabajador(empresa, perfil):
    return Trabajador.objects.create(
        empresa=empresa,
        perfil_cargo=perfil,
        nombre="Carlos Restrepo",
        documento="71234567",
        tipo_vinculacion="dependiente",
        tipo_contrato="indefinido",
        fecha_ingreso=date.today() - timedelta(days=120),
    )


@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class Fase3MichcHbseoFormacionTests(TestCase):
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
            fecha_examen=self.today - timedelta(days=40),
            fecha_vencimiento=self.today + timedelta(days=325),
            concepto_aptitud="apto",
            presenta_restricciones=False,
        )
        AfiliacionTrabajador.objects.create(
            trabajador=self.trabajador,
            tipo="arl",
            entidad_nombre="ARL Sura",
        )

        # Cursos del catálogo
        self.curso_alturas = CursoFormacion.objects.create(
            empresa=self.empresa,
            nombre="Trabajo Seguro en Alturas",
            categoria=CursoFormacion.Categoria.TECNICA,
            vigencia_meses=12,
            requiere_certificado=True,
        )
        self.curso_defensivo = CursoFormacion.objects.create(
            empresa=self.empresa,
            nombre="Manejo Defensivo",
            categoria=CursoFormacion.Categoria.VIAL,
            vigencia_meses=24,
            requiere_certificado=True,
        )

    def test_criterio_aceptacion_vencer_curso_baja_porcentaje_deja_brecha_y_renovar_lo_revierte(self):
        """
        CRITERIO DE ACEPTACIÓN PRINCIPAL:
        1. Trabajador con curso obligatorio vigente -> 100% / verde / habilitado.
        2. Vencer el curso obligatorio -> baja porcentaje, cambia estado operativo a restringido/no_apto,
           y deja una brecha visible en HBSEO (origen formacion).
        3. Renovar el curso -> revierte a 100% / verde / habilitado, y la brecha en HBSEO pasa a subsanada.
        """
        # Exigir curso obligatorio en el perfil
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=self.curso_alturas,
            obligatorio=True,
            vigencia_meses=12,
        )

        # 1. Trabajador con curso VIGENTE
        reg = RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=self.curso_alturas,
            fecha_realizacion=self.today - timedelta(days=30),
            fecha_vencimiento=self.today + timedelta(days=335),
            origen="carga_manual",
        )

        eval1 = recalcular_habilitacion(self.trabajador.id)
        self.assertEqual(eval1.porcentaje_cumplimiento, 100.0)
        self.assertEqual(eval1.semaforo, "verde")
        self.assertEqual(eval1.estado_habilitacion, "habilitado")
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_operativo, "habilitado")

        # 2. VENCER EL CURSO (fecha_vencimiento en el pasado)
        reg.fecha_vencimiento = self.today - timedelta(days=10)
        reg.save()

        eval2 = recalcular_habilitacion(self.trabajador.id)
        # El porcentaje debe bajar (< 100.0)
        self.assertLess(eval2.porcentaje_cumplimiento, 100.0)
        self.assertIn(eval2.semaforo, ["amarillo", "rojo"])
        self.assertNotEqual(eval2.estado_habilitacion, "habilitado")
        self.trabajador.refresh_from_db()
        self.assertNotEqual(self.trabajador.estado_operativo, "habilitado")

        # Debe existir una brecha en HBSEO originada en 'formacion' con clasificacion 'incumplimiento'
        brechas_formacion = Brecha.objects.filter(
            trabajador=self.trabajador,
            origenes__modulo_origen="formacion",
            clasificacion="incumplimiento",
        )
        self.assertTrue(brechas_formacion.exists())
        brecha = brechas_formacion.latest("fecha_deteccion")
        self.assertEqual(brecha.estado, Brecha.Estado.DETECTADA)
        self.assertIn("Trabajo Seguro en Alturas", brecha.origenes.first().descripcion)

        # 3. RENOVAR EL CURSO (nuevo registro vigente)
        with self.captureOnCommitCallbacks(execute=True):
            RegistroFormacion.objects.create(
                trabajador=self.trabajador,
                curso=self.curso_alturas,
                fecha_realizacion=self.today,
                fecha_vencimiento=self.today + timedelta(days=365),
                origen="capacitacion_interna",
            )

        eval3 = recalcular_habilitacion(self.trabajador.id)
        # El porcentaje se recupera al 100% y semáforo verde
        self.assertEqual(eval3.porcentaje_cumplimiento, 100.0)
        self.assertEqual(eval3.semaforo, "verde")
        self.assertEqual(eval3.estado_habilitacion, "habilitado")
        self.trabajador.refresh_from_db()
        self.assertEqual(self.trabajador.estado_operativo, "habilitado")

        # La brecha en HBSEO debe haberse marcado como SUBSANADA
        brecha.refresh_from_db()
        self.assertEqual(brecha.estado, Brecha.Estado.SUBSANADA)

    def test_curso_obligatorio_faltante_genera_brecha_y_baja_cumplimiento(self):
        """Un curso obligatorio del que el trabajador no tiene registro genera brecha y baja cumplimiento."""
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=self.curso_defensivo,
            obligatorio=True,
            vigencia_meses=24,
        )

        evaluacion = recalcular_habilitacion(self.trabajador.id)
        self.assertLess(evaluacion.porcentaje_cumplimiento, 100.0)

        # Detalle de requisito dice 'no' y explica la falta
        req_det = evaluacion.detalles_requisitos.filter(
            tipo_requisito="formacion",
            requisito_descripcion__icontains="Manejo Defensivo",
        ).first()
        self.assertIsNotNone(req_det)
        self.assertEqual(req_det.cumple, "no")
        self.assertIn("No registra formación", req_det.observacion)

        # Debe generar brecha como 'oportunidad_mejora' en HBSEO
        brecha = Brecha.objects.filter(
            trabajador=self.trabajador,
            origenes__modulo_origen="formacion",
            clasificacion="oportunidad_mejora",
        ).first()
        self.assertIsNotNone(brecha)
        self.assertIn("faltante", brecha.origenes.first().descripcion)

    def test_educacion_y_experiencia_aparecen_como_pendiente_de_validar(self):
        """
        Verifica que los requisitos de educación y experiencia se listen con estado
        'pendiente' (Pendiente de validar) y observación transparente.
        """
        evaluacion = recalcular_habilitacion(self.trabajador.id)

        req_edu = evaluacion.detalles_requisitos.filter(tipo_requisito="educacion").first()
        self.assertIsNotNone(req_edu)
        self.assertEqual(req_edu.cumple, DetalleCumplimientoRequisito.Cumple.PENDIENTE)
        self.assertIn("Pendiente de validar", req_edu.observacion)

        req_exp = evaluacion.detalles_requisitos.filter(tipo_requisito="experiencia").first()
        self.assertIsNotNone(req_exp)
        self.assertEqual(req_exp.cumple, DetalleCumplimientoRequisito.Cumple.PENDIENTE)
        self.assertIn("Pendiente de validar", req_exp.observacion)

    def test_competencia_no_aprobada_genera_brecha_y_recalifica_michc(self):
        """
        Evaluación de competencia vs nivel esperado:
        - Si brecha >= 2: incumple (cumple='no', brecha HBSEO='incumplimiento').
        - Si brecha = 1: parcial (cumple='parcial', brecha HBSEO='oportunidad_mejora').
        - Si nivel alcanzado >= nivel requerido: cumple='si' y subsana brecha en HBSEO.
        """
        comp = CargoCompetencia.objects.create(
            perfil_cargo=self.perfil,
            nombre="Liderazgo de Equipos SST",
            tipo="organizacional",
            nivel_requerido=4,
        )

        # 1. Evaluación con brecha = 2 (Nivel 2 vs 4) -> Incumplimiento
        eval_comp = EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=comp,
            nivel_alcanzado=2,
            evaluado_por=self.usuario,
            fecha_evaluacion=self.today,
            metodo="evaluacion_360",
        )

        eval_michc1 = recalcular_habilitacion(self.trabajador.id)
        req_comp = eval_michc1.detalles_requisitos.filter(tipo_requisito="competencia").first()
        self.assertIsNotNone(req_comp)
        self.assertEqual(req_comp.cumple, "no")
        self.assertIn("Brecha de 2 niveles", req_comp.observacion)

        brecha_comp = Brecha.objects.filter(
            trabajador=self.trabajador,
            clasificacion="incumplimiento",
            origenes__modulo_origen="formacion",
        ).latest("fecha_deteccion")
        self.assertEqual(brecha_comp.estado, Brecha.Estado.DETECTADA)

        # 2. Re-evaluación con nivel alcanzado = 4 (Cumple requerido)
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador,
            cargo_competencia=comp,
            nivel_alcanzado=4,
            evaluado_por=self.usuario,
            fecha_evaluacion=self.today + timedelta(days=1),
            metodo="prueba_tecnica",
        )

        eval_michc2 = recalcular_habilitacion(self.trabajador.id)
        req_comp2 = eval_michc2.detalles_requisitos.filter(tipo_requisito="competencia").first()
        self.assertEqual(req_comp2.cumple, "si")
        self.assertIn("cumple o supera", req_comp2.observacion)

        # Brecha subsanada
        brecha_comp.refresh_from_db()
        self.assertEqual(brecha_comp.estado, Brecha.Estado.SUBSANADA)

    def test_grupo_alternativo_cursos_cumple_cualquiera(self):
        """
        En un grupo alternativo (ej. SST 50h o SST 20h), completar cualquiera
        de los cursos satisface el requisito en MICHC al 100%.
        """
        curso_50h = CursoFormacion.objects.create(
            empresa=self.empresa,
            nombre="Curso SST 50 Horas",
            categoria=CursoFormacion.Categoria.SST,
            vigencia_meses=36,
        )
        curso_20h = CursoFormacion.objects.create(
            empresa=self.empresa,
            nombre="Curso SST 20 Horas",
            categoria=CursoFormacion.Categoria.SST,
            vigencia_meses=36,
        )

        # Configurar ambos como alternativos en el perfil
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=curso_50h,
            obligatorio=True,
            grupo_alternativo="sst_responsable",
        )
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=self.perfil,
            curso=curso_20h,
            obligatorio=True,
            grupo_alternativo="sst_responsable",
        )

        # Trabajador solo realiza el de 20h
        RegistroFormacion.objects.create(
            trabajador=self.trabajador,
            curso=curso_20h,
            fecha_realizacion=self.today - timedelta(days=15),
            fecha_vencimiento=self.today + timedelta(days=1000),
            origen="capacitacion_interna",
        )

        eval_michc = recalcular_habilitacion(self.trabajador.id)
        self.assertEqual(eval_michc.porcentaje_cumplimiento, 100.0)
        self.assertEqual(eval_michc.semaforo, "verde")

        req_alt = eval_michc.detalles_requisitos.filter(
            tipo_requisito="formacion",
            requisito_descripcion__icontains="alternativa",
        ).first()
        self.assertIsNotNone(req_alt)
        self.assertEqual(req_alt.cumple, "si")
        self.assertIn("Curso SST 20 Horas", req_alt.observacion)
