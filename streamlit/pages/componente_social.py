"""
pages/componente_social.py — Componente Social
"""

import streamlit as st

from ui import section_badge
from pages._componentes_base import panel_componentes


def page_social(perfil: dict) -> None:
    section_badge("Componente Social", "orange")
    st.markdown("### Registros del Componente Social")
    panel_componentes(perfil, filtro_tipo='social')
