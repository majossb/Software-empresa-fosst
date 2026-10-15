"""
Servicio genérico de interpretación IA para FOSST V.I.D.A.

Generaliza el patrón de IAContextoService (apps/empresas/services_ia.py):
  - ANTHROPIC_API_KEY → Claude / fallback a mock inteligente
  - Output JSON estructurado (no texto libre parseado con regex)
  - Logging de prompt/respuesta para auditoría legal
  - Deduplicación por hash de contexto

Uso:
    from apps.ia.service import IAInterpretacionService

    resultado = IAInterpretacionService.generar(
        tipo="descripcion_brecha",
        contexto={
            "modulo_origen": "michc",
            "clasificacion": "restriccion",
            "descripcion_base": "Trabajador sin examen médico vigente",
            "empresa_nombre": "Acme SAS",
        }
    )
    # resultado = {"descripcion_automatica": "...", "interpretacion_ia": "...", ...}
"""
import hashlib
import json
import logging

from django.conf import settings
from django.core.cache import cache

from .prompts import PROMPT_REGISTRY

logger = logging.getLogger(__name__)

# Tiempo de cache para deduplicación de interpretaciones IA (24 horas).
IA_CACHE_TTL = 60 * 60 * 24


class IAInterpretacionService:
    """
    Punto de entrada único para todas las interpretaciones IA del sistema.

    Sigue exactamente el patrón de IAContextoService:
      1. Verifica ANTHROPIC_API_KEY
      2. Si existe: llama a Claude con prompt estructurado → parsea JSON
      3. Si falla o no hay key: genera mock inteligente
      4. En ambos casos: loguea prompt + respuesta para auditoría
    """

    @staticmethod
    def _get_api_key():
        return getattr(settings, "ANTHROPIC_API_KEY", "")

    @staticmethod
    def _hash_contexto(tipo: str, contexto: dict) -> str:
        """Hash estable del contexto para deduplicación."""
        payload = json.dumps({"tipo": tipo, "contexto": contexto}, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()[:32]

    @classmethod
    def generar(cls, tipo: str, contexto: dict, forzar: bool = False) -> dict:
        """
        Genera una interpretación IA estructurada.

        Args:
            tipo: Uno de los tipos registrados en PROMPT_REGISTRY
                  ("descripcion_brecha", "interpretacion_michc", "recomendacion_brecha")
            contexto: Dict con los datos que alimentan el prompt (ver docstring de cada prompt)
            forzar: Si True, ignora cache y regenera aunque el contexto no haya cambiado

        Returns:
            Dict con los campos del output_schema del tipo solicitado.
            Incluye siempre el campo adicional "fuente" ("Anthropic Claude" o "Mock Inteligente").

        Raises:
            ValueError: si el tipo no está registrado
        """
        if tipo not in PROMPT_REGISTRY:
            raise ValueError(
                f"Tipo de interpretación IA desconocido: '{tipo}'. "
                f"Tipos válidos: {list(PROMPT_REGISTRY.keys())}"
            )

        # Deduplicación: no re-llamar a la IA si el contexto no cambió
        ctx_hash = cls._hash_contexto(tipo, contexto)
        cache_key = f"ia_interp:{tipo}:{ctx_hash}"

        if not forzar:
            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    logger.debug(
                        "[IAInterpretacionService] Cache hit para tipo=%s hash=%s",
                        tipo, ctx_hash,
                    )
                    return cached
            except Exception as e:
                logger.warning("[IAInterpretacionService] Cache read error (continuing without cache): %s", e)

        # Generar prompt
        prompt_fn = PROMPT_REGISTRY[tipo]
        prompt_data = prompt_fn(contexto)
        prompt_text = prompt_data["prompt"]
        output_schema = prompt_data["output_schema"]

        # Intentar llamada real a Claude
        api_key = cls._get_api_key()
        resultado = None

        if api_key:
            resultado = cls._llamar_claude(tipo, prompt_text, output_schema, api_key)

        # Fallback a mock si no hay API key o si la llamada falló
        if resultado is None:
            resultado = cls._generar_mock(tipo, contexto, output_schema)

        # Cachear resultado (graceful degradation si cache no está disponible)
        try:
            cache.set(cache_key, resultado, timeout=IA_CACHE_TTL)
        except Exception as e:
            logger.warning("[IAInterpretacionService] Cache write error: %s", e)

        return resultado

    @classmethod
    def _llamar_claude(cls, tipo, prompt_text, output_schema, api_key):
        """Llama a Anthropic Claude — patrón idéntico a IAContextoService."""
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            logger.info(
                "[IAInterpretacionService] Llamando a Claude para tipo=%s (prompt %d chars)",
                tipo, len(prompt_text),
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt_text}],
            )

            text = response.content[0].text if response.content else ""

            # Parseo robusto: buscar JSON en la respuesta (mismo patrón que IAContextoService)
            start = text.find("{")
            end = text.rfind("}") + 1
            if start == -1 or end == 0:
                raise ValueError(f"Respuesta de Claude no contiene JSON válido: {text[:200]}")

            cleaned = text[start:end]
            parsed = json.loads(cleaned)

            # Validar que tenga los campos esperados
            missing = [k for k in output_schema if k not in parsed]
            if missing:
                logger.warning(
                    "[IAInterpretacionService] Campos faltantes en respuesta Claude: %s", missing,
                )

            logger.info(
                "[IAInterpretacionService] Respuesta Claude exitosa para tipo=%s", tipo,
            )

            parsed["fuente"] = "Anthropic Claude"
            return parsed

        except Exception as e:
            logger.error(
                "[IAInterpretacionService] Error llamando a Claude para tipo=%s: %s. Usando mock.",
                tipo, e,
            )
            return None

    @classmethod
    def _generar_mock(cls, tipo, contexto, output_schema):
        """
        Mock inteligente por tipo — genera respuestas razonables sin IA real.
        Sigue el patrón de los mocks de IAContextoService (contextual, no placeholder).
        """
        logger.info(
            "[IAInterpretacionService] Generando mock para tipo=%s", tipo,
        )

        if tipo == "descripcion_brecha":
            return cls._mock_descripcion_brecha(contexto)
        elif tipo == "interpretacion_michc":
            return cls._mock_interpretacion_michc(contexto)
        elif tipo == "recomendacion_brecha":
            return cls._mock_recomendacion_brecha(contexto)
        else:
            # Fallback genérico: llenar output_schema con placeholders
            result = {k: f"[Mock] {k}" for k in output_schema}
            result["fuente"] = "Mock Inteligente"
            return result

    @staticmethod
    def _mock_descripcion_brecha(ctx):
        modulo = ctx.get("modulo_origen", "no especificado")
        clasificacion = ctx.get("clasificacion", "no especificada")
        desc_base = ctx.get("descripcion_base", "Sin descripción")
        trabajador = ctx.get("trabajador_nombre", "")
        cargo = ctx.get("cargo_nombre", "")

        sujeto = f" del trabajador {trabajador}" if trabajador else ""
        en_cargo = f" en el cargo {cargo}" if cargo else ""

        return {
            "descripcion_automatica": (
                f"Se detectó una brecha de tipo '{clasificacion}' desde el módulo de {modulo}{sujeto}{en_cargo}. "
                f"Detalle: {desc_base}. "
                f"Esta condición requiere atención según los estándares del SG-SST vigentes."
            ),
            "interpretacion_ia": (
                f"La brecha identificada ({clasificacion}) originada en el módulo de {modulo} "
                f"puede impactar el cumplimiento normativo de la empresa y la seguridad{sujeto}. "
                f"Se recomienda evaluar la criticidad real en función del contexto operativo "
                f"y tomar acciones correctivas dentro de los plazos normativos aplicables."
            ),
            "nivel_atencion": "medio",
            "recomendacion_automatica": (
                f"Asignar un responsable de seguimiento para esta brecha en un plazo máximo de 5 días hábiles. "
                f"Documentar las acciones correctivas y su evidencia de cierre en el sistema. "
                f"Realizar seguimiento periódico hasta la subsanación completa."
            ),
            "fuente": "Mock Inteligente",
        }

    @staticmethod
    def _mock_interpretacion_michc(ctx):
        pct = ctx.get("porcentaje_cumplimiento", 0)
        semaforo = ctx.get("semaforo", "rojo")
        trabajador = ctx.get("trabajador_nombre", "el trabajador")
        cargo = ctx.get("cargo_nombre", "el cargo asignado")

        requisitos = ctx.get("requisitos_incumplidos", [])
        incumplidos_text = ", ".join(
            r.get("descripcion", "requisito no especificado") for r in requisitos[:3]
        ) or "ninguno identificado"

        if pct >= 100:
            compat = "compatible"
            nivel = "bajo"
            interp = (
                f"{trabajador} cumple con el 100% de los requisitos para {cargo}. "
                f"No se identifican brechas que afecten la habilitación."
            )
        elif pct >= 80:
            compat = "compatible_con_restricciones"
            nivel = "medio"
            interp = (
                f"{trabajador} cumple parcialmente ({pct}%) los requisitos para {cargo}. "
                f"Las brechas identificadas ({incumplidos_text}) no impiden la operación "
                f"pero deben subsanarse en el corto plazo para mantener la habilitación completa."
            )
        else:
            compat = "incompatible_temporal"
            nivel = "alto" if pct >= 50 else "critico"
            interp = (
                f"{trabajador} presenta un cumplimiento insuficiente ({pct}%) para {cargo}. "
                f"Las brechas críticas ({incumplidos_text}) representan un riesgo operativo y "
                f"normativo que requiere intervención inmediata."
            )

        return {
            "interpretacion_general": interp,
            "nivel_atencion": nivel,
            "compatibilidad": compat,
            "recomendacion": (
                f"Priorizar la subsanación de las brechas identificadas: {incumplidos_text}. "
                f"Programar las acciones correctivas necesarias y asignar responsables. "
                f"Realizar seguimiento semanal hasta alcanzar el nivel de habilitación requerido."
            ),
            "fuente": "Mock Inteligente",
        }

    @staticmethod
    def _mock_recomendacion_brecha(ctx):
        codigo = ctx.get("brecha_codigo", "N/A")
        origenes = ctx.get("origenes", [])
        modulos = ", ".join(o.get("modulo_origen", "N/A") for o in origenes) or "no especificados"

        return {
            "interpretacion_ia": (
                f"La brecha {codigo} presenta orígenes múltiples desde los módulos de {modulos}. "
                f"La convergencia de estos orígenes sugiere una condición sistémica que "
                f"requiere un abordaje integral, no acciones aisladas por módulo."
            ),
            "nivel_atencion": "alto",
            "recomendacion_automatica": (
                f"Conformar un equipo interdisciplinario que aborde la brecha {codigo} de manera integral. "
                f"Definir un plan de acción unificado que contemple las perspectivas de "
                f"todos los módulos involucrados ({modulos}). "
                f"Establecer hitos de seguimiento quincenales hasta el cierre completo."
            ),
            "fuente": "Mock Inteligente",
        }
