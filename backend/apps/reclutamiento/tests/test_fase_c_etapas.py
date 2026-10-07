from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Candidato,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    Entrevista,
    Evaluacion,
    ValidacionDocumental,
    PostulacionEvento,
)
from apps.reclutamiento.services.postulacion import (
    registrar_postulacion,
    preseleccionar_candidato,
    seleccionar_candidato,
)
from apps.reclutamiento.services.etapas import (
    registrar_y_completar_entrevista,
    registrar_y_completar_evaluacion,
    registrar_y_completar_validacion,
)

Usuario = get_user_model()


class FaseCEtapasTestCase(TestCase):
    """
    Suite de pruebas para etapas subordinadas a la postulación (Entrevistas, Evaluaciones, Validaciones).
    """

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nit="900777888-4",
            nombre="Logística y Transporte S.A.S.",
            num_trabajadores=30,
            nivel_riesgo=2,
            capitulo_vigente="II",
        )
        self.usuario_rh = Usuario.objects.create_user(
            username="rh_etapas",
            email="rh_etapas@empresa.com",
            password="Password123!",
            rol="responsable",
            empresa=self.empresa,
        )
        self.cargo = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-2026-0010",
            nombre_cargo="Coordinador Logístico",
            nivel_riesgo=2,
        )
        self.vacante = Vacante.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo,
            titulo="Convocatoria Coordinador Logístico",
            numero_cupos=1,
            estado=Vacante.Estado.ABIERTA,
        )
        self.proceso = ProcesoSeleccion.objects.create(
            empresa=self.empresa,
            vacante=self.vacante,
            responsable_rh=self.usuario_rh,
            requiere_entrevista=True,
            requiere_evaluacion=True,
            requiere_validacion_documental=True,
            requisitos_obligatorios=[
                {"id": "titulo", "nombre": "Título profesional en Logística o Ing. Industrial"},
            ],
        )
        self.candidato = Candidato.objects.create(
            empresa=self.empresa,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="77889900",
            nombres="Diana",
            apellidos="Restrepo",
            email="diana.restrepo@example.com",
        )

    def test_flujo_integral_etapas_y_seleccion_exitosa(self):
        """
        Verifica el paso por cada etapa y la habilitación de la selección final
        al completar entrevista, evaluación y validación documental.
        """
        # 1. Postulación y preselección
        postulacion = registrar_postulacion(
            candidato=self.candidato,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        preseleccionar_candidato(
            postulacion=postulacion,
            calificacion_requisitos={"titulo": True},
            usuario=self.usuario_rh,
            puntuacion=90.0,
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.PRESELECCIONADO)

        # 2. Registrar Entrevista Técnica Favorable
        entrevista = registrar_y_completar_entrevista(
            postulacion=postulacion,
            tipo_entrevista=Entrevista.TipoEntrevista.TECNICA,
            modalidad=Entrevista.Modalidad.VIRTUAL,
            fecha_programada=timezone.now(),
            calificacion=95.0,
            concepto=Entrevista.Concepto.FAVORABLE,
            observaciones="Excelente manejo de ERP y gestión de flota",
            usuario=self.usuario_rh,
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_ENTREVISTA)
        self.assertIn("entrevista", postulacion.etapas_completadas)
        self.assertEqual(entrevista.estado, Entrevista.Estado.REALIZADA)

        # 3. Registrar Prueba Técnica Aprobada (85/100 -> >= 70%)
        evaluacion = registrar_y_completar_evaluacion(
            postulacion=postulacion,
            tipo_evaluacion=Evaluacion.TipoEvaluacion.TECNICA,
            nombre_prueba="Evaluación de Operaciones Logísticas",
            puntaje_obtenido=85.0,
            puntaje_maximo=100.0,
            porcentaje_aprobacion=70.0,
            usuario=self.usuario_rh,
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_EVALUACION)
        self.assertIn("evaluacion", postulacion.etapas_completadas)
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.APROBADA)

        # 4. Registrar Validación Documental Conforme
        validacion = registrar_y_completar_validacion(
            postulacion=postulacion,
            tipo_verificacion=ValidacionDocumental.TipoVerificacion.REFERENCIA_LABORAL,
            entidad_o_contacto="Transportes Unidos S.A.S. - Jefe de Operaciones",
            estado=ValidacionDocumental.Estado.VERIFICADO_CONFORME,
            detalles_verificacion="Desempeño sobresaliente y retiro voluntario confirmado",
            usuario=self.usuario_rh,
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_VALIDACION)
        self.assertIn("validacion_documental", postulacion.etapas_completadas)
        self.assertEqual(validacion.estado, ValidacionDocumental.Estado.VERIFICADO_CONFORME)

        # 5. Selección final autorizada (todas las etapas cumplidas)
        seleccionar_candidato(
            postulacion=postulacion,
            usuario=self.usuario_rh,
            notas_finales="Candidata aprobó todo el proceso de selección con honores",
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.SELECCIONADO)
        self.assertEqual(self.vacante.proceso_seleccion.postulaciones.filter(estado=Postulacion.Estado.SELECCIONADO).count(), 1)

    def test_evaluacion_reprobada_no_agrega_etapa(self):
        """Verifica que una prueba no aprobada (puntaje < umbral) no marca la etapa como superada."""
        postulacion = registrar_postulacion(
            candidato=self.candidato,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        preseleccionar_candidato(
            postulacion=postulacion,
            calificacion_requisitos={"titulo": True},
            usuario=self.usuario_rh,
        )

        evaluacion = registrar_y_completar_evaluacion(
            postulacion=postulacion,
            tipo_evaluacion=Evaluacion.TipoEvaluacion.TECNICA,
            nombre_prueba="Examen de Aptitud Operativa",
            puntaje_obtenido=50.0,
            puntaje_maximo=100.0,
            porcentaje_aprobacion=70.0,
            usuario=self.usuario_rh,
        )
        postulacion.refresh_from_db()
        self.assertEqual(evaluacion.estado, Evaluacion.Estado.NO_APROBADA)
        self.assertNotIn("evaluacion", postulacion.etapas_completadas)
