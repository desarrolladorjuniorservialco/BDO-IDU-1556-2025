"""
pages/presupuesto.py — Página: Seguimiento Presupuestal
Presupuesto completo del contrato con valor ejecutado calculado
a partir de los registros de cantidades aprobados (cant_interventor × precio_unitario).

Fuentes:
  · presupuesto_bd          — ítems de presupuesto con precios unitarios
  · registros_cantidades    — mediciones de campo; solo se usan las APROBADAS

Lógica de ejecución:
  Para cada ítem_pago: ejecutado = Σ cant_interventor × valor_unitario
  Si no existe cant_interventor, se usa cantidad (nivel inspector).
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from database import (
    load_presupuesto, load_cantidades,
    load_tramos_bd, load_tramos_bd_historial,
    update_tramo_ejecutado,
)
from ui import kpi, section_badge, safe_float


def _fmt_cop(val) -> str:
    v = safe_float(val)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f} B"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f} M"
    return f"${v:,.0f}"


def _pct_bar(pct: float) -> str:
    """Mini barra de progreso HTML para ejecución."""
    p = max(min(float(pct or 0), 100.0), 0.0)
    cls = "danger" if p < 30 else ("warn" if p < 70 else "")
    return (
        f'<div class="presup-bar-wrap">'
        f'<div class="presup-bar-fill {cls}" style="width:{p:.1f}%;"></div>'
        f'</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.67rem;'
        f'color:var(--text-muted);margin-top:2px;">{p:.1f}%</div>'
    )


def _calcular_ejecutado(df_pres: pd.DataFrame, contrato_id: str) -> pd.DataFrame:
    """
    Calcula valor_ejecutado y pct_ejecutado para cada ítem del presupuesto
    a partir de las cantidades APROBADAS.
    """
    # Carga solo los registros aprobados
    df_apr = load_cantidades(contrato_id, estados=['APROBADO'])

    if df_apr.empty or 'item_pago' not in df_apr.columns:
        df_pres['cantidad_ejecutada'] = 0.0
        df_pres['valor_ejecutado']    = 0.0
        df_pres['pct_ejecutado']      = 0.0
        return df_pres

    # Columna de cantidad final (preferir interventor, caer a inspector)
    cant_col = 'cant_interventor' if 'cant_interventor' in df_apr.columns else 'cantidad'
    df_apr = df_apr.copy()
    df_apr['_cant'] = pd.to_numeric(df_apr[cant_col], errors='coerce').fillna(0)

    # Agrupar por item_pago
    ejec = (
        df_apr.groupby('item_pago', as_index=False)['_cant']
        .sum()
        .rename(columns={'_cant': 'cantidad_ejecutada'})
    )

    # Unir con presupuesto
    clave = 'item_pago'
    if clave not in df_pres.columns:
        df_pres['cantidad_ejecutada'] = 0.0
        df_pres['valor_ejecutado']    = 0.0
        df_pres['pct_ejecutado']      = 0.0
        return df_pres

    df_pres = df_pres.merge(ejec, on=clave, how='left')
    df_pres['cantidad_ejecutada'] = df_pres['cantidad_ejecutada'].fillna(0.0)

    # Calcular valor ejecutado
    vu_col = 'valor_unitario'
    if vu_col in df_pres.columns:
        df_pres['_vu'] = pd.to_numeric(df_pres[vu_col], errors='coerce').fillna(0)
        df_pres['valor_ejecutado'] = df_pres['cantidad_ejecutada'] * df_pres['_vu']
        df_pres.drop(columns=['_vu'], inplace=True)
    else:
        df_pres['valor_ejecutado'] = 0.0

    # Porcentaje de ejecución
    vt_col = 'valor_total'
    if vt_col in df_pres.columns:
        df_pres['_vt'] = pd.to_numeric(df_pres[vt_col], errors='coerce').fillna(0)
        df_pres['pct_ejecutado'] = df_pres.apply(
            lambda r: round(r['valor_ejecutado'] / r['_vt'] * 100, 1)
            if r['_vt'] > 0 else 0.0,
            axis=1,
        )
        df_pres.drop(columns=['_vt'], inplace=True)
    else:
        df_pres['pct_ejecutado'] = 0.0

    return df_pres


def page_presupuesto(perfil: dict) -> None:
    section_badge("Seguimiento Presupuestal", "orange")
    st.markdown("### Presupuesto del Contrato IDU-1556-2025")

    cid    = perfil['contrato_id']
    df_raw = load_presupuesto(cid)

    if df_raw.empty:
        st.info("Sin datos de presupuesto. Verifica la tabla 'presupuesto_bd' en Supabase.")
        return

    # Normalizar typos de columna de componente (varios nombres posibles en la BD)
    for _old in ('compenente', 'Componente', 'COMPONENTE', 'capitulo', 'Capitulo'):
        if _old in df_raw.columns and 'componente' not in df_raw.columns:
            df_raw = df_raw.rename(columns={_old: 'componente'})
            break

    # Normalizar columna de cantidad programada (cantidad_ppto -> cantidad_contrato)
    if 'cantidad_contrato' not in df_raw.columns:
        for _old in ('cantidad_ppto', 'cantidad_presupuesto', 'cant_contrato',
                     'Cantidad', 'cantidad'):
            if _old in df_raw.columns:
                df_raw = df_raw.rename(columns={_old: 'cantidad_contrato'})
                break

    # Normalizar unidad (unidad -> und si falta)
    if 'und' not in df_raw.columns and 'unidad' in df_raw.columns:
        df_raw = df_raw.rename(columns={'unidad': 'und'})

    # Calcular ejecutado a partir de cantidades aprobadas
    with st.spinner("Calculando ejecución presupuestal…"):
        df = _calcular_ejecutado(df_raw.copy(), cid)

    # ── Formulario de filtros ──────────────────────────────
    import re as _re

    # Valores únicos de componente (desde df calculado, no df_raw)
    comps_opts = []
    if 'componente' in df.columns:
        comps_opts = sorted(df['componente'].dropna().astype(str)
                            .str.strip().replace('', pd.NA).dropna().unique().tolist())

    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    with st.form("form_presupuesto"):
        ff1, ff2 = st.columns(2)
        with ff1:
            comp_f = st.multiselect(
                "Componente",
                comps_opts,
                key="ps_comp",
                help="Filtra por componente del presupuesto",
            )
        with ff2:
            buscar = st.text_input("Buscar ítem / descripción", key="ps_bus")
        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    df_filt = df.copy()
    if comp_f:
        df_filt = df_filt[df_filt['componente'].astype(str).str.strip().isin(comp_f)]
    if buscar.strip() and not df_filt.empty:
        b = _re.escape(buscar.strip())
        mask = pd.Series(False, index=df_filt.index)
        for col in ['item_pago', 'descripcion', 'und']:
            if col in df_filt.columns:
                mask |= df_filt[col].astype(str).str.contains(b, case=False, na=False)
        df_filt = df_filt[mask]

    if not df_filt.empty:
        _csv_cols_ps = [c for c in [
            'componente', 'item_pago', 'descripcion', 'und',
            'cantidad_contrato', 'valor_unitario', 'valor_total',
            'cantidad_ejecutada', 'valor_ejecutado', 'pct_ejecutado',
        ] if c in df_filt.columns]
        st.download_button(
            "Exportar CSV",
            data=df_filt[_csv_cols_ps].to_csv(index=False).encode('utf-8'),
            file_name="Presupuesto_IDU-1556-2025.csv",
            mime="text/csv",
        )

    # ── KPIs financieros ───────────────────────────────────
    if 'valor_total' in df_filt.columns:
        total_c = df_filt['valor_total'].apply(safe_float).sum()
        total_e = df_filt['valor_ejecutado'].apply(safe_float).sum() if 'valor_ejecutado' in df_filt.columns else 0
        total_p = max(total_c - total_e, 0)
        pct_e   = round(total_e / total_c * 100, 1) if total_c > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi("Valor Total Contrato", _fmt_cop(total_c),
                sub=f"${total_c:,.0f}", card_accent="accent-blue")
        with k2:
            kpi("Valor Ejecutado", _fmt_cop(total_e),
                sub=f"{pct_e}% del contrato",
                accent="kpi-green" if pct_e >= 70 else ("kpi-orange" if pct_e >= 40 else "kpi-red"),
                card_accent="accent-green" if pct_e >= 70 else "accent-orange")
        with k3:
            kpi("Valor Pendiente", _fmt_cop(total_p),
                sub=f"{100 - pct_e:.1f}% por ejecutar",
                card_accent="accent-red" if pct_e < 30 else "")
        with k4:
            n_items_apr = len(df_filt[df_filt['pct_ejecutado'] > 0]) if 'pct_ejecutado' in df_filt.columns else 0
            kpi("Ítems con ejecución", str(n_items_apr),
                sub=f"de {len(df_filt)} ítems totales",
                card_accent="accent-teal")

        # Barra de ejecución global
        st.markdown(
            f'<div class="timeline-container">'
            f'<div class="timeline-label-row">'
            f'<span class="timeline-label">Ejecución global del presupuesto</span>'
            f'<span class="timeline-pct">{pct_e}%</span>'
            f'</div>'
            f'<div class="timeline-bar-wrap">'
            f'<div class="timeline-bar-fill" '
            f'style="width:{min(pct_e,100):.1f}%; background:{"#6D8E2D" if pct_e>=70 else "#FD7E14" if pct_e>=40 else "#ED1C24"};">'
            f'<span class="timeline-bar-text">{pct_e}%</span>'
            f'</div></div>'
            f'<div class="timeline-dates">'
            f'<span class="timeline-date-item">Ejecutado: {_fmt_cop(total_e)}</span>'
            f'<span class="timeline-date-item">Pendiente: {_fmt_cop(total_p)}</span>'
            f'<span class="timeline-date-item">Total: {_fmt_cop(total_c)}</span>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        st.divider()

    # ── Gráfica por componente ─────────────────────────────
    if 'componente' in df_filt.columns and 'valor_total' in df_filt.columns:
        agg_data: dict = {'valor_total': 'sum'}
        if 'valor_ejecutado' in df_filt.columns:
            agg_data['valor_ejecutado'] = 'sum'

        df_grp = df_filt.groupby('componente').agg(
            **{k: pd.NamedAgg(column=k, aggfunc='sum') for k in agg_data}
        ).reset_index()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Presupuestado',
            x=df_grp['componente'],
            y=df_grp['valor_total'],
            marker_color='#002D57',
        ))
        if 'valor_ejecutado' in df_grp.columns:
            fig.add_trace(go.Bar(
                name='Ejecutado',
                x=df_grp['componente'],
                y=df_grp['valor_ejecutado'],
                marker_color='#6D8E2D',
            ))
        fig.update_layout(
            barmode='group',
            height=320,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='IBM Plex Sans'),
            legend=dict(orientation='h', y=1.12, font=dict(size=11)),
            yaxis=dict(
                title='Valor ($)',
                gridcolor='rgba(150,150,150,0.15)',
            ),
            xaxis=dict(tickfont=dict(size=10)),
        )
        st.plotly_chart(fig, width="stretch",
                        config={'displayModeBar': False})

    st.divider()

    # ── Tabla presupuestal completa ────────────────────────
    cols_show = [c for c in [
        'componente', 'item_pago', 'descripcion', 'und',
        'cantidad_contrato', 'valor_unitario', 'valor_total',
        'cantidad_ejecutada', 'valor_ejecutado', 'pct_ejecutado',
    ] if c in df_filt.columns]

    if cols_show:
        st.dataframe(
            df_filt[cols_show],
            hide_index=True,
            width="stretch",
            column_config={
                'componente':          st.column_config.TextColumn('Componente'),
                'item_pago':           st.column_config.TextColumn('Ítem Pago'),
                'descripcion':         st.column_config.TextColumn('Descripción'),
                'und':                 st.column_config.TextColumn('Und'),
                'cantidad_contrato':   st.column_config.NumberColumn(
                    'Cant. Programada',       format="%.3f"),
                'valor_unitario':      st.column_config.NumberColumn(
                    'V. Unitario ($)',        format="$%,.0f"),
                'valor_total':         st.column_config.NumberColumn(
                    'V. Programado ($)',      format="$%,.0f"),
                'cantidad_ejecutada':  st.column_config.NumberColumn(
                    'Cant. Ejecutada',        format="%.3f"),
                'valor_ejecutado':     st.column_config.NumberColumn(
                    'V. Ejecutado ($)',       format="$%,.0f"),
                'pct_ejecutado':       st.column_config.ProgressColumn(
                    'Ejecución (%)',          format="%.1f%%",
                    min_value=0, max_value=100),
            },
        )

    else:
        st.dataframe(df_filt, hide_index=True, width="stretch")

    # ══════════════════════════════════════════════════════════════
    # SECCIÓN: DASHBOARDS META FÍSICA (separado por tipo)
    # ══════════════════════════════════════════════════════════════
    import pytz as _pytz
    _bog = _pytz.timezone('America/Bogota')

    st.divider()

    df_tramos = load_tramos_bd(cid)

    if df_tramos.empty:
        st.info("Sin datos de meta física. Verifica la tabla 'tramos_bd' en Supabase.")
        return

    tramo_col = 'id_tramo'
    mf_col    = 'meta_fisica'

    # Fallback: derivar meta_fisica y und desde cicloruta_km / esp_publico_m2
    if mf_col not in df_tramos.columns or df_tramos[mf_col].isna().all():
        df_tramos = df_tramos.copy()
        df_tramos['meta_fisica'] = df_tramos.apply(
            lambda r: r.get('cicloruta_km') if r.get('infraestructura') == 'CI'
                      else r.get('esp_publico_m2'),
            axis=1,
        )
    if 'und' not in df_tramos.columns or df_tramos['und'].isna().all():
        df_tramos['und'] = df_tramos['infraestructura'].map(
            {'CI': 'km', 'EP': 'm²', 'MV': 'ml'}
        )

    df_tramos[mf_col] = pd.to_numeric(df_tramos[mf_col], errors='coerce').fillna(0)
    df_tramos['ejecutado'] = pd.to_numeric(
        df_tramos.get('ejecutado', 0), errors='coerce'
    ).fillna(0)
    df_tramos['pct_avance'] = df_tramos.apply(
        lambda r: round(r['ejecutado'] / r[mf_col] * 100, 1) if r[mf_col] > 0 else 0.0,
        axis=1,
    )
    df_tramos = df_tramos[df_tramos[mf_col] > 0].copy()

    if df_tramos.empty:
        st.warning("Ningún tramo tiene meta física registrada en 'tramos_bd'.")
        return

    # Catálogo de tipos: código → nombre, unidad, colores IDU
    # color_meta: Azul Institucional Bogotá (uniforme = autoridad/plan)
    # color_ejec: acento diferenciador por tipo dentro de la paleta IDU
    # card_accent: clase CSS del sistema de diseño para la barra lateral del KPI
    TIPOS = {
        'MV': {'nombre': 'Malla Vial',     'und': 'ml', 'color_meta': '#002D57', 'color_ejec': '#0076B0', 'card_accent': 'accent-teal'},
        'EP': {'nombre': 'Espacio Público', 'und': 'm²', 'color_meta': '#002D57', 'color_ejec': '#6D8E2D', 'card_accent': 'accent-green'},
        'CI': {'nombre': 'Ciclorruta',     'und': 'km', 'color_meta': '#002D57', 'color_ejec': '#E6BC00', 'card_accent': 'accent-blue'},
    }

    # ── Dashboard 1: Indicadores acumulados por tipo ───────────
    section_badge("Seguimiento de Avance Meta Física General", "blue")

    cols_tipo = st.columns(len(TIPOS), gap="medium")
    for col_ui, (codigo, info) in zip(cols_tipo, TIPOS.items()):
        df_t  = df_tramos[df_tramos['infraestructura'] == codigo]
        meta  = df_t[mf_col].sum()
        ejec  = df_t['ejecutado'].sum()
        pend  = max(meta - ejec, 0)
        pct   = round(ejec / meta * 100, 1) if meta > 0 else 0.0
        n_tr  = len(df_t)
        # Semáforo IDU: completado=#6D8E2D · atrasado=#FD7E14 · crítico=#ED1C24
        bar_color = '#6D8E2D' if pct >= 70 else '#FD7E14' if pct >= 40 else '#ED1C24'
        with col_ui:
            kpi(
                info['nombre'],
                f"{ejec:,.1f} / {meta:,.1f} {info['und']}",
                sub=f"{n_tr} tramo(s) · Pendiente: {pend:,.1f} {info['und']}",
                accent="kpi-green" if pct >= 70 else ("kpi-orange" if pct >= 40 else "kpi-red"),
                card_accent=info['card_accent'],
            )
            st.markdown(
                f'<div class="timeline-container" style="margin-top:6px;">'
                f'<div class="timeline-label-row">'
                f'<span class="timeline-label">Avance</span>'
                f'<span class="timeline-pct">{pct}%</span>'
                f'</div>'
                f'<div class="timeline-bar-wrap">'
                f'<div class="timeline-bar-fill" style="width:{min(pct,100):.1f}%;background:{bar_color};">'
                f'<span class="timeline-bar-text">{pct}%</span>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Dashboard 2: Detalle por tramo separado por tipo (tabs) ─
    section_badge("Seguimiento de Avance Meta Física por Tramo", "teal")

    tab_labels = [f"{info['nombre']}" for info in TIPOS.values()]
    tabs = st.tabs(tab_labels)

    # Tabla consolidada de avance (todos los tipos) para CSV global
    _csv_avance_frames = []

    for tab, (codigo, info) in zip(tabs, TIPOS.items()):
        df_t = df_tramos[df_tramos['infraestructura'] == codigo].copy()
        und  = info['und']

        with tab:
            if df_t.empty:
                st.info(f"Sin tramos registrados para {info['nombre']}.")
                continue

            col_ch, col_tb = st.columns([3, 2], gap="large")

            with col_ch:
                st.markdown(f"#### Avance por tramo — {info['nombre']}")
                _desc = df_t.get('tramo_descripcion', df_t[tramo_col]).fillna(df_t[tramo_col]).astype(str)
                _ids  = df_t[tramo_col].astype(str)
                _tip  = (_ids + '<br>' + _desc).tolist()
                fig_t = go.Figure()
                fig_t.add_trace(go.Bar(
                    name='Meta física',
                    x=df_t[tramo_col].astype(str),
                    y=df_t[mf_col],
                    marker_color=info['color_meta'],
                    customdata=_tip,
                    hovertemplate='<b>%{customdata}</b><br>Meta: %{y:,.2f} ' + und + '<extra></extra>',
                ))
                fig_t.add_trace(go.Bar(
                    name='Ejecutado',
                    x=df_t[tramo_col].astype(str),
                    y=df_t['ejecutado'],
                    marker_color=info['color_ejec'],
                    customdata=_tip,
                    hovertemplate='<b>%{customdata}</b><br>Ejecutado: %{y:,.2f} ' + und + '<extra></extra>',
                ))
                fig_t.update_layout(
                    barmode='group',
                    height=360,
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(family='IBM Plex Sans'),
                    legend=dict(orientation='h', y=1.12, font=dict(size=11)),
                    yaxis=dict(
                        title=f'Cantidad ({und})',
                        gridcolor='rgba(150,150,150,0.15)',
                    ),
                    xaxis=dict(tickfont=dict(size=10)),
                )
                st.plotly_chart(fig_t, width="stretch",
                                config={'displayModeBar': False})

            with col_tb:
                df_show = df_t[[tramo_col, mf_col, 'ejecutado', 'pct_avance']].copy()
                df_show.columns = [
                    'Tramo', f'Meta ({und})', f'Ejecutado ({und})', 'Avance (%)'
                ]
                st.dataframe(
                    df_show,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        'Tramo':               st.column_config.TextColumn('Tramo'),
                        f'Meta ({und})':       st.column_config.NumberColumn(
                            f'Meta ({und})',      format="%.2f"),
                        f'Ejecutado ({und})':  st.column_config.NumberColumn(
                            f'Ejecutado ({und})', format="%.2f"),
                        'Avance (%)':          st.column_config.ProgressColumn(
                            'Avance (%)', format="%.1f%%", min_value=0, max_value=100),
                    },
                )
                # CSV por tipo
                st.download_button(
                    f"Descargar CSV — {info['nombre']}",
                    data=df_show.to_csv(index=False).encode('utf-8'),
                    file_name=f"MetaFisica_{codigo}_IDU-1556-2025.csv",
                    mime="text/csv",
                    key=f"csv_mf_{codigo}",
                )

            # Acumular para CSV global
            df_csv_tipo = df_t[[tramo_col, mf_col, 'ejecutado', 'pct_avance']].copy()
            df_csv_tipo.insert(0, 'tipo', info['nombre'])
            df_csv_tipo.insert(0, 'und', und)
            _csv_avance_frames.append(df_csv_tipo)

    # CSV consolidado (todos los tipos)
    if _csv_avance_frames:
        df_csv_global = pd.concat(_csv_avance_frames, ignore_index=True)
        st.download_button(
            "Descargar CSV — Avance completo (todos los tipos)",
            data=df_csv_global.to_csv(index=False).encode('utf-8'),
            file_name="MetaFisica_TodosTipos_IDU-1556-2025.csv",
            mime="text/csv",
        )

    # ── Edición de ejecutado (solo rol obra) ───────────────────
    es_obra = perfil.get('rol') == 'obra'
    if es_obra:
        st.divider()
        section_badge("Registrar Avance de Meta Física", "orange")
        st.caption("Solo visible para el rol Obra. Los cambios quedan registrados en el historial de auditoría.")

        with st.expander("Actualizar ejecutado por tramo", expanded=False):
            with st.form("form_meta_fisica"):
                filas = []
                for codigo, info in TIPOS.items():
                    df_t = df_tramos[df_tramos['infraestructura'] == codigo]
                    if df_t.empty:
                        continue
                    st.markdown(
                        f'<div class="mf-tipo-header">{info["nombre"]} · {info["und"]}</div>',
                        unsafe_allow_html=True,
                    )
                    for _, row in df_t.iterrows():
                        tid   = row[tramo_col]
                        desc  = str(row.get('tramo_descripcion') or '')
                        label = f"[{tid}] {desc}".strip() if desc else f"[{tid}]"
                        meta  = float(row[mf_col])
                        ejec  = float(row['ejecutado'])
                        nuevo = st.number_input(
                            f"{label} — meta: {meta:,.2f} {info['und']}",
                            min_value=0.0,
                            max_value=float(meta) if meta > 0 else 1e9,
                            value=ejec,
                            step=0.01,
                            format="%.2f",
                            key=f"mf_ejec_{tid}",
                        )
                        filas.append((tid, ejec, nuevo))
                    st.markdown("---")

                guardar = st.form_submit_button("Guardar cambios", type="primary",
                                                width="stretch")

            if guardar:
                token     = st.session_state.get('_access_token', '')
                errores   = []
                guardados = 0
                for tid, ant, nuevo in filas:
                    if abs(nuevo - ant) < 1e-6:
                        continue
                    ok = update_tramo_ejecutado(tid, ant, nuevo, perfil, token)
                    if ok:
                        guardados += 1
                    else:
                        errores.append(tid)
                if guardados:
                    st.success(f"{guardados} tramo(s) actualizado(s) correctamente.")
                if errores:
                    st.error(f"Error al guardar: {', '.join(errores)}")
                if not guardados and not errores:
                    st.info("Sin cambios que guardar.")

    # ── Historial de modificaciones ────────────────────────────
    st.divider()
    section_badge("Historial de Modificaciones — Meta Física", "gray")

    df_hist = load_tramos_bd_historial()
    if df_hist.empty:
        st.info("Sin modificaciones registradas aún.")
    else:
        # Convertir timestamp a UTC-5
        if 'modificado_en' in df_hist.columns:
            df_hist['Fecha (UTC-5)'] = (
                pd.to_datetime(df_hist['modificado_en'], utc=True)
                .dt.tz_convert(_bog)
                .dt.strftime('%Y-%m-%d %H:%M:%S')
            )

        # Enriquecer con nombre del tipo si se puede cruzar con df_tramos
        if 'id_tramo' in df_hist.columns and 'infraestructura' in df_tramos.columns:
            tipo_map = (
                df_tramos[['id_tramo', 'infraestructura']]
                .drop_duplicates('id_tramo')
                .set_index('id_tramo')['infraestructura']
                .map({k: v['nombre'] for k, v in TIPOS.items()})
            )
            df_hist['Tipo'] = df_hist['id_tramo'].map(tipo_map)

        cols_hist = ['Fecha (UTC-5)', 'Tipo', 'id_tramo', 'modificado_nombre',
                     'ejecutado_ant', 'ejecutado_nuevo']
        cols_hist = [c for c in cols_hist if c in df_hist.columns]

        st.download_button(
            "Descargar CSV — Historial de modificaciones",
            data=df_hist[cols_hist].to_csv(index=False).encode('utf-8'),
            file_name="Historial_MetaFisica_IDU-1556-2025.csv",
            mime="text/csv",
        )

        st.dataframe(
            df_hist[cols_hist],
            hide_index=True,
            width="stretch",
            column_config={
                'Fecha (UTC-5)':      st.column_config.TextColumn('Fecha (UTC-5)'),
                'Tipo':               st.column_config.TextColumn('Tipo'),
                'id_tramo':           st.column_config.TextColumn('Tramo'),
                'modificado_nombre':  st.column_config.TextColumn('Usuario'),
                'ejecutado_ant':      st.column_config.NumberColumn('Anterior', format="%.2f"),
                'ejecutado_nuevo':    st.column_config.NumberColumn('Nuevo',    format="%.2f"),
            },
        )
