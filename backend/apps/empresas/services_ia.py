import json
import logging
from django.conf import settings
from .utils_ciiu import buscar_por_codigo_768, serializar_para_prompt

logger = logging.getLogger(__name__)

class IAContextoService:

    @staticmethod
    def get_api_key():
        return getattr(settings, "ANTHROPIC_API_KEY", "")

    @classmethod
    def sugerir_identidad(cls, nombre, sector, ciiu_desc):
        api_key = cls.get_api_key()

        if not api_key:
            logger.info("[IAContextoService] ANTHROPIC_API_KEY no detectada. Usando Mock Inteligente.")
            identidad = cls.generar_identidad_mock(nombre, sector, ciiu_desc)
            return {"identidad": identidad, "fuente": "Mock Inteligente v2.0"}

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            prompt = (
                "Actúa como un consultor experto en planeación estratégica corporativa y salud y seguridad en el trabajo (SST).\n"
                f"Genera una propuesta de Misión, Visión y Valores Institucionales altamente profesional, moderna y personalizada para la siguiente empresa:\n"
                f"- Nombre: \"{nombre}\"\n"
                f"- Sector Económico: \"{sector or 'General'}\"\n"
                f"- Actividad Económica (CIIU): \"{ciiu_desc or 'No especificada'}\"\n\n"
                "Requisitos indispensables del formato:\n"
                "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, sin textos explicativos introductorios ni de cierre, con la siguiente estructura exacta:\n"
                "{\n"
                "  \"mision\": \"Texto fluido y aspiracional de la misión de 2 a 3 oraciones...\",\n"
                "  \"vision\": \"Texto proyectado a 2030 de la visión corporativa...\",\n"
                "  \"valores\": [\"Valor1\", \"Valor2\", \"Valor3\", \"Valor4\", \"Valor5\"]\n"
                "}\n\n"
                "Asegúrate de que los valores corporativos incluyan al menos uno explícitamente alineado con la SST (ej. Seguridad, Autocuidado, Prevención o Bienestar)."
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text if response.content else ""
            cleaned = text.strip()[text.find("{"):text.rfind("}") + 1]
            parsed = json.loads(cleaned)

            return {"identidad": parsed, "fuente": "Anthropic Claude"}
        except Exception as e:
            logger.error(f"[IAContextoService] Error llamando a Anthropic, usando fallback mock: {e}")
            identidad = cls.generar_identidad_mock(nombre, sector, ciiu_desc)
            return {"identidad": identidad, "fuente": "Mock Inteligente v2.0"}

    @classmethod
    def sugerir_procesos(cls, nombre, sector, ciiu_codigo, ciiu_desc):
        api_key = cls.get_api_key()

        if not api_key:
            logger.info("[IAContextoService] ANTHROPIC_API_KEY no detectada. Usando Mock Inteligente.")
            procesos = cls.generar_procesos_mock(sector, ciiu_codigo, ciiu_desc)
            return {"procesos": procesos, "fuente": "Mock Inteligente v2.0"}

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            prompt = (
                "Actúa como un experto consultor organizacional de procesos y sistemas de gestión integrados (ISO 9001, ISO 45001).\n"
                f"Diseña el mapa de procesos de primer nivel adecuado para la siguiente empresa:\n"
                f"- Nombre: \"{nombre}\"\n"
                f"- Sector: \"{sector or 'General'}\"\n"
                f"- Código CIIU: \"{ciiu_codigo or 'No especificado'}\"\n"
                f"- Descripción CIIU: \"{ciiu_desc or 'No especificada'}\"\n\n"
                "Genera una lista equilibrada de 6 a 9 procesos esenciales, clasificados rigurosamente en \"estrategico\", \"misional\" y \"apoyo\".\n"
                "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, sin textos explicativos introductorios ni de cierre, con la siguiente estructura exacta:\n"
                "{\n"
                "  \"procesos\": [\n"
                "    {\n"
                "      \"nombre\": \"Nombre claro del proceso (ej. Gestión de Calidad)\",\n"
                "      \"tipo\": \"estrategico\",\n"
                "      \"descripcion\": \"Descripción concisa de sus objetivos e impacto.\"\n"
                "    },\n"
                "    ...\n"
                "  ]\n"
                "}\n\n"
                "Clasificaciones aceptadas en \"tipo\": \"estrategico\" | \"misional\" | \"apoyo\"."
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.6,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text if response.content else ""
            cleaned = text.strip()[text.find("{"):text.rfind("}") + 1]
            parsed = json.loads(cleaned)

            return {"procesos": parsed.get("procesos", []), "fuente": "Anthropic Claude"}
        except Exception as e:
            logger.error(f"[IAContextoService] Error llamando a Anthropic, usando fallback mock: {e}")
            procesos = cls.generar_procesos_mock(sector, ciiu_codigo, ciiu_desc)
            return {"procesos": procesos, "fuente": "Mock Inteligente v2.0"}

    @classmethod
    def sugerir_codigo_ciiu(cls, nombre, sector, descripcion_actividad, candidatos):
        api_key = cls.get_api_key()

        if not api_key:
            logger.info("[IAContextoService] ANTHROPIC_API_KEY no detectada. Usando Mock Inteligente para CIIU.")
            sugerencia = cls.generar_sugerencia_ciiu_mock(nombre, sector, descripcion_actividad, candidatos)
            return {"sugerencia": sugerencia, "fuente": "Mock Inteligente v2.0"}

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            prompt = (
                "Actúa como un consultor experto en el Decreto 768 / CIIU Rev. 4 A.C. de Colombia y salud y seguridad en el trabajo (SST).\n"
                "Tu objetivo es sugerir la actividad económica principal y hasta 3 actividades económicas secundarias aplicables a partir del contexto de la empresa y una lista de códigos candidatos pre-filtrados.\n\n"
                "Empresa:\n"
                f"- Nombre: \"{nombre}\"\n"
                f"- Sector: \"{sector or 'General'}\"\n"
                f"- Descripción de actividad del usuario: \"{descripcion_actividad or 'No provista'}\"\n\n"
                "Códigos CIIU 768 Candidatos (JSON compacto):\n"
                f"{serializar_para_prompt(candidatos)}\n\n"
                "Requisitos del análisis:\n"
                "1. Analiza cuál de los códigos candidatos se ajusta mejor como la actividad principal de la empresa.\n"
                "2. Identifica si hay otras actividades secundarias complementarias y necesarias en la operación de la empresa dentro de los candidatos.\n"
                "3. Para cada actividad sugerida, redacta una justificación breve, clara y profesional en español de por qué aplica y su relación con el nivel de riesgo de la empresa.\n"
                "4. Si la lista de candidatos está vacía o ningún candidato aplica bien, selecciona el candidato más cercano e indica por qué.\n\n"
                "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, sin textos explicativos introductorios ni de cierre, con la siguiente estructura exacta:\n"
                "{\n"
                "  \"actividad_principal\": {\n"
                "    \"codigo_768\": \"código de 7 dígitos seleccionado de la lista\",\n"
                "    \"justificacion\": \"breve justificación de la selección...\"\n"
                "  },\n"
                "  \"actividades_secundarias\": [\n"
                "    {\n"
                "      \"codigo_768\": \"código de 7 dígitos seleccionado\",\n"
                "      \"justificacion\": \"breve justificación...\"\n"
                "    }\n"
                "  ]\n"
                "}"
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text if response.content else ""
            cleaned = text.strip()[text.find("{"):text.rfind("}") + 1]
            parsed = json.loads(cleaned)

            suggested_principal_code = parsed["actividad_principal"]["codigo_768"]
            catalog_principal = buscar_por_codigo_768(suggested_principal_code)
            enriched_principal = catalog_principal or next((c for c in candidatos if c["codigo_768"] == suggested_principal_code), None) or candidatos[0]

            activity_principal = {**enriched_principal, "justificacion": parsed["actividad_principal"]["justificacion"]}

            activities_secundarias = []
            for sec in parsed.get("actividades_secundarias", []):
                sec_code = sec["codigo_768"]
                catalog_sec = buscar_por_codigo_768(sec_code)
                enriched_sec = catalog_sec or next((c for c in candidatos if c["codigo_768"] == sec_code), None)
                if enriched_sec:
                    activities_secundarias.append({**enriched_sec, "justificacion": sec["justificacion"]})

            return {
                "sugerencia": {
                    "actividad_principal": activity_principal,
                    "actividades_secundarias": activities_secundarias,
                },
                "fuente": "Anthropic Claude"
            }
        except Exception as e:
            logger.error(f"[IAContextoService] Error llamando a Anthropic para sugerir CIIU, usando fallback: {e}")
            sugerencia = cls.generar_sugerencia_ciiu_mock(nombre, sector, descripcion_actividad, candidatos)
            return {"sugerencia": sugerencia, "fuente": "Mock Inteligente v2.0"}

    @classmethod
    def describir_codigo_ciiu(cls, nombre, sector, registro_principal, registros_secundarios):
        api_key = cls.get_api_key()

        if not api_key:
            logger.info("[IAContextoService] ANTHROPIC_API_KEY no detectada. Usando Mock Inteligente para descripción CIIU.")
            descripcion = cls.generar_descripcion_ciiu_mock(nombre, sector, registro_principal, registros_secundarios)
            return {"descripcion": descripcion, "fuente": "Mock Inteligente v2.0"}

        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)

            prompt = (
                "Actúa como un experto en salud y seguridad en el trabajo (SST) y normatividad laboral de Colombia (Decreto 768 / CIIU Rev. 4 A.C.).\n"
                "Tu objetivo es generar una descripción narrativa detallada y contextualizada para las actividades económicas de la empresa, relacionándolas con su operación y el sistema de gestión de seguridad y salud en el trabajo (SG-SST).\n\n"
                "Empresa:\n"
                f"- Nombre: \"{nombre}\"\n"
                f"- Sector: \"{sector or 'General'}\"\n\n"
                "Actividad Principal:\n"
                f"- Código: \"{registro_principal['codigo_768']}\" - \"{registro_principal['descripcion']}\" (Riesgo Clase {registro_principal['clase_riesgo']})\n"
                f"- Grupo: \"{registro_principal['grupo']}\"\n"
                f"- División: \"{registro_principal['division']}\"\n\n"
                "Actividades Secundarias:\n"
                f"{chr(10).join(['- Código: \"' + r['codigo_768'] + '\" - \"' + r['descripcion'] + '\" (Riesgo Clase ' + str(r['clase_riesgo']) + ')' for r in registros_secundarios]) or 'Ninguna'}\n\n"
                "Requisitos de la descripción:\n"
                f"Genera un análisis estructurado explicando el alcance de estas actividades en la empresa, los riesgos generales asociados (con base en la clase de riesgo de cada código) y consideraciones clave para el SG-SST (ej. exámenes médicos ocupacionales, controles principales, equipos de protección).\n"
                "La respuesta DEBE ser EXCLUSIVAMENTE un objeto JSON válido, con la siguiente estructura exacta:\n"
                "{\n"
                "  \"actividad_principal\": {\n"
                f"    \"codigo_768\": \"{registro_principal['codigo_768']}\",\n"
                f"    \"descripcion_contextualizada\": \"Análisis narrativo fluido y profesional (de 2 a 3 párrafos) conectando este código con las operaciones cotidianas de {nombre}, los principales factores de riesgo según la clase {registro_principal['clase_riesgo']} y el enfoque de prevención de SST.\"\n"
                "  },\n"
                "  \"actividades_secundarias\": [\n"
                f"    {','.join(['{\n      \"codigo_768\": \"' + r['codigo_768'] + '\",\n      \"descripcion_contextualizada\": \"Análisis contextualizado breve (1 párrafo) de cómo esta actividad complementa la principal y sus implicaciones preventivas.\"\n    }' for r in registros_secundarios])}\n"
                "  ]\n"
                "}"
            )

            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1200,
                temperature=0.4,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text if response.content else ""
            cleaned = text.strip()[text.find("{"):text.rfind("}") + 1]
            parsed = json.loads(cleaned)

            enriched_principal = {
                **registro_principal,
                "descripcion_contextualizada": parsed["actividad_principal"]["descripcion_contextualizada"]
            }

            enriched_secundarias = []
            for sec in parsed.get("actividades_secundarias", []):
                sec_code = sec["codigo_768"]
                matched_sec = next((r for r in registros_secundarios if r["codigo_768"] == sec_code), None)
                if matched_sec:
                    enriched_secundarias.append({
                        **matched_sec,
                        "descripcion_contextualizada": sec["descripcion_contextualizada"]
                    })

            return {
                "descripcion": {
                    "actividad_principal": enriched_principal,
                    "actividades_secundarias": enriched_secundarias
                },
                "fuente": "Anthropic Claude"
            }
        except Exception as e:
            logger.error(f"[IAContextoService] Error llamando a Anthropic para descripción CIIU: {e}")
            descripcion = cls.generar_descripcion_ciiu_mock(nombre, sector, registro_principal, registros_secundarios)
            return {"descripcion": descripcion, "fuente": "Mock Inteligente v2.0"}

    # --- MOCKS INTELIGENTES ---

    @staticmethod
    def generar_identidad_mock(nombre, sector, ciiu_desc):
        sec = (sector or "").lower()
        desc = (ciiu_desc or "").lower()
        clean_nombre = nombre or "Nuestra Organización"

        if "tecnologia" in sec or "software" in sec or "sistemas" in desc or "tecnolog" in desc or "informatic" in desc:
            return {
                "mision": f"Impulsar la transformación digital y competitividad de nuestros aliados estratégicos en {clean_nombre} a través del diseño, desarrollo e implementación de soluciones tecnológicas innovadoras, seguras y escalables que superen las expectativas de calidad y eficiencia operativa.",
                "vision": f"Ser reconocidos para el año 2030 como la compañía líder y referente regional en innovación tecnológica y consultoría en software, distinguiéndonos por la excelencia y bienestar de nuestro talento, la solidez de nuestras operaciones y una cultura organizacional enfocada en la seguridad y el crecimiento sostenible.",
                "valores": ["Innovación", "Seguridad Digital", "Excelencia Técnica", "Orientación al Cliente", "Bienestar y Prevención"]
            }

        if "construccion" in sec or "obras" in desc or "ingenieria" in desc or "edificac" in desc:
            return {
                "mision": f"Construir proyectos de infraestructura civil y edificación de la más alta calidad y solidez técnica en {clean_nombre}, aportando al desarrollo urbano y social mediante procesos seguros, eficientes y sostenibles, garantizando la absoluta protección y bienestar de nuestra fuerza laboral.",
                "vision": f"Consolidarnos en el año 2030 como la constructora de referencia nacional por su excelencia operativa, solidez financiera, cumplimiento riguroso en los plazos y por liderar la adopción de prácticas sostenibles y altos estándares de seguridad laboral y salud ocupacional.",
                "valores": ["Seguridad en Obra", "Integridad", "Calidad Constructiva", "Sostenibilidad", "Trabajo Colaborativo"]
            }

        if "salud" in sec or "medic" in desc or "clinica" in desc or "hospital" in desc:
            return {
                "mision": f"Brindar servicios integrales de salud en {clean_nombre} enfocados en la seguridad del paciente, la humanización del servicio y la excelencia clínica, apoyados en un equipo multidisciplinario altamente calificado y comprometido con la prevención de riesgos y la mejora de la calidad de vida de nuestra comunidad.",
                "vision": f"Ser reconocidos en el año 2030 como un centro de salud líder y de alta complejidad en la región, certificado bajo los más rigurosos estándares nacionales e internacionales de calidad médica, acreditación y seguridad ocupacional para el personal de la salud.",
                "valores": ["Humanización", "Seguridad del Paciente", "Compromiso Ético", "Autocuidado", "Calidad Asistencial"]
            }

        return {
            "mision": f"Ofrecer soluciones y servicios integrales de la más alta calidad en {clean_nombre}, orientados a satisfacer plenamente las necesidades de nuestros clientes mediante procesos eficientes, un equipo humano comprometido y el estricto cumplimiento de los estándares de seguridad, salud y cuidado ambiental.",
            "vision": f"Llegar al año 2030 siendo una organización altamente competitiva y consolidada en el mercado nacional, reconocida por su constante innovación, excelencia en la gestión del talento humano y un firme compromiso social enfocado en la prevención de riesgos laborales.",
            "valores": ["Responsabilidad", "Seguridad y Salud", "Calidad en el Servicio", "Transparencia", "Innovación Sostenible"]
        }

    @staticmethod
    def generar_procesos_mock(sector, ciiu_codigo, ciiu_desc):
        sec = (sector or "").lower()
        desc = (ciiu_desc or "").lower()
        cod = ciiu_codigo or ""

        if "tecnologia" in sec or "software" in sec or "sistemas" in desc or "tecnolog" in desc or "informatic" in desc or cod.startswith("62"):
            return [
                {
                    "nombre": "Gestión Estratégica e Innovación",
                    "tipo": "estrategico",
                    "descripcion": "Planificación corporativa a largo plazo, establecimiento de metas anuales y fomento de iniciativas de I+D tecnológica."
                },
                {
                    "nombre": "Gestión de Seguridad de la Información",
                    "tipo": "estrategico",
                    "descripcion": "Definición de políticas de ciberseguridad, resguardo de datos sensibles de clientes y cumplimiento normativo (ISO 27001)."
                },
                {
                    "nombre": "Desarrollo de Software y DevOps",
                    "tipo": "misional",
                    "descripcion": "Arquitectura de software, codificación, integración continua y despliegue automatizado de plataformas digitales."
                },
                {
                    "nombre": "Aseguramiento de la Calidad (QA Testing)",
                    "tipo": "misional",
                    "descripcion": "Ejecución de pruebas funcionales, automatizadas y de rendimiento para certificar entregas de software sin errores."
                },
                {
                    "nombre": "Soporte y Éxito del Cliente (Customer Success)",
                    "tipo": "misional",
                    "descripcion": "Mesa de ayuda técnica de segundo nivel, mantenimiento preventivo de plataformas y capacitación al cliente final."
                },
                {
                    "nombre": "Gestión del Talento de IT",
                    "tipo": "apoyo",
                    "descripcion": "Atracción de talento técnico, retención de ingenieros, capacitación continua y planes de carrera."
                },
                {
                    "nombre": "Gestión de Infraestructura Cloud",
                    "tipo": "apoyo",
                    "descripcion": "Aprovisionamiento y administración de recursos cloud (AWS, Azure o GCP) para soporte a operaciones de desarrollo."
                },
                {
                    "nombre": "Seguridad y Salud en el Trabajo (SST)",
                    "tipo": "apoyo",
                    "descripcion": "Prevención de riesgos ergonómicos (trabajo frente a pantallas), salud mental, pausas activas y programas de autocuidado."
                }
            ]

        if "construccion" in sec or "obras" in desc or "ingenieria" in desc or "edificac" in desc or cod.startswith("41") or cod.startswith("42") or cod.startswith("43"):
            return [
                {
                    "nombre": "Gestión Comercial y Planeación de Licitaciones",
                    "tipo": "estrategico",
                    "descripcion": "Búsqueda de oportunidades, análisis técnico-económico de pliegos y estructuración de ofertas ganadoras."
                },
                {
                    "nombre": "Gestión de Calidad, Seguridad y Medio Ambiente (HSEQ)",
                    "tipo": "estrategico",
                    "descripcion": "Garantía del cumplimiento de estándares de seguridad industrial en obra, salud ocupacional e impacto ambiental."
                },
                {
                    "nombre": "Diseño e Ingeniería de Proyectos",
                    "tipo": "misional",
                    "descripcion": "Cálculo estructural, planos arquitectónicos, especificaciones técnicas y modelado BIM."
                },
                {
                    "nombre": "Ejecución y Control de Obras",
                    "tipo": "misional",
                    "descripcion": "Operación directa en el terreno de construcción, cimentación, acabados y coordinación de cuadrillas de obra."
                },
                {
                    "nombre": "Gestión de Subcontratistas e Interventoría",
                    "tipo": "misional",
                    "descripcion": "Evaluación técnica, seguimiento de avances físicos e inspecciones reglamentarias de subcontratistas."
                },
                {
                    "nombre": "Compras y Logística de Insumos",
                    "tipo": "apoyo",
                    "descripcion": "Adquisición de concreto, acero y materiales, administración de inventarios en bodegas de obra."
                },
                {
                    "nombre": "Mantenimiento de Maquinaria y Equipos",
                    "tipo": "apoyo",
                    "descripcion": "Planes de mantenimiento preventivo y correctivo de grúas, excavadoras, herramientas mayores y menores."
                },
                {
                    "nombre": "Gestión de Talento Humano en Obra",
                    "tipo": "apoyo",
                    "descripcion": "Contratación de personal operativo, inducciones específicas de seguridad industrial y pago de nóminas."
                }
            ]

        return [
            {
                "nombre": "Planeación Estratégica y HSEQ",
                "tipo": "estrategico",
                "descripcion": "Establecimiento del rumbo corporativo, políticas de gestión integrada, calidad y prevención de riesgos."
            },
            {
                "nombre": "Producción y Operaciones",
                "tipo": "misional",
                "descripcion": "Transformación de insumos en productos terminados o prestación directa del servicio principal de la empresa."
            },
            {
                "nombre": "Comercialización y Ventas",
                "tipo": "misional",
                "descripcion": "Investigación de mercados, prospección de clientes, negociación y cierre de contratos comerciales."
            },
            {
                "nombre": "Servicio y Atención al Cliente",
                "tipo": "misional",
                "descripcion": "Gestión de requerimientos, soporte post-venta, resolución de peticiones, quejas y reclamos (PQR)."
            },
            {
                "nombre": "Gestión Administrativa y Financiera",
                "tipo": "apoyo",
                "descripcion": "Facturación, cobranzas, contabilidad general, tesorería y control de presupuestos operativos."
            },
            {
                "nombre": "Gestión del Talento Humano",
                "tipo": "apoyo",
                "descripcion": "Procesos de nómina, selección de personal, clima organizacional, bienestar y capacitación."
            },
            {
                "nombre": "Gestión de Seguridad y Salud en el Trabajo (SST)",
                "tipo": "apoyo",
                "descripcion": "Administración del SG-SST, investigación de incidentes, dotaciones, exámenes ocupacionales y comités COPASST."
            }
        ]

    @classmethod
    def generar_sugerencia_ciiu_mock(cls, nombre, sector, descripcion_actividad, candidatos):
        if not candidatos:
            return {
                "actividad_principal": {
                    "codigo_768": "6201001",
                    "clase_riesgo": 1,
                    "ciiu_rev4": "6201",
                    "descripcion": "Actividades de desarrollo de sistemas informáticos (planificación, análisis, diseño, programación, pruebas)",
                    "sector": "INFORMACIÓN Y COMUNICACIONES",
                    "division": "Actividades de servicios de información",
                    "grupo": "Desarrollo de sistemas informáticos",
                    "justificacion": "Código por defecto de soporte de desarrollo (Riesgo Clase 1) debido a la falta de candidatos."
                },
                "actividades_secundarias": []
            }

        principal = candidatos[0]
        activity_principal = {
            **principal,
            "justificacion": f"Código principal sugerido automáticamente con base al sector \"{principal['sector']}\" y la coincidencia directa con la descripción de actividad de la empresa. Representa el núcleo principal de la operación comercial de {nombre}."
        }

        activities_secundarias = []
        for c in candidatos[1:min(len(candidatos), 3)]:
            activities_secundarias.append({
                **c,
                "justificacion": f"Actividad complementaria identificada en la división \"{c['division']}\". Soporta los procesos operativos o de servicios de la actividad principal."
            })

        return {
            "actividad_principal": activity_principal,
            "actividades_secundarias": activities_secundarias
        }

    @classmethod
    def generar_descripcion_ciiu_mock(cls, nombre, sector, registro_principal, registros_secundarios):
        desc_principal = (
            f"La actividad económica principal de {nombre} bajo el código {registro_principal['codigo_768']} "
            f"({registro_principal['descripcion']}) abarca las operaciones clave del negocio en el sector de {registro_principal['sector']}. "
            f"Dado que esta actividad está clasificada en la Clase de Riesgo {registro_principal['clase_riesgo']}, "
            f"el SG-SST debe implementar controles y procedimientos específicos para los riesgos del grupo {registro_principal['grupo']}. "
            f"Se recomiendan inspecciones de seguridad periódicas, el diseño de puestos de trabajo ergonómicos y "
            f"capacitaciones sobre autocuidado para el control de los peligros prioritarios."
        )

        principal_enriched = {
            **registro_principal,
            "descripcion_contextualizada": desc_principal
        }

        secundarias_enriched = []
        for r in registros_secundarios:
            secundarias_enriched.append({
                **r,
                "descripcion_contextualizada": (
                    f"La actividad secundaria con código {r['codigo_768']} ({r['descripcion']}) actúa como complemento a la principal. "
                    f"Con una Clase de Riesgo {r['clase_riesgo']}, introduce riesgos operativos adicionales en la división {r['division']}, "
                    f"requiriendo inducciones específicas y equipo de protección personal adecuado para los trabajadores asignados a esta área."
                )
            })

        return {
            "actividad_principal": principal_enriched,
            "actividades_secundarias": secundarias_enriched
        }
