"""
auth.py — Autenticación de usuarios
Login con Supabase Auth y gestión de sesión Streamlit.
"""

import streamlit as st
from database import get_supabase


def login() -> None:
    """Pantalla de inicio de sesión. Escribe en st.session_state['user'] y ['perfil']."""
    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-family:'IBM Plex Mono',monospace; font-size:0.68rem;
                        letter-spacing:0.16em; color:var(--accent-blue);
                        text-transform:uppercase; margin-bottom:0.3rem;">
                Sistema de Bitácora Digital
            </div>
            <div style="font-size:1.85rem; font-weight:700; color:var(--text-primary);
                        margin-bottom:0.1rem; font-family:'IBM Plex Sans',sans-serif;">
                BDO · IDU-1556-2025
            </div>
            <div style="font-size:0.84rem; color:var(--text-muted); margin-bottom:2rem;">
                Contrato de obra · Grupo 4<br>
                Mártires · San Cristóbal · Rafael Uribe Uribe · Santafé · Antonio Nariño
            </div>
            """,
            unsafe_allow_html=True,
        )

        email    = st.text_input("Correo electrónico", placeholder="usuario@empresa.com")
        password = st.text_input("Contraseña", type="password")
        st.markdown("<br>", unsafe_allow_html=True)
        submit   = st.button("Ingresar al sistema", use_container_width=True, type="primary")

        if submit:
            if not email or not password:
                st.error("Ingresa correo y contraseña")
                return
            try:
                sb   = get_supabase()
                resp = sb.auth.sign_in_with_password({"email": email, "password": password})
                if resp.user:
                    perfil_r = sb.table('perfiles').select('*').eq('id', resp.user.id).execute()
                    if not perfil_r.data:
                        st.error("Usuario sin perfil configurado. Contacta al administrador.")
                        return
                    st.session_state['user']   = resp.user
                    st.session_state['perfil'] = perfil_r.data[0]
                    st.rerun()
            except Exception as e:
                st.error(f"Error de autenticación: {e}")


def logout() -> None:
    """Cierra la sesión y limpia el estado."""
    for k in ['user', 'perfil', 'current_page']:
        st.session_state.pop(k, None)
    st.rerun()
