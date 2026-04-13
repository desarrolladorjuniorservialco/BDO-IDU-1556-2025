"""
pages/anotaciones.py — Página: Anotaciones de Bitácora
Vista de registros_cantidades APROBADOS con registro fotográfico.
Flujo de aprobación (para roles con acceso) sobre los mismos registros.

SEGURIDAD:
  - re.escape() previene ReDoS en el campo de búsqueda libre.
  - max_chars en text_area de observación limita payloads grandes.
"""

import logging
import re
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st

from config import APROBACION_CONFIG
from database import (
    load_cantidades, load_fotos_cantidades,
    get_user_client, clear_cache,
)
from ui import badge, section_badge, safe_float

_log = logging.getLogger(__name__)


def _pill(label: str, valor, color: str = "") -> str:
    if valor is None or str(valor).strip() in ('', 'nan', 'None', '—'):
        return ""
    cls = f"info-pill {color}" if color else "info-pill"
    return f'<span class="{cls}">{label}: {valor}</span>'


def page_anotaciones(perfil: dict) -> None:
    rol = perfil['rol']
    section_badge("Anotaciones Aprobadas", "green")
    st.markdown("### Registro de Actividades Aprobadas")

    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg

    # ── Formulario de filtros ──────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    with st.form("form_anotaciones"):
        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            fi = st.date_input("Desde", value=date.today() - timedelta(days=30))
        with fc2:
            ff = st.date_input("Hasta", value=date.today())
        with fc3:
            buscar = st.text_input("Folio / Actividad / CIV / Tramo")

        fa1, fa2 = st.columns(2)
        with fa1:
            tramo_f = st.text_input("Tramo")
        with fa2:
            civ_f = st.text_input("CIV")

        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Solo carga tras primer submit o recarga normal
    if not aplicar and 'anot_df' not in st.session_state:
        st.info("Define los filtros y presiona **Aplicar filtros** para cargar.")
        return

    # Siempre cargar solo APROBADO (la página es solo lectura de aprobados)
    df = load_cantidades(
        estados=['APROBADO'],
        fecha_ini=fi.isoformat(),
        fecha_fin=ff.isoformat(),
    )

    def _tf(df, col, val):
        if val.strip() and not df.empty and col in df.columns:
            return df[df[col].astype(str).str.contains(
                re.escape(val.strip()), case=False, na=False
            )]
        return df

    if buscar.strip() and not df.empty:
        b = re.escape(buscar.strip())
        mask = pd.Series(False, index=df.index)
        for col in ['folio', 'tipo_actividad', 'civ', 'id_tramo',
                    'item_pago', 'item_descripcion', 'usuario_qfield']:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(b, case=False, na=False)
        df = df[mask]

    df = _tf(df, 'id_tramo', tramo_f)
    df = _tf(df, 'civ',      civ_f)

    if df.empty:
        st.info("No hay registros aprobados para los filtros seleccionados.")
        return

    # ── Métricas ───────────────────────────────────────────
    cant_col  = 'cant_interventor' if 'cant_interventor' in df.columns else 'cantidad'
    suma_cant = df[cant_col].apply(safe_float).sum() if cant_col in df.columns else 0

    m1, m2, m3 = st.columns(3)
    with m1: st.metric("Registros aprobados", len(df))
    with m2: st.metric("Σ Cantidad (Interventor)", f"{suma_cant:,.3f}")
    with m3:
        tramos_uniq = df['id_tramo'].nunique() if 'id_tramo' in df.columns else 0
        st.metric("Tramos involucrados", tramos_uniq)
    st.divider()

    # Carga en batch de fotos
    folios = tuple(df['folio'].dropna().tolist()) if 'folio' in df.columns else ()
    df_fot = load_fotos_cantidades(folios) if folios else pd.DataFrame()

    st.markdown(f"**{len(df)} registro(s) aprobado(s)**")

    for _, reg in df.iterrows():
        est_actual = str(reg.get('estado', ''))
        folio      = str(reg.get('folio', '—'))
        actividad  = str(reg.get('tipo_actividad', reg.get('item_descripcion', '—')))
        tramo      = str(reg.get('id_tramo', '—'))
        fecha_c    = str(reg.get('fecha_creacion', reg.get('fecha_inicio', '')))[:10]
        usuario    = str(reg.get('usuario_qfield', '—'))

        with st.expander(f"**{folio}** · {actividad[:55]} · {tramo}", expanded=False):
            st.markdown(
                f'<div class="record-meta-row">'
                f'{badge(est_actual)}'
                f'<span class="info-pill">{fecha_c}</span>'
                f'{_pill("Tramo", tramo, "blue")}'
                f'{_pill("CIV", reg.get("civ"), "teal")}'
                f'{_pill("Ítem", reg.get("item_pago"), "orange")}'
                f'</div>',
                unsafe_allow_html=True,
            )

            ci, ca = st.columns([2.2, 1])

            with ci:
                st.markdown(
                    f'<div class="record-field-grid">'
                    f'<div><div class="record-field-label">Inspector</div>'
                    f'<div class="record-field-value">{usuario}</div></div>'
                    f'<div><div class="record-field-label">Componente / Cap.</div>'
                    f'<div class="record-field-value">{reg.get("codigo_elemento","—")}</div></div>'
                    f'<div><div class="record-field-label">Ítem de pago</div>'
                    f'<div class="record-field-value">{reg.get("item_pago","—")}</div></div>'
                    f'<div><div class="record-field-label">Actividad</div>'
                    f'<div class="record-field-value">{actividad[:80]}</div></div>'
                    f'<div><div class="record-field-label">Cant. Inspector</div>'
                    f'<div class="record-field-value">{safe_float(reg.get("cantidad")) or 0:.3f} {reg.get("unidad","")}</div></div>'
                    f'<div><div class="record-field-label">Cant. Residente</div>'
                    f'<div class="record-field-value">{safe_float(reg.get("cant_residente")) or "—"}</div></div>'
                    f'<div><div class="record-field-label">Cant. Interventor</div>'
                    f'<div class="record-field-value kpi-green">{safe_float(reg.get("cant_interventor")) or "—"}</div></div>'
                    f'<div><div class="record-field-label">Unidad</div>'
                    f'<div class="record-field-value">{reg.get("unidad","—")}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if reg.get('observaciones'):
                    st.info(str(reg['observaciones']))

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

            with ca:
                # Trazabilidad de aprobación
                if reg.get('aprobado_residente'):
                    fec = str(reg.get('fecha_residente', ''))[:10]
                    obs = reg.get('obs_residente', '')
                    st.markdown(
                        f'<div class="approval-history">'
                        f'<div class="approval-history-item">'
                        f'<span class="approval-history-role">Residente · {fec}</span>'
                        f'<span style="font-size:0.78rem;">{reg["aprobado_residente"]}</span>'
                        f'{f"<span style=\'color:var(--accent-orange);font-size:0.76rem;\'>↩ {obs}</span>" if obs else ""}'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                if reg.get('aprobado_interventor'):
                    fec = str(reg.get('fecha_interventor', ''))[:10]
                    obs = reg.get('obs_interventor', '')
                    st.markdown(
                        f'<div class="approval-history">'
                        f'<div class="approval-history-item">'
                        f'<span class="approval-history-role">Interventor · {fec}</span>'
                        f'<span style="font-size:0.78rem;">{reg["aprobado_interventor"]}</span>'
                        f'{f"<span style=\'color:var(--accent-orange);font-size:0.76rem;\'>↩ {obs}</span>" if obs else ""}'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
