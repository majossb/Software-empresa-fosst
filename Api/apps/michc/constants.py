"""
Configuración de Escalas de Semaforización del MICHC (§3.1 / Resultado 2 vs Resultado 3 del documento de módulos v02).

Nota de Diseño:
El documento de módulos contiene dos escalas distintas:
- Escala de 3 tramos (Sección 3.1): 100% Cumple (Verde) / 80-99% Parcial (Amarillo) / <80% Intervención (Rojo)
- Escala de 4 tramos (Resultado 3): 95-100% Habilitado / 80-94% Habilitado con observaciones / 70-79% Habilitación condicionada / <70% No Habilitado

Esta configuración abstrae ambas escalas en constantes centralizadas de forma que el cliente pueda alternar entre ellas
vía configuración de entorno o preferencia de negocio, sin modificar la lógica de negocio en engine.py.
"""

from typing import Tuple
from django.conf import settings

# Modos soportados: '3_TRAMOS' o '4_TRAMOS'
ESCALA_MICHC_MODO = getattr(settings, "MICHC_ESCALA_MODO", "3_TRAMOS")


def determinar_semaforo_y_estado(porcentaje: float, modo: str = None) -> Tuple[str, str]:
    """
    Recibe un porcentaje de cumplimiento (0.0 a 100.0) y retorna (semaforo, estado_habilitacion)
    según el modo configurado.
    """
    modo_activo = modo or ESCALA_MICHC_MODO

    if modo_activo == "4_TRAMOS":
        if porcentaje >= 95.0:
            return "verde", "habilitado"
        elif porcentaje >= 80.0:
            return "amarillo", "habilitado_con_observaciones"
        elif porcentaje >= 70.0:
            return "amarillo", "habilitacion_condicionada"
        else:
            return "rojo", "no_habilitado"
    else:
        # 3 Tramos por defecto
        if porcentaje >= 100.0:
            return "verde", "habilitado"
        elif porcentaje >= 80.0:
            return "amarillo", "habilitado_con_observaciones"
        else:
            return "rojo", "no_habilitado"
