import hashlib
import os
import tempfile
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import Usuario
from apps.empresas.models import Empresa
from apps.estandares.models import Evaluacion, Estandar, Respuesta
from apps.evidencias.models import Evidencia, Archivo


TEMP_MEDIA_DIR = tempfile.mkdtemp()

@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
    },
    DEFAULT_FILE_STORAGE="django.core.files.storage.FileSystemStorage",
    MEDIA_ROOT=TEMP_MEDIA_DIR
)
class EvidenciaIntegridadTestCase(APITestCase):

    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Test Evidencias S.A.S.",
            nit="900999888-1",
            sector_economico="Servicios",
            num_trabajadores=15,
            nivel_riesgo=3,
            capitulo_vigente="capitulo_1"
        )
        self.usuario = Usuario.objects.create_user(
            username="user_evidencia_test",
            email="evidencia@test.com",
            password="Password123!",
            empresa=self.empresa,
            rol="responsable"
        )
        self.client.force_authenticate(user=self.usuario)

        self.evaluacion = Evaluacion.objects.create(
            empresa=self.empresa,
            anio=2026,
            capitulo="capitulo_1",
            puntaje_total=80.0
        )
        self.estandar = Estandar.objects.create(
            codigo="1.1.1",
            nombre="Responsable del SG-SST",
            capitulo="capitulo_1",
            ciclo_phva="Planear",
            puntaje_maximo=0.5
        )
        self.respuesta = Respuesta.objects.create(
            evaluacion=self.evaluacion,
            estandar=self.estandar,
            estado="cumple",
            puntaje=0.5
        )

    def test_evi_01_y_02_carga_verificacion_integridad_hash(self):
        # 1. Crear archivo binario real
        content_original = b"CONTENIDO DE PRUEBA DE EVIDENCIA EVI-02 SHA-256 INTEGRIDAD FOSST V.I.D.A."
        hash_esperado = hashlib.sha256(content_original).hexdigest()

        file_obj = SimpleUploadedFile(
            "acta_comite_sst.pdf",
            content_original,
            content_type="application/pdf"
        )

        # 2. POST /api/evidencias/
        response = self.client.post(
            "/api/evidencias/",
            {
                "respuesta_id": str(self.respuesta.id),
                "descripcion": "Acta de Conformación Comité SST",
                "archivo": file_obj
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evidencia_id = response.data["id"]
        archivo_id = response.data["archivo"]["id"]

        archivo_obj = Archivo.objects.get(id=archivo_id)
        self.assertEqual(archivo_obj.sha256_hash, hash_esperado)

        # 3. GET /api/evidencias/<id>/verificar-integridad
        url_verificar = f"/api/evidencias/{evidencia_id}/verificar-integridad"
        res_verificar = self.client.get(url_verificar)
        self.assertEqual(res_verificar.status_code, status.HTTP_200_OK)
        self.assertTrue(res_verificar.data["integro"])
        self.assertEqual(res_verificar.data["sha256_hash"], hash_esperado)

        # 4. Simular alteración física del hash para probar caso negativo (corrupción de hash)
        archivo_obj.sha256_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        archivo_obj.save()

        res_corrupto = self.client.get(url_verificar)
        self.assertEqual(res_corrupto.status_code, status.HTTP_200_OK)
        self.assertFalse(res_corrupto.data["integro"])

    def test_evi_03_soft_delete_evidencia(self):
        content = b"DOCUMENTO PARA PRUEBA SOFT DELETE"
        file_obj = SimpleUploadedFile("documento.pdf", content, content_type="application/pdf")

        res_post = self.client.post(
            "/api/evidencias/",
            {
                "respuesta_id": str(self.respuesta.id),
                "descripcion": "Evidencia para eliminar",
                "archivo": file_obj
            },
            format="multipart"
        )
        evidencia_id = res_post.data["id"]
        archivo_id = res_post.data["archivo"]["id"]

        # DELETE /api/evidencias/<id>
        res_delete = self.client.delete(f"/api/evidencias/{evidencia_id}")
        self.assertEqual(res_delete.status_code, status.HTTP_200_OK)

        # Confirmar Soft Delete usando all_objects: la fila continua en DB con deleted_at != None
        evidencia_db = Evidencia.all_objects.get(id=evidencia_id)
        self.assertIsNotNone(evidencia_db.deleted_at)

        archivo_db = Archivo.all_objects.get(id=archivo_id)
        self.assertIsNotNone(archivo_db.deleted_at)

        # Confirmar que en la lista GET con default manager no se devuelve la evidencia eliminada
        res_list = self.client.get("/api/evidencias/")
        self.assertEqual(res_list.data["total"], 0)
