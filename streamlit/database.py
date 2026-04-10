"""
database.py — Conexión Supabase y carga de datos
Todos los data loaders centralizados con caché.
"""

import os
import streamlit as st
import pandas as pd
from supabase import create_client


# ══════════════════════════════════════════════════════════════
# CLIENTE SUPABASE
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase():
    """
    Retorna el cliente Supabase inicializado.
    Prioriza st.secrets; cae a variables de entorno.
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_KEY", "")
    if not url or not key:
        st.error("Configura SUPABASE_URL y SUPABASE_KEY en secrets.toml o variables de entorno.")
        st.stop()
    return create_client(url, key)


def clear_cache() -> None:
    """Invalida el caché de todos los data loaders."""
    st.cache_data.clear()


# ══════════════════════════════════════════════════════════════
# LOADERS — FORMULARIOS DE CAMPO
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_cantidades(
    estados: list[str] | None = None,
    fecha_ini: str | None = None,
    fecha_fin: str | None = None,
) -> pd.DataFrame:
    """Registros de medición de cantidades de obra."""
    sb    = get_supabase()
    query = sb.table('registros_cantidades').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_componentes(
    estados: list[str] | None = None,
    fecha_ini: str | None = None,
    fecha_fin: str | None = None,
) -> pd.DataFrame:
    """Registros de componentes transversales (ambiental, SST, social, PMT)."""
    sb    = get_supabase()
    query = sb.table('registros_componentes').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


@st.cache_data(ttl=60)
def load_reporte_diario(
    estados: list[str] | None = None,
    fecha_ini: str | None = None,
    fecha_fin: str | None = None,
) -> pd.DataFrame:
    """Registros del reporte diario de obra."""
    sb    = get_supabase()
    query = sb.table('registros_reporte_diario').select('*')
    if estados:
        query = query.in_('estado', estados)
    if fecha_ini:
        query = query.gte('fecha_creacion', fecha_ini)
    if fecha_fin:
        query = query.lte('fecha_creacion', fecha_fin)
    result = query.order('fecha_creacion', desc=True).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


# ══════════════════════════════════════════════════════════════
# LOADERS — DATOS DEL CONTRATO Y PRESUPUESTO
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_contrato() -> dict:
    """Datos del contrato IDU-1556-2025."""
    sb = get_supabase()
    r  = sb.table('contratos').select('*').eq('id', 'IDU-1556-2025').execute()
    return r.data[0] if r.data else {}


@st.cache_data(ttl=120)
def load_presupuesto() -> pd.DataFrame:
    """Ítems de presupuesto (presupuesto_bd)."""
    sb = get_supabase()
    r  = sb.table('presupuesto_bd').select('*').execute()
    return pd.DataFrame(r.data) if r.data else pd.DataFrame()


@st.cache_data(ttl=120)
def load_pmts() -> pd.DataFrame:
    """Tabla de Planes de Manejo de Tránsito."""
    sb = get_supabase()
    try:
        r = sb.table('pmts').select('*').execute()
        return pd.DataFrame(r.data) if r.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()
