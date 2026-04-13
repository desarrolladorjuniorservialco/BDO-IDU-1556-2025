"""
pages/generar_pdf.py — Página: Generar Informe de Bitácora
Exporta registros en PDF, CSV o Excel (multi-hoja) según filtros.
"""

import io
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from database import (
    load_cantidades, load_componentes, load_reporte_diario, load_contrato,
)
from pdf_generator import generate_pdf_bitacora
from ui import kpi, section_badge

# Tipos de formulario disponibles
_TIPOS = {
    "Cantidades de Obra":       "cantidades",
    "Componentes Transversales":"componentes",
    "Reporte Diario":           "diario",
}

# Mapeo estado filtro → lista
_FILTRO_ESTADOS = {
    "Todos":               None,
    "Solo Aprobados":      ["APROBADO"],
    "Revisados y Aprobados": ["REVISADO", "APROBADO"],
    "Borradores":          ["BORRADOR"],
    "Devueltos":           ["DEVUELTO"],
}

# Columnas a mostrar en vista previa por tipo
_PREVIEW_COLS = {
    "cantidades":  ['folio', 'usuario_qfield', 'id_tramo', 'civ',
                    'tipo_actividad', 'cantidad', 'unidad', 'estado'],
    "componentes": ['folio', 'usuario_qfield', 'id_tramo', 'componente',
                    'tipo_actividad', 'estado'],
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

    # ── Filtros ────────────────────────────────────────────────
    ff1, ff2 = st.columns(2)
    with ff1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7), key="inf_fi")
    with ff2: ff = st.date_input("Hasta", value=date.today(), key="inf_ff")

    fo1, fo2, fo3 = st.columns(3)
    with fo1:
        tipos_sel = st.multiselect(
            "Tipos de formulario",
            list(_TIPOS.keys()),
            default=["Cantidades de Obra"],
            key="inf_tipos",
        )
    with fo2:
        estado_f = st.selectbox("Estado", list(_FILTRO_ESTADOS.keys()), key="inf_est")
    with fo3:
        formato = st.selectbox("Formato de exportación",
                               ["PDF", "CSV", "Excel (multi-hoja)"], key="inf_fmt")

    estados_q = _FILTRO_ESTADOS[estado_f]

    # ── Cargar datos según selección ───────────────────────────
    frames: dict[str, pd.DataFrame] = {}
    for tipo_label in tipos_sel:
        tipo_key = _TIPOS[tipo_label]
        if tipo_key == "cantidades":
            frames[tipo_label] = load_cantidades(
                estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        elif tipo_key == "componentes":
            frames[tipo_label] = load_componentes(
                estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())
        elif tipo_key == "diario":
            frames[tipo_label] = load_reporte_diario(
                estados=estados_q, fecha_ini=fi.isoformat(), fecha_fin=ff.isoformat())

    contrato = load_contrato()
    total_registros = sum(len(df) for df in frames.values())

    # ── KPIs de vista previa ───────────────────────────────────
    if total_registros > 0:
        apr = sum(len(df[df['estado'] == 'APROBADO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)
        rev = sum(len(df[df['estado'] == 'REVISADO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)
        dev = sum(len(df[df['estado'] == 'DEVUELTO']) for df in frames.values()
                  if not df.empty and 'estado' in df.columns)

        p1, p2, p3, p4 = st.columns(4)
        with p1: kpi("Registros totales",  str(total_registros), card_accent="accent-blue")
        with p2: kpi("Aprobados", str(apr), accent="kpi-green",  card_accent="accent-green")
        with p3: kpi("Revisados", str(rev), accent="kpi-blue",   card_accent="accent-blue")
        with p4: kpi("Devueltos", str(dev),
                     accent="kpi-red" if dev > 0 else "",
                     card_accent="accent-red" if dev > 0 else "")

        st.divider()
        st.markdown("#### Vista previa de registros")
        for tipo_label, df in frames.items():
            if df.empty:
                continue
            tipo_key = _TIPOS[tipo_label]
            cols_prev = [c for c in _PREVIEW_COLS.get(tipo_key, []) if c in df.columns]
            st.markdown(f"**{tipo_label}** — {len(df)} registros")
            st.dataframe(df[cols_prev].head(15) if cols_prev else df.head(15),
                         hide_index=True, use_container_width=True)
            if len(df) > 15:
                st.caption(f"Mostrando 15 de {len(df)} registros")

    st.divider()

    # ── Botones de exportación ─────────────────────────────────
    fecha_tag = f"{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}"
    disabled  = total_registros == 0

    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        generar = st.button(f"Generar {formato}", type="primary",
                            use_container_width=True, disabled=disabled)
    with col_msg:
        if disabled:
            st.info("Sin registros para el período y filtros seleccionados")

    if generar and not disabled:
        # ── PDF ────────────────────────────────────────────────
        if formato == "PDF":
            df_pdf = frames.get("Cantidades de Obra", pd.DataFrame())
            if df_pdf.empty and frames:
                df_pdf = next(iter(frames.values()))
            with st.spinner("Generando PDF..."):
                pdf_bytes = generate_pdf_bitacora(
                    df_pdf, contrato, fi, ff,
                    "Bitácora Consolidada", []
                )
            if pdf_bytes:
                nombre = f"Bitacora_IDU-1556-2025_{fecha_tag}.pdf"
                st.success(f"PDF generado — {total_registros} registros")
                st.download_button("Descargar PDF", data=pdf_bytes,
                                   file_name=nombre, mime="application/pdf",
                                   type="primary", use_container_width=True)
            else:
                st.error("No se pudo generar el PDF. Verifica que reportlab esté instalado:")
                st.code("pip install reportlab", language="bash")

        # ── CSV ────────────────────────────────────────────────
        elif formato == "CSV":
            if len(frames) == 1:
                df_csv = next(iter(frames.values()))
                nombre = f"Informe_IDU-1556-2025_{fecha_tag}.csv"
                csv_bytes = df_csv.to_csv(index=False).encode('utf-8')
            else:
                # Combinar todas las hojas con columna de tipo
                partes = []
                for label, df in frames.items():
                    if not df.empty:
                        df = df.copy()
                        df.insert(0, 'tipo_formulario', label)
                        partes.append(df)
                combined = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
                nombre = f"Informe_IDU-1556-2025_{fecha_tag}.csv"
                csv_bytes = combined.to_csv(index=False).encode('utf-8')
            st.success(f"CSV generado — {total_registros} registros")
            st.download_button("Descargar CSV", data=csv_bytes,
                               file_name=nombre, mime="text/csv",
                               type="primary", use_container_width=True)

        # ── Excel ──────────────────────────────────────────────
        elif formato == "Excel (multi-hoja)":
            try:
                with st.spinner("Generando Excel..."):
                    xl_bytes = _build_excel(frames)
                nombre = f"Informe_IDU-1556-2025_{fecha_tag}.xlsx"
                st.success(f"Excel generado — {total_registros} registros en {len(frames)} hoja(s)")
                st.download_button(
                    "Descargar Excel", data=xl_bytes, file_name=nombre,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary", use_container_width=True,
                )
            except ImportError:
                st.error("openpyxl no está instalado:")
                st.code("pip install openpyxl", language="bash")
