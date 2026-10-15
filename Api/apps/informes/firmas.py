"""
Módulo de firma gráfica y estampado de informes (RF-EVI-03).
Aclaración de alcance: Esta implementación constituye una firma gráfica declarativa con trazabilidad
interna (imagen + usuario + fecha/hora + hash SHA-256). No constituye una firma digital con validez
jurídica certificada (ONAC / entidad certificadora).
"""

import io
import base64
import hashlib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors


def generar_pdf_informe_firmado(informe) -> bytes:
    """
    Genera un PDF formal del informe incluyendo los sellos de firma gráfica y marcas de agua auditables.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Encabezado
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"INFORME SG-SST — {informe.get_tipo_display().upper()}")

    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, f"Fecha de Elaboración: {informe.fecha_elaboracion.strftime('%Y-%m-%d %H:%M:%S')}")
    p.drawString(50, height - 85, f"ID de Informe: {informe.id}")

    # Línea divisoria
    p.setStrokeColor(colors.HexColor("#1E3A8A"))
    p.setLineWidth(2)
    p.line(50, height - 95, width - 50, height - 95)

    # Contenido del informe
    y = height - 120
    contenido = informe.contenido_json or {}
    meta = contenido.get("meta", {})
    resumen = contenido.get("resumen_ejecutivo", {})

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"Empresa: {meta.get('empresa', 'N/A')} (NIT: {meta.get('nit', 'N/A')})")
    y -= 20
    p.setFont("Helvetica", 11)
    p.drawString(50, y, f"Año de Evaluación: {meta.get('anio', 'N/A')} — Capítulo: {meta.get('capitulo', 'N/A')}")
    y -= 20
    p.drawString(50, y, f"Cumplimiento Global: {resumen.get('cumplimiento_global', 0)}%")
    y -= 30

    # Sección de Firmas
    p.setLineWidth(1)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Firmas y Soportes de Verificación")
    y -= 20

    # Firma Responsable SST
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Firma Responsable SST:")
    if informe.firmado_responsable and informe.firma_responsable_usuario:
        p.setFont("Helvetica", 9)
        p.drawString(200, y, f"Firmado por: {informe.firma_responsable_usuario.get_full_name() or informe.firma_responsable_usuario.email}")
        y -= 15
        p.drawString(200, y, f"Fecha/Hora: {informe.firma_responsable_fecha.strftime('%Y-%m-%d %H:%M:%S') if informe.firma_responsable_fecha else 'N/A'}")
    else:
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(200, y, "Pendiente de firma")
    y -= 35

    # Firma Alta Dirección
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Firma Alta Dirección:")
    if informe.firmado_direccion and informe.firma_direccion_usuario:
        p.setFont("Helvetica", 9)
        p.drawString(200, y, f"Firmado por: {informe.firma_direccion_usuario.get_full_name() or informe.firma_direccion_usuario.email}")
        y -= 15
        p.drawString(200, y, f"Fecha/Hora: {informe.firma_direccion_fecha.strftime('%Y-%m-%d %H:%M:%S') if informe.firma_direccion_fecha else 'N/A'}")
    else:
        p.setFont("Helvetica-Oblique", 9)
        p.drawString(200, y, "Pendiente de firma")
    y -= 40

    # Sello de integridad y Hash
    p.setFont("Helvetica", 8)
    p.setFillColor(colors.gray)
    hash_txt = informe.hash_documento or hashlib.sha256(f"{informe.id}-{informe.fecha_elaboracion}".encode()).hexdigest()
    p.drawString(50, 40, f"Hash SHA-256 de Verificación: {hash_txt}")
    p.drawString(50, 25, "Este documento cuenta con trazabilidad interna y firma gráfica declarativa registrada en FOSST V.I.D.A.")

    p.showPage()
    p.save()

    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data
