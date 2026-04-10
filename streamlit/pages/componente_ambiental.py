"""
pages/componente_ambiental.py — Componente Ambiental y SST
"""

import streamlit as st

from ui import section_badge
from pages._componentes_base import panel_componentes


def page_ambiental(perfil: dict) -> None:
    section_badge("Componente Ambiental y SST", "green")
    st.markdown("### Registros Ambientales y de Seguridad")
    panel_componentes(perfil, filtro_tipo='ambiental')
