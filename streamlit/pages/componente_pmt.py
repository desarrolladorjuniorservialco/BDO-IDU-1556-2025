"""
pages/componente_pmt.py — Componente PMT (ítems de ejecución en campo)
Diferente de seguimiento_pmts: aquí se revisan los registros de campo
vinculados a los Planes de Manejo de Tránsito.
"""

import streamlit as st

from ui import section_badge
from pages._componentes_base import panel_componentes


def page_componente_pmt(perfil: dict) -> None:
    section_badge("Componente PMT — Planes de Manejo de Tránsito", "purple")
    st.markdown("### Ejecución de Items PMT")
    st.caption(
        "Seguimiento de los ítems de ejecución registrados en campo "
        "para el Plan de Manejo de Tránsito."
    )
    panel_componentes(perfil, filtro_tipo='pmt')
