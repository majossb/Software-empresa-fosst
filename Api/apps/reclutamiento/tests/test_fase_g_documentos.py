"""
Documentos requeridos en la postulación pública:
- Si el proceso exige documentos, el portal no permite postular sin ellos.
- Con los documentos requeridos adjuntos, la postulación es exitosa.
"""
import tempfile

from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from apps.empresas.models import Empresa
from apps.organizacion.models import Sede
from apps.perfilcargo.models import PerfilCargo
from apps.reclutamiento.models import Vacante, ProcesoSeleccion

TEMP_MEDIA_DIR = tempfile.mkdtemp()


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    },
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_ROOT=TEMP_MEDIA_DIR,
)
class DocumentosRequeridosPortalTestCase(APITestCase):
    def setUp(self):
        empresa = Empresa.objects.create(
            nombre="Empresa Docs", nit="900830001-1",
            num_trabajadores=10, nivel_riesgo=2, capitulo_vigente="I",
        )
        Sede.objects.create(empresa=empresa, nombre="Sede", ciudad="Bogotá")
        cargo = PerfilCargo.objects.create(
            empresa=empresa, codigo="PC-DOC", nombre_cargo="Auxiliar",
        )
        self.vacante = Vacante.objects.create(
            empresa=empresa, perfil_cargo=cargo, titulo="Auxiliar",
            numero_cupos=1, estado=Vacante.Estado.ABIERTA, publicada_en_portal=True,
        )
        ProcesoSeleccion.objects.create(
            empresa=empresa, vacante=self.vacante,
            documentos_requeridos=["hoja_de_vida", "cedula"],
        )

    def _post(self, files=None):
        data = {
            "tipo_documento": "CC",
            "documento": "99887766",
            "nombres": "Ana",
            "apellidos": "Docs",
            "email": "ana.docs@mail.com",
            "autoriza_tratamiento_datos": True,
        }
        if files:
            data.update(files)
        return self.client.post(
            f"/api/reclutamiento/portal/vacantes/{self.vacante.id}/postular/",
            data,
            format="multipart",
        )

    def test_bloquea_si_faltan_documentos_requeridos(self):
        res = self._post()
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Faltan documentos requeridos", res.data["detail"])

    def test_acepta_con_documentos_requeridos(self):
        cv = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 cv", content_type="application/pdf")
        cedula = SimpleUploadedFile("cedula.pdf", b"%PDF-1.4 cc", content_type="application/pdf")
        res = self._post({"archivo_cv": cv, "archivo_cedula": cedula})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("postulacion_id", res.data)
