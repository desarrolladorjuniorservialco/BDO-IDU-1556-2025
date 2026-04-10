"""
app.py — Orquestador principal · BDO IDU-1556-2025
Bitácora Digital de Obra — Contrato IDU-1556-2025 Grupo 4

Responsabilidades de este archivo:
  1. Configurar la página de Streamlit
  2. Inyectar el CSS global
  3. Registrar el mapa de páginas (PAGE_MAP)
  4. Ejecutar el loop principal con verificación de autorización

SEGURIDAD:
  - Toda página pasa por _authorized() antes de renderizarse.
  - Los errores internos se loguean pero no se exponen al usuario.
  - El perfil se re-valida en cada carga desde session_state.
"""

import inspect
import logging

import streamlit as st

# ── Infraestructura ────────────────────────────────────────
from styles  import CSS
from auth    import login
from sidebar import sidebar
from config  import NAV_ACCESS

# ── Páginas ────────────────────────────────────────────────
from pages.estado_actual        import page_estado_actual
from pages.anotaciones          import page_anotaciones
from pages.generar_pdf          import page_generar_pdf
from pages.mapa                 import page_mapa
from pages.presupuesto          import page_presupuesto
from pages.reporte_cantidades   import page_reporte_cantidades
from pages.componente_ambiental import page_ambiental
from pages.componente_social    import page_social
from pages.componente_pmt       import page_componente_pmt
from pages.seguimiento_pmts     import page_seguimiento_pmts

# Logger interno — los errores van a los logs del servidor, no al usuario
_log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="BDO · IDU-1556-2025",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# MAPA DE PÁGINAS
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
# CONTROL DE ACCESO
# ══════════════════════════════════════════════════════════════

def _authorized(perfil: dict, page: str) -> bool:
    """
    Verifica en el servidor que el rol del usuario tiene acceso a la página.
    Segunda línea de defensa: la primera es el sidebar que no muestra
    páginas no autorizadas; esta impide el acceso aunque se manipule
    la sesión para cambiar 'current_page'.
    """
    rol = perfil.get('rol', '')
    return rol in NAV_ACCESS.get(page, [])


def _perfil_integro(perfil: dict) -> bool:
    """Valida que el perfil tenga los campos mínimos esperados."""
    return (
        isinstance(perfil, dict)
        and isinstance(perfil.get('id'), str) and len(perfil['id']) > 0
        and isinstance(perfil.get('rol'), str) and perfil['rol'] in {
            'inspector', 'obra', 'residente', 'coordinador',
            'interventor', 'supervisor', 'admin',
        }
        and isinstance(perfil.get('nombre'), str)
    )

# ══════════════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main() -> None:
    # ── 1. Verificar sesión ────────────────────────────────
    if 'user' not in st.session_state or 'perfil' not in st.session_state:
        login()
        return

    perfil = st.session_state['perfil']

    # ── 2. Validar integridad del perfil ───────────────────
    if not _perfil_integro(perfil):
        st.error("Sesión inválida. Por favor, inicia sesión nuevamente.")
        for k in ['user', 'perfil', 'current_page']:
            st.session_state.pop(k, None)
        st.rerun()
        return

    # ── 3. Renderizar sidebar y obtener página activa ──────
    page = sidebar(perfil)

    # ── 4. Verificar autorización (server-side) ────────────
    if not _authorized(perfil, page):
        st.error("No tienes permiso para acceder a esta sección.")
        _log.warning(
            "Acceso no autorizado: usuario=%s rol=%s página=%s",
            perfil.get('id', '?'), perfil.get('rol', '?'), page,
        )
        return

    # ── 5. Renderizar página ───────────────────────────────
    fn = PAGE_MAP.get(page)
    if not fn:
        st.error("Página no disponible.")
        _log.error("Página '%s' no encontrada en PAGE_MAP", page)
        return

    try:
        if inspect.signature(fn).parameters:
            fn(perfil)
        else:
            fn()
    except Exception:
        # Loguear detalles internos, mostrar mensaje genérico al usuario
        _log.exception("Error al renderizar página '%s'", page)
        st.error("Ocurrió un error al cargar esta sección. Contacta al administrador.")


if __name__ == '__main__':
    main()
