"""
Definición centralizada de la escala de niveles de competencias (1 a 5).

Requerimientos FOSST VIDA - Fase 1:
- 1: Básico (nombre por confirmar)
- 2: En desarrollo (nombre por confirmar)
- 3: Autónomo (definido por cliente)
- 4: Dominio avanzado (definido por cliente)
- 5: Referente (definido por cliente)

Centralizado en un único lugar para eliminar números y textos mágicos repetidos.
"""

NIVEL_MINIMO = 1
NIVEL_MAXIMO = 5

ESCALA_NIVELES_COMPETENCIA = {
    1: {
        "numero": 1,
        "nombre": "Básico",
        "por_confirmar": True,
        "descripcion": "Conocimiento inicial o teórico; requiere supervisión y acompañamiento constante.",
    },
    2: {
        "numero": 2,
        "nombre": "En desarrollo",
        "por_confirmar": True,
        "descripcion": "Aplica los conocimientos y habilidades en tareas rutinarias con supervisión periódica.",
    },
    3: {
        "numero": 3,
        "nombre": "Autónomo",
        "por_confirmar": False,
        "descripcion": "Ejecuta de forma independiente y eficaz en situaciones habituales del cargo.",
    },
    4: {
        "numero": 4,
        "nombre": "Dominio avanzado",
        "por_confirmar": False,
        "descripcion": "Domina la competencia en situaciones complejas, resuelve imprevistos y orienta a otros.",
    },
    5: {
        "numero": 5,
        "nombre": "Referente",
        "por_confirmar": False,
        "descripcion": "Modelo de excelencia, líder metodológico, genera buenas prácticas y transfiere conocimiento.",
    },
}

NIVELES_CHOICES = [
    (nivel, f"{nivel} - {info['nombre']}")
    for nivel, info in ESCALA_NIVELES_COMPETENCIA.items()
]

# Mapa flexible para parsear texto o números a nivel entero (1..5)
MAPA_NIVELES_PARSER = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5,
    "básico": 1, "basico": 1,
    "en desarrollo": 2, "intermedio": 2,
    "autónomo": 3, "autonomo": 3, "avanzado": 3,
    "dominio avanzado": 4, "experto": 4,
    "referente": 5,
}

def obtener_nombre_nivel(nivel: int) -> str:
    try:
        info = ESCALA_NIVELES_COMPETENCIA.get(int(nivel) if nivel else 0)
        return info["nombre"] if info else f"Nivel {nivel}"
    except (ValueError, TypeError):
        return str(nivel)

def parse_nivel(valor, default=3) -> int:
    if valor is None:
        return default
    if isinstance(valor, int) and NIVEL_MINIMO <= valor <= NIVEL_MAXIMO:
        return valor
    val_str = str(valor).strip().lower()
    return MAPA_NIVELES_PARSER.get(val_str, default)
