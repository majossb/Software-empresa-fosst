"""
Fase G — Reglas de entrevista/evaluación/selección:
- Entrevista desfavorable: cierre automático + notificación.
- Puntaje de entrevista reflejado en la postulación.
- Umbrales de evaluación (0-60 crítico / 61-80 alerta / 81+ apto).
- Cierre por falta de documentos.
- Selección masiva por cupos.
- Exportación del histórico (csv/xlsx/pdf).
"""
from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Candidato, Vacante, ProcesoSeleccion, Postulacion,
)
from apps.reclutamiento.services.etapas import (
    registrar_y_completar_entrevista,
    registrar_y_completar_evaluacion,
)


def _empresa(nit, nombre):
    return Empresa.objects.create(
        nit=nit, nombre=nombre, num_trabajadores=20, nivel_riesgo=2, capitulo_vigente="I",
    )


def _contexto(empresa, sufijo, *, req_ent=True, req_eval=True, req_val=False,
              cupos=1, estado=Postulacion.Estado.PRESELECCIONADO):
    sede = Sede.objects.create(empresa=empresa, nombre=f"Sede {sufijo}", ciudad="Bogotá")
    cargo = PerfilCargo.objects.create(empresa=empresa, codigo=f"PC-{sufijo}", nombre_cargo=f"Cargo {sufijo}")
    vacante = Vacante.objects.create(
        empresa=empresa, perfil_cargo=cargo, sede=sede,
        titulo=f"Vacante {sufijo}", numero_cupos=cupos, estado=Vacante.Estado.ABIERTA,
    )
    proceso = ProcesoSeleccion.objects.create(
        empresa=empresa, vacante=vacante,
        requiere_entrevista=req_ent,
        requiere_evaluacion=req_eval,
        requiere_validacion_documental=req_val,
    )
    candidato = Candidato.objects.create(
        empresa=empresa, documento=f"DOC-{sufijo}", nombres="Cand", apellidos=sufijo,
        email=f"cand.{sufijo}@mail.com",
    )
    postulacion = Postulacion.objects.create(
        empresa=empresa, candidato=candidato, proceso_seleccion=proceso, estado=estado,
    )
    return proceso, candidato, postulacion


class FaseGReglasTestCase(APITestCase):
    def setUp(self):
        self.empresa = _empresa("900700001-1", "Empresa G")
        self.user = Usuario.objects.create_user(
            username="g_user", email="g@a.com", password="Password123!",
            rol=UserRole.RESPONSABLE, empresa=self.empresa, activo=True, is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    def test_entrevista_desfavorable_cierra_y_notifica(self):
        proceso, cand, post = _contexto(self.empresa, "DESF", req_ent=True)
        with patch("apps.reclutamiento.services.notificaciones._enviar") as send, \
                self.captureOnCommitCallbacks(execute=True):
            registrar_y_completar_entrevista(
                postulacion=post, tipo_entrevista="tecnica", modalidad="virtual",
                fecha_programada=timezone.now(), calificacion=40,
                concepto="desfavorable", observaciones="No cumple competencias",
                usuario=self.user,
            )
        post.refresh_from_db()
        self.assertEqual(post.estado, Postulacion.Estado.NO_SELECCIONADO)
        self.assertEqual(post.puntuacion_general, 40)
        send.assert_called_once()

    def test_entrevista_favorable_actualiza_puntaje(self):
        proceso, cand, post = _contexto(self.empresa, "FAV", req_ent=True)
        registrar_y_completar_entrevista(
            postulacion=post, tipo_entrevista="tecnica", modalidad="virtual",
            fecha_programada=timezone.now(), calificacion=88,
            concepto="favorable", usuario=self.user,
        )
        post.refresh_from_db()
        self.assertEqual(post.puntuacion_general, 88)
        self.assertIn("entrevista", post.etapas_completadas)
        self.assertEqual(post.estado, Postulacion.Estado.EN_ENTREVISTA)

    def test_evaluacion_critica_cierra_no_seleccionado(self):
        proceso, cand, post = _contexto(self.empresa, "CRIT", req_ent=False, req_eval=True)
        with patch("apps.reclutamiento.services.notificaciones._enviar") as send, \
                self.captureOnCommitCallbacks(execute=True):
            registrar_y_completar_evaluacion(
                postulacion=post, tipo_evaluacion="tecnica", nombre_prueba="Prueba",
                puntaje_obtenido=60, puntaje_maximo=100, usuario=self.user,
            )
        post.refresh_from_db()
        self.assertEqual(post.estado, Postulacion.Estado.NO_SELECCIONADO)
        send.assert_called_once()

    def test_evaluacion_alerta_continua_con_refuerzo(self):
        proceso, cand, post = _contexto(self.empresa, "ALERT", req_ent=False, req_eval=True)
        ev = registrar_y_completar_evaluacion(
            postulacion=post, tipo_evaluacion="tecnica", nombre_prueba="Prueba",
            puntaje_obtenido=70, puntaje_maximo=100, usuario=self.user,
        )
        post.refresh_from_db()
        self.assertEqual(ev.estado, "aprobada")
        self.assertIn("evaluacion", post.etapas_completadas)
        self.assertEqual(post.estado, Postulacion.Estado.EN_EVALUACION)

    def test_evaluacion_apta(self):
        proceso, cand, post = _contexto(self.empresa, "APTO", req_ent=False, req_eval=True)
        ev = registrar_y_completar_evaluacion(
            postulacion=post, tipo_evaluacion="tecnica", nombre_prueba="Prueba",
            puntaje_obtenido=85, puntaje_maximo=100, usuario=self.user,
        )
        self.assertEqual(ev.estado, "aprobada")
        post.refresh_from_db()
        self.assertIn("evaluacion", post.etapas_completadas)

    def test_cerrar_por_falta_documentos(self):
        proceso, cand, post = _contexto(self.empresa, "DOCS", estado=Postulacion.Estado.EN_VALIDACION)
        with patch("apps.reclutamiento.services.notificaciones._enviar") as send, \
                self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(f"/api/reclutamiento/postulaciones/{post.id}/cerrar-por-falta-documentos/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.estado, Postulacion.Estado.NO_CONTINUO)
        send.assert_called_once()

    def test_seleccion_masiva_cubre_cupos_y_cierra_resto(self):
        proceso, cand, post = _contexto(
            self.empresa, "BATCH", req_ent=False, req_eval=False, req_val=False,
            cupos=2, estado=Postulacion.Estado.PRESELECCIONADO,
        )
        p2 = Postulacion.objects.create(
            empresa=self.empresa,
            candidato=Candidato.objects.create(empresa=self.empresa, documento="B2", nombres="B", apellidos="Dos", email="b2@mail.com"),
            proceso_seleccion=proceso, estado=Postulacion.Estado.PRESELECCIONADO,
        )
        p3 = Postulacion.objects.create(
            empresa=self.empresa,
            candidato=Candidato.objects.create(empresa=self.empresa, documento="B3", nombres="B", apellidos="Tres", email="b3@mail.com"),
            proceso_seleccion=proceso, estado=Postulacion.Estado.PRESELECCIONADO,
        )
        with patch("apps.reclutamiento.services.notificaciones._enviar") as send, \
                self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                "/api/reclutamiento/postulaciones/seleccionar-masivo/",
                {"postulacion_ids": [str(post.id), str(p2.id)]},
                format="json",
            )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        post.refresh_from_db(); p2.refresh_from_db(); p3.refresh_from_db()
        self.assertEqual(post.estado, Postulacion.Estado.SELECCIONADO)
        self.assertEqual(p2.estado, Postulacion.Estado.SELECCIONADO)
        self.assertEqual(p3.estado, Postulacion.Estado.NO_SELECCIONADO)
        proceso.vacante.refresh_from_db()
        self.assertEqual(proceso.vacante.numero_seleccionados, 2)

    def test_exportar_historico_formatos(self):
        _contexto(self.empresa, "EXP", req_ent=False, req_eval=False, req_val=False)
        for fmt, ctype in [
            ("csv", "text/csv"),
            ("xlsx", "application/vnd.openxmlformats"),
            ("pdf", "application/pdf"),
        ]:
            res = self.client.get(f"/api/reclutamiento/postulaciones/historico/exportar/?formato={fmt}")
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertIn(ctype, res["Content-Type"])
