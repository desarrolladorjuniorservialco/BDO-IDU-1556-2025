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

def _paginate(query_builder, page_size: int = 1499) -> list:
    """Fetch all rows bypassing Supabase PostgREST's default 1499-row cap."""
    rows, offset = [], 0
    while True:
        batch = query_builder.range(offset, offset + page_size - 1).execute().data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size
    return rows


def _safe_query(query_fn, context: str = "query") -> pd.DataFrame:
    """
    Ejecuta una función de consulta y retorna DataFrame.
    Loguea errores internamente; retorna DataFrame vacío en caso de fallo.
    Acepta que query_fn retorne un objeto con .data o una lista (de _paginate).
    """
    try:
        result = query_fn()
        data = result if isinstance(result, list) else (result.data or [])
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        _log.exception("Error en consulta Supabase: %s", context)
        return pd.DataFrame()


def _chunked_in_query(table: str, column: str, values: list,
                      chunk_size: int = 200) -> pd.DataFrame:
    """
    Ejecuta SELECT * WHERE column IN (values) en lotes para evitar URLs
    demasiado largas (límite ~8 KB de PostgREST con listas grandes).
    """
    if not values:
        return pd.DataFrame()
    frames: list[pd.DataFrame] = []
    sb = get_supabase()
    for i in range(0, len(values), chunk_size):
        chunk = values[i: i + chunk_size]
        def _q(c=chunk):
            return _paginate(sb.table(table).select('*').in_(column, c))
        frames.append(_safe_query(_q, context=f'{table}.{column} chunk {i}'))
    non_empty = [f for f in frames if not f.empty]
    return pd.concat(non_empty, ignore_index=True) if non_empty else pd.DataFrame()


# ══════════════════════════════════════════════════════════════
# LOADERS — FORMULARIOS DE CAMPO
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_cantidades(
    estados: list[str] | None = None,
) -> pd.DataFrame:
    """Registros de medición de cantidades de obra."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_cantidades').select('*')
        if estados:
            query = query.in_('estado', estados)
        return _paginate(query.order('fecha_creacion', desc=True))

    return _safe_query(_q, context='load_cantidades')


@st.cache_data(ttl=60)
def load_componentes(
    estados: list[str] | None = None,
    componente: str | None = None,
) -> pd.DataFrame:
    """Registros de componentes transversales."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_componentes').select('*')
        if estados:
            query = query.in_('estado', estados)
        if componente is not None:
            query = query.eq('componente', componente)
        return _paginate(query.order('fecha_creacion', desc=True))

    return _safe_query(_q, context='load_componentes')


@st.cache_data(ttl=60)
def load_reporte_diario(
    estados: list[str] | None = None,
) -> pd.DataFrame:
    """Registros del reporte diario de obra."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_reporte_diario').select('*')
        if estados:
            query = query.in_('estado', estados)
        return _paginate(query.order('fecha_creacion', desc=True))

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
        return _paginate(sb.table('presupuesto_bd').select('*'))

    return _safe_query(_q, context='load_presupuesto')


@st.cache_data(ttl=300)
def load_prorrogas() -> pd.DataFrame:
    """Prórrogas del contrato IDU-1556-2025."""
    def _q():
        sb = get_supabase()
        return _paginate(sb.table('contratos_prorrogas')
                  .select('*')
                  .eq('contrato_id', 'IDU-1556-2025')
                  .order('numero'))
    return _safe_query(_q, context='load_prorrogas')


@st.cache_data(ttl=300)
def load_adiciones() -> pd.DataFrame:
    """Adiciones presupuestales del contrato IDU-1556-2025."""
    def _q():
        sb = get_supabase()
        return _paginate(sb.table('contratos_adiciones')
                  .select('*')
                  .eq('contrato_id', 'IDU-1556-2025')
                  .order('numero'))
    return _safe_query(_q, context='load_adiciones')


@st.cache_data(ttl=120)
def load_bd_personal(folios: tuple) -> pd.DataFrame:
    """Personal de obra vinculado a folios de reporte diario."""
    return _chunked_in_query('bd_personal_obra', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_bd_clima(folios: tuple) -> pd.DataFrame:
    """Condición climática vinculada a folios de reporte diario."""
    return _chunked_in_query('bd_condicion_climatica', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_bd_maquinaria(folios: tuple) -> pd.DataFrame:
    """Maquinaria en obra vinculada a folios de reporte diario."""
    return _chunked_in_query('bd_maquinaria_obra', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_bd_sst(folios: tuple) -> pd.DataFrame:
    """Datos SST/Ambiental vinculados a folios de reporte diario."""
    return _chunked_in_query('bd_sst_ambiental', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_fotos_cantidades(folios: tuple) -> pd.DataFrame:
    """Fotos de registros de cantidades."""
    return _chunked_in_query('rf_cantidades', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_fotos_componentes(folios: tuple) -> pd.DataFrame:
    """Fotos de registros de componentes."""
    return _chunked_in_query('rf_componentes', 'folio', list(folios))


@st.cache_data(ttl=120)
def load_fotos_reporte(folios: tuple) -> pd.DataFrame:
    """Fotos del reporte diario."""
    return _chunked_in_query('rf_reporte_diario', 'folio', list(folios))


@st.cache_data(ttl=30)
def load_anotaciones_generales(limit: int = 300) -> pd.DataFrame:
    """
    Anotaciones generales de bitácora.
    Retorna las `limit` más recientes ordenadas ASC (más antigua arriba,
    más reciente abajo) para visualización tipo chat.
    TTL corto (30 s) para que el historial se sienta responsivo.
    """
    _cols = (
        'id,fecha,tramo,civ,pk,anotacion,'
        'usuario_nombre,usuario_rol,usuario_empresa,created_at'
    )

    def _q():
        # Traer las más recientes (DESC) y reordenar en Python a ASC
        result = (
            get_supabase()
            .table('anotaciones_generales')
            .select(_cols)
            .order('created_at', desc=True)
            .limit(limit)
            .execute()
        )
        return result

    df = _safe_query(_q, context='load_anotaciones_generales')
    if not df.empty:
        df = df.iloc[::-1].reset_index(drop=True)
    return df


@st.cache_data(ttl=300)
def load_formulario_pmt() -> pd.DataFrame:
    """Formularios PMT registrados en campo."""
    def _q():
        sb = get_supabase()
        return _paginate(sb.table('formulario_pmt')
                  .select('*')
                  .eq('contrato_id', 'IDU-1556-2025'))
    return _safe_query(_q, context='load_formulario_pmt')


@st.cache_data(ttl=300)
def load_presupuesto_componentes() -> pd.DataFrame:
    """Presupuesto de componentes transversales (con precio_unitario)."""
    def _q():
        return _paginate(get_supabase().table('presupuesto_componentes_bd').select('*'))
    return _safe_query(_q, context='load_presupuesto_componentes')


@st.cache_data(ttl=300)
def load_tramos_bd() -> pd.DataFrame:
    """Tramos de obra con meta física y avance ejecutado."""
    def _q():
        return _paginate(get_supabase().table('tramos_bd').select('*'))
    return _safe_query(_q, context='load_tramos_bd')


@st.cache_data(ttl=60)
def load_tramos_bd_historial() -> pd.DataFrame:
    """Historial de modificaciones al campo ejecutado de tramos_bd."""
    def _q():
        return _paginate(
            get_supabase()
            .table('tramos_bd_historial')
            .select('*')
            .order('modificado_en', desc=True)
        )
    return _safe_query(_q, context='load_tramos_bd_historial')


def update_tramo_ejecutado(
    id_tramo: str,
    ejecutado_ant: float | None,
    ejecutado_nuevo: float,
    perfil: dict,
    access_token: str,
) -> bool:
    """
    Actualiza tramos_bd.ejecutado e inserta un registro de auditoría
    en tramos_bd_historial. Usa el cliente con JWT del usuario (RLS activo).
    """
    try:
        client = get_user_client(access_token)
        client.table('tramos_bd').update(
            {'ejecutado': ejecutado_nuevo}
        ).eq('id_tramo', id_tramo).execute()
        client.table('tramos_bd_historial').insert({
            'id_tramo':          id_tramo,
            'ejecutado_ant':     ejecutado_ant,
            'ejecutado_nuevo':   ejecutado_nuevo,
            'modificado_por':    perfil.get('id'),
            'modificado_nombre': perfil.get('nombre', ''),
        }).execute()
        clear_cache()
        return True
    except Exception:
        _log.exception("Error actualizando ejecutado para tramo %s", id_tramo)
        return False


@st.cache_data(ttl=120)
def load_pmts() -> pd.DataFrame:
    """Alias de load_formulario_pmt() — compatibilidad."""
    return load_formulario_pmt()


# ══════════════════════════════════════════════════════════════
# LOADERS — CORRESPONDENCIA
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_correspondencia() -> pd.DataFrame:
    """Registros de correspondencia del contrato IDU-1556-2025."""
    def _q():
        return _paginate(
            get_supabase()
            .table('correspondencia')
            .select('*')
            .eq('contrato_id', 'IDU-1556-2025')
            .order('fecha', desc=True)
        )
    return _safe_query(_q, context='load_correspondencia')


def insert_correspondencia(data: dict) -> bool:
    """Inserta un nuevo registro de correspondencia. Retorna True si OK."""
    try:
        get_supabase().table('correspondencia').insert(data).execute()
        clear_cache()
        return True
    except Exception:
        _log.exception("Error insertando correspondencia")
        return False


def update_correspondencia(record_id: str, data: dict) -> bool:
    """Actualiza un registro de correspondencia. Retorna True si OK."""
    try:
        get_supabase().table('correspondencia').update(data).eq('id', record_id).execute()
        clear_cache()
        return True
    except Exception:
        _log.exception("Error actualizando correspondencia")
        return False
