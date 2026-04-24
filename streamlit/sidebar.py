"""
sidebar.py — Navegación lateral con control de acceso por rol.
"""

import streamlit as st
from config        import ROL_LABELS, NAV_ACCESS, NAV_CATEGORIES
from database      import load_cantidades
from auth          import logout
from session_store import update_page


def sidebar(perfil: dict) -> str:
    """
    Renderiza el sidebar con:
      - Header de usuario y rol
      - Chips de estado rápido (cantidades)
      - Navegación por categorías con ítem activo resaltado
      - Botón de cerrar sesión

    Retorna el nombre de la página actualmente seleccionada.
    """
    rol = perfil['rol']

    with st.sidebar:
        # ── Header de usuario ──────────────────────────────
        st.markdown(
            f"""
            <div style="padding:1rem 0 0.75rem 0;
                        border-bottom:1px solid rgba(255,255,255,0.08);
                        margin-bottom:0.5rem;">
                <div style="font-size:0.62rem; color:#7a8aa0;
                            font-family:'IBM Plex Mono',monospace;
                            text-transform:uppercase; letter-spacing:0.12em;
                            margin-bottom:0.2rem;">
                    {ROL_LABELS.get(rol, rol)}
                </div>
                <div style="font-size:1rem; font-weight:700; color:#e6edf3;
                            font-family:'IBM Plex Sans',sans-serif;">
                    {perfil['nombre']}
                </div>
                <div style="font-size:0.78rem; color:#8b949e;">
                    {perfil.get('empresa', '')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Chips de estado rápido ─────────────────────────
        df_q = load_cantidades(perfil['contrato_id'])
        if not df_q.empty:
            total = len(df_q)
            apr   = len(df_q[df_q['estado'] == 'APROBADO'])
            rev   = len(df_q[df_q['estado'] == 'REVISADO'])
            dev   = len(df_q[df_q['estado'] == 'DEVUELTO'])
            st.markdown(
                f"""
                <div class="stat-row">
                    <span class="stat-chip"
                          style="background:rgba(109,109,110);color:#6d6d6e;">
                        {total} total
                    </span>
                    <span class="stat-chip"
                          style="background:#0d2818;color:#3fb950;">
                        {apr} aprobados
                    </span>
                    <span class="stat-chip"
                          style="background:#0d3050;color:#58a6ff;">
                        {rev} revisados
                    </span>
                    <span class="stat-chip"
                          style="background:#3d1010;color:#f85149;">
                        {dev} devueltos
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ── Páginas accesibles para este rol ───────────────
        opciones: list[str] = []
        for cat in NAV_CATEGORIES:
            for page in cat["pages"]:
                if rol in NAV_ACCESS.get(page, []) and page not in opciones:
                    opciones.append(page)

        selected: str = st.session_state.get(
            'current_page',
            opciones[0] if opciones else "Estado Actual",
        )

        # ── Render de categorías y páginas ─────────────────
        for cat in NAV_CATEGORIES:
            accesibles = [p for p in cat["pages"] if rol in NAV_ACCESS.get(p, [])]
            if not accesibles:
                continue

            cat_class = "nav-cat-hi" if cat["highlight"] else "nav-cat"
            st.markdown(
                f'<div class="{cat_class}">{cat["label"]}</div>',
                unsafe_allow_html=True,
            )

            for page in accesibles:
                if selected == page:
                    # Ítem activo: resaltado, no clickable
                    st.markdown(
                        f'<div class="nav-item-active">{page}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    if st.button(page, key=f"nav_{page}", width="stretch"):
                        st.session_state['current_page'] = page
                        update_page(st.session_state.get('_session_id', ''), page)
                        st.query_params['page'] = page
                        st.rerun()

        # ── Cerrar sesión ──────────────────────────────────
        st.divider()
        if st.button("Cerrar sesión", width="stretch"):
            logout()

    return selected
