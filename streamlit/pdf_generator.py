"""
pdf_generator.py — Bitácora Diaria de Obra · BDO IDU-1556-2025
Genera un PDF formato bitácora institucional según Guía de Identidad Visual IDU 2025.

Layout (distribución vertical por hoja A4 vertical):
  Header     (15%) — Logo ficticio + "BITÁCORA DIARIA DE OBRA" + No. Contrato + Fecha
  Localización(10%) — Fecha, Frente de Obra / Tramo, Clima AM/PM
  Narrativa  (40%) — Cuadro de Observaciones / Descripción de la Jornada
  Data       (25%) — Tabla de Cantidades Ejecutadas
  Footer     (10%) — Firmas (Residente Obra / Residente Interventoría) + Folio X/Y

Colores IDU:
  Azul IDU    #00A6E1 — títulos, cabeceras activas
  Rojo Bogotá #ED1C24 — alertas, borde observación crítica
  Amarillo    #FFC425 — advertencias
  Azul Oscuro #0076B0 — cabecera tabla
  Gris Neutro #EDF1F6 — fondo bloque metadata
  Gris Texto  #4D4D4D — texto cuerpo

SEGURIDAD:
  - _esc() aplica html.escape() a todos los valores de la BD antes de pasarlos
    a Paragraph() para prevenir errores de parseo XML de ReportLab.
"""

from __future__ import annotations

import html as _html
import io
import logging
import math
from datetime import datetime, date
from typing import List

import pandas as pd

_log = logging.getLogger(__name__)


def generate_pdf_bitacora(
    df: pd.DataFrame,
    contrato: dict,
    fi: date,
    ff: date,
    tipo_reporte: str,
    secciones: List[str],
    *,
    observaciones: str = "",
    frente_obra: str = "",
    clima_am: str = "",
    clima_pm: str = "",
    alerta: bool = False,
) -> bytes | None:
    """
    Genera el PDF de Bitácora Diaria de Obra.

    Parámetros adicionales:
      observaciones — texto narrativo de la jornada
      frente_obra   — frente/tramo del reporte
      clima_am      — condición climática AM
      clima_pm      — condición climática PM
      alerta        — si True, el borde del cuadro de observaciones es Rojo Bogotá

    Retorna bytes del PDF, o None si reportlab no está instalado.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle,
            Paragraph, Spacer, HRFlowable,
        )
    except ImportError:
        return None

    # ── Configuración del documento ────────────────────────
    buf    = io.BytesIO()
    PAGE   = A4                    # 21 × 29.7 cm — vertical
    MARGIN = 1.6 * cm

    doc = SimpleDocTemplate(
        buf, pagesize=PAGE,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN,   bottomMargin=2.2 * cm,
    )

    W = PAGE[0] - 2 * MARGIN   # ancho útil ≈ 17.8 cm

    # ── Paleta IDU ─────────────────────────────────────────
    C_IDU_BLUE   = rl_colors.HexColor('#00A6E1')   # Azul IDU primario
    C_IDU_DARK   = rl_colors.HexColor('#0076B0')   # Azul Oscuro / cabecera tabla
    C_IDU_RED    = rl_colors.HexColor('#ED1C24')   # Rojo Bogotá
    C_IDU_YELLOW = rl_colors.HexColor('#FFC425')   # Amarillo Estelar
    C_NEUTRAL    = rl_colors.HexColor('#EDF1F6')   # Gris Neutro — fondo metadata
    C_TEXT       = rl_colors.HexColor('#4D4D4D')   # Gris Texto — cuerpo
    C_MUTED      = rl_colors.HexColor('#7A8A99')   # Texto secundario
    C_WHITE      = rl_colors.white
    C_BORDER     = rl_colors.HexColor('#D8E3ED')   # Borde tabla
    C_ROW_ALT    = rl_colors.HexColor('#F8FBFD')   # Fila alterna tabla

    # ── Estilos tipográficos ───────────────────────────────
    base = getSampleStyleSheet()

    S = {
        # Encabezado principal
        'bdo_title': ParagraphStyle('bdo_title', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=14,
            textColor=C_IDU_BLUE, spaceAfter=2),
        'bdo_contract': ParagraphStyle('bdo_contract', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=10,
            textColor=C_WHITE, spaceAfter=1),
        'bdo_date': ParagraphStyle('bdo_date', parent=base['Normal'],
            fontName='Helvetica', fontSize=9,
            textColor=rl_colors.HexColor('#c8dff0'), spaceAfter=0),
        # Metadata localización
        'meta_label': ParagraphStyle('meta_label', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_MUTED, leading=9),
        'meta_value': ParagraphStyle('meta_value', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=8.5,
            textColor=C_TEXT, leading=11),
        # Secciones
        'section': ParagraphStyle('section', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=8,
            textColor=C_IDU_BLUE, spaceBefore=6, spaceAfter=3,
            textTransform='uppercase', letterSpacing=0.8),
        # Observaciones
        'obs': ParagraphStyle('obs', parent=base['Normal'],
            fontName='Helvetica', fontSize=8.5,
            textColor=C_TEXT, leading=12, spaceAfter=4),
        # Cabecera tabla
        'th': ParagraphStyle('th', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_WHITE, alignment=TA_CENTER, leading=9),
        # Celdas tabla
        'td': ParagraphStyle('td', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, leading=10),
        'td_center': ParagraphStyle('td_c', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, leading=10, alignment=TA_CENTER),
        'td_num': ParagraphStyle('td_n', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7.5,
            textColor=C_IDU_BLUE, leading=10, alignment=TA_CENTER),
        # Firmas
        'firma_line': ParagraphStyle('firma_line', parent=base['Normal'],
            fontName='Helvetica', fontSize=8,
            textColor=C_MUTED, alignment=TA_CENTER),
        'firma_label': ParagraphStyle('firma_label', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7.5,
            textColor=C_TEXT, alignment=TA_CENTER),
        'firma_sub': ParagraphStyle('firma_sub', parent=base['Normal'],
            fontName='Helvetica', fontSize=6.5,
            textColor=C_MUTED, alignment=TA_CENTER),
        'small': ParagraphStyle('small', parent=base['Normal'],
            fontName='Helvetica', fontSize=6.5, textColor=C_MUTED),
    }

    story = []
    numero_contrato = _ce(contrato, 'id',     'IDU-1556-2025') if contrato else 'IDU-1556-2025'
    contratista     = _ce(contrato, 'contratista', 'SERVIALCO S.A.S.') if contrato else 'SERVIALCO S.A.S.'

    # ══════════════════════════════════════════════════════
    # 1. HEADER (15%) — Azul IDU fondo, título bitácora
    # ══════════════════════════════════════════════════════
    fecha_rpt = fi.strftime('%d/%m/%Y') if fi == ff else (
        f"{fi.strftime('%d/%m/%Y')} — {ff.strftime('%d/%m/%Y')}"
    )

    # Panel izquierdo: bloque de identificación
    id_block = [
        [Paragraph('BITÁCORA DIARIA DE OBRA', S['bdo_title'])],
        [Paragraph(f"Contrato N.° <b>{numero_contrato}</b>", S['bdo_contract'])],
        [Paragraph(f"Fecha: {fecha_rpt}", S['bdo_date'])],
    ]
    id_tbl = Table(id_block, colWidths=[W * 0.55])
    id_tbl.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
    ]))

    # Panel derecho: contratista / tipo
    right_block = [
        [Paragraph('CONTRATISTA', S['meta_label'])],
        [Paragraph(contratista, ParagraphStyle('ct', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=8, textColor=C_WHITE))],
        [Paragraph(tipo_reporte, ParagraphStyle('tr', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=rl_colors.HexColor('#c8dff0')))],
    ]
    right_tbl = Table(right_block, colWidths=[W * 0.45])
    right_tbl.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 1),
    ]))

    hdr_data = [[id_tbl, right_tbl]]
    hdr_tbl  = Table(hdr_data, colWidths=[W * 0.55, W * 0.45])
    hdr_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), C_IDU_DARK),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING',   (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 10),
        ('LINEBELOW',    (0, 0), (-1, 0), 3, C_IDU_BLUE),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 0.25 * cm))

    # ══════════════════════════════════════════════════════
    # 2. BLOQUE DE LOCALIZACIÓN (10%) — Gris Neutro
    # ══════════════════════════════════════════════════════
    loc_data = [
        [
            Paragraph('FECHA', S['meta_label']),
            Paragraph('FRENTE DE OBRA / TRAMO', S['meta_label']),
            Paragraph('CLIMA AM', S['meta_label']),
            Paragraph('CLIMA PM', S['meta_label']),
        ],
        [
            Paragraph(fi.strftime('%d/%m/%Y'), S['meta_value']),
            Paragraph(_esc(frente_obra) or '—', S['meta_value']),
            Paragraph(_esc(clima_am)    or '—', S['meta_value']),
            Paragraph(_esc(clima_pm)    or '—', S['meta_value']),
        ],
    ]
    loc_tbl = Table(loc_data, colWidths=[W * 0.15, W * 0.45, W * 0.20, W * 0.20])
    loc_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0, 0), (-1, -1), C_NEUTRAL),
        ('GRID',         (0, 0), (-1, -1), 0.5, C_BORDER),
        ('LEFTPADDING',  (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING',   (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 4),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(loc_tbl)
    story.append(Spacer(1, 0.25 * cm))

    # ══════════════════════════════════════════════════════
    # 3. NARRATIVA (40%) — Cuadro de Observaciones
    # ══════════════════════════════════════════════════════
    story.append(Paragraph('OBSERVACIONES / DESCRIPCIÓN DE LA JORNADA', S['section']))

    obs_text = _esc(observaciones) if observaciones else (
        'Sin observaciones registradas para este período.'
    )
    border_color = C_IDU_RED if alerta else C_BORDER

    # Usar Paragraph directo (sin Table) para que el texto pueda paginar
    # si las observaciones son muy largas.
    story.append(HRFlowable(width=W, thickness=1.2, color=border_color))
    obs_style = ParagraphStyle(
        'obs_block', parent=S['obs'],
        leftIndent=10, rightIndent=10,
        spaceBefore=6, spaceAfter=6,
        backColor=C_WHITE,
    )
    for linea in obs_text.split(' | '):
        linea = linea.strip()
        if linea:
            story.append(Paragraph(linea, obs_style))
    story.append(HRFlowable(width=W, thickness=0.5, color=border_color))
    story.append(Spacer(1, 0.3 * cm))

    # ══════════════════════════════════════════════════════
    # 4. TABLA DE CANTIDADES EJECUTADAS (25%)
    # ══════════════════════════════════════════════════════
    if not df.empty and ('Registro de actividades' in secciones or not secciones):
        story.append(Paragraph('TABLA DE CANTIDADES EJECUTADAS', S['section']))
        _build_records_table(story, df, S, C_IDU_DARK, C_NEUTRAL, C_BORDER,
                             C_WHITE, C_ROW_ALT, C_IDU_RED, C_IDU_YELLOW, W)
        story.append(Spacer(1, 0.3 * cm))

    # ══════════════════════════════════════════════════════
    # 5. RESUMEN ESTADÍSTICO (opcional)
    # ══════════════════════════════════════════════════════
    if not df.empty and 'estado' in df.columns:
        total = len(df)
        apr   = len(df[df['estado'] == 'APROBADO'])
        rev   = len(df[df['estado'] == 'REVISADO'])
        dev   = len(df[df['estado'] == 'DEVUELTO'])
        bor   = total - apr - rev - dev

        res_h = ['Registros', 'Aprobados', 'Revisados', 'Devueltos', 'Borradores']
        res_v = [str(total), str(apr), str(rev), str(dev), str(bor)]

        res_tbl = Table([res_h, res_v], colWidths=[W / 5] * 5)
        res_tbl.setStyle(TableStyle([
            ('BACKGROUND',   (0, 0), (-1, 0), C_IDU_BLUE),
            ('TEXTCOLOR',    (0, 0), (-1, 0), C_WHITE),
            ('FONT',         (0, 0), (-1, 0), 'Helvetica-Bold', 7),
            ('BACKGROUND',   (0, 1), (-1, 1), C_NEUTRAL),
            ('FONT',         (0, 1), (-1, 1), 'Helvetica-Bold', 9),
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID',         (0, 0), (-1, -1), 0.4, C_BORDER),
            ('TOPPADDING',   (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 5),
        ]))
        story.append(Paragraph('RESUMEN DEL PERÍODO', S['section']))
        story.append(res_tbl)
        story.append(Spacer(1, 0.4 * cm))

    # ══════════════════════════════════════════════════════
    # 7. PIE: FIRMAS (10%)
    # ══════════════════════════════════════════════════════
    if 'Firmas' in secciones or not secciones:
        story.append(HRFlowable(width=W, thickness=0.8, color=C_IDU_BLUE))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph('CONTROL Y FIRMAS', S['section']))

        firma_data = [
            [
                Paragraph('_' * 38, S['firma_line']),
                Paragraph('_' * 38, S['firma_line']),
            ],
            [
                Paragraph('RESIDENTE DE OBRA', S['firma_label']),
                Paragraph('RESIDENTE DE INTERVENTORÍA', S['firma_label']),
            ],
            [
                Paragraph('Nombre y Matrícula Profesional', S['firma_sub']),
                Paragraph('Nombre y Matrícula Profesional', S['firma_sub']),
            ],
        ]
        firma_tbl = Table(firma_data, colWidths=[W / 2, W / 2])
        firma_tbl.setStyle(TableStyle([
            ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING',   (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ]))
        story.append(firma_tbl)

    # ── Footer con número de página ────────────────────────
    def _footer(canvas, doc_):
        canvas.saveState()
        # Línea superior del pie
        canvas.setStrokeColor(C_IDU_BLUE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, 1.4 * cm, PAGE[0] - MARGIN, 1.4 * cm)
        # Texto izquierda
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(
            MARGIN, 0.9 * cm,
            f"BDO IDU-1556-2025  ·  {contratista}  ·  "
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        # Paginación "Página X de Y" — derecha
        canvas.setFillColor(C_IDU_BLUE)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.drawRightString(
            PAGE[0] - MARGIN, 0.9 * cm,
            f"Página {doc_.page}",
        )
        canvas.restoreState()

    try:
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return buf.getvalue()
    except Exception:
        _log.exception("Error al construir el PDF (doc.build falló)")
        return None


# ══════════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ══════════════════════════════════════════════════════════════

def _safe_float(val) -> float:
    try:
        f = float(val)
        return 0.0 if math.isnan(f) else f
    except (TypeError, ValueError):
        return 0.0


def _esc(val) -> str:
    """Escapa caracteres XML/HTML antes de pasarlos a Paragraph (ReportLab)."""
    return _html.escape(str(val) if val is not None else '')


def _ce(d: dict, key: str, default: str) -> str:
    """Escapa campo de contrato."""
    return _esc(str(d.get(key, default) or default))


def _build_records_table(
    story, df, S,
    C_IDU_DARK, C_NEUTRAL, C_BORDER, C_WHITE, C_ROW_ALT,
    C_IDU_RED, C_IDU_YELLOW, W,
):
    """Construye la tabla de cantidades con cabecera Azul Oscuro IDU."""
    try:
        from reportlab.platypus import Table, TableStyle, Paragraph as _P
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.units import cm as _cm
    except ImportError:
        return

    COLS   = ['folio', 'id_tramo', 'civ', 'tipo_actividad',
              'cantidad', 'unidad', 'cant_residente', 'cant_interventor', 'estado']
    LABELS = {
        'folio': 'Folio', 'id_tramo': 'Tramo', 'civ': 'CIV',
        'tipo_actividad': 'Actividad / Descripción',
        'cantidad': 'Cant.\nInspector', 'unidad': 'Und.',
        'cant_residente': 'Cant.\nResidente',
        'cant_interventor': 'Cant.\nInterventor',
        'estado': 'Estado',
    }
    COL_W_CM = {
        'folio': 1.3, 'id_tramo': 1.6, 'civ': 1.2,
        'tipo_actividad': 4.5, 'cantidad': 1.2, 'unidad': 0.9,
        'cant_residente': 1.2, 'cant_interventor': 1.3, 'estado': 1.4,
    }

    cols      = [c for c in COLS if c in df.columns]
    col_widths = [COL_W_CM.get(c, W / len(cols) / _cm) * _cm for c in cols]

    header = [_P(LABELS.get(c, c), S['th']) for c in cols]
    rows   = [header]

    estado_bg = {
        'APROBADO': rl_colors.HexColor('#d1f2dc'),
        'REVISADO': rl_colors.HexColor('#fff5d6'),
        'DEVUELTO': rl_colors.HexColor('#fde8e9'),
        'BORRADOR': rl_colors.HexColor('#EDF1F6'),
    }

    for _, r in df.iterrows():
        row = []
        for c in cols:
            val = r.get(c, '')
            if val is None or (isinstance(val, float) and math.isnan(val)):
                val = '—'
            elif c in ('cantidad', 'cant_residente', 'cant_interventor'):
                f = _safe_float(val)
                val = f"{f:,.2f}" if f else '—'
            sty = S['td_num'] if c in ('cantidad', 'cant_residente', 'cant_interventor') else S['td_center'] if c in ('estado', 'unidad', 'folio') else S['td']
            row.append(_P(_esc(val), sty))
        rows.append(row)

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)

    tbl_style = [
        # Cabecera — Azul Oscuro IDU
        ('BACKGROUND',    (0, 0), (-1, 0), C_IDU_DARK),
        ('GRID',          (0, 0), (-1, -1), 0.3, C_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]

    # Filas alternas (zebra) — compatible con todas las versiones de ReportLab
    for idx in range(1, len(rows)):
        bg = C_WHITE if idx % 2 == 1 else C_ROW_ALT
        tbl_style.append(('BACKGROUND', (0, idx), (-1, idx), bg))

    # Color semántico por estado en columna
    if 'estado' in cols:
        ei = cols.index('estado')
        for idx in range(1, len(rows)):
            val = df.iloc[idx - 1].get('estado', '')
            clr = estado_bg.get(val, C_WHITE)
            tbl_style.append(('BACKGROUND', (ei, idx), (ei, idx), clr))

    tbl.setStyle(TableStyle(tbl_style))
    story.append(tbl)


# ── Meses en español (sin locale para portabilidad) ────────────
_MESES_ES = {
    1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
    5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
    9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre',
}


def _fecha_es(d) -> str:
    """Formatea un objeto date como '14 de abril de 2026'."""
    from datetime import date as _date
    if not isinstance(d, _date):
        d = pd.to_datetime(d).date()
    return f"{d.day} de {_MESES_ES[d.month]} de {d.year}"


def _to_date(val):
    """Convierte string/datetime/date a objeto date. Retorna None si falla."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None


def _norm_str(val) -> str:
    """Normaliza un valor a string, convierte None/NaN a ''."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return ''
    s = str(val).strip()
    return '' if s.lower() in ('none', 'nan', 'nat') else s


def _filter_by_group(
    df: pd.DataFrame,
    fecha,
    date_col: str,
    tramo_id: str,
    civ: str,
) -> pd.DataFrame:
    """
    Filtra df por (fecha, id_tramo, civ).
    - Si date_col no existe en df, retorna DataFrame vacío.
    - Si id_tramo no existe en df, se omite ese filtro.
      (Nombre de columna hardcodeado como 'id_tramo' y 'civ'.)
    - Si civ no existe en df, se omite ese filtro.
    """
    if df.empty or date_col not in df.columns:
        return pd.DataFrame()

    from datetime import date as _date
    if not isinstance(fecha, _date):
        fecha = pd.to_datetime(fecha).date()

    dates = df[date_col].apply(_to_date)
    mask = dates == fecha

    if 'id_tramo' in df.columns:
        mask &= df['id_tramo'].apply(_norm_str) == tramo_id

    if 'civ' in df.columns:
        mask &= df['civ'].apply(_norm_str) == civ

    return df[mask].copy()


def _collect_groups(
    df_cant: pd.DataFrame,
    df_comp: pd.DataFrame,
    df_diario: pd.DataFrame,
) -> list:
    """
    Devuelve lista ordenada de tuplas únicas (date, tramo_id, civ)
    presentes en cualquiera de las tres tablas.
    """
    tuples: set = set()

    sources = [
        (df_cant,   'fecha_creacion'),
        (df_comp,   'fecha_creacion'),
        (df_diario, 'fecha_reporte'),
    ]

    for df, date_col in sources:
        if df.empty:
            continue
        # Soporte para columna alternativa en reporte_diario
        col = date_col if date_col in df.columns else ('fecha' if 'fecha' in df.columns else None)
        if col is None:
            continue
        for _, r in df.iterrows():
            d = _to_date(r.get(col))
            if d is None:
                continue
            tramo = _norm_str(r.get('id_tramo', ''))
            civ   = _norm_str(r.get('civ', ''))
            tuples.add((d, tramo, civ))

    return sorted(tuples)


def _format_clima(folio: str, df_clima: pd.DataFrame) -> str:
    """
    Formatea condición climática de un folio.
    Retorna p.ej. '08:00 Soleado, 14:00 Nublado' o '' si no hay datos.
    """
    if df_clima.empty or 'folio' not in df_clima.columns:
        return ''
    sub = df_clima[df_clima['folio'].astype(str) == folio]
    if sub.empty:
        return ''
    parts = []
    for _, r in sub.iterrows():
        hora   = _norm_str(r.get('hora', ''))[:5]
        estado = _norm_str(r.get('estado_clima', ''))
        if estado:
            parts.append(f"{hora} {estado}".strip())
    return ', '.join(parts)


def _format_personal(folio: str, df_personal: pd.DataFrame) -> str:
    """
    Formatea personal de obra de un folio.
    Retorna p.ej. 'Inspectores: 2, Operativo: 5' o '' si todo es cero.
    """
    if df_personal.empty or 'folio' not in df_personal.columns:
        return ''
    sub = df_personal[df_personal['folio'].astype(str) == folio]
    if sub.empty:
        return ''
    CAMPOS = [
        ('inspectores',        'Inspectores'),
        ('personal_operativo', 'Operativo'),
        ('personal_boal',      'BOAL'),
        ('personal_transito',  'Tránsito'),
    ]
    parts = []
    for row_idx in range(len(sub)):
        r = sub.iloc[row_idx]
        for col, label in CAMPOS:
            v = int(r.get(col, 0) or 0)
            if v:
                parts.append(f"{label}: {v}")
    return ', '.join(parts)


def _format_maquinaria(folio: str, df_maquinaria: pd.DataFrame) -> str:
    """
    Formatea maquinaria en obra de un folio.
    Retorna columnas no nulas/cero o '' si todo es cero.
    """
    if df_maquinaria.empty or 'folio' not in df_maquinaria.columns:
        return ''
    sub = df_maquinaria[df_maquinaria['folio'].astype(str) == folio]
    if sub.empty:
        return ''
    CAMPOS = [
        ('operarios',            'Operarios'),
        ('volquetas',            'Volquetas'),
        ('vibrocompactador',     'Vibrocompactador'),
        ('minicargador',         'Minicargador'),
        ('ruteadora',            'Ruteadora'),
        ('compresor',            'Compresor'),
        ('retrocargador',        'Retrocargador'),
        ('extendedora_asfalto',  'Extendedora'),
        ('compactador_neumatico','Compactador neum.'),
        ('equipos_especiales',   'Equipos esp.'),
    ]
    parts = []
    for row_idx in range(len(sub)):
        r = sub.iloc[row_idx]
        for col, label in CAMPOS:
            if col not in r.index:
                continue
            v = int(r.get(col, 0) or 0)
            if v:
                parts.append(f"{label}: {v}")
    return ', '.join(parts)


def _format_sst(folio: str, df_sst: pd.DataFrame) -> str:
    """
    Formatea datos SST/Ambiental de un folio.
    Retorna columnas no nulas/cero o '' si todo es cero.
    """
    if df_sst.empty or 'folio' not in df_sst.columns:
        return ''
    sub = df_sst[df_sst['folio'].astype(str) == folio]
    if sub.empty:
        return ''
    CAMPOS = [
        ('botiquin',          'Botiquin'),
        ('kit_antiderrames',  'Kit antiderrames'),
        ('punto_hidratacion', 'Punto hidratación'),
        ('punto_ecologico',   'Punto ecológico'),
        ('extintor',          'Extintor'),
    ]
    parts = []
    for row_idx in range(len(sub)):
        r = sub.iloc[row_idx]
        for col, label in CAMPOS:
            if col not in r.index:
                continue
            v = int(r.get(col, 0) or 0)
            if v:
                parts.append(f"{label}: {v}")
    return ', '.join(parts)

