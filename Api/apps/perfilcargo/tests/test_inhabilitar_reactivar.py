"""
Inhabilitación/reactivación de Perfil de Cargo:
- Bloquea si hay trabajadores activos, vacantes activas o procesos activos.
- Inhabilitar es soft-delete (no borra histórico).
- Reactivar restaura el perfil; listado con incluir_inactivos.
"""
from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import Vacante, ProcesoSeleccion


class InhabilitarReactivarPerfilTestCase(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Perfil", nit="900810001-1",
            num_trabajadores=10, nivel_riesgo=2, capitulo_vigente="I",
        )
        self.user = Usuario.objects.create_user(
            username="perfil_user", email="perfil@a.com", password="Password123!",
            documento="555000111", rol=UserRole.RESPONSABLE,
            empresa=self.empresa, activo=True, is_active=True,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.perfil = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-TEST-01", nombre_cargo="Auxiliar",
        )

    def _crear_vacante(self, estado=Vacante.Estado.ABIERTA):
        return Vacante.objects.create(
            empresa=self.empresa, perfil_cargo=self.perfil,
            titulo="Vacante de prueba", numero_cupos=1, estado=estado,
        )

    def test_no_inhabilitar_con_vacante_activa(self):
        self._crear_vacante(Vacante.Estado.ABIERTA)
        res = self.client.delete(f"/api/modulo1/perfil-cargo/{self.perfil.id}")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.activo)

    def test_no_inhabilitar_con_proceso_activo(self):
        vacante = self._crear_vacante(Vacante.Estado.CERRADA)
        ProcesoSeleccion.objects.create(empresa=self.empresa, vacante=vacante, estado=ProcesoSeleccion.Estado.ACTIVO)
        res = self.client.delete(f"/api/modulo1/perfil-cargo/{self.perfil.id}")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.activo)

    def test_inhabilitar_reactivar_y_listar_inactivos(self):
        # Sin dependencias activas -> se inhabilita (soft delete)
        res = self.client.delete(f"/api/modulo1/perfil-cargo/{self.perfil.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.perfil.refresh_from_db()
        self.assertFalse(self.perfil.activo)

        # No aparece por defecto
        res_list = self.client.get("/api/modulo1/perfil-cargo")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 0)

        # Sí aparece con incluir_inactivos
        res_all = self.client.get("/api/modulo1/perfil-cargo?incluir_inactivos=true")
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 1)
        self.assertFalse(res_all.data[0]["activo"])

        # Reactivar
        res_re = self.client.post(f"/api/modulo1/perfil-cargo/{self.perfil.id}/reactivar")
        self.assertEqual(res_re.status_code, status.HTTP_200_OK)
        self.perfil.refresh_from_db()
        self.assertTrue(self.perfil.activo)
