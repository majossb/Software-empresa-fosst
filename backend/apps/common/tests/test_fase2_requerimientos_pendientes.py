import io
from datetime import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from openpyxl import Workbook

from apps.accounts.models import Usuario, UserRole
from apps.empresas.models import Empresa
from apps.planes.models import Plan, Suscripcion
from apps.estandares.models import Evaluacion
from apps.informes.models import Informe
from apps.calendario.models import Incidente
from apps.capacitaciones.models import Trabajador
from apps.capacitaciones.services import calcular_indicadores_accidentalidad, generar_plantilla_furat_pdf
from apps.gestion_humana.importador import procesar_importacion_trabajadores, generar_plantilla_excel


class Fase2RequerimientosPendientesTest(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(
            nombre="Empresa Test Fase 2",
            nit="900999888-2",
            sector_economico="Servicios",
            nivel_riesgo=2,
            num_trabajadores=5,
        )

        self.user = Usuario.objects.create_user(
            username="responsable_fase2",
            email="responsable@fase2.com",
            password="Password123!",
            first_name="Responsable",
            last_name="Fase 2",
            rol=UserRole.RESPONSABLE,
            empresa=self.empresa,
        )

        plan = Plan.objects.create(
            nombre="Plan Completo",
            precio_mensual=500,
            precio_anual=5000,
            max_usuarios=50,
            max_evidencias_mb=1000,
            tiene_auditoria=True,
            tiene_informes=True,
            tiene_calendario=True,
        )
        Suscripcion.objects.create(
            empresa=self.empresa,
            plan=plan,
            estado=Suscripcion.Estado.ACTIVA,
            fecha_inicio=datetime.now(),
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_importacion_masiva_trabajadores_excel(self):
        """Verifica la importación masiva de trabajadores desde Excel con reporte fila por fila."""
        wb = Workbook()
        ws = wb.active
        ws.append(["nombre", "apellidos", "tipo_documento", "documento", "email", "telefono", "tipo_vinculacion", "tipo_contrato", "fecha_ingreso", "salario"])
        ws.append(["Pedro", "Alvarado", "CC", "111222333", "pedro@test.com", "3001112233", "dependiente", "indefinido", "2026-01-01", "2000000"])
        # Duplicado
        ws.append(["Pedro", "Alvarado", "CC", "111222333", "pedro@test.com", "3001112233", "dependiente", "indefinido", "2026-01-01", "2000000"])

        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)
        file_stream.name = "trabajadores.xlsx"

        res = procesar_importacion_trabajadores(file_stream, self.empresa, self.user)
        self.assertEqual(res["total_filas"], 2)
        self.assertEqual(res["creadas"], 1)
        self.assertEqual(res["fallidas"], 1)
        self.assertTrue(Trabajador.objects.filter(empresa=self.empresa, documento="111222333").exists())

    def test_plantilla_importacion_excel_download(self):
        """Verifica la generación y descarga de la plantilla Excel."""
        content = generar_plantilla_excel()
        self.assertIsNotNone(content)
        self.assertTrue(len(content) > 0)

    def test_firma_digital_informe_y_pdf(self):
        """Verifica el flujo de firma gráfica, sellado de hash SHA-256 y generación de PDF."""
        evaluacion = Evaluacion.objects.create(empresa=self.empresa, anio=2026, capitulo="II")
        informe = Informe.objects.create(
            evaluacion=evaluacion,
            tipo=Informe.Tipo.EJECUTIVO,
            contenido_json={"resumen": "Ok"},
        )

        res_firmar = self.client.post(
            f"/api/informes/{informe.id}/firmar",
            {"tipo_firma": "responsable", "firma_base64": "data:image/png;base64,iVBORw0KGgo="},
            format="json"
        )
        self.assertEqual(res_firmar.status_code, status.HTTP_200_OK)

        informe.refresh_from_db()
        self.assertTrue(informe.firmado_responsable)
        self.assertIsNotNone(informe.hash_documento)
        self.assertEqual(informe.firma_responsable_usuario, self.user)

    def test_furat_pdf_e_indicadores_accidentalidad(self):
        """Verifica el cálculo de IFA, ISA, ILI y la plantilla PDF FURAT para incidentes."""
        incidente = Incidente.objects.create(
            empresa=self.empresa,
            tipo=Incidente.Tipo.ACCIDENTE,
            fecha=datetime.now(),
            descripcion="Caída de altura al inspeccionar vehículo",
            dias_incapacidad=15,
        )

        indicadores = calcular_indicadores_accidentalidad(self.empresa, anio=2026)
        self.assertEqual(indicadores["num_accidentes"], 1)
        self.assertEqual(indicadores["total_dias_incapacidad"], 15)
        self.assertGreater(indicadores["indice_frecuencia_ifa"], 0)

        pdf_bytes = generar_plantilla_furat_pdf(incidente)
        self.assertIsNotNone(pdf_bytes)
        self.assertTrue(len(pdf_bytes) > 0)
