"""
pages/mapa.py — Página: Mapa de Obra
Distribución geográfica de registros de cantidades.
"""

from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import load_cantidades
from ui import section_badge


def page_mapa(perfil: dict) -> None:
    section_badge("Mapa de Obra", "teal")
    st.markdown("### Distribución Geográfica de Registros")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=30))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df = load_cantidades(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if df.empty or 'latitud' not in df.columns:
        st.info("No hay registros con coordenadas para el período seleccionado.")
        return

    df_geo = df.dropna(subset=['latitud', 'longitud']).copy()
    df_geo['latitud']  = pd.to_numeric(df_geo['latitud'],  errors='coerce')
    df_geo['longitud'] = pd.to_numeric(df_geo['longitud'], errors='coerce')
    df_geo = df_geo.dropna(subset=['latitud', 'longitud'])

    if df_geo.empty:
        st.info("No hay registros con coordenadas válidas.")
        return

    color_map = {
        'BORRADOR': '#6b7280',
        'REVISADO': '#0d7a4e',
        'APROBADO': '#1a56db',
        'DEVUELTO': '#b91c1c',
    }

    hover_cols = {c: True for c in
                  ['folio', 'tipo_actividad', 'id_tramo', 'cantidad', 'unidad']
                  if c in df_geo.columns}

    fig = px.scatter_mapbox(
        df_geo,
        lat='latitud', lon='longitud',
        color='estado' if 'estado' in df_geo else None,
        color_discrete_map=color_map,
        hover_data=hover_cols or None,
        zoom=12, height=540,
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(orientation="h", y=0.01, x=0.01,
                    bgcolor='rgba(255,255,255,0.8)'),
    )
    st.plotly_chart(fig, use_container_width=True)
