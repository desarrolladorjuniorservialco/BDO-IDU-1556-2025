"""
pages/estado_actual.py — Página: Estado Actual del Contrato
Identificación completa, KPIs de plazo y financieros, barra de tiempo,
tablas de seguimiento de prórrogas y adiciones.

Columnas reales de la tabla `contratos`:
  id, nombre, contratista, intrventoria (typo del Excel),
  supervisor_idu, fecha_inicio, fecha_fin, valor_contrato, valor_actual,
  prorrogas (contador), plazo_actual (fecha), adiciones (contador)
"""

import math
from datetime import datetime, date

import pandas as pd
import streamlit as st

from database import load_contrato, load_prorrogas, load_adiciones
from ui import kpi, section_badge, safe_float


def _fmt_cop(val) -> str:
    """Ajuste de escala monetaria para Colombia (mil MM = 10^9)."""
    v = safe_float(val)
    if v is None:
        return "—"
    
    abs_v = abs(v)
    
    # Billones reales (10^12)
    if abs_v >= 1_000_000_000_000:
        return f"${v / 1_000_000_000_000:.2f} Billones"
    # Mil millones (10^9) - Antes marcado como "B"
    if abs_v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f} milM"
    # Millones (10^6)
    if abs_v >= 1_000_000:
        return f"${v / 1_000_000:.1f} M"
        
    return f"${v:,.0f}"


def _fmt_date(val, fmt: str = '%d/%m/%Y') -> str:
    if not val:
        return "—"
    try:
        return datetime.strptime(str(val)[:10], '%Y-%m-%d').strftime(fmt)
    except Exception:
        return str(val)[:10]


def _timeline_html(pct: float, dias_trans: int, dias_rest: int,
                    fecha_ini: str, fecha_fin: str) -> str:
    """Renderiza la barra de ejecución del plazo en HTML puro."""
    p = max(min(pct, 100.0), 0.0)
    if p > 85:
        color = "#ED1C24"   # Rojo Bogotá — retraso/alerta
    elif p > 60:
        color = "#FFC425"   # Amarillo Estelar — en proceso
    else:
        color = "#198754"   # Verde — cumplido

    # Evitar desbordamiento de texto en barras muy cortas
    bar_text = f"{p:.1f}% transcurrido" if p >= 20 else f"{p:.1f}%"
    width_pct = f"{p:.1f}"

    return f"""
    <div class="timeline-container">
        <div class="timeline-label-row">
            <span class="timeline-label">Ejecución del plazo vigente</span>
            <span class="timeline-pct" style="color:{color};">{p:.1f}%</span>
        </div>
        <div class="timeline-bar-wrap">
            <div class="timeline-bar-fill"
                 style="width:{width_pct}%; background:{color};">
                <span class="timeline-bar-text">{bar_text}</span>
            </div>
        </div>
        <div class="timeline-dates">
            <span class="timeline-date-item">Inicio: {fecha_ini}</span>
            <span class="timeline-date-item"
                  style="color:{color}; font-weight:700;">
                {dias_trans} días transcurridos · {dias_rest} restantes
            </span>
            <span class="timeline-date-item">Fin vigente: {fecha_fin}</span>
        </div>
    </div>
    """


def page_estado_actual() -> None:
    section_badge("Estado Actual del Contrato", "blue")

    contrato = load_contrato()
    df_pro   = load_prorrogas()
    df_adi   = load_adiciones()

    if not contrato:
        st.info("Sin datos de contrato en la tabla 'contratos'. "
                "Verifica la sincronización del Excel.")
        return

    # ── Cálculos de tiempo ─────────────────────────────────
    fi_str  = str(contrato.get('fecha_inicio')  or '2025-01-01')[:10]
    ff_str  = str(contrato.get('fecha_fin')     or '2028-01-01')[:10]
    pa_str  = str(contrato.get('plazo_actual')  or ff_str)[:10]

    fecha_inicio   = datetime.strptime(fi_str,  '%Y-%m-%d').date()
    fecha_fin_orig = datetime.strptime(ff_str,  '%Y-%m-%d').date()
    fecha_fin_act  = datetime.strptime(pa_str,  '%Y-%m-%d').date()

    hoy         = date.today()
    dias_trans  = (hoy - fecha_inicio).days
    plazo_orig  = (fecha_fin_orig - fecha_inicio).days
    plazo_total = max((fecha_fin_act - fecha_inicio).days, 1)
    dias_rest   = max((fecha_fin_act - hoy).days, 0)
    pct_tiempo  = round(min(dias_trans / plazo_total * 100, 100), 1)

    val_ini = safe_float(contrato.get('valor_contrato')) or 0
    val_act = safe_float(contrato.get('valor_actual'))   or val_ini
    n_pro   = int(contrato.get('prorrogas')  or 0)
    n_adi   = int(contrato.get('adiciones')  or 0)

    # ── Header de identificación ───────────────────────────
    st.markdown(
        f"""
        <div class="contract-header">
            <div class="contract-id">Contrato de Obra</div>
            <div class="contract-name">{contrato.get('nombre', 'Contrato IDU-1556-2025')}</div>
            <div class="contract-meta-grid">
                <div class="contract-meta-item">
                    <div class="contract-meta-label">N.° Contrato</div>
                    <div class="contract-meta-value">{contrato.get('id', '—')}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Contratista</div>
                    <div class="contract-meta-value">{contrato.get('contratista', '—')}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Interventoría</div>
                    <div class="contract-meta-value">{contrato.get('intrventoria', '—')}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Supervisor IDU</div>
                    <div class="contract-meta-value">{contrato.get('supervisor_idu', '—')}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Fecha Inicio</div>
                    <div class="contract-meta-value">{_fmt_date(fi_str)}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Fecha Fin Original</div>
                    <div class="contract-meta-value">{_fmt_date(ff_str)}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Fecha Fin Vigente</div>
                    <div class="contract-meta-value">{_fmt_date(pa_str)}</div>
                </div>
                <div class="contract-meta-item">
                    <div class="contract-meta-label">Valor Contrato</div>
                    <div class="contract-meta-value">{_fmt_cop(val_ini)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Barra de tiempo ────────────────────────────────────
    st.markdown(
        _timeline_html(
            pct_tiempo, dias_trans, dias_rest,
            fecha_inicio.strftime('%d/%m/%Y'),
            fecha_fin_act.strftime('%d/%m/%Y'),
        ),
        unsafe_allow_html=True,
    )

    # ── KPIs de plazo ──────────────────────────────────────
    ct1, ct2, ct3, ct4 = st.columns(4)
    t_a = ("kpi-red"    if pct_tiempo > 85 else
           "kpi-orange" if pct_tiempo > 60 else "kpi-green")  # naranja=amarillo IDU
    t_c = ("accent-red"    if pct_tiempo > 85 else
           "accent-orange" if pct_tiempo > 60 else "accent-green")

    with ct1:
        kpi("Días Transcurridos", str(dias_trans),
            sub=f"{pct_tiempo}% del plazo vigente", accent=t_a, card_accent=t_c)
    with ct2:
        kpi("Días Restantes", str(dias_rest),
            sub=f"Fecha fin: {fecha_fin_act.strftime('%d/%m/%Y')}")
    with ct3:
        kpi("Plazo Original", f"{plazo_orig} días",
            sub=f"Hasta {fecha_fin_orig.strftime('%d/%m/%Y')}")
    with ct4:
        dias_ext = (fecha_fin_act - fecha_fin_orig).days
        kpi("Prórrogas Aplicadas", str(n_pro),
            sub=f"+{dias_ext} días totales" if n_pro else "Sin prórrogas",
            accent="kpi-orange" if n_pro else "",
            card_accent="accent-orange" if n_pro else "")

    st.divider()

    # ── KPIs financieros ───────────────────────────────────
    section_badge("Ejecución Financiera", "orange")

    diff = val_act - val_ini
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        kpi("Valor Inicial del Contrato", _fmt_cop(val_ini),
            sub=f"${val_ini:,.0f}", card_accent="accent-blue")
    with cf2:
        kpi("Valor Actualizado", _fmt_cop(val_act),
            sub=f"Δ {_fmt_cop(diff)} · {n_adi} adición(es)",
            accent="kpi-orange" if diff > 0 else ("kpi-red" if diff < 0 else ""),
            card_accent="accent-orange" if diff != 0 else "")
    with cf3:
        kpi("Adiciones Presupuestales", str(n_adi),
            sub=f"Valor actualizado: {_fmt_cop(val_act)}",
            card_accent="accent-green")

    st.divider()

    # ── Tabla de prórrogas ─────────────────────────────────
    section_badge("Seguimiento de Prórrogas", "orange")

    if df_pro.empty:
        st.info("Sin prórrogas registradas para este contrato.")
    else:
        # Columnas disponibles en contratos_prorrogas
        cols_pro = [c for c in [
            'numero', 'plazo_dias', 'fecha_fin', 'fecha_firma',
            'acta', 'objeto', 'observaciones',
        ] if c in df_pro.columns]

        col_cfg = {
            'numero':         st.column_config.NumberColumn('No.',               format="%d"),
            'plazo_dias':     st.column_config.NumberColumn('Días adicionados', format="%d"),
            'fecha_fin':      st.column_config.DateColumn('Nueva fecha fin',    format="DD/MM/YYYY"),
            'fecha_firma':    st.column_config.DateColumn('Fecha firma',        format="DD/MM/YYYY"),
            'acta':           st.column_config.TextColumn('Acta'),
            'objeto':         st.column_config.TextColumn('Objeto'),
            'observaciones':  st.column_config.TextColumn('Observaciones'),
        }

        st.markdown(
            f'<div class="tracking-table-wrap">'
            f'<div class="tracking-table-header">'
            f'<span class="tracking-table-title">Prórrogas de Plazo</span>'
            f'<span class="tracking-table-count">{len(df_pro)} registro(s)</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            df_pro[cols_pro],
            hide_index=True,
            width="stretch",
            column_config={k: v for k, v in col_cfg.items() if k in cols_pro},
        )

        # Resumen acumulado
        if 'plazo_dias' in df_pro.columns:
            total_ext = int(
                pd.to_numeric(df_pro['plazo_dias'], errors='coerce').fillna(0).sum()
            )
            st.caption(f"Total días adicionados por prórrogas: **{total_ext} días**")

    st.divider()

    # ── Tabla de adiciones ─────────────────────────────────
    section_badge("Seguimiento de Adiciones Presupuestales", "blue")

    if df_adi.empty:
        st.info("Sin adiciones presupuestales registradas para este contrato.")
    else:
        cols_adi = [c for c in [
            'numero', 'adicion', 'valor_actual', 'fecha_firma',
            'acta', 'objeto', 'observaciones',
        ] if c in df_adi.columns]

        col_cfg_adi = {
            'numero':         st.column_config.NumberColumn('No.',                format="%d"),
            'adicion':        st.column_config.NumberColumn('Adición ($)',         format="$%,.0f"),
            'valor_actual':   st.column_config.NumberColumn('Valor Acumulado ($)', format="$%,.0f"),
            'fecha_firma':    st.column_config.DateColumn('Fecha firma',           format="DD/MM/YYYY"),
            'acta':           st.column_config.TextColumn('Acta'),
            'objeto':         st.column_config.TextColumn('Objeto'),
            'observaciones':  st.column_config.TextColumn('Observaciones'),
        }

        st.markdown(
            f'<div class="tracking-table-wrap">'
            f'<div class="tracking-table-header">'
            f'<span class="tracking-table-title">Adiciones Presupuestales</span>'
            f'<span class="tracking-table-count">{len(df_adi)} registro(s)</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            df_adi[cols_adi],
            hide_index=True,
            width="stretch",
            column_config={k: v for k, v in col_cfg_adi.items() if k in cols_adi},
        )

        # Resumen acumulado de adiciones
        if 'adicion' in df_adi.columns:
            total_adi = pd.to_numeric(df_adi['adicion'], errors='coerce').fillna(0).sum()
            st.caption(f"Total adicionado al contrato: **{_fmt_cop(total_adi)}** "
                       f"(valor inicial {_fmt_cop(val_ini)} → actualizado {_fmt_cop(val_act)})")