from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Candidato,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
    PostulacionEvento,
)
from apps.reclutamiento.services.transiciones import (
    TransicionInvalidaError,
    RequisitoIncumplidoError,
    EtapaObligatoriaFaltanteError,
    MotivoRequeridoError,
    CuposAgotadosError,
    ExcepcionNoAutorizadaError,
)
from apps.reclutamiento.services.postulacion import (
    transicionar_postulacion,
    registrar_postulacion,
    preseleccionar_candidato,
    seleccionar_candidato,
    cerrar_postulacion,
    reabrir_postulacion_excepcional,
)

Usuario = get_user_model()


class FaseBTransicionesTestCase(TestCase):
    """
    Suite de pruebas exhaustiva para la máquina de estados de Postulacion (Fase B).
    Verifica RN-R01 hasta RN-R09.
    """

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nit="900555666-3",
            nombre="Industrias del Futuro S.A.S.",
            num_trabajadores=40,
            nivel_riesgo=3,
            capitulo_vigente="II",
        )
        self.usuario_rh = Usuario.objects.create_user(
            username="rh_user",
            email="rh@empresa.com",
            password="Password123!",
            rol="responsable",
            empresa=self.empresa,
        )
        self.sede = Sede.objects.create(
            empresa=self.empresa,
            nombre="Sede Norte",
            ciudad="Barranquilla",
        )
        self.cargo = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-2026-0005",
            nombre_cargo="Supervisor de Seguridad Industrial",
            nivel_riesgo=3,
        )
        self.vacante = Vacante.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo,
            sede=self.sede,
            titulo="Convocatoria Supervisor SST",
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
                {"id": "licencia_sst", "nombre": "Licencia en SST vigente"},
                {"id": "exp_minima", "nombre": "Experiencia mínima de 2 años"},
            ],
        )
        self.candidato_1 = Candidato.objects.create(
            empresa=self.empresa,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="11223344",
            nombres="Andrés",
            apellidos="Moreno",
            email="andres.moreno@example.com",
        )
        self.candidato_2 = Candidato.objects.create(
            empresa=self.empresa,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="55667788",
            nombres="Beatriz",
            apellidos="Salazar",
            email="beatriz.salazar@example.com",
        )

    def test_rn_r01_flujo_completo_exitoso_y_eventos(self):
        """RN-R01/RN-R08: Transiciones válidas paso a paso registran su línea de tiempo inmutable."""
        postulacion = registrar_postulacion(
            candidato=self.candidato_1,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.POSTULADO)
        self.assertEqual(postulacion.eventos.count(), 1)

        # 1. En revisión
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_REVISION,
            usuario=self.usuario_rh,
            motivo="Inicio de análisis de CV",
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_REVISION)

        # 2. Preseleccionado
        preseleccionar_candidato(
            postulacion=postulacion,
            calificacion_requisitos={"licencia_sst": True, "exp_minima": True},
            usuario=self.usuario_rh,
            puntuacion=95.0,
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.PRESELECCIONADO)

        # 3. En entrevista
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_ENTREVISTA,
            usuario=self.usuario_rh,
            motivo="Entrevista técnica programada",
            contexto={"etapas_completadas": ["entrevista"]},
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_ENTREVISTA)

        # 4. En evaluación
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_EVALUACION,
            usuario=self.usuario_rh,
            motivo="Prueba psicotécnica aplicada",
            contexto={"etapas_completadas": ["evaluacion"]},
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_EVALUACION)

        # 5. En validación documental
        transicionar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.EN_VALIDACION,
            usuario=self.usuario_rh,
            motivo="Verificación de antecedentes y referencias",
            contexto={"etapas_completadas": ["validacion_documental"]},
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_VALIDACION)

        # 6. Selección final
        seleccionar_candidato(
            postulacion=postulacion,
            usuario=self.usuario_rh,
            notas_finales="Candidato idóneo seleccionado",
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.SELECCIONADO)

        # Trazabilidad total de eventos inmutables
        self.assertGreaterEqual(postulacion.eventos.count(), 6)

    def test_rn_r01_bloqueo_transicion_invalida(self):
        """RN-R01: Se rechaza saltar estados no permitidos en la máquina de estados."""
        postulacion = registrar_postulacion(
            candidato=self.candidato_1,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        # Intentar pasar directo de POSTULADO a SELECCIONADO
        with self.assertRaises(TransicionInvalidaError):
            transicionar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.SELECCIONADO,
                usuario=self.usuario_rh,
            )

    def test_rn_r02_bloqueo_preseleccion_requisitos_incumplidos(self):
        """RN-R02: No se puede preseleccionar si no cumple requisitos obligatorios."""
        postulacion = registrar_postulacion(
            candidato=self.candidato_1,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        # Cumple licencia pero incumple experiencia mínima
        calificacion = {"licencia_sst": True, "exp_minima": False}
        with self.assertRaises(RequisitoIncumplidoError) as ctx:
            preseleccionar_candidato(
                postulacion=postulacion,
                calificacion_requisitos=calificacion,
                usuario=self.usuario_rh,
            )
        self.assertIn("Experiencia mínima de 2 años", str(ctx.exception))

    def test_rn_r03_bloqueo_seleccion_sin_etapas_obligatorias(self):
        """RN-R03: No se puede seleccionar si no ha completado las etapas obligatorias del proceso."""
        postulacion = registrar_postulacion(
            candidato=self.candidato_1,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        preseleccionar_candidato(
            postulacion=postulacion,
            calificacion_requisitos={"licencia_sst": True, "exp_minima": True},
            usuario=self.usuario_rh,
        )
        # Intentar seleccionar sin registrar entrevista, evaluacion ni validacion
        with self.assertRaises(EtapaObligatoriaFaltanteError) as ctx:
            seleccionar_candidato(
                postulacion=postulacion,
                usuario=self.usuario_rh,
            )
        self.assertIn("Entrevista", str(ctx.exception))
        self.assertIn("Evaluación", str(ctx.exception))

    def test_rn_r04_motivo_obligatorio_en_cierre(self):
        """RN-R04: Cerrar a NO_SELECCIONADO sin motivo es rechazado."""
        postulacion = registrar_postulacion(
            candidato=self.candidato_1,
            proceso_seleccion=self.proceso,
            usuario=self.usuario_rh,
        )
        with self.assertRaises(MotivoRequeridoError):
            cerrar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.NO_SELECCIONADO,
                motivo="",
                usuario=self.usuario_rh,
            )

    def test_rn_r06_cierre_automatico_al_cubrir_vacante(self):
        """RN-R06: Al seleccionar N candidatos cubriendo cupos, las demás postulaciones activas se cierran."""
        post_1 = registrar_postulacion(candidato=self.candidato_1, proceso_seleccion=self.proceso)
        post_2 = registrar_postulacion(candidato=self.candidato_2, proceso_seleccion=self.proceso)

        # Preparar post_1 con todas las etapas completas
        preseleccionar_candidato(
            postulacion=post_1,
            calificacion_requisitos={"licencia_sst": True, "exp_minima": True},
        )
        post_1.etapas_completadas = ["entrevista", "evaluacion", "validacion_documental"]
        post_1.save()

        # Seleccionar post_1 -> Llena el cupo (1 de 1)
        seleccionar_candidato(postulacion=post_1, usuario=self.usuario_rh)

        post_1.refresh_from_db()
        post_2.refresh_from_db()
        self.vacante.refresh_from_db()

        self.assertEqual(post_1.estado, Postulacion.Estado.SELECCIONADO)
        self.assertEqual(self.vacante.estado, Vacante.Estado.CUBIERTA)
        self.assertEqual(self.vacante.numero_seleccionados, 1)

        # post_2 debe haberse cerrado automáticamente como NO_SELECCIONADO
        self.assertEqual(post_2.estado, Postulacion.Estado.NO_SELECCIONADO)
        self.assertIn("Vacante cubierta", post_2.motivo_cierre)
        # Verifica que el evento de cierre quedó registrado
        ultimo_evento = post_2.eventos.last()
        self.assertEqual(ultimo_evento.estado_nuevo, Postulacion.Estado.NO_SELECCIONADO)

    def test_rn_r07_reapertura_excepcional(self):
        """RN-R07: Reapertura excepcional crea un nuevo evento sin borrar la historia."""
        postulacion = registrar_postulacion(candidato=self.candidato_1, proceso_seleccion=self.proceso)
        cerrar_postulacion(
            postulacion=postulacion,
            nuevo_estado=Postulacion.Estado.NO_SELECCIONADO,
            motivo="Descarte inicial por salario",
            usuario=self.usuario_rh,
        )
        self.assertEqual(postulacion.estado, Postulacion.Estado.NO_SELECCIONADO)
        conteo_eventos_antes = postulacion.eventos.count()

        # Reabrir por excepción
        reabrir_postulacion_excepcional(
            postulacion=postulacion,
            justificacion="Candidato ajustó su aspiración salarial y fue autorizado por Gerencia",
            usuario=self.usuario_rh,
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.EN_REVISION)
        self.assertTrue(postulacion.es_excepcion)
        self.assertEqual(postulacion.eventos.count(), conteo_eventos_antes + 1)
        self.assertTrue(postulacion.eventos.last().es_excepcion)

    def test_rn_r09_excepcion_sin_justificacion_es_rechazada(self):
        """RN-R09: Si se intenta una excepción sin justificación explícita, se rechaza."""
        postulacion = registrar_postulacion(candidato=self.candidato_1, proceso_seleccion=self.proceso)
        with self.assertRaises(ExcepcionNoAutorizadaError):
            transicionar_postulacion(
                postulacion=postulacion,
                nuevo_estado=Postulacion.Estado.EN_REVISION,
                usuario=self.usuario_rh,
                es_excepcion=True,
                justificacion_excepcion="",  # Vacía
            )
