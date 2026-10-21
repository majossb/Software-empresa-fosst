from datetime import date
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo, CargoCompetencia
from apps.formacion.models import EvaluacionCompetencia


def _crear_empresa(nit="900888111-2"):
    return Empresa.objects.create(
        nombre="Empresa Evaluaciones SAS",
        nit=nit,
        num_trabajadores=30,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


@override_settings(
    GEMINI_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class EvaluacionRolesFase1Tests(TestCase):
    def setUp(self):
        self.empresa = _crear_empresa()
        self.otra_empresa = _crear_empresa(nit="900888222-3")

        # Cargos: Jefe y Operativo
        self.cargo_jefe = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-JEFE-01",
            nombre_cargo="Supervisor de Operaciones",
        )
        self.cargo_operario = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-OP-01",
            nombre_cargo="Conductor de Distribución",
            jefe_inmediato=self.cargo_jefe,
        )
        self.cargo_otro_equipo = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="PC-OTRO-01",
            nombre_cargo="Auxiliar Administrativo",
            # No reporta al cargo_jefe
        )

        # Competencia en el cargo del operario (Nivel 5)
        self.comp_conduccion = CargoCompetencia.objects.create(
            perfil_cargo=self.cargo_operario,
            nombre="Conducción Defensiva",
            tipo="tecnica",
            nivel_requerido=5,
            nivel="Referente",
            descripcion="Dominio total y referente en conducción segura"
        )

        # Usuarios
        self.usuario_gh = Usuario.objects.create_user(
            username="gestor_gh",
            email="gh@test.com",
            documento="1111111",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa,
        )
        self.usuario_jefe = Usuario.objects.create_user(
            username="jefe_supervisor",
            email="jefe@test.com",
            documento="2222222",
            rol=UserRole.AUDITOR, # Rol no-GH para asegurar que evalúa como jefe
            empresa=self.empresa,
        )
        self.usuario_otro = Usuario.objects.create_user(
            username="otro_empleado",
            email="otro@test.com",
            documento="3333333",
            rol=UserRole.AUDITOR,
            empresa=self.empresa,
        )
        self.usuario_otra_empresa = Usuario.objects.create_user(
            username="jefe_otra_empresa",
            email="ajeno@test.com",
            documento="4444444",
            rol=UserRole.RESPONSABLE,
            empresa=self.otra_empresa,
        )

        # Trabajadores vinculados
        self.trabajador_jefe = Trabajador.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo_jefe,
            nombre="Carlos Jefe",
            documento="2222222",
            usuario=self.usuario_jefe,
            tipo_vinculacion="dependiente",
        )
        self.trabajador_subordinado = Trabajador.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo_operario,
            nombre="Pedro Operario",
            documento="5555555",
            tipo_vinculacion="dependiente",
        )
        self.trabajador_otro_equipo = Trabajador.objects.create(
            empresa=self.empresa,
            perfil_cargo=self.cargo_otro_equipo,
            nombre="Laura Administrativa",
            documento="6666666",
            tipo_vinculacion="dependiente",
        )

    def test_gestion_humana_puede_evaluar_a_cualquier_trabajador_con_nivel_5(self):
        """Gestión Humana puede evaluar a cualquier trabajador y se registra rol 'gestion_humana'."""
        client = APIClient()
        client.force_authenticate(user=self.usuario_gh)

        payload = {
            "trabajador": str(self.trabajador_subordinado.id),
            "cargo_competencia": str(self.comp_conduccion.id),
            "nivel_alcanzado": 5,
            "metodo": "observacion_directa",
            "fecha_evaluacion": str(date.today()),
        }

        res = client.post("/api/formacion/evaluaciones/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["nivel_alcanzado"], 5)
        self.assertEqual(res.data["nivel_alcanzado_nombre"], "Referente")
        self.assertEqual(res.data["rol_evaluador"], "gestion_humana")
        self.assertEqual(res.data["brecha_calculada"], 0)

    def test_jefe_inmediato_puede_evaluar_a_su_subordinado(self):
        """El jefe inmediato puede evaluar a su trabajador directo y se registra 'jefe_inmediato'."""
        client = APIClient()
        client.force_authenticate(user=self.usuario_jefe)

        payload = {
            "trabajador": str(self.trabajador_subordinado.id),
            "cargo_competencia": str(self.comp_conduccion.id),
            "nivel_alcanzado": 4,
            "metodo": "evaluacion_360",
            "fecha_evaluacion": str(date.today()),
        }

        res = client.post("/api/formacion/evaluaciones/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["rol_evaluador"], "jefe_inmediato")
        self.assertEqual(res.data["brecha_calculada"], 1) # Req 5 - Alc 4 = 1

    def test_jefe_inmediato_no_puede_evaluar_a_trabajador_de_otro_equipo(self):
        """Un jefe no puede evaluar a trabajadores que no reportan a su cargo."""
        client = APIClient()
        client.force_authenticate(user=self.usuario_jefe)

        # Crear una competencia en el otro cargo
        comp_admin = CargoCompetencia.objects.create(
            perfil_cargo=self.cargo_otro_equipo,
            nombre="Gestión Documental",
            nivel_requerido=3,
        )

        payload = {
            "trabajador": str(self.trabajador_otro_equipo.id),
            "cargo_competencia": str(comp_admin.id),
            "nivel_alcanzado": 3,
            "metodo": "evaluacion_360",
            "fecha_evaluacion": str(date.today()),
        }

        res = client.post("/api/formacion/evaluaciones/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_usuario_de_otra_empresa_no_puede_evaluar(self):
        """Un usuario de otra empresa no puede evaluar a este trabajador."""
        client = APIClient()
        client.force_authenticate(user=self.usuario_otra_empresa)

        payload = {
            "trabajador": str(self.trabajador_subordinado.id),
            "cargo_competencia": str(self.comp_conduccion.id),
            "nivel_alcanzado": 3,
            "metodo": "evaluacion_360",
            "fecha_evaluacion": str(date.today()),
        }

        res = client.post("/api/formacion/evaluaciones/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_nadie_se_evalua_a_si_mismo_salvo_metodo_autoevaluacion(self):
        """Si un usuario intenta evaluarse a sí mismo sin método autoevaluacion, se rechaza."""
        usuario_operario = Usuario.objects.create_user(
            username="pedro_op",
            email="pedro@test.com",
            documento="5555555", # mismo documento que trabajador_subordinado
            empresa=self.empresa,
        )
        self.trabajador_subordinado.usuario = usuario_operario
        self.trabajador_subordinado.save()

        client = APIClient()
        client.force_authenticate(user=usuario_operario)

        # Intento con evaluacion_360 (debe fallar)
        res_fallido = client.post("/api/formacion/evaluaciones/", {
            "trabajador": str(self.trabajador_subordinado.id),
            "cargo_competencia": str(self.comp_conduccion.id),
            "nivel_alcanzado": 5,
            "metodo": "evaluacion_360",
            "fecha_evaluacion": str(date.today()),
        }, format="json")
        self.assertEqual(res_fallido.status_code, status.HTTP_400_BAD_REQUEST)

        # Con autoevaluacion (debe tener éxito)
        res_ok = client.post("/api/formacion/evaluaciones/", {
            "trabajador": str(self.trabajador_subordinado.id),
            "cargo_competencia": str(self.comp_conduccion.id),
            "nivel_alcanzado": 5,
            "metodo": "autoevaluacion",
            "fecha_evaluacion": str(date.today()),
        }, format="json")
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ok.data["rol_evaluador"], "autoevaluacion")

    def test_autoevaluacion_no_cuenta_como_cumplimiento_por_si_sola(self):
        """En matriz-trabajador, una autoevaluación aunque alcance o supere el nivel requerido no marca 'cumple=True'."""
        EvaluacionCompetencia.objects.create(
            trabajador=self.trabajador_subordinado,
            cargo_competencia=self.comp_conduccion,
            nivel_alcanzado=5, # supera o iguala requerido 5
            metodo="autoevaluacion",
            rol_evaluador="autoevaluacion",
            fecha_evaluacion=date.today(),
            evaluado_por=self.usuario_gh,
        )

        client = APIClient()
        client.force_authenticate(user=self.usuario_gh)

        res = client.get(f"/api/formacion/evaluaciones/matriz-trabajador/{self.trabajador_subordinado.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        comp = res.data["competencias"][0]
        self.assertFalse(comp["cumple"])
        self.assertTrue(comp["solo_autoevaluado"])
