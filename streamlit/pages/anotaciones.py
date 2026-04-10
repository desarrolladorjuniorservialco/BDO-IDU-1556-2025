"""
pages/anotaciones.py — Página: Anotaciones de Bitácora
Flujo de aprobación escalonada sobre registros_cantidades.
"""

from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from config import APROBACION_CONFIG
from database import load_cantidades, get_supabase, clear_cache
from ui import badge, section_badge, safe_float


def page_anotaciones(perfil: dict) -> None:
    rol = perfil['rol']
    section_badge("Anotaciones de Bitácora", "purple")
    st.markdown("### Registro y aprobación de actividades")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # ── Filtros ────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=15))
    with c2: ff = st.date_input("Hasta", value=date.today())
    with c3:
        opts = (["Todos"] + estados_vis) if estados_vis else (
            ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
        )
        estado_f = st.selectbox("Estado", opts)
    with c4:
        buscar = st.text_input("Folio / Actividad / CIV")

    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_cantidades(estados=estados_q,
                         fecha_ini=fi.isoformat(),
                         fecha_fin=ff.isoformat())

    if buscar and not df.empty:
        mask = (
            df.get('folio', pd.Series(dtype=str))
              .astype(str).str.contains(buscar, case=False, na=False)
            | df.get('tipo_actividad', pd.Series(dtype=str))
              .astype(str).str.contains(buscar, case=False, na=False)
            | df.get('civ', pd.Series(dtype=str))
              .astype(str).str.contains(buscar, case=False, na=False)
        )
        df = df[mask]

    if df.empty:
        st.info("No hay registros para los filtros seleccionados")
        return

    # ── Métricas ───────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Total", len(df))
    with m2: st.metric("Borradores", len(df[df['estado'] == 'BORRADOR']) if 'estado' in df else 0)
    with m3: st.metric("Revisados",  len(df[df['estado'] == 'REVISADO'])  if 'estado' in df else 0)
    with m4: st.metric("Aprobados",  len(df[df['estado'] == 'APROBADO'])  if 'estado' in df else 0)
    st.divider()

    # ── Vista solo lectura ─────────────────────────────────
    if not campos:
        cols = ['folio', 'usuario_qfield', 'id_tramo', 'civ',
                'tipo_actividad', 'cantidad', 'unidad', 'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    # ── Vista con aprobación ───────────────────────────────
    st.markdown(f"**{len(df)} registro(s) para revisión**")

    for _, reg in df.iterrows():
        estado_actual = reg.get('estado', '')
        folio         = reg.get('folio', '—')
        actividad     = reg.get('tipo_actividad', '—')
        tramo         = reg.get('tramo_descripcion', reg.get('id_tramo', '—'))

        with st.expander(f"**{folio}** · {actividad} · {tramo}", expanded=False):
            ci, ca = st.columns([2.2, 1])

            with ci:
                st.markdown(f"""
                <div style="display:flex;gap:0.5rem;margin-bottom:0.75rem;flex-wrap:wrap;">
                    {badge(estado_actual)}
                    <span style="font-family:'IBM Plex Mono',monospace;font-size:0.70rem;
                                 color:var(--text-muted);">
                        {str(reg.get('fecha_inicio', ''))[:10]}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                ca1, ca2, ca3 = st.columns(3)
                with ca1:
                    st.markdown(f"**Inspector:** {reg.get('usuario_qfield', '—')}")
                    st.markdown(f"**Tramo:** {reg.get('id_tramo', '—')}")
                    st.markdown(f"**CIV:** {reg.get('civ', '—')}")
                with ca2:
                    st.markdown(f"**Item pago:** {reg.get('item_pago', '—')}")
                    st.markdown(f"**Cod. elemento:** {reg.get('codigo_elemento', '—')}")
                    st.markdown(f"**Unidad:** {reg.get('unidad', '—')}")
                with ca3:
                    cant = safe_float(reg.get('cantidad')) or 0
                    st.metric("Cant. inspector", f"{cant:.2f} {reg.get('unidad', '')}")
                    if reg.get('cant_residente'):
                        st.metric("Cant. residente",
                                  f"{safe_float(reg.get('cant_residente') or 0):.2f}")

                if reg.get('descripcion'):
                    st.info(reg['descripcion'])
                if reg.get('obs_residente') and rol in ('interventor', 'admin'):
                    st.warning(f"Obs. residente: {reg['obs_residente']}")
                if reg.get('documento_adj'):
                    st.caption(f"Adjunto de campo: {reg['documento_adj']}")

            with ca:
                st.markdown("**Validación**")
                campo_cant = campos['campo_cant']
                campo_obs  = campos['campo_obs']
                cant_def   = (safe_float(reg.get(campo_cant)) or
                              safe_float(reg.get('cantidad')) or 0.0)

                cant_val = st.number_input(
                    "Cantidad validada", value=float(cant_def),
                    step=0.01, key=f"cant_{reg['id']}"
                )
                obs_val = st.text_area(
                    "Observación", key=f"obs_{reg['id']}", height=80,
                    placeholder="Opcional para aprobar · Obligatoria para devolver"
                )

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Aprobar", key=f"apr_{reg['id']}",
                                 use_container_width=True, type="primary"):
                        try:
                            sb  = get_supabase()
                            upd = {
                                'estado':               estado_apr,
                                campo_cant:             cant_val,
                                campos['campo_estado']: 'aprobado',
                                campos['campo_apr']:    perfil['id'],
                                campos['campo_fecha']:  datetime.now().isoformat(),
                            }
                            if obs_val:
                                upd[campo_obs] = obs_val
                            sb.table('registros_cantidades')\
                              .update(upd).eq('id', reg['id']).execute()
                            clear_cache()
                            st.success("Aprobado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with b2:
                    if st.button("Devolver", key=f"dev_{reg['id']}",
                                 use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación para devolver")
                        else:
                            try:
                                sb = get_supabase()
                                sb.table('registros_cantidades').update({
                                    'estado':               'DEVUELTO',
                                    campos['campo_estado']: 'devuelto',
                                    campo_obs:              obs_val,
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }).eq('id', reg['id']).execute()
                                clear_cache()
                                st.warning("Devuelto")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
