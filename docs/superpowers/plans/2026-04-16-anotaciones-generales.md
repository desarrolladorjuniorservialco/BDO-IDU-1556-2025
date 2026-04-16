# Anotaciones Generales — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar la página `anotaciones.py` por un sistema de bitácora libre estilo chat de red social, con nueva tabla Supabase, RLS y loader.

**Architecture:** Nueva tabla `anotaciones_generales` en Supabase con RLS (lectura para todos, inserción bloqueada para `supervisor`). Loader en `database.py`. La página renderiza el historial en un `st.container(height=500)` con `st.chat_message`, y el compositor usa `st.chat_input()` fijo al fondo con una fila de metadatos en `session_state`.

**Tech Stack:** Python 3.11, Streamlit 1.32.0, supabase-py 1.2.0, Supabase PostgreSQL (RLS con tabla `perfiles`)

---

## File Map

| Acción | Archivo | Responsabilidad |
|--------|---------|-----------------|
| Modificar | `streamlit/database.py` | Agregar `load_anotaciones_generales()` |
| Reescribir | `streamlit/pages/anotaciones.py` | Nueva UI: chat + compositor |
| SQL manual | Supabase SQL Editor | Tabla, RLS, índice |

---

## Task 1: Crear la tabla en Supabase

**Files:**
- SQL a ejecutar manualmente en el Supabase SQL Editor del proyecto

- [ ] **Step 1: Ejecutar el SQL de creación de tabla y RLS**

Ir al panel de Supabase → SQL Editor → New query. Pegar y ejecutar el bloque completo:

```sql
-- ── Tabla principal ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS anotaciones_generales (
    id               uuid        DEFAULT gen_random_uuid() PRIMARY KEY,
    fecha            date        NOT NULL,
    tramo            text,
    civ              text,
    pk               text,
    anotacion        text        NOT NULL CHECK (char_length(anotacion) <= 2000),
    usuario_id       uuid        NOT NULL REFERENCES auth.users(id),
    usuario_nombre   text        NOT NULL,
    usuario_rol      text        NOT NULL,
    usuario_empresa  text,
    created_at       timestamptz DEFAULT now()
);

-- ── Índice de rendimiento ─────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_ag_created_at
    ON anotaciones_generales (created_at ASC);

-- ── RLS ───────────────────────────────────────────────────────
ALTER TABLE anotaciones_generales ENABLE ROW LEVEL SECURITY;

-- Lectura: cualquier usuario autenticado
CREATE POLICY "ag_select_authenticated"
ON anotaciones_generales
FOR SELECT TO authenticated
USING (true);

-- Inserción: autenticados con rol != 'supervisor'
CREATE POLICY "ag_insert_non_supervisor"
ON anotaciones_generales
FOR INSERT TO authenticated
WITH CHECK (
    (SELECT rol FROM perfiles WHERE id = auth.uid()) != 'supervisor'
);

-- Sin UPDATE ni DELETE: registro inmutable (bitácora)
```

- [ ] **Step 2: Verificar la tabla en Table Editor**

En Supabase → Table Editor → `anotaciones_generales`. Confirmar que:
- La tabla aparece con las columnas descritas.
- En Authentication → Policies, la tabla muestra las dos políticas: `ag_select_authenticated` y `ag_insert_non_supervisor`.

- [ ] **Step 3: Insertar una fila de prueba para validar constraint**

```sql
-- Debe fallar (anotacion vacía supera CHECK, en realidad anotacion = '' no supera char_length > 0)
-- Este insert debe INSERTARSE correctamente:
INSERT INTO anotaciones_generales
    (fecha, tramo, civ, pk, anotacion, usuario_id, usuario_nombre, usuario_rol, usuario_empresa)
VALUES
    ('2026-04-16', 'T-01', '1234', 'PK+0500',
     'Anotación de prueba técnica.',
     auth.uid(),  -- solo funciona si ejecutas como usuario autenticado con service_role
     'Admin Test', 'admin', 'Empresa Test');
```

Si usas service_role en el SQL Editor, reemplaza `auth.uid()` por cualquier UUID válido de `auth.users`. El registro debe insertarse sin errores.

- [ ] **Step 4: Borrar la fila de prueba**

```sql
DELETE FROM anotaciones_generales WHERE anotacion = 'Anotación de prueba técnica.';
```

---

## Task 2: Agregar loader en `database.py`

**Files:**
- Modify: `streamlit/database.py` (al final del archivo, antes de la última función existente)

- [ ] **Step 1: Agregar la función `load_anotaciones_generales` al final de `database.py`**

Abrir [streamlit/database.py](streamlit/database.py) y añadir al final del archivo:

```python
@st.cache_data(ttl=30)
def load_anotaciones_generales(limit: int = 300) -> pd.DataFrame:
    """
    Anotaciones generales de bitácora, ordenadas ASC por created_at.
    Carga las últimas `limit` anotaciones (default 300).
    TTL corto (30 s) para que el historial se sienta responsivo.
    """
    def _q():
        return (
            get_supabase()
            .table('anotaciones_generales')
            .select('*')
            .order('created_at', desc=False)
            .limit(limit)
            .execute()
        )
    return _safe_query(_q, context='load_anotaciones_generales')
```

- [ ] **Step 2: Verificar que el módulo importa sin errores**

Desde el directorio `streamlit/`:

```bash
python -c "from database import load_anotaciones_generales; print('OK')"
```

Salida esperada: `OK`

- [ ] **Step 3: Commit**

```bash
git add streamlit/database.py
git commit -m "feat: add load_anotaciones_generales loader"
```

---

## Task 3: Reescribir `pages/anotaciones.py`

**Files:**
- Rewrite: `streamlit/pages/anotaciones.py`

- [ ] **Step 1: Reemplazar el contenido completo del archivo**

Reemplazar todo el contenido de [streamlit/pages/anotaciones.py](streamlit/pages/anotaciones.py) con:

```python
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
from ui import section_badge

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
                nombre   = str(row.get('usuario_nombre', '—'))
                rol_u    = str(row.get('usuario_rol',    '') or '')
                empresa  = str(row.get('usuario_empresa','') or '')
                fecha    = str(row.get('fecha',          '') or '')
                tramo    = str(row.get('tramo',          '') or '')
                civ      = str(row.get('civ',            '') or '')
                pk       = str(row.get('pk',             '') or '')
                texto    = str(row.get('anotacion',      ''))
                ts       = str(row.get('created_at',     ''))[:16].replace('T', ' ')

                with st.chat_message(nombre):
                    # ── Fila de metadatos ──────────────────
                    pills = (
                        f'<span class="info-pill">{nombre}</span>'
                        f'<span class="info-pill blue">'
                        f'{rol_u.replace("_"," ").title()}'
                        f'</span>'
                    )
                    if empresa:
                        pills += f'<span class="info-pill teal">{empresa}</span>'
                    if fecha:
                        pills += f'<span class="info-pill">{fecha}</span>'
                    if tramo:
                        pills += f'<span class="info-pill orange">Tramo: {tramo}</span>'
                    if civ:
                        pills += f'<span class="info-pill teal">CIV: {civ}</span>'
                    if pk:
                        pills += f'<span class="info-pill">PK: {pk}</span>'

                    st.markdown(
                        f'<div class="record-meta-row">{pills}</div>',
                        unsafe_allow_html=True,
                    )
                    # ── Texto de la anotación ──────────────
                    st.markdown(texto)
                    # ── Timestamp de creación (caption) ───
                    st.caption(ts)

    # ── Compositor (no se renderiza para supervisor) ───────────
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
        )
    with mc3:
        ag_civ = st.text_input(
            "CIV",
            key="ag_civ",
            placeholder="Opcional",
        )
    with mc4:
        ag_pk = st.text_input(
            "PK",
            key="ag_pk",
            placeholder="Opcional",
        )

    # Chat input fijo al fondo de la página
    texto_nuevo = st.chat_input(
        "Escribe tu anotación...",
        max_chars=2000,
    )

    if texto_nuevo:
        _insertar_anotacion(
            texto   = texto_nuevo.strip(),
            fecha   = ag_fecha,
            tramo   = ag_tramo.strip() or None,
            civ     = ag_civ.strip()   or None,
            pk      = ag_pk.strip()    or None,
            perfil  = perfil,
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
```

- [ ] **Step 2: Verificar que el módulo importa sin errores**

```bash
python -c "from pages.anotaciones import page_anotaciones; print('OK')"
```

Salida esperada: `OK`

- [ ] **Step 3: Commit**

```bash
git add streamlit/pages/anotaciones.py
git commit -m "feat: rewrite anotaciones as general bitacora chat page"
```

---

## Task 4: Prueba funcional en el navegador

- [ ] **Step 1: Levantar la app**

Desde el directorio `streamlit/`:

```bash
streamlit run app.py
```

- [ ] **Step 2: Verificar historial vacío**

- Iniciar sesión con cualquier rol.
- Navegar a **Anotaciones**.
- Esperar ver el caption `"Aún no hay anotaciones registradas."` dentro del contenedor de chat.
- Verificar que aparece la fila de metadatos (Fecha · Tramo · CIV · PK) y la barra de `st.chat_input()` fija al fondo.

- [ ] **Step 3: Crear una anotación**

- Completar campos: Fecha (hoy), Tramo `T-01`, CIV `123456`, PK `PK+0000`.
- Escribir texto en la barra de chat: `Prueba de anotación general.`
- Presionar Enter o el botón de envío.
- Esperar que la página recargue.
- Verificar que la burbuja aparece en el historial con nombre, rol, empresa, pills de Tramo/CIV/PK y el texto.
- Verificar que los campos Tramo, CIV y PK se limpiaron (vuelven a estar en blanco).

- [ ] **Step 4: Verificar rol supervisor**

- Cerrar sesión e iniciar con un usuario de rol `supervisor`.
- Navegar a **Anotaciones**.
- Verificar que el historial con las burbujas es visible.
- Verificar que **no aparece** la fila de metadatos ni la barra de chat.

- [ ] **Step 5: Commit final y push**

```bash
git add -A
git commit -m "feat: anotaciones generales — complete implementation"
git push
```

---

## Checklist de cobertura del spec

| Requisito | Tarea |
|-----------|-------|
| Tabla `anotaciones_generales` con campos definidos | Task 1 |
| RLS: lectura para todos los autenticados | Task 1 |
| RLS: inserción bloqueada para supervisor | Task 1 |
| Índice `created_at ASC` | Task 1 |
| `load_anotaciones_generales()` en database.py | Task 2 |
| Historial en `st.container(height=500)` con `st.chat_message` | Task 3 |
| Burbujas muestran nombre, rol, empresa, fecha, tramo/civ/pk, texto, timestamp | Task 3 |
| Compositor con fecha/tramo/civ/pk + `st.chat_input()` fijo al fondo | Task 3 |
| Supervisor solo ve historial, sin compositor | Task 3 |
| Limpieza de tramo/civ/pk tras envío | Task 3 |
| Inserción vía `get_user_client()` con RLS activo | Task 3 |
| Verificación funcional en navegador | Task 4 |
