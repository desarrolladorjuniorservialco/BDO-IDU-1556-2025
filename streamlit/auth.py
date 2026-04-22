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
import threading
from datetime import datetime, timedelta

import streamlit as st

from database import get_supabase
from session_store import create_session, invalidate_session

_log = logging.getLogger(__name__)

# Límites de entrada
_MAX_EMAIL    = 100
_MAX_PASSWORD = 128

# Regex básica de email (no exhaustiva, solo bloquea basura obvia)
_EMAIL_RE = re.compile(r'^[^@\s]{1,64}@[^@\s]{1,64}\.[^@\s]{1,10}$')

# Roles válidos permitidos en perfiles
_ROLES_VALIDOS = frozenset({
    'operativo', 'obra', 'interventoria', 'supervision', 'admin',
})

# ── Rate limiting SERVER-SIDE ──────────────────────────────
# El contador se guarda en un cache compartido entre TODAS las sesiones
# del servidor (st.cache_resource), no solo en la pestaña del navegador.
# Esto impide que abrir pestañas nuevas evite el bloqueo.
# El tracking es por email (el objetivo del ataque, no la IP).
#
# Adicionalmente, activar "Rate Limits" en Supabase Dashboard:
#   Auth → Settings → Rate Limits
# para protección a nivel de infraestructura independiente del código.

_MAX_INTENTOS     = 3    # intentos fallidos antes del bloqueo
_BLOQUEO_SEGUNDOS = 900  # 15 minutos de bloqueo


@st.cache_resource
def _rate_limiter() -> dict:
    """
    Cache compartido entre todas las sesiones Streamlit del servidor.
    Estructura: { email_hash: (intentos: int, bloqueado_hasta: datetime | None) }
    Usa un threading.Lock para seguridad en entornos con múltiples hilos.
    """
    return {'datos': {}, 'lock': threading.Lock()}


def _hash_email(email: str) -> str:
    """Hash simple del email para no almacenar el valor original en memoria."""
    import hashlib
    return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:16]


def _verificar_intento(email: str, registrar_fallo: bool = False) -> bool:
    """
    Operación ATÓMICA que verifica bloqueo y, opcionalmente, registra un fallo.
    Usar un solo lock para ambas acciones elimina la race condition entre
    _bloqueado() y _registrar_fallo() cuando múltiples hilos intentan login.

    Retorna True si el email está bloqueado (no debe continuar).

    Parámetros:
        email:           dirección de correo del intento.
        registrar_fallo: si True, incrementa el contador antes de retornar.
                         Usar solo cuando el intento ya falló (credenciales
                         incorrectas). No usar en la verificación previa.
    """
    rl    = _rate_limiter()
    llave = _hash_email(email)
    ahora = datetime.now()

    with rl['lock']:
        # Limpiar entradas expiradas (evita memory leak en servidores longevos)
        expiradas = [
            k for k, (_, hasta) in rl['datos'].items()
            if hasta and ahora >= hasta
        ]
        for k in expiradas:
            del rl['datos'][k]

        intentos, hasta = rl['datos'].get(llave, (0, None))

        # ── Verificar si ya está bloqueado ─────────────────
        if hasta and ahora < hasta:
            restante = int((hasta - ahora).total_seconds())
            minutos  = restante // 60
            segundos = restante % 60
            # Mostramos el error fuera del lock no es posible aquí,
            # lo almacenamos y lo mostramos tras liberar el lock.
            # st.error se llama dentro del lock solo brevemente.
            st.error(
                f"Demasiados intentos fallidos. "
                f"Espera {minutos}m {segundos}s antes de intentarlo de nuevo."
            )
            return True

        # ── Registrar fallo si se solicita ─────────────────
        if registrar_fallo:
            intentos += 1
            nueva_hasta = None
            if intentos >= _MAX_INTENTOS:
                nueva_hasta = ahora + timedelta(seconds=_BLOQUEO_SEGUNDOS)
                _log.warning(
                    "Login bloqueado para hash=%s tras %d intentos. Hasta %s",
                    llave, intentos, nueva_hasta.isoformat(),
                )
            else:
                _log.warning(
                    "Intento de login fallido para hash=%s (%d/%d)",
                    llave, intentos, _MAX_INTENTOS,
                )
            rl['datos'][llave] = (intentos, nueva_hasta)

        return False


def _resetear_intentos(email: str) -> None:
    """Limpia el contador del email tras un login exitoso."""
    rl    = _rate_limiter()
    llave = _hash_email(email)
    with rl['lock']:
        rl['datos'].pop(llave, None)


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
                BOB - Sistema de Bitácora Digital
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
        submit = st.button("Ingresar al sistema", width="stretch", type="primary")

        if not submit:
            return

        # ── Verificar bloqueo server-side (atómico, sin race condition) ──
        if _verificar_intento(email, registrar_fallo=False):
            return

        # ── Validación local antes de llamar a Supabase ────
        if not email or not password:
            st.error("Ingresa correo electrónico y contraseña.")
            return

        if not _EMAIL_RE.match(email):
            _verificar_intento(email, registrar_fallo=True)
            st.error("Correo o contraseña incorrectos.")
            return

        # ── Autenticación ──────────────────────────────────
        try:
            sb   = get_supabase()
            resp = sb.auth.sign_in_with_password({"email": email, "password": password})

            if not resp.user:
                _verificar_intento(email, registrar_fallo=True)
                st.error("Correo o contraseña incorrectos.")
                return

            # ── Cargar perfil ──────────────────────────────
            perfil_r = (
                sb.table('perfiles')
                .select('id, nombre, rol, empresa')
                .eq('id', resp.user.id)
                .execute()
            )

            if not perfil_r.data:
                _verificar_intento(email, registrar_fallo=True)
                st.error("Cuenta sin perfil configurado. Contacta al administrador.")
                _log.warning("Login sin perfil: user_id=%s", _hash_email(email))
                return

            perfil = perfil_r.data[0]

            # ── Validar rol ────────────────────────────────
            if perfil.get('rol') not in _ROLES_VALIDOS:
                _verificar_intento(email, registrar_fallo=True)
                st.error("Rol no reconocido. Contacta al administrador.")
                _log.warning(
                    "Rol inválido en login: hash=%s rol=%s",
                    _hash_email(email), perfil.get('rol'),
                )
                return

            # ── Escribir sesión ────────────────────────────
            _resetear_intentos(email)
            access_token  = None
            refresh_token = None
            if resp.session:
                access_token  = resp.session.access_token
                refresh_token = resp.session.refresh_token

            sid = create_session(resp.user, perfil, access_token or '', refresh_token or '')
            st.session_state['user']          = resp.user
            st.session_state['perfil']        = perfil
            st.session_state['_access_token'] = access_token
            st.session_state['_session_id']   = sid
            st.query_params['sid'] = sid
            if refresh_token:
                st.query_params['rt'] = refresh_token
            st.rerun()

        except Exception:
            _verificar_intento(email, registrar_fallo=True)
            # Log con hash del email, nunca el valor original
            _log.exception("Error en autenticación para hash=%s", _hash_email(email))
            st.error("No fue posible iniciar sesión. Intenta de nuevo.")


def logout() -> None:
    """Cierra la sesión y limpia todo el estado de Streamlit."""
    sid = st.session_state.get('_session_id')
    if sid:
        invalidate_session(sid)
    st.query_params.clear()
    for k in list(st.session_state.keys()):
        st.session_state.pop(k, None)
    st.rerun()
