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
  · max_chars en text_area limita payloads de observación.
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
from ui import badge, kpi, section_badge, safe_float

_log = logging.getLogger(__name__)

# Tipo de reporte → label visible y color
_TIPO_META: dict[str, tuple[str, str]] = {
    'general':   ('General',    'blue'),
    'clima':     ('Clima',      'teal'),
    'maquinaria':('Maquinaria', 'orange'),
    'personal':  ('Personal',   'green'),
    'sst':       ('SST',        'purple'),
}


def _pill(label: str, valor, color: str = "") -> str:
    if valor is None or str(valor).strip() in ('', 'nan', 'None', '—'):
        return ""
    cls = f"info-pill {color}" if color else "info-pill"
    return f'<span class="{cls}">{label}: {valor}</span>'


def _historial_aprobacion_html(reg: pd.Series) -> str:
    items = []
    if reg.get('aprobado_residente'):
        est = str(reg.get('estado_residente', '')).capitalize()
        fec = str(reg.get('fecha_residente', ''))[:10]
        obs = reg.get('obs_residente', '')
        items.append(f"""
        <div class="approval-history-item">
            <span class="approval-history-role">Obra (Niv. 1) · {est} · {fec}</span>
            <span style="font-size:0.78rem;">{reg['aprobado_residente']}</span>
            {f'<span style="color:var(--accent-orange);font-size:0.76rem;">↩ {obs}</span>' if obs else ''}
        </div>""")
    if reg.get('aprobado_interventor'):
        est = str(reg.get('estado_interventor', '')).capitalize()
        fec = str(reg.get('fecha_interventor', ''))[:10]
        obs = reg.get('obs_interventor', '')
        items.append(f"""
        <div class="approval-history-item">
            <span class="approval-history-role">Interventoría (Niv. 2) · {est} · {fec}</span>
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


def page_anotaciones_diario(perfil: dict) -> None:
    rol = perfil['rol']
    section_badge("Anotaciones — Reporte Diario", "purple")
    st.markdown("### Registro Diario de Obra")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None, None))
    estados_vis, estado_apr, campos, estados_accion = cfg

    # ── Formulario de filtros ──────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    with st.form("form_rd"):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            fi = st.date_input("Desde",
                               value=date.today() - timedelta(days=15),
                               key="rd_fi")
        with fc2:
            ff = st.date_input("Hasta", value=date.today(), key="rd_ff")
        with fc3:
            opts_est = (["Todos"] + estados_vis) if estados_vis else (
                ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
            )
            estado_f = st.selectbox("Estado", opts_est, key="rd_est")
        with fc4:
            buscar = st.text_input("Buscar: folio / usuario / observación", key="rd_bus")
        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    if not aplicar and 'rd_loaded' not in st.session_state:
        st.info("Define los filtros y presiona **Aplicar filtros** para cargar.")
        return
    st.session_state['rd_loaded'] = True

    # ── Carga de datos ─────────────────────────────────────
    estados_q = None if estado_f == "Todos" else [estado_f]
    if estados_vis and estado_f == "Todos":
        estados_q = estados_vis

    df = load_reporte_diario(estados=estados_q)

    # Filtro de fecha en Python sobre fecha_reporte (maneja NULLs sin excluirlos si no hay filtro)
    if not df.empty and 'fecha_reporte' in df.columns:
        fechas = pd.to_datetime(df['fecha_reporte'], errors='coerce')
        mask = (fechas >= pd.Timestamp(fi)) & (fechas <= pd.Timestamp(ff))
        df = df[mask | fechas.isna()]

    if buscar.strip() and not df.empty:
        b = re.escape(buscar.strip())
        mask = pd.Series(False, index=df.index)
        for col in ['folio', 'usuario_qfield', 'observaciones']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(b, case=False, na=False)
        df = df[mask]

    if df.empty:
        st.info("No hay reportes diarios para los filtros seleccionados.")
        return

    _csv_cols_rd = [c for c in [
        'folio', 'fecha_reporte', 'fecha', 'usuario_qfield', 'estado',
        'civ', 'pk_id', 'id_tramo', 'cantidad', 'unidad', 'observaciones',
    ] if c in df.columns]
    st.download_button(
        "Exportar CSV",
        data=df[_csv_cols_rd].to_csv(index=False).encode('utf-8'),
        file_name=f"ReporteDiario_{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    # ── Indicadores acumulados ─────────────────────────────
    n_total = len(df)
    n_apr   = len(df[df['estado'] == 'APROBADO'])  if 'estado' in df else 0
    n_rev   = len(df[df['estado'] == 'REVISADO'])  if 'estado' in df else 0
    n_bor   = len(df[df['estado'] == 'BORRADOR'])  if 'estado' in df else 0
    n_dev   = len(df[df['estado'] == 'DEVUELTO'])  if 'estado' in df else 0

    ki1, ki2, ki3, ki4, ki5 = st.columns(5)
    with ki1: kpi("Total reportes", str(n_total), card_accent="accent-blue")
    with ki2: kpi("Aprobados",  str(n_apr),  accent="kpi-green",  card_accent="accent-green")
    with ki3: kpi("Revisados",  str(n_rev),  accent="kpi-blue",   card_accent="accent-blue")
    with ki4: kpi("Borradores", str(n_bor),  accent="kpi-orange" if n_bor else "")
    with ki5: kpi("Devueltos",  str(n_dev),
                  accent="kpi-red" if n_dev else "",
                  card_accent="accent-red" if n_dev else "")

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

    # KPIs de personal acumulado en el período
    if not df_pers.empty:
        num_cols_pers = [c for c in [
            'inspectores', 'personal_operativo',
            'personal_boal', 'personal_transito',
        ] if c in df_pers.columns]
        if num_cols_pers:
            st.markdown(
                '<div class="acum-panel">'
                '<div class="acum-panel-title">Personal acumulado en el período</div>'
                + "".join([
                    f'<div class="acum-item">'
                    f'<div class="acum-item-label">{c.replace("_"," ").title()}</div>'
                    f'<div class="acum-item-value">'
                    f'{int(pd.to_numeric(df_pers[c], errors="coerce").fillna(0).sum())}'
                    f'</div></div>'
                    for c in num_cols_pers
                ])
                + '</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown(f"**{n_total} reporte(s)**")

    # ── Lista de reportes ──────────────────────────────────
    for _row_idx, (_, reg) in enumerate(df.iterrows()):
        folio      = str(reg.get('folio', '—'))
        est_actual = str(reg.get('estado', ''))
        fecha_rep  = str(reg.get('fecha_reporte', reg.get('fecha', '')))[:10]
        usuario    = str(reg.get('usuario_qfield', '—'))

        # El GPKG puede tener múltiples ítems por folio (pk_id/civ distintos).
        # Se incluyen en el título para distinguirlos visualmente.
        pk_id_v = reg.get('pk_id')
        civ_v   = reg.get('civ')
        sufijo  = ""
        if pk_id_v not in (None, '', 'nan', 'None'):
            sufijo += f" · PK {pk_id_v}"
        if civ_v not in (None, '', 'nan', 'None'):
            sufijo += f" · CIV {civ_v}"

        with st.expander(
            f"**{folio}**{sufijo} · {fecha_rep} · {usuario}",
            expanded=False,
        ):
            # Determinar tabs disponibles
            has_clim = (not df_clim.empty and
                        'folio' in df_clim.columns and
                        folio in df_clim['folio'].tolist())
            has_maq  = (not df_maq.empty and
                        'folio' in df_maq.columns and
                        folio in df_maq['folio'].tolist())
            has_pers = (not df_pers.empty and
                        'folio' in df_pers.columns and
                        folio in df_pers['folio'].tolist())
            has_sst  = (not df_sst.empty and
                        'folio' in df_sst.columns and
                        folio in df_sst['folio'].tolist())

            tab_labels = ["General"]
            if has_clim: tab_labels.append("Clima")
            if has_maq:  tab_labels.append("Maquinaria")
            if has_pers: tab_labels.append("Personal")
            if has_sst:  tab_labels.append("SST")

            tabs = st.tabs(tab_labels)
            t = 0

            # ── Tab General ────────────────────────────────
            with tabs[t]:
                cg1, cg2 = st.columns([2.5, 1.2])
                with cg1:
                    st.markdown(
                        f'<div class="record-meta-row">'
                        f'{badge(est_actual)}'
                        f'<span class="info-pill">{fecha_rep}</span>'
                        f'{_pill("Inspector", usuario, "blue")}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Campos de actividad del reporte diario
                    _activity_fields = {
                        'Tramo':    reg.get('id_tramo'),
                        'CIV':      reg.get('civ'),
                        'PK':       reg.get('pk_id'),
                        'Cantidad': reg.get('cantidad'),
                        'Unidad':   reg.get('unidad'),
                        'Leído':    reg.get('leido'),
                    }
                    _pills_html = "".join(
                        _pill(k, v) for k, v in _activity_fields.items() if v not in (None, '', 'nan', 'None')
                    )
                    if _pills_html:
                        st.markdown(
                            f'<div class="record-meta-row">{_pills_html}</div>',
                            unsafe_allow_html=True,
                        )

                    if reg.get('observaciones'):
                        st.info(str(reg['observaciones']))

                    # Observaciones de revisión previas (visibles según rol)
                    if reg.get('obs_residente') and rol in ('interventoria', 'supervision', 'admin'):
                        st.warning(f"Obs. Obra (Niv. 1): {reg['obs_residente']}")
                    if reg.get('obs_interventor') and rol in ('supervision', 'admin'):
                        st.warning(f"Obs. Interventoría (Niv. 2): {reg['obs_interventor']}")

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
                                    st.image(url, width="stretch")
                        else:
                            st.caption("Sin fotos registradas")

                with cg2:
                    # Historial de aprobación
                    hist = _historial_aprobacion_html(reg)
                    if hist:
                        st.markdown(hist, unsafe_allow_html=True)

                    _panel_aprobacion_rd(reg, perfil, campos, estado_apr, estados_accion, _row_idx)
            t += 1

            # ── Tab Clima ──────────────────────────────────
            if has_clim:
                with tabs[t]:
                    sub = df_clim[df_clim['folio'] == folio]
                    for _, r in sub.iterrows():
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric(
                                "Estado climático",
                                str(r.get('estado_clima', '—')),
                            )
                        with col_b:
                            st.metric("Hora", str(r.get('hora', '—'))[:5])
                        if r.get('observaciones'):
                            st.caption(str(r['observaciones']))
                        st.divider()
                t += 1

            # ── Tab Maquinaria ─────────────────────────────
            if has_maq:
                with tabs[t]:
                    sub = df_maq[df_maq['folio'] == folio]
                    maq_cols = [c for c in [
                        'operarios', 'volquetas', 'vibrocompactador',
                        'equipos_especiales', 'minicargador', 'ruteadora',
                        'compresor', 'retrocargador', 'extendedora_asfalto',
                        'compactador_neumatico', 'observaciones',
                    ] if c in sub.columns]
                    if maq_cols:
                        st.dataframe(sub[maq_cols],
                                     hide_index=True, width="stretch")
                t += 1

            # ── Tab Personal ───────────────────────────────
            if has_pers:
                with tabs[t]:
                    sub = df_pers[df_pers['folio'] == folio]
                    num_c = [c for c in [
                        'inspectores', 'personal_operativo',
                        'personal_boal', 'personal_transito',
                    ] if c in sub.columns]
                    for _, r in sub.iterrows():
                        p_cols = st.columns(max(len(num_c), 1))
                        for i, col in enumerate(num_c):
                            with p_cols[i]:
                                st.metric(
                                    col.replace('_', ' ').title(),
                                    int(r.get(col, 0) or 0),
                                )
                t += 1

            # ── Tab SST ────────────────────────────────────
            if has_sst:
                with tabs[t]:
                    sub = df_sst[df_sst['folio'] == folio]
                    sst_num = [c for c in [
                        'botiquin', 'kit_antiderrames',
                        'punto_hidratacion', 'punto_ecologico', 'extintor',
                    ] if c in sub.columns]
                    for _, r in sub.iterrows():
                        s_cols = st.columns(max(len(sst_num), 1))
                        for i, col in enumerate(sst_num):
                            with s_cols[i]:
                                st.metric(
                                    col.replace('_', ' ').title(),
                                    int(r.get(col, 0) or 0),
                                )
                        if r.get('observaciones'):
                            st.warning(str(r['observaciones']))
                t += 1


def _panel_aprobacion_rd(reg: pd.Series, perfil: dict,
                          campos: dict | None, estado_apr: str | None,
                          estados_accion: list | None,
                          row_idx: int = 0) -> None:
    """Panel de aprobación/devolución para reporte diario."""
    est_actual = str(reg.get('estado', '')).upper()
    if not campos or not estados_accion or est_actual not in estados_accion:
        st.caption(f"Estado: {reg.get('estado', '—')}")
        return

    reg_id = str(reg.get('id', ''))
    # Incluir row_idx para garantizar unicidad cuando varios registros comparten id
    wkey = f"{row_idx}_{reg_id}"

    st.markdown(
        '<div class="approval-panel-title">Validación</div>',
        unsafe_allow_html=True,
    )

    obs_val = st.text_area(
        "Observación",
        key=f"obs_rd_{wkey}",
        height=80,
        max_chars=1000,
        placeholder="Opcional para aprobar · Obligatoria para devolver",
        value=str(reg.get(campos.get('campo_obs', ''), '') or ''),
    )

    b1, b2 = st.columns(2)
    with b1:
        if st.button("Aprobar", key=f"apr_rd_{wkey}",
                     width="stretch", type="primary"):
            try:
                sb  = get_user_client(st.session_state.get('_access_token', ''))
                upd = {
                    'estado':               estado_apr,
                    campos['campo_estado']: 'aprobado',
                    campos['campo_apr']:    perfil.get('nombre', perfil['id']),
                    campos['campo_fecha']:  datetime.now().isoformat(),
                }
                if obs_val.strip():
                    upd[campos['campo_obs']] = obs_val.strip()
                sb.table('registros_reporte_diario').update(upd)\
                  .eq('id', reg_id).execute()
                clear_cache()
                st.success("Aprobado")
                st.rerun()
            except Exception:
                _log.exception("Error al aprobar reporte diario id=%s", reg_id)
                st.error("No fue posible actualizar. Intenta de nuevo.")

    with b2:
        if st.button("Devolver", key=f"dev_rd_{wkey}",
                     width="stretch"):
            if not obs_val.strip():
                st.error("Escribe una observación para devolver")
            else:
                try:
                    sb = get_user_client(st.session_state.get('_access_token', ''))
                    sb.table('registros_reporte_diario').update({
                        'estado':               'DEVUELTO',
                        campos['campo_estado']: 'devuelto',
                        campos['campo_obs']:    obs_val.strip(),
                        campos['campo_fecha']:  datetime.now().isoformat(),
                    }).eq('id', reg_id).execute()
                    clear_cache()
                    st.warning("Devuelto")
                    st.rerun()
                except Exception:
                    _log.exception("Error al devolver reporte diario id=%s", reg_id)
                    st.error("No fue posible devolver. Intenta de nuevo.")
