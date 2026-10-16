"""
Fase F — Correcciones de seguridad/estabilidad del módulo de Reclutamiento.

Cubre:
- RN-R02: preselección con requisitos obligatorios tipo string (antes: 500).
- Autenticación del portal: un token ya usado no debe autenticar.
- RN-R10: un sub-recurso (entrevista) no puede enlazarse a una postulación de otra empresa.
"""
import tempfile

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import (
    Candidato,
    CandidatoDocumento,
    Vacante,
    ProcesoSeleccion,
    Postulacion,
)

TEMP_MEDIA_DIR = tempfile.mkdtemp()
from apps.reclutamiento.services.postulacion import preseleccionar_candidato
from apps.reclutamiento.services.transiciones import RequisitoIncumplidoError
from apps.reclutamiento.services.portal import generar_token_acceso_candidato


def _crear_empresa(nit, nombre):
    return Empresa.objects.create(
        nit=nit, nombre=nombre, num_trabajadores=10, nivel_riesgo=2, capitulo_vigente="I",
    )


def _crear_contexto_postulacion(empresa, sufijo, requisitos=None, estado=Postulacion.Estado.POSTULADO):
    sede = Sede.objects.create(empresa=empresa, nombre=f"Sede {sufijo}", ciudad="Bogotá")
    cargo = PerfilCargo.objects.create(empresa=empresa, codigo=f"PC-{sufijo}", nombre_cargo=f"Cargo {sufijo}")
    vacante = Vacante.objects.create(
        empresa=empresa, perfil_cargo=cargo, sede=sede, titulo=f"Vacante {sufijo}", numero_cupos=1,
    )
    proceso = ProcesoSeleccion.objects.create(
        empresa=empresa, vacante=vacante, requisitos_obligatorios=requisitos or [],
    )
    candidato = Candidato.objects.create(
        empresa=empresa, documento=f"DOC{sufijo}", nombres="Ana", apellidos="Prueba",
        email=f"ana.{sufijo}@mail.com",
    )
    postulacion = Postulacion.objects.create(
        empresa=empresa, candidato=candidato, proceso_seleccion=proceso, estado=estado,
    )
    return postulacion


class FaseFSeguridadTestCase(APITestCase):
    def setUp(self):
        self.empresa_a = _crear_empresa("900000001-1", "Empresa A")
        self.empresa_b = _crear_empresa("900000002-2", "Empresa B")
        self.user_a = Usuario.objects.create_user(
            username="resp_a", email="resp.a@a.com", password="Password123!",
            rol=UserRole.RESPONSABLE, empresa=self.empresa_a, activo=True, is_active=True,
        )
        self.client = APIClient()

    # ── RN-R02: requisitos tipo string no deben romper con 500 ────
    def test_preseleccion_requisitos_string_cumplidos(self):
        postulacion = _crear_contexto_postulacion(
            self.empresa_a, "A1", requisitos=["Licencia vigente", "Certificado alturas"],
        )
        preseleccionar_candidato(
            postulacion=postulacion,
            calificacion_requisitos={
                "Licencia vigente": {"cumple": True},
                "Certificado alturas": {"cumple": True},
            },
            usuario=self.user_a,
        )
        postulacion.refresh_from_db()
        self.assertEqual(postulacion.estado, Postulacion.Estado.PRESELECCIONADO)

    def test_preseleccion_requisitos_string_incumplidos_levanta_error_controlado(self):
        postulacion = _crear_contexto_postulacion(
            self.empresa_a, "A2", requisitos=["Licencia vigente"],
        )
        with self.assertRaises(RequisitoIncumplidoError):
            preseleccionar_candidato(
                postulacion=postulacion,
                calificacion_requisitos={"Licencia vigente": {"cumple": False}},
                usuario=self.user_a,
            )

    # ── Token usado no debe autenticar ────────────────────────────
    def test_token_usado_no_autentica(self):
        candidato = Candidato.objects.create(
            empresa=self.empresa_a, documento="TOK1", nombres="Luis", apellidos="Token",
            email="luis.token@mail.com",
        )
        token = generar_token_acceso_candidato(candidato=candidato)
        token.usado = True
        token.save(update_fields=["usado"])

        res = self.client.get(
            "/api/reclutamiento/portal/mis-postulaciones/",
            HTTP_AUTHORIZATION=f"Bearer {token.token}",
        )
        self.assertIn(res.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    # ── RN-R10: sub-recurso no cruza empresas ─────────────────────
    def test_entrevista_cross_tenant_rechazada(self):
        postulacion_b = _crear_contexto_postulacion(self.empresa_b, "B1")
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(
            "/api/reclutamiento/entrevistas/",
            {
                "postulacion": str(postulacion_b.id),
                "tipo_entrevista": "inicial_rh",
                "modalidad": "virtual",
                "fecha_programada": timezone.now().isoformat(),
                "concepto": "pendiente",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_entrevista_misma_empresa_ok(self):
        postulacion_a = _crear_contexto_postulacion(self.empresa_a, "A3")
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(
            "/api/reclutamiento/entrevistas/",
            {
                "postulacion": str(postulacion_a.id),
                "tipo_entrevista": "inicial_rh",
                "modalidad": "virtual",
                "fecha_programada": timezone.now().isoformat(),
                "concepto": "pendiente",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


def _pdf(nombre="cv.pdf"):
    return SimpleUploadedFile(nombre, b"%PDF-1.4 contenido de prueba", content_type="application/pdf")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_ROOT=TEMP_MEDIA_DIR,
)
class FaseFDocumentoUploadTestCase(APITestCase):
    def setUp(self):
        self.empresa_a = _crear_empresa("900000011-1", "Empresa Doc A")
        self.empresa_b = _crear_empresa("900000012-2", "Empresa Doc B")
        self.user_a = Usuario.objects.create_user(
            username="doc_a", email="doc.a@a.com", password="Password123!",
            rol=UserRole.RESPONSABLE, empresa=self.empresa_a, activo=True, is_active=True,
        )
        self.cand_a = Candidato.objects.create(
            empresa=self.empresa_a, documento="D1", nombres="A", apellidos="Uno", email="a.uno@mail.com",
        )
        self.cand_b = Candidato.objects.create(
            empresa=self.empresa_b, documento="D2", nombres="B", apellidos="Dos", email="b.dos@mail.com",
        )
        self.client = APIClient()

    def test_subir_documento_ok_guarda_hash(self):
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(
            f"/api/reclutamiento/candidatos/{self.cand_a.id}/subir-documento/",
            {"archivo": _pdf(), "tipo_documento": "hoja_de_vida"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc = CandidatoDocumento.objects.get(candidato=self.cand_a)
        self.assertTrue(doc.archivo.sha256_hash)
        self.assertEqual(doc.archivo.tipo_mime, "application/pdf")

    def test_subir_documento_mime_invalido(self):
        self.client.force_authenticate(user=self.user_a)
        archivo = SimpleUploadedFile("nota.txt", b"texto plano", content_type="text/plain")
        res = self.client.post(
            f"/api/reclutamiento/candidatos/{self.cand_a.id}/subir-documento/",
            {"archivo": archivo, "tipo_documento": "otro"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_subir_documento_cross_tenant_404(self):
        self.client.force_authenticate(user=self.user_a)
        res = self.client.post(
            f"/api/reclutamiento/candidatos/{self.cand_b.id}/subir-documento/",
            {"archivo": _pdf(), "tipo_documento": "hoja_de_vida"},
            format="multipart",
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
