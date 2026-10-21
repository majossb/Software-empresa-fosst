import json
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia, CargoVersion


def _crear_empresa(nit="900999111-1"):
    return Empresa.objects.create(
        nombre="Empresa Test Perfil SAS",
        nit=nit,
        num_trabajadores=20,
        nivel_riesgo=2,
        capitulo_vigente="I",
    )


def _crear_usuario(empresa, username="responsable_perfil"):
    return Usuario.objects.create_user(
        username=username,
        password="clave-segura-123",
        email=f"{username}@test.com",
        documento="200000001",
        rol=UserRole.RESPONSABLE,
        empresa=empresa,
    )


@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class PerfilCompetenciasFase1Tests(TestCase):
    def setUp(self):
        self.empresa = _crear_empresa()
        self.usuario = _crear_usuario(self.empresa)
        self.client = APIClient()
        self.client.force_authenticate(user=self.usuario)

    def test_crear_perfil_con_competencias_tres_tipos_nivel_5_y_descripcion(self):
        """
        Verifica que se puede crear un perfil con competencias técnicas, conductuales y organizacionales,
        incluyendo nivel 5 (Referente) y descripciones detalladas.
        """
        payload = {
            "codigo": "PC-EXP-01",
            "nombre_cargo": "Especialista en Seguridad Vial",
            "educacion": "Profesional en Ingeniería / Transporte",
            "experiencia": "3 años",
            "tipo_cargo": "operativo",
            "competencias": [
                {
                    "nombre": "Conducción defensiva avanzada",
                    "tipo": "tecnica",
                    "nivel_requerido": 5,
                    "descripcion": "Referente institucional en técnicas de manejo evasivo y defensivo"
                },
                {
                    "nombre": "Comunicación asertiva en crisis",
                    "tipo": "conductual",
                    "nivel_requerido": 4,
                    "descripcion": "Capacidad de liderar y comunicar con calma bajo incidentes"
                },
                {
                    "nombre": "Cultura de seguridad vial",
                    "tipo": "organizacional",
                    "nivel_requerido": 5,
                    "descripcion": "Promotor activo de los valores y normas del PESV"
                }
            ]
        }

        res = self.client.post("/api/modulo1/perfil-cargo", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        perfil_id = res.data["id"]

        perfil = PerfilCargo.objects.get(id=perfil_id)
        comps = perfil.competencias.all()
        self.assertEqual(comps.count(), 3)

        comp_tecnica = comps.get(nombre="Conducción defensiva avanzada")
        self.assertEqual(comp_tecnica.tipo, "tecnica")
        self.assertEqual(comp_tecnica.nivel_requerido, 5)
        self.assertEqual(comp_tecnica.nivel, "Referente")
        self.assertIn("Referente institucional", comp_tecnica.descripcion)

        comp_conductual = comps.get(nombre="Comunicación asertiva en crisis")
        self.assertEqual(comp_conductual.tipo, "blanda")
        self.assertEqual(comp_conductual.nivel_requerido, 4)
        self.assertEqual(comp_conductual.nivel, "Dominio avanzado")

        comp_org = comps.get(nombre="Cultura de seguridad vial")
        self.assertEqual(comp_org.tipo, "organizacional")
        self.assertEqual(comp_org.nivel_requerido, 5)

    def test_cambio_de_competencias_incrementa_version_y_registra_snapshot(self):
        """
        Modificar las competencias de un perfil existente constituye un cambio sustancial:
        debe incrementar la versión del perfil y generar un CargoVersion snapshot.
        """
        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-VERS-01",
            nombre_cargo="Analista SST",
            version_actual=1
        )
        CargoCompetencia.objects.create(
            perfil_cargo=perfil,
            nombre="Inspecciones",
            tipo="tecnica",
            nivel_requerido=2,
            nivel="En desarrollo"
        )

        update_payload = {
            "nombre_cargo": "Analista SST Senior",
            "competencias": [
                {
                    "nombre": "Inspecciones",
                    "tipo": "tecnica",
                    "nivel_requerido": 4, # Cambio sustancial de nivel 2 a 4
                    "descripcion": "Inspecciones técnicas de alta complejidad"
                }
            ]
        }

        res = self.client.put(f"/api/modulo1/perfil-cargo/{perfil.id}", update_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        perfil.refresh_from_db()
        self.assertEqual(perfil.version_actual, 2)

        # Debe existir un CargoVersion con la versión 2
        version_snap = CargoVersion.objects.filter(perfil_cargo=perfil, numero_version=2).first()
        self.assertIsNotNone(version_snap)
