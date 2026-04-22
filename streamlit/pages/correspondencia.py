"""
pages/correspondencia.py — Módulo de Correspondencia
Seguimiento de comunicaciones del contrato IDU-1556-2025.
"""

import logging
from datetime import date, datetime

import pandas as pd
import streamlit as st

from database import load_correspondencia, insert_correspondencia, update_correspondencia
from ui import section_badge

_log = logging.getLogger(__name__)

_ESTADOS = ['PENDIENTE', 'RESPONDIDO', 'NO APLICA RESPUESTA']

_COMPONENTES = [
    'Ambiental - SST', 'Social', 'PMT', 'Técnico',
    'Jurídico', 'Financiero', 'General',
]

_COLS_DISPLAY = [
    'emisor', 'receptor', 'consecutivo', 'fecha', 'componente',
    'asunto', 'plazo_respuesta', 'estado',
    'consecutivo_respuesta', 'fecha_respuesta', 'link',
]

_COL_LABELS = {
    'emisor':                'Emisor',
    'receptor':              'Receptor',
    'consecutivo':           'No. Consecutivo',
    'fecha':                 'Fecha',
    'componente':            'Componente',
    'asunto':                'Asunto',
    'plazo_respuesta':       'Plazo Respuesta',
    'estado':                'Estado',
    'consecutivo_respuesta': 'Consecutivo Respuesta',
    'fecha_respuesta':       'Fecha Respuesta',
    'link':                  'Link',
}


def _parse_date(val) -> date | None:
    if not val:
        return None
    try:
        return date.fromisoformat(str(val)[:10])
    except Exception:
        return None


@st.dialog("Nueva Correspondencia", width="large")
def _dialog_nueva(perfil: dict) -> None:
    st.markdown("##### Registrar nueva correspondencia")
    with st.form("form_nueva_corresp", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            emisor        = st.text_input("Emisor *")
            consecutivo   = st.text_input("No. Consecutivo *")
            componente    = st.selectbox("Componente", [""] + _COMPONENTES)
            plazo_resp    = st.date_input("Plazo Respuesta", value=None)
            consec_resp   = st.text_input("Consecutivo Respuesta")
        with c2:
            receptor      = st.text_input("Receptor *")
            fecha         = st.date_input("Fecha *", value=date.today())
            asunto        = st.text_input("Asunto *")
            estado        = st.selectbox("Estado *", _ESTADOS)
            fecha_resp    = st.date_input("Fecha Respuesta", value=None)
        link = st.text_input("Link (URL del documento)")

        submitted = st.form_submit_button("Guardar", type="primary", width="stretch")

    if submitted:
        campos_vacios = not emisor.strip() or not receptor.strip() or \
                        not consecutivo.strip() or not asunto.strip()
        if campos_vacios:
            st.error("Los campos marcados con * son obligatorios.")
            return

        data = {
            'contrato_id':           'IDU-1556-2025',
            'emisor':                emisor.strip(),
            'receptor':              receptor.strip(),
            'consecutivo':           consecutivo.strip(),
            'fecha':                 fecha.isoformat() if fecha else None,
            'componente':            componente if componente else None,
            'asunto':                asunto.strip(),
            'plazo_respuesta':       plazo_resp.isoformat() if plazo_resp else None,
            'estado':                estado,
            'consecutivo_respuesta': consec_resp.strip() or None,
            'fecha_respuesta':       fecha_resp.isoformat() if fecha_resp else None,
            'link':                  link.strip() or None,
            'creado_por':            perfil['id'],
            'creado_en':             datetime.utcnow().isoformat(),
        }
        if insert_correspondencia(data):
            st.success("Correspondencia registrada exitosamente.")
            st.rerun()
        else:
            st.error("Error al guardar. Verifica la conexión e intenta de nuevo.")


@st.dialog("Editar Correspondencia", width="large")
def _dialog_editar(row: dict, perfil: dict) -> None:
    st.markdown(f"##### Editando consecutivo **{row.get('consecutivo', '')}**")

    comp_opts  = [""] + _COMPONENTES
    comp_val   = row.get('componente') or ''
    comp_idx   = comp_opts.index(comp_val) if comp_val in comp_opts else 0
    estado_idx = _ESTADOS.index(row['estado']) if row.get('estado') in _ESTADOS else 0

    # Mostrar auditoría de última modificación
    if row.get('modificado_por_nombre') and row.get('modificado_en'):
        mod_en = str(row.get('modificado_en', ''))[:10]
        st.caption(f"Última modificación: **{row['modificado_por_nombre']}** · {mod_en}")

    with st.form("form_editar_corresp", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            emisor      = st.text_input("Emisor *",           value=row.get('emisor', ''))
            consecutivo = st.text_input("No. Consecutivo *",  value=row.get('consecutivo', ''))
            componente  = st.selectbox("Componente",          comp_opts, index=comp_idx)
            plazo_resp  = st.date_input("Plazo Respuesta",    value=_parse_date(row.get('plazo_respuesta')))
            consec_resp = st.text_input("Consecutivo Respuesta",
                                        value=row.get('consecutivo_respuesta') or '')
        with c2:
            receptor    = st.text_input("Receptor *",         value=row.get('receptor', ''))
            fecha       = st.date_input("Fecha *",            value=_parse_date(row.get('fecha')) or date.today())
            asunto      = st.text_input("Asunto *",           value=row.get('asunto', ''))
            estado      = st.selectbox("Estado *",            _ESTADOS, index=estado_idx)
            fecha_resp  = st.date_input("Fecha Respuesta",    value=_parse_date(row.get('fecha_respuesta')))
        link = st.text_input("Link (URL del documento)", value=row.get('link') or '')

        submitted = st.form_submit_button("Guardar cambios", type="primary", width="stretch")

    if submitted:
        campos_vacios = not emisor.strip() or not receptor.strip() or \
                        not consecutivo.strip() or not asunto.strip()
        if campos_vacios:
            st.error("Los campos marcados con * son obligatorios.")
            return

        data = {
            'emisor':                emisor.strip(),
            'receptor':              receptor.strip(),
            'consecutivo':           consecutivo.strip(),
            'fecha':                 fecha.isoformat() if fecha else None,
            'componente':            componente if componente else None,
            'asunto':                asunto.strip(),
            'plazo_respuesta':       plazo_resp.isoformat() if plazo_resp else None,
            'estado':                estado,
            'consecutivo_respuesta': consec_resp.strip() or None,
            'fecha_respuesta':       fecha_resp.isoformat() if fecha_resp else None,
            'link':                  link.strip() or None,
            'modificado_por':        perfil['id'],
            'modificado_en':         datetime.utcnow().isoformat(),
            'modificado_por_nombre': perfil.get('nombre', ''),
        }
        if update_correspondencia(row['id'], data):
            st.success("Correspondencia actualizada.")
            st.rerun()
        else:
            st.error("Error al actualizar. Verifica la conexión e intenta de nuevo.")


def _highlight_vencidas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Retorna DataFrame con columna _vencida (bool) para usar en el estilo.
    Una fila está vencida cuando: PENDIENTE + plazo_respuesta < hoy.
    """
    today = date.today().isoformat()
    df = df.copy()
    df['_vencida'] = (
        (df.get('estado', pd.Series()) == 'PENDIENTE') &
        (df.get('plazo_respuesta', pd.Series()).astype(str).str[:10] < today) &
        (df.get('plazo_respuesta', pd.Series()).notna()) &
        (df.get('plazo_respuesta', pd.Series()).astype(str) != 'None') &
        (df.get('plazo_respuesta', pd.Series()).astype(str) != 'NaT') &
        (df.get('plazo_respuesta', pd.Series()).astype(str) != '')
    )
    return df


def page_correspondencia(perfil: dict) -> None:
    section_badge("Correspondencia", "teal")
    st.markdown("### Seguimiento de Correspondencia")

    df_raw = load_correspondencia()

    # ── Sección de filtros ────────────────────────────────────
    st.markdown(
        '<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>',
        unsafe_allow_html=True,
    )
    with st.form("form_filtros_corresp"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            f_emisor     = st.text_input("Emisor")
            f_estado     = st.multiselect("Estado", _ESTADOS)
        with fc2:
            f_receptor   = st.text_input("Receptor")
            f_componente = st.multiselect("Componente", _COMPONENTES)
        with fc3:
            f_fecha_ini  = st.date_input("Fecha desde", value=None)
            f_fecha_fin  = st.date_input("Fecha hasta",  value=None)
        aplicar = st.form_submit_button(
            "Aplicar filtros", type="primary", width="stretch"
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Aplicar filtros ───────────────────────────────────────
    df = df_raw.copy() if not df_raw.empty else pd.DataFrame(columns=_COLS_DISPLAY + ['id'])

    if not df.empty and aplicar:
        if f_emisor.strip():
            df = df[df['emisor'].astype(str).str.contains(f_emisor.strip(), case=False, na=False)]
        if f_receptor.strip():
            df = df[df['receptor'].astype(str).str.contains(f_receptor.strip(), case=False, na=False)]
        if f_estado:
            df = df[df['estado'].isin(f_estado)]
        if f_componente:
            df = df[df['componente'].isin(f_componente)]
        if f_fecha_ini:
            df = df[df['fecha'].astype(str) >= f_fecha_ini.isoformat()]
        if f_fecha_fin:
            df = df[df['fecha'].astype(str) <= f_fecha_fin.isoformat()]

    if not df.empty:
        _csv_cols_corresp = [c for c in _COLS_DISPLAY if c in df.columns]
        st.download_button(
            "Exportar CSV",
            data=df[_csv_cols_corresp].to_csv(index=False).encode('utf-8'),
            file_name="Correspondencia_IDU-1556-2025.csv",
            mime="text/csv",
            help="Descargar la tabla visible como archivo CSV",
        )

    # ── Tabla con resaltado de filas vencidas ─────────────────
    if not df.empty:
        df_marked = _highlight_vencidas(df)

        cols_exist = [c for c in _COLS_DISPLAY if c in df_marked.columns]
        df_show    = df_marked[cols_exist].copy()

        def _row_style(row):
            idx  = row.name
            flag = df_marked.loc[idx, '_vencida'] if '_vencida' in df_marked.columns else False
            bg   = 'background-color: rgba(255,210,0,0.22)' if flag else ''
            return [bg] * len(row)

        styled = df_show.style.apply(_row_style, axis=1)

        st.dataframe(
            styled,
            hide_index=True,
            width="stretch",
            column_config={
                'emisor':                st.column_config.TextColumn('Emisor'),
                'receptor':              st.column_config.TextColumn('Receptor'),
                'consecutivo':           st.column_config.TextColumn('No. Consecutivo'),
                'fecha':                 st.column_config.DateColumn('Fecha', format='DD/MM/YYYY'),
                'componente':            st.column_config.TextColumn('Componente'),
                'asunto':                st.column_config.TextColumn('Asunto'),
                'plazo_respuesta':       st.column_config.DateColumn('Plazo Respuesta', format='DD/MM/YYYY'),
                'estado':                st.column_config.TextColumn('Estado'),
                'consecutivo_respuesta': st.column_config.TextColumn('Consecutivo Respuesta'),
                'fecha_respuesta':       st.column_config.DateColumn('Fecha Respuesta', format='DD/MM/YYYY'),
                'link':                  st.column_config.LinkColumn('Link', display_text='Ver documento'),
            },
        )

        # Leyenda de filas vencidas
        n_vencidas = int(df_marked['_vencida'].sum()) if '_vencida' in df_marked.columns else 0
        if n_vencidas > 0:
            st.markdown(
                f'<span style="display:inline-block;width:14px;height:14px;'
                f'background:rgba(255,210,0,0.35);border:1px solid #c8a800;'
                f'border-radius:3px;vertical-align:middle;margin-right:6px;"></span>'
                f'<span style="font-size:0.8rem;color:var(--text-secondary);">'
                f'{n_vencidas} registro(s) PENDIENTE(S) con plazo de respuesta vencido</span>',
                unsafe_allow_html=True,
            )
    else:
        msg = "No hay registros de correspondencia." if df_raw.empty \
              else "No hay registros que coincidan con los filtros aplicados."
        st.info(msg)

    st.divider()

    # ── Acciones: Nuevo y Editar ──────────────────────────────
    can_write = perfil.get('rol') in ('obra', 'admin')

    col_new, col_sep, col_edit = st.columns([1, 0.1, 3])

    with col_new:
        if can_write:
            if st.button("＋ Nuevo", type="primary", width="stretch",
                         help="Registrar nueva correspondencia"):
                _dialog_nueva(perfil)
        else:
            st.caption("Solo gestión puede registrar correspondencia.")

    with col_edit:
        if not df.empty and 'consecutivo' in df.columns and can_write:
            opciones = ['— seleccionar registro —'] + df['consecutivo'].astype(str).tolist()
            sel = st.selectbox(
                "Editar registro existente:",
                opciones,
                key="sel_edit_corresp",
                label_visibility="collapsed",
            )
            if sel != '— seleccionar registro —':
                match = df[df['consecutivo'].astype(str) == sel]
                if not match.empty and st.button(
                    f"Editar · {sel}", key="btn_edit_corresp", width="stretch"
                ):
                    # Tomar el dato completo del df_raw para tener el id y auditoría
                    row_full = df_raw[df_raw['consecutivo'].astype(str) == sel].iloc[0].to_dict()
                    _dialog_editar(row_full, perfil)
