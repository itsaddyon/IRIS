"""
report.py — Generates a PDF inspection report for approved High severity potholes.
Includes vehicle number, GPS coordinates, snapshots, and session details.
Install: pip install reportlab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, Image as RLImage, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from datetime import datetime
import os

def generate_report(detections, output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    elements = []

    title_s = ParagraphStyle('t', fontSize=18, alignment=TA_CENTER,
                              textColor=colors.HexColor('#1a1a2e'),
                              spaceAfter=4, fontName='Helvetica-Bold')
    sub_s   = ParagraphStyle('s', fontSize=9, alignment=TA_CENTER,
                              textColor=colors.grey, spaceAfter=4)
    cell_s  = ParagraphStyle('c', fontSize=7, leading=9)

    # ── Header ─────────────────────────────────────────────
    elements.append(Paragraph("IRIS – Road Inspection Report", title_s))
    elements.append(Paragraph("Intelligent Road Inspection System | Team Grey Hats | Technomax 2026", sub_s))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}  |  "
        f"Total Approved Potholes: {len(detections)}", sub_s))
    elements.append(HRFlowable(width="100%", thickness=1,
                                color=colors.HexColor('#2563eb'), spaceAfter=14))

    # ── Vehicle summary block ───────────────────────────────
    # Group by vehicle
    vehicles = {}
    for d in detections:
        vid = d.get('vehicle_id') or 'Unknown'
        vehicles[vid] = vehicles.get(vid, 0) + 1

    if len(vehicles) > 1:
        v_data = [['Vehicle ID', 'Approved Potholes']]
        for vid, cnt in sorted(vehicles.items(), key=lambda x: -x[1]):
            v_data.append([vid, str(cnt)])
        v_table = Table(v_data, colWidths=[10*cm, 6*cm], repeatRows=1)
        v_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0),(-1,0), colors.HexColor('#2563eb')),
            ('TEXTCOLOR',   (0,0),(-1,0), colors.white),
            ('FONTNAME',    (0,0),(-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0,0),(-1,-1), 8),
            ('ALIGN',       (0,0),(-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#eff6ff')]),
            ('GRID',        (0,0),(-1,-1), 0.4, colors.HexColor('#dde')  ),
        ]))
        elements.append(Paragraph("Vehicle-wise Summary", ParagraphStyle(
            'vh', fontSize=10, fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a1a2e'), spaceAfter=6)))
        elements.append(v_table)
        elements.append(Spacer(1, 0.5*cm))

    # ── Main detections table ───────────────────────────────
    header = ['#', 'Vehicle', 'Timestamp', 'Confidence', 'GPS Coordinates', 'Snapshot']
    rows   = [header]

    for i, d in enumerate(detections, 1):
        loc  = d.get('location') or '—'
        conf = f"{float(d['confidence'])*100:.1f}%"
        vid  = d.get('vehicle_id') or '—'
        photo = d.get('photo_path')
        if photo and os.path.exists(photo):
            try:
                snap = RLImage(photo, width=2.5*cm, height=1.8*cm)
            except Exception:
                snap = Paragraph('(error)', cell_s)
        else:
            snap = Paragraph('No image', cell_s)

        rows.append([
            str(i),
            Paragraph(vid, cell_s),
            Paragraph(d['timestamp'], cell_s),
            conf,
            Paragraph(loc, cell_s),
            snap
        ])

    col_w = [0.7*cm, 3.2*cm, 3.5*cm, 1.8*cm, 4.3*cm, 2.5*cm]
    table = Table(rows, colWidths=col_w, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',     (0,0),(-1,0),  colors.HexColor('#2563eb')),
        ('TEXTCOLOR',      (0,0),(-1,0),  colors.white),
        ('FONTNAME',       (0,0),(-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0),(-1,0),  8),
        ('ALIGN',          (0,0),(-1,-1), 'CENTER'),
        ('VALIGN',         (0,0),(-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1),(-1,-1), [colors.white, colors.HexColor('#eff6ff')]),
        ('GRID',           (0,0),(-1,-1), 0.4, colors.HexColor('#dde')),
        ('FONTSIZE',       (0,1),(-1,-1), 7),
        ('TOPPADDING',     (0,0),(-1,-1), 4),
        ('BOTTOMPADDING',  (0,0),(-1,-1), 4),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.4*cm))

    # ── Footer ─────────────────────────────────────────────
    foot_s = ParagraphStyle('f', fontSize=7, alignment=TA_CENTER,
                             textColor=colors.grey)
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "Auto-generated by IRIS | Intelligent Road Inspection System | "
        "Approved potholes only | Dispatch repair teams to GPS coordinates above.",
        foot_s))
    doc.build(elements)
    return output_path
