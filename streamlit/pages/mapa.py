"""
pages/mapa.py — Página: Mapa de Ejecución
Distribución geográfica interactiva con 3 capas de datos:
  · Cantidades de Obra      (registros_cantidades)
  · Componentes Transv.     (registros_componentes)
  · Reporte Diario          (registros_reporte_diario)

Filtros disponibles:
  · Rango de fechas
  · Estado de registro
  · Tramo, CIV, ítem de pago, componente/capítulo
  · Búsqueda libre por texto

Indicadores acumulados de acuerdo a los filtros activos.
"""

import re
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import load_cantidades, load_componentes, load_reporte_diario
from ui import kpi, section_badge

# Paleta de colores por estado
_ESTADO_COLOR = {
    'BORRADOR': '#637090',
    'REVISADO': '#005c4e',
    'APROBADO': '#1a3a6e',
    'DEVUELTO': '#aa1b1b',
}

# Color base de cada capa
_LAYER_COLOR = {
    'cantidades':  '#1a3a6e',
    'componentes': '#c97a00',
    'diario':      '#5b21b6',
}

_ESTADO_OPTS = ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]


def _latlon_df(df: pd.DataFrame) -> pd.DataFrame:
    """Filtra y convierte lat/lon a numérico."""
    if df.empty or 'latitud' not in df.columns or 'longitud' not in df.columns:
        return pd.DataFrame()
    d = df.dropna(subset=['latitud', 'longitud']).copy()
    d['latitud']  = pd.to_numeric(d['latitud'],  errors='coerce')
    d['longitud'] = pd.to_numeric(d['longitud'], errors='coerce')
    return d.dropna(subset=['latitud', 'longitud'])


def _scatter(df: pd.DataFrame, name: str, color: str,
             hover_cols: list[str], symbol: str = 'circle') -> go.Scattermapbox:
    avail = [c for c in hover_cols if c in df.columns]
    parts = [f"<b>{c}:</b> %{{customdata[{i}]}}" for i, c in enumerate(avail)]
    customdata = df[avail].astype(str).values.tolist()

    return go.Scattermapbox(
        lat=df['latitud'],
        lon=df['longitud'],
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=11, color=color, symbol=symbol, opacity=0.85,
        ),
        name=name,
        customdata=customdata,
        hovertemplate="<br>".join(parts) + "<extra></extra>",
    )


def _text_filter(df: pd.DataFrame, cols: list[str], val: str) -> pd.DataFrame:
    if not val.strip() or df.empty:
        return df
    b = re.escape(val.strip())
    mask = pd.Series(False, index=df.index)
    for c in cols:
        if c in df.columns:
            mask |= df[c].astype(str).str.contains(b, case=False, na=False)
    return df[mask]


def page_mapa(perfil: dict) -> None:
    section_badge("Mapa de Ejecución", "teal")
    st.markdown("### Distribución Geográfica de Registros")

    # ── Formulario de filtros ──────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros y capas</div>', unsafe_allow_html=True)
    with st.form("form_mapa"):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            fi = st.date_input("Desde",
                               value=date.today() - timedelta(days=30),
                               key="map_fi")
        with fc2:
            ff = st.date_input("Hasta", value=date.today(), key="map_ff")
        with fc3:
            estado_f = st.selectbox("Estado", _ESTADO_OPTS, key="map_est")
        with fc4:
            buscar = st.text_input("Búsqueda libre (folio, CIV, tramo…)", key="map_bus")

        fa1, fa2, fa3, fa4 = st.columns(4)
        with fa1:
            tramo_f = st.text_input("Tramo", key="map_tramo")
        with fa2:
            civ_f   = st.text_input("CIV",   key="map_civ")
        with fa3:
            item_f  = st.text_input("Ítem de pago", key="map_item")
        with fa4:
            comp_f  = st.text_input("Componente / Cap.", key="map_comp")

        lc1, lc2, lc3 = st.columns(3)
        with lc1:
            show_cant   = st.checkbox("Cantidades de Obra",  value=True, key="map_cant")
        with lc2:
            show_comp   = st.checkbox("Componentes Transv.", value=True, key="map_comp_tog")
        with lc3:
            show_diario = st.checkbox("Reporte Diario",      value=True, key="map_diario")

        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not aplicar and 'mapa_loaded' not in st.session_state:
        st.info("Define los filtros y presiona **Aplicar filtros** para cargar el mapa.")
        return
    st.session_state['mapa_loaded'] = True

    estados_q = None if estado_f == "Todos" else [estado_f]

    # ── Carga de datos ─────────────────────────────────────
    df_cant   = (load_cantidades(estados=estados_q,
                                 fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
                 if show_cant else pd.DataFrame())
    df_comp   = (load_componentes(estados=estados_q,
                                  fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
                 if show_comp else pd.DataFrame())
    df_diario = (load_reporte_diario(estados=estados_q,
                                     fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
                 if show_diario else pd.DataFrame())

    # ── Filtros de texto ───────────────────────────────────
    base_cols = ['folio', 'id_tramo', 'civ', 'usuario_qfield']
    df_cant   = _text_filter(df_cant,   base_cols + ['tipo_actividad','item_pago'],   buscar)
    df_comp   = _text_filter(df_comp,   base_cols + ['tipo_componente','tipo_actividad'], buscar)
    df_diario = _text_filter(df_diario, base_cols + ['observaciones'],                buscar)

    def _adv_filter(df, col, val):
        if val.strip() and not df.empty and col in df.columns:
            return df[df[col].astype(str).str.contains(
                re.escape(val.strip()), case=False, na=False
            )]
        return df

    df_cant = _adv_filter(df_cant, 'id_tramo',        tramo_f)
    df_cant = _adv_filter(df_cant, 'civ',             civ_f)
    df_cant = _adv_filter(df_cant, 'item_pago',       item_f)
    df_cant = _adv_filter(df_cant, 'codigo_elemento', comp_f)
    df_comp = _adv_filter(df_comp, 'id_tramo',        tramo_f)
    df_comp = _adv_filter(df_comp, 'civ',             civ_f)
    df_comp = _adv_filter(df_comp, 'tipo_componente', comp_f)

    # ── Geolocalizar ───────────────────────────────────────
    geo_cant   = _latlon_df(df_cant)
    geo_comp   = _latlon_df(df_comp)
    geo_diario = _latlon_df(df_diario)

    # ── Indicadores acumulados ─────────────────────────────
    ki1, ki2, ki3, ki4 = st.columns(4)
    with ki1:
        kpi("Cantidades (coord.)",  str(len(geo_cant)),   card_accent="accent-blue")
    with ki2:
        kpi("Componentes (coord.)", str(len(geo_comp)),   card_accent="accent-orange")
    with ki3:
        kpi("Diario (coord.)",      str(len(geo_diario)), card_accent="accent-purple")
    with ki4:
        total_geo = len(geo_cant) + len(geo_comp) + len(geo_diario)
        # Suma cantidades aprobadas en el filtro actual
        if not df_cant.empty and 'estado' in df_cant.columns:
            apr_cant = df_cant[df_cant['estado'] == 'APROBADO']
            cant_col = 'cant_interventor' if 'cant_interventor' in apr_cant.columns else 'cantidad'
            if cant_col in apr_cant.columns:
                import pandas as _pd
                suma_apr = _pd.to_numeric(apr_cant[cant_col], errors='coerce').fillna(0).sum()
                kpi("Σ Cant. aprobadas",
                    f"{suma_apr:,.2f}",
                    sub="registros_cantidades · APROBADO",
                    card_accent="accent-green")
            else:
                kpi("Total en mapa", str(total_geo))
        else:
            kpi("Total en mapa", str(total_geo))

    all_empty = geo_cant.empty and geo_comp.empty and geo_diario.empty
    if all_empty:
        st.info("No hay registros con coordenadas para los filtros seleccionados.")
    else:
        # ── Mapa ───────────────────────────────────────────
        traces: list[go.BaseTraceType] = []

        if not geo_cant.empty:
            by_est = geo_cant.groupby('estado') if 'estado' in geo_cant.columns else [('', geo_cant)]
            for estado, grp in by_est:
                color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['cantidades'])
                traces.append(_scatter(
                    grp, f"Cantidades — {estado}", color,
                    ['folio', 'id_tramo', 'civ', 'tipo_actividad',
                     'cantidad', 'unidad', 'item_pago', 'estado'],
                ))

        if not geo_comp.empty:
            by_est = geo_comp.groupby('estado') if 'estado' in geo_comp.columns else [('', geo_comp)]
            for estado, grp in by_est:
                color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['componentes'])
                traces.append(_scatter(
                    grp, f"Componentes — {estado}", color,
                    ['folio', 'id_tramo', 'tipo_componente', 'tipo_actividad',
                     'cantidad', 'unidad', 'estado'],
                    symbol='square',
                ))

        if not geo_diario.empty:
            by_est = geo_diario.groupby('estado') if 'estado' in geo_diario.columns else [('', geo_diario)]
            for estado, grp in by_est:
                color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['diario'])
                traces.append(_scatter(
                    grp, f"Reporte Diario — {estado}", color,
                    ['folio', 'usuario_qfield', 'observaciones', 'estado'],
                    symbol='star',
                ))

        # Centro automático
        all_lats, all_lons = [], []
        for gdf in [geo_cant, geo_comp, geo_diario]:
            if not gdf.empty:
                all_lats.extend(gdf['latitud'].tolist())
                all_lons.extend(gdf['longitud'].tolist())
        center_lat = sum(all_lats) / len(all_lats) if all_lats else 4.65
        center_lon = sum(all_lons) / len(all_lons) if all_lons else -74.08

        fig = go.Figure(traces)
        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=13,
            ),
            height=580,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                orientation="v",
                x=0.01, y=0.99,
                bgcolor='rgba(255,255,255,0.88)',
                bordercolor='#d0d9e8',
                borderwidth=1,
                font=dict(size=10, family='Barlow'),
            ),
        )
        st.plotly_chart(fig, use_container_width=True,
                        config={'displayModeBar': True, 'scrollZoom': True})

    st.divider()

    # ── Tablas de registros con coordenadas ────────────────
    with st.expander("Tablas de registros con coordenadas", expanded=False):
        tab_c, tab_comp, tab_d = st.tabs([
            "Cantidades", "Componentes", "Reporte Diario",
        ])

        with tab_c:
            if geo_cant.empty:
                st.info("Sin registros de cantidades con coordenadas.")
            else:
                cols = [c for c in [
                    'folio', 'fecha_creacion', 'id_tramo', 'civ',
                    'tipo_actividad', 'item_pago', 'cantidad', 'unidad',
                    'estado', 'latitud', 'longitud',
                ] if c in geo_cant.columns]
                st.dataframe(geo_cant[cols], hide_index=True, use_container_width=True)

        with tab_comp:
            if geo_comp.empty:
                st.info("Sin registros de componentes con coordenadas.")
            else:
                cols = [c for c in [
                    'folio', 'fecha_creacion', 'id_tramo', 'tipo_componente',
                    'tipo_actividad', 'cantidad', 'unidad', 'estado',
                    'latitud', 'longitud',
                ] if c in geo_comp.columns]
                st.dataframe(geo_comp[cols], hide_index=True, use_container_width=True)

        with tab_d:
            if geo_diario.empty:
                st.info("Sin registros de reporte diario con coordenadas.")
            else:
                cols = [c for c in [
                    'folio', 'fecha_reporte', 'usuario_qfield',
                    'observaciones', 'estado', 'latitud', 'longitud',
                ] if c in geo_diario.columns]
                st.dataframe(geo_diario[cols], hide_index=True, use_container_width=True)
