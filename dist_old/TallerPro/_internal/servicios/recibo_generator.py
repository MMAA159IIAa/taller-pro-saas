import os
import tempfile
from datetime import datetime
from utils.database import get_config
from utils.logger import info, error

def generar_recibo(nombre, auto, servicio, fecha, costo, id_registro):
    """Genera recibo PDF. Requiere: pip install reportlab"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        taller   = get_config("taller_nombre", "Taller Pro")
        tel      = get_config("taller_tel", "")
        correo   = get_config("smtp_email", "")

        ruta = os.path.join(tempfile.gettempdir(), f"recibo_{id_registro}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        doc  = SimpleDocTemplate(ruta, pagesize=letter,
                                  rightMargin=50, leftMargin=50,
                                  topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        elements = []

        # Título
        titulo = ParagraphStyle("titulo", fontSize=24, textColor=colors.HexColor("#e8a020"),
                                 alignment=TA_CENTER, fontName="Helvetica-Bold")
        subtitulo = ParagraphStyle("sub", fontSize=11, textColor=colors.grey, alignment=TA_CENTER)
        normal = ParagraphStyle("normal", fontSize=11, textColor=colors.black)
        label  = ParagraphStyle("label", fontSize=10, textColor=colors.grey)

        elements.append(Paragraph(taller, titulo))
        elements.append(Spacer(1, 6))
        if tel:   elements.append(Paragraph(f"Tel: {tel}", subtitulo))
        if correo: elements.append(Paragraph(correo, subtitulo))
        elements.append(Spacer(1, 12))
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#e8a020")))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"RECIBO DE SERVICIO", ParagraphStyle("rec", fontSize=16,
                                   fontName="Helvetica-Bold", alignment=TA_CENTER)))
        elements.append(Paragraph(f"No. {id_registro:04d}   |   Fecha: {fecha}",
                                   ParagraphStyle("meta", fontSize=10, textColor=colors.grey, alignment=TA_CENTER)))
        elements.append(Spacer(1, 20))

        # Datos
        data = [
            ["Cliente:",  nombre],
            ["Vehiculo:", auto],
            ["Servicio:", servicio],
            ["Fecha:",    fecha],
            ["",          ""],
            ["TOTAL:",    f"${float(costo):,.2f}"],
        ]
        tabla = Table(data, colWidths=[120, 340])
        tabla.setStyle(TableStyle([
            ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTSIZE",  (0,0), (-1,-1), 12),
            ("TEXTCOLOR", (0,-1), (-1,-1), colors.HexColor("#e8a020")),
            ("FONTSIZE",  (0,-1), (-1,-1), 16),
            ("FONTNAME",  (0,-1), (-1,-1), "Helvetica-Bold"),
            ("TOPPADDING",(0,0), (-1,-1), 6),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("LINEABOVE", (0,-1), (-1,-1), 1.5, colors.HexColor("#e8a020")),
        ]))
        elements.append(tabla)
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Gracias por su preferencia.", subtitulo))

        doc.build(elements)
        info("ReciboGenerator", f"Recibo generado: {ruta}")
        return ruta

    except ImportError:
        error("ReciboGenerator", "reportlab no instalado. Ejecuta: pip install reportlab")
        return None
    except Exception as ex:
        error("ReciboGenerator", f"Error generando recibo: {ex}")
        return None
