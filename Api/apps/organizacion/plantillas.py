# Plantillas normativas institucionales del Mapa de Procesos SG-SST

PLANTILLAS_SGSST = {
    "estandar": {
        "id": "estandar",
        "nombre": "Estándar SG-SST (Decreto 1072 / Res. 0312 de 2019)",
        "descripcion": "Estructura integral de 12 procesos clave para empresas de 11 a 50+ trabajadores.",
        "procesos": [
            {
                "nombre": "Direccionamiento Estratégico y Liderazgo SST",
                "tipo": "estrategico",
                "descripcion": "Definición de política, objetivos y asignación de recursos anuales.",
                "subprocesos": [
                    "Política y Objetivos SST",
                    "Rendición de Cuentas",
                    "Asignación de Recursos Anuales",
                ],
            },
            {
                "nombre": "Auditoría y Revisión por la Alta Dirección",
                "tipo": "estrategico",
                "descripcion": "Evaluación periódica del cumplimiento del SG-SST y planes de mejora.",
                "subprocesos": [
                    "Auditoría Interna del SG-SST",
                    "Revisión por la Dirección",
                    "Planes Correctivos",
                ],
            },
            {
                "nombre": "Identificación de Peligros y Valoración de Riesgos",
                "tipo": "misional",
                "descripcion": "Metodología GTC 45, inspecciones de seguridad y controles jerárquicos.",
                "subprocesos": [
                    "Matriz GTC 45",
                    "Inspecciones Planeadas",
                    "Jerarquía de Controles",
                ],
            },
            {
                "nombre": "Medicina Preventiva y Vigilancia Epidemiológica",
                "tipo": "misional",
                "descripcion": "Evaluaciones médicas ocupacionales y sistemas SVE.",
                "subprocesos": [
                    "Profesiogramas y Exámenes",
                    "Sistemas SVE",
                ],
            },
            {
                "nombre": "Control Operacional y Tareas de Alto Riesgo",
                "tipo": "misional",
                "descripcion": "Permisos de trabajo seguro en alturas, confinados, caliente.",
                "subprocesos": [
                    "Permisos de Trabajo",
                    "Análisis ATS",
                    "Inspección de EPP",
                ],
            },
            {
                "nombre": "Preparación y Respuesta ante Emergencias",
                "tipo": "misional",
                "descripcion": "Plan de emergencias, brigadas, señalización y simulacros.",
                "subprocesos": [
                    "Plan de Emergencias",
                    "Capacitación Brigadistas",
                    "Simulacros",
                ],
            },
            {
                "nombre": "Formación, Inducción y Competencias SST",
                "tipo": "apoyo",
                "descripcion": "Plan anual de capacitación e inducción.",
                "subprocesos": [
                    "Inducción en SST",
                    "Plan Anual de Capacitación",
                ],
            },
            {
                "nombre": "Gestión Documental y Control de Evidencias",
                "tipo": "apoyo",
                "descripcion": "Custodia, retención por 20 años y control de versiones.",
                "subprocesos": [
                    "Control de Registros",
                    "Custodia de Historias Ocupacionales",
                ],
            },
        ],
    },
    "alto_riesgo": {
        "id": "alto_riesgo",
        "nombre": "Sector Industrial / Construcción / Alto Riesgo",
        "descripcion": "Enfocado en control estricto de energías, frentes de obra y tareas críticas.",
        "procesos": [
            {
                "nombre": "Gobierno Corporativo y Cultura de Seguridad",
                "tipo": "estrategico",
                "descripcion": "Liderazgo en campo y comités de seguridad.",
                "subprocesos": [
                    "Liderazgo Visible",
                    "Comités de Seguridad",
                ],
            },
            {
                "nombre": "Gestión de Riesgos Críticos",
                "tipo": "misional",
                "descripcion": "Control exhaustivo de tareas críticas (alturas, izaje, excavaciones).",
                "subprocesos": [
                    "Permisos de Trabajo Crítico",
                    "Procedimientos POE",
                ],
            },
            {
                "nombre": "Mantenimiento e Inspecciones Técnicas",
                "tipo": "apoyo",
                "descripcion": "Certificación de maquinaria pesada y calibración.",
                "subprocesos": [
                    "Certificación de Equipos",
                    "Calibración de Instrumentos",
                ],
            },
        ],
    },
}
