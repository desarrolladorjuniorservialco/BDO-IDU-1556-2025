"""Tests para helpers puros de pdf_generator (sin ReportLab, sin Supabase)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import date
import pandas as pd

from pdf_generator import _fecha_es, _collect_groups, _filter_by_group


# ── _fecha_es ─────────────────────────────────────────────────
def test_fecha_es_abril():
    assert _fecha_es(date(2026, 4, 14)) == "14 de abril de 2026"

def test_fecha_es_enero():
    assert _fecha_es(date(2025, 1, 1)) == "1 de enero de 2025"

def test_fecha_es_diciembre():
    assert _fecha_es(date(2024, 12, 31)) == "31 de diciembre de 2024"

def test_fecha_es_datetime_object():
    from datetime import datetime
    assert _fecha_es(datetime(2026, 4, 14, 10, 30)) == "14 de abril de 2026"


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

def test_collect_groups_diario_fecha_fallback():
    """df_diario con columna 'fecha' en lugar de 'fecha_reporte' debe funcionar."""
    df_diario = pd.DataFrame([{
        'fecha': '2026-04-14', 'id_tramo': 'T-01', 'civ': '444',
    }])
    result = _collect_groups(pd.DataFrame(), pd.DataFrame(), df_diario)
    assert result == [(date(2026, 4, 14), 'T-01', '444')]


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

def test_to_date_unparseable_returns_none():
    from pdf_generator import _to_date
    assert _to_date('not-a-date') is None

def test_norm_str_nat_string():
    from pdf_generator import _norm_str
    assert _norm_str('NaT') == ''
    assert _norm_str('nan') == ''
    assert _norm_str('None') == ''


# ── _format_clima ─────────────────────────────────────────────
def test_format_clima_empty():
    from pdf_generator import _format_clima
    assert _format_clima('F001', pd.DataFrame()) == ''

def test_format_clima_single():
    from pdf_generator import _format_clima
    df = pd.DataFrame([{'folio': 'F001', 'hora': '08:00', 'estado_clima': 'Soleado'}])
    assert _format_clima('F001', df) == '08:00 Soleado'

def test_format_clima_multiple():
    from pdf_generator import _format_clima
    df = pd.DataFrame([
        {'folio': 'F001', 'hora': '08:00', 'estado_clima': 'Soleado'},
        {'folio': 'F001', 'hora': '14:00', 'estado_clima': 'Nublado'},
    ])
    result = _format_clima('F001', df)
    assert '08:00 Soleado' in result
    assert '14:00 Nublado' in result

def test_format_clima_other_folio_ignored():
    from pdf_generator import _format_clima
    df = pd.DataFrame([{'folio': 'F002', 'hora': '08:00', 'estado_clima': 'Soleado'}])
    assert _format_clima('F001', df) == ''


# ── _format_personal ──────────────────────────────────────────
def test_format_personal_empty():
    from pdf_generator import _format_personal
    assert _format_personal('F001', pd.DataFrame()) == ''

def test_format_personal_all_zero():
    from pdf_generator import _format_personal
    df = pd.DataFrame([{
        'folio': 'F001',
        'inspectores': 0, 'personal_operativo': 0,
        'personal_boal': 0, 'personal_transito': 0,
    }])
    assert _format_personal('F001', df) == ''

def test_format_personal_nonzero():
    from pdf_generator import _format_personal
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
    from pdf_generator import _format_maquinaria
    assert _format_maquinaria('F001', pd.DataFrame()) == ''

def test_format_maquinaria_nonzero():
    from pdf_generator import _format_maquinaria
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
    from pdf_generator import _format_sst
    assert _format_sst('F001', pd.DataFrame()) == ''

def test_format_sst_nonzero():
    from pdf_generator import _format_sst
    df = pd.DataFrame([{
        'folio': 'F001', 'botiquin': 1, 'extintor': 2,
        'kit_antiderrames': 0, 'punto_hidratacion': 0, 'punto_ecologico': 0,
    }])
    result = _format_sst('F001', df)
    assert 'Botiquin: 1' in result
    assert 'Extintor: 2' in result
    assert 'Kit' not in result
