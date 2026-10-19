"""
Catálogo de fuentes de reclutamiento: helper de fuentes de sistema por empresa.
"""
from apps.reclutamiento.models import FuenteReclutamiento

FUENTES_SISTEMA = [
    "Portal Web",
    "Referido",
    "LinkedIn",
    "Servicio Público de Empleo",
    "Redes sociales",
    "Registro manual",
]


def asegurar_fuentes_sistema(empresa):
    """Crea (si no existen) las fuentes semilla para una empresa."""
    if not empresa:
        return []
    existentes = set(
        FuenteReclutamiento.objects.filter(empresa=empresa).values_list("nombre", flat=True)
    )
    nuevas = [
        FuenteReclutamiento(empresa=empresa, nombre=nombre, es_sistema=True)
        for nombre in FUENTES_SISTEMA
        if nombre not in existentes
    ]
    if nuevas:
        FuenteReclutamiento.objects.bulk_create(nuevas, ignore_conflicts=True)
    return list(FuenteReclutamiento.objects.filter(empresa=empresa, activo=True))


def obtener_o_crear_fuente_portal(empresa):
    """Devuelve la fuente 'Portal Web' de la empresa (la crea si falta)."""
    fuente, _ = FuenteReclutamiento.objects.get_or_create(
        empresa=empresa,
        nombre="Portal Web",
        defaults={"es_sistema": True},
    )
    return fuente
