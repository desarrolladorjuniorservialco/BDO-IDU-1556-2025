"""
auth.py — Autenticación de usuarios
Login con Supabase Auth y gestión de sesión Streamlit.

SEGURIDAD:
  - Mensajes de error genéricos: no revelan si el correo existe o no.
  - Límites de longitud en campos de entrada para prevenir payloads grandes.
  - Validación básica de formato de email antes de llamar a Supabase.
  - La contraseña nunca se almacena ni se loguea.
  - El perfil de usuario se verifica antes de almacenar en session_state.
  - Rate limiting por sesión: bloqueo temporal tras N intentos fallidos.
    Nota: el bloqueo es por pestaña del navegador (st.session_state).
    Para protección a nivel de IP activar "Rate Limiting" en el panel
    de Supabase: Auth → Settings → Rate Limits.
  - El JWT del usuario se guarda en session_state para que las
    operaciones de escritura usen el cliente con RLS activo.
"""

import logging
import re
from datetime import datetime, timedelta

import streamlit as st

from database import get_supabase

_log = logging.getLogger(__name__)

# Límites de entrada
_MAX_EMAIL    = 100
_MAX_PASSWORD = 128

# Regex básica de email (no exhaustiva, solo bloquea basura obvia)
_EMAIL_RE = re.compile(r'^[^@\s]{1,64}@[^@\s]{1,64}\.[^@\s]{1,10}$')

# Roles válidos permitidos en perfiles
_ROLES_VALIDOS = frozenset({
    'inspector', 'obra', 'residente', 'coordinador',
    'interventor', 'supervisor', 'admin',
})

# ── Rate limiting ──────────────────────────────────────────
_MAX_INTENTOS      = 5    # intentos fallidos antes del bloqueo
_BLOQUEO_SEGUNDOS  = 300  # 5 minutos de bloqueo
_KEY_INTENTOS      = '_login_intentos'
_KEY_BLOQUEO_HASTA = '_login_bloqueo_hasta'


def _bloqueado() -> bool:
    """
    Retorna True si el usuario está en período de bloqueo y muestra
    el tiempo restante. Limpia el bloqueo si ya expiró.
    """
    hasta = st.session_state.get(_KEY_BLOQUEO_HASTA)
    if hasta is None:
        return False
    ahora = datetime.now()
    if ahora < hasta:
        restante = int((hasta - ahora).total_seconds())
        st.error(
            f"Demasiados intentos fallidos. "
            f"Espera {restante} segundo(s) antes de intentarlo de nuevo."
        )
        return True
    # Bloqueo expirado: limpiar contadores
    st.session_state.pop(_KEY_INTENTOS, None)
    st.session_state.pop(_KEY_BLOQUEO_HASTA, None)
    return False


def _registrar_fallo() -> None:
    """Incrementa el contador de fallos y aplica bloqueo si se supera el límite."""
    intentos = st.session_state.get(_KEY_INTENTOS, 0) + 1
    st.session_state[_KEY_INTENTOS] = intentos
    _log.warning("Intento de login fallido (%d/%d)", intentos, _MAX_INTENTOS)
    if intentos >= _MAX_INTENTOS:
        hasta = datetime.now() + timedelta(seconds=_BLOQUEO_SEGUNDOS)
        st.session_state[_KEY_BLOQUEO_HASTA] = hasta
        _log.warning(
            "Login bloqueado por %d intentos fallidos. Bloqueado hasta %s",
            intentos, hasta.isoformat(),
        )


def _resetear_intentos() -> None:
    """Limpia el contador tras un login exitoso."""
    st.session_state.pop(_KEY_INTENTOS, None)
    st.session_state.pop(_KEY_BLOQUEO_HASTA, None)


def login() -> None:
    """
    Pantalla de inicio de sesión.
    En caso de éxito escribe en st.session_state['user'] y ['perfil'].
    """
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

        email    = st.text_input(
            "Correo electrónico",
            placeholder="usuario@empresa.com",
            max_chars=_MAX_EMAIL,
        )
        password = st.text_input(
            "Contraseña",
            type="password",
            max_chars=_MAX_PASSWORD,
        )
        st.markdown("<br>", unsafe_allow_html=True)
        submit = st.button("Ingresar al sistema", use_container_width=True, type="primary")

        if not submit:
            return

        # ── Verificar bloqueo por intentos fallidos ────────
        if _bloqueado():
            return

        # ── Validación local antes de llamar a Supabase ────
        if not email or not password:
            st.error("Ingresa correo electrónico y contraseña.")
            return

        if not _EMAIL_RE.match(email):
            # Mensaje genérico para no confirmar existencia de cuentas
            _registrar_fallo()
            st.error("Correo o contraseña incorrectos.")
            return

        # ── Autenticación ──────────────────────────────────
        try:
            sb   = get_supabase()
            resp = sb.auth.sign_in_with_password({"email": email, "password": password})

            if not resp.user:
                _registrar_fallo()
                st.error("Correo o contraseña incorrectos.")
                return

            # ── Cargar perfil ──────────────────────────────
            perfil_r = (
                sb.table('perfiles')
                .select('id, nombre, rol, empresa')   # solo columnas necesarias
                .eq('id', resp.user.id)
                .execute()
            )

            if not perfil_r.data:
                _registrar_fallo()
                st.error("Cuenta sin perfil configurado. Contacta al administrador.")
                _log.warning("Login sin perfil: user_id=%s", resp.user.id)
                return

            perfil = perfil_r.data[0]

            # ── Validar rol ────────────────────────────────
            if perfil.get('rol') not in _ROLES_VALIDOS:
                _registrar_fallo()
                st.error("Rol no reconocido. Contacta al administrador.")
                _log.warning(
                    "Rol inválido en login: user_id=%s rol=%s",
                    resp.user.id, perfil.get('rol'),
                )
                return

            # ── Escribir sesión ────────────────────────────
            # El access_token se guarda por separado para usarlo en el
            # cliente con RLS (get_user_client). No se incluye en 'perfil'
            # para evitar que circule innecesariamente por el código de UI.
            _resetear_intentos()
            access_token = None
            if resp.session:
                access_token = resp.session.access_token
            st.session_state['user']            = resp.user
            st.session_state['perfil']          = perfil
            st.session_state['_access_token']   = access_token
            st.rerun()

        except Exception:
            # Loguear detalles internos; mostrar mensaje genérico
            _registrar_fallo()
            _log.exception("Error en autenticación para email=%s", email[:20])
            st.error("No fue posible iniciar sesión. Intenta de nuevo.")


def logout() -> None:
    """Cierra la sesión y limpia todo el estado de Streamlit."""
    # Incluye _access_token y contadores de rate limiting
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)
    st.rerun()
