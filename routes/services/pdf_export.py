"""
Exportação da rota como PDF usando ReportLab.
"""
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)


def generate_route_pdf(session, points: list) -> bytes:
    """
    Gera um PDF com o resumo e detalhes da rota.
    Retorna os bytes do PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # --- Cabeçalho ---
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=12,
    )

    story.append(Paragraph("Rota Otimizada — CCO", title_style))
    story.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} | ID: {str(session.id)[:8]}",
        subtitle_style,
    ))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#1a73e8')))
    story.append(Spacer(1, 0.4 * cm))

    # --- Resumo ---
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
    )
    bold_style = ParagraphStyle(
        'Bold',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
    )

    story.append(Paragraph("<b>Resumo da Rota</b>", bold_style))
    story.append(Spacer(1, 0.2 * cm))

    if session.origin_address:
        story.append(Paragraph(f"<b>Partida:</b> {session.origin_address}", summary_style))

    dist_km = session.total_distance_km or '—'
    dur_min = session.total_duration_min or '—'
    fuel_l = session.fuel_liters or '—'
    fuel_cost = session.fuel_cost or '—'

    summary_data = [
        ['Distância Total', f"{dist_km} km" if isinstance(dist_km, float) else dist_km],
        ['Tempo Estimado', f"{int(dur_min)} min ({int(dur_min)//60}h {int(dur_min)%60}min)" if isinstance(dur_min, float) else dur_min],
        ['Consumo estimado', f"{fuel_l} litros" if isinstance(fuel_l, float) else fuel_l],
        ['Custo estimado', f"R$ {fuel_cost:.2f}" if isinstance(fuel_cost, float) else fuel_cost],
        ['Qtd. de Pontos', str(len(points))],
        ['Rota Otimizada', 'Sim' if session.is_optimized else 'Não'],
    ]

    summary_table = Table(summary_data, colWidths=[6 * cm, 8 * cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f3f4')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.6 * cm))

    # --- Lista de pontos ---
    story.append(Paragraph("<b>Sequência de Paradas</b>", bold_style))
    story.append(Spacer(1, 0.3 * cm))

    headers = ['#', 'Endereço', 'Dist. próx.', 'Tempo próx.']
    rows = [headers]

    for p in points:
        dist_str = f"{p.distance_to_next_km} km" if p.distance_to_next_km else '—'
        dur_str = f"{p.duration_to_next_min} min" if p.duration_to_next_min else '—'
        addr = p.formatted_address or p.address
        rows.append([str(p.order), addr[:60], dist_str, dur_str])

    points_table = Table(rows, colWidths=[1 * cm, 11 * cm, 2.5 * cm, 2.5 * cm])
    points_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dadce0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(points_table)

    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.grey))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey)
    story.append(Paragraph(
        "Documento gerado automaticamente pelo sistema CCO — Gerador de Rotas.",
        footer_style,
    ))

    doc.build(story)
    return buffer.getvalue()
