"""
Informe gerencial de Reclutamiento & Selección (por vacante) con IA.

- Métricas agregadas y anonimizadas (sin PII) con umbral k=3.
- Narrativa generada con Gemini (vía IAInterpretacionService) y fallback Mock.
- Exportación a PDF presentable.
"""
import io
from datetime import date, datetime
from typing import Optional

from django.db.models import Count, Q
from django.utils import timezone

from apps.ia.service import IAInterpretacionService
from apps.reclutamiento.models import (
    Candidato,
    Entrevista,
    Evaluacion,
    Postulacion,
    PostulacionEvento,
    ValidacionDocumental,
)

K_ANONIMATO = 3


def _dias(desde, hasta) -> Optional[float]:
    if not desde or not hasta:
        return None
    if isinstance(desde, datetime):
        desde = desde.date()
    if isinstance(hasta, datetime):
        hasta = hasta.date()
    return round((hasta - desde).days, 1)


def _promedio(valores):
    valores = [v for v in valores if v is not None]
    if not valores:
        return None
    return round(sum(valores) / len(valores), 2)


def _anonimizar(conteo: dict, k: int = K_ANONIMATO) -> dict:
    """Oculta categorías con menos de k casos y las agrupa en 'Otros'."""
    visibles = {nombre: total for nombre, total in conteo.items() if total >= k}
    otros = sum(total for nombre, total in conteo.items() if total < k)
    if otros:
        visibles["Otros (<3)"] = otros
    return visibles


def _conteo(lista) -> dict:
    conteo = {}
    for valor in lista:
        clave = valor or "No especificado"
        conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def construir_metricas(empresa, vacante) -> dict:
    """Construye métricas agregadas y anonimizadas de una vacante."""
    postulaciones = Postulacion.objects.filter(
        empresa=empresa,
        proceso_seleccion__vacante=vacante,
        deleted_at__isnull=True,
    )
    total = postulaciones.count()

    estados = {clave: 0 for clave, _ in Postulacion.Estado.choices}
    for fila in postulaciones.values("estado").annotate(total=Count("id")):
        estados[fila["estado"]] = fila["total"]

    # Fuentes de reclutamiento
    estados_preseleccion = [
        Postulacion.Estado.PRESELECCIONADO,
        Postulacion.Estado.EN_ENTREVISTA,
        Postulacion.Estado.EN_EVALUACION,
        Postulacion.Estado.EN_VALIDACION,
        Postulacion.Estado.SELECCIONADO,
    ]
    estados_entrevista = [
        Postulacion.Estado.EN_ENTREVISTA,
        Postulacion.Estado.EN_EVALUACION,
        Postulacion.Estado.EN_VALIDACION,
        Postulacion.Estado.SELECCIONADO,
    ]
    fuentes = []
    for fila in (
        postulaciones.values("candidato__fuente_reclutamiento__nombre")
        .annotate(
            candidatos=Count("id", distinct=True),
            preseleccionados=Count("id", filter=Q_estado(estados_preseleccion), distinct=True),
            entrevistados=Count("id", filter=Q_estado(estados_entrevista), distinct=True),
            contratados=Count(
                "id", filter=Q_estado([Postulacion.Estado.SELECCIONADO]), distinct=True
            ),
        )
    ):
        candidatos = fila["candidatos"]
        contratados = fila["contratados"]
        fuentes.append({
            "nombre": fila["candidato__fuente_reclutamiento__nombre"] or "Sin fuente",
            "candidatos": candidatos,
            "preseleccionados": fila["preseleccionados"],
            "entrevistados": fila["entrevistados"],
            "contratados": contratados,
            "tasa_conversion": round((contratados / candidatos) * 100, 2) if candidatos else 0.0,
        })
    fuentes.sort(key=lambda f: f["candidatos"], reverse=True)

    # Perfiles de los candidatos que postularon (agregado y anonimizado)
    candidatos = Candidato.objects.filter(
        empresa=empresa,
        postulaciones__proceso_seleccion__vacante=vacante,
        postulaciones__deleted_at__isnull=True,
    ).distinct().select_related("perfil")

    perfiles = {
        "total_candidatos": candidatos.count(),
        "nivel_educativo": {},
        "experiencia": {},
        "ciudades": {},
        "competencias": [],
    }
    if perfiles["total_candidatos"] >= K_ANONIMATO:
        niveles, experiencias, ciudades, competencias = [], [], [], []
        for candidato in candidatos:
            perfil = getattr(candidato, "perfil", None)
            if perfil:
                niveles.append(perfil.nivel_educativo)
                anios = float(perfil.anios_experiencia or 0)
                if anios <= 1:
                    experiencias.append("0-1 año")
                elif anios <= 3:
                    experiencias.append("2-3 años")
                elif anios <= 5:
                    experiencias.append("4-5 años")
                else:
                    experiencias.append("6+ años")
                for competencia in (perfil.competencias or []):
                    if isinstance(competencia, str):
                        competencias.append(competencia)
            ciudades.append(candidato.ciudad)

        perfiles["nivel_educativo"] = _anonimizar(_conteo(niveles))
        perfiles["experiencia"] = _anonimizar(_conteo(experiencias))
        top_ciudades = _anonimizar(_conteo(ciudades))
        perfiles["ciudades"] = dict(sorted(top_ciudades.items(), key=lambda x: x[1], reverse=True)[:6])
        conteo_comp = _conteo(competencias)
        perfiles["competencias"] = [
            {"nombre": nombre, "total": total}
            for nombre, total in sorted(conteo_comp.items(), key=lambda x: x[1], reverse=True)[:8]
            if total >= K_ANONIMATO
        ]

    # Entrevistas
    entrevistas_qs = Entrevista.objects.filter(postulacion__in=postulaciones)
    calificaciones = [float(e.calificacion) for e in entrevistas_qs if e.calificacion is not None]
    entrevistas = {
        "total": entrevistas_qs.count(),
        "realizadas": entrevistas_qs.filter(estado=Entrevista.Estado.REALIZADA).count(),
        "favorables": entrevistas_qs.filter(concepto=Entrevista.Concepto.FAVORABLE).count(),
        "con_reservas": entrevistas_qs.filter(concepto=Entrevista.Concepto.CON_RESERVAS).count(),
        "desfavorables": entrevistas_qs.filter(concepto=Entrevista.Concepto.DESFAVORABLE).count(),
        "promedio_calificacion": _promedio(calificaciones),
    }

    # Evaluaciones
    evaluaciones_qs = Evaluacion.objects.filter(postulacion__in=postulaciones)
    porcentajes = [e.porcentaje_obtenido for e in evaluaciones_qs if e.porcentaje_obtenido is not None]
    clasificacion = {"critico": 0, "alerta": 0, "apto": 0}
    for pct in porcentajes:
        if pct <= 60:
            clasificacion["critico"] += 1
        elif pct < 81:
            clasificacion["alerta"] += 1
        else:
            clasificacion["apto"] += 1
    evaluaciones = {
        "total": evaluaciones_qs.count(),
        "aprobadas": evaluaciones_qs.filter(estado=Evaluacion.Estado.APROBADA).count(),
        "no_aprobadas": evaluaciones_qs.filter(estado=Evaluacion.Estado.NO_APROBADA).count(),
        "promedio_porcentaje": _promedio(porcentajes),
        "clasificacion": clasificacion,
    }

    # Validaciones documentales
    validaciones_qs = ValidacionDocumental.objects.filter(postulacion__in=postulaciones)
    validaciones = {clave: 0 for clave, _ in ValidacionDocumental.Estado.choices}
    for fila in validaciones_qs.values("estado").annotate(total=Count("id")):
        validaciones[fila["estado"]] = fila["total"]

    # Cumplimiento documental (requeridos por el proceso)
    requeridos = []
    try:
        if getattr(vacante, "proceso_seleccion", None):
            requeridos = vacante.proceso_seleccion.documentos_requeridos or []
    except Exception:
        requeridos = []
    documentos = {"requeridos": requeridos, "completos": 0, "con_faltantes": 0}
    if requeridos:
        for postulacion in postulaciones.select_related("candidato"):
            presentes = set(postulacion.candidato.documentos.values_list("tipo_documento", flat=True))
            if all(tipo in presentes for tipo in requeridos):
                documentos["completos"] += 1
            else:
                documentos["con_faltantes"] += 1

    # Tiempos
    hoy = timezone.now().date()
    inicio_vacante = vacante.created_at.date() if vacante.created_at else None
    cierre = vacante.fecha_cierre_real or (hoy if vacante.esta_cubierta else None)
    time_to_fill = _dias(inicio_vacante, cierre)

    tiempos_entrevista = []
    for postulacion in postulaciones:
        primera = postulacion.entrevistas.order_by("fecha_programada").first()
        if primera:
            tiempos_entrevista.append(_dias(postulacion.fecha_postulacion, primera.fecha_programada))

    tiempos_seleccion = []
    for evento in PostulacionEvento.objects.filter(
        postulacion__in=postulaciones,
        estado_nuevo=Postulacion.Estado.SELECCIONADO,
    ).select_related("postulacion"):
        tiempos_seleccion.append(_dias(evento.postulacion.fecha_postulacion, evento.created_at))

    primera_postulacion = postulaciones.order_by("fecha_postulacion").first()
    duracion_total = _dias(
        primera_postulacion.fecha_postulacion if primera_postulacion else None,
        cierre or hoy,
    )

    tiempos = {
        "time_to_fill_dias": time_to_fill,
        "postulacion_a_entrevista_dias": _promedio(tiempos_entrevista),
        "postulacion_a_seleccion_dias": _promedio(tiempos_seleccion),
        "duracion_total_dias": duracion_total,
    }

    # Perfil del cargo (contexto)
    perfil_cargo = None
    try:
        pc = vacante.perfil_cargo
        perfil_cargo = {
            "area": pc.area or "",
            "tipo_cargo": pc.get_tipo_cargo_display() if hasattr(pc, "get_tipo_cargo_display") else pc.tipo_cargo,
            "nivel_riesgo": pc.nivel_riesgo,
        }
    except Exception:
        perfil_cargo = None

    return {
        "vacante_codigo": vacante.codigo,
        "vacante_titulo": vacante.titulo,
        "cupos": vacante.numero_cupos,
        "estado_vacante": vacante.get_estado_display(),
        "perfil_cargo": perfil_cargo,
        "postulaciones": {"total": total, "por_estado": estados},
        "fuentes": fuentes,
        "perfiles": perfiles,
        "entrevistas": entrevistas,
        "evaluaciones": evaluaciones,
        "validaciones": validaciones,
        "documentos": documentos,
        "tiempos": tiempos,
    }


# Helper para los filtros de estado en las anotaciones
def Q_estado(estados):
    return Q(estado__in=estados)


def generar_informe_gerencial(empresa, vacante, forzar: bool = False) -> dict:
    metricas = construir_metricas(empresa, vacante)
    contexto = {
        "empresa_nombre": empresa.nombre,
        "vacante_codigo": metricas["vacante_codigo"],
        "vacante_titulo": metricas["vacante_titulo"],
        "cupos": metricas["cupos"],
        "estado_vacante": metricas["estado_vacante"],
        "perfil_cargo": metricas["perfil_cargo"],
        "postulaciones": metricas["postulaciones"],
        "fuentes": metricas["fuentes"],
        "perfiles": metricas["perfiles"],
        "entrevistas": metricas["entrevistas"],
        "evaluaciones": metricas["evaluaciones"],
        "validaciones": metricas["validaciones"],
        "documentos": metricas["documentos"],
        "tiempos": metricas["tiempos"],
    }
    ia = IAInterpretacionService.generar(
        "informe_gerencial_reclutamiento", contexto, forzar=forzar
    )
    return {
        "empresa": {"nombre": empresa.nombre, "nit": empresa.nit},
        "vacante": {
            "id": str(vacante.id),
            "codigo": vacante.codigo,
            "titulo": vacante.titulo,
            "estado": vacante.estado,
        },
        "metricas": metricas,
        "ia": ia,
        "generado_en": timezone.now().isoformat(),
        "confidencialidad": (
            "Informe agregado y anonimizado. No contiene datos personales "
            "(Ley 1581 de 2012). La IA apoya la lectura, no toma decisiones."
        ),
    }


def render_pdf(informe: dict) -> bytes:
    """Genera un PDF presentable del informe gerencial."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )
    from xml.sax.saxutils import escape

    def _e(value):
        return escape(str(value or ""))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"Informe gerencial {informe['vacante']['codigo']}",
    )
    styles = getSampleStyleSheet()
    azul = colors.HexColor("#002D62")
    titulo = ParagraphStyle("t", parent=styles["Title"], textColor=azul, fontSize=18, leading=22)
    h1 = ParagraphStyle("h1", parent=styles["Heading2"], textColor=azul, fontSize=12, leading=15, spaceBefore=10, spaceAfter=3)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=9, leading=12.5, spaceAfter=3)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=7.5, leading=10, textColor=colors.HexColor("#666666"))

    m = informe["metricas"]
    ia = informe.get("ia") or {}
    story = [
        Paragraph("Informe Gerencial — Reclutamiento &amp; Selección", titulo),
        Paragraph(f"{_e(informe['empresa']['nombre'])} · NIT {_e(informe['empresa']['nit'])}", small),
        Paragraph(
            f"Vacante: <b>{_e(m['vacante_codigo'])} — {_e(m['vacante_titulo'])}</b> · "
            f"Estado: {_e(m['estado_vacante'])} · Cupos: {_e(m['cupos'])}", body),
        Spacer(1, 6),
    ]

    def tabla(encabezado, filas):
        data = [encabezado] + filas
        t = Table(data, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), azul),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        return t

    # KPIs
    story.append(Paragraph("Indicadores generales", h1))
    story.append(tabla(["Métrica", "Valor"], [
        ["Postulaciones", str(m["postulaciones"]["total"])],
        ["Seleccionados", str(m["postulaciones"]["por_estado"].get("seleccionado", 0))],
        ["Entrevistas registradas", str(m["entrevistas"]["total"])],
        ["Evaluaciones registradas", str(m["evaluaciones"]["total"])],
        ["Promedio entrevistas", str(m["entrevistas"]["promedio_calificacion"] or "N/A")],
        ["Promedio evaluaciones (%)", str(m["evaluaciones"]["promedio_porcentaje"] or "N/A")],
        ["Time-to-fill (días)", str(m["tiempos"]["time_to_fill_dias"] or "N/A")],
    ]))

    # Embudo
    story.append(Paragraph("Embudo por estado", h1))
    story.append(tabla(
        ["Estado", "Total"],
        [[estado.replace("_", " ").capitalize(), str(total)] for estado, total in m["postulaciones"]["por_estado"].items()],
    ))

    # Fuentes
    if m["fuentes"]:
        story.append(Paragraph("Fuentes de reclutamiento", h1))
        story.append(tabla(
            ["Fuente", "Candidatos", "Preselecc.", "Entrevist.", "Contrat.", "% Conv."],
            [[f["nombre"], str(f["candidatos"]), str(f["preseleccionados"]),
              str(f["entrevistados"]), str(f["contratados"]), f"{f['tasa_conversion']}%"]
             for f in m["fuentes"]],
        ))

    # Perfiles (k-anonimizado)
    perfiles = m["perfiles"]
    if perfiles.get("total_candidatos", 0) >= K_ANONIMATO:
        story.append(Paragraph("Perfil de los candidatos (agregado y anonimizado)", h1))
        if perfiles["nivel_educativo"]:
            story.append(Paragraph(_e("Nivel educativo: " + ", ".join(f"{k}: {v}" for k, v in perfiles["nivel_educativo"].items())), body))
        if perfiles["experiencia"]:
            story.append(Paragraph(_e("Experiencia: " + ", ".join(f"{k}: {v}" for k, v in perfiles["experiencia"].items())), body))
        if perfiles["ciudades"]:
            story.append(Paragraph(_e("Ciudades: " + ", ".join(f"{k}: {v}" for k, v in perfiles["ciudades"].items())), body))
        if perfiles["competencias"]:
            story.append(Paragraph(_e("Competencias frecuentes: " + ", ".join(f"{c['nombre']} ({c['total']})" for c in perfiles["competencias"])), body))

    # Entrevistas / evaluaciones
    story.append(Paragraph("Resultados de entrevistas y evaluaciones", h1))
    story.append(tabla(["Indicador", "Valor"], [
        ["Entrevistas favorables", str(m["entrevistas"]["favorables"])],
        ["Entrevistas con reservas", str(m["entrevistas"]["con_reservas"])],
        ["Entrevistas desfavorables", str(m["entrevistas"]["desfavorables"])],
        ["Evaluaciones aprobadas", str(m["evaluaciones"]["aprobadas"])],
        ["Evaluaciones no aprobadas", str(m["evaluaciones"]["no_aprobadas"])],
        ["Clasificación crítico/alerta/apto", f"{m['evaluaciones']['clasificacion']['critico']}/"
                                              f"{m['evaluaciones']['clasificacion']['alerta']}/"
                                              f"{m['evaluaciones']['clasificacion']['apto']}"],
    ]))

    # Tiempos
    story.append(Paragraph("Tiempos del proceso", h1))
    story.append(tabla(["Indicador", "Días"], [
        ["Time-to-fill", str(m["tiempos"]["time_to_fill_dias"] or "N/A")],
        ["Postulación a entrevista", str(m["tiempos"]["postulacion_a_entrevista_dias"] or "N/A")],
        ["Postulación a selección", str(m["tiempos"]["postulacion_a_seleccion_dias"] or "N/A")],
        ["Duración total", str(m["tiempos"]["duracion_total_dias"] or "N/A")],
    ]))

    # Narrativa IA
    story.append(Paragraph("Análisis con IA", h1))
    if ia.get("resumen_ejecutivo"):
        story.append(Paragraph("<b>Resumen ejecutivo.</b> " + _e(ia["resumen_ejecutivo"]), body))
    for clave, etiqueta in [
        ("analisis_fuentes", "Fuentes"),
        ("analisis_perfiles", "Perfiles"),
        ("resultados_entrevistas", "Entrevistas y evaluaciones"),
        ("tiempos_y_eficiencia", "Tiempos y eficiencia"),
    ]:
        if ia.get(clave):
            story.append(Paragraph(f"<b>{etiqueta}.</b> " + _e(ia[clave]), body))

    for clave, etiqueta in [
        ("hallazgos_clave", "Hallazgos clave"),
        ("riesgos", "Riesgos"),
        ("recomendaciones", "Recomendaciones"),
    ]:
        valores = ia.get(clave) or []
        if valores:
            story.append(Paragraph(etiqueta, h1))
            for valor in valores:
                story.append(Paragraph("- " + _e(valor), body))

    if ia.get("conclusion_para_gerencia"):
        story.append(Paragraph("Conclusión para gerencia", h1))
        story.append(Paragraph(_e(ia["conclusion_para_gerencia"]), body))

    story.append(Spacer(1, 10))
    story.append(Paragraph(_e(informe.get("confidencialidad", "")), small))
    story.append(Paragraph(
        _e(f"Fuente del análisis: {ia.get('fuente', 'N/A')} · Generado: {informe.get('generado_en', '')}"),
        small,
    ))

    doc.build(story)
    return buffer.getvalue()
