"""
pages/estado_actual.py — Página: Estado Actual del Contrato
KPIs de plazo y ejecución financiera.
"""

from datetime import datetime, date

import plotly.graph_objects as go
import streamlit as st

from database import load_contrato
from ui import kpi, section_badge, safe_float


def page_estado_actual() -> None:
    section_badge("Estado Actual del Contrato", "blue")
    st.markdown("### IDU-1556-2025 · Grupo 4")

    contrato = load_contrato()
    if not contrato:
        st.info("Sin datos de contrato. Verifica la tabla 'contratos' en Supabase.")
        contrato = {
            "numero": "IDU-1556-2025",
            "objeto": "Mantenimiento y rehabilitación de vías locales — Grupo 4",
            "entidad": "Instituto de Desarrollo Urbano (IDU)",
            "contratista": "SERVIALCO S.A.S.",
            "valor_inicial": 8_500_000_000,
            "valor_actualizado": 8_500_000_000,
            "plazo_dias": 180,
            "fecha_inicio": "2025-02-01",
            "anticipos_total": 1,
            "valor_anticipo": 2_550_000_000,
            "valor_amortizado": 850_000_000,
            "adicion_plazo_dias": 0,
            "adicion_valor": 0,
            "valor_ejecutado": 3_200_000_000,
        }

    # ── Cálculos ───────────────────────────────────────────
    fecha_inicio = datetime.strptime(
        contrato.get('fecha_inicio', '2025-01-01'), '%Y-%m-%d'
    ).date()
    adicion_dias = int(contrato.get('adicion_plazo_dias', 0) or 0)
    plazo        = int(contrato.get('plazo_dias', 0)) + adicion_dias
    dias_trans   = (date.today() - fecha_inicio).days
    dias_rest    = max(plazo - dias_trans, 0)
    pct_tiempo   = round(min(dias_trans / plazo * 100, 100)) if plazo > 0 else 0

    val_ini   = safe_float(contrato.get('valor_inicial'))  or 0
    val_act   = safe_float(contrato.get('valor_actualizado')) or val_ini
    val_ejec  = safe_float(contrato.get('valor_ejecutado'))  or 0
    pct_ejec  = round(val_ejec / val_act * 100, 1) if val_act > 0 else 0
    val_ant   = safe_float(contrato.get('valor_anticipo'))   or 0
    val_amort = safe_float(contrato.get('valor_amortizado')) or 0
    pct_amort = round(val_amort / val_ant * 100, 1) if val_ant > 0 else 0

    # ── Información general ────────────────────────────────
    st.markdown("#### Información General")
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Contrato", contrato.get('numero', '—'), card_accent="accent-blue")
        kpi("Entidad Contratante", contrato.get('entidad', '—'))
    with c2:
        kpi("Contratista", contrato.get('contratista', '—'), card_accent="accent-green")
        kpi("Fecha de Inicio", fecha_inicio.strftime('%d/%m/%Y'))
    with c3:
        kpi("Plazo Total", f"{plazo} días",
            sub=f"+{adicion_dias} días de adición", card_accent="accent-orange")
        kpi("Localidades",
            "Mártires · S.Cristóbal · R.Uribe<br>Santafé · A.Nariño",
            accent="kpi-info")

    st.markdown(f"""
    <div class="kpi-card accent-blue">
        <div class="kpi-label">Objeto del Contrato</div>
        <div style="color:var(--text-secondary);font-size:0.94rem;line-height:1.55;">
            {contrato.get('objeto', '—')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    # ── Plazo ──────────────────────────────────────────────
    st.markdown("#### Ejecución del Plazo")
    ct1, ct2, ct3, ct4 = st.columns(4)
    t_a = "kpi-orange" if pct_tiempo > 70 else "kpi-green"
    t_c = "accent-orange" if pct_tiempo > 70 else "accent-green"
    with ct1: kpi("Días Transcurridos", str(dias_trans),
                  sub=f"{pct_tiempo}% del plazo", accent=t_a, card_accent=t_c)
    with ct2: kpi("Días Restantes", str(dias_rest))
    with ct3: kpi("Plazo Original", f"{contrato.get('plazo_dias', '—')} días")
    with ct4: kpi("Adiciones de Plazo", f"{adicion_dias} días",
                  accent="kpi-orange" if adicion_dias > 0 else "",
                  card_accent="accent-orange" if adicion_dias > 0 else "")

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

    # ── Financiero ─────────────────────────────────────────
    st.markdown("#### Ejecución Financiera")
    cf1, cf2, cf3, cf4 = st.columns(4)
    e_a = "kpi-red" if pct_ejec < pct_tiempo - 15 else (
        "kpi-green" if pct_ejec >= 80 else "kpi-orange"
    )
    e_c = "accent-red" if pct_ejec < pct_tiempo - 15 else (
        "accent-green" if pct_ejec >= 80 else "accent-orange"
    )
    with cf1: kpi("Valor Contrato", f"${val_act:,.0f}", sub="Actualizado",
                  accent="kpi-blue", card_accent="accent-blue")
    with cf2: kpi("Valor Ejecutado", f"${val_ejec:,.0f}",
                  sub=f"{pct_ejec}% del contrato", accent=e_a, card_accent=e_c)
    with cf3: kpi("Anticipos Desembolsados", f"${val_ant:,.0f}",
                  sub=f"{contrato.get('anticipos_total', 0)} anticipo(s)",
                  card_accent="accent-purple")
    with cf4: kpi("Amortizado", f"${val_amort:,.0f}",
                  sub=f"{pct_amort}% del anticipo",
                  accent="kpi-green" if pct_amort > 50 else "kpi-orange",
                  card_accent="accent-green" if pct_amort > 50 else "accent-orange")

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        fig_fin = go.Figure()
        for name, col_, val, color in [
            ('Ejecutado',   'Financiero', pct_ejec,       '#1a56db'),
            ('Pendiente',   'Financiero', 100 - pct_ejec, '#dde2eb'),
            ('Tiempo',      'Tiempo',     pct_tiempo,     '#0d7a4e'),
            ('Tiempo rest.','Tiempo',     100-pct_tiempo, '#dde2eb'),
        ]:
            fig_fin.add_trace(go.Bar(
                name=name, x=[col_], y=[val], marker_color=color,
            ))
        fig_fin.update_layout(
            barmode='stack', height=240,
            margin=dict(l=0, r=0, t=24, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation='h', y=-0.15, font_size=10),
            yaxis=dict(range=[0, 100], ticksuffix='%'),
            font=dict(family='IBM Plex Sans'),
            title=dict(text='Ejecución Financiera vs Tiempo (%)', font=dict(size=11)),
        )
        st.plotly_chart(fig_fin, use_container_width=True,
                        config={'displayModeBar': False})

    with col_g2:
        fig_ant = go.Figure(go.Pie(
            values=[val_amort, max(val_ant - val_amort, 0)],
            labels=['Amortizado', 'Pendiente'],
            hole=0.65,
            marker_colors=['#6d28d9', '#dde2eb'],
            textinfo='none',
        ))
        fig_ant.add_annotation(
            text=f"{pct_amort}%<br><span style='font-size:10px'>amortizado</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
            font=dict(family='IBM Plex Mono'),
        )
        fig_ant.update_layout(
            height=240, margin=dict(l=0, r=0, t=24, b=0),
            paper_bgcolor='rgba(0,0,0,0)', showlegend=False,
            title=dict(text='Amortización de Anticipos', font=dict(size=11)),
        )
        st.plotly_chart(fig_ant, use_container_width=True,
                        config={'displayModeBar': False})
