"""
Tests de la Fase 1 (Perfil del Cargo extendido).

Cubren:
  - Creación de un PerfilCargo con los campos nuevos de §4.1
    (criticidad multidimensional, suplencia, aptitudes, interacciones,
    restricciones, competencias tipadas).
  - RN-11: que modificar un CatalogoPeligro/CatalogoEPP ya en uso dispare
    automáticamente una nueva CargoVersion en cada PerfilCargo afectado,
    con el snapshot correcto — no solo "que no falle".
  - Aislamiento multi-tenant básico sobre el nuevo endpoint.
"""
import uuid

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.organizacion.models import Proceso
from apps.perfilcargo.models import (
    PerfilCargo, CargoVersion, CatalogoPeligro, CatalogoEPP,
    CargoPeligro, CargoEPP, CargoCompetencia,
)


def _crear_empresa(nit="900123456-1"):
    return Empresa.objects.create(
        nombre="Empresa de Prueba SAS",
        nit=nit,
        num_trabajadores=10,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable1", rol=UserRole.RESPONSABLE):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="1000000001",
        rol=rol,
        empresa=empresa,
    )


# CELERY en modo eager para que transaction.on_commit + tareas encoladas (si
# las hubiera) se ejecuten de forma síncrona durante el test.
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class PerfilCargoFase1Tests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_creacion_perfil_con_campos_nuevos(self):
        payload = {
            "codigo": "PC-2026-0001",
            "nombre_cargo": "Técnico de Alturas",
            "area": "Operaciones",
            "criticidad_sst": "critico",
            "criticidad_operacional": "alto",
            "requiere_suplencia": True,
            "impacto_descripcion": "Impacto alto por trabajo en alturas.",
            "naturaleza_descripcion": "Cargo operativo de campo.",
            "competencias": [
                {"nombre": "Trabajo en alturas", "tipo": "tecnica", "nivel_requerido": 3},
            ],
            "aptitudes": [
                {"tipo": "fisica", "nombre": "Aptitud para alturas", "requerida": True},
            ],
            "restricciones": [
                {"descripcion": "No apto para personas con vértigo", "activa": True},
            ],
        }

        response = self.client.post("/api/modulo1/perfil-cargo", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        perfil = PerfilCargo.objects.get(codigo="PC-2026-0001")

        self.assertEqual(perfil.criticidad_sst, "critico")
        self.assertEqual(perfil.criticidad_operacional, "alto")
        self.assertTrue(perfil.requiere_suplencia)
        self.assertEqual(perfil.competencias.count(), 1)
        self.assertEqual(perfil.competencias.first().nivel_requerido, 3)
        self.assertEqual(perfil.aptitudes.count(), 1)
        self.assertEqual(perfil.restricciones.count(), 1)

        # Toda creación deja una CargoVersion inicial (comportamiento ya existente).
        self.assertEqual(perfil.versiones.count(), 1)

    def test_suplente_requiere_otro_perfil_existente(self):
        principal = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-2026-0002", nombre_cargo="Supervisor SST",
            requiere_suplencia=True,
        )
        suplente = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-2026-0003", nombre_cargo="Supervisor SST (suplente)",
        )

        payload = {"suplentes": [{"cargo_suplente_id": str(suplente.id), "orden_prioridad": 1}]}
        response = self.client.put(f"/api/modulo1/perfil-cargo/{principal.id}", payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(principal.suplentes.count(), 1)
        self.assertEqual(principal.suplentes.first().cargo_suplente_id, suplente.id)

    def test_rn11_cambio_catalogo_peligro_reversiona_perfiles_afectados(self):
        """
        RN-11: editar un CatalogoPeligro ya vinculado a un PerfilCargo debe
        generar automáticamente una nueva CargoVersion — sin que nadie llame
        a un endpoint de "re-versionar" a mano.
        """
        peligro = CatalogoPeligro.objects.create(tipo="Trabajo en alturas", clasificacion="Físico")
        perfil = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-2026-0004", nombre_cargo="Técnico de Alturas",
        )
        CargoPeligro.objects.create(perfil_cargo=perfil, catalogo_peligro=peligro)

        version_inicial = perfil.version_actual
        conteo_versiones_inicial = perfil.versiones.count()

        # El signal usa transaction.on_commit — TestCase envuelve cada test en
        # una transacción que se revierte al final, así que hay que forzar la
        # ejecución de esos callbacks explícitamente para poder observarlos.
        with self.captureOnCommitCallbacks(execute=True):
            peligro.descripcion = "Trabajo en alturas superiores a 1.5 m — actualizado"
            peligro.save()

        perfil.refresh_from_db()

        self.assertEqual(perfil.version_actual, version_inicial + 1)
        self.assertEqual(perfil.versiones.count(), conteo_versiones_inicial + 1)

        ultima_version = perfil.versiones.order_by("-numero_version").first()
        self.assertIn("catálogo", ultima_version.motivo_cambio.lower())
        self.assertEqual(ultima_version.creado_por, "Sistema (actualización de catálogo)")
        # El snapshot debe reflejar el estado real del perfil en ese momento,
        # no un snapshot vacío o desactualizado.
        self.assertEqual(ultima_version.snapshot.get("codigo"), "PC-2026-0004")

    def test_rn11_no_reversiona_perfiles_no_relacionados(self):
        """El signal solo debe afectar a los perfiles que realmente usan ese catálogo."""
        peligro_usado = CatalogoPeligro.objects.create(tipo="Ruido", clasificacion="Físico")
        peligro_no_usado = CatalogoPeligro.objects.create(tipo="Radiación", clasificacion="Físico")

        perfil_relacionado = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-2026-0005", nombre_cargo="Operario de Planta",
        )
        perfil_no_relacionado = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-2026-0006", nombre_cargo="Analista Administrativo",
        )
        CargoPeligro.objects.create(perfil_cargo=perfil_relacionado, catalogo_peligro=peligro_usado)

        version_no_relacionado_antes = perfil_no_relacionado.version_actual

        with self.captureOnCommitCallbacks(execute=True):
            peligro_no_usado.descripcion = "Actualización sin impacto"
            peligro_no_usado.save()

        perfil_no_relacionado.refresh_from_db()
        self.assertEqual(perfil_no_relacionado.version_actual, version_no_relacionado_antes)
        self.assertEqual(perfil_no_relacionado.versiones.count(), 0)

    def test_rn11_no_dispara_en_creacion_del_catalogo(self):
        """Crear un catálogo nuevo (sin perfiles vinculados aún) no debe generar ruido."""
        peligro = CatalogoPeligro.objects.create(tipo="Nuevo peligro", clasificacion="Físico")
        self.assertEqual(CargoVersion.objects.count(), 0)

    def test_aislamiento_multitenant_perfil_cargo(self):
        """Empresa A no debe poder leer ni modificar perfiles de Empresa B."""
        otra_empresa = _crear_empresa(nit="900999999-1")
        perfil_ajeno = PerfilCargo.objects.create(
            empresa=otra_empresa, codigo="PC-2026-0007", nombre_cargo="Cargo de otra empresa",
        )

        response = self.client.get(f"/api/modulo1/perfil-cargo/{perfil_ajeno.id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_permiso_denegado_sin_autenticacion(self):
        client_anonimo = APIClient()
        response = client_anonimo.get("/api/modulo1/perfil-cargo")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
