"""
Informe gerencial por vacante:
- Métricas agregadas y sin PII.
- Endpoint JSON y PDF.
- Permisos (solo responsable/admin).
"""
import json

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Candidato, PerfilCandidato, FuenteReclutamiento, Vacante,
    ProcesoSeleccion, Postulacion, Entrevista, Evaluacion,
)
from apps.reclutamiento.services.informe_gerencial import construir_metricas


@override_settings(GEMINI_API_KEY="")
class InformeGerencialTestCase(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Informe", nit="900840001-1",
            num_trabajadores=20, nivel_riesgo=2, capitulo_vigente="I",
        )
        self.user = Usuario.objects.create_user(
            username="inf_user", email="inf@a.com", password="Password123!",
            documento="777000111", rol=UserRole.RESPONSABLE,
            empresa=self.empresa, activo=True, is_active=True,
        )
        self.auditor = Usuario.objects.create_user(
            username="inf_aud", email="aud@a.com", password="Password123!",
            documento="777000222", rol=UserRole.AUDITOR,
            empresa=self.empresa, activo=True, is_active=True,
        )
        cargo = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-INF", nombre_cargo="Auxiliar",
        )
        self.vacante = Vacante.objects.create(
            empresa=self.empresa, perfil_cargo=cargo, titulo="Auxiliar",
            numero_cupos=2, estado=Vacante.Estado.ABIERTA,
        )
        self.proceso = ProcesoSeleccion.objects.create(
            empresa=self.empresa, vacante=self.vacante,
            documentos_requeridos=["hoja_de_vida"],
        )
        self.fuente = FuenteReclutamiento.objects.create(empresa=self.empresa, nombre="LinkedIn")

        estados = [
            Postulacion.Estado.POSTULADO,
            Postulacion.Estado.PRESELECCIONADO,
            Postulacion.Estado.EN_ENTREVISTA,
            Postulacion.Estado.SELECCIONADO,
        ]
        self.postulaciones = []
        for i, estado in enumerate(estados):
            candidato = Candidato.objects.create(
                empresa=self.empresa, documento=f"90000{i}", nombres=f"Cand{i}",
                apellidos="Prueba", email=f"cand{i}@mail.com", ciudad="Bogotá",
                fuente_reclutamiento=self.fuente,
            )
            PerfilCandidato.objects.create(
                candidato=candidato, nivel_educativo="universitario",
                anios_experiencia=2 + i, competencias=["Trabajo en equipo", "Excel"],
            )
            post = Postulacion.objects.create(
                empresa=self.empresa, candidato=candidato,
                proceso_seleccion=self.proceso, estado=estado,
            )
            self.postulaciones.append(post)

        Entrevista.objects.create(
            empresa=self.empresa, postulacion=self.postulaciones[2],
            tipo_entrevista="tecnica", modalidad="virtual",
            fecha_programada=timezone.now(), estado=Entrevista.Estado.REALIZADA,
            concepto=Entrevista.Concepto.FAVORABLE, calificacion=85,
        )
        Evaluacion.objects.create(
            empresa=self.empresa, postulacion=self.postulaciones[2],
            tipo_evaluacion="tecnica", nombre_prueba="Prueba",
            puntaje_obtenido=82, puntaje_maximo=100,
            estado=Evaluacion.Estado.APROBADA,
        )

    def test_metricas_sin_pii(self):
        metricas = construir_metricas(self.empresa, self.vacante)
        texto = json.dumps(metricas, default=str)
        self.assertEqual(metricas["postulaciones"]["total"], 4)
        self.assertNotIn("cand0@mail.com", texto)
        self.assertNotIn("900000", texto)
        self.assertNotIn("Cand0", texto)

    def test_endpoint_informe_json(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(f"/api/reclutamiento/vacantes/{self.vacante.id}/informe-gerencial/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("metricas", res.data)
        self.assertIn("ia", res.data)
        self.assertIn("resumen_ejecutivo", res.data["ia"])
        self.assertIn("confidencialidad", res.data)

    def test_endpoint_informe_pdf(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(f"/api/reclutamiento/vacantes/{self.vacante.id}/informe-gerencial/pdf/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))

    def test_auditor_sin_acceso(self):
        self.client.force_authenticate(user=self.auditor)
        res = self.client.get(f"/api/reclutamiento/vacantes/{self.vacante.id}/informe-gerencial/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
