import uuid
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import UserRole
from apps.empresas.models import Empresa
from apps.perfilcargo.models import PerfilCargo
from apps.capacitaciones.models import Trabajador
from apps.formacion.models import (
    CursoFormacion,
    CargoRequisitoFormacion,
    RegistroFormacion,
    poblar_catalogo_formacion_semilla,
)
from apps.formacion.services import calcular_matriz_formacion_trabajador

User = get_user_model()


def _crear_empresa(nit="900123456-1"):
    return Empresa.objects.create(
        nombre="Transportes & Carga S.A.S.",
        nit=nit,
        num_trabajadores=30,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


class Fase2FormacionTests(TestCase):
    def setUp(self):
        self.empresa = _crear_empresa()
        self.empresa_otra = _crear_empresa(nit="900999888-2")
        self.user_gh = User.objects.create_user(
            username="gh_user",
            email="gh@transportes.com",
            password="Password123!",
            empresa=self.empresa,
            rol=UserRole.RESPONSABLE
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user_gh)

    def test_catalogo_formacion_semilla_crea_ocho_cursos(self):
        """El catálogo de arranque por empresa crea los 8 cursos semilla."""
        cursos = poblar_catalogo_formacion_semilla(self.empresa)
        self.assertEqual(len(cursos), 8)
        self.assertEqual(CursoFormacion.objects.filter(empresa=self.empresa).count(), 8)

        nombres = set(CursoFormacion.objects.filter(empresa=self.empresa).values_list("nombre", flat=True))
        self.assertIn("Trabajo seguro en alturas", nombres)
        self.assertIn("Curso SST 50 horas", nombres)
        self.assertIn("Curso SST 20 horas", nombres)
        self.assertIn("Manejo defensivo", nombres)
        self.assertIn("Primeros auxilios", nombres)
        self.assertIn("Brigadas de emergencia", nombres)
        self.assertIn("Auditor interno", nombres)
        self.assertIn("Curso PESV", nombres)

        # Aislamiento multi-empresa
        self.assertEqual(CursoFormacion.objects.filter(empresa=self.empresa_otra).count(), 0)

    def test_requisitos_formacion_y_versionado_de_perfil(self):
        """Los requisitos de formación se guardan con el perfil y versionan el cargo."""
        poblar_catalogo_formacion_semilla(self.empresa)
        curso_alturas = CursoFormacion.objects.get(empresa=self.empresa, nombre="Trabajo seguro en alturas")

        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="OP-001",
            nombre_cargo="Operario de Mantenimiento",
            version_actual=1,
            activo=True
        )

        # Ningún perfil hereda cursos automáticamente
        self.assertEqual(perfil.requisitos_formacion.count(), 0)

        # Crear requisito de formación para este perfil
        req = CargoRequisitoFormacion.objects.create(
            perfil_cargo=perfil,
            curso=curso_alturas,
            obligatorio=True
            # vigencia_meses se hereda automáticamente del curso (12 meses)
        )
        self.assertEqual(req.vigencia_meses, 12)

        # Actualización vía PUT /api/modulo1/perfil-cargo/{id} debe detectar el cambio y versionar
        curso_defensivo = CursoFormacion.objects.get(empresa=self.empresa, nombre="Manejo defensivo")
        payload = {
            "nombre_cargo": "Operario de Mantenimiento",
            "requisitos_formacion": [
                {"curso_id": str(curso_alturas.id), "obligatorio": True, "vigencia_meses": 12},
                {"curso_id": str(curso_defensivo.id), "obligatorio": True, "vigencia_meses": 24},
            ]
        }
        resp = self.client.put(f"/api/modulo1/perfil-cargo/{perfil.id}", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        perfil.refresh_from_db()
        self.assertEqual(perfil.version_actual, 2)
        self.assertEqual(perfil.requisitos_formacion.count(), 2)

    def test_cursos_alternativos_sst_50_y_20_horas(self):
        """
        Decisión de la cliente: Cursos SST 50h y 20h aplican solo cuando se configuran
        en el perfil, y son alternativos (cumplir cualquiera de los dos basta).
        """
        poblar_catalogo_formacion_semilla(self.empresa)
        curso_50h = CursoFormacion.objects.get(empresa=self.empresa, nombre="Curso SST 50 horas")
        curso_20h = CursoFormacion.objects.get(empresa=self.empresa, nombre="Curso SST 20 horas")

        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="SST-001",
            nombre_cargo="Coordinador SST",
            version_actual=1,
            activo=True
        )

        # Configurar ambos cursos bajo el mismo grupo_alternativo
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=perfil,
            curso=curso_50h,
            obligatorio=True,
            grupo_alternativo="sst_responsable"
        )
        CargoRequisitoFormacion.objects.create(
            perfil_cargo=perfil,
            curso=curso_20h,
            obligatorio=True,
            grupo_alternativo="sst_responsable"
        )

        trabajador = Trabajador.objects.create(
            empresa=self.empresa,
            nombre="Laura Gómez",
            documento="55667788",
            perfil_cargo=perfil,
            tipo_vinculacion="dependiente",
            activo=True
        )

        # Caso A: Sin registros de formación -> Faltan (cumplimiento 0%)
        matriz_inicial = calcular_matriz_formacion_trabajador(trabajador)
        self.assertEqual(matriz_inicial["resumen"]["total_exigidos"], 1)  # Agrupado como 1 requisito
        self.assertEqual(matriz_inicial["resumen"]["cumplidos"], 0)
        self.assertEqual(matriz_inicial["resumen"]["porcentaje_cumplimiento"], 0.0)

        # Caso B: Trabajador realiza solo el curso de 20 horas -> Cumple la exigencia del grupo
        RegistroFormacion.objects.create(
            trabajador=trabajador,
            curso=curso_20h,
            fecha_realizacion=date.today(),
            fecha_vencimiento=date.today() + relativedelta(months=36),
            origen="proveedor_externo"
        )

        matriz_con_20h = calcular_matriz_formacion_trabajador(trabajador)
        self.assertEqual(matriz_con_20h["resumen"]["total_exigidos"], 1)
        self.assertEqual(matriz_con_20h["resumen"]["cumplidos"], 1)
        self.assertEqual(matriz_con_20h["resumen"]["porcentaje_cumplimiento"], 100.0)

        # El curso de 50h queda marcado como cubierto por alternativa
        item_50h = next(c for c in matriz_con_20h["cursos"] if c["curso_id"] == str(curso_50h.id))
        self.assertTrue(item_50h["cumple"])
        self.assertTrue(item_50h["alternativa_satisfecha"])
        self.assertEqual(item_50h["alternativa_cubierta_por"], "Curso SST 20 horas")

    def test_matriz_formacion_tres_cursos_obligatorios_vigente_por_vencer_falta(self):
        """
        Criterio de aceptación 'Listo cuando':
        Dado un cargo con tres cursos obligatorios, el sistema muestra por trabajador
        cuáles tiene vigentes, cuáles vencen pronto y cuáles faltan.
        """
        poblar_catalogo_formacion_semilla(self.empresa)
        c_alturas = CursoFormacion.objects.get(empresa=self.empresa, nombre="Trabajo seguro en alturas")
        c_vial = CursoFormacion.objects.get(empresa=self.empresa, nombre="Manejo defensivo")
        c_auxilios = CursoFormacion.objects.get(empresa=self.empresa, nombre="Primeros auxilios")

        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="COND-001",
            nombre_cargo="Conductor de Operaciones Especiales",
            activo=True
        )

        CargoRequisitoFormacion.objects.create(perfil_cargo=perfil, curso=c_alturas, obligatorio=True)
        CargoRequisitoFormacion.objects.create(perfil_cargo=perfil, curso=c_vial, obligatorio=True)
        CargoRequisitoFormacion.objects.create(perfil_cargo=perfil, curso=c_auxilios, obligatorio=True)

        trabajador = Trabajador.objects.create(
            empresa=self.empresa,
            nombre="Carlos Mendoza",
            documento="11223344",
            perfil_cargo=perfil,
            tipo_vinculacion="dependiente",
            activo=True
        )

        today = date.today()

        # 1. Alturas: VIGENTE (vence en 6 meses)
        RegistroFormacion.objects.create(
            trabajador=trabajador,
            curso=c_alturas,
            fecha_realizacion=today - timedelta(days=60),
            fecha_vencimiento=today + timedelta(days=180),
            origen="proveedor_externo"
        )

        # 2. Manejo defensivo: POR VENCER (vence en 15 días, <= 30 días)
        RegistroFormacion.objects.create(
            trabajador=trabajador,
            curso=c_vial,
            fecha_realizacion=today - timedelta(days=700),
            fecha_vencimiento=today + timedelta(days=15),
            origen="capacitacion_interna"
        )

        # 3. Primeros auxilios: NO REALIZADO (FALTA)

        # Consultar matriz vía API
        url = f"/api/formacion/registros/matriz-trabajador/{trabajador.id}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        data = resp.json()
        resumen = data["resumen"]

        self.assertEqual(resumen["total_exigidos"], 3)
        self.assertEqual(resumen["cumplidos"], 2)  # 1 vigente + 1 por vencer
        self.assertEqual(resumen["por_vencer"], 1)
        self.assertEqual(resumen["vencidos"], 0)
        self.assertEqual(resumen["faltantes"], 1)

        # Verificar estados individuales
        cursos_dict = {c["curso_nombre"]: c for c in data["cursos"]}
        self.assertEqual(cursos_dict["Trabajo seguro en alturas"]["estado"], "vigente")
        self.assertEqual(cursos_dict["Manejo defensivo"]["estado"], "por_vencer")
        self.assertEqual(cursos_dict["Primeros auxilios"]["estado"], "falta")

    def test_expediente_trabajador_incluye_formacion(self):
        """El endpoint del expediente consolidado incluye la matriz de formación."""
        perfil = PerfilCargo.objects.create(
            empresa=self.empresa,
            codigo="ADM-001",
            nombre_cargo="Asistente Administrativo",
            activo=True
        )
        trabajador = Trabajador.objects.create(
            empresa=self.empresa,
            nombre="Diana Torres",
            documento="99887766",
            perfil_cargo=perfil,
            tipo_vinculacion="dependiente",
            activo=True
        )

        url = f"/api/gestion-humana/expediente/{trabajador.id}/"
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()

        self.assertIn("formacion", data)
        self.assertEqual(data["formacion"]["trabajador"]["id"], str(trabajador.id))
