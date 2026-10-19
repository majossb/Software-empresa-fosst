"""
Templates de prompt para el servicio de interpretación IA.

Cada función recibe un dict de contexto y devuelve:
  - prompt (str): el texto completo del mensaje para el modelo
  - output_schema (dict): la estructura JSON esperada de la respuesta

Separar los prompts de la lógica de llamada permite:
  - auditar/iterar sobre los prompts sin tocar el servicio
  - testear la generación de prompts sin llamar a la API
"""


def prompt_descripcion_brecha(contexto: dict) -> dict:
    """
    Genera la descripción automática e interpretación de una brecha.

    Contexto esperado:
      - modulo_origen (str)
      - clasificacion (str)
      - descripcion_base (str)
      - trabajador_nombre (str, opcional)
      - cargo_nombre (str, opcional)
      - empresa_nombre (str)
      - origenes_previos (list[dict], opcional) — para brechas con múltiples orígenes
    """
    origenes_text = ""
    if contexto.get("origenes_previos"):
        items = []
        for o in contexto["origenes_previos"]:
            items.append(f"  - Módulo: {o.get('modulo_origen', 'N/A')}, Descripción: {o.get('descripcion', 'N/A')}")
        origenes_text = (
            "\n\nEsta brecha ya tiene los siguientes orígenes registrados:\n"
            + "\n".join(items)
            + "\n\nIntegra el nuevo origen con los anteriores en tu interpretación."
        )

    prompt = (
        "Actúa como un experto en sistemas de gestión de seguridad y salud en el trabajo (SG-SST), "
        "gestión humana y cumplimiento normativo colombiano.\n\n"
        "Se ha detectado una brecha organizacional con los siguientes datos:\n"
        f"- Empresa: \"{contexto.get('empresa_nombre', 'N/A')}\"\n"
        f"- Módulo de origen: \"{contexto.get('modulo_origen', 'N/A')}\"\n"
        f"- Clasificación: \"{contexto.get('clasificacion', 'N/A')}\"\n"
        f"- Descripción base: \"{contexto.get('descripcion_base', 'N/A')}\"\n"
    )

    if contexto.get("trabajador_nombre"):
        prompt += f"- Trabajador afectado: \"{contexto['trabajador_nombre']}\"\n"
    if contexto.get("cargo_nombre"):
        prompt += f"- Cargo: \"{contexto['cargo_nombre']}\"\n"

    prompt += origenes_text

    prompt += (
        "\n\nGenera un análisis profesional y estructurado de esta brecha. "
        "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, sin textos "
        "explicativos introductorios ni de cierre, con la siguiente estructura exacta:\n"
        "{\n"
        '  "descripcion_automatica": "Descripción clara y concisa de la brecha detectada, '
        'qué requisito normativo o de gestión se ve afectado y cuál es la condición actual (2-3 oraciones).",\n'
        '  "interpretacion_ia": "Análisis del impacto potencial de esta brecha sobre la operación, '
        'la seguridad del trabajador y el cumplimiento legal de la empresa (1-2 párrafos).",\n'
        '  "nivel_atencion": "bajo | medio | alto | critico",\n'
        '  "recomendacion_automatica": "Recomendación concreta y accionable para subsanar la brecha, '
        'incluyendo plazos sugeridos y responsables típicos (2-3 oraciones)."\n'
        "}"
    )

    output_schema = {
        "descripcion_automatica": "str",
        "interpretacion_ia": "str",
        "nivel_atencion": "str",  # bajo | medio | alto | critico
        "recomendacion_automatica": "str",
    }

    return {"prompt": prompt, "output_schema": output_schema}


def prompt_interpretacion_michc(contexto: dict) -> dict:
    """
    Genera interpretación de la evaluación MICHC de un trabajador.

    Contexto esperado:
      - trabajador_nombre (str)
      - cargo_nombre (str)
      - empresa_nombre (str)
      - porcentaje_cumplimiento (float)
      - semaforo (str)
      - requisitos_incumplidos (list[dict]) — cada uno con tipo, descripcion, cumple
      - restricciones_medicas (list[str], opcional)
      - restricciones_cargo (list[str], opcional)
    """
    requisitos_text = ""
    if contexto.get("requisitos_incumplidos"):
        items = []
        for r in contexto["requisitos_incumplidos"]:
            items.append(f"  - [{r.get('tipo', 'N/A')}] {r.get('descripcion', 'N/A')} → {r.get('cumple', 'N/A')}")
        requisitos_text = "\n\nRequisitos no cumplidos o parcialmente cumplidos:\n" + "\n".join(items)

    restricciones_text = ""
    if contexto.get("restricciones_medicas") or contexto.get("restricciones_cargo"):
        restricciones_text = "\n\nRestricciones relevantes:"
        for rm in contexto.get("restricciones_medicas", []):
            restricciones_text += f"\n  - [Médica] {rm}"
        for rc in contexto.get("restricciones_cargo", []):
            restricciones_text += f"\n  - [Cargo] {rc}"

    prompt = (
        "Actúa como un experto en habilitación de cargos, gestión humana y SG-SST colombiano.\n\n"
        "Evalúa la siguiente situación de habilitación cargo-trabajador:\n"
        f"- Empresa: \"{contexto.get('empresa_nombre', 'N/A')}\"\n"
        f"- Trabajador: \"{contexto.get('trabajador_nombre', 'N/A')}\"\n"
        f"- Cargo: \"{contexto.get('cargo_nombre', 'N/A')}\"\n"
        f"- Porcentaje de cumplimiento: {contexto.get('porcentaje_cumplimiento', 'N/A')}%\n"
        f"- Semáforo: {contexto.get('semaforo', 'N/A')}\n"
        f"{requisitos_text}"
        f"{restricciones_text}"
        "\n\nGenera un análisis profesional. "
        "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido con la siguiente estructura:\n"
        "{\n"
        '  "interpretacion_general": "Análisis del estado de habilitación del trabajador, '
        'incluyendo las brechas más críticas y su impacto en la operación (1-2 párrafos).",\n'
        '  "nivel_atencion": "bajo | medio | alto | critico",\n'
        '  "compatibilidad": "compatible | compatible_con_restricciones | incompatible_temporal",\n'
        '  "recomendacion": "Acciones específicas para cerrar las brechas identificadas, '
        'priorizadas por urgencia (2-3 oraciones)."\n'
        "}"
    )

    output_schema = {
        "interpretacion_general": "str",
        "nivel_atencion": "str",
        "compatibilidad": "str",
        "recomendacion": "str",
    }

    return {"prompt": prompt, "output_schema": output_schema}


def prompt_recomendacion_brecha(contexto: dict) -> dict:
    """
    Genera recomendación de subsanación para una brecha existente cuando
    se agrega un nuevo origen (regeneración con contexto combinado).

    Contexto esperado:
      - empresa_nombre (str)
      - brecha_codigo (str)
      - clasificacion (str)
      - estado_actual (str)
      - origenes (list[dict]) — todos los orígenes con modulo y descripcion
      - acciones_existentes (list[str], opcional)
    """
    origenes_text = "\n".join(
        f"  - [{o.get('modulo_origen', 'N/A')}] {o.get('descripcion', 'N/A')}"
        for o in contexto.get("origenes", [])
    )

    acciones_text = ""
    if contexto.get("acciones_existentes"):
        acciones_text = "\n\nAcciones ya registradas:\n" + "\n".join(
            f"  - {a}" for a in contexto["acciones_existentes"]
        )

    prompt = (
        "Actúa como un experto en gestión de hallazgos, no conformidades y planes de mejora "
        "bajo estándares colombianos (SG-SST, ISO 45001, ISO 9001).\n\n"
        "Analiza la siguiente brecha organizacional con múltiples orígenes:\n"
        f"- Empresa: \"{contexto.get('empresa_nombre', 'N/A')}\"\n"
        f"- Código de brecha: \"{contexto.get('brecha_codigo', 'N/A')}\"\n"
        f"- Clasificación: \"{contexto.get('clasificacion', 'N/A')}\"\n"
        f"- Estado actual: \"{contexto.get('estado_actual', 'N/A')}\"\n"
        f"\nOrígenes de la brecha:\n{origenes_text}"
        f"{acciones_text}"
        "\n\nGenera una interpretación integrada y recomendaciones. "
        "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido:\n"
        "{\n"
        '  "interpretacion_ia": "Interpretación integrada que conecta todos los orígenes y su impacto combinado (1-2 párrafos).",\n'
        '  "nivel_atencion": "bajo | medio | alto | critico",\n'
        '  "recomendacion_automatica": "Plan de acción integrado para subsanar la brecha considerando todos los orígenes (2-4 oraciones)."\n'
        "}"
    )

    output_schema = {
        "interpretacion_ia": "str",
        "nivel_atencion": "str",
        "recomendacion_automatica": "str",
    }

    return {"prompt": prompt, "output_schema": output_schema}


def prompt_informe_gerencial_reclutamiento(contexto: dict) -> dict:
    """
    Genera un informe gerencial de resultados de reclutamiento por vacante.

    Contexto esperado: métricas AGREGADAS y anonimizadas (sin PII):
      empresa_nombre, vacante_codigo, vacante_titulo, perfil_cargo,
      postulaciones, fuentes, perfiles, entrevistas, evaluaciones,
      validaciones, documentos, tiempos.
    """
    import json as _json

    datos = _json.dumps(contexto, ensure_ascii=False, default=str, indent=2)

    prompt = (
        "Actúa como un analista senior de talento humano y gestión organizacional. "
        "Redacta un INFORME GERENCIAL de resultados de un proceso de Reclutamiento & Selección "
        "para presentar a la alta dirección.\n\n"
        "Reglas obligatorias:\n"
        "- Usa SOLO los datos agregados proporcionados; NO inventes cifras ni candidatos.\n"
        "- NO incluyas nombres, documentos, correos, teléfonos ni datos personales.\n"
        "- Garantiza confidencialidad y protección de datos (Ley 1581 de 2012).\n"
        "- Redacta en español, tono ejecutivo, claro; máximo 2 párrafos por sección.\n"
        "- No emitas decisiones de contratación: el informe apoya, no decide.\n\n"
        f"Datos agregados (JSON):\n{datos}\n\n"
        "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, sin texto adicional, "
        "con esta estructura exacta:\n"
        "{\n"
        '  "resumen_ejecutivo": "Síntesis de 3-4 oraciones para gerencia.",\n'
        '  "hallazgos_clave": ["Hallazgo 1", "Hallazgo 2", "Hallazgo 3"],\n'
        '  "analisis_fuentes": "Qué fuentes aportaron más y su efectividad.",\n'
        '  "analisis_perfiles": "Tendencias de los perfiles que postularon (sin datos personales).",\n'
        '  "resultados_entrevistas": "Resultados generales de entrevistas y evaluaciones.",\n'
        '  "tiempos_y_eficiencia": "Lectura de los tiempos del proceso.",\n'
        '  "riesgos": ["Riesgo 1", "Riesgo 2"],\n'
        '  "recomendaciones": ["Recomendación 1", "Recomendación 2", "Recomendación 3"],\n'
        '  "conclusion_para_gerencia": "Conclusión y siguiente paso sugerido."\n'
        "}"
    )

    output_schema = {
        "resumen_ejecutivo": "str",
        "hallazgos_clave": "list[str]",
        "analisis_fuentes": "str",
        "analisis_perfiles": "str",
        "resultados_entrevistas": "str",
        "tiempos_y_eficiencia": "str",
        "riesgos": "list[str]",
        "recomendaciones": "list[str]",
        "conclusion_para_gerencia": "str",
    }

    return {"prompt": prompt, "output_schema": output_schema}


# Registro de prompts por tipo — el servicio usa esta tabla para despachar.
PROMPT_REGISTRY = {
    "descripcion_brecha": prompt_descripcion_brecha,
    "interpretacion_michc": prompt_interpretacion_michc,
    "recomendacion_brecha": prompt_recomendacion_brecha,
    "informe_gerencial_reclutamiento": prompt_informe_gerencial_reclutamiento,
}
