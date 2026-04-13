"""
pages/_componentes_base.py — Panel base compartido para componentes transversales.
Importado por: componente_ambiental, componente_social, componente_pmt.

Características:
  · Filtros: fechas, estado, tramo, tipo_actividad, búsqueda libre
  · Indicadores acumulados por período
  · Vista detallada por registro con registro fotográfico
  · Panel de aprobación/devolución con trazabilidad (flujo APROBACION_CONFIG)

SEGURIDAD:
  - re.escape() previene ReDoS en filtros de texto.
  - max_chars en text_area limita payloads de observación.
  - Escrituras via get_user_client() → RLS activo.
"""

import logging
import re
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from config import APROBACION_CONFIG
from database import (
    load_componentes, load_fotos_componentes,
    get_user_client, clear_cache,
)
from ui import badge, kpi, safe_float

_log = logging.getLogger(__name__)


def _pill(label: str, valor, color: str = "") -> str:
    if valor is None or str(valor).strip() in ('', 'nan', 'None', '—'):
        return ""
    cls = f"info-pill {color}" if color else "info-pill"
    return f'<span class="{cls}">{label}: {valor}</span>'


def _historial_aprobacion_html(reg: pd.Series) -> str:
    """HTML del historial de aprobación del registro."""
    items = []
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


def _panel_aprobacion_comp(reg: pd.Series, perfil: dict,
                            campos: dict | None, estado_apr: str | None,
                            tabla: str) -> None:
    """Panel de aprobación/devolución con cantidad validada."""
    est_actual = str(reg.get('estado', '')).upper()
    reg_id     = str(reg.get('id', ''))

    hist_html = _historial_aprobacion_html(reg)
    if hist_html:
        st.markdown(hist_html, unsafe_allow_html=True)

    if not campos:
        st.caption(f"Estado: {est_actual}")
        return

    st.markdown(
        '<div class="approval-panel-title">Validación</div>',
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
        key=f"comp_cant_{reg_id}",
    )
    obs_val = st.text_area(
        "Observación",
        key=f"comp_obs_{reg_id}",
        height=70,
        max_chars=1000,
        placeholder="Opcional para aprobar · Obligatoria para devolver",
        value=str(reg.get(campo_obs, '') or ''),
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Aprobar", key=f"comp_apr_{reg_id}",
                     use_container_width=True, type="primary"):
            try:
                sb  = get_user_client(st.session_state.get('_access_token', ''))
                upd = {
                    'estado':               estado_apr,
                    campo_cant:             cant_val,
                    campos['campo_estado']: 'aprobado',
                    campos['campo_apr']:    perfil['id'],
                    campos['campo_fecha']:  datetime.now().isoformat(),
                }
                if obs_val.strip():
                    upd[campo_obs] = obs_val.strip()
                sb.table(tabla).update(upd).eq('id', reg_id).execute()
                clear_cache()
                st.success("Registro aprobado")
                st.rerun()
            except Exception:
                _log.exception("Error al aprobar id=%s tabla=%s", reg_id, tabla)
                st.error("No fue posible aprobar. Intenta de nuevo.")

    with b2:
        if st.button("Devolver", key=f"comp_dev_{reg_id}",
                     use_container_width=True):
            if not obs_val.strip():
                st.error("Escribe una observación para devolver")
            else:
                try:
                    sb = get_user_client(st.session_state.get('_access_token', ''))
                    sb.table(tabla).update({
                        'estado':               'DEVUELTO',
                        campos['campo_estado']: 'devuelto',
                        campo_obs:              obs_val.strip(),
                        campos['campo_fecha']:  datetime.now().isoformat(),
                    }).eq('id', reg_id).execute()
                    clear_cache()
                    st.warning("Registro devuelto")
                    st.rerun()
                except Exception:
                    _log.exception("Error al devolver id=%s tabla=%s", reg_id, tabla)
                    st.error("No fue posible devolver. Intenta de nuevo.")


def panel_componentes(
    perfil: dict,
    filtro_tipo: str | None,
    tabla: str = 'registros_componentes',
) -> None:
    """
    Panel genérico para listar y aprobar registros de componentes transversales.

    filtro_tipo: cadena que se busca en la columna 'tipo_componente' (case-insensitive).
                 Si es None, no se aplica filtro de tipo.
    tabla:       tabla Supabase donde se persisten las aprobaciones.
    """
    rol = perfil['rol']
    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # ── Filtros ────────────────────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    _form_key = f"form_comp_{filtro_tipo or 'all'}"
    with st.form(_form_key):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            fi = st.date_input("Desde",
                               value=date.today() - timedelta(days=15),
                               key=f"comp_{filtro_tipo}_fi")
        with fc2:
            ff = st.date_input("Hasta",
                               value=date.today(),
                               key=f"comp_{filtro_tipo}_ff")
        with fc3:
            opts_est = (["Todos"] + estados_vis) if estados_vis else (
                ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
            )
            estado_f = st.selectbox("Estado", opts_est, key=f"comp_{filtro_tipo}_est")
        with fc4:
            buscar = st.text_input(
                "Buscar folio / actividad / tramo",
                key=f"comp_{filtro_tipo}_bus",
            )
        fa1, fa2 = st.columns(2)
        with fa1:
            tramo_f = st.text_input("Tramo", key=f"comp_{filtro_tipo}_tramo")
        with fa2:
            act_f = st.text_input("Tipo actividad", key=f"comp_{filtro_tipo}_act")
        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    _sess_key = f"comp_loaded_{filtro_tipo or 'all'}"
    if not aplicar and _sess_key not in st.session_state:
        st.info("Define los filtros y presiona **Aplicar filtros** para cargar.")
        return
    st.session_state[_sess_key] = True

    # ── Carga de datos ─────────────────────────────────────
    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_componentes(
        estados=estados_q,
        fecha_ini=fi.isoformat(),
        fecha_fin=ff.isoformat(),
    )

    # Filtro por tipo de componente
    if filtro_tipo and not df.empty and 'tipo_componente' in df.columns:
        df = df[df['tipo_componente'].str.contains(
            re.escape(filtro_tipo), case=False, na=False
        )]

    # Filtros adicionales
    def _tf(df, col, val):
        if val.strip() and not df.empty and col in df.columns:
            return df[df[col].astype(str).str.contains(
                re.escape(val.strip()), case=False, na=False
            )]
        return df

    df = _tf(df, 'id_tramo',      tramo_f)
    df = _tf(df, 'tipo_actividad', act_f)

    if buscar.strip() and not df.empty:
        b = re.escape(buscar.strip())
        mask = pd.Series(False, index=df.index)
        for col in ['folio', 'tipo_actividad', 'id_tramo', 'usuario_qfield']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(b, case=False, na=False)
        df = df[mask]

    # ── Indicadores acumulados ─────────────────────────────
    total = len(df)
    apr   = len(df[df['estado'] == 'APROBADO'])  if not df.empty and 'estado' in df else 0
    rev   = len(df[df['estado'] == 'REVISADO'])  if not df.empty and 'estado' in df else 0
    bor   = len(df[df['estado'] == 'BORRADOR'])  if not df.empty and 'estado' in df else 0
    dev   = len(df[df['estado'] == 'DEVUELTO'])  if not df.empty and 'estado' in df else 0

    cant_col  = 'cant_interventor' if 'cant_interventor' in df.columns else 'cantidad'
    suma_cant = df[cant_col].apply(safe_float).sum() if (not df.empty and cant_col in df.columns) else 0

    ki1, ki2, ki3, ki4, ki5 = st.columns(5)
    with ki1: kpi("Total registros", str(total), card_accent="accent-blue")
    with ki2: kpi("Aprobados",  str(apr),  accent="kpi-green",  card_accent="accent-green")
    with ki3: kpi("Revisados",  str(rev),  accent="kpi-blue")
    with ki4: kpi("Borradores", str(bor),  accent="kpi-orange" if bor else "")
    with ki5: kpi("Σ Cant.",    f"{suma_cant:,.3f}", card_accent="accent-teal")

    if dev > 0:
        st.warning(f"⚠ {dev} registro(s) devuelto(s) requieren corrección del inspector")

    st.divider()
    st.markdown(f"**{total} registro(s) en el período**")

    if df.empty:
        st.info("Sin registros para los filtros seleccionados.")
        return

    # ── Vista solo lectura ─────────────────────────────────
    if not campos:
        cols = [c for c in [
            'folio', 'fecha_creacion', 'usuario_qfield', 'id_tramo',
            'tipo_componente', 'tipo_actividad', 'cantidad', 'unidad', 'estado',
        ] if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    # ── Vista con aprobación ───────────────────────────────
    # Carga en batch de fotos
    folios = tuple(df['folio'].dropna().tolist()) if 'folio' in df.columns else ()
    df_fot = load_fotos_componentes(folios) if folios else pd.DataFrame()

    for _, reg in df.iterrows():
        tipo_label = str(reg.get('tipo_componente', reg.get('tipo_actividad', '—')))
        folio      = str(reg.get('folio', '—'))
        tramo      = str(reg.get('id_tramo', '—'))
        fecha_c    = str(reg.get('fecha_creacion', ''))[:10]
        usuario    = str(reg.get('usuario_qfield', '—'))
        est_actual = str(reg.get('estado', ''))

        with st.expander(
            f"**{folio}** · {tipo_label[:55]} · {tramo}",
            expanded=False,
        ):
            # Meta-pills
            st.markdown(
                f'<div class="record-meta-row">'
                f'{badge(est_actual)}'
                f'<span class="info-pill">{fecha_c}</span>'
                f'{_pill("Tramo", tramo, "blue")}'
                f'{_pill("CIV", reg.get("civ"), "teal")}'
                f'{_pill("PK", reg.get("pk") or reg.get("civ_pk"), "green")}'
                f'</div>',
                unsafe_allow_html=True,
            )

            col_info, col_apr = st.columns([2.2, 1])

            with col_info:
                cant = safe_float(reg.get('cantidad')) or 0
                st.markdown(
                    f'<div class="record-field-grid">'
                    f'<div><div class="record-field-label">Inspector</div>'
                    f'<div class="record-field-value">{usuario}</div></div>'
                    f'<div><div class="record-field-label">Tipo componente</div>'
                    f'<div class="record-field-value">{tipo_label[:60]}</div></div>'
                    f'<div><div class="record-field-label">Tipo actividad</div>'
                    f'<div class="record-field-value">{reg.get("tipo_actividad","—")}</div></div>'
                    f'<div><div class="record-field-label">Cantidad reportada</div>'
                    f'<div class="record-field-value">{cant:.3f} {reg.get("unidad","")}</div></div>'
                    f'<div><div class="record-field-label">Cant. Residente</div>'
                    f'<div class="record-field-value">{safe_float(reg.get("cant_residente")) or "—"}</div></div>'
                    f'<div><div class="record-field-label">Cant. Interventor</div>'
                    f'<div class="record-field-value">{safe_float(reg.get("cant_interventor")) or "—"}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if reg.get('descripcion'):
                    st.info(str(reg['descripcion']))

                if reg.get('obs_residente') and rol in ('interventor', 'supervisor', 'admin'):
                    st.warning(f"Obs. Residente: {reg['obs_residente']}")
                if reg.get('obs_interventor') and rol in ('supervisor', 'admin'):
                    st.warning(f"Obs. Interventor: {reg['obs_interventor']}")

                # Fotos
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
                _panel_aprobacion_comp(reg, perfil, campos, estado_apr, tabla)
