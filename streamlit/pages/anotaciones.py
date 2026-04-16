"""
pages/anotaciones.py — Página: Anotaciones Generales de Bitácora
Registro libre de notas no vinculadas a reportes de QFieldCloud.

Flujo:
  - Todos los roles autenticados pueden leer el historial (chat).
  - El rol 'supervisor' solo puede leer; el compositor no se renderiza.
  - El resto de roles pueden insertar anotaciones.

SEGURIDAD:
  - Inserción vía get_user_client() → RLS activo en Supabase.
  - Rol 'supervisor' bloqueado en RLS además de en UI.
  - max_chars=2000 en st.chat_input() limita el payload.
  - Los valores de tramo/civ/pk se insertan como parámetros (sin
    concatenación SQL directa).
"""

import logging
from datetime import date

import streamlit as st

from database import load_anotaciones_generales, get_user_client, clear_cache
from ui import section_badge, esc

_log = logging.getLogger(__name__)


def page_anotaciones(perfil: dict) -> None:
    """
    Página principal de Anotaciones Generales.

    perfil: dict con claves id, nombre, rol, empresa
            (cargado desde st.session_state['perfil'] en app.py)
    """
    rol          = perfil['rol']
    puede_anotar = rol != 'supervisor'

    section_badge("Anotaciones Generales", "purple")
    st.markdown("### Bitácora General")

    # ── Historial ──────────────────────────────────────────────
    df = load_anotaciones_generales()

    chat_container = st.container(height=500)
    with chat_container:
        if df.empty:
            st.caption("Aún no hay anotaciones registradas.")
        else:
            for _, row in df.iterrows():
                nombre  = str(row.get('usuario_nombre', '—'))
                rol_u   = str(row.get('usuario_rol',    '') or '')
                empresa = str(row.get('usuario_empresa','') or '')
                fecha   = str(row.get('fecha',          '') or '')
                tramo   = str(row.get('tramo',          '') or '')
                civ     = str(row.get('civ',            '') or '')
                pk      = str(row.get('pk',             '') or '')
                texto   = str(row.get('anotacion',      ''))
                ts      = str(row.get('created_at',     ''))[:16].replace('T', ' ')

                with st.chat_message(nombre):
                    # ── Fila de metadatos — todos los valores escapados ──
                    pills = (
                        f'<span class="info-pill">{esc(nombre)}</span>'
                        f'<span class="info-pill blue">'
                        f'{esc(rol_u.replace("_", " ").title())}'
                        f'</span>'
                    )
                    if empresa:
                        pills += f'<span class="info-pill teal">{esc(empresa)}</span>'
                    if fecha:
                        pills += f'<span class="info-pill">{esc(fecha)}</span>'
                    if tramo:
                        pills += f'<span class="info-pill orange">Tramo: {esc(tramo)}</span>'
                    if civ:
                        pills += f'<span class="info-pill teal">CIV: {esc(civ)}</span>'
                    if pk:
                        pills += f'<span class="info-pill">PK: {esc(pk)}</span>'

                    st.markdown(
                        f'<div class="record-meta-row">{pills}</div>',
                        unsafe_allow_html=True,
                    )
                    st.write(texto)   # st.write() renderiza texto plano de forma segura
                    st.caption(esc(ts))

    # ── Compositor (no se renderiza para supervisor) ────────────
    if not puede_anotar:
        return

    # Fila de metadatos — viven en session_state fuera de un form
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        ag_fecha = st.date_input(
            "Fecha",
            value=date.today(),
            key="ag_fecha",
        )
    with mc2:
        ag_tramo = st.text_input(
            "Tramo",
            key="ag_tramo",
            placeholder="Opcional",
            max_chars=50,
        )
    with mc3:
        ag_civ = st.text_input(
            "CIV",
            key="ag_civ",
            placeholder="Opcional",
            max_chars=50,
        )
    with mc4:
        ag_pk = st.text_input(
            "PK",
            key="ag_pk",
            placeholder="Opcional",
            max_chars=20,
        )

    # Chat input fijo al fondo de la página
    texto_nuevo = st.chat_input(
        "Escribe tu anotación...",
        max_chars=2000,
    )

    if texto_nuevo:
        _insertar_anotacion(
            texto  = texto_nuevo.strip(),
            fecha  = ag_fecha,
            tramo  = ag_tramo.strip() or None,
            civ    = ag_civ.strip()   or None,
            pk     = ag_pk.strip()    or None,
            perfil = perfil,
        )


def _insertar_anotacion(
    texto:  str,
    fecha:  date,
    tramo:  str | None,
    civ:    str | None,
    pk:     str | None,
    perfil: dict,
) -> None:
    """
    Inserta una anotación en Supabase y recarga la página.
    Usa get_user_client() para que RLS esté activo.
    Limpia los campos opcionales de session_state tras el envío.
    """
    if not texto.strip():
        return

    try:
        sb = get_user_client(st.session_state.get('_access_token', ''))
        sb.table('anotaciones_generales').insert({
            'fecha':           fecha.isoformat(),
            'tramo':           tramo,
            'civ':             civ,
            'pk':              pk,
            'anotacion':       texto,
            'usuario_id':      perfil['id'],
            'usuario_nombre':  perfil.get('nombre', ''),
            'usuario_rol':     perfil.get('rol',    ''),
            'usuario_empresa': perfil.get('empresa', ''),
        }).execute()

        # Limpiar campos opcionales para la siguiente anotación
        for key in ('ag_tramo', 'ag_civ', 'ag_pk'):
            st.session_state.pop(key, None)

        clear_cache()
        st.rerun()

    except Exception:
        _log.exception(
            "Error al insertar anotación — usuario_id=%s",
            perfil.get('id', '?'),
        )
        st.error("No fue posible guardar la anotación. Intenta de nuevo.")
