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
