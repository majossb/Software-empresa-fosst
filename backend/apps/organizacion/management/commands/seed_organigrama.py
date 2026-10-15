import random
from django.core.management.base import BaseCommand
from apps.empresas.models import Empresa
from apps.organizacion.models import NodoOrganigrama

AREAS = [
    "Dirección General",
    "Seguridad y Salud en el Trabajo",
    "Operaciones y Logística",
    "Recursos Humanos",
    "Finanzas y Contabilidad",
    "Tecnología de la Información",
    "Calidad y Medio Ambiente",
    "Mantenimiento Industrial",
    "Ventas y Comercial",
]

CARGOS_POR_NIVEL = {
    1: ["Gerente General / CEO"],
    2: [
        "Director SG-SST",
        "Director de Operaciones",
        "Director Financiero",
        "Director de Tecnología",
        "Director de Recursos Humanos",
    ],
    3: [
        "Jefe de Prevención de Riesgos",
        "Jefe de Logística",
        "Jefe de Planta",
        "Contador General",
        "Líder de Desarrollo",
        "Jefe de Selección y Nómina",
        "Coordinador de Calidad",
    ],
    4: [
        "Analista Senior SST",
        "Supervisor de Producción A",
        "Supervisor de Producción B",
        "Analista Financiero",
        "Ingeniero de Software Senior",
        "Analista de Talento Humano",
        "Inspector de Calidad",
        "Coordinador de Mantenimiento",
        "Especialista en Compras",
    ],
    5: [
        "Inspector de Campo SST 1",
        "Inspector de Campo SST 2",
        "Operador de Maquinaria 1",
        "Operador de Maquinaria 2",
        "Auxiliar Contable 1",
        "Desarrollador Frontend",
        "Desarrollador Backend",
        "Auxiliar de Selección",
        "Técnico de Mantenimiento A",
        "Técnico de Mantenimiento B",
        "Auxiliar de Logística 1",
        "Auxiliar de Logística 2",
    ],
    6: [
        "Asistente SST",
        "Auxiliar de Planta 1",
        "Auxiliar de Planta 2",
        "Auxiliar de Planta 3",
        "Pasante de Sistemas",
        "Pasante de Contabilidad",
        "Pasante de SST",
        "Operador de Empaque 1",
        "Operador de Empaque 2",
    ]
}


class Command(BaseCommand):
    help = "Genera un organigrama de prueba masivo (40+ cargos, 6 niveles) para pruebas de rendimiento y visualización."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina el organigrama existente antes de sembrar.",
        )

    def handle(self, *args, **options):
        empresa = Empresa.objects.first()
        if not empresa:
            self.stderr.write(self.style.ERROR("No se encontró ninguna empresa en la base de datos."))
            return

        if options["limpiar"]:
            count = NodoOrganigrama.objects.filter(empresa=empresa).delete()[0]
            self.stdout.write(self.style.WARNING(f"Eliminados {count} nodos existentes."))

        self.stdout.write(f"Generando organigrama masivo para: {empresa.nombre}")

        creados = []
        nodos_por_nivel = {i: [] for i in range(1, 7)}

        # Nivel 1: Raíz
        raiz = NodoOrganigrama.objects.create(
            empresa=empresa,
            nombre_cargo=CARGOS_POR_NIVEL[1][0],
            area=AREAS[0],
            nivel=1,
            padre=None,
            orden=0,
            activo=True,
        )
        creados.append(raiz)
        nodos_por_nivel[1].append(raiz)

        # Nivel 2: Directores
        for idx, cargo in enumerate(CARGOS_POR_NIVEL[2]):
            area = AREAS[(idx + 1) % len(AREAS)]
            nodo = NodoOrganigrama.objects.create(
                empresa=empresa,
                nombre_cargo=cargo,
                area=area,
                nivel=2,
                padre=raiz,
                orden=idx,
                activo=True,
            )
            creados.append(nodo)
            nodos_por_nivel[2].append(nodo)

        # Niveles 3 a 6
        for lvl in range(3, 7):
            padres_disponibles = nodos_por_nivel[lvl - 1]
            for idx, cargo in enumerate(CARGOS_POR_NIVEL[lvl]):
                padre = padres_disponibles[idx % len(padres_disponibles)]
                area = padre.area
                nodo = NodoOrganigrama.objects.create(
                    empresa=empresa,
                    nombre_cargo=cargo,
                    area=area,
                    nivel=lvl,
                    padre=padre,
                    orden=idx,
                    activo=True,
                )
                creados.append(nodo)
                nodos_por_nivel[lvl].append(nodo)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Organigrama generado exitosamente. Total cargos creados: {len(creados)} distribuidos en 6 niveles."
            )
        )
