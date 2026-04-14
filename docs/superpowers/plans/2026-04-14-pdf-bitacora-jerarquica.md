# PDF Bitácora Jerárquica — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el PDF plano por un formato jerárquico agrupado por `(fecha, id_tramo, civ)` con encabezado de línea única, párrafos de contenido por folio y tabla de cantidades ejecutadas por sección.

**Architecture:** Los helpers puros (`_fecha_es`, `_collect_groups`, `_filter_by_group`, `_format_*`) se añaden primero y son testeables sin ReportLab. Luego se añaden los builders de ReportLab. Finalmente se reescribe `generate_pdf_bitacora` con la nueva firma `datos: dict` y se actualiza `generar_pdf.py`.

**Tech Stack:** Python 3.11, ReportLab, pandas, Streamlit, Supabase.

---

## File Map

| Acción | Archivo | Responsabilidad |
|---|---|---|
| Crear | `streamlit/tests/__init__.py` | Marca el directorio como paquete de tests |
| Crear | `streamlit/tests/test_pdf_generator.py` | Tests unitarios de helpers puros |
| Modificar | `streamlit/pdf_generator.py` | Helpers nuevos + reescritura de `generate_pdf_bitacora` |
| Modificar | `streamlit/pages/generar_pdf.py` | Carga sub-tablas + nueva llamada con `datos` dict |

---

## Task 1: Helpers puros — `_fecha_es`, `_collect_groups`, `_filter_by_group`

**Files:**
- Modify: `streamlit/pdf_generator.py` (añadir al final del archivo, antes del último `\n`)
- Create: `streamlit/tests/__init__.py`
- Create: `streamlit/tests/test_pdf_generator.py`

- [ ] **Step 1: Crear directorio de tests e `__init__.py`**

```bash
mkdir -p "streamlit/tests"
touch "streamlit/tests/__init__.py"
```

- [ ] **Step 2: Escribir tests que fallan**

Crear `streamlit/tests/test_pdf_generator.py`:

```python
"""Tests para helpers puros de pdf_generator (sin ReportLab, sin Supabase)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
import pandas as pd
import pytest

from pdf_generator import _fecha_es, _collect_groups, _filter_by_group


# ── _fecha_es ─────────────────────────────────────────────────
def test_fecha_es_abril():
    assert _fecha_es(date(2026, 4, 14)) == "14 de abril de 2026"

def test_fecha_es_enero():
    assert _fecha_es(date(2025, 1, 1)) == "1 de enero de 2025"

def test_fecha_es_diciembre():
    assert _fecha_es(date(2024, 12, 31)) == "31 de diciembre de 2024"


# ── _collect_groups ───────────────────────────────────────────
def test_collect_groups_empty():
    assert _collect_groups(pd.DataFrame(), pd.DataFrame(), pd.DataFrame()) == []

def test_collect_groups_single_cant():
    df = pd.DataFrame([{
        'fecha_creacion': '2026-04-14',
        'id_tramo': 'T-01',
        'civ': '154654',
    }])
    result = _collect_groups(df, pd.DataFrame(), pd.DataFrame())
    assert result == [(date(2026, 4, 14), 'T-01', '154654')]

def test_collect_groups_deduplicates():
    df = pd.DataFrame([
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '111'},
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '111'},
    ])
    result = _collect_groups(df, pd.DataFrame(), pd.DataFrame())
    assert result == [(date(2026, 4, 14), 'T-01', '111')]

def test_collect_groups_sorted():
    df_cant = pd.DataFrame([
        {'fecha_creacion': '2026-04-15', 'id_tramo': 'T-01', 'civ': '111'},
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '111'},
    ])
    result = _collect_groups(df_cant, pd.DataFrame(), pd.DataFrame())
    assert result[0][0] == date(2026, 4, 14)
    assert result[1][0] == date(2026, 4, 15)

def test_collect_groups_null_tramo_normalized():
    df = pd.DataFrame([{
        'fecha_creacion': '2026-04-14',
        'id_tramo': None,
        'civ': '111',
    }])
    result = _collect_groups(df, pd.DataFrame(), pd.DataFrame())
    assert result == [(date(2026, 4, 14), '', '111')]

def test_collect_groups_merges_all_tables():
    df_cant = pd.DataFrame([{
        'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '111',
    }])
    df_comp = pd.DataFrame([{
        'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '222',
    }])
    df_diario = pd.DataFrame([{
        'fecha_reporte': '2026-04-14', 'id_tramo': 'T-01', 'civ': '333',
    }])
    result = _collect_groups(df_cant, df_comp, df_diario)
    civs = [g[2] for g in result]
    assert '111' in civs
    assert '222' in civs
    assert '333' in civs


# ── _filter_by_group ──────────────────────────────────────────
def test_filter_by_group_basic():
    df = pd.DataFrame([
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '111', 'val': 1},
        {'fecha_creacion': '2026-04-15', 'id_tramo': 'T-01', 'civ': '111', 'val': 2},
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-02', 'civ': '111', 'val': 3},
        {'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01', 'civ': '999', 'val': 4},
    ])
    result = _filter_by_group(df, date(2026, 4, 14), 'fecha_creacion', 'T-01', '111')
    assert len(result) == 1
    assert result.iloc[0]['val'] == 1

def test_filter_by_group_empty_df():
    result = _filter_by_group(pd.DataFrame(), date(2026, 4, 14), 'fecha_creacion', 'T-01', '111')
    assert result.empty

def test_filter_by_group_missing_date_col():
    df = pd.DataFrame([{'id_tramo': 'T-01', 'civ': '111'}])
    result = _filter_by_group(df, date(2026, 4, 14), 'fecha_creacion', 'T-01', '111')
    assert result.empty

def test_filter_by_group_no_tramo_col_matches_all_dates():
    df = pd.DataFrame([
        {'fecha_creacion': '2026-04-14', 'civ': '111', 'val': 1},
        {'fecha_creacion': '2026-04-14', 'civ': '111', 'val': 2},
    ])
    result = _filter_by_group(df, date(2026, 4, 14), 'fecha_creacion', 'T-01', '111')
    assert len(result) == 2
```

- [ ] **Step 3: Ejecutar tests — verificar que fallan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | head -40
```

Resultado esperado: `ImportError: cannot import name '_fecha_es' from 'pdf_generator'`

- [ ] **Step 4: Implementar helpers en `pdf_generator.py`**

Añadir al final del archivo (antes del último `\n`), después de `_build_records_table`:

```python
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
```

- [ ] **Step 5: Ejecutar tests — verificar que pasan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | head -50
```

Resultado esperado: todos los tests en verde (`PASSED`).

- [ ] **Step 6: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pdf_generator.py streamlit/tests/__init__.py streamlit/tests/test_pdf_generator.py
git commit -m "feat: add _fecha_es, _collect_groups, _filter_by_group helpers"
```

---

## Task 2: Format helpers para sub-tablas

**Files:**
- Modify: `streamlit/pdf_generator.py` (añadir funciones `_format_clima`, `_format_personal`, `_format_maquinaria`, `_format_sst`)
- Modify: `streamlit/tests/test_pdf_generator.py` (añadir tests)

- [ ] **Step 1: Añadir tests para format helpers**

Añadir al final de `streamlit/tests/test_pdf_generator.py`:

```python
from pdf_generator import _format_clima, _format_personal, _format_maquinaria, _format_sst


# ── _format_clima ─────────────────────────────────────────────
def test_format_clima_empty():
    assert _format_clima('F001', pd.DataFrame()) == ''

def test_format_clima_single():
    df = pd.DataFrame([{'folio': 'F001', 'hora': '08:00', 'estado_clima': 'Soleado'}])
    assert _format_clima('F001', df) == '08:00 Soleado'

def test_format_clima_multiple():
    df = pd.DataFrame([
        {'folio': 'F001', 'hora': '08:00', 'estado_clima': 'Soleado'},
        {'folio': 'F001', 'hora': '14:00', 'estado_clima': 'Nublado'},
    ])
    result = _format_clima('F001', df)
    assert '08:00 Soleado' in result
    assert '14:00 Nublado' in result

def test_format_clima_other_folio_ignored():
    df = pd.DataFrame([{'folio': 'F002', 'hora': '08:00', 'estado_clima': 'Soleado'}])
    assert _format_clima('F001', df) == ''


# ── _format_personal ──────────────────────────────────────────
def test_format_personal_empty():
    assert _format_personal('F001', pd.DataFrame()) == ''

def test_format_personal_all_zero():
    df = pd.DataFrame([{
        'folio': 'F001',
        'inspectores': 0, 'personal_operativo': 0,
        'personal_boal': 0, 'personal_transito': 0,
    }])
    assert _format_personal('F001', df) == ''

def test_format_personal_nonzero():
    df = pd.DataFrame([{
        'folio': 'F001',
        'inspectores': 2, 'personal_operativo': 5,
        'personal_boal': 0, 'personal_transito': 0,
    }])
    result = _format_personal('F001', df)
    assert 'Inspectores: 2' in result
    assert 'Operativo: 5' in result
    assert 'BOAL' not in result


# ── _format_maquinaria ────────────────────────────────────────
def test_format_maquinaria_empty():
    assert _format_maquinaria('F001', pd.DataFrame()) == ''

def test_format_maquinaria_nonzero():
    df = pd.DataFrame([{
        'folio': 'F001', 'volquetas': 3, 'vibrocompactador': 0,
        'operarios': 0, 'minicargador': 1,
    }])
    result = _format_maquinaria('F001', df)
    assert 'Volquetas: 3' in result
    assert 'Minicargador: 1' in result
    assert 'Vibrocompactador' not in result


# ── _format_sst ───────────────────────────────────────────────
def test_format_sst_empty():
    assert _format_sst('F001', pd.DataFrame()) == ''

def test_format_sst_nonzero():
    df = pd.DataFrame([{
        'folio': 'F001', 'botiquin': 1, 'extintor': 2,
        'kit_antiderrames': 0, 'punto_hidratacion': 0, 'punto_ecologico': 0,
    }])
    result = _format_sst('F001', df)
    assert 'Botiquin: 1' in result
    assert 'Extintor: 2' in result
    assert 'Kit' not in result
```

- [ ] **Step 2: Ejecutar tests — verificar que fallan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -k "format" -v 2>&1 | head -20
```

Resultado esperado: `ImportError: cannot import name '_format_clima'`

- [ ] **Step 3: Implementar format helpers en `pdf_generator.py`**

Añadir al final de `pdf_generator.py`:

```python
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
```

- [ ] **Step 4: Ejecutar tests — verificar que pasan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | tail -20
```

Resultado esperado: todos los tests en verde.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pdf_generator.py streamlit/tests/test_pdf_generator.py
git commit -m "feat: add _format_clima/personal/maquinaria/sst helpers"
```

---

## Task 3: ReportLab builders — `_build_group_header` y `_build_content_paragraphs`

Estas funciones dependen de ReportLab y se testean con smoke tests (verifican tipo y no-crash).

**Files:**
- Modify: `streamlit/pdf_generator.py`
- Modify: `streamlit/tests/test_pdf_generator.py`

- [ ] **Step 1: Añadir smoke tests**

Añadir al final de `streamlit/tests/test_pdf_generator.py`:

```python
from pdf_generator import _build_group_header, _build_content_paragraphs


# ── _build_group_header ───────────────────────────────────────
def test_build_group_header_returns_paragraph():
    from reportlab.platypus import Paragraph
    p = _build_group_header(date(2026, 4, 14), 'T-01', 'Carrera 26', '154654')
    assert isinstance(p, Paragraph)

def test_build_group_header_sin_tramo():
    from reportlab.platypus import Paragraph
    p = _build_group_header(date(2026, 4, 14), '', '', '154654')
    assert isinstance(p, Paragraph)
    assert 'Sin Tramo' in p.text

def test_build_group_header_sin_civ():
    from reportlab.platypus import Paragraph
    p = _build_group_header(date(2026, 4, 14), 'T-01', 'Carrera 26', '')
    assert isinstance(p, Paragraph)
    assert 'Sin CIV' in p.text


# ── _build_content_paragraphs ─────────────────────────────────
def test_build_content_paragraphs_empty_diario():
    result = _build_content_paragraphs(
        date(2026, 4, 14), 'T-01', '111',
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
        pd.DataFrame(), pd.DataFrame(),
    )
    assert result == []

def test_build_content_paragraphs_returns_paragraphs():
    from reportlab.platypus import Paragraph
    df_diario = pd.DataFrame([{
        'folio': 'F001', 'fecha_reporte': '2026-04-14',
        'id_tramo': 'T-01', 'civ': '111',
        'pk': '18474', 'observaciones': 'Todo bien',
    }])
    result = _build_content_paragraphs(
        date(2026, 4, 14), 'T-01', '111',
        df_diario, pd.DataFrame(), pd.DataFrame(),
        pd.DataFrame(), pd.DataFrame(),
    )
    assert len(result) == 1
    assert isinstance(result[0], Paragraph)
```

- [ ] **Step 2: Ejecutar tests — verificar que fallan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -k "build_group or build_content" -v 2>&1 | head -20
```

Resultado esperado: `ImportError: cannot import name '_build_group_header'`

- [ ] **Step 3: Implementar `_build_group_header` y `_build_content_paragraphs` en `pdf_generator.py`**

Añadir al final de `pdf_generator.py`:

```python
def _build_group_header(
    fecha,
    tramo_id: str,
    tramo_desc: str,
    civ: str,
) -> object:
    """
    Retorna un Paragraph con el encabezado de sección:
    '14 de abril de 2026 – Tramo T-01 Carrera 26 – CIV 154654'
    """
    try:
        from reportlab.platypus import Paragraph
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors as rl_colors
    except ImportError:
        raise

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
```

- [ ] **Step 4: Ejecutar todos los tests**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | tail -30
```

Resultado esperado: todos en verde.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pdf_generator.py streamlit/tests/test_pdf_generator.py
git commit -m "feat: add _build_group_header and _build_content_paragraphs"
```

---

## Task 4: Builder de tabla de cantidades — `_build_quantities_table`

**Files:**
- Modify: `streamlit/pdf_generator.py`
- Modify: `streamlit/tests/test_pdf_generator.py`

- [ ] **Step 1: Añadir smoke test**

Añadir al final de `streamlit/tests/test_pdf_generator.py`:

```python
from pdf_generator import _build_quantities_table


def test_build_quantities_table_empty_returns_none():
    result = _build_quantities_table(
        date(2026, 4, 14), 'T-01', '111',
        pd.DataFrame(), pd.DataFrame(),
    )
    assert result is None

def test_build_quantities_table_with_cant_returns_table():
    from reportlab.platypus import Table
    df_cant = pd.DataFrame([{
        'fecha_creacion': '2026-04-14',
        'id_tramo': 'T-01',
        'civ': '111',
        'pk': '18474',
        'item_pago': '2.1',
        'item_descripcion': 'Demolición de pavimento',
        'cantidad': 150.0,
        'unidad': 'm2',
        'observaciones': '',
    }])
    result = _build_quantities_table(
        date(2026, 4, 14), 'T-01', '111',
        df_cant, pd.DataFrame(),
    )
    assert isinstance(result, Table)

def test_build_quantities_table_merges_comp():
    from reportlab.platypus import Table
    df_comp = pd.DataFrame([{
        'fecha_creacion': '2026-04-14',
        'id_tramo': 'T-01',
        'civ': '111',
        'pk': '18474',
        'tipo_componente': 'PMT',
        'tipo_actividad': 'Señalización',
        'cantidad': 5.0,
        'unidad': 'und',
        'observaciones': '',
    }])
    result = _build_quantities_table(
        date(2026, 4, 14), 'T-01', '111',
        pd.DataFrame(), df_comp,
    )
    assert isinstance(result, Table)
```

- [ ] **Step 2: Ejecutar tests — verificar que fallan**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -k "quantities" -v 2>&1 | head -15
```

Resultado esperado: `ImportError: cannot import name '_build_quantities_table'`

- [ ] **Step 3: Implementar `_build_quantities_table` en `pdf_generator.py`**

Añadir al final de `pdf_generator.py`:

```python
def _build_quantities_table(
    fecha,
    tramo_id: str,
    civ: str,
    df_cant: pd.DataFrame,
    df_comp: pd.DataFrame,
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
    W_TOTAL = 17.8 * _cm
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
```

- [ ] **Step 4: Ejecutar todos los tests**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | tail -30
```

Resultado esperado: todos en verde.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pdf_generator.py streamlit/tests/test_pdf_generator.py
git commit -m "feat: add _build_quantities_table helper"
```

---

## Task 5: Reescribir `generate_pdf_bitacora` — nueva firma y cuerpo jerárquico

**Files:**
- Modify: `streamlit/pdf_generator.py` (reemplazar función completa)
- Modify: `streamlit/tests/test_pdf_generator.py` (smoke test de integración)

- [ ] **Step 1: Añadir smoke test de integración**

Añadir al final de `streamlit/tests/test_pdf_generator.py`:

```python
from pdf_generator import generate_pdf_bitacora
from datetime import date


def _make_datos(with_diario=True, with_cant=True):
    datos = {
        'cantidades': pd.DataFrame([{
            'fecha_creacion': '2026-04-14', 'id_tramo': 'T-01',
            'civ': '111', 'pk': '18474', 'item_pago': '2.1',
            'item_descripcion': 'Demolición', 'tramo_descripcion': 'Carrera 26',
            'cantidad': 100.0, 'unidad': 'm2', 'observaciones': '',
        }]) if with_cant else pd.DataFrame(),
        'componentes': pd.DataFrame(),
        'diario': pd.DataFrame([{
            'fecha_reporte': '2026-04-14', 'id_tramo': 'T-01',
            'civ': '111', 'pk': '18474', 'folio': 'F001',
            'observaciones': 'Sin novedad',
        }]) if with_diario else pd.DataFrame(),
        'clima':     pd.DataFrame(),
        'personal':  pd.DataFrame(),
        'maquinaria': pd.DataFrame(),
        'sst':        pd.DataFrame(),
    }
    return datos


def test_generate_pdf_returns_bytes():
    datos = _make_datos()
    contrato = {'id': 'IDU-1556-2025', 'contratista': 'SERVIALCO S.A.S.'}
    result = generate_pdf_bitacora(
        datos, contrato,
        date(2026, 4, 14), date(2026, 4, 14),
        'Bitácora Consolidada',
    )
    assert isinstance(result, bytes)
    assert len(result) > 1000  # PDF válido tiene más de 1 KB

def test_generate_pdf_empty_datos_returns_none():
    datos = {k: pd.DataFrame() for k in
             ['cantidades','componentes','diario','clima','personal','maquinaria','sst']}
    result = generate_pdf_bitacora(
        datos, {},
        date(2026, 4, 14), date(2026, 4, 14),
        'Bitácora Consolidada',
    )
    assert result is None

def test_generate_pdf_only_cant_no_diario():
    datos = _make_datos(with_diario=False, with_cant=True)
    contrato = {'id': 'IDU-1556-2025', 'contratista': 'SERVIALCO S.A.S.'}
    result = generate_pdf_bitacora(
        datos, contrato,
        date(2026, 4, 14), date(2026, 4, 14),
        'Bitácora Consolidada',
    )
    assert isinstance(result, bytes)
```

- [ ] **Step 2: Ejecutar tests — verificar que fallan (firma incorrecta)**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -k "generate_pdf" -v 2>&1 | head -20
```

Resultado esperado: `TypeError: generate_pdf_bitacora() got unexpected keyword argument` o error de firma.

- [ ] **Step 3: Reemplazar la función `generate_pdf_bitacora` completa en `pdf_generator.py`**

Localizar la función actual (desde `def generate_pdf_bitacora(` hasta el `return None` del `except ImportError`) y reemplazarla íntegramente con:

```python
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
    fi_date = fi if isinstance(fi, _date) else pd.to_datetime(fi).date()
    ff_date = ff if isinstance(ff, _date) else pd.to_datetime(ff).date()
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

        tbl = _build_quantities_table(fecha, tramo_id, civ, df_cant, df_comp)
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
```

- [ ] **Step 4: Ejecutar todos los tests**

```bash
cd streamlit && python -m pytest tests/test_pdf_generator.py -v 2>&1 | tail -35
```

Resultado esperado: todos en verde, incluyendo los 3 smoke tests de `generate_pdf`.

- [ ] **Step 5: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pdf_generator.py streamlit/tests/test_pdf_generator.py
git commit -m "feat: rewrite generate_pdf_bitacora with hierarchical fecha/tramo/CIV structure"
```

---

## Task 6: Actualizar `generar_pdf.py` — carga de sub-tablas y nueva llamada

**Files:**
- Modify: `streamlit/pages/generar_pdf.py`

- [ ] **Step 1: Añadir imports faltantes**

En `generar_pdf.py`, localizar el bloque de imports de `database`:

```python
from database import (
    load_cantidades, load_componentes, load_reporte_diario, load_contrato,
)
```

Reemplazarlo con:

```python
from database import (
    load_cantidades, load_componentes, load_reporte_diario, load_contrato,
    load_bd_clima, load_bd_personal, load_bd_maquinaria, load_bd_sst,
)
```

- [ ] **Step 2: Reemplazar bloque PDF en `page_generar_pdf`**

Localizar el bloque actual (desde `# ── PDF ────` hasta el `else: st.error(...)`) y reemplazarlo con:

```python
        # ── PDF ────────────────────────────────────────────
        if formato == "PDF":
            df_diario = frames.get('Reporte Diario', pd.DataFrame())

            # Cargar sub-tablas vinculadas a los folios del reporte diario
            folios_diario = (
                tuple(df_diario['folio'].dropna().tolist())
                if not df_diario.empty and 'folio' in df_diario.columns
                else ()
            )
            with st.spinner("Cargando datos del reporte…"):
                df_clima      = load_bd_clima(folios_diario)
                df_personal   = load_bd_personal(folios_diario)
                df_maquinaria = load_bd_maquinaria(folios_diario)
                df_sst        = load_bd_sst(folios_diario)

            datos = {
                'cantidades':  frames.get('Cantidades de Obra',        pd.DataFrame()),
                'componentes': frames.get('Componentes Transversales', pd.DataFrame()),
                'diario':      df_diario,
                'clima':       df_clima,
                'personal':    df_personal,
                'maquinaria':  df_maquinaria,
                'sst':         df_sst,
            }

            with st.spinner("Generando Bitácora PDF…"):
                pdf_bytes = generate_pdf_bitacora(
                    datos, contrato, fi, ff, "Bitácora Consolidada",
                )

            if pdf_bytes:
                nombre = f"Bitacora_IDU-1556-2025_{fecha_tag}.pdf"
                st.success(f"Bitácora PDF generada — {total_registros} registros")
                st.download_button(
                    "Descargar Bitácora PDF",
                    data=pdf_bytes,
                    file_name=nombre,
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                )
            else:
                st.warning(
                    "No se generó el PDF. "
                    "Verifica que los registros tengan fechas y tramos asignados."
                )
```

- [ ] **Step 3: Verificar que no quedan referencias a la firma antigua**

```bash
grep -n "observaciones_pdf\|frente_obra\|clima_am\|clima_pm\|secciones" \
  "streamlit/pages/generar_pdf.py"
```

Resultado esperado: sin output (ninguna referencia a parámetros eliminados).

- [ ] **Step 4: Commit y push**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pages/generar_pdf.py
git commit -m "feat: update generar_pdf.py to pass datos dict to generate_pdf_bitacora"
git push origin main
```

---

## Self-Review

**Cobertura del spec:**
- ✅ Agrupación por `(fecha, tramo, civ)` → `_collect_groups` (Task 1)
- ✅ Encabezado de línea única fecha–tramo–CIV → `_build_group_header` (Task 3)
- ✅ Párrafos de contenido por folio con clima/personal/maquinaria/sst/obs → `_build_content_paragraphs` (Task 3)
- ✅ Tabla de cantidades PK/Ítem/Desc/Cant/Und/Obs → `_build_quantities_table` (Task 4)
- ✅ Fecha en español sin locale → `_fecha_es` (Task 1)
- ✅ `tramo_descripcion` desde `df_cantidades` → Task 5 (loop principal)
- ✅ Sin tramo → "Sin Tramo", sin CIV → "Sin CIV" → `_build_group_header`
- ✅ Firma `datos: dict` → Task 5
- ✅ Actualización de `generar_pdf.py` → Task 6
- ✅ Carga `load_bd_clima/personal/maquinaria/sst` → Task 6

**Consistencia de tipos:**
- `_filter_by_group` retorna `pd.DataFrame` — usado en `_build_quantities_table` y `_build_content_paragraphs` ✅
- `_collect_groups` retorna `list[tuple[date, str, str]]` — iterado en Task 5 ✅
- `_build_group_header` y `_build_content_paragraphs` no reciben `S` dict — los estilos se crean internamente con `ParagraphStyle` (self-contained) ✅
- `generate_pdf_bitacora` nueva firma sin `secciones`, `observaciones`, `frente_obra`, `clima_am`, `clima_pm` ✅
