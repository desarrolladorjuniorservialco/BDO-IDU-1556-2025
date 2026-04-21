"""
pages/seguimiento_pmts.py — Seguimiento de Planes de Manejo de Tránsito
Estado, vigencia y registro histórico de los PMTs del proyecto.
"""

from datetime import date, timedelta

import plotly.express as px
import streamlit as st

from database import load_pmts, load_componentes
from ui import kpi, section_badge


def page_seguimiento_pmts(perfil: dict) -> None:
    section_badge("Seguimiento de Planes de Manejo de Tránsito", "red")
    st.markdown("### Estado y Vigencia de los PMTs")

    df_pmt = load_pmts()

    if df_pmt.empty:
        st.info("Sin registros de PMTs. Configura la tabla 'pmts' en Supabase.")
        import pandas as pd
        df_pmt = pd.DataFrame({
            'codigo':       ['PMT-01', 'PMT-02', 'PMT-03'],
            'tramo':        ['Av. Boyacá x Calle 3',
                             'Carrera 10 x Calle 1S',
                             'Av. Caracas x Calle 14S'],
            'estado':       ['ACTIVO', 'VENCIDO', 'ACTIVO'],
            'vigencia':     ['2025-05-01', '2025-03-15', '2025-06-30'],
            'observaciones':['OK', 'Renovar urgente', 'Modificar por desvío'],
        })

    # ── KPIs ───────────────────────────────────────────────
    activos  = len(df_pmt[df_pmt['estado'] == 'ACTIVO'])  if 'estado' in df_pmt else 0
    vencidos = len(df_pmt[df_pmt['estado'] == 'VENCIDO']) if 'estado' in df_pmt else 0
    total    = len(df_pmt)

    k1, k2, k3 = st.columns(3)
    with k1: kpi("PMTs Totales", str(total), card_accent="accent-blue")
    with k2: kpi("PMTs Activos", str(activos),
                 accent="kpi-green", card_accent="accent-green")
    with k3: kpi("PMTs Vencidos", str(vencidos),
                 accent="kpi-red" if vencidos > 0 else "",
                 card_accent="accent-red" if vencidos > 0 else "")

    st.divider()

    # ── Gráfica de estado + tabla ──────────────────────────
    if 'estado' in df_pmt.columns:
        cnt = df_pmt['estado'].value_counts().reset_index()
        cnt.columns = ['Estado', 'Cantidad']
        fig_pmt = px.pie(
            cnt, names='Estado', values='Cantidad', color='Estado',
            color_discrete_map={
                'ACTIVO':    '#0d7a4e',
                'VENCIDO':   '#b91c1c',
                'EN_TRAMITE':'#c2410c',
            },
            hole=0.5, height=220, title='Estado de PMTs',
        )
        fig_pmt.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True, font=dict(family='IBM Plex Sans'),
        )
        col_fig, col_tbl = st.columns([1, 2])
        with col_fig:
            st.plotly_chart(fig_pmt, use_container_width=True,
                            config={'displayModeBar': False})
        with col_tbl:
            st.markdown("#### Listado de PMTs")
            st.dataframe(df_pmt, hide_index=True, use_container_width=True)
    else:
        st.dataframe(df_pmt, hide_index=True, use_container_width=True)

    # ── Registros de campo asociados ──────────────────────
    st.divider()
    st.markdown("#### Registros de Campo del Período")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df_comp = load_componentes(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if df_comp.empty:
        st.info("No hay registros de componentes en el período.")
    else:
        cols = ['folio', 'usuario_qfield', 'id_tramo',
                'tipo_componente', 'estado', 'fecha']
        cols = [c for c in cols if c in df_comp.columns]
        st.dataframe(df_comp[cols], hide_index=True, use_container_width=True)
