"""
app.py — Orquestador principal · BDO IDU-1556-2025
Bitácora Digital de Obra — Contrato IDU-1556-2025 Grupo 4

Responsabilidades de este archivo:
  1. Configurar la página de Streamlit
  2. Inyectar el CSS global
  3. Registrar el mapa de páginas (PAGE_MAP)
  4. Ejecutar el loop principal (main)

Toda la lógica de negocio, UI y datos está en módulos separados:
  config.py        — Roles, navegación, APROBACION_CONFIG
  styles.py        — CSS completo (modo claro + oscuro)
  database.py      — Supabase client y data loaders
  ui.py            — kpi(), badge(), section_badge()
  auth.py          — login(), logout()
  sidebar.py       — Navegación lateral
  pdf_generator.py — Generación de PDF con reportlab
  pages/           — Una función de página por archivo
"""

import inspect

import streamlit as st

# ── Infraestructura ────────────────────────────────────────
from styles  import CSS
from auth    import login
from sidebar import sidebar

# ── Páginas ────────────────────────────────────────────────
from pages.estado_actual       import page_estado_actual
from pages.anotaciones         import page_anotaciones
from pages.generar_pdf         import page_generar_pdf
from pages.mapa                import page_mapa
from pages.presupuesto         import page_presupuesto
from pages.reporte_cantidades  import page_reporte_cantidades
from pages.componente_ambiental import page_ambiental
from pages.componente_social   import page_social
from pages.componente_pmt      import page_componente_pmt
from pages.seguimiento_pmts    import page_seguimiento_pmts

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="BDO · IDU-1556-2025",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global (modo claro + oscuro con variables CSS)
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MAPA DE PÁGINAS
# Nombre de página (usado en navegación) → función de página
# ══════════════════════════════════════════════════════════════

PAGE_MAP: dict = {
    "Estado Actual":              page_estado_actual,
    "Anotaciones":                page_anotaciones,
    "Generar PDF":                page_generar_pdf,
    "Mapa de Obra":               page_mapa,
    "Seguimiento Presupuesto":    page_presupuesto,
    "Reporte Cantidades":         page_reporte_cantidades,
    "Componente Ambiental - SST": page_ambiental,
    "Componente Social":          page_social,
    "Componente PMT":             page_componente_pmt,
    "Seguimiento PMTs":           page_seguimiento_pmts,
}

# ══════════════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main() -> None:
    # Mostrar pantalla de login si no hay sesión activa
    if 'user' not in st.session_state:
        login()
        return

    perfil = st.session_state['perfil']
    page   = sidebar(perfil)          # renderiza sidebar y retorna página activa

    fn = PAGE_MAP.get(page)
    if not fn:
        st.error(f"Página '{page}' no encontrada en PAGE_MAP")
        return

    try:
        # Pasar perfil si la función lo acepta
        if inspect.signature(fn).parameters:
            fn(perfil)
        else:
            fn()
    except Exception as e:
        st.error(f"Error al cargar la página '{page}': {e}")
        raise  # para ver el traceback completo en los logs


if __name__ == '__main__':
    main()
