"""
pages/mapa.py — Página: Mapa de Ejecución
Distribución geográfica con 3 capas:
  · Cantidades de Obra      (registros_cantidades)
  · Componentes Transv.     (registros_componentes)
  · Reporte Diario          (registros_reporte_diario)
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import load_cantidades, load_componentes, load_reporte_diario
from ui import section_badge


# Paleta de colores por estado (consistente en toda la app)
_ESTADO_COLOR = {
    'BORRADOR': '#6b7280',
    'REVISADO': '#0d7a4e',
    'APROBADO': '#1a56db',
    'DEVUELTO': '#b91c1c',
}

# Color de capa cuando no se diferencia por estado
_LAYER_COLOR = {
    'cantidades':   '#1a56db',
    'componentes':  '#d97706',
    'diario':       '#7c3aed',
}


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
    hover_parts = []
    for c in hover_cols:
        if c in df.columns:
            hover_parts.append(f"<b>{c}:</b> %{{customdata[{hover_cols.index(c)}]}}")
    customdata = df[[c for c in hover_cols if c in df.columns]].values.tolist()

    return go.Scattermapbox(
        lat=df['latitud'],
        lon=df['longitud'],
        mode='markers',
        marker=go.scattermapbox.Marker(size=10, color=color, symbol=symbol),
        name=name,
        customdata=customdata,
        hovertemplate="<br>".join(hover_parts) + "<extra></extra>",
    )


def page_mapa(perfil: dict) -> None:
    section_badge("Mapa de Ejecución", "teal")
    st.markdown("### Distribución Geográfica de Registros")

    # ── Filtros globales ───────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1: fi = st.date_input("Desde", value=date.today() - timedelta(days=30), key="map_fi")
    with fc2: ff = st.date_input("Hasta", value=date.today(), key="map_ff")
    with fc3:
        estado_f = st.selectbox("Estado", ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"],
                                key="map_est")
    with fc4:
        buscar = st.text_input("Tramo / CIV / Folio", key="map_bus")

    estados_q = None if estado_f == "Todos" else [estado_f]

    # ── Toggles de capa ────────────────────────────────────────
    lc1, lc2, lc3 = st.columns(3)
    with lc1: show_cant  = st.checkbox("Cantidades de Obra",     value=True,  key="map_cant")
    with lc2: show_comp  = st.checkbox("Componentes Transv.",    value=True,  key="map_comp")
    with lc3: show_diario = st.checkbox("Reporte Diario",        value=False, key="map_diario")

    # ── Carga de datos ─────────────────────────────────────────
    df_cant = load_cantidades(estados=estados_q,
                              fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat()) if show_cant else pd.DataFrame()
    df_comp = load_componentes(estados=estados_q,
                               fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat()) if show_comp else pd.DataFrame()
    df_diario = load_reporte_diario(estados=estados_q,
                                    fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat()) if show_diario else pd.DataFrame()

    # Filtro texto libre
    def _text_filter(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        if not buscar or df.empty:
            return df
        import re
        b = re.escape(buscar)
        mask = pd.Series(False, index=df.index)
        for c in cols:
            if c in df.columns:
                mask |= df[c].astype(str).str.contains(b, case=False, na=False)
        return df[mask]

    df_cant   = _text_filter(df_cant,   ['folio', 'id_tramo', 'civ'])
    df_comp   = _text_filter(df_comp,   ['folio', 'id_tramo', 'civ'])
    df_diario = _text_filter(df_diario, ['folio', 'usuario_qfield'])

    # Convertir a georef
    geo_cant   = _latlon_df(df_cant)
    geo_comp   = _latlon_df(df_comp)
    geo_diario = _latlon_df(df_diario)

    # ── Métricas ───────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Cantidades c/ coord.", len(geo_cant))
    with m2: st.metric("Componentes c/ coord.", len(geo_comp))
    with m3: st.metric("Reporte Diario c/ coord.", len(geo_diario))

    all_empty = geo_cant.empty and geo_comp.empty and geo_diario.empty
    if all_empty:
        st.info("No hay registros con coordenadas para los filtros seleccionados.")
        return

    # ── Mapa ───────────────────────────────────────────────────
    traces = []

    if not geo_cant.empty:
        for estado, grp in geo_cant.groupby('estado') if 'estado' in geo_cant.columns else [('', geo_cant)]:
            color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['cantidades'])
            traces.append(_scatter(
                grp, f"Cantidades — {estado}", color,
                ['folio', 'id_tramo', 'civ', 'tipo_actividad', 'cantidad', 'unidad', 'estado'],
            ))

    if not geo_comp.empty:
        for estado, grp in geo_comp.groupby('estado') if 'estado' in geo_comp.columns else [('', geo_comp)]:
            color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['componentes'])
            traces.append(_scatter(
                grp, f"Componentes — {estado}", color,
                ['folio', 'id_tramo', 'componente', 'tipo_actividad', 'estado'],
                symbol='square',
            ))

    if not geo_diario.empty:
        for estado, grp in geo_diario.groupby('estado') if 'estado' in geo_diario.columns else [('', geo_diario)]:
            color = _ESTADO_COLOR.get(str(estado), _LAYER_COLOR['diario'])
            traces.append(_scatter(
                grp, f"Reporte Diario — {estado}", color,
                ['folio', 'usuario_qfield', 'observaciones', 'estado'],
                symbol='star',
            ))

    # Centro del mapa: promedio de coordenadas disponibles
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
        height=560,
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            orientation="v", x=0.01, y=0.99,
            bgcolor='rgba(255,255,255,0.85)',
            bordercolor='#dde2eb', borderwidth=1,
            font=dict(size=11),
        ),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ── Tabla resumen ──────────────────────────────────────────
    with st.expander("Ver tabla de registros"):
        tab_c, tab_comp, tab_d = st.tabs(["Cantidades", "Componentes", "Reporte Diario"])
        with tab_c:
            if geo_cant.empty:
                st.info("Sin registros de cantidades con coordenadas.")
            else:
                cols = [c for c in ['folio', 'id_tramo', 'civ', 'tipo_actividad',
                                    'cantidad', 'unidad', 'estado', 'latitud', 'longitud']
                        if c in geo_cant.columns]
                st.dataframe(geo_cant[cols], hide_index=True, use_container_width=True)
        with tab_comp:
            if geo_comp.empty:
                st.info("Sin registros de componentes con coordenadas.")
            else:
                cols = [c for c in ['folio', 'id_tramo', 'componente',
                                    'tipo_actividad', 'estado', 'latitud', 'longitud']
                        if c in geo_comp.columns]
                st.dataframe(geo_comp[cols], hide_index=True, use_container_width=True)
        with tab_d:
            if geo_diario.empty:
                st.info("Sin registros de reporte diario con coordenadas.")
            else:
                cols = [c for c in ['folio', 'usuario_qfield', 'observaciones',
                                    'estado', 'latitud', 'longitud']
                        if c in geo_diario.columns]
                st.dataframe(geo_diario[cols], hide_index=True, use_container_width=True)
