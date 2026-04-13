"""
pages/estado_actual.py — Página: Estado Actual del Contrato
Identificación del contrato, KPIs de plazo y financieros,
tablas de seguimiento de prórrogas y adiciones.

Columnas reales de la tabla `contratos`:
  id, nombre, contratista, intrventoria (typo intencional del Excel),
  supervisor_idu, fecha_inicio, fecha_fin, valor_contrato, valor_actual,
  prorrogas (contador), plazo_actual (fecha), adiciones (contador)
"""

import math
from datetime import datetime, date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import load_contrato, load_prorrogas, load_adiciones
from ui import kpi, section_badge, safe_float


def _fmt_cop(val) -> str:
    v = safe_float(val)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000:
        return f"${v/1_000_000_000:.2f} B"
    if abs(v) >= 1_000_000:
        return f"${v/1_000_000:.1f} M"
    return f"${v:,.0f}"


def page_estado_actual() -> None:
    section_badge("Estado Actual del Contrato", "blue")
    st.markdown("### IDU-1556-2025 · Grupo 4")

    contrato  = load_contrato()
    df_pro    = load_prorrogas()
    df_adi    = load_adiciones()

    if not contrato:
        st.info("Sin datos de contrato en la tabla 'contratos'. "
                "Verifica la sincronización del Excel.")
        return

    # ── Cálculos de tiempo ─────────────────────────────────
    fi_str  = str(contrato.get('fecha_inicio')  or '2025-01-01')[:10]
    ff_str  = str(contrato.get('fecha_fin')     or '2028-01-01')[:10]
    pa_str  = str(contrato.get('plazo_actual')  or ff_str)[:10]

    fecha_inicio   = datetime.strptime(fi_str, '%Y-%m-%d').date()
    fecha_fin_orig = datetime.strptime(ff_str, '%Y-%m-%d').date()
    fecha_fin_act  = datetime.strptime(pa_str, '%Y-%m-%d').date()

    hoy          = date.today()
    dias_trans   = (hoy - fecha_inicio).days
    plazo_orig   = (fecha_fin_orig - fecha_inicio).days
    plazo_total  = max((fecha_fin_act - fecha_inicio).days, 1)
    dias_rest    = max((fecha_fin_act - hoy).days, 0)
    pct_tiempo   = round(min(dias_trans / plazo_total * 100, 100), 1)

    val_ini  = safe_float(contrato.get('valor_contrato')) or 0
    val_act  = safe_float(contrato.get('valor_actual'))   or val_ini
    n_pro    = int(contrato.get('prorrogas')  or 0)
    n_adi    = int(contrato.get('adiciones')  or 0)

    # ── Identificación del contrato ────────────────────────
    st.markdown("#### Identificación del Contrato")
    ci1, ci2 = st.columns(2)

    with ci1:
        kpi("Número de Contrato",
            contrato.get('id', '—'),
            sub=contrato.get('nombre', ''),
            card_accent="accent-blue")
        kpi("Contratista",   contrato.get('contratista', '—'))
        kpi("Interventoría", contrato.get('intrventoria', '—'))

    with ci2:
        kpi("Supervisor IDU", contrato.get('supervisor_idu', '—'))
        kpi("Fecha de Inicio",
            fecha_inicio.strftime('%d/%m/%Y'),
            sub=f"Fecha fin original: {fecha_fin_orig.strftime('%d/%m/%Y')}")
        kpi("Fecha Fin Vigente",
            fecha_fin_act.strftime('%d/%m/%Y'),
            sub=f"{n_pro} prórroga(s) aplicada(s)",
            accent="kpi-orange" if n_pro > 0 else "",
            card_accent="accent-orange" if n_pro > 0 else "")

    st.divider()

    # ── Ejecución del plazo ────────────────────────────────
    st.markdown("#### Ejecución del Plazo")
    ct1, ct2, ct3, ct4 = st.columns(4)

    t_a = "kpi-red"    if pct_tiempo > 85 else ("kpi-orange" if pct_tiempo > 60 else "kpi-green")
    t_c = "accent-red" if pct_tiempo > 85 else ("accent-orange" if pct_tiempo > 60 else "accent-green")

    with ct1: kpi("Días Transcurridos", str(dias_trans),
                  sub=f"{pct_tiempo}% del plazo vigente", accent=t_a, card_accent=t_c)
    with ct2: kpi("Días Restantes", str(dias_rest))
    with ct3: kpi("Plazo Original",  f"{plazo_orig} días",
                  sub=fecha_fin_orig.strftime('%d/%m/%Y'))
    with ct4: kpi("Prórrogas", str(n_pro),
                  sub=f"+{(fecha_fin_act - fecha_fin_orig).days} días totales",
                  accent="kpi-orange" if n_pro > 0 else "",
                  card_accent="accent-orange" if n_pro > 0 else "")

    fig_t = go.Figure(go.Bar(
        x=[pct_tiempo, 100 - pct_tiempo], y=["Plazo"], orientation='h',
        marker_color=['#1a56db', '#dde2eb'],
        text=[f"{pct_tiempo}% transcurrido", ""],
        textposition='inside',
        textfont=dict(family="IBM Plex Mono", size=11, color="white"),
    ))
    fig_t.update_layout(
        height=60, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False, barmode='stack',
        xaxis=dict(showticklabels=False, range=[0, 100]),
        yaxis=dict(showticklabels=False),
    )
    st.plotly_chart(fig_t, use_container_width=True, config={'displayModeBar': False})
    st.divider()

    # ── Ejecución financiera ───────────────────────────────
    st.markdown("#### Ejecución Financiera")
    cf1, cf2, cf3 = st.columns(3)

    diff = val_act - val_ini
    with cf1: kpi("Valor Inicial del Contrato", _fmt_cop(val_ini),
                  sub=f"${val_ini:,.0f}", card_accent="accent-blue")
    with cf2: kpi("Valor Actualizado", _fmt_cop(val_act),
                  sub=f"Δ {_fmt_cop(diff)} · {n_adi} adición(es)",
                  accent="kpi-orange" if diff > 0 else ("kpi-red" if diff < 0 else ""),
                  card_accent="accent-orange" if diff != 0 else "")
    with cf3: kpi("Adiciones", str(n_adi),
                  sub=f"Última: {_fmt_cop(val_act)}", card_accent="accent-green")

    st.divider()

    # ── Tabla de prórrogas ─────────────────────────────────
    st.markdown("#### Seguimiento de Prórrogas")

    if df_pro.empty:
        st.info("Sin prórrogas registradas para este contrato.")
    else:
        cols_pro = [c for c in ['numero','plazo_dias','fecha_fin','fecha_firma','observaciones']
                    if c in df_pro.columns]
        st.dataframe(
            df_pro[cols_pro],
            hide_index=True,
            use_container_width=True,
            column_config={
                'numero':      st.column_config.NumberColumn('No.',              format="%d"),
                'plazo_dias':  st.column_config.NumberColumn('Días adicionados', format="%d"),
                'fecha_fin':   st.column_config.DateColumn('Nueva fecha fin',    format="DD/MM/YYYY"),
                'fecha_firma': st.column_config.DateColumn('Fecha firma',        format="DD/MM/YYYY"),
                'observaciones': st.column_config.TextColumn('Observaciones'),
            }
        )

    st.divider()

    # ── Tabla de adiciones ─────────────────────────────────
    st.markdown("#### Seguimiento de Adiciones Presupuestales")

    if df_adi.empty:
        st.info("Sin adiciones presupuestales registradas para este contrato.")
    else:
        cols_adi = [c for c in ['numero','adicion','valor_actual','fecha_firma','observaciones']
                    if c in df_adi.columns]
        st.dataframe(
            df_adi[cols_adi],
            hide_index=True,
            use_container_width=True,
            column_config={
                'numero':        st.column_config.NumberColumn('No.',               format="%d"),
                'adicion':       st.column_config.NumberColumn('Adición ($)',        format="$%,.0f"),
                'valor_actual':  st.column_config.NumberColumn('Valor Acumulado ($)',format="$%,.0f"),
                'fecha_firma':   st.column_config.DateColumn('Fecha firma',          format="DD/MM/YYYY"),
                'observaciones': st.column_config.TextColumn('Observaciones'),
            }
        )
