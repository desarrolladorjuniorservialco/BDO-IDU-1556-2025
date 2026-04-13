"""
pages/_componentes_base.py — Panel base compartido para componentes transversales.
Importado por: componente_ambiental, componente_social, componente_pmt.

SEGURIDAD:
  - re.escape() previene ReDoS en filtro_tipo (parámetro interno, pero
    se trata como no confiable por buenas prácticas defensivas).
  - max_chars en text_area limita payloads de observación.
  - Errores de Supabase se loguean internamente; el usuario recibe
    mensajes genéricos.
"""

import logging
import re
from datetime import datetime, date, timedelta

import streamlit as st

from config import APROBACION_CONFIG
from database import load_componentes, get_user_client, clear_cache
from ui import kpi, safe_float

_log = logging.getLogger(__name__)


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

    # ── Filtros de fecha ───────────────────────────────────
    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    df = load_componentes(fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    if filtro_tipo and not df.empty and 'tipo_componente' in df.columns:
        # re.escape previene ReDoS; el filtro se trata como literal
        df = df[df['tipo_componente'].str.contains(
            re.escape(filtro_tipo), case=False, na=False
        )]

    # ── KPIs ───────────────────────────────────────────────
    total = len(df)
    apr   = len(df[df['estado'] == 'APROBADO'])   if not df.empty and 'estado' in df else 0
    rev   = len(df[df['estado'] == 'REVISADO'])   if not df.empty and 'estado' in df else 0
    dev   = len(df[df['estado'] == 'DEVUELTO'])   if not df.empty and 'estado' in df else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Total", str(total), card_accent="accent-blue")
    with k2: kpi("Aprobados", str(apr), accent="kpi-green", card_accent="accent-green")
    with k3: kpi("Revisados", str(rev), accent="kpi-blue")
    with k4: kpi("Devueltos", str(dev),
                 accent="kpi-red" if dev > 0 else "",
                 card_accent="accent-red" if dev > 0 else "")

    st.divider()
    st.markdown("#### Registros del período")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    if df.empty:
        st.info("Sin registros para el período seleccionado")
        return

    # ── Vista solo lectura ─────────────────────────────────
    if not campos:
        cols = ['folio', 'usuario_qfield', 'id_tramo',
                'tipo_componente', 'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    df_vis = df[df['estado'].isin(estados_vis)] if estados_vis else df

    if df_vis.empty:
        st.success("Sin registros pendientes de revisión")
        cols = ['folio', 'usuario_qfield', 'id_tramo',
                'tipo_componente', 'estado', 'fecha_creacion']
        cols = [c for c in cols if c in df.columns]
        st.dataframe(df[cols], hide_index=True, use_container_width=True)
        return

    st.markdown(f"**{len(df_vis)} pendiente(s) de revisión**")

    for _, reg in df_vis.iterrows():
        tipo_label = reg.get('tipo_componente', reg.get('tipo_actividad', '—'))
        with st.expander(f"**{reg.get('folio','—')}** · {tipo_label}", expanded=False):
            ci, ca = st.columns([2, 1])

            with ci:
                st.markdown(
                    f"**Inspector:** {reg.get('usuario_qfield','—')} &nbsp;|&nbsp; "
                    f"**Tramo:** {reg.get('id_tramo','—')}"
                )
                cant = safe_float(reg.get('cantidad')) or 0
                st.metric("Cantidad reportada",
                          f"{cant:.2f} {reg.get('unidad', '')}")
                if reg.get('descripcion'):
                    st.info(reg['descripcion'])

            with ca:
                campo_cant = campos['campo_cant']
                campo_obs  = campos['campo_obs']
                cant_def   = (safe_float(reg.get(campo_cant)) or
                              safe_float(reg.get('cantidad')) or 0.0)

                cant_val = st.number_input(
                    "Cant. validada", value=float(cant_def),
                    min_value=0.0, max_value=9_999_999.0,
                    step=0.01, key=f"tc_cant_{reg['id']}"
                )
                obs_val = st.text_area(
                    "Observación", key=f"tc_obs_{reg['id']}", height=70,
                    max_chars=1000,
                    placeholder="Opcional / Obligatoria para devolver"
                )

                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Aprobar", key=f"tc_apr_{reg['id']}",
                                 use_container_width=True, type="primary"):
                        try:
                            # get_user_client → RLS activo (JWT del usuario)
                            sb  = get_user_client(st.session_state.get('_access_token', ''))
                            upd = {
                                'estado':               estado_apr,
                                campo_cant:             cant_val,
                                campos['campo_estado']: 'aprobado',
                                campos['campo_apr']:    perfil['id'],
                                campos['campo_fecha']:  datetime.now().isoformat(),
                            }
                            if obs_val:
                                upd[campo_obs] = obs_val
                            sb.table(tabla).update(upd).eq('id', reg['id']).execute()
                            clear_cache()
                            st.rerun()
                        except Exception:
                            _log.exception(
                                "Error al aprobar registro id=%s tabla=%s",
                                reg.get('id'), tabla,
                            )
                            st.error("No fue posible aprobar el registro. Intenta de nuevo.")
                with b2:
                    if st.button("Devolver", key=f"tc_dev_{reg['id']}",
                                 use_container_width=True):
                        if not obs_val:
                            st.error("Escribe una observación para devolver el registro")
                        else:
                            try:
                                # get_user_client → RLS activo (JWT del usuario)
                                sb = get_user_client(st.session_state.get('_access_token', ''))
                                sb.table(tabla).update({
                                    'estado':               'DEVUELTO',
                                    campos['campo_estado']: 'devuelto',
                                    campo_obs:              obs_val,
                                    campos['campo_fecha']:  datetime.now().isoformat(),
                                }).eq('id', reg['id']).execute()
                                clear_cache()
                                st.rerun()
                            except Exception:
                                _log.exception(
                                    "Error al devolver registro id=%s tabla=%s",
                                    reg.get('id'), tabla,
                                )
                                st.error("No fue posible devolver el registro. Intenta de nuevo.")
