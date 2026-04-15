"""
pages/reporte_cantidades.py — Página: Reporte de Cantidades de Obra
Visualización completa, aprobación y exportación de registros_cantidades.

Características:
  · Filtros: fechas, estado, tramo, CIV, capítulo/componente, búsqueda libre
  · Indicadores acumulados (total, aprobados, suma de cantidades, valor estimado)
  · Vista por registro con: todos los campos, registro fotográfico
  · Panel de aprobación/devolución escalonada según rol (flujo APROBACION_CONFIG)
  · Trazabilidad: observaciones de cada nivel quedan en la BD
  · Exportación CSV

SEGURIDAD:
  · re.escape() previene ReDoS en búsqueda libre.
  · Escrituras via get_user_client() → RLS activo.
  · max_chars en text_area limita payloads de observación.
"""

import logging
import re
from datetime import datetime, date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from config import APROBACION_CONFIG
from database import (
    load_cantidades, load_fotos_cantidades,
    get_user_client, clear_cache,
)
from ui import badge, kpi, section_badge, safe_float

_log = logging.getLogger(__name__)


# ── Helpers de formato ─────────────────────────────────────────
def _fmt_cop(val) -> str:
    v = safe_float(val)
    if v is None:
        return "—"
    if abs(v) >= 1_000_000_000:
        return f"${v / 1_000_000_000:.2f} B"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:.1f} M"
    return f"${v:,.0f}"


def _pill(label: str, valor, color: str = "") -> str:
    if valor is None or str(valor).strip() in ('', 'nan', 'None', '—'):
        return ""
    cls = f"info-pill {color}" if color else "info-pill"
    return f'<span class="{cls}">{label}: {valor}</span>'


def _historial_aprobacion_html(reg: pd.Series) -> str:
    """Genera HTML con el historial de aprobación del registro."""
    items = []

    # Residente
    if reg.get('aprobado_residente'):
        est = str(reg.get('estado_residente', '')).capitalize()
        fec = str(reg.get('fecha_residente', ''))[:10]
        obs = reg.get('obs_residente', '')
        items.append(f"""
        <div class="approval-history-item">
            <span class="approval-history-role">Residente · {est} · {fec}</span>
            <span style="font-size:0.78rem;">{reg['aprobado_residente']}</span>
            {f'<span style="color:var(--accent-orange);font-size:0.76rem;">↩ {obs}</span>' if obs else ''}
        </div>""")

    # Interventor
    if reg.get('aprobado_interventor'):
        est = str(reg.get('estado_interventor', '')).capitalize()
        fec = str(reg.get('fecha_interventor', ''))[:10]
        obs = reg.get('obs_interventor', '')
        items.append(f"""
        <div class="approval-history-item">
            <span class="approval-history-role">Interventor · {est} · {fec}</span>
            <span style="font-size:0.78rem;">{reg['aprobado_interventor']}</span>
            {f'<span style="color:var(--accent-orange);font-size:0.76rem;">↩ {obs}</span>' if obs else ''}
        </div>""")

    if not items:
        return ""
    return (
        '<div class="approval-history">'
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:0.62rem;'
        'text-transform:uppercase;letter-spacing:0.10em;color:var(--text-muted);'
        'margin-bottom:0.4rem;">Trazabilidad</div>'
        + "".join(items)
        + '</div>'
    )


def _panel_aprobacion(reg: pd.Series, perfil: dict,
                       campos: dict | None, estado_apr: str | None) -> None:
    """Panel de aprobación/devolución con trazabilidad completa."""
    est_actual = str(reg.get('estado', '')).upper()
    reg_id     = str(reg.get('id', ''))

    # Historial previo
    hist_html = _historial_aprobacion_html(reg)
    if hist_html:
        st.markdown(hist_html, unsafe_allow_html=True)

    if not campos:
        st.caption(f"Estado: {est_actual}")
        return

    st.markdown(
        '<div class="approval-panel-title">Validación de Cantidad</div>',
        unsafe_allow_html=True,
    )

    campo_cant = campos['campo_cant']
    campo_obs  = campos['campo_obs']
    cant_def   = (safe_float(reg.get(campo_cant)) or
                  safe_float(reg.get('cantidad')) or 0.0)

    cant_val = st.number_input(
        "Cantidad validada",
        value=float(cant_def),
        min_value=0.0,
        max_value=9_999_999.0,
        step=0.01,
        key=f"rc_cant_{reg_id}",
    )
    obs_val = st.text_area(
        "Observación de revisión",
        key=f"rc_obs_{reg_id}",
        height=70,
        max_chars=1000,
        placeholder="Opcional para aprobar · Obligatoria para devolver",
        value=str(reg.get(campo_obs, '') or ''),
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Aprobar", key=f"rc_apr_{reg_id}",
                     use_container_width=True, type="primary"):
            token = st.session_state.get('_access_token', '')
            if not token:
                st.error("Sesión expirada. Recarga la página e inicia sesión de nuevo.")
            else:
                try:
                    sb  = get_user_client(token)
                    upd = {
                        'estado':               estado_apr,
                        campo_cant:             cant_val,
                        campos['campo_estado']: 'aprobado',
                        campos['campo_apr']:    perfil['id'],
                        campos['campo_fecha']:  datetime.now().isoformat(),
                    }
                    if obs_val.strip():
                        upd[campo_obs] = obs_val.strip()
                    resp = sb.table('registros_cantidades').update(upd).eq('id', reg_id).execute()
                    if not resp.data:
                        st.error(
                            "La actualización no afectó ningún registro. "
                            "Verifica que tengas permiso para aprobar este registro."
                        )
                    else:
                        clear_cache()
                        st.success("Registro aprobado")
                        st.rerun()
                except Exception as exc:
                    _log.exception("Error al aprobar registro id=%s", reg_id)
                    st.error(f"No fue posible aprobar: {exc}")

    with b2:
        if st.button("Devolver", key=f"rc_dev_{reg_id}",
                     use_container_width=True):
            if not obs_val.strip():
                st.error("Escribe una observación para devolver")
            else:
                token = st.session_state.get('_access_token', '')
                if not token:
                    st.error("Sesión expirada. Recarga la página e inicia sesión de nuevo.")
                else:
                    try:
                        sb = get_user_client(token)
                        resp = sb.table('registros_cantidades').update({
                            'estado':               'DEVUELTO',
                            campos['campo_estado']: 'devuelto',
                            campo_obs:              obs_val.strip(),
                            campos['campo_fecha']:  datetime.now().isoformat(),
                        }).eq('id', reg_id).execute()
                        if not resp.data:
                            st.error(
                                "La actualización no afectó ningún registro. "
                                "Verifica que tengas permiso para devolver este registro."
                            )
                        else:
                            clear_cache()
                            st.warning("Registro devuelto")
                            st.rerun()
                    except Exception as exc:
                        _log.exception("Error al devolver registro id=%s", reg_id)
                        st.error(f"No fue posible devolver: {exc}")


def page_reporte_cantidades(perfil: dict) -> None:
    rol = perfil['rol']
    section_badge("Reporte de Cantidades de Obra", "blue")
    st.markdown("### Medición y Validación de Cantidades")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # ── Filtros ───────────────────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    with st.form("form_rc"):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            fi = st.date_input("Desde",
                               value=date.today() - timedelta(days=30),
                               key="rc_fi")
        with fc2:
            ff = st.date_input("Hasta", value=date.today(), key="rc_ff")
        with fc3:
            opts = (["Todos"] + estados_vis) if estados_vis else (
                ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
            )
            estado_f = st.selectbox("Estado", opts, key="rc_est")
        with fc4:
            buscar = st.text_input(
                "Buscar: folio / CIV / actividad / tramo",
                key="rc_bus",
            )
        fa1, fa2, fa3, fa4, fa5 = st.columns(5)
        with fa1:
            tramo_f = st.text_input("Tramo (ID)", key="rc_tramo")
        with fa2:
            civ_f   = st.text_input("CIV", key="rc_civ")
        with fa3:
            item_f  = st.text_input("Ítem de pago", key="rc_item")
        with fa4:
            comp_f  = st.text_input("Componente / Cap.", key="rc_comp")
        with fa5:
            user_f  = st.text_input("Inspector / Usuario", key="rc_user")
        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not aplicar and 'rc_loaded' not in st.session_state:
        st.info("Define los filtros y presiona **Aplicar filtros** para cargar.")
        return
    st.session_state['rc_loaded'] = True

    # ── Carga de datos ─────────────────────────────────────
    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_cantidades(
        estados=estados_q,
        fecha_ini=fi.isoformat(),
        fecha_fin=ff.isoformat(),
    )

    # Búsqueda libre
    if buscar.strip() and not df.empty:
        b = re.escape(buscar.strip())
        mask = pd.Series(False, index=df.index)
        for col in ['folio', 'civ', 'tipo_actividad', 'id_tramo',
                    'item_pago', 'item_descripcion', 'usuario_qfield']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(b, case=False, na=False)
        df = df[mask]

    # Filtros avanzados
    def _text_filt(df, col, val):
        if val.strip() and not df.empty and col in df.columns:
            return df[df[col].astype(str).str.contains(
                re.escape(val.strip()), case=False, na=False
            )]
        return df

    df = _text_filt(df, 'id_tramo',        tramo_f)
    df = _text_filt(df, 'civ',             civ_f)
    df = _text_filt(df, 'item_pago',       item_f)
    df = _text_filt(df, 'codigo_elemento', comp_f)
    df = _text_filt(df, 'usuario_qfield',  user_f)

    if df.empty:
        st.info("No hay registros para los filtros seleccionados.")
        return

    # ── Indicadores acumulados ─────────────────────────────
    n_total   = len(df)
    n_apr     = len(df[df['estado'] == 'APROBADO'])  if 'estado' in df else 0
    n_rev     = len(df[df['estado'] == 'REVISADO'])  if 'estado' in df else 0
    n_bor     = len(df[df['estado'] == 'BORRADOR'])  if 'estado' in df else 0
    n_dev     = len(df[df['estado'] == 'DEVUELTO'])  if 'estado' in df else 0

    cant_col    = 'cant_interventor' if 'cant_interventor' in df.columns else 'cantidad'
    suma_cant   = df[cant_col].apply(safe_float).sum() if cant_col in df.columns else 0
    suma_cant_i = df['cantidad'].apply(safe_float).sum() if 'cantidad' in df.columns else 0

    ki1, ki2, ki3, ki4, ki5 = st.columns(5)
    with ki1:
        kpi("Total registros", str(n_total), card_accent="accent-blue")
    with ki2:
        kpi("Aprobados",  str(n_apr),  accent="kpi-green",  card_accent="accent-green")
    with ki3:
        kpi("Revisados",  str(n_rev),  accent="kpi-blue",   card_accent="accent-blue")
    with ki4:
        kpi("Devueltos",  str(n_dev),
            accent="kpi-red" if n_dev else "",
            card_accent="accent-red" if n_dev else "")
    with ki5:
        kpi("Σ Cant. validada", f"{suma_cant:,.3f}",
            sub=f"Inspector: {suma_cant_i:,.3f}",
            card_accent="accent-teal")

    # Gráfica distribución por estado
    if 'estado' in df.columns:
        cnt = df['estado'].value_counts().reset_index()
        cnt.columns = ['Estado', 'Registros']
        fig_e = px.bar(
            cnt, x='Estado', y='Registros', color='Estado',
            color_discrete_map={
                'APROBADO': '#198754',   # Verde — cumplido
                'REVISADO': '#FFC425',   # Amarillo Estelar — en proceso
                'DEVUELTO': '#ED1C24',   # Rojo Bogotá — alerta
                'BORRADOR': '#B0BEC5',   # Gris Neutro — planeación
            },
            height=200,
        )
        fig_e.update_layout(
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            font=dict(family='Barlow'),
            xaxis=dict(title=''),
            yaxis=dict(title='Registros', gridcolor='rgba(150,150,150,0.2)'),
        )
        st.plotly_chart(fig_e, use_container_width=True,
                        config={'displayModeBar': False})

    st.divider()

    # ── Vista: tabla resumen vs detalle por registro ───────
    vista = st.radio("Vista", ["Detalle por registro", "Tabla resumen"],
                     horizontal=True, key="rc_vista")
    st.markdown(f"**{n_total} registro(s)**")

    if vista == "Tabla resumen":
        # ── Vista tabla ────────────────────────────────────
        cols_show = [c for c in [
            'folio', 'fecha_creacion', 'usuario_qfield', 'id_tramo', 'civ',
            'codigo_elemento', 'tipo_actividad', 'item_pago', 'item_descripcion',
            'cantidad', 'unidad', 'cant_residente', 'cant_interventor', 'estado',
        ] if c in df.columns]

        st.dataframe(
            df[cols_show],
            hide_index=True,
            use_container_width=True,
            column_config={
                'fecha_creacion':   st.column_config.DateColumn('Fecha',               format="DD/MM/YYYY"),
                'cantidad':         st.column_config.NumberColumn('Cant. Inspector',    format="%.3f"),
                'cant_residente':   st.column_config.NumberColumn('Cant. Residente',    format="%.3f"),
                'cant_interventor': st.column_config.NumberColumn('Cant. Interventor',  format="%.3f"),
                'estado':           st.column_config.TextColumn('Estado'),
            },
        )

        csv = df[cols_show].to_csv(index=False).encode('utf-8')
        st.download_button(
            "Exportar CSV",
            data=csv,
            file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    else:
        # ── Vista detalle por registro ─────────────────────
        # Carga en batch de fotos
        folios = tuple(df['folio'].dropna().tolist()) if 'folio' in df.columns else ()
        df_fot = load_fotos_cantidades(folios) if folios else pd.DataFrame()

        for _, reg in df.iterrows():
            folio       = str(reg.get('folio', '—'))
            est_actual  = str(reg.get('estado', ''))
            actividad   = str(reg.get('tipo_actividad', reg.get('item_descripcion', '—')))
            tramo       = str(reg.get('id_tramo', '—'))
            fecha_c     = str(reg.get('fecha_creacion', reg.get('fecha_inicio', '')))[:10]
            usuario     = str(reg.get('usuario_qfield', '—'))

            with st.expander(
                f"**{folio}** · {actividad[:60]} · {tramo}",
                expanded=False,
            ):
                # Fila de metadata
                st.markdown(
                    f'<div class="record-meta-row">'
                    f'{badge(est_actual)}'
                    f'<span class="info-pill">{fecha_c}</span>'
                    f'{_pill("Tramo", tramo, "blue")}'
                    f'{_pill("CIV", reg.get("civ"), "teal")}'
                    f'{_pill("PK", reg.get("pk") or reg.get("civ_pk"), "green")}'
                    f'{_pill("Ítem", reg.get("item_pago"), "orange")}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                col_info, col_apr = st.columns([2.2, 1])

                with col_info:
                    # Grilla de campos de info
                    st.markdown(
                        f'<div class="record-field-grid">'
                        f'<div><div class="record-field-label">Inspector / Usuario</div>'
                        f'<div class="record-field-value">{usuario}</div></div>'
                        f'<div><div class="record-field-label">Componente / Cap.</div>'
                        f'<div class="record-field-value">{reg.get("codigo_elemento", reg.get("componente", "—"))}</div></div>'
                        f'<div><div class="record-field-label">Ítem de pago</div>'
                        f'<div class="record-field-value">{reg.get("item_pago", "—")}</div></div>'
                        f'<div><div class="record-field-label">Actividad / Descripción</div>'
                        f'<div class="record-field-value">{actividad[:80]}</div></div>'
                        f'<div><div class="record-field-label">Cantidad Inspector</div>'
                        f'<div class="record-field-value">{safe_float(reg.get("cantidad")) or 0:.3f} {reg.get("unidad","")}</div></div>'
                        f'<div><div class="record-field-label">Cant. Residente</div>'
                        f'<div class="record-field-value">{safe_float(reg.get("cant_residente")) or "—"}</div></div>'
                        f'<div><div class="record-field-label">Cant. Interventor</div>'
                        f'<div class="record-field-value">{safe_float(reg.get("cant_interventor")) or "—"}</div></div>'
                        f'<div><div class="record-field-label">Unidad</div>'
                        f'<div class="record-field-value">{reg.get("unidad","—")}</div></div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Observaciones
                    if reg.get('observaciones'):
                        st.info(str(reg['observaciones']))
                    if reg.get('descripcion') and str(reg['descripcion']) != str(reg.get('observaciones', '')):
                        st.caption(str(reg['descripcion']))

                    # Observaciones de niveles previos (visibles para roles superiores)
                    if reg.get('obs_residente') and rol in ('interventor', 'supervisor', 'admin'):
                        st.warning(f"Obs. Residente: {reg['obs_residente']}")
                    if reg.get('obs_interventor') and rol in ('supervisor', 'admin'):
                        st.warning(f"Obs. Interventor: {reg['obs_interventor']}")

                    # Registro fotográfico
                    if not df_fot.empty and 'folio' in df_fot.columns:
                        fotos_r = df_fot[df_fot['folio'] == folio]
                        urls = fotos_r['foto_url'].dropna().tolist() if not fotos_r.empty else []
                        if urls:
                            st.markdown(
                                '<div style="font-family:\'JetBrains Mono\',monospace;'
                                'font-size:0.63rem;text-transform:uppercase;'
                                'letter-spacing:0.1em;color:var(--text-muted);'
                                'margin:0.6rem 0 0.35rem;">Registro fotográfico</div>',
                                unsafe_allow_html=True,
                            )
                            f_cols = st.columns(min(len(urls), 4))
                            for i, url in enumerate(urls[:4]):
                                with f_cols[i]:
                                    st.image(url, use_column_width=True)
                        else:
                            st.caption("Sin fotos registradas")

                with col_apr:
                    st.markdown(
                        '<div class="approval-panel">',
                        unsafe_allow_html=True,
                    )
                    _panel_aprobacion(reg, perfil, campos, estado_apr)
                    st.markdown('</div>', unsafe_allow_html=True)

        # ── Exportar CSV al final del detalle ─────────────
        st.divider()
        cols_csv = [c for c in [
            'folio', 'fecha_creacion', 'usuario_qfield', 'id_tramo', 'civ',
            'codigo_elemento', 'tipo_actividad', 'item_pago', 'item_descripcion',
            'cantidad', 'unidad', 'cant_residente', 'cant_interventor',
            'obs_residente', 'obs_interventor', 'estado',
        ] if c in df.columns]
        csv = df[cols_csv].to_csv(index=False).encode('utf-8')
        st.download_button(
            "Exportar CSV",
            data=csv,
            file_name=f"Cantidades_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
