"""
pages/anotaciones.py — Página: Anotaciones Generales de Bitácora
Registro libre de notas no vinculadas a reportes de QFieldCloud.

Flujo:
  - Todos los roles autenticados pueden leer el historial (chat).
  - Todos los roles autenticados pueden insertar anotaciones.

SEGURIDAD:
  - Inserción vía get_user_client() → RLS activo en Supabase.
  - max_chars=2000 en st.chat_input() limita el payload.
  - Los valores de tramo/civ/pk se insertan como parámetros (sin
    concatenación SQL directa).
"""

import base64
import logging
import re
from datetime import date, datetime, timezone, timedelta

import streamlit as st

from database import load_anotaciones_generales, get_user_client, clear_cache
from ui import section_badge, esc

_log = logging.getLogger(__name__)

_TZ_BOGOTA = timezone(timedelta(hours=-5))

# Colores por empresa — coinciden con identidad visual del proyecto
_COMPANY_COLORS: dict[str, str] = {
    'CONSORCIO INTERCONSERVACION': '#4194E8',
    'URBACON':                     '#D95134',
    'IDU':                         '#7DCF38',
}
_COLOR_DEFAULT = '#888888'


def _company_color(empresa: str) -> str:
    """Retorna el color hex asociado a la empresa del usuario."""
    emp_upper = empresa.upper()
    for key, color in _COMPANY_COLORS.items():
        if key in emp_upper:
            return color
    return _COLOR_DEFAULT


def _avatar_svg(empresa: str) -> str:
    """
    Data URL de un SVG con ícono clásico de usuario.
    El color de fondo varía según la empresa para diferenciar visualmente
    quién pertenece a cada organización.
    """
    color = _company_color(empresa)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">'
        f'<circle cx="20" cy="20" r="20" fill="{color}"/>'
        f'<circle cx="20" cy="15" r="7" fill="white" opacity="0.92"/>'
        f'<ellipse cx="20" cy="35" rx="12" ry="9" fill="white" opacity="0.92"/>'
        f'</svg>'
    )
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def _fmt_ts(raw: str) -> str:
    """
    Convierte un timestamp UTC de Supabase a hora de Bogotá (UTC-5).
    Retorna string con formato 'YYYY-MM-DD HH:MM'.
    """
    if not raw:
        return ''
    try:
        ts = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(_TZ_BOGOTA).strftime('%Y-%m-%d %H:%M')
    except Exception:
        return raw[:16].replace('T', ' ')


def page_anotaciones(perfil: dict) -> None:
    """
    Página principal de Anotaciones Generales.

    perfil: dict con claves id, nombre, rol, empresa
            (cargado desde st.session_state['perfil'] en app.py)
    """
    section_badge("Anotaciones Generales", "purple")
    st.markdown("### Bitácora General")

    # ── Filtros ────────────────────────────────────────────────
    st.markdown('<div class="filter-form-wrap"><div class="filter-form-title">Filtros</div>', unsafe_allow_html=True)
    with st.form("form_anotaciones_filtros"):
        fc1, fc2, fc3, fc4 = st.columns(4)
        with fc1:
            f_fi = st.date_input("Desde",
                                 value=date.today() - timedelta(days=30),
                                 key="ag_fi")
        with fc2:
            f_ff = st.date_input("Hasta", value=date.today(), key="ag_ff")
        with fc3:
            f_usuario = st.text_input("Usuario", key="ag_f_user",
                                      placeholder="Nombre del autor")
        with fc4:
            f_buscar = st.text_input("Buscar en anotación", key="ag_f_bus",
                                     placeholder="Texto libre")
        fa1, fa2 = st.columns(2)
        with fa1:
            f_tramo = st.text_input("Tramo", key="ag_f_tramo", placeholder="ID de tramo")
        with fa2:
            f_civ = st.text_input("CIV", key="ag_f_civ", placeholder="Código CIV")
        st.form_submit_button("Aplicar filtros", type="primary",
                              width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Carga y filtrado ───────────────────────────────────────
    df = load_anotaciones_generales(perfil['contrato_id'])

    df_filt = df.copy() if not df.empty else df

    if not df_filt.empty:
        if 'fecha' in df_filt.columns:
            df_filt = df_filt[df_filt['fecha'].astype(str) >= f_fi.isoformat()]
            df_filt = df_filt[df_filt['fecha'].astype(str) <= f_ff.isoformat()]
        if f_usuario.strip() and 'usuario_nombre' in df_filt.columns:
            df_filt = df_filt[df_filt['usuario_nombre'].astype(str)
                              .str.contains(re.escape(f_usuario.strip()), case=False, na=False)]
        if f_tramo.strip() and 'tramo' in df_filt.columns:
            df_filt = df_filt[df_filt['tramo'].astype(str)
                              .str.contains(re.escape(f_tramo.strip()), case=False, na=False)]
        if f_civ.strip() and 'civ' in df_filt.columns:
            df_filt = df_filt[df_filt['civ'].astype(str)
                              .str.contains(re.escape(f_civ.strip()), case=False, na=False)]
        if f_buscar.strip() and 'anotacion' in df_filt.columns:
            df_filt = df_filt[df_filt['anotacion'].astype(str)
                              .str.contains(re.escape(f_buscar.strip()), case=False, na=False)]

    # ── Exportar CSV ───────────────────────────────────────────
    if not df_filt.empty:
        _csv_cols_ag = [c for c in [
            'fecha', 'tramo', 'civ', 'pk', 'anotacion',
            'usuario_nombre', 'usuario_rol', 'usuario_empresa', 'created_at',
        ] if c in df_filt.columns]
        st.download_button(
            "Exportar CSV",
            data=df_filt[_csv_cols_ag].to_csv(index=False).encode('utf-8'),
            file_name=f"Anotaciones_{f_fi.strftime('%Y%m%d')}_{f_ff.strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )

    st.markdown(f"**{len(df_filt)} anotación(es)**")

    # ── Historial ──────────────────────────────────────────────
    chat_container = st.container(height=500)
    with chat_container:
        if df_filt.empty:
            st.caption("No hay anotaciones para los filtros seleccionados.")
        else:
            rows  = list(df_filt.iterrows())
            total = len(rows)
            for i, (_, row) in enumerate(rows):
                nombre  = str(row.get('usuario_nombre', '—'))
                rol_u   = str(row.get('usuario_rol',    '') or '')
                empresa = str(row.get('usuario_empresa','') or '')
                fecha   = str(row.get('fecha',          '') or '')
                tramo   = str(row.get('tramo',          '') or '')
                civ     = str(row.get('civ',            '') or '')
                pk      = str(row.get('pk',             '') or '')
                texto   = str(row.get('anotacion',      ''))
                ts_raw  = str(row.get('created_at',     ''))

                with st.chat_message(nombre, avatar=_avatar_svg(empresa)):
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
                    st.write(texto)
                    st.caption(esc(_fmt_ts(ts_raw)))

                # Separador sutil entre anotaciones (fuera del globo)
                if i < total - 1:
                    st.markdown(
                        '<hr style="border:none;border-top:1px solid '
                        'rgba(128,128,128,0.18);margin:2px 0 4px 0;">',
                        unsafe_allow_html=True,
                    )

    # ── Compositor ─────────────────────────────────────────────
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
