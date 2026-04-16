"""
session_store.py — Almacén server-side de sesiones de usuario.

Permite restaurar la sesión del usuario tras una recarga del navegador
(F5 / Ctrl+R) sin requerir un nuevo login, mientras el servidor Streamlit
esté corriendo.

MECANISMO:
  1. Al hacer login, se genera un session_id criptográficamente aleatorio
     y se guarda en la URL como ?sid=<token>.
  2. Los tokens de Supabase y el perfil se almacenan en este store,
     indexados por session_id. El navegador SOLO guarda el sid opaco.
  3. Al recargar la página, la URL conserva ?sid=<token>. La app lo lee,
     busca la sesión en el store y restaura session_state.
  4. Al cerrar sesión, la entrada se elimina del store y ?sid se limpia
     de la URL.

SEGURIDAD:
  - session_id: token aleatorio de 32 bytes (secrets.token_urlsafe).
  - Los tokens Supabase (access_token) no pasan por el navegador.
  - Las sesiones expiran automáticamente tras SESSION_TTL_HOURS horas.
  - El store es compartido entre hilos → acceso protegido con threading.Lock.
  - Si el servidor se reinicia, el store se vacía: los usuarios deben
    re-autenticarse (comportamiento esperado para Streamlit Cloud).
"""

import secrets
import threading
from datetime import datetime, timedelta

import streamlit as st

_SESSION_TTL_HOURS = 24


@st.cache_resource
def _store() -> dict:
    """
    Singleton compartido entre todas las sesiones del servidor.
    Estructura interna:
      {
        session_id (str): {
          'user':         objeto de usuario Supabase,
          'perfil':       dict (id, nombre, rol, empresa),
          'access_token': str,
          'current_page': str | None,
          'expires_at':   datetime,
        }
      }
    """
    return {'data': {}, 'lock': threading.Lock()}


def _clean_expired() -> None:
    """Elimina silenciosamente las sesiones expiradas (evita memory leak)."""
    s   = _store()
    now = datetime.now()
    with s['lock']:
        expired = [k for k, v in s['data'].items() if v['expires_at'] < now]
        for k in expired:
            del s['data'][k]


def create_session(user: object, perfil: dict, access_token: str) -> str:
    """
    Registra una nueva sesión y retorna el session_id.
    Llamar justo después de un login exitoso.
    """
    _clean_expired()
    sid = secrets.token_urlsafe(32)
    s   = _store()
    with s['lock']:
        s['data'][sid] = {
            'user':         user,
            'perfil':       perfil,
            'access_token': access_token,
            'current_page': None,
            'expires_at':   datetime.now() + timedelta(hours=_SESSION_TTL_HOURS),
        }
    return sid


def restore_session(sid: str) -> dict | None:
    """
    Retorna una copia de los datos de sesión si el sid es válido y no expiró.
    Retorna None si no existe o la sesión caducó.
    """
    s = _store()
    with s['lock']:
        data = s['data'].get(sid)
        if not data:
            return None
        if data['expires_at'] < datetime.now():
            del s['data'][sid]
            return None
        return dict(data)   # copia defensiva para no exponer el objeto interno


def update_page(sid: str, page: str) -> None:
    """
    Guarda la página actualmente activa en la sesión.
    Llamar en sidebar cada vez que el usuario navega.
    Permite restaurar la página correcta al recargar.
    """
    if not sid:
        return
    s = _store()
    with s['lock']:
        if sid in s['data']:
            s['data'][sid]['current_page'] = page


def invalidate_session(sid: str) -> None:
    """
    Elimina la sesión del store.
    Llamar al hacer logout.
    """
    if not sid:
        return
    s = _store()
    with s['lock']:
        s['data'].pop(sid, None)
