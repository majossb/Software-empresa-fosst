"""
Servicios de cálculo de indicadores de accidentalidad (IFA, ISA, Tasa Accidentalidad)
y generación de plantilla oficial FURAT en PDF (RF-CAP-02).
"""

import io
from datetime import datetime
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def calcular_indicadores_accidentalidad(empresa, anio: int = None) -> Dict[str, Any]:
    """
    Calcula indicadores oficiales de accidentalidad SG-SST (Res. 0312 de 2019):
    - Tasa de Accidentalidad: (Nº accidentes en el año / Nº promedio trabajadores) * 100
    - Índice de Frecuencia de Accidentalidad (IFA): (Nº accidentes / Horas Hombre Trabajadas) * 240.000
    - Índice de Severidad de Accidentalidad (ISA): (Días incapacidad / Horas Hombre Trabajadas) * 240.000
    - ILI (Índice de Lesión Incapacitante): (IFA * ISA) / 1.000
    """
    if not anio:
        anio = datetime.now().year

    from apps.calendario.models import Incidente
    from apps.capacitaciones.models import Trabajador

    # Obtener incidentes del año de la empresa
    incidentes_qs = Incidente.objects.filter(
        empresa=empresa,
        fecha__year=anio,
        deleted_at__isnull=True
    )

    num_accidentes = incidentes_qs.filter(tipo=Incidente.Tipo.ACCIDENTE).count()
    num_incidentes = incidentes_qs.filter(tipo=Incidente.Tipo.INCIDENTE).count()
    num_enfermedades = incidentes_qs.filter(tipo=Incidente.Tipo.ENFERMEDAD_LABORAL).count()

    total_dias_incapacidad = sum(
        inc.dias_incapacidad or 0 for inc in incidentes_qs if inc.dias_incapacidad
    )

    num_trabajadores = Trabajador.objects.filter(
        empresa=empresa,
        deleted_at__isnull=True
    ).count() or 1

    # Estimar Horas Hombre Trabajadas (HHT): trabajadores * 48 hrs/semana * 48 semanas aprox
    horas_hombre_trabajadas = num_trabajadores * 2304

    tasa_accidentalidad = round((num_accidentes / num_trabajadores) * 100, 2)
    ifa = round((num_accidentes / horas_hombre_trabajadas) * 240000, 2) if horas_hombre_trabajadas > 0 else 0.0
    isa = round((total_dias_incapacidad / horas_hombre_trabajadas) * 240000, 2) if horas_hombre_trabajadas > 0 else 0.0
    ili = round((ifa * isa) / 1000, 2)

    return {
        "anio": anio,
        "num_trabajadores": num_trabajadores,
        "horas_hombre_trabajadas": horas_hombre_trabajadas,
        "num_accidentes": num_accidentes,
        "num_incidentes": num_incidentes,
        "num_enfermedades_laborales": num_enfermedades,
        "total_dias_incapacidad": total_dias_incapacidad,
        "tasa_accidentalidad": tasa_accidentalidad,
        "indice_frecuencia_ifa": ifa,
        "indice_severidad_isa": isa,
        "indice_lesion_incapacitante_ili": ili,
    }


def generar_plantilla_furat_pdf(incidente) -> bytes:
    """
    Genera el formato único de reporte de accidente de trabajo (FURAT) en PDF.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado FURAT
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 50, "FURAT — Formato Único de Reporte de Accidente de Trabajo")

    p.setFont("Helvetica", 9)
    p.drawString(50, height - 65, "Ministerio del Trabajo / ARL Colombia")
    p.drawString(400, height - 65, f"Código Único: FURAT-{incidente.id}")

    p.setStrokeColor(colors.HexColor("#1E3A8A"))
    p.setLineWidth(1.5)
    p.line(50, height - 75, width - 50, height - 75)

    y = height - 95

    # 1. Datos del Empleador
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "1. IDENTIFICACIÓN DEL EMPLEADOR")
    y -= 15
    p.setFont("Helvetica", 10)
    empresa = incidente.empresa
    p.drawString(60, y, f"Razón Social: {empresa.nombre}")
    p.drawString(350, y, f"NIT: {empresa.nit}")
    y -= 15
    p.drawString(60, y, f"Actividad Económica (CIIU): {getattr(empresa, 'ciiu_codigo', None) or getattr(empresa, 'ciiu_code', 'N/A')}")
    p.drawString(350, y, f"Nivel de Riesgo ARL: {empresa.nivel_riesgo}")
    y -= 25

    # 2. Datos del Accidente
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "2. INFORMACIÓN DEL ACCIDENTE / INCIDENTE")
    y -= 15
    p.setFont("Helvetica", 10)
    p.drawString(60, y, f"Tipo de Evento: {incidente.get_tipo_display()}")
    p.drawString(350, y, f"Fecha/Hora: {incidente.fecha.strftime('%Y-%m-%d %H:%M')}")
    y -= 15
    p.drawString(60, y, f"Días de Incapacidad Asignados: {incidente.dias_incapacidad or 0}")
    p.drawString(350, y, f"Estado de Investigación: {incidente.estado_investigacion.title()}")
    y -= 25

    # 3. Descripción del Evento
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "3. DESCRIPCIÓN DETALLADA DEL EVENTO")
    y -= 15
    p.setFont("Helvetica", 9)

    desc = incidente.descripcion or "Sin descripción registrada."
    lines = [desc[i:i+80] for i in range(0, len(desc), 80)]
    for line in lines:
        p.drawString(60, y, line)
        y -= 12

    y -= 20
    p.setStrokeColor(colors.gray)
    p.setLineWidth(0.5)
    p.line(50, y, width - 50, y)
    y -= 20

    # Nota Legal
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.gray)
    p.drawString(50, y, "Documento generado automáticamente por FOSST V.I.D.A. conforme a estándares ARL Colombia.")

    p.showPage()
    p.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
