from datetime import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import Usuario, UserRole
from apps.empresas.models import Empresa
from apps.perfilcargo.models import PerfilCargo, TipoCargo
from apps.organizacion.models import Proceso
from apps.reclutamiento.models import FuenteReclutamiento, Vacante, ProcesoSeleccion, Postulacion, Candidato
from apps.hbseo.models import Brecha
from apps.michc.constants import determinar_semaforo_y_estado


class Fase3BrechasV02Test(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Test Fase 3",
            nit="900777666-3",
            sector_economico="Transporte",
            nivel_riesgo=4,
            num_trabajadores=20,
        )

        self.user = Usuario.objects.create_user(
            username="responsable_fase3",
            email="responsable@fase3.com",
            password="Password123!",
            first_name="Responsable",
            last_name="Fase 3",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa,
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_perfil_cargo_campos_fase3(self):
        """Verifica los campos jefe_inmediato, tipo_cargo y cargo_critico en PerfilCargo."""
        jefe = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="CARG-001",
            nombre_cargo="Gerente de Operaciones",
            tipo_cargo=TipoCargo.ADMINISTRATIVO,
            cargo_critico=True,
        )

        conductor = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="CARG-002",
            nombre_cargo="Conductor de Vehículo Pesado",
            jefe_inmediato=jefe,
            tipo_cargo=TipoCargo.OPERATIVO,
            cargo_critico=True,
        )

        self.assertEqual(conductor.jefe_inmediato, jefe)
        self.assertEqual(conductor.tipo_cargo, TipoCargo.OPERATIVO)
        self.assertTrue(conductor.cargo_critico)
        self.assertIn(conductor, jefe.subordinados_directos.all())

    def test_exportar_mapa_procesos_pdf(self):
        """Verifica la exportación en PDF del mapa de procesos con logo e identidad."""
        Proceso.objects.create(
            empresa=self.empresa,
            nombre="Gestión Estratégica",
            tipo="estrategico",
        )

        res = self.client.get("/api/modulo0/procesos/exportar-mapa-pdf")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(len(res.content) > 0)

    def test_hbseo_informes_periodo(self):
        """Verifica el endpoint de informes de brechas filtrado por periodo."""
        Brecha.objects.create(
            empresa=self.empresa,
            clasificacion=Brecha.Clasificacion.INCUMPLIMIENTO,
            estado=Brecha.Estado.SUBSANADA,
            descripcion_automatica="Curso de alturas vencido",
        )

        res = self.client.get("/api/hbseo/brechas/informes-periodo/?periodo=trimestral")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("total_brechas", res.data)
        self.assertEqual(res.data["total_brechas"], 1)
        self.assertEqual(res.data["subsanadas"], 1)

    def test_reclutamiento_indicadores_fuente(self):
        """Verifica el embudo de conversión por fuente de reclutamiento."""
        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="CARG-003",
            nombre_cargo="Auxiliar Logístico",
        )
        fuente = FuenteReclutamiento.objects.create(empresa=self.empresa, nombre="SPE SENA")
        vacante = Vacante.objects.create(
            empresa=self.empresa,
            perfil_cargo=perfil,
            titulo="Auxiliar Logístico",
            numero_cupos=2,
        )
        proceso = ProcesoSeleccion.objects.create(empresa=self.empresa, vacante=vacante)
        candidato = Candidato.objects.create(
            empresa=self.empresa,
            nombres="Juan",
            apellidos="Pérez",
            tipo_documento="CC",
            documento="1055443322",
            email="juan.perez@test.com",
            fuente_reclutamiento=fuente,
        )

        Postulacion.objects.create(
            empresa=self.empresa,
            proceso_seleccion=proceso,
            candidato=candidato,
            estado=Postulacion.Estado.SELECCIONADO,
        )

        res = self.client.get("/api/reclutamiento/fuentes/indicadores-efectividad/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res.data) > 0)
        spe_data = next((item for item in res.data if item["fuente_nombre"] == "SPE SENA"), None)
        self.assertIsNotNone(spe_data)
        self.assertEqual(spe_data["candidatos"], 1)
        self.assertEqual(spe_data["contratados"], 1)

    def test_escala_michc_configurable(self):
        """Verifica la semaforización configurable en 3 y 4 tramos."""
        sem3, est3 = determinar_semaforo_y_estado(85.0, modo="3_TRAMOS")
        self.assertEqual(sem3, "amarillo")
        self.assertEqual(est3, "habilitado_con_observaciones")

        sem4, est4 = determinar_semaforo_y_estado(75.0, modo="4_TRAMOS")
        self.assertEqual(sem4, "amarillo")
        self.assertEqual(est4, "habilitacion_condicionada")
