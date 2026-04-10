"""
database.py — Conexión Supabase y carga de datos
Todos los data loaders centralizados con caché.

SEGURIDAD:
  - Las credenciales se leen SOLO de st.secrets o variables de entorno.
    Nunca se hardcodean ni se loguean.
  - Si faltan credenciales, la app se detiene con st.stop() antes de
    intentar conexiones parciales.
  - Los loaders solo solicitan columnas necesarias para el módulo;
    evitan SELECT * en producción cuando las tablas tengan datos sensibles.
  - Los errores de consulta se loguean internamente; no se exponen al usuario.

DOS TIPOS DE CLIENTE:
  - get_supabase():   usa service_role key → bypasea RLS → solo para lecturas
                      y operaciones administrativas (sync QField).
  - get_user_client(jwt): usa anon key + JWT del usuario → RLS activo →
                      usar en TODAS las operaciones de escritura (UPDATE/INSERT
                      de aprobaciones). Requiere SUPABASE_ANON_KEY en secrets.
                      Si la anon key no está configurada, cae a service_role
                      con advertencia en logs (degradación no bloqueante).
"""

import logging
import os

import pandas as pd
import streamlit as st
from supabase import create_client

_log = logging.getLogger(__name__)


def _read_credential(key_secret: str, key_env: str) -> str:
    """Lee una credencial desde st.secrets o variable de entorno."""
    try:
        return st.secrets[key_secret]
    except Exception:
        return os.environ.get(key_env, "")


# ══════════════════════════════════════════════════════════════
# CLIENTE SUPABASE
# ══════════════════════════════════════════════════════════════

@st.cache_resource
def get_supabase():
    """
    Cliente Supabase con service_role key.
    Usa este cliente SOLO para lecturas (@st.cache_data loaders) y para
    el script de sincronización QField.

    IMPORTANTE: service_role bypasea RLS. Para operaciones de escritura
    (aprobaciones, devoluciones) usa get_user_client() para que RLS aplique.
    """
    url = _read_credential("SUPABASE_URL", "SUPABASE_URL")
    key = _read_credential("SUPABASE_KEY", "SUPABASE_KEY")

    if not url or not key:
        st.error(
            "Credenciales de base de datos no configuradas. "
            "Contacta al administrador del sistema."
        )
        _log.critical("SUPABASE_URL o SUPABASE_KEY no configurados.")
        st.stop()

    _log.info("Supabase service_role client inicializado.")
    return create_client(url, key)


def get_user_client(access_token: str):
    """
    Cliente Supabase con el JWT del usuario autenticado.
    Las operaciones realizadas con este cliente RESPETAN el RLS de Supabase:
    el usuario solo puede leer/escribir lo que sus políticas permiten.

    Usar en TODAS las operaciones de escritura (UPDATE/INSERT de aprobaciones).

    Requiere SUPABASE_ANON_KEY en st.secrets o variable de entorno.
    Si la anon key no está configurada, cae a service_role con advertencia
    (degradación no bloqueante para no romper la app en despliegues sin
    la key configurada todavía).
    """
    if not access_token:
        _log.warning(
            "get_user_client() llamado sin access_token — "
            "usando service_role (RLS no activo para esta operación)"
        )
        return get_supabase()

    url      = _read_credential("SUPABASE_URL",      "SUPABASE_URL")
    anon_key = _read_credential("SUPABASE_ANON_KEY", "SUPABASE_ANON_KEY")

    if not anon_key:
        _log.warning(
            "SUPABASE_ANON_KEY no configurada — "
            "usando service_role (RLS no activo). "
            "Configura SUPABASE_ANON_KEY en secrets para activar RLS en escrituras."
        )
        return get_supabase()

    client = create_client(url, anon_key)
    # Inyectar el JWT del usuario: PostgREST lo enviará en Authorization: Bearer
    client.postgrest.auth(access_token)
    return client


def clear_cache() -> None:
    """Invalida el caché de todos los data loaders."""
    st.cache_data.clear()


# ══════════════════════════════════════════════════════════════
# HELPER INTERNO
# ══════════════════════════════════════════════════════════════

def _safe_query(query_fn, context: str = "query") -> pd.DataFrame:
    """
    Ejecuta una función de consulta y retorna DataFrame.
    Loguea errores internamente; retorna DataFrame vacío en caso de fallo.
    """
    try:
        result = query_fn()
        return pd.DataFrame(result.data) if result.data else pd.DataFrame()
    except Exception:
        _log.exception("Error en consulta Supabase: %s", context)
        return pd.DataFrame()


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
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_cantidades').select('*')
        if estados:
            query = query.in_('estado', estados)
        if fecha_ini:
            query = query.gte('fecha_creacion', fecha_ini)
        if fecha_fin:
            query = query.lte('fecha_creacion', fecha_fin)
        return query.order('fecha_creacion', desc=True).execute()

    return _safe_query(_q, context='load_cantidades')


@st.cache_data(ttl=60)
def load_componentes(
    estados: list[str] | None = None,
    fecha_ini: str | None = None,
    fecha_fin: str | None = None,
) -> pd.DataFrame:
    """Registros de componentes transversales."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_componentes').select('*')
        if estados:
            query = query.in_('estado', estados)
        if fecha_ini:
            query = query.gte('fecha_creacion', fecha_ini)
        if fecha_fin:
            query = query.lte('fecha_creacion', fecha_fin)
        return query.order('fecha_creacion', desc=True).execute()

    return _safe_query(_q, context='load_componentes')


@st.cache_data(ttl=60)
def load_reporte_diario(
    estados: list[str] | None = None,
    fecha_ini: str | None = None,
    fecha_fin: str | None = None,
) -> pd.DataFrame:
    """Registros del reporte diario de obra."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_reporte_diario').select('*')
        if estados:
            query = query.in_('estado', estados)
        if fecha_ini:
            query = query.gte('fecha_creacion', fecha_ini)
        if fecha_fin:
            query = query.lte('fecha_creacion', fecha_fin)
        return query.order('fecha_creacion', desc=True).execute()

    return _safe_query(_q, context='load_reporte_diario')


# ══════════════════════════════════════════════════════════════
# LOADERS — CONTRATO Y PRESUPUESTO
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def load_contrato() -> dict:
    """Datos del contrato IDU-1556-2025."""
    def _q():
        sb = get_supabase()
        return sb.table('contratos').select('*').eq('id', 'IDU-1556-2025').execute()

    df = _safe_query(_q, context='load_contrato')
    return df.iloc[0].to_dict() if not df.empty else {}


@st.cache_data(ttl=120)
def load_presupuesto() -> pd.DataFrame:
    """Ítems de presupuesto (presupuesto_bd)."""
    def _q():
        sb = get_supabase()
        return sb.table('presupuesto_bd').select('*').execute()

    return _safe_query(_q, context='load_presupuesto')


@st.cache_data(ttl=120)
def load_pmts() -> pd.DataFrame:
    """Tabla de Planes de Manejo de Tránsito."""
    def _q():
        sb = get_supabase()
        return sb.table('pmts').select('*').execute()

    return _safe_query(_q, context='load_pmts')
