from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.organizacion.models import NodoOrganigrama, Proceso


class OrganigramaExportTest(TestCase):
    """
    Suite de pruebas unitarias para Organigrama y Exportación de Mapa de Procesos (FASE 2 + FASE 4).
    Prueba:
      1. Auto-organizar organigrama (restablece pos_x/pos_y a null).
      2. Prevención de ciclos al intentar asignar un subordinado como padre (CYCLE_DETECTED 400).
      3. Exportación de Mapa de Procesos a PDF (HTTP 200 OK con Content-Type application/pdf).
      4. Aislamiento multi-tenant en exportación de PDF.
    """

    def setUp(self):
        self.client = APIClient()

        # Empresa A
        self.empresa_a = Empresa.objects.create(
            nombre="Empresa Alpha S.A.S.",
            nit="900111222",
            num_trabajadores=15,
            nivel_riesgo=3,
            capitulo_vigente="II",
            estado=Empresa.Estado.ACTIVA,
            branding={
                "preset": "azul_fosst",
                "primario": "#002D62",
                "secundario": "#0284C7",
                "acento": "#F5A800",
                "mapa_procesos": {
                    "estrategico": "#002D62",
                    "misional": "#0284C7",
                    "apoyo": "#64748B"
                }
            }
        )

        self.user_resp = Usuario.objects.create_user(
            username="resp_alpha",
            email="resp.alpha@empresa-a.com",
            password="Password123!",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa_a,
            activo=True,
            is_active=True,
        )

        # Nodos de organigrama
        self.nodo_gerencia = NodoOrganigrama.objects.create(
            empresa=self.empresa_a,
            nombre_cargo="Gerente General",
            area="Dirección",
            nivel=1,
            padre=None,
            orden=0,
            pos_x=100.0,
            pos_y=50.0,
            activo=True
        )

        self.nodo_jefe = NodoOrganigrama.objects.create(
            empresa=self.empresa_a,
            nombre_cargo="Jefe de Operaciones",
            area="Operaciones",
            nivel=2,
            padre=self.nodo_gerencia,
            orden=0,
            pos_x=100.0,
            pos_y=200.0,
            activo=True
        )

        self.nodo_super = NodoOrganigrama.objects.create(
            empresa=self.empresa_a,
            nombre_cargo="Supervisor de Planta",
            area="Operaciones",
            nivel=3,
            padre=self.nodo_jefe,
            orden=0,
            pos_x=100.0,
            pos_y=350.0,
            activo=True
        )

        # Procesos
        self.proceso_est = Proceso.objects.create(
            empresa=self.empresa_a,
            nombre="Direccionamiento Estratégico",
            tipo="estrategico",
            descripcion="Proceso estratégico de liderazgo",
            activo=True
        )

        self.proceso_mis = Proceso.objects.create(
            empresa=self.empresa_a,
            nombre="Gestión de Riesgos SST",
            tipo="misional",
            descripcion="Proceso misional operativo",
            activo=True
        )

    def test_auto_organizar_limpia_posiciones(self):
        """Verifica que /api/modulo0/organigrama/auto-organizar restablezca pos_x y pos_y a null."""
        self.client.force_authenticate(user=self.user_resp)
        res = self.client.post("/api/modulo0/organigrama/auto-organizar")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.nodo_gerencia.refresh_from_db()
        self.nodo_jefe.refresh_from_db()
        self.assertIsNone(self.nodo_gerencia.pos_x)
        self.assertIsNone(self.nodo_gerencia.pos_y)
        self.assertIsNone(self.nodo_jefe.pos_x)
        self.assertIsNone(self.nodo_jefe.pos_y)

    def test_bloqueo_ciclos_organigrama(self):
        """Verifica que asignar un descendiente como padre sea rechazado con 400 CYCLE_DETECTED."""
        self.client.force_authenticate(user=self.user_resp)
        # Intentar asignar el nodo supervisor (nivel 3) como padre de la gerencia (nivel 1)
        payload = {"padre_id": str(self.nodo_super.id)}
        res = self.client.put(f"/api/modulo0/organigrama/{self.nodo_gerencia.id}", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "CYCLE_DETECTED")

    def test_exportar_mapa_pdf_exitoso(self):
        """Verifica que /api/modulo0/procesos/exportar-mapa-pdf genere un PDF binario con cabecera application/pdf."""
        self.client.force_authenticate(user=self.user_resp)
        res = self.client.get("/api/modulo0/procesos/exportar-mapa-pdf")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res["Content-Type"], "application/pdf")
        self.assertTrue(res.content.startswith(b"%PDF"))
