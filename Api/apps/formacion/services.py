"""
Servicios de cálculo y matriz de formación para trabajadores.
"""
from datetime import timedelta
from django.utils import timezone
from apps.formacion.models import (
    CursoFormacion,
    CargoRequisitoFormacion,
    RegistroFormacion
)


def calcular_matriz_formacion_trabajador(trabajador):
    """
    Evalúa la formación exigida por el cargo del trabajador frente a sus registros de formación.
    
    Toma en consideración:
    - Cursos obligatorios vs opcionales.
    - Cursos alternativos (mismo grupo_alternativo): si el trabajador cumple CUALQUIERA
      de los cursos del grupo alternativo (ej. Curso 50h o Curso 20h SST), el requerimiento
      del grupo se considera cumplido.
    - Estado de vigencia: 'vigente', 'por_vencer' (<= 30 días), 'vencido', o 'falta'.
    """
    perfil = trabajador.perfil_cargo
    if not perfil:
        return {
            "trabajador": {
                "id": str(trabajador.id),
                "nombre": trabajador.nombre,
                "documento": trabajador.documento,
                "cargo": trabajador.cargo or "Sin cargo",
                "perfil_cargo_id": None,
            },
            "cursos": [],
            "resumen": {
                "total_exigidos": 0,
                "cumplidos": 0,
                "por_vencer": 0,
                "vencidos": 0,
                "faltantes": 0,
                "porcentaje_cumplimiento": 100.0,
            }
        }

    requisitos = list(
        CargoRequisitoFormacion.objects.filter(perfil_cargo=perfil)
        .select_related("curso")
        .order_by("-obligatorio", "curso__nombre")
    )

    # Todos los registros de formación del trabajador
    registros = list(
        RegistroFormacion.objects.filter(trabajador=trabajador)
        .select_related("curso", "soporte")
        .order_by("-fecha_realizacion", "-created_at")
    )

    # Mapear los registros más recientes por curso_id
    registros_por_curso = {}
    for reg in registros:
        cid = str(reg.curso_id)
        if cid not in registros_por_curso:
            registros_por_curso[cid] = reg

    today = timezone.now().date()
    limite_por_vencer = today + timedelta(days=30)

    # Detectar qué grupos alternativos están cumplidos
    # Un grupo alternativo está cumplido si al menos uno de sus cursos tiene registro vigente o por_vencer
    grupos_satisfechos = {}  # {grupo_nombre: {curso_nombre, registro}}
    for req in requisitos:
        if req.grupo_alternativo:
            reg = registros_por_curso.get(str(req.curso_id))
            if reg:
                # Verificar si está vigente o por vencer
                if not reg.fecha_vencimiento or reg.fecha_vencimiento >= today:
                    if req.grupo_alternativo not in grupos_satisfechos:
                        grupos_satisfechos[req.grupo_alternativo] = {
                            "curso_id": str(req.curso_id),
                            "curso_nombre": req.curso.nombre,
                            "registro_id": str(reg.id),
                        }

    items_matriz = []
    total_exigidos_grupos = set()  # Para contar requisitos agrupados correctamente
    cumplidos_grupos = set()
    total_por_vencer = 0
    total_vencidos = 0

    cursos_procesados_ids = set()

    for req in requisitos:
        curso = req.curso
        cid = str(curso.id)
        cursos_procesados_ids.add(cid)
        reg = registros_por_curso.get(cid)

        # Clave única de exigencia (si tiene grupo_alternativo, se agrupa bajo ese identificador)
        clave_exigencia = f"grupo:{req.grupo_alternativo}" if req.grupo_alternativo else f"curso:{cid}"
        if req.obligatorio:
            total_exigidos_grupos.add(clave_exigencia)

        # Determinar estado
        estado = "falta"
        cumple = False
        alternativa_satisfecha = False
        alternativa_cubierta_por = None

        if reg:
            if not reg.fecha_vencimiento:
                estado = "vigente"
                cumple = True
            elif reg.fecha_vencimiento < today:
                estado = "vencido"
                cumple = False
            elif reg.fecha_vencimiento <= limite_por_vencer:
                estado = "por_vencer"
                cumple = True
            else:
                estado = "vigente"
                cumple = True
        else:
            # Si no tiene registro directo pero pertenece a un grupo alternativo satisfecho
            if req.grupo_alternativo and req.grupo_alternativo in grupos_satisfechos:
                info_alt = grupos_satisfechos[req.grupo_alternativo]
                if info_alt["curso_id"] != cid:
                    alternativa_satisfecha = True
                    alternativa_cubierta_por = info_alt["curso_nombre"]
                    cumple = True
                    estado = "cumple_alternativa"

        if cumple:
            if req.obligatorio:
                cumplidos_grupos.add(clave_exigencia)
            if estado == "por_vencer":
                total_por_vencer += 1
        else:
            if req.obligatorio and estado == "vencido":
                total_vencidos += 1

        reg_data = None
        if reg:
            soporte_data = None
            if reg.soporte:
                soporte_data = {
                    "id": str(reg.soporte.id),
                    "nombre": reg.soporte.nombre,
                    "url": reg.soporte.url,
                }
            reg_data = {
                "id": str(reg.id),
                "fecha_realizacion": reg.fecha_realizacion.isoformat() if reg.fecha_realizacion else None,
                "fecha_vencimiento": reg.fecha_vencimiento.isoformat() if reg.fecha_vencimiento else None,
                "estado_derivado": reg.estado_derivado,
                "dias_para_vencer": reg.dias_para_vencer,
                "origen": reg.origen,
                "origen_display": reg.get_origen_display(),
                "entidad_emisora": reg.entidad_emisora,
                "horas_duracion": reg.horas_duracion,
                "soporte": soporte_data,
            }

        items_matriz.append({
            "curso_id": cid,
            "curso_nombre": curso.nombre,
            "categoria": curso.categoria,
            "categoria_display": curso.get_categoria_display(),
            "requiere_certificado": curso.requiere_certificado,
            "obligatorio": req.obligatorio,
            "vigencia_meses": req.vigencia_meses,
            "grupo_alternativo": req.grupo_alternativo,
            "estado": estado,
            "cumple": cumple,
            "alternativa_satisfecha": alternativa_satisfecha,
            "alternativa_cubierta_por": alternativa_cubierta_por,
            "ultimo_registro": reg_data,
        })

    # Cursos completados por el trabajador que no están en los requisitos del perfil
    for cid, reg in registros_por_curso.items():
        if cid not in cursos_procesados_ids:
            curso = reg.curso
            soporte_data = None
            if reg.soporte:
                soporte_data = {
                    "id": str(reg.soporte.id),
                    "nombre": reg.soporte.nombre,
                    "url": reg.soporte.url,
                }
            items_matriz.append({
                "curso_id": cid,
                "curso_nombre": curso.nombre,
                "categoria": curso.categoria,
                "categoria_display": curso.get_categoria_display(),
                "requiere_certificado": curso.requiere_certificado,
                "obligatorio": False,
                "vigencia_meses": curso.vigencia_meses,
                "grupo_alternativo": None,
                "estado": reg.estado_derivado,
                "cumple": reg.estado_derivado in ["vigente", "por_vencer"],
                "alternativa_satisfecha": False,
                "alternativa_cubierta_por": None,
                "ultimo_registro": {
                    "id": str(reg.id),
                    "fecha_realizacion": reg.fecha_realizacion.isoformat() if reg.fecha_realizacion else None,
                    "fecha_vencimiento": reg.fecha_vencimiento.isoformat() if reg.fecha_vencimiento else None,
                    "estado_derivado": reg.estado_derivado,
                    "dias_para_vencer": reg.dias_para_vencer,
                    "origen": reg.origen,
                    "origen_display": reg.get_origen_display(),
                    "entidad_emisora": reg.entidad_emisora,
                    "horas_duracion": reg.horas_duracion,
                    "soporte": soporte_data,
                },
            })

    num_exigidos = len(total_exigidos_grupos)
    num_cumplidos = len(cumplidos_grupos)
    num_faltantes = max(0, num_exigidos - num_cumplidos)
    porcentaje = round((num_cumplidos / num_exigidos * 100.0), 1) if num_exigidos > 0 else 100.0

    return {
        "trabajador": {
            "id": str(trabajador.id),
            "nombre": trabajador.nombre,
            "documento": trabajador.documento,
            "cargo": perfil.nombre_cargo,
            "perfil_cargo_id": str(perfil.id),
        },
        "cursos": items_matriz,
        "resumen": {
            "total_exigidos": num_exigidos,
            "cumplidos": num_cumplidos,
            "por_vencer": total_por_vencer,
            "vencidos": total_vencidos,
            "faltantes": num_faltantes,
            "porcentaje_cumplimiento": porcentaje,
        }
    }
