"""
pages/reporte_cantidades.py — Página: Reportes de Cantidades
Medición y validación de cantidades de obra con gráficas y exportación CSV.

SEGURIDAD:
  - re.escape() previene ReDoS en el campo de búsqueda libre.
"""

import re
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import load_cantidades
from ui import kpi, section_badge, safe_float


def page_reporte_cantidades(perfil: dict) -> None:
    section_badge("Reportes de Cantidades", "blue")
    st.markdown("### Medición y Validación de Cantidades de Obra")

    c1, c2, c3 = st.columns(3)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3: buscar = st.text_input("Folio / Actividad")

    df = load_cantidades(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        # re.escape previene ReDoS: el input se trata como literal, no como regex
        buscar_safe = re.escape(buscar)
        mask = (
            df.get('folio', pd.Series(dtype=str))
              .astype(str).str.contains(buscar_safe, case=False, na=False)
            | df.get('tipo_actividad', pd.Series(dtype=str))
              .astype(str).str.contains(buscar_safe, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay registros para el período seleccionado")
        return

    # ── KPIs ───────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    total_cant = df['cantidad'].apply(safe_float).sum() if 'cantidad' in df.columns else 0
    with m1: kpi("Total registros", str(len(df)), card_accent="accent-blue")
    with m2: kpi("Aprobados",
                 str(len(df[df['estado'] == 'APROBADO'])) if 'estado' in df else "0",
                 accent="kpi-green", card_accent="accent-green")
    with m3: kpi("Revisados",
                 str(len(df[df['estado'] == 'REVISADO'])) if 'estado' in df else "0",
                 accent="kpi-blue", card_accent="accent-blue")
    with m4: kpi("Devueltos",
                 str(len(df[df['estado'] == 'DEVUELTO'])) if 'estado' in df else "0",
                 accent="kpi-red", card_accent="accent-red")
    with m5: kpi("Suma cantidades", f"{total_cant:,.2f}", card_accent="accent-purple")

    st.divider()

    # ── Gráfica distribución por estado ───────────────────
    if 'estado' in df.columns:
        cnt = df['estado'].value_counts().reset_index()
        cnt.columns = ['Estado', 'Cantidad']
        fig_e = px.bar(
            cnt, x='Estado', y='Cantidad', color='Estado',
            color_discrete_map={
                'APROBADO': '#1a56db', 'REVISADO': '#0d7a4e',
                'DEVUELTO': '#b91c1c', 'BORRADOR': '#6b7280',
            },
            height=220, title='Distribución por Estado',
        )
        fig_e.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False, font=dict(family='IBM Plex Sans'),
        )
        st.plotly_chart(fig_e, use_container_width=True,
                        config={'displayModeBar': False})

    st.divider()

    # ── Tabla de registros ─────────────────────────────────
    cols_show = ['folio', 'usuario_qfield', 'id_tramo', 'civ', 'codigo_elemento',
                 'tipo_actividad', 'item_pago', 'item_descripcion',
                 'cantidad', 'unidad', 'cant_residente', 'cant_interventor', 'estado']
    cols_show = [c for c in cols_show if c in df.columns]

    st.dataframe(
        df[cols_show], hide_index=True, use_container_width=True,
        column_config={
            'cantidad':         st.column_config.NumberColumn('Cant. Inspector',   format="%.2f"),
            'cant_residente':   st.column_config.NumberColumn('Cant. Residente',   format="%.2f"),
            'cant_interventor': st.column_config.NumberColumn('Cant. Interventor', format="%.2f"),
            'estado':           st.column_config.TextColumn('Estado'),
        },
    )

    csv = df[cols_show].to_csv(index=False).encode('utf-8')
    st.download_button(
        "Exportar CSV", data=csv,
        file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
