# Reporte Cantidades — Visibilidad y Acciones por Rol

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separar visibilidad de estados y accionabilidad en el Reporte de Cantidades, para que `obra` e `interventoria` vean todos los registros pero solo puedan aprobar/devolver los que corresponden a su nivel.

**Architecture:** Se agrega un cuarto elemento `estados_accion` a cada tupla de `APROBACION_CONFIG`. La función `_panel_aprobacion` recibe ese valor y solo muestra los botones de acción si el estado actual del registro está en `estados_accion`.

**Tech Stack:** Python 3.13, Streamlit 1.32, pytest (dev)

---

## Archivos afectados

| Archivo | Cambio |
|---|---|
| `streamlit/config.py` | Tuplas de `APROBACION_CONFIG` pasan de 3 a 4 elementos |
| `streamlit/pages/reporte_cantidades.py` | Desempaquetar 4 valores; firma de `_panel_aprobacion`; lógica del panel |
| `streamlit/tests/test_reporte_cantidades_config.py` | Tests unitarios nuevos |

---

## Task 1: Tests de configuración de roles

**Files:**
- Create: `streamlit/tests/test_reporte_cantidades_config.py`

- [ ] **Step 1: Escribir los tests**

Crear `streamlit/tests/test_reporte_cantidades_config.py` con el siguiente contenido:

```python
"""
Tests unitarios para APROBACION_CONFIG y la lógica de visibilidad/acción
del Reporte de Cantidades.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from config import APROBACION_CONFIG


def _cfg(rol):
    """Devuelve la tupla de 4 elementos para un rol."""
    return APROBACION_CONFIG[rol]


# ── Estructura de la tupla ───────────────────────────────────────────────────

class TestTuplaConfig:
    def test_todos_los_roles_tienen_4_elementos(self):
        for rol, cfg in APROBACION_CONFIG.items():
            assert len(cfg) == 4, f"Rol '{rol}' tiene {len(cfg)} elementos, se esperan 4"

    def test_rol_obra_existe(self):
        assert 'obra' in APROBACION_CONFIG

    def test_rol_interventoria_existe(self):
        assert 'interventoria' in APROBACION_CONFIG

    def test_rol_operativo_existe(self):
        assert 'operativo' in APROBACION_CONFIG

    def test_rol_supervision_existe(self):
        assert 'supervision' in APROBACION_CONFIG

    def test_rol_admin_existe(self):
        assert 'admin' in APROBACION_CONFIG


# ── Visibilidad: todos los roles activos ven todos los estados ───────────────

class TestVisibilidad:
    @pytest.mark.parametrize("rol", ['obra', 'interventoria', 'supervision', 'admin'])
    def test_estados_vis_es_none_para_roles_activos(self, rol):
        estados_vis, _, _, _ = _cfg(rol)
        assert estados_vis is None, (
            f"Rol '{rol}' tiene estados_vis={estados_vis!r}, se espera None (todos los estados)"
        )

    def test_operativo_estados_vis_es_none(self):
        estados_vis, _, _, _ = _cfg('operativo')
        assert estados_vis is None


# ── Accionabilidad: solo el estado correcto habilita el panel ────────────────

class TestAccionabilidad:
    def test_obra_acciona_solo_borrador(self):
        _, _, _, estados_accion = _cfg('obra')
        assert estados_accion == ['BORRADOR']

    def test_interventoria_acciona_solo_revisado(self):
        _, _, _, estados_accion = _cfg('interventoria')
        assert estados_accion == ['REVISADO']

    def test_operativo_sin_panel(self):
        _, _, campos, estados_accion = _cfg('operativo')
        assert campos is None
        assert estados_accion is None

    def test_supervision_sin_panel(self):
        _, _, campos, estados_accion = _cfg('supervision')
        assert campos is None
        assert estados_accion is None

    def test_admin_acciona_solo_revisado(self):
        _, _, _, estados_accion = _cfg('admin')
        assert estados_accion == ['REVISADO']


# ── Estado de aprobación ─────────────────────────────────────────────────────

class TestEstadoAprobacion:
    def test_obra_aprueba_a_revisado(self):
        _, estado_apr, _, _ = _cfg('obra')
        assert estado_apr == 'REVISADO'

    def test_interventoria_aprueba_a_aprobado(self):
        _, estado_apr, _, _ = _cfg('interventoria')
        assert estado_apr == 'APROBADO'

    def test_admin_aprueba_a_aprobado(self):
        _, estado_apr, _, _ = _cfg('admin')
        assert estado_apr == 'APROBADO'

    def test_operativo_no_aprueba(self):
        _, estado_apr, _, _ = _cfg('operativo')
        assert estado_apr is None

    def test_supervision_no_aprueba(self):
        _, estado_apr, _, _ = _cfg('supervision')
        assert estado_apr is None


# ── Campos de BD ─────────────────────────────────────────────────────────────

class TestCamposBD:
    def test_obra_usa_campos_residente(self):
        _, _, campos, _ = _cfg('obra')
        assert campos['campo_cant']   == 'cant_residente'
        assert campos['campo_estado'] == 'estado_residente'
        assert campos['campo_apr']    == 'aprobado_residente'
        assert campos['campo_fecha']  == 'fecha_residente'
        assert campos['campo_obs']    == 'obs_residente'

    def test_interventoria_usa_campos_interventor(self):
        _, _, campos, _ = _cfg('interventoria')
        assert campos['campo_cant']   == 'cant_interventor'
        assert campos['campo_estado'] == 'estado_interventor'
        assert campos['campo_apr']    == 'aprobado_interventor'
        assert campos['campo_fecha']  == 'fecha_interventor'
        assert campos['campo_obs']    == 'obs_interventor'
```

- [ ] **Step 2: Ejecutar los tests y verificar que fallen**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025/streamlit"
python -m pytest tests/test_reporte_cantidades_config.py -v
```

Salida esperada: varios `FAILED` — `AssertionError: Rol 'obra' tiene 3 elementos, se esperan 4` y similares.

---

## Task 2: Actualizar `APROBACION_CONFIG` en `config.py`

**Files:**
- Modify: `streamlit/config.py:115-156`

- [ ] **Step 1: Reemplazar `APROBACION_CONFIG`**

En `streamlit/config.py`, reemplazar el bloque completo de `APROBACION_CONFIG` (desde `APROBACION_CONFIG: dict[str, tuple] = {` hasta el `}` de cierre) con:

```python
APROBACION_CONFIG: dict[str, tuple] = {
    # operativo: solo lectura, sin panel de aprobación
    'operativo': (None, None, None, None),

    # obra (residente): nivel 1 — ve todos, acciona solo BORRADOR → REVISADO
    'obra': (
        None,
        'REVISADO',
        {
            'campo_cant':   'cant_residente',
            'campo_estado': 'estado_residente',
            'campo_apr':    'aprobado_residente',
            'campo_fecha':  'fecha_residente',
            'campo_obs':    'obs_residente',
        },
        ['BORRADOR'],
    ),

    # interventoria: nivel 2 — ve todos, acciona solo REVISADO → APROBADO
    'interventoria': (
        None,
        'APROBADO',
        {
            'campo_cant':   'cant_interventor',
            'campo_estado': 'estado_interventor',
            'campo_apr':    'aprobado_interventor',
            'campo_fecha':  'fecha_interventor',
            'campo_obs':    'obs_interventor',
        },
        ['REVISADO'],
    ),

    # supervision: ve todos los estados, sin panel de acciones
    'supervision': (None, None, None, None),

    # admin: mismos permisos de acción que interventoria
    'admin': (
        None,
        'APROBADO',
        {
            'campo_cant':   'cant_interventor',
            'campo_estado': 'estado_interventor',
            'campo_apr':    'aprobado_interventor',
            'campo_fecha':  'fecha_interventor',
            'campo_obs':    'obs_interventor',
        },
        ['REVISADO'],
    ),
}
```

- [ ] **Step 2: Ejecutar los tests de configuración**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025/streamlit"
python -m pytest tests/test_reporte_cantidades_config.py -v
```

Salida esperada: todos los tests en `PASSED`.

- [ ] **Step 3: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/config.py streamlit/tests/test_reporte_cantidades_config.py
git commit -m "feat(config): separar visibilidad y accionabilidad en APROBACION_CONFIG"
```

---

## Task 3: Actualizar `reporte_cantidades.py`

**Files:**
- Modify: `streamlit/pages/reporte_cantidades.py:96-97` (firma `_panel_aprobacion`)
- Modify: `streamlit/pages/reporte_cantidades.py:208-209` (desempaque en `page_reporte_cantidades`)
- Modify: `streamlit/pages/reporte_cantidades.py:107-109` (guard del panel)
- Modify: `streamlit/pages/reporte_cantidades.py:471` (llamada a `_panel_aprobacion`)

- [ ] **Step 1: Actualizar firma de `_panel_aprobacion`**

Reemplazar la línea 96-97:

```python
def _panel_aprobacion(reg: pd.Series, perfil: dict,
                       campos: dict | None, estado_apr: str | None) -> None:
```

Por:

```python
def _panel_aprobacion(reg: pd.Series, perfil: dict,
                       campos: dict | None, estado_apr: str | None,
                       estados_accion: list | None) -> None:
```

- [ ] **Step 2: Actualizar el guard del panel dentro de `_panel_aprobacion`**

Localizar el bloque (línea ~107):

```python
    if not campos:
        st.caption(f"Estado: {est_actual}")
        return
```

Reemplazarlo por:

```python
    if not campos or not estados_accion or est_actual not in estados_accion:
        st.caption(f"Estado: {est_actual}")
        return
```

- [ ] **Step 3: Actualizar desempaque de la tupla en `page_reporte_cantidades`**

Localizar (línea ~208-209):

```python
    cfg = APROBACION_CONFIG.get(rol, (None, None, None))
    estados_vis, estado_apr, campos = cfg
```

Reemplazarlo por:

```python
    cfg = APROBACION_CONFIG.get(rol, (None, None, None, None))
    estados_vis, estado_apr, campos, estados_accion = cfg
```

- [ ] **Step 4: Actualizar la llamada a `_panel_aprobacion`**

Localizar (línea ~471):

```python
                    _panel_aprobacion(reg, perfil, campos, estado_apr)
```

Reemplazarlo por:

```python
                    _panel_aprobacion(reg, perfil, campos, estado_apr, estados_accion)
```

- [ ] **Step 5: Verificar que la app no tiene errores de importación**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025/streamlit"
python -c "from pages.reporte_cantidades import page_reporte_cantidades; print('OK')"
```

Salida esperada: `OK`

- [ ] **Step 6: Ejecutar todos los tests**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025/streamlit"
python -m pytest tests/ -v
```

Salida esperada: todos en `PASSED`.

- [ ] **Step 7: Commit**

```bash
cd "C:/Users/Gabriel Sanchez/Documents/GitHub/BDO-IDU-1556-2025/BDO-IDU-1556-2025"
git add streamlit/pages/reporte_cantidades.py
git commit -m "feat(reporte-cantidades): habilitar visibilidad total por rol con panel selectivo"
```

---

## Verificación manual en Streamlit

Una vez implementados los tres tasks:

| Rol | Filtro "Todos" muestra | Panel de acción aparece en |
|---|---|---|
| `obra` | BORRADOR, REVISADO, APROBADO, DEVUELTO | Solo registros en BORRADOR |
| `interventoria` | BORRADOR, REVISADO, APROBADO, DEVUELTO | Solo registros en REVISADO |
| `supervision` | BORRADOR, REVISADO, APROBADO, DEVUELTO | Nunca |
| `operativo` | Sus propios registros (RLS) | Nunca |
