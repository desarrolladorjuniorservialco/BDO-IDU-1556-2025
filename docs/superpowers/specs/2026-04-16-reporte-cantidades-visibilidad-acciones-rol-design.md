# Diseño: Visibilidad y acciones por rol en Reporte de Cantidades

**Fecha:** 2026-04-16
**Área:** `streamlit/config.py`, `streamlit/pages/reporte_cantidades.py`

---

## Contexto

El flujo de aprobación de cantidades de obra tiene tres actores:

1. **operativo** — sube registros desde QField; llegan en estado `BORRADOR`.
2. **obra** (residente de obra) — revisa borradores; aprueba o devuelve.
3. **interventoria** (residente técnico de interventoría) — revisa registros ya revisados por obra; aprueba o devuelve definitivamente.
4. **supervision** — observa el proceso; sin acciones.
5. **admin** — mismos permisos de acción que interventoría.

El estado de un registro sigue la cadena:

```
BORRADOR → (obra aprueba) → REVISADO → (interventoria aprueba) → APROBADO (inmutable)
         ↘ (obra devuelve) → DEVUELTO ↗ (obra vuelve a revisar)
                                      ↘ (interventoria devuelve) → DEVUELTO
```

---

## Problema actual

`APROBACION_CONFIG` usa un único campo `estados_visibles` para dos responsabilidades distintas:

1. **Visibilidad** — qué estados aparecen en el dropdown de filtros y se cargan de BD.
2. **Accionabilidad** — en qué estados se muestra el panel de aprobar/devolver.

Esto hace que `obra` solo vea `BORRADOR`/`DEVUELTO` e `interventoria` solo vea `REVISADO`, cuando el requerimiento es que ambos roles vean todos los estados pero solo puedan actuar sobre los que les corresponden.

---

## Diseño

### 1. Separación de visibilidad y accionabilidad en `APROBACION_CONFIG`

La tupla pasa de 3 a **4 elementos**:

```python
rol → (estados_vis, estado_apr, campos, estados_accion)
```

| Campo | Tipo | Descripción |
|---|---|---|
| `estados_vis` | `list[str] \| None` | Estados que se cargan y filtran. `None` = todos. |
| `estado_apr` | `str \| None` | Estado al que pasa el registro al aprobar. |
| `campos` | `dict \| None` | Campos de BD que escribe la acción. `None` = sin panel. |
| `estados_accion` | `list[str] \| None` | Estados en los que se habilita el panel de acción. `None` = sin panel. |

### 2. Configuración por rol

| Rol | `estados_vis` | `estados_accion` | Al aprobar |
|---|---|---|---|
| `operativo` | `None` | `None` | sin panel |
| `obra` | `None` (todos) | `['BORRADOR']` | → `REVISADO` |
| `interventoria` | `None` (todos) | `['REVISADO']` | → `APROBADO` |
| `supervision` | `None` (todos) | `None` | sin panel |
| `admin` | `None` (todos) | `['REVISADO']` | → `APROBADO` |

### 3. Cambios en `reporte_cantidades.py`

**a) Desempaque de la tupla**

```python
estados_vis, estado_apr, campos, estados_accion = cfg
```

**b) Dropdown de filtros**

Cuando `estados_vis` es `None`, el dropdown ofrece todos los estados:

```python
opts = (["Todos"] + estados_vis) if estados_vis else (
    ["Todos", "BORRADOR", "REVISADO", "APROBADO", "DEVUELTO"]
)
```

*(Sin cambio en la lógica actual — ya estaba preparado para `None`.)*

**c) Carga de datos**

Cuando `estados_vis` es `None` y el usuario selecciona "Todos", se carga sin filtro de estado (comportamiento actual para `None`).

**d) Panel de aprobación**

`_panel_aprobacion` recibe el nuevo parámetro `estados_accion`. Si el estado actual del registro **no está** en `estados_accion`, muestra solo el historial de trazabilidad (modo lectura):

```python
def _panel_aprobacion(reg, perfil, campos, estado_apr, estados_accion):
    est_actual = str(reg.get('estado', '')).upper()
    ...
    # Solo mostrar botones si el estado del registro es accionable
    if not campos or not estados_accion or est_actual not in estados_accion:
        st.caption(f"Estado: {est_actual}")
        return
    ...
```

La llamada en el loop de registros pasa el nuevo argumento:

```python
_panel_aprobacion(reg, perfil, campos, estado_apr, estados_accion)
```

---

## Sin cambios en BD ni RLS

- La tabla `registros_cantidades` no cambia.
- El RLS existente ya permite que `obra` e `interventoria` lean todos los registros del proyecto.
- No se agregan ni eliminan columnas.

---

## Archivos afectados

| Archivo | Cambio |
|---|---|
| `streamlit/config.py` | Ampliar tuplas de `APROBACION_CONFIG` a 4 elementos; ajustar `estados_vis` a `None` para todos los roles con visibilidad total |
| `streamlit/pages/reporte_cantidades.py` | Desempaquetar 4 valores; pasar `estados_accion` a `_panel_aprobacion`; ajustar lógica del panel |

---

## Criterios de aceptación

- [ ] `obra` ve registros en todos los estados al seleccionar "Todos" en el filtro.
- [ ] `obra` solo ve el panel de aprobar/devolver en registros con estado `BORRADOR`.
- [ ] `interventoria` ve registros en todos los estados.
- [ ] `interventoria` solo ve el panel de aprobar/devolver en registros con estado `REVISADO`.
- [ ] `supervision` ve registros en todos los estados sin panel de acciones en ningún estado.
- [ ] El historial de trazabilidad sigue siendo visible para todos los roles en todos los registros.
- [ ] Al aprobar o devolver, el comportamiento y los campos escritos en BD no cambian.
