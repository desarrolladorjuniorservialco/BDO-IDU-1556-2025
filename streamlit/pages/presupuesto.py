"""
pages/presupuesto.py — Página: Seguimiento Presupuestal
Consulta y visualización de la tabla presupuesto_bd.
"""

import plotly.graph_objects as go
import streamlit as st

from database import load_presupuesto
from ui import kpi, section_badge, safe_float


def page_presupuesto(perfil: dict) -> None:
    section_badge("Seguimiento Presupuestal", "orange")
    st.markdown("### Presupuesto del Contrato")

    df = load_presupuesto()

    if df.empty:
        st.info("Sin datos de presupuesto. Verifica la tabla 'presupuesto_bd' en Supabase.")
        return

    # Normalizar typo de columna del GPKG
    if 'compenente' in df.columns and 'componente' not in df.columns:
        df = df.rename(columns={'compenente': 'componente'})

    cols_show = [c for c in [
        'componente', 'item_pago', 'descripcion', 'und',
        'cantidad_contrato', 'valor_unitario', 'valor_total',
        'cantidad_ejecutada', 'valor_ejecutado', 'pct_ejecutado',
    ] if c in df.columns]

    # ── KPIs financieros ───────────────────────────────────
    if 'valor_total' in df.columns:
        total_c = df['valor_total'].apply(safe_float).sum()
        total_e = (df['valor_ejecutado'].apply(safe_float).sum()
                   if 'valor_ejecutado' in df.columns else 0)
        pct_e   = round(total_e / total_c * 100, 1) if total_c > 0 else 0

        k1, k2, k3 = st.columns(3)
        with k1: kpi("Valor Total Contrato", f"${total_c:,.0f}",
                     accent="kpi-blue", card_accent="accent-blue")
        with k2: kpi("Valor Ejecutado", f"${total_e:,.0f}",
                     sub=f"{pct_e}% del contrato",
                     accent="kpi-green" if pct_e >= 70 else "kpi-orange",
                     card_accent="accent-green" if pct_e >= 70 else "accent-orange")
        with k3: kpi("Valor Pendiente", f"${max(total_c - total_e, 0):,.0f}",
                     card_accent="accent-red" if pct_e < 50 else "")
        st.divider()

    # ── Gráfica por componente ─────────────────────────────
    if 'componente' in df.columns and 'valor_total' in df.columns:
        agg = {'valor_total': ('valor_total', lambda x: x.apply(safe_float).sum())}
        if 'valor_ejecutado' in df.columns:
            agg['valor_ejecutado'] = ('valor_ejecutado',
                                      lambda x: x.apply(safe_float).sum())
        df_grp = df.groupby('componente').agg(**agg).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Presupuestado', x=df_grp['componente'],
            y=df_grp['valor_total'], marker_color='#1a56db',
        ))
        if 'valor_ejecutado' in df_grp.columns:
            fig.add_trace(go.Bar(
                name='Ejecutado', x=df_grp['componente'],
                y=df_grp['valor_ejecutado'], marker_color='#0d7a4e',
            ))
        fig.update_layout(
            barmode='group', height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='IBM Plex Sans'),
            legend=dict(orientation='h', y=1.1),
            yaxis_title='Valor ($)',
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ── Tabla ──────────────────────────────────────────────
    if cols_show:
        st.dataframe(
            df[cols_show], hide_index=True, use_container_width=True,
            column_config={
                'valor_total':     st.column_config.NumberColumn(
                    'Valor Total ($)',     format="$%.0f"),
                'valor_ejecutado': st.column_config.NumberColumn(
                    'Valor Ejecutado ($)', format="$%.0f"),
                'valor_unitario':  st.column_config.NumberColumn(
                    'Valor Unitario ($)',  format="$%.0f"),
                'pct_ejecutado':   st.column_config.ProgressColumn(
                    'Ejecutado (%)', format="%.1f%%", min_value=0, max_value=100),
            },
        )
        csv = df[cols_show].to_csv(index=False).encode('utf-8')
        st.download_button("Exportar CSV", data=csv,
                           file_name="Presupuesto_IDU-1556-2025.csv",
                           mime="text/csv")
    else:
        st.dataframe(df, hide_index=True, use_container_width=True)
