"""
Siembra datos de prueba para Reclutamiento y Selección.

Crea en la empresa indicada:
  - 10 perfiles de cargo completos (PC-2026-0201..0210).
  - 1 vacante de prueba con su proceso de selección.
  - 20 candidatos/postulaciones con estados, documentos y etapas variadas.

Uso:
    python manage.py seed_pruebas_reclutamiento --nit 900000000
    python manage.py seed_pruebas_reclutamiento --nit 900000000 --reset
"""
import hashlib
import io
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from apps.accounts.models import Usuario
from apps.empresas.models import Empresa
from apps.evidencias.models import Archivo
from apps.organizacion.models import Sede
from apps.perfilcargo.models import (
    CargoCompetencia,
    CargoFuncion,
    CargoIndicador,
    CargoResponsabilidad,
    CargoVersion,
    NivelCriticidad,
    PerfilCargo,
    TipoCargo,
)
from apps.reclutamiento.models import (
    Candidato,
    CandidatoDocumento,
    Entrevista,
    Evaluacion,
    FuenteReclutamiento,
    PerfilCandidato,
    Postulacion,
    PostulacionEvento,
    ProcesoSeleccion,
    Vacante,
    ValidacionDocumental,
)
from apps.reclutamiento.services.portal import _guardar_documento_candidato

TITULO_VACANTE = "[PRUEBAS] Analista de Gestión Humana"
PERFIL_VACANTE = "PC-2026-0201"
DOCS_REQUERIDOS = [
    CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA,
    CandidatoDocumento.TipoDocumento.CEDULA,
    CandidatoDocumento.TipoDocumento.CERTIFICACION_LABORAL,
]
TITULO_VACANTE_TIC = "[PRUEBAS] Ingeniero de Soporte TI"
PERFIL_VACANTE_TIC = "PC-2026-0210"
DOCS_REQUERIDOS_TIC = [
    CandidatoDocumento.TipoDocumento.HOJA_DE_VIDA,
    CandidatoDocumento.TipoDocumento.CEDULA,
    CandidatoDocumento.TipoDocumento.CERTIFICACION_ACADEMICA,
]
DOC_LABELS = dict(CandidatoDocumento.TipoDocumento.choices)

PERFILES = [
    {
        "codigo": "PC-2026-0201",
        "nombre_cargo": "Analista de Gestión Humana",
        "area": "Gestión Humana",
        "tipo_cargo": TipoCargo.ADMINISTRATIVO,
        "nivel_riesgo": 1,
        "proposito": "Ejecutar los procesos de atracción, selección, contratación, formación y bienestar del talento, garantizando el cumplimiento normativo y un adecuado clima laboral.",
        "educacion": "Profesional en Administración de Empresas, Psicología, Ingeniería Industrial o afines.",
        "experiencia": "Mínimo 1 año en procesos de talento humano o gestión humana.",
        "formacion": "Excel intermedio, normatividad laboral colombiana y SG-SST (deseable).",
        "habilidades": "Comunicación asertiva, organización, confidencialidad, negociación y manejo de Excel.",
        "criticidades": {"sst": NivelCriticidad.BAJO, "operacional": NivelCriticidad.MEDIO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.BAJO, "estrategica": NivelCriticidad.ALTO},
        "requiere_suplencia": True,
        "cargo_critico": False,
        "funciones": [
            "Ejecutar el proceso de reclutamiento y selección de personal.",
            "Apoyar la liquidación de nómina y las novedades de personal.",
            "Coordinar inducción, reinducción y plan de capacitación.",
            "Mantener actualizados los expedientes y la documentación laboral.",
        ],
        "responsabilidades": [
            "Garantizar la confidencialidad de la información de los colaboradores.",
            "Cumplir la normatividad laboral y de protección de datos.",
            "Reportar oportunamente los indicadores de gestión humana.",
        ],
        "competencias": [
            ("Gestión del talento", CargoCompetencia.Tipo.TECNICA, 3),
            ("Comunicación asertiva", CargoCompetencia.Tipo.BLANDA, 3),
            ("Excel intermedio", CargoCompetencia.Tipo.TECNICA, 2),
            ("Normatividad laboral", CargoCompetencia.Tipo.TECNICA, 3),
        ],
        "indicador": ("Rotación mensual de personal", "< 5%"),
    },
    {
        "codigo": "PC-2026-0202",
        "nombre_cargo": "Auxiliar Contable",
        "area": "Financiera",
        "tipo_cargo": TipoCargo.ADMINISTRATIVO,
        "nivel_riesgo": 1,
        "proposito": "Registrar y conciliar las operaciones contables, garantizando información financiera oportuna y confiable.",
        "educacion": "Técnico o tecnólogo en contabilidad y finanzas.",
        "experiencia": "Mínimo 1 año como auxiliar contable.",
        "formacion": "Manejo de software contable y Excel intermedio.",
        "habilidades": "Atención al detalle, organización y ética profesional.",
        "criticidades": {"sst": NivelCriticidad.BAJO, "operacional": NivelCriticidad.MEDIO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.BAJO, "estrategica": NivelCriticidad.MEDIO},
        "requiere_suplencia": False,
        "cargo_critico": False,
        "funciones": [
            "Causar facturas, comprobantes y documentos contables.",
            "Realizar conciliaciones bancarias y de cuentas auxiliares.",
            "Organizar y archivar los soportes contables.",
            "Apoyar la preparación de información para impuestos.",
        ],
        "responsabilidades": [
            "Cumplir los plazos de cierre contable.",
            "Proteger la confidencialidad de la información financiera.",
            "Reportar diferencias o inconsistencias oportunamente.",
        ],
        "competencias": [
            ("Contabilidad general", CargoCompetencia.Tipo.TECNICA, 3),
            ("Excel intermedio", CargoCompetencia.Tipo.TECNICA, 3),
            ("Atención al detalle", CargoCompetencia.Tipo.BLANDA, 3),
        ],
        "indicador": ("Conciliaciones bancarias al día", "100%"),
    },
    {
        "codigo": "PC-2026-0203",
        "nombre_cargo": "Coordinador de SST",
        "area": "Seguridad y Salud en el Trabajo",
        "tipo_cargo": TipoCargo.ADMINISTRATIVO,
        "nivel_riesgo": 3,
        "proposito": "Diseñar, implementar y mantener el Sistema de Gestión de Seguridad y Salud en el Trabajo, previniendo accidentes y enfermedades laborales.",
        "educacion": "Profesional en Seguridad y Salud en el Trabajo, Ingeniería Industrial o afines con licencia vigente.",
        "experiencia": "Mínimo 3 años en coordinación de SG-SST.",
        "formacion": "Licencia en SST, curso de 50 horas y GTC 45.",
        "habilidades": "Liderazgo, análisis de riesgos, comunicación y seguimiento.",
        "criticidades": {"sst": NivelCriticidad.ALTO, "operacional": NivelCriticidad.ALTO, "vial": NivelCriticidad.MEDIO, "ambiental": NivelCriticidad.MEDIO, "estrategica": NivelCriticidad.ALTO},
        "requiere_suplencia": True,
        "cargo_critico": True,
        "funciones": [
            "Actualizar la matriz de peligros y valoración de riesgos.",
            "Ejecutar el plan anual de capacitación y sensibilización.",
            "Realizar auditorías e inspecciones de seguridad.",
            "Investigar incidentes y accidentes de trabajo.",
        ],
        "responsabilidades": [
            "Garantizar el cumplimiento legal en materia de SST.",
            "Reportar los indicadores de seguridad a la gerencia.",
            "Verificar el uso y suministro de elementos de protección personal.",
        ],
        "competencias": [
            ("SG-SST", CargoCompetencia.Tipo.TECNICA, 4),
            ("GTC 45", CargoCompetencia.Tipo.TECNICA, 3),
            ("Liderazgo", CargoCompetencia.Tipo.BLANDA, 3),
            ("Gestión de riesgos", CargoCompetencia.Tipo.TECNICA, 3),
        ],
        "indicador": ("Cumplimiento del plan de trabajo anual", ">= 95%"),
    },
    {
        "codigo": "PC-2026-0204",
        "nombre_cargo": "Operario de Producción",
        "area": "Producción",
        "tipo_cargo": TipoCargo.OPERATIVO,
        "nivel_riesgo": 4,
        "proposito": "Ejecutar las operaciones de producción conforme a los procedimientos, estándares de calidad y normas de seguridad.",
        "educacion": "Bachiller académico.",
        "experiencia": "Mínimo 6 meses en plantas de producción.",
        "formacion": "Inducción en maquinaria y trabajo seguro.",
        "habilidades": "Trabajo en equipo, atención y cumplimiento de instrucciones.",
        "criticidades": {"sst": NivelCriticidad.ALTO, "operacional": NivelCriticidad.ALTO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.MEDIO, "estrategica": NivelCriticidad.BAJO},
        "requiere_suplencia": False,
        "cargo_critico": True,
        "funciones": [
            "Operar máquinas y equipos de producción.",
            "Verificar la calidad del producto en proceso.",
            "Mantener el orden y aseo del puesto de trabajo.",
            "Reportar novedades de producción y mantenimiento.",
        ],
        "responsabilidades": [
            "Usar correctamente los elementos de protección personal.",
            "Cumplir los procedimientos y estándares de calidad.",
            "Cuidar los equipos y herramientas asignados.",
        ],
        "competencias": [
            ("Operación de maquinaria", CargoCompetencia.Tipo.TECNICA, 2),
            ("Trabajo en equipo", CargoCompetencia.Tipo.BLANDA, 3),
            ("Seguridad industrial", CargoCompetencia.Tipo.TECNICA, 3),
        ],
        "indicador": ("Cumplimiento de la meta de producción", ">= 95%"),
    },
    {
        "codigo": "PC-2026-0205",
        "nombre_cargo": "Auxiliar de Bodega",
        "area": "Logística",
        "tipo_cargo": TipoCargo.OPERATIVO,
        "nivel_riesgo": 3,
        "proposito": "Recibir, almacenar y despachar mercancías, manteniendo la exactitud del inventario y las condiciones de seguridad.",
        "educacion": "Bachiller académico.",
        "experiencia": "Mínimo 1 año en bodega o manejo de inventarios.",
        "formacion": "Manejo de inventarios y montacargas (deseable).",
        "habilidades": "Organización, agilidad y responsabilidad.",
        "criticidades": {"sst": NivelCriticidad.MEDIO, "operacional": NivelCriticidad.ALTO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.BAJO, "estrategica": NivelCriticidad.BAJO},
        "requiere_suplencia": False,
        "cargo_critico": False,
        "funciones": [
            "Recibir y verificar la mercancía contra documentos.",
            "Ubicar y organizar los productos en el almacén.",
            "Alistar y despachar pedidos.",
            "Participar en los inventarios físicos.",
        ],
        "responsabilidades": [
            "Mantener la exactitud del inventario.",
            "Conservar el orden y la limpieza del área.",
            "Cumplir las normas de seguridad y uso de EPP.",
        ],
        "competencias": [
            ("Gestión de inventarios", CargoCompetencia.Tipo.TECNICA, 3),
            ("Organización", CargoCompetencia.Tipo.BLANDA, 3),
            ("Operación de montacargas", CargoCompetencia.Tipo.TECNICA, 2),
        ],
        "indicador": ("Exactitud de inventario", ">= 98%"),
    },
    {
        "codigo": "PC-2026-0206",
        "nombre_cargo": "Conductor de Reparto",
        "area": "Logística",
        "tipo_cargo": TipoCargo.OPERATIVO,
        "nivel_riesgo": 4,
        "proposito": "Transportar y entregar mercancías de forma segura y oportuna, cumpliendo la normatividad vial y el PESV.",
        "educacion": "Bachiller académico con licencia de conducción C2 vigente.",
        "experiencia": "Mínimo 2 años conduciendo vehículos de reparto.",
        "formacion": "Curso de conducción defensiva y PESV.",
        "habilidades": "Conducción segura, servicio al cliente y orientación.",
        "criticidades": {"sst": NivelCriticidad.ALTO, "operacional": NivelCriticidad.MEDIO, "vial": NivelCriticidad.CRITICO, "ambiental": NivelCriticidad.MEDIO, "estrategica": NivelCriticidad.BAJO},
        "requiere_suplencia": False,
        "cargo_critico": True,
        "funciones": [
            "Realizar las entregas asignadas en las rutas establecidas.",
            "Revisar el estado del vehículo antes y después de la ruta.",
            "Diligenciar los documentos de transporte.",
            "Reportar novedades mecánicas o de tránsito.",
        ],
        "responsabilidades": [
            "Cumplir las normas de tránsito y el PESV.",
            "Cuidar la carga y los documentos a cargo.",
            "Brindar un trato adecuado al cliente.",
        ],
        "competencias": [
            ("Conducción segura", CargoCompetencia.Tipo.TECNICA, 3),
            ("Servicio al cliente", CargoCompetencia.Tipo.BLANDA, 3),
            ("Conocimiento de rutas", CargoCompetencia.Tipo.TECNICA, 2),
        ],
        "indicador": ("Entregas a tiempo", ">= 95%"),
    },
    {
        "codigo": "PC-2026-0207",
        "nombre_cargo": "Técnico de Mantenimiento",
        "area": "Mantenimiento",
        "tipo_cargo": TipoCargo.OPERATIVO,
        "nivel_riesgo": 4,
        "proposito": "Ejecutar el mantenimiento preventivo y correctivo de equipos e instalaciones, asegurando su disponibilidad y operación segura.",
        "educacion": "Técnico en electricidad, mecánica o mantenimiento.",
        "experiencia": "Mínimo 2 años en mantenimiento industrial.",
        "formacion": "Electricidad básica, mecánica y trabajo en alturas (deseable).",
        "habilidades": "Diagnóstico, trabajo en equipo y seguridad.",
        "criticidades": {"sst": NivelCriticidad.ALTO, "operacional": NivelCriticidad.ALTO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.MEDIO, "estrategica": NivelCriticidad.MEDIO},
        "requiere_suplencia": True,
        "cargo_critico": True,
        "funciones": [
            "Ejecutar rutinas de mantenimiento preventivo.",
            "Atender correctivos y diagnosticar fallas.",
            "Registrar las órdenes de trabajo en el sistema.",
            "Controlar el inventario de repuestos.",
        ],
        "responsabilidades": [
            "Cumplir las normas de seguridad y bloqueo de energías.",
            "Mantener la disponibilidad de los equipos.",
            "Reportar las actividades realizadas.",
        ],
        "competencias": [
            ("Mantenimiento preventivo", CargoCompetencia.Tipo.TECNICA, 3),
            ("Electricidad básica", CargoCompetencia.Tipo.TECNICA, 2),
            ("Trabajo en alturas", CargoCompetencia.Tipo.TECNICA, 2),
            ("Seguridad industrial", CargoCompetencia.Tipo.TECNICA, 3),
        ],
        "indicador": ("Disponibilidad de equipos", ">= 95%"),
    },
    {
        "codigo": "PC-2026-0208",
        "nombre_cargo": "Asesor Comercial",
        "area": "Comercial",
        "tipo_cargo": TipoCargo.ADMINISTRATIVO,
        "nivel_riesgo": 1,
        "proposito": "Gestionar la relación con clientes, identificar oportunidades de negocio y cumplir las metas comerciales.",
        "educacion": "Tecnólogo o profesional en mercadeo, administración o afines.",
        "experiencia": "Mínimo 1 año en ventas o atención comercial.",
        "formacion": "Manejo de CRM, técnicas de venta y negociación.",
        "habilidades": "Negociación, comunicación y orientación a metas.",
        "criticidades": {"sst": NivelCriticidad.BAJO, "operacional": NivelCriticidad.MEDIO, "vial": NivelCriticidad.MEDIO, "ambiental": NivelCriticidad.BAJO, "estrategica": NivelCriticidad.ALTO},
        "requiere_suplencia": False,
        "cargo_critico": False,
        "funciones": [
            "Realizar prospección y captación de clientes.",
            "Elaborar cotizaciones y presentaciones comerciales.",
            "Hacer seguimiento a las oportunidades y al cierre.",
            "Atender la postventa y las solicitudes del cliente.",
        ],
        "responsabilidades": [
            "Cumplir las metas comerciales asignadas.",
            "Reportar la gestión en el CRM.",
            "Mantener la confidencialidad de la información comercial.",
        ],
        "competencias": [
            ("Ventas", CargoCompetencia.Tipo.TECNICA, 3),
            ("Negociación", CargoCompetencia.Tipo.BLANDA, 3),
            ("Manejo de CRM", CargoCompetencia.Tipo.TECNICA, 2),
        ],
        "indicador": ("Cumplimiento de la meta comercial", ">= 100%"),
    },
    {
        "codigo": "PC-2026-0209",
        "nombre_cargo": "Auxiliar de Servicios Generales",
        "area": "Administrativa",
        "tipo_cargo": TipoCargo.APOYO,
        "nivel_riesgo": 2,
        "proposito": "Mantener las condiciones de aseo, orden y bioseguridad en las instalaciones de la empresa.",
        "educacion": "Primaria o bachillerato.",
        "experiencia": "Mínimo 6 meses en servicios generales.",
        "formacion": "Bioseguridad, manejo de residuos y productos de limpieza.",
        "habilidades": "Responsabilidad, orden y servicio.",
        "criticidades": {"sst": NivelCriticidad.MEDIO, "operacional": NivelCriticidad.BAJO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.MEDIO, "estrategica": NivelCriticidad.BAJO},
        "requiere_suplencia": False,
        "cargo_critico": False,
        "funciones": [
            "Realizar el aseo y desinfección de las áreas asignadas.",
            "Apoyar el servicio de cafetería.",
            "Clasificar y disponer los residuos.",
            "Reportar daños o necesidades de insumos.",
        ],
        "responsabilidades": [
            "Cumplir las normas de bioseguridad.",
            "Usar adecuadamente los insumos de limpieza.",
            "Mantener el orden de las áreas comunes.",
        ],
        "competencias": [
            ("Aseo y desinfección", CargoCompetencia.Tipo.TECNICA, 2),
            ("Manejo de residuos", CargoCompetencia.Tipo.TECNICA, 2),
            ("Servicio", CargoCompetencia.Tipo.BLANDA, 3),
        ],
        "indicador": ("Cumplimiento del plan de aseo", ">= 95%"),
    },
    {
        "codigo": "PC-2026-0210",
        "nombre_cargo": "Ingeniero de Soporte TI",
        "area": "Tecnología",
        "tipo_cargo": TipoCargo.ADMINISTRATIVO,
        "nivel_riesgo": 1,
        "proposito": "Brindar soporte técnico y mantener la infraestructura tecnológica, garantizando disponibilidad, seguridad y continuidad.",
        "educacion": "Profesional en Ingeniería de Sistemas, Software o afines.",
        "experiencia": "Mínimo 2 años en soporte TI e infraestructura.",
        "formacion": "Redes, Windows/Linux y ciberseguridad básica.",
        "habilidades": "Análisis, servicio y documentación.",
        "criticidades": {"sst": NivelCriticidad.BAJO, "operacional": NivelCriticidad.ALTO, "vial": NivelCriticidad.BAJO, "ambiental": NivelCriticidad.BAJO, "estrategica": NivelCriticidad.ALTO},
        "requiere_suplencia": True,
        "cargo_critico": False,
        "funciones": [
            "Atender las solicitudes de soporte de los usuarios.",
            "Administrar la red y los servidores.",
            "Ejecutar y verificar los respaldos de información.",
            "Mantener el inventario tecnológico actualizado.",
        ],
        "responsabilidades": [
            "Garantizar la disponibilidad de los servicios TI.",
            "Proteger la confidencialidad de la información.",
            "Documentar las soluciones e incidencias.",
        ],
        "competencias": [
            ("Soporte técnico", CargoCompetencia.Tipo.TECNICA, 3),
            ("Redes", CargoCompetencia.Tipo.TECNICA, 3),
            ("Ciberseguridad básica", CargoCompetencia.Tipo.TECNICA, 2),
        ],
        "indicador": ("Tiempo medio de resolución", "<= 4 horas"),
    },
]

CANDIDATOS = [
    {
        "documento": "9900000001", "nombres": "Laura", "apellidos": "Gómez",
        "email": "laura.gomez.prueba@fosst-test.com", "telefono": "3001000001",
        "ciudad": "Popayán", "departamento": "Cauca",
        "nivel": "universitario", "titulo": "Administradora de Empresas",
        "experiencia": "3.0", "competencias": ["Gestión del talento", "Excel intermedio", "Comunicación asertiva"],
        "fuente": "LinkedIn", "estado": "postulado", "docs": 0, "score": None,
        "etapas": [], "motivo": "", "dias": 3,
    },
    {
        "documento": "9900000002", "nombres": "Carlos", "apellidos": "Ramírez",
        "email": "carlos.ramirez.prueba@fosst-test.com", "telefono": "3001000002",
        "ciudad": "Cali", "departamento": "Valle del Cauca",
        "nivel": "tecnologo", "titulo": "Tecnólogo en Gestión Humana",
        "experiencia": "1.5", "competencias": ["Gestión del talento", "Nómina", "Atención al cliente"],
        "fuente": "Computrabajo", "estado": "postulado", "docs": 1, "score": None,
        "etapas": [], "motivo": "", "dias": 5,
    },
    {
        "documento": "9900000003", "nombres": "Andrea", "apellidos": "Muñoz",
        "email": "andrea.munoz.prueba@fosst-test.com", "telefono": "3001000003",
        "ciudad": "Bogotá", "departamento": "Cundinamarca",
        "nivel": "tecnico", "titulo": "Técnica en Talento Humano",
        "experiencia": "1.0", "competencias": ["Archivo", "Excel intermedio", "Comunicación asertiva"],
        "fuente": "Portal Web", "estado": "postulado", "docs": 0, "score": None,
        "etapas": [], "motivo": "", "dias": 7,
    },
    {
        "documento": "9900000004", "nombres": "Felipe", "apellidos": "Torres",
        "email": "felipe.torres.prueba@fosst-test.com", "telefono": "3001000004",
        "ciudad": "Pasto", "departamento": "Nariño",
        "nivel": "universitario", "titulo": "Psicólogo",
        "experiencia": "2.0", "competencias": ["Entrevistas", "Comunicación asertiva", "Gestión del talento"],
        "fuente": "Referido", "estado": "postulado", "docs": 2, "score": None,
        "etapas": [], "motivo": "", "dias": 9,
    },
    {
        "documento": "9900000005", "nombres": "Diana", "apellidos": "Castro",
        "email": "diana.castro.prueba@fosst-test.com", "telefono": "3001000005",
        "ciudad": "Medellín", "departamento": "Antioquia",
        "nivel": "especializacion", "titulo": "Especialista en Gestión Humana",
        "experiencia": "6.0", "competencias": ["Gestión del talento", "Normatividad laboral", "Liderazgo"],
        "fuente": "LinkedIn", "estado": "en_revision", "docs": 3, "score": None,
        "etapas": [], "motivo": "", "dias": 12,
    },
    {
        "documento": "9900000006", "nombres": "Jorge", "apellidos": "Herrera",
        "email": "jorge.herrera.prueba@fosst-test.com", "telefono": "3001000006",
        "ciudad": "Manizales", "departamento": "Caldas",
        "nivel": "bachillerato", "titulo": "Bachiller Académico",
        "experiencia": "0.5", "competencias": ["Archivo", "Atención al cliente", "Excel básico"],
        "fuente": "Servicio Público de Empleo", "estado": "en_revision", "docs": 1, "score": None,
        "etapas": [], "motivo": "", "dias": 14,
    },
    {
        "documento": "9900000007", "nombres": "Camila", "apellidos": "Rojas",
        "email": "camila.rojas.prueba@fosst-test.com", "telefono": "3001000007",
        "ciudad": "Pereira", "departamento": "Risaralda",
        "nivel": "universitario", "titulo": "Administradora de Empresas",
        "experiencia": "2.5", "competencias": ["Nómina", "Excel intermedio", "Gestión del talento"],
        "fuente": "Computrabajo", "estado": "en_revision", "docs": 2, "score": None,
        "etapas": [], "motivo": "", "dias": 16,
    },
    {
        "documento": "9900000008", "nombres": "Sebastián", "apellidos": "Vargas",
        "email": "sebastian.vargas.prueba@fosst-test.com", "telefono": "3001000008",
        "ciudad": "Tunja", "departamento": "Boyacá",
        "nivel": "universitario", "titulo": "Ingeniero Industrial",
        "experiencia": "3.0", "competencias": ["Gestión del talento", "Indicadores", "Excel intermedio"],
        "fuente": "Portal Web", "estado": "preseleccionado", "docs": 3, "score": 80,
        "etapas": [], "motivo": "", "dias": 18,
    },
    {
        "documento": "9900000009", "nombres": "Valentina", "apellidos": "López",
        "email": "valentina.lopez.prueba@fosst-test.com", "telefono": "3001000009",
        "ciudad": "Neiva", "departamento": "Huila",
        "nivel": "tecnologo", "titulo": "Tecnóloga en Gestión Humana",
        "experiencia": "2.0", "competencias": ["Reclutamiento", "Comunicación asertiva", "Nómina"],
        "fuente": "Referido", "estado": "preseleccionado", "docs": 2, "score": 76,
        "etapas": [], "motivo": "", "dias": 20,
    },
    {
        "documento": "9900000010", "nombres": "Andrés", "apellidos": "Mejía",
        "email": "andres.mejia.prueba@fosst-test.com", "telefono": "3001000010",
        "ciudad": "Villavicencio", "departamento": "Meta",
        "nivel": "tecnico", "titulo": "Técnico en Recursos Humanos",
        "experiencia": "1.5", "competencias": ["Archivo", "Atención al cliente", "Excel intermedio"],
        "fuente": "Servicio Público de Empleo", "estado": "preseleccionado", "docs": 1, "score": 72,
        "etapas": [], "motivo": "", "dias": 22,
    },
    {
        "documento": "9900000011", "nombres": "Paola", "apellidos": "Cárdenas",
        "email": "paola.cardenas.prueba@fosst-test.com", "telefono": "3001000011",
        "ciudad": "Popayán", "departamento": "Cauca",
        "nivel": "universitario", "titulo": "Psicóloga",
        "experiencia": "4.0", "competencias": ["Entrevistas", "Gestión del talento", "Comunicación asertiva"],
        "fuente": "LinkedIn", "estado": "en_entrevista", "docs": 3, "score": 85,
        "etapas": ["entrevista"], "motivo": "", "dias": 24,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 85, "offset": 14, "observaciones": "Cumple con las competencias y la experiencia requerida."},
    },
    {
        "documento": "9900000012", "nombres": "Julián", "apellidos": "Ospina",
        "email": "julian.ospina.prueba@fosst-test.com", "telefono": "3001000012",
        "ciudad": "Cali", "departamento": "Valle del Cauca",
        "nivel": "universitario", "titulo": "Administrador de Empresas",
        "experiencia": "3.0", "competencias": ["Gestión del talento", "Normatividad laboral", "Excel intermedio"],
        "fuente": "Computrabajo", "estado": "en_entrevista", "docs": 3, "score": None,
        "etapas": [], "motivo": "", "dias": 26,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.INICIAL_RH, "estado": Entrevista.Estado.PROGRAMADA, "concepto": Entrevista.Concepto.PENDIENTE, "calificacion": None, "offset": 30, "observaciones": "Entrevista programada con el candidato."},
    },
    {
        "documento": "9900000013", "nombres": "Natalia", "apellidos": "Salazar",
        "email": "natalia.salazar.prueba@fosst-test.com", "telefono": "3001000013",
        "ciudad": "Bogotá", "departamento": "Cundinamarca",
        "nivel": "tecnologo", "titulo": "Tecnóloga en Gestión Humana",
        "experiencia": "2.0", "competencias": ["Reclutamiento", "Nómina", "Atención al cliente"],
        "fuente": "Portal Web", "estado": "en_entrevista", "docs": 2, "score": 72,
        "etapas": ["entrevista"], "motivo": "", "dias": 28,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.CON_RESERVAS, "calificacion": 72, "offset": 12, "observaciones": "Requiere refuerzo en normatividad laboral."},
    },
    {
        "documento": "9900000014", "nombres": "Ricardo", "apellidos": "Peña",
        "email": "ricardo.pena.prueba@fosst-test.com", "telefono": "3001000014",
        "ciudad": "Pasto", "departamento": "Nariño",
        "nivel": "universitario", "titulo": "Administrador Público",
        "experiencia": "5.0", "competencias": ["Gestión del talento", "Normatividad laboral", "Indicadores"],
        "fuente": "Referido", "estado": "en_evaluacion", "docs": 3, "score": 82,
        "etapas": ["entrevista", "evaluacion"], "motivo": "", "dias": 30,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 80, "offset": 15, "observaciones": "Buen conocimiento del marco laboral."},
        "evaluacion": {"tipo": Evaluacion.TipoEvaluacion.TECNICA, "nombre": "Prueba técnica de gestión humana", "estado": Evaluacion.Estado.APROBADA, "puntaje": 88, "offset": 24, "concepto": "Aprueba la prueba técnica."},
    },
    {
        "documento": "9900000015", "nombres": "Mónica", "apellidos": "Ríos",
        "email": "monica.rios.prueba@fosst-test.com", "telefono": "3001000015",
        "ciudad": "Medellín", "departamento": "Antioquia",
        "nivel": "universitario", "titulo": "Psicóloga",
        "experiencia": "3.0", "competencias": ["Entrevistas", "Comunicación asertiva", "Gestión del talento"],
        "fuente": "Servicio Público de Empleo", "estado": "en_evaluacion", "docs": 2, "score": 80,
        "etapas": ["entrevista"], "motivo": "", "dias": 32,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 82, "offset": 18, "observaciones": "Cumple con el perfil."},
        "evaluacion": {"tipo": Evaluacion.TipoEvaluacion.PSICOTECNICA, "nombre": "Prueba psicotécnica", "estado": Evaluacion.Estado.PENDIENTE, "puntaje": None, "offset": 24, "concepto": ""},
    },
    {
        "documento": "9900000016", "nombres": "Esteban", "apellidos": "Giraldo",
        "email": "esteban.giraldo.prueba@fosst-test.com", "telefono": "3001000016",
        "ciudad": "Manizales", "departamento": "Caldas",
        "nivel": "especializacion", "titulo": "Especialista en Gerencia del Talento Humano",
        "experiencia": "7.0", "competencias": ["Gestión del talento", "Liderazgo", "Normatividad laboral"],
        "fuente": "LinkedIn", "estado": "en_validacion", "docs": 3, "score": 90,
        "etapas": ["entrevista", "evaluacion", "validacion_documental"], "motivo": "", "dias": 34,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.GERENCIAL, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 90, "offset": 18, "observaciones": "Perfil senior con experiencia relevante."},
        "evaluacion": {"tipo": Evaluacion.TipoEvaluacion.TECNICA, "nombre": "Prueba técnica de gestión humana", "estado": Evaluacion.Estado.APROBADA, "puntaje": 92, "offset": 24, "concepto": "Excelente desempeño."},
        "validacion": {"tipo": ValidacionDocumental.TipoVerificacion.REFERENCIA_LABORAL, "entidad": "Empresa anterior", "estado": ValidacionDocumental.Estado.VERIFICADO_CONFORME, "offset": 28, "detalles": "Referencias verificadas satisfactoriamente."},
    },
    {
        "documento": "9900000017", "nombres": "Luisa Fernanda", "apellidos": "Mora",
        "email": "luisa.mora.prueba@fosst-test.com", "telefono": "3001000017",
        "ciudad": "Pereira", "departamento": "Risaralda",
        "nivel": "universitario", "titulo": "Administradora de Empresas",
        "experiencia": "4.0", "competencias": ["Gestión del talento", "Nómina", "Excel intermedio"],
        "fuente": "Computrabajo", "estado": "en_validacion", "docs": 2, "score": 85,
        "etapas": ["entrevista", "evaluacion"], "motivo": "", "dias": 36,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 86, "offset": 20, "observaciones": "Cumple con el perfil."},
        "evaluacion": {"tipo": Evaluacion.TipoEvaluacion.TECNICA, "nombre": "Prueba técnica de gestión humana", "estado": Evaluacion.Estado.APROBADA, "puntaje": 84, "offset": 26, "concepto": "Aprueba la prueba técnica."},
        "validacion": {"tipo": ValidacionDocumental.TipoVerificacion.REFERENCIA_LABORAL, "entidad": "Empresa anterior", "estado": ValidacionDocumental.Estado.PENDIENTE, "offset": 30, "detalles": "Pendiente verificación de referencias."},
    },
    {
        "documento": "9900000018", "nombres": "Diego Alejandro", "apellidos": "Cruz",
        "email": "diego.cruz.prueba@fosst-test.com", "telefono": "3001000018",
        "ciudad": "Bogotá", "departamento": "Cundinamarca",
        "nivel": "universitario", "titulo": "Ingeniero Industrial",
        "experiencia": "6.0", "competencias": ["Gestión del talento", "Indicadores", "Liderazgo"],
        "fuente": "Portal Web", "estado": "seleccionado", "docs": 3, "score": 94,
        "etapas": ["entrevista", "evaluacion", "validacion_documental"], "motivo": "", "dias": 40,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.GERENCIAL, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.FAVORABLE, "calificacion": 92, "offset": 22, "observaciones": "Candidato con alto potencial."},
        "evaluacion": {"tipo": Evaluacion.TipoEvaluacion.TECNICA, "nombre": "Prueba técnica de gestión humana", "estado": Evaluacion.Estado.APROBADA, "puntaje": 95, "offset": 28, "concepto": "Desempeño sobresaliente."},
        "validacion": {"tipo": ValidacionDocumental.TipoVerificacion.REFERENCIA_LABORAL, "entidad": "Empresa anterior", "estado": ValidacionDocumental.Estado.VERIFICADO_CONFORME, "offset": 33, "detalles": "Referencias y títulos verificados."},
    },
    {
        "documento": "9900000019", "nombres": "Sara", "apellidos": "Cardona",
        "email": "sara.cardona.prueba@fosst-test.com", "telefono": "3001000019",
        "ciudad": "Cali", "departamento": "Valle del Cauca",
        "nivel": "tecnico", "titulo": "Técnica en Recursos Humanos",
        "experiencia": "1.0", "competencias": ["Archivo", "Atención al cliente", "Excel básico"],
        "fuente": "Referido", "estado": "no_seleccionado", "docs": 3, "score": 45,
        "etapas": ["entrevista"], "motivo": "Entrevista desfavorable: no cumple competencias clave del cargo.", "dias": 38,
        "entrevista": {"tipo": Entrevista.TipoEntrevista.TECNICA, "estado": Entrevista.Estado.REALIZADA, "concepto": Entrevista.Concepto.DESFAVORABLE, "calificacion": 45, "offset": 20, "observaciones": "No evidencia las competencias técnicas requeridas."},
    },
    {
        "documento": "9900000020", "nombres": "Juan Pablo", "apellidos": "Restrepo",
        "email": "juan.restrepo.prueba@fosst-test.com", "telefono": "3001000020",
        "ciudad": "Medellín", "departamento": "Antioquia",
        "nivel": "bachillerato", "titulo": "Bachiller Académico",
        "experiencia": "0.5", "competencias": ["Archivo", "Servicio", "Excel básico"],
        "fuente": "Servicio Público de Empleo", "estado": "retiro_candidatura", "docs": 1, "score": None,
        "etapas": [], "motivo": "Retiro voluntario del candidato.", "dias": 42,
    },
]


NOMBRES_TIC = [
    ("Santiago", "Gómez", "Popayán", "Cauca", "universitario", "Ingeniero de Sistemas", "4.0"),
    ("Valentina", "Ríos", "Cali", "Valle del Cauca", "tecnologo", "Tecnóloga en Sistemas", "2.5"),
    ("Andrés Felipe", "Torres", "Bogotá", "Cundinamarca", "universitario", "Ingeniero de Software", "3.0"),
    ("Camila", "Herrera", "Medellín", "Antioquia", "especializacion", "Especialista en Seguridad Informática", "6.0"),
    ("Daniel", "Ospina", "Pasto", "Nariño", "universitario", "Ingeniero de Sistemas", "2.0"),
    ("Laura", "Cárdenas", "Manizales", "Caldas", "tecnico", "Técnica en Soporte TI", "1.5"),
    ("Sebastián", "Mora", "Pereira", "Risaralda", "universitario", "Ingeniero de Sistemas", "5.0"),
    ("Natalia", "Vargas", "Tunja", "Boyacá", "tecnologo", "Tecnóloga en Redes", "3.0"),
    ("Julián", "Ramírez", "Neiva", "Huila", "universitario", "Ingeniero de Software", "2.0"),
    ("Diana", "Salazar", "Villavicencio", "Meta", "universitario", "Ingeniera de Sistemas", "4.0"),
    ("Ricardo", "Peña", "Popayán", "Cauca", "tecnologo", "Tecnólogo en Sistemas", "2.0"),
    ("Mónica", "Castro", "Cali", "Valle del Cauca", "universitario", "Ingeniera de Sistemas", "3.5"),
    ("Esteban", "Giraldo", "Bogotá", "Cundinamarca", "especializacion", "Especialista en Ciberseguridad", "7.0"),
    ("Luisa", "Mora", "Medellín", "Antioquia", "universitario", "Ingeniera de Software", "2.0"),
    ("Diego", "Cruz", "Pasto", "Nariño", "tecnologo", "Tecnólogo en Soporte TI", "1.5"),
    ("Sara", "Cardona", "Manizales", "Caldas", "universitario", "Ingeniera de Sistemas", "4.0"),
    ("Juan", "Restrepo", "Pereira", "Risaralda", "tecnico", "Técnico en Redes", "2.0"),
    ("Paola", "Cárdenas", "Tunja", "Boyacá", "universitario", "Ingeniera de Sistemas", "3.0"),
    ("Felipe", "Mejía", "Neiva", "Huila", "universitario", "Ingeniero de Software", "5.0"),
    ("Andrea", "Rojas", "Villavicencio", "Meta", "tecnologo", "Tecnóloga en Sistemas", "2.0"),
]

CANDIDATOS_TIC = []
for _i, (_nombres, _apellidos, _ciudad, _departamento, _nivel, _titulo, _experiencia) in enumerate(NOMBRES_TIC):
    CANDIDATOS_TIC.append({
        "documento": f"99000010{_i + 1:02d}",
        "nombres": _nombres,
        "apellidos": _apellidos,
        "email": f"tic{_i + 1:02d}@fosst-test.com",
        "telefono": f"301200{_i + 1:04d}",
        "ciudad": _ciudad,
        "departamento": _departamento,
        "nivel": _nivel,
        "titulo": _titulo,
        "experiencia": _experiencia,
        "competencias": [
            ["Soporte técnico", "Redes", "Windows Server"],
            ["Soporte técnico", "Ciberseguridad", "Linux"],
            ["Redes", "Soporte técnico", "Office 365"],
            ["Ciberseguridad", "Redes", "Soporte técnico"],
        ][_i % 4],
        "fuente": ["LinkedIn", "Computrabajo", "Portal Web", "Referido", "Servicio Público de Empleo"][_i % 5],
        "estado": Postulacion.Estado.POSTULADO,
        "docs": [3, 2, 1, 0][_i % 4],
        "score": None,
        "etapas": [],
        "motivo": "",
        "dias": _i + 1,
    })


class Command(BaseCommand):
    help = "Siembra 10 perfiles, vacantes y postulaciones de prueba para Reclutamiento."

    def add_arguments(self, parser):
        parser.add_argument("--nit", default="900000000", help="NIT de la empresa destino.")
        parser.add_argument("--reset", action="store_true", help="Elimina los datos de prueba previos antes de sembrar.")
        parser.add_argument("--tic", action="store_true", help="Crea la vacante TIC y sus 20 postulados.")

    def handle(self, *args, **options):
        empresa = Empresa.objects.filter(nit=options["nit"]).first()
        if not empresa:
            raise CommandError(f"No existe una empresa con NIT {options['nit']}.")
        sede = Sede.objects.filter(empresa=empresa, nombre="Sede Principal").first()
        if not sede:
            sede = Sede.objects.filter(empresa=empresa).first()
        if not sede:
            raise CommandError("La empresa no tiene sedes configuradas.")
        responsable = Usuario.objects.filter(empresa=empresa, rol="RESPONSABLE", activo=True).first()

        with transaction.atomic():
            if options["reset"]:
                self._reset(empresa)
                self.stdout.write(self.style.WARNING("Datos de prueba anteriores eliminados."))
            perfiles = self._crear_perfiles(empresa, sede)
            if options["tic"]:
                perfil = next((p for p in perfiles if p.codigo == PERFIL_VACANTE_TIC), None)
                if not perfil:
                    raise CommandError(f"No se encontró el perfil {PERFIL_VACANTE_TIC}.")
                vacante, proceso = self._crear_vacante(
                    empresa, perfil, sede, responsable,
                    titulo=TITULO_VACANTE_TIC,
                    descripcion=(
                        "Buscamos un Ingeniero de Soporte TI para brindar soporte técnico, "
                        "administrar la infraestructura, la red y los respaldos, garantizando "
                        "disponibilidad, seguridad y continuidad del servicio."
                    ),
                    documentos=DOCS_REQUERIDOS_TIC,
                    requisitos=[
                        "Formación mínima: Profesional en Ingeniería de Sistemas, Software o afines.",
                        "Experiencia mínima: Mínimo 2 años en soporte TI e infraestructura.",
                    ],
                    requisitos_deseables=[
                        "Certificación en redes o ciberseguridad.",
                        "Experiencia con Windows Server, Linux y Office 365.",
                    ],
                    cupos=3,
                    seleccionados=0,
                    salario_min=Decimal("3000000"),
                    salario_max=Decimal("4500000"),
                )
                total = self._crear_postulaciones(
                    empresa, vacante, proceso, responsable,
                    CANDIDATOS_TIC, DOCS_REQUERIDOS_TIC,
                    area="Tecnología", cargo="Ingeniero de Soporte TI",
                )
                self._resumen(vacante, proceso, len(perfiles), total, DOCS_REQUERIDOS_TIC)
            else:
                vacante, proceso = self._crear_vacante(
                    empresa, perfiles[0], sede, responsable,
                    titulo=TITULO_VACANTE,
                    descripcion=(
                        "Buscamos un Analista de Gestión Humana para liderar los procesos de "
                        "reclutamiento, selección, contratación, formación y bienestar del talento, "
                        "asegurando el cumplimiento de la normatividad laboral y el fortalecimiento "
                        "del clima organizacional."
                    ),
                    documentos=DOCS_REQUERIDOS,
                    requisitos=[
                        "Profesional en Administración, Psicología, Ingeniería Industrial o afines.",
                        "Mínimo 1 año de experiencia en gestión humana o talento humano.",
                    ],
                    requisitos_deseables=[
                        "Especialización en Gestión Humana o SST.",
                        "Manejo de Excel intermedio.",
                    ],
                    cupos=3,
                    seleccionados=1,
                    salario_min=Decimal("2500000"),
                    salario_max=Decimal("3500000"),
                )
                total = self._crear_postulaciones(
                    empresa, vacante, proceso, responsable,
                    CANDIDATOS, DOCS_REQUERIDOS,
                    area="Gestión Humana", cargo="Analista de Gestión Humana",
                )
                self._resumen(vacante, proceso, len(perfiles), total, DOCS_REQUERIDOS)

    def _reset(self, empresa):
        Vacante.objects.filter(empresa=empresa, titulo__startswith="[PRUEBAS]").delete()
        candidatos = Candidato.objects.filter(empresa=empresa, documento__startswith="990000")
        archivo_ids = list(
            CandidatoDocumento.objects.filter(candidato__in=candidatos).values_list("archivo_id", flat=True)
        )
        candidatos.delete()
        if archivo_ids:
            Archivo.objects.filter(id__in=archivo_ids).delete()
        for perfil in PerfilCargo.objects.filter(empresa=empresa, codigo__startswith="PC-2026-02"):
            if not perfil.vacantes.exists():
                perfil.delete()

    def _crear_perfiles(self, empresa, sede):
        perfiles = []
        creados = 0
        for data in PERFILES:
            perfil, created = PerfilCargo.objects.update_or_create(
                empresa=empresa,
                codigo=data["codigo"],
                defaults={
                    "nombre_cargo": data["nombre_cargo"],
                    "area": data["area"],
                    "sede": sede,
                    "tipo_cargo": data["tipo_cargo"],
                    "nivel_riesgo": data["nivel_riesgo"],
                    "proposito": data["proposito"],
                    "educacion": data["educacion"],
                    "experiencia": data["experiencia"],
                    "formacion": data["formacion"],
                    "habilidades": data["habilidades"],
                    "criticidad_sst": data["criticidades"]["sst"],
                    "criticidad_operacional": data["criticidades"]["operacional"],
                    "criticidad_vial": data["criticidades"]["vial"],
                    "criticidad_ambiental": data["criticidades"]["ambiental"],
                    "criticidad_estrategica": data["criticidades"]["estrategica"],
                    "requiere_suplencia": data["requiere_suplencia"],
                    "cargo_critico": data["cargo_critico"],
                    "activo": True,
                },
            )
            creados += int(created)
            for orden, descripcion in enumerate(data["funciones"]):
                CargoFuncion.objects.update_or_create(
                    perfil_cargo=perfil, descripcion=descripcion, defaults={"orden": orden}
                )
            for orden, descripcion in enumerate(data["responsabilidades"]):
                CargoResponsabilidad.objects.update_or_create(
                    perfil_cargo=perfil, descripcion=descripcion, defaults={"orden": orden}
                )
            for nombre, tipo, nivel in data["competencias"]:
                CargoCompetencia.objects.update_or_create(
                    perfil_cargo=perfil,
                    nombre=nombre,
                    defaults={"tipo": tipo, "nivel_requerido": nivel},
                )
            CargoIndicador.objects.update_or_create(
                perfil_cargo=perfil,
                descripcion=data["indicador"][0],
                defaults={"meta": data["indicador"][1]},
            )
            if not perfil.versiones.exists():
                from apps.perfilcargo.serializers import PerfilCargoSerializer
                import json

                snapshot = json.loads(
                    json.dumps(PerfilCargoSerializer(perfil).data, cls=DjangoJSONEncoder)
                )
                CargoVersion.objects.create(
                    perfil_cargo=perfil,
                    numero_version=perfil.version_actual,
                    snapshot=snapshot,
                    motivo_cambio="Creación (datos de prueba)",
                    creado_por="seed_pruebas_reclutamiento",
                )
            perfiles.append(perfil)
        self.stdout.write(
            self.style.SUCCESS(f"Perfiles: {len(perfiles)} listos ({creados} nuevos).")
        )
        return perfiles

    def _crear_vacante(
        self, empresa, perfil, sede, responsable, *,
        titulo, descripcion, documentos, requisitos, requisitos_deseables,
        cupos, seleccionados, salario_min, salario_max,
    ):
        hoy = timezone.localdate()
        vacante = Vacante.objects.filter(empresa=empresa, titulo=titulo).first()
        if not vacante:
            vacante = Vacante(empresa=empresa, titulo=titulo)
        vacante.perfil_cargo = perfil
        vacante.sede = sede
        vacante.descripcion_publica = descripcion
        vacante.numero_cupos = cupos
        vacante.numero_seleccionados = seleccionados
        vacante.tipo_contrato = "Término indefinido"
        vacante.modalidad = Vacante.Modalidad.PRESENCIAL
        vacante.rango_salarial_min = salario_min
        vacante.rango_salarial_max = salario_max
        vacante.mostrar_salario_publico = True
        vacante.estado = Vacante.Estado.ABIERTA
        vacante.fecha_apertura = hoy - timedelta(days=40)
        vacante.fecha_cierre_estimada = hoy + timedelta(days=10)
        vacante.publicada_en_portal = True
        vacante.save()

        proceso, _ = ProcesoSeleccion.objects.get_or_create(
            vacante=vacante,
            defaults={"empresa": empresa},
        )
        proceso.empresa = empresa
        proceso.responsable_rh = responsable
        proceso.requiere_entrevista = True
        proceso.requiere_evaluacion = True
        proceso.requiere_validacion_documental = True
        proceso.documentos_requeridos = list(documentos)
        proceso.requisitos_obligatorios = requisitos
        proceso.requisitos_deseables = requisitos_deseables
        proceso.estado = ProcesoSeleccion.Estado.ACTIVO
        proceso.save()
        self.stdout.write(
            self.style.SUCCESS(f"Vacante: {vacante.codigo} — {vacante.titulo} (proceso {proceso.codigo}).")
        )
        return vacante, proceso

    def _crear_postulaciones(self, empresa, vacante, proceso, responsable, candidatos, docs_requeridos, area, cargo):
        total = 0
        for idx, data in enumerate(candidatos):
            fuente, _ = FuenteReclutamiento.objects.get_or_create(
                empresa=empresa, nombre=data["fuente"], defaults={"activo": True}
            )
            estado_perfil = Candidato.EstadoPerfil.EN_BUSQUEDA
            if data["estado"] == Postulacion.Estado.SELECCIONADO:
                estado_perfil = Candidato.EstadoPerfil.CONTRATADO
            elif data["estado"] in (Postulacion.Estado.NO_SELECCIONADO, Postulacion.Estado.RETIRO_CANDIDATURA):
                estado_perfil = Candidato.EstadoPerfil.DESCARTADO

            candidato, _ = Candidato.objects.update_or_create(
                empresa=empresa,
                tipo_documento=Candidato.TipoDocumento.CC,
                documento=data["documento"],
                defaults={
                    "nombres": data["nombres"],
                    "apellidos": data["apellidos"],
                    "email": data["email"],
                    "telefono": data["telefono"],
                    "ciudad": data["ciudad"],
                    "departamento": data["departamento"],
                    "municipio": data["ciudad"],
                    "estado_perfil": estado_perfil,
                    "fuente_reclutamiento": fuente,
                    "fuente_detalle": f"Campaña {data['fuente']} 2026",
                    "autoriza_tratamiento_datos": True,
                    "fecha_autorizacion_datos": timezone.now(),
                    "etiquetas": list(dict.fromkeys(data["competencias"] + [data["ciudad"]])),
                    "notas_internas": "Candidato de prueba generado automáticamente.",
                    "registrado_por": "seed_pruebas_reclutamiento",
                },
            )

            perfil_candidato, _ = PerfilCandidato.objects.update_or_create(
                candidato=candidato,
                defaults={
                    "titulo_profesional": data["titulo"],
                    "nivel_educativo": data["nivel"],
                    "resumen_profesional": f"{data['titulo']}. {data['experiencia']} años de experiencia en {area}.",
                    "anios_experiencia": Decimal(data["experiencia"]),
                    "experiencia_laboral": [
                        {
                            "empresa": "Empresa de prueba",
                            "cargo": f"Profesional de {area}",
                            "fecha_inicio": "2022-01",
                            "fecha_fin": "2025-12",
                            "actual": False,
                            "funciones": f"Apoyo en procesos de {area}.",
                        }
                    ],
                    "formacion_academica": [
                        {
                            "institucion": "Institución de prueba",
                            "titulo": data["titulo"],
                            "nivel": data["nivel"],
                            "anio_graduacion": 2022,
                            "en_curso": False,
                        }
                    ],
                    "certificaciones": [{"nombre": "SG-SST", "institucion": "SENA", "anio": 2023}] if idx % 4 == 0 else [],
                    "competencias": data["competencias"],
                    "profesion": data["titulo"],
                    "area_conocimiento": area,
                    "cargos_interes": [cargo],
                    "idiomas": [{"idioma": "Inglés", "nivel": "B1"}] if idx % 3 == 0 else [],
                    "disponibilidad": "inmediata",
                    "aspiracion_salarial": Decimal(str(2500000 + idx * 50000)),
                    "disponibilidad_viaje": idx % 4 == 0,
                    "disponibilidad_traslado": idx % 3 == 0,
                },
            )

            post, _ = Postulacion.objects.update_or_create(
                proceso_seleccion=proceso,
                candidato=candidato,
                defaults={
                    "empresa": empresa,
                    "estado": data["estado"],
                    "puntuacion_general": Decimal(str(data["score"])) if data["score"] is not None else None,
                    "etapas_completadas": data["etapas"],
                    "motivo_cierre": data["motivo"],
                },
            )
            fecha_post = timezone.now() - timedelta(days=data["dias"])
            Postulacion.objects.filter(pk=post.pk).update(fecha_postulacion=fecha_post)
            post.refresh_from_db()

            self._crear_eventos(post, data, responsable)
            self._crear_documentos(candidato, data, docs_requeridos)
            self._crear_etapas(empresa, post, data, responsable)
            total += 1
        return total

    def _crear_eventos(self, post, data, responsable):
        PostulacionEvento.objects.get_or_create(
            postulacion=post,
            tipo_evento=PostulacionEvento.TipoEvento.POSTULACION_REGISTRADA,
            defaults={
                "estado_nuevo": Postulacion.Estado.POSTULADO,
                "descripcion": "Postulación registrada (datos de prueba).",
                "usuario": responsable,
            },
        )
        if data["estado"] != Postulacion.Estado.POSTULADO:
            PostulacionEvento.objects.get_or_create(
                postulacion=post,
                tipo_evento=PostulacionEvento.TipoEvento.CAMBIO_ESTADO,
                estado_nuevo=data["estado"],
                defaults={
                    "estado_anterior": Postulacion.Estado.POSTULADO,
                    "descripcion": f"Cambio de estado a {data['estado']} (datos de prueba).",
                    "motivo": data["motivo"],
                    "usuario": responsable,
                },
            )

    def _crear_documentos(self, candidato, data, docs_requeridos):
        for tipo in docs_requeridos[: data["docs"]]:
            if CandidatoDocumento.objects.filter(candidato=candidato, tipo_documento=tipo).exists():
                continue
            label = DOC_LABELS[tipo]
            pdf_bytes = self._pdf_documento(candidato, label)
            archivo = SimpleUploadedFile(
                f"{tipo}_{candidato.documento}.pdf",
                pdf_bytes,
                content_type="application/pdf",
            )
            try:
                _guardar_documento_candidato(
                    candidato,
                    archivo,
                    tipo,
                    descripcion=f"{label} de prueba",
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.WARNING(
                        f"  Documento {tipo} de {candidato.documento}: fallback local ({exc})"
                    )
                )
                archivo_db = Archivo.objects.create(
                    nombre=archivo.name,
                    url=f"https://pruebas.fosst.local/{candidato.documento}/{tipo}.pdf",
                    tipo_mime="application/pdf",
                    tamanio_kb=max(1, len(pdf_bytes) // 1024),
                    subido_por="seed_pruebas_reclutamiento",
                    sha256_hash=hashlib.sha256(pdf_bytes).hexdigest(),
                )
                CandidatoDocumento.objects.create(
                    candidato=candidato,
                    archivo=archivo_db,
                    tipo_documento=tipo,
                    nombre_descriptivo=f"{label} de prueba",
                )

    def _pdf_documento(self, candidato, label):
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        pdf.setTitle(f"{label} - {candidato.nombre_completo}")
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(72, 790, "FOSST V.I.D.A. - Documento de prueba")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(72, 750, f"Tipo de documento: {label}")
        pdf.drawString(72, 730, f"Candidato: {candidato.nombre_completo}")
        pdf.drawString(72, 710, f"Identificacion: {candidato.tipo_documento} {candidato.documento}")
        pdf.drawString(72, 690, f"Ciudad: {candidato.ciudad}")
        pdf.drawString(72, 670, f"Correo: {candidato.email}")
        pdf.drawString(72, 650, f"Fecha de generacion: {date.today().isoformat()}")
        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawString(72, 610, "Archivo generado automaticamente para pruebas de reclutamiento.")
        pdf.showPage()
        pdf.save()
        return buffer.getvalue()

    def _crear_etapas(self, empresa, post, data, responsable):
        fecha_base = post.fecha_postulacion
        entrevista = data.get("entrevista")
        if entrevista:
            fecha = fecha_base + timedelta(days=entrevista["offset"])
            Entrevista.objects.get_or_create(
                postulacion=post,
                tipo_entrevista=entrevista["tipo"],
                fecha_programada=fecha,
                defaults={
                    "empresa": empresa,
                    "modalidad": Entrevista.Modalidad.VIRTUAL,
                    "entrevistador": responsable,
                    "estado": entrevista["estado"],
                    "calificacion": entrevista.get("calificacion"),
                    "concepto": entrevista["concepto"],
                    "observaciones": entrevista.get("observaciones", ""),
                    "aspectos_evaluados": {"competencias": "Evaluación de prueba"},
                },
            )

        evaluacion = data.get("evaluacion")
        if evaluacion:
            fecha_real = None
            if evaluacion["estado"] != Evaluacion.Estado.PENDIENTE:
                fecha_real = fecha_base + timedelta(days=evaluacion["offset"])
            Evaluacion.objects.get_or_create(
                postulacion=post,
                nombre_prueba=evaluacion["nombre"],
                defaults={
                    "empresa": empresa,
                    "tipo_evaluacion": evaluacion["tipo"],
                    "fecha_realizacion": fecha_real,
                    "evaluador": responsable,
                    "puntaje_obtenido": Decimal(str(evaluacion["puntaje"])) if evaluacion.get("puntaje") is not None else None,
                    "puntaje_maximo": Decimal("100"),
                    "porcentaje_aprobacion": Decimal("70"),
                    "estado": evaluacion["estado"],
                    "concepto": evaluacion.get("concepto", ""),
                },
            )

        validacion = data.get("validacion")
        if validacion:
            fecha_val = None
            if validacion["estado"] != ValidacionDocumental.Estado.PENDIENTE:
                fecha_val = fecha_base + timedelta(days=validacion["offset"])
            ValidacionDocumental.objects.get_or_create(
                postulacion=post,
                tipo_verificacion=validacion["tipo"],
                entidad_o_contacto=validacion["entidad"],
                defaults={
                    "empresa": empresa,
                    "verificado_por": responsable,
                    "fecha_verificacion": fecha_val,
                    "estado": validacion["estado"],
                    "detalles_verificacion": validacion.get("detalles", ""),
                },
            )

    def _resumen(self, vacante, proceso, total_perfiles, total_postulaciones, docs_requeridos):
        postulaciones = Postulacion.objects.filter(proceso_seleccion=proceso).select_related("candidato")
        estados = Counter(postulaciones.values_list("estado", flat=True))
        completos = parciales = sin_documentos = 0
        for post in postulaciones:
            presentes = set(post.candidato.documentos.values_list("tipo_documento", flat=True))
            faltantes = [tipo for tipo in docs_requeridos if tipo not in presentes]
            if not faltantes:
                completos += 1
            elif len(faltantes) == len(docs_requeridos):
                sin_documentos += 1
            else:
                parciales += 1

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=== Resumen de datos de prueba ==="))
        self.stdout.write(f"Perfiles de cargo: {total_perfiles}")
        self.stdout.write(f"Vacante: {vacante.codigo} — {vacante.titulo} ({vacante.get_estado_display()})")
        self.stdout.write(f"Proceso: {proceso.codigo} | Cupos: {vacante.numero_cupos}")
        self.stdout.write(f"Postulaciones: {total_postulaciones}")
        self.stdout.write("Estados: " + ", ".join(f"{k}={v}" for k, v in sorted(estados.items())))
        self.stdout.write(
            f"Documentos: {completos} completos, {parciales} parciales, {sin_documentos} sin documentos."
        )
        self.stdout.write("Requeridos: " + ", ".join(DOC_LABELS[t] for t in docs_requeridos))
