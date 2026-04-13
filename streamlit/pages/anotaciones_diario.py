"""
pages/anotaciones_diario.py — Página: Anotaciones del Reporte Diario
Visualización y aprobación de registros_reporte_diario con subtabs
para condición climática, maquinaria, personal y SST.

Fuentes:
  · registros_reporte_diario  — registro maestro (estado, aprobación)
  · bd_personal_obra          — personal en campo
  · bd_condicion_climatica    — condición climática por hora
  · bd_maquinaria_obra        — maquinaria activa
  · bd_sst_ambiental          — dotación SST/Ambiental
  · rf_reporte_diario         — registro fotográfico

SEGURIDAD:
  · re.escape() previene ReDoS en búsqueda libre.
  · Escrituras via get_user_client() → RLS activo.
"""

import logging
import re
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from config import APROBACION_CONFIG
from database import (
    load_reporte_diario, get_user_client, clear_cache,
    load_bd_personal, load_bd_clima, load_bd_maquinaria, load_bd_sst,
    load_fotos_reporte,
)
from ui import badge, section_badge, safe_float

_log = logging.getLogger(__name__)


def page_anotaciones_diario(perfil: dict) -> None:
    rol = perfil['rol']
    section_badge("Anotaciones — Reporte Diario", "purple")
    st.markdown("### Registro Diario de Obra")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # ── Filtros ────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        fi = st.date_input("Desde", value=date.today() - timedelta(days=15),
                           key="rd_fi")
    with fc2:
        ff = st.date_input("Hasta", value=date.today(), key="rd_ff")
    with fc3:
        opts = (["Todos"] + estados_vis) if estados_vis else (
            ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
        )
        estado_f = st.selectbox("Estado", opts, key="rd_est")
    with fc4:
        buscar = st.text_input("🔍 Folio / Usuario / Observación", key="rd_bus")

    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_reporte_diario(estados=estados_q,
                             fecha_ini=fi.isoformat(),
                             fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        b = re.escape(buscar)
        mask = pd.Series(False, index=df.index)
        for col in ['folio', 'usuario_qfield', 'observaciones']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(b, case=False, na=False)
        df = df[mask]

    if df.empty:
        st.info("No hay reportes diarios para los filtros seleccionados.")
        return

    # ── Indicadores acumulados ─────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: st.metric("Total reportes", len(df))
    with m2: st.metric("Aprobados",  len(df[df['estado'] == 'APROBADO'])  if 'estado' in df else 0)
    with m3: st.metric("Revisados",  len(df[df['estado'] == 'REVISADO'])  if 'estado' in df else 0)
    with m4: st.metric("Borradores", len(df[df['estado'] == 'BORRADOR'])  if 'estado' in df else 0)
    with m5: st.metric("Devueltos",  len(df[df['estado'] == 'DEVUELTO'])  if 'estado' in df else 0)

    # Carga en batch de todos los sub-datos
    folios = tuple(df['folio'].dropna().tolist()) if 'folio' in df.columns else ()
    if folios:
        df_pers = load_bd_personal(folios)
        df_clim = load_bd_clima(folios)
        df_maq  = load_bd_maquinaria(folios)
        df_sst  = load_bd_sst(folios)
        df_fot  = load_fotos_reporte(folios)
    else:
        df_pers = df_clim = df_maq = df_sst = df_fot = pd.DataFrame()

    # KPIs personal acumulado
    if not df_pers.empty:
        num_cols = [c for c in ['inspectores','personal_operativo','personal_boal','personal_transito']
                    if c in df_pers.columns]
        if num_cols:
            st.markdown("**Personal acumulado en el período:**")
            p_cols = st.columns(len(num_cols))
            for i, col in enumerate(num_cols):
                total = int(pd.to_numeric(df_pers[col], errors='coerce').fillna(0).sum())
                with p_cols[i]:
                    st.metric(col.replace('_', ' ').title(), total)

    st.divider()
    st.markdown(f"**{len(df)} reporte(s)**")

    # ── Lista de reportes ──────────────────────────────────
    for _, reg in df.iterrows():
        folio      = str(reg.get('folio', '—'))
        est_actual = str(reg.get('estado', ''))
        fecha_rep  = str(reg.get('fecha_reporte', reg.get('fecha', '')))[:10]
        usuario    = str(reg.get('usuario_qfield', '—'))

        with st.expander(f"**{folio}** · {fecha_rep} · {usuario}", expanded=False):
            # Determinar tabs disponibles
            has_clim = not df_clim.empty and folio in df_clim.get('folio', pd.Series()).tolist()
            has_maq  = not df_maq.empty  and folio in df_maq.get('folio',  pd.Series()).tolist()
            has_pers = not df_pers.empty and folio in df_pers.get('folio', pd.Series()).tolist()
            has_sst  = not df_sst.empty  and folio in df_sst.get('folio',  pd.Series()).tolist()

            tab_labels = ["📋 General"]
            if has_clim: tab_labels.append("🌤️ Clima")
            if has_maq:  tab_labels.append("🚜 Maquinaria")
            if has_pers: tab_labels.append("👷 Personal")
            if has_sst:  tab_labels.append("⚠️ SST")

            tabs = st.tabs(tab_labels)
            t = 0

            # ── Tab General ────────────────────────────────
            with tabs[t]:
                cg1, cg2 = st.columns([2.5, 1.2])
                with cg1:
                    st.markdown(f"""
                    <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;flex-wrap:wrap;">
                        {badge(est_actual)}
                        <span style="font-family:'IBM Plex Mono',monospace;font-size:0.70rem;
                                     color:var(--text-muted);">{fecha_rep}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"**Inspector/Usuario:** {usuario}")
                    if reg.get('observaciones'):
                        st.info(str(reg['observaciones']))

                    # Observaciones de revisión previas
                    if reg.get('obs_residente') and rol in ('interventor', 'admin'):
                        st.warning(f"Obs. residente: {reg['obs_residente']}")
                    if reg.get('obs_interventor') and rol in ('supervisor', 'admin'):
                        st.warning(f"Obs. interventor: {reg['obs_interventor']}")

                    # Fotos
                    if not df_fot.empty and 'folio' in df_fot.columns:
                        fotos_r = df_fot[df_fot['folio'] == folio]
                        urls = fotos_r['foto_url'].dropna().tolist() if not fotos_r.empty else []
                        if urls:
                            st.markdown("**📷 Registro fotográfico**")
                            f_cols = st.columns(min(len(urls), 4))
                            for i, url in enumerate(urls[:4]):
                                with f_cols[i]:
                                    st.image(url, use_column_width=True)
                        else:
                            st.caption("Sin fotos registradas")

                with cg2:
                    _panel_aprobacion_rd(reg, perfil, campos, estado_apr)
            t += 1

            # ── Tab Clima ──────────────────────────────────
            if has_clim:
                with tabs[t]:
                    sub = df_clim[df_clim['folio'] == folio]
                    for _, r in sub.iterrows():
                        st.markdown(
                            f"**Estado clima:** {r.get('estado_clima','—')} &nbsp;|&nbsp; "
                            f"**Hora:** {str(r.get('hora','—'))[:5]}"
                        )
                        if r.get('observaciones'):
                            st.caption(str(r['observaciones']))
                t += 1

            # ── Tab Maquinaria ─────────────────────────────
            if has_maq:
                with tabs[t]:
                    sub = df_maq[df_maq['folio'] == folio]
                    maq_cols = [c for c in [
                        'operarios','volquetas','vibrocompactador','equipos_especiales',
                        'minicargador','ruteadora','compresor','retrocargador',
                        'extendedora_asfalto','compactador_neumatico','observaciones',
                    ] if c in sub.columns]
                    if maq_cols:
                        st.dataframe(sub[maq_cols], hide_index=True, use_container_width=True)
                t += 1

            # ── Tab Personal ───────────────────────────────
            if has_pers:
                with tabs[t]:
                    sub = df_pers[df_pers['folio'] == folio]
                    num_c = [c for c in ['inspectores','personal_operativo',
                                         'personal_boal','personal_transito']
                             if c in sub.columns]
                    for _, r in sub.iterrows():
                        p_cols = st.columns(max(len(num_c), 1))
                        for i, col in enumerate(num_c):
                            with p_cols[i]:
                                st.metric(col.replace('_',' ').title(),
                                          int(r.get(col, 0) or 0))
                t += 1

            # ── Tab SST ────────────────────────────────────
            if has_sst:
                with tabs[t]:
                    sub = df_sst[df_sst['folio'] == folio]
                    sst_num = [c for c in ['botiquin','kit_antiderrames',
                                           'punto_hidratacion','punto_ecologico','extintor']
                               if c in sub.columns]
                    for _, r in sub.iterrows():
                        s_cols = st.columns(max(len(sst_num), 1))
                        for i, col in enumerate(sst_num):
                            with s_cols[i]:
                                st.metric(col.replace('_',' ').title(),
                                          int(r.get(col, 0) or 0))
                        if r.get('observaciones'):
                            st.warning(str(r['observaciones']))
                t += 1


def _panel_aprobacion_rd(reg: pd.Series, perfil: dict,
                          campos: dict | None, estado_apr: str | None) -> None:
    """Panel de aprobación/devolución para reporte diario (sin campo cantidad)."""
    if not campos:
        st.caption(f"Estado: {reg.get('estado','—')}")
        return

    estado_actual = str(reg.get('estado', '')).upper()
    reg_id = str(reg.get('id', ''))

    st.markdown("**Validación**")
    obs_val = st.text_area(
        "Observación",
        key=f"obs_rd_{reg_id}",
        height=80,
        max_chars=1000,
        placeholder="Opcional para aprobar · Obligatoria para devolver",
        value=str(reg.get(campos.get('campo_obs', ''), '') or ''),
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Aprobar", key=f"apr_rd_{reg_id}",
                     use_container_width=True, type="primary"):
            try:
                sb  = get_user_client(st.session_state.get('_access_token', ''))
                upd = {
                    'estado':               estado_apr,
                    campos['campo_estado']: 'aprobado',
                    campos['campo_apr']:    perfil['id'],
                    campos['campo_fecha']:  datetime.now().isoformat(),
                }
                if obs_val:
                    upd[campos['campo_obs']] = obs_val
                sb.table('registros_reporte_diario').update(upd).eq('id', reg_id).execute()
                clear_cache()
                st.success("Aprobado")
                st.rerun()
            except Exception:
                _log.exception("Error al aprobar reporte diario id=%s", reg_id)
                st.error("No fue posible actualizar. Intenta de nuevo.")

    with b2:
        if st.button("Devolver", key=f"dev_rd_{reg_id}",
                     use_container_width=True):
            if not obs_val or not obs_val.strip():
                st.error("Escribe una observación para devolver")
            else:
                try:
                    sb = get_user_client(st.session_state.get('_access_token', ''))
                    sb.table('registros_reporte_diario').update({
                        'estado':               'DEVUELTO',
                        campos['campo_estado']: 'devuelto',
                        campos['campo_obs']:    obs_val,
                        campos['campo_fecha']:  datetime.now().isoformat(),
                    }).eq('id', reg_id).execute()
                    clear_cache()
                    st.warning("Devuelto")
                    st.rerun()
                except Exception:
                    _log.exception("Error al devolver reporte diario id=%s", reg_id)
                    st.error("No fue posible devolver. Intenta de nuevo.")
