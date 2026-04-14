"""
ui.py — Componentes de interfaz reutilizables
KPI cards, badges de estado, section badges y helpers de formato.

SEGURIDAD:
  - kpi() escapa label, value y sub para prevenir XSS almacenado.
    Los valores que provienen de la base de datos (nombres, descripciones,
    folios, etc.) se tratan como no confiables.
  - badge() solo acepta estados conocidos; cualquier otro valor se
    normaliza a 'badge-borrador' sin renderizar el texto crudo.
  - section_badge() usa solo el color como clase CSS; el label se escapa.
"""

import html as _html
import math
import streamlit as st

# Conjunto de estados válidos (whitelist)
_ESTADOS_VALIDOS = frozenset({'BORRADOR', 'REVISADO', 'APROBADO', 'DEVUELTO'})

# Colores de section_badge permitidos (whitelist)
_COLORES_VALIDOS = frozenset({'blue', 'green', 'red', 'orange', 'yellow', 'purple', 'teal'})


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


def esc(value) -> str:
    """Escapa caracteres HTML de un valor arbitrario. Uso interno."""
    return _html.escape(str(value) if value is not None else '')


# ══════════════════════════════════════════════════════════════
# BADGES
# ══════════════════════════════════════════════════════════════

def badge(estado: str) -> str:
    """
    Retorna el HTML de un badge de estado de registro.
    Solo renderiza el texto si el estado está en la whitelist.
    Cualquier valor no reconocido muestra 'BORRADOR' con clase neutra.
    """
    estado_upper = str(estado).upper() if estado else ''
    if estado_upper not in _ESTADOS_VALIDOS:
        # Estado desconocido: clase neutra, sin texto libre
        return '<span class="badge badge-borrador">—</span>'
    cls = {
        'BORRADOR': 'badge-borrador',
        'REVISADO': 'badge-revisado',
        'APROBADO': 'badge-aprobado',
        'DEVUELTO': 'badge-devuelto',
    }[estado_upper]
    return f'<span class="badge {cls}">{estado_upper}</span>'


def section_badge(label: str, color: str = "blue") -> None:
    """
    Renderiza un badge pill de sección al estilo IDU.
    El color se valida contra una whitelist; el label se escapa.
    Colores válidos: blue | green | red | orange | purple | teal
    """
    safe_color = color if color in _COLORES_VALIDOS else "blue"
    safe_label = esc(label)
    st.markdown(
        f'<div class="section-badge sb-{safe_color}">{safe_label}</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# KPI CARD
# ══════════════════════════════════════════════════════════════

# Clases CSS de valor permitidas (whitelist)
_ACCENT_VALIDOS = frozenset({
    '', 'kpi-blue', 'kpi-green', 'kpi-red', 'kpi-orange',
    'kpi-purple', 'kpi-teal', 'kpi-accent', 'kpi-warn',
    'kpi-danger', 'kpi-info',
})

# Clases CSS de tarjeta permitidas (whitelist)
_CARD_ACCENT_VALIDOS = frozenset({
    '', 'accent-blue', 'accent-green', 'accent-red',
    'accent-orange', 'accent-purple', 'accent-teal',
})


def kpi(
    label: str,
    value: str,
    sub: str = "",
    accent: str = "",
    card_accent: str = "",
) -> None:
    """
    Renderiza una tarjeta KPI con barra de color izquierda.

    Todos los valores de texto se escapan para prevenir XSS almacenado.
    Las clases CSS se validan contra whitelists.

    Parámetros:
        label       — Etiqueta superior
        value       — Valor principal (se escapa; no usar HTML intencional aquí)
        sub         — Subtexto opcional (se escapa)
        accent      — Clase CSS para el color del valor (whitelist)
        card_accent — Clase CSS para la barra lateral (whitelist)
    """
    safe_label      = esc(label)
    safe_value      = esc(value)
    safe_sub        = esc(sub) if sub else ""
    safe_accent     = accent      if accent      in _ACCENT_VALIDOS      else ""
    safe_card       = card_accent if card_accent in _CARD_ACCENT_VALIDOS else ""

    val_class  = f"kpi-value {safe_accent}" if safe_accent else "kpi-value"
    card_class = f"kpi-card {safe_card}"    if safe_card   else "kpi-card"
    sub_html   = f'<div class="kpi-sub">{safe_sub}</div>' if safe_sub else ""

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="kpi-label">{safe_label}</div>
            <div class="{val_class}">{safe_value}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
