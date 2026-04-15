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
    datos: dict,
    contrato: dict,
    fi,
    ff,
    tipo_reporte: str,
    *,
    alerta: bool = False,
) -> bytes | None:
    """
    Genera el PDF de Bitácora Diaria de Obra en formato jerárquico.

    datos: dict con claves
      'cantidades'  → pd.DataFrame de registros_cantidades
      'componentes' → pd.DataFrame de registros_componentes
      'diario'      → pd.DataFrame de registros_reporte_diario
      'clima'       → pd.DataFrame de bd_condicion_climatica
      'personal'    → pd.DataFrame de bd_personal_obra
      'maquinaria'  → pd.DataFrame de bd_maquinaria_obra
      'sst'         → pd.DataFrame de bd_sst_ambiental

    alerta: reserved for future use (currently has no effect on output).

    Retorna bytes del PDF, o None si reportlab no está instalado o datos vacíos.
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

    from datetime import date as _date

    # ── Extraer DataFrames ─────────────────────────────────────
    df_cant     = datos.get('cantidades',  pd.DataFrame())
    df_comp     = datos.get('componentes', pd.DataFrame())
    df_diario   = datos.get('diario',      pd.DataFrame())
    df_clima    = datos.get('clima',       pd.DataFrame())
    df_personal = datos.get('personal',    pd.DataFrame())
    df_maq      = datos.get('maquinaria',  pd.DataFrame())
    df_sst      = datos.get('sst',         pd.DataFrame())

    if df_cant.empty and df_comp.empty and df_diario.empty:
        return None

    # ── Configuración del documento ────────────────────────────
    buf    = io.BytesIO()
    PAGE   = A4
    MARGIN = 1.6 * cm

    doc = SimpleDocTemplate(
        buf, pagesize=PAGE,
        rightMargin=MARGIN, leftMargin=MARGIN,
        topMargin=MARGIN,   bottomMargin=2.2 * cm,
    )

    W = PAGE[0] - 2 * MARGIN

    # ── Paleta IDU ─────────────────────────────────────────────
    C_IDU_BLUE = rl_colors.HexColor('#00A6E1')
    C_IDU_DARK = rl_colors.HexColor('#0076B0')
    C_NEUTRAL  = rl_colors.HexColor('#EDF1F6')
    C_TEXT     = rl_colors.HexColor('#4D4D4D')
    C_MUTED    = rl_colors.HexColor('#7A8A99')
    C_WHITE    = rl_colors.white
    C_BORDER   = rl_colors.HexColor('#D8E3ED')

    # ── Estilos tipográficos ───────────────────────────────────
    base = getSampleStyleSheet()

    S = {
        'bdo_title': ParagraphStyle('bdo_title', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=14,
            textColor=C_IDU_BLUE, spaceAfter=2),
        'bdo_contract': ParagraphStyle('bdo_contract', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=10,
            textColor=C_WHITE, spaceAfter=1),
        'bdo_date': ParagraphStyle('bdo_date', parent=base['Normal'],
            fontName='Helvetica', fontSize=9,
            textColor=rl_colors.HexColor('#c8dff0'), spaceAfter=0),
        'meta_label': ParagraphStyle('meta_label', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_MUTED, leading=9),
        'th': ParagraphStyle('th', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7,
            textColor=C_WHITE, alignment=TA_CENTER, leading=9),
        'td': ParagraphStyle('td', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, leading=10),
        'td_center': ParagraphStyle('td_c', parent=base['Normal'],
            fontName='Helvetica', fontSize=7.5,
            textColor=C_TEXT, leading=10, alignment=TA_CENTER),
        'td_num': ParagraphStyle('td_n', parent=base['Normal'],
            fontName='Helvetica-Bold', fontSize=7.5,
            textColor=C_IDU_BLUE, leading=10, alignment=TA_CENTER),
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
    try:
        fi_date = fi if isinstance(fi, _date) else pd.to_datetime(fi).date()
    except Exception:
        fi_date = _date.today()
    try:
        ff_date = ff if isinstance(ff, _date) else pd.to_datetime(ff).date()
    except Exception:
        ff_date = _date.today()
    numero_contrato = _ce(contrato, 'id',         'IDU-1556-2025') if contrato else 'IDU-1556-2025'
    contratista     = _ce(contrato, 'contratista','SERVIALCO S.A.S.') if contrato else 'SERVIALCO S.A.S.'

    # ══════════════════════════════════════════════════════════
    # 1. HEADER — Azul IDU
    # ══════════════════════════════════════════════════════════
    fecha_rpt = (fi_date.strftime('%d/%m/%Y') if fi_date == ff_date else
                 f"{fi_date.strftime('%d/%m/%Y')} — {ff_date.strftime('%d/%m/%Y')}")

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

    hdr_tbl = Table([[id_tbl, right_tbl]], colWidths=[W * 0.55, W * 0.45])
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
    story.append(Spacer(1, 0.4 * cm))

    # ══════════════════════════════════════════════════════════
    # 2. SECCIONES JERÁRQUICAS (fecha, tramo, CIV)
    # ══════════════════════════════════════════════════════════
    tramo_desc_map: dict[str, str] = {}
    if (not df_cant.empty
            and 'id_tramo' in df_cant.columns
            and 'tramo_descripcion' in df_cant.columns):
        for _, r in df_cant.dropna(subset=['id_tramo']).iterrows():
            tid   = _norm_str(r.get('id_tramo', ''))
            tdesc = _norm_str(r.get('tramo_descripcion', ''))
            if tid and tdesc and tid not in tramo_desc_map:
                tramo_desc_map[tid] = tdesc

    groups = _collect_groups(df_cant, df_comp, df_diario)

    for (fecha, tramo_id, civ) in groups:
        tramo_desc = tramo_desc_map.get(tramo_id, '')

        story.append(_build_group_header(fecha, tramo_id, tramo_desc, civ))

        paras = _build_content_paragraphs(
            fecha, tramo_id, civ,
            df_diario, df_clima, df_personal, df_maq, df_sst,
        )
        story.extend(paras)

        tbl = _build_quantities_table(fecha, tramo_id, civ, df_cant, df_comp, W)
        if tbl is not None:
            story.append(Spacer(1, 0.2 * cm))
            story.append(tbl)

        story.append(Spacer(1, 0.4 * cm))

    # ══════════════════════════════════════════════════════════
    # 3. PIE: FIRMAS
    # ══════════════════════════════════════════════════════════
    story.append(HRFlowable(width=W, thickness=0.8, color=C_IDU_BLUE))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph('CONTROL Y FIRMAS', ParagraphStyle('sec',
        parent=base['Normal'], fontName='Helvetica-Bold', fontSize=8,
        textColor=C_IDU_BLUE, spaceBefore=6, spaceAfter=3)))

    firma_data = [
        [Paragraph('_' * 38, S['firma_line']),
         Paragraph('_' * 38, S['firma_line'])],
        [Paragraph('RESIDENTE DE OBRA', S['firma_label']),
         Paragraph('RESIDENTE DE INTERVENTORÍA', S['firma_label'])],
        [Paragraph('Nombre y Matrícula Profesional', S['firma_sub']),
         Paragraph('Nombre y Matrícula Profesional', S['firma_sub'])],
    ]
    firma_tbl = Table(firma_data, colWidths=[W / 2, W / 2])
    firma_tbl.setStyle(TableStyle([
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
    ]))
    story.append(firma_tbl)

    # ── Footer paginación ──────────────────────────────────────
    def _footer(canvas, doc_):
        canvas.saveState()
        canvas.setStrokeColor(C_IDU_BLUE)
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN, 1.4 * cm, PAGE[0] - MARGIN, 1.4 * cm)
        canvas.setFont('Helvetica', 6.5)
        canvas.setFillColor(C_MUTED)
        canvas.drawString(
            MARGIN, 0.9 * cm,
            f"BDO IDU-1556-2025  ·  {contratista}  ·  "
            f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        )
        canvas.setFillColor(C_IDU_BLUE)
        canvas.setFont('Helvetica-Bold', 7)
        canvas.drawRightString(PAGE[0] - MARGIN, 0.9 * cm, f"Página {doc_.page}")
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


def _to_int(val) -> int:
    """Coerce None/NaN/falsy numeric to 0, safe for pandas NaN."""
    if val is None:
        return 0
    try:
        f = float(val)
    except (TypeError, ValueError):
        return 0
    return 0 if math.isnan(f) else int(f)


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
            v = _to_int(r.get(col))
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
            v = _to_int(r.get(col))
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
            v = _to_int(r.get(col))
            if v:
                parts.append(f"{label}: {v}")
    return ', '.join(parts)


def _build_group_header(
    fecha,
    tramo_id: str,
    tramo_desc: str,
    civ: str,
) -> object:
    """
    Retorna un Paragraph con el encabezado de sección:
    '14 de abril de 2026 – Tramo T-01 Carrera 26 – CIV 154654'
    Usa estilos internos (no depende de un dict S externo).
    """
    try:
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors as rl_colors
    except ImportError:
        return None

    fecha_str = _fecha_es(fecha)

    if tramo_id:
        tramo_part = f" – Tramo {tramo_id}"
        if tramo_desc:
            tramo_part += f" {tramo_desc}"
    else:
        tramo_part = " – Sin Tramo"

    civ_part = f" – CIV {civ}" if civ else " – Sin CIV"

    text = f"{fecha_str}{tramo_part}{civ_part}"

    style = ParagraphStyle(
        'grp_hdr',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=rl_colors.HexColor('#0076B0'),
        spaceBefore=10,
        spaceAfter=4,
        leading=12,
    )
    return Paragraph(_esc(text), style)


def _build_content_paragraphs(
    fecha,
    tramo_id: str,
    civ: str,
    df_diario: pd.DataFrame,
    df_clima: pd.DataFrame,
    df_personal: pd.DataFrame,
    df_maquinaria: pd.DataFrame,
    df_sst: pd.DataFrame,
) -> list:
    """
    Retorna lista de Paragraph, uno por folio de reporte_diario
    que pertenece al grupo (fecha, tramo_id, civ).
    Formato: 'PK 18474. Clima: … Personal: … Maquinaria: … SST: … Obs'
    """
    try:
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib import colors as rl_colors
    except ImportError:
        return []

    if df_diario.empty:
        return []

    # Intentar filtrar por fecha_reporte, luego por fecha
    date_col = 'fecha_reporte' if 'fecha_reporte' in df_diario.columns else 'fecha'
    # NOTE: if id_tramo or civ columns are absent, _filter_by_group degrades gracefully
    # (omitting that filter condition) but may over-select rows.
    sub = _filter_by_group(df_diario, fecha, date_col, tramo_id, civ)
    if sub.empty:
        return []

    style = ParagraphStyle(
        'cont_para',
        fontName='Helvetica',
        fontSize=8,
        textColor=rl_colors.HexColor('#4D4D4D'),
        leftIndent=8,
        spaceAfter=3,
        leading=11,
    )

    paras = []
    for _, r in sub.iterrows():
        folio = str(r.get('folio', ''))
        pk    = _norm_str(r.get('pk', r.get('civ_pk', '')))
        obs   = _norm_str(r.get('observaciones', ''))

        parts = []
        if pk:
            parts.append(f"PK {pk}")

        clima_txt = _format_clima(folio, df_clima)
        if clima_txt:
            parts.append(f"Estado del clima: {clima_txt}")

        pers_txt = _format_personal(folio, df_personal)
        if pers_txt:
            parts.append(f"Personal: {pers_txt}")

        maq_txt = _format_maquinaria(folio, df_maquinaria)
        if maq_txt:
            parts.append(f"Maquinaria: {maq_txt}")

        sst_txt = _format_sst(folio, df_sst)
        if sst_txt:
            parts.append(f"SST: {sst_txt}")

        if obs:
            parts.append(obs)

        if parts:
            text = '. '.join(parts)
            paras.append(Paragraph(_esc(text), style))

    return paras


def _build_quantities_table(
    fecha,
    tramo_id: str,
    civ: str,
    df_cant: pd.DataFrame,
    df_comp: pd.DataFrame,
    page_width: float = 0,
) -> object | None:
    """
    Construye la tabla de cantidades ejecutadas para un grupo (fecha, tramo, civ).
    Columnas: PK | Ítem | Descripción | Cantidad | Unidad | Observaciones
    Retorna Table o None si no hay filas.
    """
    try:
        from reportlab.platypus import Table, TableStyle, Paragraph as _P
        from reportlab.lib import colors as rl_colors
        from reportlab.lib.units import cm as _cm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.lib.enums import TA_CENTER
    except ImportError:
        return None

    # ── Estilos locales ────────────────────────────────────────
    C_DARK   = rl_colors.HexColor('#0076B0')
    C_WHITE  = rl_colors.white
    C_TEXT   = rl_colors.HexColor('#4D4D4D')
    C_BLUE   = rl_colors.HexColor('#00A6E1')
    C_BORDER = rl_colors.HexColor('#D8E3ED')
    C_ALT    = rl_colors.HexColor('#F8FBFD')

    s_th = ParagraphStyle('qt_th', fontName='Helvetica-Bold', fontSize=7,
                          textColor=C_WHITE, alignment=TA_CENTER, leading=9)
    s_td = ParagraphStyle('qt_td', fontName='Helvetica', fontSize=7.5,
                          textColor=C_TEXT, leading=10)
    s_tc = ParagraphStyle('qt_tc', fontName='Helvetica', fontSize=7.5,
                          textColor=C_TEXT, leading=10, alignment=TA_CENTER)
    s_tn = ParagraphStyle('qt_tn', fontName='Helvetica-Bold', fontSize=7.5,
                          textColor=C_BLUE, leading=10, alignment=TA_CENTER)

    # ── Recolectar filas ───────────────────────────────────────
    rows_data = []

    sub_cant = _filter_by_group(df_cant, fecha, 'fecha_creacion', tramo_id, civ)
    for _, r in sub_cant.iterrows():
        rows_data.append({
            'pk':          _norm_str(r.get('pk', r.get('civ_pk', ''))),
            'item':        _norm_str(r.get('item_pago', '')),
            'descripcion': _norm_str(r.get('item_descripcion', r.get('tipo_actividad', ''))),
            'cantidad':    _safe_float(r.get('cantidad')),
            'unidad':      _norm_str(r.get('unidad', '')),
            'obs':         _norm_str(r.get('observaciones', '')),
        })

    sub_comp = _filter_by_group(df_comp, fecha, 'fecha_creacion', tramo_id, civ)
    for _, r in sub_comp.iterrows():
        rows_data.append({
            'pk':          _norm_str(r.get('pk', r.get('civ_pk', ''))),
            'item':        _norm_str(r.get('tipo_componente', '')),
            'descripcion': _norm_str(r.get('tipo_actividad', '')),
            'cantidad':    _safe_float(r.get('cantidad')),
            'unidad':      _norm_str(r.get('unidad', '')),
            'obs':         _norm_str(r.get('observaciones', '')),
        })

    if not rows_data:
        return None

    # ── Anchos de columna ──────────────────────────────────────
    # Total útil ≈ 17.8 cm
    # PK=1.8 | Ítem=1.5 | Descripción=5.5 | Cantidad=1.8 | Unidad=1.4 | Obs=resto
    W_TOTAL = page_width if page_width > 0 else 17.8 * _cm
    col_w = [1.8*_cm, 1.5*_cm, 5.5*_cm, 1.8*_cm, 1.4*_cm,
             W_TOTAL - 1.8*_cm - 1.5*_cm - 5.5*_cm - 1.8*_cm - 1.4*_cm]

    # ── Construir filas ────────────────────────────────────────
    header = [
        _P('PK',          s_th),
        _P('Ítem',        s_th),
        _P('Descripción', s_th),
        _P('Cantidad',    s_th),
        _P('Unidad',      s_th),
        _P('Obs.',        s_th),
    ]
    table_rows = [header]

    for r in rows_data:
        cant_str = f"{r['cantidad']:,.2f}" if r['cantidad'] else '—'
        table_rows.append([
            _P(_esc(r['pk']),          s_tc),
            _P(_esc(r['item']),        s_tc),
            _P(_esc(r['descripcion']), s_td),
            _P(cant_str,               s_tn),
            _P(_esc(r['unidad']),      s_tc),
            _P(_esc(r['obs']),         s_td),
        ])

    tbl = Table(table_rows, colWidths=col_w, repeatRows=1)

    tbl_style = [
        ('BACKGROUND',    (0, 0), (-1, 0),  C_DARK),
        ('GRID',          (0, 0), (-1, -1), 0.3, C_BORDER),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 4),
    ]
    for idx in range(1, len(table_rows)):
        bg = C_WHITE if idx % 2 == 1 else C_ALT
        tbl_style.append(('BACKGROUND', (0, idx), (-1, idx), bg))

    tbl.setStyle(TableStyle(tbl_style))
    return tbl

