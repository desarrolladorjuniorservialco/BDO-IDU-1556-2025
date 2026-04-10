"""
pdf_generator.py — Generación de PDF de Bitácora Digital
Usa reportlab. Instalar: pip install reportlab
"""

import io
import math
from datetime import datetime, date

import pandas as pd


def generate_pdf_bitacora(
    df: pd.DataFrame,
    contrato: dict,
    fi: date,
    ff: date,
    tipo_reporte: str,
    secciones: list[str],
) -> bytes | None:
    """
    Genera el PDF de bitácora.

    Retorna los bytes del PDF, o None si reportlab no está instalado.
    """
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer, HRFlowable,
        )
    except ImportError:
        return None

    # ── Configuración del documento ────────────────────────
    buf    = io.BytesIO()
    PAGE   = landscape(A4)
    MARGIN = 1.8 * cm

    doc = SimpleDocTemplate(
        buf, pagesize=PAGE,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN,   bottomMargin=MARGIN,
    )

    W = PAGE[0] - 2 * MARGIN  # ancho útil

    # ── Paleta de colores ──────────────────────────────────
    C_DARK   = rl_colors.HexColor('#1c2340')
    C_BLUE   = rl_colors.HexColor('#1a56db')
    C_GREEN  = rl_colors.HexColor('#0d7a4e')
    C_RED    = rl_colors.HexColor('#b91c1c')
    C_LGRAY  = rl_colors.HexColor('#f2f4f8')
    C_MGRAY  = rl_colors.HexColor('#dde2eb')
    C_TEXT   = rl_colors.HexColor('#111827')
    C_MUTED  = rl_colors.HexColor('#6b7280')
    C_WHITE  = rl_colors.white

    # ── Estilos tipográficos ───────────────────────────────
    base = getSampleStyleSheet()

    S = {
        'title': ParagraphStyle('title', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=16,
            textColor=C_WHITE),
        'sub': ParagraphStyle('sub', parent=base['Normal'],
            fontName='Helvetica', fontSize=8,
            textColor=rl_colors.HexColor('#c8d0e0')),
        'section': ParagraphStyle('section', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=9,
            textColor=C_BLUE, spaceBefore=8, spaceAfter=4),
        'info_key': ParagraphStyle('ik', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7.5, textColor=C_MUTED),
        'info_val': ParagraphStyle('iv', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5, textColor=C_TEXT, leading=10),
        'th': ParagraphStyle('th', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_WHITE, alignment=TA_CENTER),
        'td': ParagraphStyle('td', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, leading=10),
        'small': ParagraphStyle('small', parent=base['Normal'],
            fontName='Helvetica', fontSize=6.5, textColor=C_MUTED),
        'firma': ParagraphStyle('firma', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, alignment=TA_CENTER),
    }

    story = []

    # ── ENCABEZADO ─────────────────────────────────────────
    hdr_data = [[
        Paragraph('BITÁCORA DIGITAL DE OBRA', S['title']),
        Paragraph(
            f"Período: {fi.strftime('%d/%m/%Y')} — {ff.strftime('%d/%m/%Y')}<br/>"
            f"{tipo_reporte}",
            S['sub'],
        ),
        Paragraph(
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            S['sub'],
        ),
    ]]
    hdr_tbl = Table(hdr_data, colWidths=[W * 0.50, W * 0.30, W * 0.20])
    hdr_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), C_DARK),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING',   (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.3 * cm))

    # ── INFORMACIÓN DEL CONTRATO ───────────────────────────
    if contrato:
        info_rows = [
            [Paragraph('Contrato',    S['info_key']),
             Paragraph(contrato.get('numero', 'IDU-1556-2025'), S['info_val'])],
            [Paragraph('Contratista', S['info_key']),
             Paragraph(contrato.get('contratista', 'SERVIALCO S.A.S.'), S['info_val'])],
            [Paragraph('Entidad',     S['info_key']),
             Paragraph(contrato.get('entidad', 'IDU'), S['info_val'])],
            [Paragraph('Objeto',      S['info_key']),
             Paragraph(contrato.get('objeto', '—'), S['info_val'])],
        ]
        info_tbl = Table(info_rows, colWidths=[2.5 * cm, W - 2.5 * cm])
        info_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (0, -1), C_LGRAY),
            ('GRID',         (0, 0), (-1, -1), 0.4, C_MGRAY),
            ('LEFTPADDING',  (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING',   (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ]))
        story.append(Paragraph('INFORMACIÓN DEL CONTRATO', S['section']))
        story.append(info_tbl)
        story.append(Spacer(1, 0.3 * cm))

    # ── RESUMEN ESTADÍSTICO ────────────────────────────────
    if not df.empty:
        total     = len(df)
        apr       = len(df[df['estado'] == 'APROBADO'])   if 'estado' in df else 0
        rev       = len(df[df['estado'] == 'REVISADO'])   if 'estado' in df else 0
        dev       = len(df[df['estado'] == 'DEVUELTO'])   if 'estado' in df else 0
        bor       = len(df[df['estado'] == 'BORRADOR'])   if 'estado' in df else 0
        sum_cant  = (df['cantidad'].apply(_safe_float).sum()
                     if 'cantidad' in df else 0)

        res_header = ['Registros', 'Aprobados', 'Revisados', 'Devueltos',
                      'Borradores', 'Suma cantidades']
        res_values = [str(total), str(apr), str(rev), str(dev),
                      str(bor), f"{sum_cant:,.2f}"]

        res_tbl = Table(
            [res_header, res_values],
            colWidths=[W / 6] * 6,
        )
        res_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0), C_BLUE),
            ('TEXTCOLOR',    (0, 0), (-1, 0), C_WHITE),
            ('FONT',         (0, 0), (-1, 0), 'Helvetica-Bold', 7.5),
            ('BACKGROUND',   (0, 1), (-1, 1), C_LGRAY),
            ('FONT',         (0, 1), (-1, 1), 'Helvetica-Bold', 9),
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID',         (0, 0), (-1, -1), 0.4, C_MGRAY),
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
        ]))
        story.append(Paragraph('RESUMEN DEL PERÍODO', S['section']))
        story.append(res_tbl)
        story.append(Spacer(1, 0.3 * cm))

    # ── TABLA DE REGISTROS ─────────────────────────────────
    if not df.empty and 'Registro de actividades' in secciones:
        _build_records_table(story, df, S, C_DARK, C_LGRAY, C_MGRAY, C_WHITE, W)

    # ── FIRMAS ────────────────────────────────────────────
    if 'Firmas' in secciones:
        story.append(Spacer(1, 0.6 * cm))
        story.append(HRFlowable(width=W, thickness=0.5, color=C_MGRAY))
        story.append(Spacer(1, 0.3 * cm))
        firma_data = [
            ['_' * 35, '_' * 35, '_' * 35],
            ['Residente de Obra', 'Interventor IDU', 'Supervisor IDU'],
        ]
        firma_tbl = Table(firma_data, colWidths=[W / 3] * 3)
        firma_tbl.setStyle(TableStyle([
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('FONT',         (0, 0), (-1, 0), 'Helvetica',      8),
            ('FONT',         (0, 1), (-1, 1), 'Helvetica-Bold', 7),
            ('TEXTCOLOR',    (0, 1), (-1, 1), C_MUTED),
            ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ]))
        story.append(firma_tbl)

    # ── Construcción final ─────────────────────────────────
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(
            MARGIN, 0.9 * cm,
            f"BDO IDU-1556-2025  ·  Grupo 4  ·  SERVIALCO S.A.S.  ·  "
            f"{datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        canvas.drawRightString(
            PAGE[0] - MARGIN, 0.9 * cm,
            f"Pág. {doc_.page}",
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ══════════════════════════════════════════════════════════════

def _safe_float(val) -> float:
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


def _build_records_table(story, df, S, C_DARK, C_LGRAY, C_MGRAY, C_WHITE, W):
    """Construye y agrega la tabla de registros al story de reportlab."""
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors as rl_colors

    COLS = ['folio', 'usuario_qfield', 'id_tramo', 'civ',
            'tipo_actividad', 'cantidad', 'unidad',
            'cant_residente', 'cant_interventor', 'estado']
    LABELS = {
        'folio': 'Folio', 'usuario_qfield': 'Inspector',
        'id_tramo': 'Tramo', 'civ': 'CIV',
        'tipo_actividad': 'Actividad',
        'cantidad': 'Cant.\nInspector', 'unidad': 'Und',
        'cant_residente': 'Cant.\nResidente',
        'cant_interventor': 'Cant.\nInterventor',
        'estado': 'Estado',
    }
    COL_W = {  # en cm
        'folio': 1.4, 'usuario_qfield': 2.2, 'id_tramo': 1.6,
        'civ': 1.2, 'tipo_actividad': 4.0, 'cantidad': 1.2,
        'unidad': 0.9, 'cant_residente': 1.2,
        'cant_interventor': 1.3, 'estado': 1.4,
    }
    from reportlab.lib.units import cm as _cm

    cols = [c for c in COLS if c in df.columns]
    col_widths = [COL_W.get(c, W / len(cols) / _cm) * _cm for c in cols]

    header = [S['th'].__class__.__name__]  # placeholder
    from reportlab.platypus import Paragraph as _P
    header = [_P(LABELS.get(c, c), S['th']) for c in cols]

    rows = [header]
    estado_color_map = {
        'APROBADO': rl_colors.HexColor('#dbeafe'),
        'REVISADO': rl_colors.HexColor('#d1fae5'),
        'DEVUELTO': rl_colors.HexColor('#fee2e2'),
        'BORRADOR': rl_colors.HexColor('#f1f5f9'),
    }

    for _, r in df.iterrows():
        row = []
        for c in cols:
            val = r.get(c, '')
            if val is None or (isinstance(val, float) and math.isnan(val)):
                val = '—'
            elif c in ('cantidad', 'cant_residente', 'cant_interventor'):
                f = _safe_float(val)
                val = f"{f:.2f}" if f else '—'
            row.append(_P(str(val), S['td']))
        rows.append(row)

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)

    tbl_style = [
        ('BACKGROUND',    (0, 0), (-1, 0), C_DARK),
        ('GRID',          (0, 0), (-1, -1), 0.3, C_MGRAY),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]
    # Filas alternas
    for idx in range(1, len(rows)):
        bg = C_WHITE if idx % 2 == 1 else C_LGRAY
        tbl_style.append(('BACKGROUND', (0, idx), (-1, idx), bg))
    # Columna estado con color semántico
    if 'estado' in cols:
        ei = cols.index('estado')
        for idx in range(1, len(rows)):
            val = df.iloc[idx - 1].get('estado', '')
            clr = estado_color_map.get(val, C_WHITE)
            tbl_style.append(('BACKGROUND', (ei, idx), (ei, idx), clr))

    tbl.setStyle(TableStyle(tbl_style))

    from reportlab.platypus import Paragraph as _P2
    from reportlab.lib.styles import getSampleStyleSheet
    _S_section = getSampleStyleSheet()['Normal']

    story.append(_P2('REGISTRO DE ACTIVIDADES', S['section']))
    story.append(tbl)
