"""
Tests del servicio genérico de interpretación IA.

Cubren:
  - Generación con mock (sin API key) para cada tipo registrado
  - Deduplicación por hash de contexto (cache hit)
  - Tipo no registrado → ValueError
  - Estructura de respuesta conforme al output_schema
  - Flag forzar=True ignora cache
"""
from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.ia.service import IAInterpretacionService
from apps.ia.prompts import PROMPT_REGISTRY


@override_settings(
    ANTHROPIC_API_KEY="",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class IAInterpretacionServiceMockTests(TestCase):
    """Tests que ejercitan los mocks inteligentes (sin API key)."""

    def test_tipo_invalido_raises_value_error(self):
        with self.assertRaises(ValueError) as cm:
            IAInterpretacionService.generar("tipo_inexistente", {})
        self.assertIn("tipo_inexistente", str(cm.exception))
        self.assertIn("Tipos válidos", str(cm.exception))

    def test_todos_los_tipos_registrados_generan_resultado(self):
        """Cada tipo registrado en PROMPT_REGISTRY debe generar un resultado válido."""
        contextos = {
            "descripcion_brecha": {
                "modulo_origen": "michc",
                "clasificacion": "restriccion",
                "descripcion_base": "Trabajador sin examen médico vigente",
                "empresa_nombre": "Test SAS",
            },
            "interpretacion_michc": {
                "trabajador_nombre": "Juan Pérez",
                "cargo_nombre": "Técnico de Alturas",
                "empresa_nombre": "Test SAS",
                "porcentaje_cumplimiento": 75.0,
                "semaforo": "rojo",
                "requisitos_incumplidos": [
                    {"tipo": "certificacion", "descripcion": "Curso alturas", "cumple": "no"}
                ],
            },
            "recomendacion_brecha": {
                "empresa_nombre": "Test SAS",
                "brecha_codigo": "BR-2026-000001",
                "clasificacion": "restriccion",
                "estado_actual": "detectada",
                "origenes": [
                    {"modulo_origen": "michc", "descripcion": "Restricción médica"},
                    {"modulo_origen": "formacion", "descripcion": "Competencia no evaluable"},
                ],
            },
        }

        for tipo, contexto in contextos.items():
            with self.subTest(tipo=tipo):
                resultado = IAInterpretacionService.generar(tipo, contexto, forzar=True)

                # Siempre incluye 'fuente'
                self.assertIn("fuente", resultado)
                self.assertEqual(resultado["fuente"], "Mock Inteligente")

                # Incluye los campos del output_schema
                prompt_data = PROMPT_REGISTRY[tipo](contexto)
                for campo in prompt_data["output_schema"]:
                    self.assertIn(campo, resultado, f"Falta campo '{campo}' en resultado de tipo '{tipo}'")
                    self.assertIsInstance(resultado[campo], str)
                    self.assertTrue(len(resultado[campo]) > 0, f"Campo '{campo}' vacío en tipo '{tipo}'")

    def test_mock_descripcion_brecha_incluye_contexto(self):
        resultado = IAInterpretacionService.generar("descripcion_brecha", {
            "modulo_origen": "gestion_humana",
            "clasificacion": "incumplimiento",
            "descripcion_base": "Examen médico vencido hace 90 días",
            "trabajador_nombre": "María García",
            "cargo_nombre": "Operaria de planta",
            "empresa_nombre": "Industrias XYZ",
        }, forzar=True)

        # El mock debe incluir datos del contexto, no ser genérico
        self.assertIn("gestion_humana", resultado["descripcion_automatica"])
        self.assertIn("María García", resultado["descripcion_automatica"])

    def test_mock_michc_semaforo_verde(self):
        resultado = IAInterpretacionService.generar("interpretacion_michc", {
            "trabajador_nombre": "Juan",
            "cargo_nombre": "Analista",
            "empresa_nombre": "Test",
            "porcentaje_cumplimiento": 100,
            "semaforo": "verde",
            "requisitos_incumplidos": [],
        }, forzar=True)

        self.assertEqual(resultado["compatibilidad"], "compatible")
        self.assertEqual(resultado["nivel_atencion"], "bajo")

    def test_mock_michc_semaforo_rojo(self):
        resultado = IAInterpretacionService.generar("interpretacion_michc", {
            "trabajador_nombre": "Juan",
            "cargo_nombre": "Técnico",
            "empresa_nombre": "Test",
            "porcentaje_cumplimiento": 45,
            "semaforo": "rojo",
            "requisitos_incumplidos": [
                {"tipo": "formacion", "descripcion": "Curso alturas", "cumple": "no"},
            ],
        }, forzar=True)

        self.assertEqual(resultado["compatibilidad"], "incompatible_temporal")
        self.assertIn(resultado["nivel_atencion"], ("alto", "critico"))

    def test_cache_deduplicacion(self):
        """Mismo contexto → cache hit en la segunda llamada."""
        contexto = {
            "modulo_origen": "sst",
            "clasificacion": "observacion",
            "descripcion_base": "Observación menor",
            "empresa_nombre": "Test",
        }

        # Primera llamada: genera mock
        r1 = IAInterpretacionService.generar("descripcion_brecha", contexto, forzar=True)

        # Segunda llamada con mismo contexto: debe usar cache
        with patch.object(IAInterpretacionService, "_generar_mock") as mock_fn:
            r2 = IAInterpretacionService.generar("descripcion_brecha", contexto, forzar=False)
            mock_fn.assert_not_called()  # No se llamó al mock porque usó cache

        self.assertEqual(r1, r2)

    def test_forzar_ignora_cache(self):
        """forzar=True debe regenerar aunque haya cache."""
        contexto = {
            "modulo_origen": "sst",
            "clasificacion": "observacion",
            "descripcion_base": "Observación",
            "empresa_nombre": "Test",
        }

        # Llenar cache
        IAInterpretacionService.generar("descripcion_brecha", contexto, forzar=True)

        # Forzar: debe llamar al mock de nuevo
        with patch.object(
            IAInterpretacionService, "_generar_mock",
            wraps=IAInterpretacionService._generar_mock,
        ) as mock_fn:
            IAInterpretacionService.generar("descripcion_brecha", contexto, forzar=True)
            mock_fn.assert_called_once()
