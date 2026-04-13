"""
pages/generar_pdf.py — Página: Generación de PDF de Bitácora
"""

from datetime import date, timedelta

import streamlit as st

from database import load_cantidades, load_contrato
from pdf_generator import generate_pdf_bitacora
from ui import kpi, section_badge


def page_generar_pdf(perfil: dict) -> None:
    section_badge("Generar PDF de Bitácora", "teal")
    st.markdown("### Exportación de Bitácora Digital")

    c1, c2 = st.columns(2)
    with c1: fi = st.date_input("Desde", value=date.today() - timedelta(days=7))
    with c2: ff = st.date_input("Hasta", value=date.today())

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        tipo_reporte = st.selectbox("Tipo de reporte", [
            "Bitácora semanal completa",
            "Solo actividades aprobadas",
            "Solo actividades revisadas",
            "Todas las anotaciones",
        ])
    with col_opt2:
        secciones = st.multiselect(
            "Secciones a incluir",
            ["Registro de actividades", "Firmas"],
            default=["Registro de actividades", "Firmas"],
        )

    filtro_estados = {
        "Bitácora semanal completa":  None,
        "Solo actividades aprobadas": ["APROBADO"],
        "Solo actividades revisadas": ["REVISADO", "APROBADO"],
        "Todas las anotaciones":      None,
    }.get(tipo_reporte)

    df       = load_cantidades(estados=filtro_estados,
                               fecha_ini=fi.isoformat(),
                               fecha_fin=ff.isoformat())
    contrato = load_contrato()

    # ── Vista previa ───────────────────────────────────────
    if not df.empty:
        apr = len(df[df['estado'] == 'APROBADO']) if 'estado' in df else 0
        rev = len(df[df['estado'] == 'REVISADO']) if 'estado' in df else 0
        dev = len(df[df['estado'] == 'DEVUELTO']) if 'estado' in df else 0

        p1, p2, p3, p4 = st.columns(4)
        with p1: kpi("Registros en el reporte", str(len(df)), card_accent="accent-blue")
        with p2: kpi("Aprobados", str(apr), accent="kpi-green", card_accent="accent-green")
        with p3: kpi("Revisados", str(rev), accent="kpi-blue",  card_accent="accent-blue")
        with p4: kpi("Devueltos", str(dev),
                     accent="kpi-red" if dev > 0 else "",
                     card_accent="accent-red" if dev > 0 else "")

        st.divider()
        st.markdown("#### Vista previa de registros")
        cols_prev = ['folio', 'usuario_qfield', 'id_tramo', 'civ',
                     'tipo_actividad', 'cantidad', 'unidad', 'estado']
        cols_prev = [c for c in cols_prev if c in df.columns]
        st.dataframe(df[cols_prev].head(20), hide_index=True, use_container_width=True)
        if len(df) > 20:
            st.caption(f"Mostrando primeros 20 de {len(df)} registros")

    st.divider()

    # ── Generar PDF ────────────────────────────────────────
    col_btn, col_msg = st.columns([1, 3])
    with col_btn:
        generar = st.button("Generar PDF", type="primary",
                            use_container_width=True, disabled=df.empty)
    with col_msg:
        if df.empty:
            st.info("Sin registros para el período y filtro seleccionados")

    if generar and not df.empty:
        with st.spinner("Generando PDF..."):
            pdf_bytes = generate_pdf_bitacora(
                df, contrato, fi, ff, tipo_reporte, secciones
            )

        if pdf_bytes:
            nombre = (
                f"Bitacora_IDU-1556-2025_"
                f"{fi.strftime('%Y%m%d')}_{ff.strftime('%Y%m%d')}.pdf"
            )
            st.success(f"PDF generado — {len(df)} registros incluidos")
            st.download_button(
                label="Descargar PDF",
                data=pdf_bytes,
                file_name=nombre,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        else:
            st.error("No se pudo generar el PDF. Instala reportlab:")
            st.code("pip install reportlab", language="bash")
