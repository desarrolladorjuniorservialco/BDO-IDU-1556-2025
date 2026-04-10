"""
ui.py — Componentes de interfaz reutilizables
KPI cards, badges de estado, section badges y helpers de formato.
"""

import math
import streamlit as st


# ══════════════════════════════════════════════════════════════
# HELPERS DE FORMATO
# ══════════════════════════════════════════════════════════════

def safe_float(val) -> float | None:
    """Convierte val a float; retorna None si es NaN o no convertible."""
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


# ══════════════════════════════════════════════════════════════
# BADGES
# ══════════════════════════════════════════════════════════════

def badge(estado: str) -> str:
    """
    Retorna el HTML de un badge de estado de registro.
    Valores esperados: BORRADOR | REVISADO | APROBADO | DEVUELTO
    """
    cls = {
        'BORRADOR': 'badge-borrador',
        'REVISADO': 'badge-revisado',
        'APROBADO': 'badge-aprobado',
        'DEVUELTO': 'badge-devuelto',
    }.get(estado, 'badge-borrador')
    return f'<span class="badge {cls}">{estado}</span>'


def section_badge(label: str, color: str = "blue") -> None:
    """
    Renderiza un badge pill de sección al estilo IDU.
    Colores válidos: blue | green | red | orange | purple | teal
    """
    st.markdown(
        f'<div class="section-badge sb-{color}">{label}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# KPI CARD
# ══════════════════════════════════════════════════════════════

def kpi(
    label: str,
    value: str,
    sub: str = "",
    accent: str = "",
    card_accent: str = "",
) -> None:
    """
    Renderiza una tarjeta KPI con barra de color izquierda.

    Parámetros:
        label       — Etiqueta superior (texto pequeño)
        value       — Valor principal (texto grande)
        sub         — Subtexto opcional debajo del valor
        accent      — Clase CSS para el color del valor
                      (kpi-blue | kpi-green | kpi-red | kpi-orange |
                       kpi-purple | kpi-teal | kpi-accent | kpi-warn | kpi-danger | kpi-info)
        card_accent — Clase CSS para la barra lateral de la tarjeta
                      (accent-blue | accent-green | accent-red | accent-orange |
                       accent-purple | accent-teal)
    """
    val_class  = f"kpi-value {accent}" if accent else "kpi-value"
    card_class = f"kpi-card {card_accent}" if card_accent else "kpi-card"
    sub_html   = f'<div class="kpi-sub">{sub}</div>' if sub else ""

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="kpi-label">{label}</div>
            <div class="{val_class}">{value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
