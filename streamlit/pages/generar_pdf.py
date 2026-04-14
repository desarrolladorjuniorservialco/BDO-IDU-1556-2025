"""
pages/generar_pdf.py — Página: Generar Informe de Bitácora
Exporta registros en PDF, CSV o Excel (multi-hoja) según filtros.

Filtros disponibles:
  · Rango de fechas
  · Tipos de formulario (cantidades, componentes, diario)
  · Estado de las anotaciones
  · Incluir/excluir fotos en el informe
"""

import io
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import (
    load_cantidades, load_componentes, load_reporte_diario, load_contrato,
    load_fotos_cantidades, load_fotos_componentes, load_fotos_reporte,
)
from pdf_generator import generate_pdf_bitacora
from ui import kpi, section_badge

# Tipos de formulario
_TIPOS = {
    "Cantidades de Obra":         "cantidades",
    "Componentes Transversales":  "componentes",
    "Reporte Diario":             "diario",
}

# Mapeo estado filtro → lista
_FILTRO_ESTADOS = {
    "Todos":                      None,
    "Solo Aprobados":             ["APROBADO"],
    "Revisados y Aprobados":      ["REVISADO", "APROBADO"],
    "Solo Borradores":            ["BORRADOR"],
    "Solo Devueltos":             ["DEVUELTO"],
}

# Columnas de vista previa por tipo
_PREVIEW_COLS = {
    "cantidades":  ['folio', 'usuario_qfield', 'id_tramo', 'civ',
                    'tipo_actividad', 'item_pago', 'cantidad', 'unidad', 'estado'],
    "componentes": ['folio', 'usuario_qfield', 'id_tramo',
                    'tipo_componente', 'tipo_actividad', 'cantidad', 'unidad', 'estado'],
    "diario":      ['folio', 'usuario_qfield', 'fecha_reporte',
                    'observaciones', 'estado'],
}


def _build_excel(frames: dict[str, pd.DataFrame]) -> bytes:
    """Genera Excel multi-hoja con openpyxl."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        for sheet_name, df in frames.items():
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return buf.getvalue()


def page_generar_pdf(perfil: dict) -> None:
    section_badge("Generar Informe", "teal")
    st.markdown("### Exportación de Bitácora Digital")

    # ── Filtros de período y contenido ────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Período y Contenido</div>', unsafe_allow_html=True)
    with st.form("form_informe"):
        ff1, ff2 = st.columns(2)
        with ff1:
            fi = st.date_input("Desde",
                               value=date.today() - timedelta(days=7),
                               key="inf_fi")
        with ff2:
            ff = st.date_input("Hasta", value=date.today(), key="inf_ff")

        fo1, fo2, fo3 = st.columns(3)
        with fo1:
            tipos_sel = st.multiselect(
                "Tipos de formulario a incluir",
                list(_TIPOS.keys()),
                default=["Cantidades de Obra"],
                key="inf_tipos",
            )
        with fo2:
            estado_f = st.selectbox(
                "Estado de las anotaciones",
                list(_FILTRO_ESTADOS.keys()),
                key="inf_est",
            )
        with fo3:
            formato = st.selectbox(
                "Formato de exportación",
                ["PDF", "CSV", "Excel (multi-hoja)"],
                key="inf_fmt",
            )

        fa1, fa2 = st.columns(2)
        with fa1:
            tramo_f = st.text_input("Filtrar por Tramo", key="inf_tramo")
        with fa2:
            user_f  = st.text_input("Filtrar por Usuario / Inspector", key="inf_user")

        aplicar = st.form_submit_button("Aplicar filtros", type="primary",
                                        use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if not aplicar and 'inf_loaded' not in st.session_state:
        st.info("Define el período y presiona **Aplicar filtros** para previsualizar registros.")
        return
    st.session_state['inf_loaded'] = True

    estados_q = _FILTRO_ESTADOS[estado_f]

    # ── Cargar datos ───────────────────────────────────────
    import re

    frames: dict[str, pd.DataFrame] = {}
    for tipo_label in tipos_sel:
        tipo_key = _TIPOS[tipo_label]
        if tipo_key == "cantidades":
            df_t = load_cantidades(
                estados=estados_q,
                fecha_ini=fi.isoformat(),
                fecha_fin=ff.isoformat(),
            )
        elif tipo_key == "componentes":
            df_t = load_componentes(
                estados=estados_q,
                fecha_ini=fi.isoformat(),
                fecha_fin=ff.isoformat(),
            )
        elif tipo_key == "diario":
            df_t = load_reporte_diario(
                estados=estados_q,
                fecha_ini=fi.isoformat(),
                fecha_fin=ff.isoformat(),
            )
        else:
            df_t = pd.DataFrame()

        # Filtros opcionales de tramo / usuario
        if tramo_f.strip() and not df_t.empty and 'id_tramo' in df_t.columns:
            df_t = df_t[df_t['id_tramo'].astype(str).str.contains(
                re.escape(tramo_f.strip()), case=False, na=False
            )]
        if user_f.strip() and not df_t.empty and 'usuario_qfield' in df_t.columns:
            df_t = df_t[df_t['usuario_qfield'].astype(str).str.contains(
                re.escape(user_f.strip()), case=False, na=False
            )]

        frames[tipo_label] = df_t

    contrato        = load_contrato()
    total_registros = sum(len(df) for df in frames.values())

    # ── KPIs de vista previa ───────────────────────────────
    if total_registros > 0:
        apr = sum(len(df[df['estado'] == 'APROBADO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)
        rev = sum(len(df[df['estado'] == 'REVISADO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)
        dev = sum(len(df[df['estado'] == 'DEVUELTO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)
        bor = total_registros - apr - rev - dev

        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: kpi("Registros totales",  str(total_registros), card_accent="accent-blue")
        with p2: kpi("Aprobados",  str(apr),  accent="kpi-green",  card_accent="accent-green")
        with p3: kpi("Revisados",  str(rev),  accent="kpi-blue",   card_accent="accent-blue")
        with p4: kpi("Borradores", str(bor),  accent="kpi-orange" if bor else "")
        with p5: kpi("Devueltos",  str(dev),
                     accent="kpi-red"       if dev else "",
                     card_accent="accent-red" if dev else "")

        st.divider()

        # Vista previa por tipo
        section_badge("Vista previa de registros", "teal")
        for tipo_label, df_prev in frames.items():
            if df_prev.empty:
                st.caption(f"{tipo_label}: sin registros")
                continue
            tipo_key = _TIPOS[tipo_label]
            cols_p = [c for c in _PREVIEW_COLS.get(tipo_key, []) if c in df_prev.columns]
            st.markdown(f"**{tipo_label}** — {len(df_prev)} registro(s)")
            st.dataframe(
                df_prev[cols_p].head(10) if cols_p else df_prev.head(10),
                hide_index=True,
                use_container_width=True,
            )
            if len(df_prev) > 10:
                st.caption(f"Mostrando 10 de {len(df_prev)} registros")

    else:
        st.info("Sin registros para el período y filtros seleccionados.")

    st.divider()

    # ── Botones de exportación ─────────────────────────────
    fecha_tag = f"{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}"
    disabled  = total_registros == 0

    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        generar = st.button(
            f"Generar {formato if not disabled else 'Informe'}",
            type="primary",
            use_container_width=True,
            disabled=disabled,
        )
    with col_msg:
        if disabled:
            st.info("Ajusta los filtros para incluir registros en el informe.")

    if generar and not disabled:

        # ── PDF ────────────────────────────────────────────
        if formato == "PDF":
            # Seleccionar df principal: preferir reporte diario, luego cantidades
            df_pdf = frames.get("Reporte Diario", pd.DataFrame())
            if df_pdf.empty:
                df_pdf = frames.get("Cantidades de Obra", pd.DataFrame())
            if df_pdf.empty and frames:
                df_pdf = next(iter(frames.values()))

            # Recopilar observaciones del reporte diario
            observaciones_pdf = ""
            if not frames.get("Reporte Diario", pd.DataFrame()).empty:
                df_d = frames["Reporte Diario"]
                if 'observaciones' in df_d.columns:
                    obs_list = df_d['observaciones'].dropna().astype(str).tolist()
                    observaciones_pdf = " | ".join(o for o in obs_list if o.strip())

            # Cargar fotos desde Supabase por folio para todos los tipos activos
            fotos_urls_pdf: list[str] = []
            for tipo_label, df_t in frames.items():
                if df_t.empty or 'folio' not in df_t.columns:
                    continue
                folios_t = tuple(df_t['folio'].dropna().tolist())
                if not folios_t:
                    continue
                tipo_key = _TIPOS.get(tipo_label, "")
                if tipo_key == "cantidades":
                    df_fot = load_fotos_cantidades(folios_t)
                elif tipo_key == "componentes":
                    df_fot = load_fotos_componentes(folios_t)
                elif tipo_key == "diario":
                    df_fot = load_fotos_reporte(folios_t)
                else:
                    df_fot = pd.DataFrame()
                if not df_fot.empty and 'foto_url' in df_fot.columns:
                    fotos_urls_pdf.extend(
                        df_fot['foto_url'].dropna().tolist()
                    )

            with st.spinner("Generando Bitácora PDF…"):
                pdf_bytes = generate_pdf_bitacora(
                    df_pdf, contrato, fi, ff,
                    "Bitácora Consolidada", [],
                    observaciones=observaciones_pdf,
                    fotos_urls=fotos_urls_pdf[:12],
                )
            if pdf_bytes:
                nombre = f"Bitacora_IDU-1556-2025_{fecha_tag}.pdf"
                st.success(
                    f"Bitácora PDF generada — {total_registros} registros"
                    + (f" · {len(fotos_urls_pdf)} foto(s)" if fotos_urls_pdf else "")
                )
                st.download_button(
                    "Descargar Bitácora PDF",
                    data=pdf_bytes,
                    file_name=nombre,
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            else:
                st.error(
                    "No se pudo generar el PDF. "
                    "El error detallado queda en los logs del servidor. "
                    "Causas comunes: registros con datos inconsistentes, "
                    "fotos con URL no accesible, o error interno de ReportLab."
                )

        # ── CSV ────────────────────────────────────────────
        elif formato == "CSV":
            if len(frames) == 1:
                df_csv = next(iter(frames.values()))
                nombre = f"Informe_IDU-1556-2025_{fecha_tag}.csv"
                csv_bytes = df_csv.to_csv(index=False).encode('utf-8')
            else:
                partes = []
                for label, df_l in frames.items():
                    if not df_l.empty:
                        df_l = df_l.copy()
                        df_l.insert(0, 'tipo_formulario', label)
                        partes.append(df_l)
                combined  = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
                nombre    = f"Informe_IDU-1556-2025_{fecha_tag}.csv"
                csv_bytes = combined.to_csv(index=False).encode('utf-8')

            st.success(f"CSV generado — {total_registros} registros")
            st.download_button(
                "Descargar CSV",
                data=csv_bytes,
                file_name=nombre,
                mime="text/csv",
                type="primary",
                use_container_width=True,
            )

        # ── Excel ──────────────────────────────────────────
        elif formato == "Excel (multi-hoja)":
            try:
                with st.spinner("Generando Excel…"):
                    xl_bytes = _build_excel(frames)
                nombre = f"Informe_IDU-1556-2025_{fecha_tag}.xlsx"
                st.success(
                    f"Excel generado — {total_registros} registros "
                    f"en {len(frames)} hoja(s)"
                )
                st.download_button(
                    "Descargar Excel",
                    data=xl_bytes,
                    file_name=nombre,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True,
                )
            except ImportError:
                st.error("openpyxl no está instalado:")
                st.code("pip install openpyxl", language="bash")
