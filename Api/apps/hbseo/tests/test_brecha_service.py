"""
Tests del servicio HBSEO y reglas de negocio RN-16, RN-17.

Cubren:
  - Creación de brecha nueva via registrar_o_vincular_brecha()
  - Vinculación de origen adicional a brecha existente
  - RN-16: rechazo de brecha sin referencia trazable
  - RN-17: cambio de estado genera BrechaEvento automáticamente
  - Deduplicación: misma condición/trabajador → vincula, no duplica
  - Código auto-generado (BR-YYYY-NNNNNN)
  - Aislamiento multi-tenant
  - Generación de textos IA (mock)
"""
from django.test import TestCase, override_settings

from apps.empresas.models import Empresa
from apps.accounts.models import Usuario, UserRole
from apps.capacitaciones.models import Trabajador
from apps.perfilcargo.models import PerfilCargo, CatalogoPeligro

from apps.hbseo.models import Brecha, BrechaOrigen, BrechaEvento, BrechaAccion
from apps.hbseo.services import registrar_o_vincular_brecha


def _crear_empresa(nit="900123456-1"):
    return Empresa.objects.create(
        nombre="Empresa de Prueba SAS",
        nit=nit,
        num_trabajadores=10,
        nivel_riesgo=3,
        capitulo_vigente="I",
    )


def _crear_trabajador(empresa, nombre="Juan Pérez", documento="1000000001"):
    return Trabajador.objects.create(
        empresa=empresa,
        nombre=nombre,
        documento=documento,
        tipo_vinculacion="dependiente",
    )


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class RegistrarBrechaTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.trabajador = _crear_trabajador(self.empresa)
        # Usar un modelo existente como referencia para GenericFK
        self.peligro = CatalogoPeligro.objects.create(
            tipo="Caída de alturas", clasificacion="Físico",
        )

    def test_crear_brecha_nueva(self):
        """registrar_o_vincular_brecha crea una brecha con código, origen y evento."""
        brecha = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="hallazgo",
            referencia_obj=self.peligro,
            descripcion_base="Riesgo de caída identificado sin control",
            trabajador=self.trabajador,
            detectado_por="Sistema (SST)",
        )

        self.assertIsNotNone(brecha.pk)
        self.assertTrue(brecha.codigo.startswith("BR-"))
        self.assertEqual(brecha.empresa, self.empresa)
        self.assertEqual(brecha.trabajador, self.trabajador)
        self.assertEqual(brecha.clasificacion, "hallazgo")
        self.assertEqual(brecha.estado, "detectada")

        # Tiene exactamente un origen (principal)
        origenes = brecha.origenes.all()
        self.assertEqual(origenes.count(), 1)
        self.assertTrue(origenes.first().es_origen_principal)
        self.assertEqual(origenes.first().modulo_origen, "sst")

        # Tiene evento de detección
        eventos = brecha.eventos.all()
        self.assertEqual(eventos.count(), 1)
        self.assertEqual(eventos.first().tipo_evento, "deteccion")

        # Tiene textos IA generados (mock)
        self.assertTrue(len(brecha.descripcion_automatica) > 0)
        self.assertTrue(len(brecha.interpretacion_ia) > 0)
        self.assertTrue(len(brecha.recomendacion_automatica) > 0)

    def test_vincular_origen_adicional_a_brecha_existente(self):
        """Si ya existe una brecha abierta para la misma condición, vincula el nuevo origen."""
        # Primer registro: crea brecha nueva
        brecha1 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="restriccion",
            referencia_obj=self.peligro,
            descripcion_base="Restricción detectada por SST",
            trabajador=self.trabajador,
            detectado_por="Sistema (SST)",
        )

        # Segundo registro con otro objeto de referencia pero misma condición
        perfil = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-TEST-001", nombre_cargo="Test",
        )
        brecha2 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="restriccion",
            referencia_obj=perfil,  # referencia distinta
            descripcion_base="Restricción confirmada por perfil",
            trabajador=self.trabajador,
            detectado_por="Sistema (SST)",
        )

        # Debe ser la misma brecha
        self.assertEqual(brecha1.pk, brecha2.pk)

        # Ahora tiene 2 orígenes
        self.assertEqual(brecha1.origenes.count(), 2)

        # Tiene evento de vinculación
        eventos_vinculacion = brecha1.eventos.filter(tipo_evento="origen_vinculado")
        self.assertEqual(eventos_vinculacion.count(), 1)

    def test_no_duplica_misma_referencia_exacta(self):
        """Si el mismo objeto de referencia ya está vinculado, no crea origen duplicado."""
        brecha1 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="observacion",
            referencia_obj=self.peligro,
            descripcion_base="Observación",
            detectado_por="Sistema",
        )

        # Mismo objeto de referencia exacto
        brecha2 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="observacion",
            referencia_obj=self.peligro,
            descripcion_base="Observación duplicada",
            detectado_por="Sistema",
        )

        self.assertEqual(brecha1.pk, brecha2.pk)
        # Solo 1 origen, no duplicado
        self.assertEqual(brecha1.origenes.count(), 1)

    def test_rn16_brecha_sin_referencia_falla(self):
        """RN-16: No se puede crear una brecha sin referencia trazable."""
        with self.assertRaises(ValueError) as cm:
            registrar_o_vincular_brecha(
                empresa=self.empresa,
                modulo_origen="sst",
                clasificacion="hallazgo",
                referencia_obj=None,
                descripcion_base="Brecha suelta sin origen",
            )
        self.assertIn("RN-16", str(cm.exception))

    def test_rn17_cambio_estado_genera_evento(self):
        """RN-17: Cambiar el estado de una brecha genera un BrechaEvento automáticamente."""
        brecha = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="michc",
            clasificacion="incumplimiento",
            referencia_obj=self.peligro,
            descripcion_base="Incumplimiento MICHC",
            detectado_por="Sistema (MICHC)",
        )

        eventos_antes = brecha.eventos.count()

        # Cambiar estado
        brecha.estado = Brecha.Estado.EN_TRATAMIENTO
        brecha.save()

        # Debe haberse creado un evento de cambio de estado
        eventos_despues = brecha.eventos.count()
        self.assertEqual(eventos_despues, eventos_antes + 1)

        evento_cambio = brecha.eventos.filter(tipo_evento="cambio_estado").first()
        self.assertIsNotNone(evento_cambio)
        self.assertIn("detectada", evento_cambio.descripcion)
        self.assertIn("en_tratamiento", evento_cambio.descripcion)

    def test_rn17_no_genera_evento_si_estado_no_cambia(self):
        """Si se guarda sin cambiar el estado, no se genera evento duplicado."""
        brecha = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="observacion",
            referencia_obj=self.peligro,
            descripcion_base="Observación",
            detectado_por="Sistema",
        )

        eventos_antes = brecha.eventos.count()

        # Guardar sin cambiar estado
        brecha.descripcion_complementaria = "Nota del usuario"
        brecha.save()

        self.assertEqual(brecha.eventos.count(), eventos_antes)

    def test_codigo_secuencial(self):
        """Los códigos de brecha son secuenciales dentro del mismo año."""
        b1 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="hallazgo",
            referencia_obj=self.peligro,
            descripcion_base="Primera",
            detectado_por="Sistema",
        )

        peligro2 = CatalogoPeligro.objects.create(
            tipo="Ruido", clasificacion="Físico",
        )
        b2 = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="observacion",
            referencia_obj=peligro2,
            descripcion_base="Segunda",
            detectado_por="Sistema",
        )

        # Ambos deben tener códigos del mismo año
        year_b1 = b1.codigo.split("-")[1]
        year_b2 = b2.codigo.split("-")[1]
        self.assertEqual(year_b1, year_b2)

        # Secuenciales
        seq_b1 = int(b1.codigo.split("-")[2])
        seq_b2 = int(b2.codigo.split("-")[2])
        self.assertEqual(seq_b2, seq_b1 + 1)

    def test_aislamiento_multitenant(self):
        """Brechas de empresa A no deben aparecer en consultas de empresa B."""
        otra_empresa = _crear_empresa(nit="900999999-1")
        otro_trabajador = _crear_trabajador(otra_empresa, "María", "2000000001")

        peligro2 = CatalogoPeligro.objects.create(
            tipo="Químico", clasificacion="Químico",
        )

        registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="hallazgo",
            referencia_obj=self.peligro,
            descripcion_base="Brecha empresa 1",
            detectado_por="Sistema",
        )

        registrar_o_vincular_brecha(
            empresa=otra_empresa,
            modulo_origen="sst",
            clasificacion="hallazgo",
            referencia_obj=peligro2,
            descripcion_base="Brecha empresa 2",
            detectado_por="Sistema",
        )

        brechas_empresa1 = Brecha.objects.filter(empresa=self.empresa)
        brechas_empresa2 = Brecha.objects.filter(empresa=otra_empresa)

        self.assertEqual(brechas_empresa1.count(), 1)
        self.assertEqual(brechas_empresa2.count(), 1)
        self.assertNotEqual(
            brechas_empresa1.first().pk,
            brechas_empresa2.first().pk,
        )

    def test_brecha_con_diferente_modulo_origen_crea_nueva(self):
        """Mismo trabajador y clasificación pero distinto módulo → brecha nueva."""
        brecha_sst = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="restriccion",
            referencia_obj=self.peligro,
            descripcion_base="Restricción SST",
            trabajador=self.trabajador,
            detectado_por="Sistema (SST)",
        )

        perfil = PerfilCargo.objects.create(
            empresa=self.empresa, codigo="PC-TEST-002", nombre_cargo="Test 2",
        )
        brecha_michc = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="michc",
            clasificacion="restriccion",
            referencia_obj=perfil,
            descripcion_base="Restricción MICHC",
            trabajador=self.trabajador,
            detectado_por="Sistema (MICHC)",
        )

        # Deben ser brechas distintas (diferente módulo de origen)
        self.assertNotEqual(brecha_sst.pk, brecha_michc.pk)


@override_settings(
    ANTHROPIC_API_KEY="",
    CELERY_TASK_ALWAYS_EAGER=True,
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class BrechaAccionTests(TestCase):

    def setUp(self):
        self.empresa = _crear_empresa()
        self.peligro = CatalogoPeligro.objects.create(
            tipo="Eléctrico", clasificacion="Físico",
        )

    def test_crear_accion_para_brecha(self):
        brecha = registrar_o_vincular_brecha(
            empresa=self.empresa,
            modulo_origen="sst",
            clasificacion="hallazgo",
            referencia_obj=self.peligro,
            descripcion_base="Hallazgo eléctrico",
            detectado_por="Sistema",
        )

        from datetime import date
        accion = BrechaAccion.objects.create(
            brecha=brecha,
            descripcion="Instalar protecciones en tablero eléctrico",
            fecha_programada=date(2026, 9, 15),
        )

        self.assertEqual(brecha.acciones.count(), 1)
        self.assertEqual(accion.estado, "programada")
