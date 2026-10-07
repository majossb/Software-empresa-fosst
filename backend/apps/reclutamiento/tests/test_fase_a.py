from datetime import timedelta
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    FuenteReclutamiento,
    Candidato,
    PerfilCandidato,
    Vacante,
    ProcesoSeleccion,
    TokenAccesoCandidato,
)


class FaseAModelosTestCase(TestCase):
    """
    Tests unitarios para la Fase A de Reclutamiento y Selección.
    Cubre: Aislamiento multi-tenant, no duplicación de candidato y auto-códigos.
    """

    def setUp(self):
        self.empresa_a = Empresa.objects.create(
            nit="900111222-1",
            nombre="Empresa A S.A.S.",
            num_trabajadores=25,
            nivel_riesgo=2,
            capitulo_vigente="II",
        )
        self.empresa_b = Empresa.objects.create(
            nit="900333444-2",
            nombre="Empresa B Ltda.",
            num_trabajadores=55,
            nivel_riesgo=4,
            capitulo_vigente="III",
        )
        self.sede_a = Sede.objects.create(
            empresa=self.empresa_a,
            nombre="Sede Principal Bogotá",
            direccion="Calle 100 # 15-20",
            ciudad="Bogotá",
        )
        self.cargo_a = PerfilCargo.objects.create(
            empresa=self.empresa_a,
            codigo="PC-2026-0001",
            nombre_cargo="Analista de Selección",
            nivel_riesgo=1,
        )

    def test_creacion_candidato_y_perfil(self):
        """Verifica que se crea un candidato con su perfil profesional 1:1."""
        candidato = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="1020304050",
            nombres="Carlos",
            apellidos="Pérez Gómez",
            email="carlos.perez@example.com",
            telefono="3001234567",
            autoriza_tratamiento_datos=True,
            fecha_autorizacion_datos=timezone.now(),
        )
        perfil = PerfilCandidato.objects.create(
            candidato=candidato,
            titulo_profesional="Psicólogo Organizacional",
            nivel_educativo=PerfilCandidato.NivelEducativo.UNIVERSITARIO,
            anios_experiencia=3.5,
        )
        self.assertEqual(candidato.nombre_completo, "Carlos Pérez Gómez")
        self.assertEqual(candidato.perfil.titulo_profesional, "Psicólogo Organizacional")
        self.assertEqual(PerfilCandidato.objects.count(), 1)

    def test_no_duplicacion_candidato_misma_empresa(self):
        """RN-R10: No se permite registrar el mismo documento dos veces en la misma empresa."""
        Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="1020304050",
            nombres="Carlos",
            apellidos="Pérez",
            email="carlos.perez@example.com",
        )
        with self.assertRaises(IntegrityError):
            Candidato.objects.create(
                empresa=self.empresa_a,
                tipo_documento=Candidato.TipoDocumento.CC,
                documento="1020304050",
                nombres="Carlos Duplicado",
                apellidos="Pérez",
                email="otro.email@example.com",
            )

    def test_aislamiento_multitenant_mismo_documento_distinta_empresa(self):
        """RN-R10: Un candidato puede existir en el banco de talento de Empresa A y Empresa B sin colisión."""
        cand_a = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="1020304050",
            nombres="Carlos",
            apellidos="Pérez",
            email="carlos.perez@example.com",
        )
        cand_b = Candidato.objects.create(
            empresa=self.empresa_b,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="1020304050",
            nombres="Carlos",
            apellidos="Pérez",
            email="carlos.perez@empresa-b.com",
        )
        self.assertNotEqual(cand_a.id, cand_b.id)
        self.assertEqual(Candidato.objects.filter(empresa=self.empresa_a).count(), 1)
        self.assertEqual(Candidato.objects.filter(empresa=self.empresa_b).count(), 1)

    def test_creacion_vacante_y_proceso_autocodigos(self):
        """Verifica generación automática de códigos VAC-YYYY-NNNN y PROC-YYYY-NNNN."""
        vacante = Vacante.objects.create(
            empresa=self.empresa_a,
            perfil_cargo=self.cargo_a,
            sede=self.sede_a,
            titulo="Convocatoria Analista SST",
            numero_cupos=2,
            estado=Vacante.Estado.ABIERTA,
        )
        proceso = ProcesoSeleccion.objects.create(
            empresa=self.empresa_a,
            vacante=vacante,
            requiere_entrevista=True,
            requiere_evaluacion=True,
            requiere_validacion_documental=True,
        )
        self.assertTrue(vacante.codigo.startswith("VAC-"))
        self.assertTrue(proceso.codigo.startswith("PROC-"))
        self.assertEqual(vacante.proceso_seleccion, proceso)

    def test_token_acceso_candidato_vigencia(self):
        """Verifica la lógica de expiración del token passwordless (Opción A)."""
        candidato = Candidato.objects.create(
            empresa=self.empresa_a,
            tipo_documento=Candidato.TipoDocumento.CC,
            documento="99887766",
            nombres="Laura",
            apellidos="Mendoza",
            email="laura@example.com",
        )
        token_activo = TokenAccesoCandidato.objects.create(
            candidato=candidato,
            token="token_secreto_valido_12345",
            codigo_otp="654321",
            expira_en=timezone.now() + timedelta(minutes=15),
        )
        token_expirado = TokenAccesoCandidato.objects.create(
            candidato=candidato,
            token="token_secreto_expirado_99999",
            codigo_otp="111222",
            expira_en=timezone.now() - timedelta(minutes=1),
        )
        self.assertTrue(token_activo.esta_vigente())
        self.assertFalse(token_expirado.esta_vigente())
