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
import os

import psutil
import streamlit as st

# ── Infraestructura ────────────────────────────────────────
from styles        import CSS, CSS_LIGHT_OVERRIDE, CSS_DARK_OVERRIDE
from auth          import login
from sidebar       import sidebar
from config        import NAV_ACCESS
from session_store import restore_session

# ── Páginas ────────────────────────────────────────────────
from pages.estado_actual        import page_estado_actual
from pages.anotaciones          import page_anotaciones
from pages.anotaciones_diario   import page_anotaciones_diario
from pages.generar_pdf          import page_generar_pdf
from pages.mapa                 import page_mapa
from pages.presupuesto          import page_presupuesto
from pages.reporte_cantidades   import page_reporte_cantidades
from pages.componente_ambiental import page_ambiental
from pages.componente_social    import page_social
from pages.componente_pmt       import page_componente_pmt
from pages.seguimiento_pmts     import page_seguimiento_pmts
from pages.correspondencia      import page_correspondencia

# Logger interno — los errores van a los logs del servidor, no al usuario
_log = logging.getLogger(__name__)


@st.cache_resource
def _get_process() -> psutil.Process:
    return psutil.Process(os.getpid())


def _consumo_ram_mb() -> float:
    return _get_process().memory_info().rss / (1024 ** 2)

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

# Inyectar override de variables CSS según el tema activo de Streamlit.
# Al insertarse DESPUÉS del CSS principal, el :root posterior gana en cascada
# sobre el @media prefers-color-scheme — sin JS ni iframes.
# st.get_option("theme.base") devuelve el tema activo de la sesión actual.
# (incluye el valor del toggle UI del usuario, no solo config.toml).
_active_theme = st.get_option("theme.base") or "light"
st.markdown(
    CSS_DARK_OVERRIDE if _active_theme == "dark" else CSS_LIGHT_OVERRIDE,
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════
# MAPA DE PÁGINAS
# ══════════════════════════════════════════════════════════════

PAGE_MAP: dict = {
    "Estado Actual":              page_estado_actual,
    "Anotaciones":                page_anotaciones,
    "Anotaciones Diario":         page_anotaciones_diario,
    "Generar Informe":            page_generar_pdf,
    "Mapa Ejecución":             page_mapa,
    "Seguimiento Presupuesto":    page_presupuesto,
    "Correspondencia":            page_correspondencia,
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
            'operativo', 'obra', 'interventoria', 'supervision', 'admin',
        }
        and isinstance(perfil.get('nombre'), str)
    )

# ══════════════════════════════════════════════════════════════
# LOOP PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main() -> None:
    # ── 1. Restaurar sesión desde URL (recarga del navegador) ──
    if 'user' not in st.session_state:
        sid = st.query_params.get('sid', '')
        if sid:
            data = restore_session(sid)
            if data:
                st.session_state['user']          = data['user']
                st.session_state['perfil']        = data['perfil']
                st.session_state['_access_token'] = data['access_token']
                st.session_state['_session_id']   = sid
                if data.get('current_page'):
                    st.session_state['current_page'] = data['current_page']
            else:
                # Sesión expirada o inválida — limpiar la URL antes de mostrar login
                st.query_params.clear()

    # ── 2. Verificar sesión ────────────────────────────────
    if 'user' not in st.session_state or 'perfil' not in st.session_state:
        login()
        return

    perfil = st.session_state['perfil']

    # ── 3. Validar integridad del perfil ───────────────────
    if not _perfil_integro(perfil):
        st.error("Sesión inválida. Por favor, inicia sesión nuevamente.")
        for k in ['user', 'perfil', 'current_page']:
            st.session_state.pop(k, None)
        st.rerun()
        return

    # ── 4. Renderizar sidebar y obtener página activa ──────
    page = sidebar(perfil)

    with st.sidebar:
        st.divider()
        st.markdown("### 📊 Monitoreo del Sistema")
        st.metric(label="Consumo de RAM", value=f"{_consumo_ram_mb():.2f} MB")
        st.caption("Límite en Streamlit Cloud: ~1000 MB")

    # ── 5. Verificar autorización (server-side) ────────────
    if not _authorized(perfil, page):
        st.error("No tienes permiso para acceder a esta sección.")
        _log.warning(
            "Acceso no autorizado: usuario=%s rol=%s página=%s",
            perfil.get('id', '?'), perfil.get('rol', '?'), page,
        )
        return

    # ── 6. Renderizar página ───────────────────────────────
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
