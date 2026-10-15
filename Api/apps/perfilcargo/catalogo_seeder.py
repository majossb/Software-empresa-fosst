"""
Utilidad de inicialización del Catálogo GTC 45 y Catálogo de EPPs.
Contiene la clasificación oficial colombiana de la Guía Técnica Colombiana GTC 45
y el catálogo estándar de Elementos de Protección Personal con sus relaciones sugeridas.
"""

from apps.perfilcargo.models import CatalogoPeligro, CatalogoEPP

CATALOGO_EPPS_DATA = [
    {"nombre": "Casco de seguridad industrial dieléctrico (Clase E)", "descripcion": "Protección craneal contra impactos, penetración y descargas eléctricas hasta 20.000V."},
    {"nombre": "Barbuquejo de 3 o 4 puntos de apoyo", "descripcion": "Sujeción del casco a la barbilla para trabajos en alturas y movimientos bruscos."},
    {"nombre": "Gafas de seguridad con protección UV y antirrayadura", "descripcion": "Protección ocular contra proyección de partículas, polvo y radiación solar."},
    {"nombre": "Monogafas de seguridad herméticas (anti-salpicaduras)", "descripcion": "Protección ocular sellada contra salpicaduras de químicos, vapores y nieblas."},
    {"nombre": "Careta de esmerilar en policarbonato", "descripcion": "Protección facial integral contra esquirlas, chispas y partículas a alta velocidad."},
    {"nombre": "Careta para soldadura con visor fotosensible", "descripcion": "Protección facial y ocular contra radiación UV/IR intensa y chispas de soldadura."},
    {"nombre": "Protector auditivo tipo inserción en silicona", "descripcion": "Reducción de ruido NRR 25-27 dB para exposición a ruido continuo."},
    {"nombre": "Protector auditivo tipo copa (diadema / adaptable)", "descripcion": "Atenuación acústica de alto rendimiento NRR 27-31 dB para ambientes de alto ruido."},
    {"nombre": "Respirador libre de mantenimiento N95 para material particulado", "descripcion": "Filtración de partículas sólidas y líquidas sin aceite (polvos, humos)."},
    {"nombre": "Respirador de media cara con cartuchos para vapores orgánicos y gases", "descripcion": "Protección respiratoria con carbón activado para disolventes, pinturas y vapores."},
    {"nombre": "Respirador con filtros para humos metálicos (P100)", "descripcion": "Filtración de humos de soldadura y partículas de alta toxicidad (99.97% eficiencia)."},
    {"nombre": "Guantes de vaqueta / carnaza para trabajo pesado", "descripcion": "Protección manual contra abrasión, fricción, calor moderado y corte básico."},
    {"nombre": "Guantes de nitrilo / neopreno resistentes a químicos", "descripcion": "Protección de manos contra solventes, aceites, grasas y productos químicos."},
    {"nombre": "Guantes anticorte nivel 5 (fibra HPPE / Kevlar)", "descripcion": "Protección de manos contra cuchillas, vidrios, láminas y bordes afilados."},
    {"nombre": "Guantes dieléctricos certificados", "descripcion": "Aislamiento eléctrico para intervención en tableros y redes eléctricas energizadas."},
    {"nombre": "Botas de seguridad con puntera de acero / composite", "descripcion": "Calzado industrial con resistencia a compresión, caída de objetos e hidrocarburos."},
    {"nombre": "Botas de seguridad dieléctricas con puntera de composite", "descripcion": "Calzado sin partes metálicas para aislamiento frente a riesgos eléctricos."},
    {"nombre": "Botas de caucho impermeables de caña alta", "descripcion": "Protección de pies y piernas contra agua, lodos y sustancias líquidas."},
    {"nombre": "Arnés de cuerpo entero de 4 argollas certificado", "descripcion": "Sistema de detención de caídas para trabajo en alturas según Res. 4272 de 2021."},
    {"nombre": "Eslinga de posicionamiento y eslinga en Y con absorbedor", "descripcion": "Elemento de amarre con absorbedor de impacto para detención de caídas."},
    {"nombre": "Chaleco reflectivo de alta visibilidad", "descripcion": "Prenda con cintas retrorreflectivas para operaciones viales, bodegas y zonas de tráfico."},
    {"nombre": "Delantal de PVC / caucho impermeable", "descripcion": "Protección corporal contra salpicaduras de líquidos corrosivos y agua."},
    {"nombre": "Ropa de trabajo ignífuga / antiestática", "descripcion": "Protección corporal contra fuego repentino, arco eléctrico y cargas electrostáticas."},
]

CATALOGO_PELIGROS_DATA = [
    # ── BIOLÓGICO ──
    {
        "tipo": "Biológico",
        "clasificacion": "Virus (Biológico)",
        "descripcion": "Exposición a agentes biológicos como SARS-CoV-2, Influenza, Hepatitis, etc.",
        "epps": ["Respirador libre de mantenimiento N95 para material particulado", "Guantes de nitrilo / neopreno resistentes a químicos", "Gafas de seguridad con protección UV y antirrayadura"]
    },
    {
        "tipo": "Biológico",
        "clasificacion": "Bacterias",
        "descripcion": "Contacto con microorganismos patógenos en ambientes clínicos, alimentos o aguas.",
        "epps": ["Respirador libre de mantenimiento N95 para material particulado", "Guantes de nitrilo / neopreno resistentes a químicos"]
    },
    {
        "tipo": "Biológico",
        "clasificacion": "Hongos",
        "descripcion": "Presencia de esporas y hongos en ambientes húmedos, bodegas o archivos.",
        "epps": ["Respirador libre de mantenimiento N95 para material particulado", "Guantes de nitrilo / neopreno resistentes a químicos", "Botas de caucho impermeables de caña alta"]
    },
    {
        "tipo": "Biológico",
        "clasificacion": "Picaduras y Mordeduras",
        "descripcion": "Riesgo de ataque o picadura de insectos, arácnidos, ofidios o animales en campo.",
        "epps": ["Guantes de vaqueta / carnaza para trabajo pesado", "Botas de caucho impermeables de caña alta", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Biológico",
        "clasificacion": "Fluidos o Excrementos",
        "descripcion": "Manipulación de muestras biológicas, residuos anatomopatológicos o aguas residuales.",
        "epps": ["Monogafas de seguridad herméticas (anti-salpicaduras)", "Guantes de nitrilo / neopreno resistentes a químicos", "Delantal de PVC / caucho impermeable", "Botas de caucho impermeables de caña alta"]
    },

    # ── FÍSICO ──
    {
        "tipo": "Físico",
        "clasificacion": "Ruido (Impacto, Intermitente, Continuo)",
        "descripcion": "Generado por maquinaria pesada, herramientas neumáticas, motores y procesos industriales.",
        "epps": ["Protector auditivo tipo inserción en silicona", "Protector auditivo tipo copa (diadema / adaptable)"]
    },
    {
        "tipo": "Físico",
        "clasificacion": "Iluminación (Exceso o Deficiencia)",
        "descripcion": "Deslumbramiento, contrastes marcados o luz insuficiente en puestos de trabajo o pantallas.",
        "epps": ["Gafas de seguridad con protección UV y antirrayadura"]
    },
    {
        "tipo": "Físico",
        "clasificacion": "Vibración (Cuerpo entero / Mano-brazo)",
        "descripcion": "Transmisión de vibraciones por conducción de maquinaria pesada o herramientas percutoras.",
        "epps": ["Guantes de vaqueta / carnaza para trabajo pesado", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Físico",
        "clasificacion": "Temperaturas Extremas (Calor / Frío)",
        "descripcion": "Trabajo a la intemperie bajo radiación solar, hornos, fundiciones o cuartos fríos.",
        "epps": ["Gafas de seguridad con protección UV y antirrayadura", "Ropa de trabajo ignífuga / antiestática", "Guantes de vaqueta / carnaza para trabajo pesado"]
    },
    {
        "tipo": "Físico",
        "clasificacion": "Radiaciones No Ionizantes (UV, IR, Láser, EMF)",
        "descripcion": "Exposición a soldadura eléctrica/oxiacetileno, láser, antenas y radiación solar continua.",
        "epps": ["Careta para soldadura con visor fotosensible", "Gafas de seguridad con protección UV y antirrayadura", "Guantes de vaqueta / carnaza para trabajo pesado"]
    },
    {
        "tipo": "Físico",
        "clasificacion": "Radiaciones Ionizantes (Rayos X, Gamma)",
        "descripcion": "Equipos de gammagrafía industrial, rayos X médicos o inspección de equipaje/aduanas.",
        "epps": ["Delantal de PVC / caucho impermeable", "Gafas de seguridad con protección UV y antirrayadura"]
    },

    # ── QUÍMICO ──
    {
        "tipo": "Químico",
        "clasificacion": "Polvos Orgánicos e Inorgánicos",
        "descripcion": "Generación de polvo por molienda, corte de madera, cemento, harina, granos o minerales.",
        "epps": ["Respirador libre de mantenimiento N95 para material particulado", "Gafas de seguridad con protección UV y antirrayadura"]
    },
    {
        "tipo": "Químico",
        "clasificacion": "Fibras",
        "descripcion": "Manipulación de fibra de vidrio, lana mineral, asbesto o textiles.",
        "epps": ["Respirador con filtros para humos metálicos (P100)", "Monogafas de seguridad herméticas (anti-salpicaduras)", "Guantes de nitrilo / neopreno resistentes a químicos"]
    },
    {
        "tipo": "Químico",
        "clasificacion": "Líquidos (Nieblas, Rocíos y Salpicaduras)",
        "descripcion": "Pintura con pistola, desengrasado con solventes, aplicación de fitosanitarios o reactivos.",
        "epps": ["Respirador de media cara con cartuchos para vapores orgánicos y gases", "Monogafas de seguridad herméticas (anti-salpicaduras)", "Guantes de nitrilo / neopreno resistentes a químicos", "Delantal de PVC / caucho impermeable"]
    },
    {
        "tipo": "Químico",
        "clasificacion": "Gases y Vapores",
        "descripcion": "Combustión, solventes orgánicos volátiles, amoníaco, cloro o hidrocarburos.",
        "epps": ["Respirador de media cara con cartuchos para vapores orgánicos y gases", "Monogafas de seguridad herméticas (anti-salpicaduras)", "Guantes de nitrilo / neopreno resistentes a químicos"]
    },
    {
        "tipo": "Químico",
        "clasificacion": "Humos Metálicos y No Metálicos",
        "descripcion": "Soldadura, oxicorte, fundición y procesos térmicos sobre metales o plásticos.",
        "epps": ["Careta para soldadura con visor fotosensible", "Respirador con filtros para humos metálicos (P100)", "Guantes de vaqueta / carnaza para trabajo pesado"]
    },
    {
        "tipo": "Químico",
        "clasificacion": "Material Particulado",
        "descripcion": "Corte de metales, construcción, demolición y tránsito por vías destapadas.",
        "epps": ["Respirador libre de mantenimiento N95 para material particulado", "Gafas de seguridad con protección UV y antirrayadura"]
    },

    # ── PSICOSOCIAL ──
    {
        "tipo": "Psicosocial",
        "clasificacion": "Gestión Organizacional y Estilo de Mando",
        "descripcion": "Mecanismos de evaluación, relaciones jerárquicas, exigencias de cumplimiento y liderazgo.",
        "epps": []
    },
    {
        "tipo": "Psicosocial",
        "clasificacion": "Características de la Organización del Trabajo",
        "descripcion": "Carga de trabajo, demandas cualitativas/cuantitativas, ritmo y repetitividad de tareas.",
        "epps": []
    },
    {
        "tipo": "Psicosocial",
        "clasificacion": "Condiciones de la Tarea (Carga Mental y Emocional)",
        "descripcion": "Atención al cliente/usuarios, toma de decisiones críticas, manejo de valores y alta concentración.",
        "epps": []
    },
    {
        "tipo": "Psicosocial",
        "clasificacion": "Jornada de Trabajo y Horarios Extensivos",
        "descripcion": "Turnos rotativos, trabajo nocturno, horas extras frecuentes y descansos limitados.",
        "epps": []
    },

    # ── BIOMECÁNICO ──
    {
        "tipo": "Biomecánico",
        "clasificacion": "Postura Prolongada / Mantenida / Forzada",
        "descripcion": "Posición de pie o sentado por más del 70% de la jornada laboral sin alternancia.",
        "epps": ["Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Biomecánico",
        "clasificacion": "Esfuerzo Físico",
        "descripcion": "Aplicación de fuerza corporal para empujar, halar, sostener o mover objetos y maquinaria.",
        "epps": ["Guantes de vaqueta / carnaza para trabajo pesado", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Biomecánico",
        "clasificacion": "Movimiento Repetitivo",
        "descripcion": "Ciclos de trabajo continuos con manos, muñecas y brazos (digitación, ensamble, empaque).",
        "epps": ["Guantes de vaqueta / carnaza para trabajo pesado"]
    },
    {
        "tipo": "Biomecánico",
        "clasificacion": "Manipulación Manual de Cargas",
        "descripcion": "Levantamiento, descenso y transporte manual de cargas superiores a 3 kg.",
        "epps": ["Guantes de vaqueta / carnaza para trabajo pesado", "Botas de seguridad con puntera de acero / composite"]
    },

    # ── CONDICIONES DE SEGURIDAD ──
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Mecánico (Máquinas, Herramientas, Proyección)",
        "descripcion": "Atrapamiento en engranajes, corte con herramientas manuales/eléctricas, proyección de sólidos.",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Gafas de seguridad con protección UV y antirrayadura", "Careta de esmerilar en policarbonato", "Guantes anticorte nivel 5 (fibra HPPE / Kevlar)", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Eléctrico (Alta y Baja Tensión, Estática)",
        "descripcion": "Contacto directo o indirecto con circuitos energizados, tableros eléctricos y transformadores.",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Gafas de seguridad con protección UV y antirrayadura", "Guantes dieléctricos certificados", "Botas de seguridad dieléctricas con puntera de composite"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Locativo (Superficies, Caída de Objetos, Orden y Aseo)",
        "descripcion": "Pisos resbalosos, desniveles, almacenamiento en altura y obstáculos en pasillos.",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Tecnológico (Incendio, Explosión, Derrame)",
        "descripcion": "Presencia de combustibles, gases comprimidos, solventes inflamables y calderas.",
        "epps": ["Ropa de trabajo ignífuga / antiestática", "Respirador de media cara con cartuchos para vapores orgánicos y gases", "Casco de seguridad industrial dieléctrico (Clase E)", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Accidentes de Tránsito / Movilidad",
        "descripcion": "Desplazamientos en vehículos de la empresa, motocicletas o transporte de carga.",
        "epps": ["Chaleco reflectivo de alta visibilidad", "Casco de seguridad industrial dieléctrico (Clase E)", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Público (Robo, Atraco, Asalto, Desorden Público)",
        "descripcion": "Atención al público en ventanilla, transporte de valores y labores en vía pública.",
        "epps": ["Chaleco reflectivo de alta visibilidad"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Trabajo en Alturas (Superior a 2.0 m)",
        "descripcion": "Labores en andamios, cubiertas, escaleras, postes o plataformas elevadas (Res. 4272/2021).",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Barbuquejo de 3 o 4 puntos de apoyo", "Arnés de cuerpo entero de 4 argollas certificado", "Eslinga de posicionamiento y eslinga en Y con absorbedor", "Botas de seguridad con puntera de acero / composite", "Guantes de vaqueta / carnaza para trabajo pesado"]
    },
    {
        "tipo": "Condiciones de Seguridad",
        "clasificacion": "Espacios Confinados",
        "descripcion": "Trabajo en tanques, pozos, silos, túneles o ductos con atmósfera potencialmente peligrosa.",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Barbuquejo de 3 o 4 puntos de apoyo", "Arnés de cuerpo entero de 4 argollas certificado", "Respirador de media cara con cartuchos para vapores orgánicos y gases", "Botas de seguridad con puntera de acero / composite"]
    },

    # ── FENÓMENOS NATURALES ──
    {
        "tipo": "Fenómenos Naturales",
        "clasificacion": "Sismo / Terremoto",
        "descripcion": "Eventos sísmicos que pueden generar colapso estructural o caída de objetos.",
        "epps": ["Casco de seguridad industrial dieléctrico (Clase E)", "Botas de seguridad con puntera de acero / composite"]
    },
    {
        "tipo": "Fenómenos Naturales",
        "clasificacion": "Precipitaciones e Inundaciones",
        "descripcion": "Lluvias torrenciales, granizadas, tormentas eléctricas y anegación de frentes de trabajo.",
        "epps": ["Botas de caucho impermeables de caña alta", "Delantal de PVC / caucho impermeable"]
    }
]


def seed_gtc45_and_epp_catalogs():
    """Siembra los catálogos en la base de datos si no existen."""
    # 1. Crear EPPs
    epp_map = {}
    for epp_data in CATALOGO_EPPS_DATA:
        epp_obj, _ = CatalogoEPP.objects.get_or_create(
            nombre=epp_data["nombre"],
            defaults={"descripcion": epp_data["descripcion"], "activo": True}
        )
        epp_map[epp_obj.nombre] = epp_obj

    # 2. Crear Peligros GTC 45 y asociar EPPs sugeridos
    for pel_data in CATALOGO_PELIGROS_DATA:
        pel_obj, _ = CatalogoPeligro.objects.get_or_create(
            tipo=pel_data["tipo"],
            clasificacion=pel_data["clasificacion"],
            defaults={"descripcion": pel_data["descripcion"], "activo": True}
        )
        # Asociar EPPs sugeridos
        epps_to_add = [epp_map[nombre] for nombre in pel_data.get("epps", []) if nombre in epp_map]
        if epps_to_add:
            pel_obj.epps_sugeridos.set(epps_to_add)

    return CatalogoPeligro.objects.count(), CatalogoEPP.objects.count()
