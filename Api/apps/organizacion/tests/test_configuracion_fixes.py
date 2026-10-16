from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.organizacion.models import NodoOrganigrama, Proceso, Sede


class ConfiguracionFixesTest(TestCase):
    """Pruebas de las correcciones de la auditoría de la sección Configuración."""

    def setUp(self):
        self.client = APIClient()

        self.empresa_a = Empresa.objects.create(
            nombre="Empresa Alpha S.A.S.", nit="900111222",
            num_trabajadores=15, nivel_riesgo=3, capitulo_vigente="II",
            estado=Empresa.Estado.ACTIVA,
        )
        self.empresa_b = Empresa.objects.create(
            nombre="Empresa Beta S.A.S.", nit="900333444",
            num_trabajadores=5, nivel_riesgo=1, capitulo_vigente="I",
            estado=Empresa.Estado.ACTIVA,
        )

        self.resp_a = Usuario.objects.create_user(
            username="resp_a", email="resp.a@a.com", password="Password123!",
            rol=UserRole.RESPONSABLE, empresa=self.empresa_a, activo=True, is_active=True,
        )
        self.auditor_a = Usuario.objects.create_user(
            username="aud_a", email="aud.a@a.com", password="Password123!",
            rol=UserRole.AUDITOR, empresa=self.empresa_a, activo=True, is_active=True,
        )
        self.resp_b = Usuario.objects.create_user(
            username="resp_b", email="resp.b@b.com", password="Password123!",
            rol=UserRole.RESPONSABLE, empresa=self.empresa_b, activo=True, is_active=True,
        )

        self.sede_a1 = Sede.objects.create(
            empresa=self.empresa_a, nombre="Sede Principal", ciudad="Bogotá",
            es_principal=True, activa=True,
        )
        self.sede_a2 = Sede.objects.create(
            empresa=self.empresa_a, nombre="Sede Norte", ciudad="Bogotá",
            es_principal=False, activa=True,
        )

        Trabajador.objects.create(
            empresa=self.empresa_a, sede=self.sede_a1,
            nombre="Ana Trabajadora", documento="1001", tipo_vinculacion="dependiente",
        )

        self.nodo_padre = NodoOrganigrama.objects.create(
            empresa=self.empresa_a, nombre_cargo="Gerente", nivel=1, orden=0, activo=True,
        )
        self.nodo_hijo = NodoOrganigrama.objects.create(
            empresa=self.empresa_a, nombre_cargo="Jefe", nivel=2,
            padre=self.nodo_padre, orden=0, activo=True,
        )

        self.proceso_padre = Proceso.objects.create(
            empresa=self.empresa_a, nombre="Proceso Principal", tipo="estrategico", activo=True,
        )
        self.subproceso = Proceso.objects.create(
            empresa=self.empresa_a, nombre="Subproceso", tipo="estrategico",
            padre=self.proceso_padre, activo=True,
        )
        self.proceso_b = Proceso.objects.create(
            empresa=self.empresa_b, nombre="Proceso Beta", tipo="estrategico", activo=True,
        )

    # ── F1.2 Sede._count ─────────────────────────────────────────
    def test_sede_count_trabajadores(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.get("/api/modulo0/sedes")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        por_id = {s["id"]: s for s in res.data}
        self.assertEqual(por_id[str(self.sede_a1.id)]["_count"]["trabajadores"], 1)
        self.assertEqual(por_id[str(self.sede_a2.id)]["_count"]["trabajadores"], 0)

    # ── F2.12 exclusividad de sede principal ─────────────────────
    def test_sede_principal_es_exclusiva(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.put(
            f"/api/modulo0/sedes/{self.sede_a2.id}",
            {"nombre": "Sede Norte", "ciudad": "Bogotá", "es_principal": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.sede_a1.refresh_from_db()
        self.sede_a2.refresh_from_db()
        self.assertFalse(self.sede_a1.es_principal)
        self.assertTrue(self.sede_a2.es_principal)

    # ── F2.12 guards de borrado ──────────────────────────────────
    def test_no_borrar_sede_con_trabajadores(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.delete(f"/api/modulo0/sedes/{self.sede_a1.id}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "SEDE_CON_TRABAJADORES")

    def test_no_borrar_nodo_con_hijos(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.delete(f"/api/modulo0/organigrama/{self.nodo_padre.id}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "NODO_CON_HIJOS")

    def test_no_borrar_proceso_con_subprocesos(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.delete(f"/api/modulo0/procesos/{self.proceso_padre.id}")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data.get("code"), "PROCESO_CON_SUBPROCESOS")

    # ── F2.7 permisos por rol ────────────────────────────────────
    def test_auditor_no_puede_escribir_sede(self):
        self.client.force_authenticate(user=self.auditor_a)
        res = self.client.post(
            "/api/modulo0/sedes",
            {"nombre": "Sede Auditor", "ciudad": "Cali"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_responsable_puede_crear_sede(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.post(
            "/api/modulo0/sedes",
            {"nombre": "Sede Nueva", "ciudad": "Medellín"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # ── F2.8 scoping de padre_id ─────────────────────────────────
    def test_padre_de_otra_empresa_rechazado(self):
        self.client.force_authenticate(user=self.resp_a)
        res = self.client.post(
            "/api/modulo0/procesos",
            {
                "nombre": "Proceso Cruzado",
                "tipo": "estrategico",
                "padre_id": str(self.proceso_b.id),
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
