# Componentes Transversales — Filtro por campo `componente` — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer que los módulos Ambiental-SST, Social y PMT en Streamlit muestren los registros de `registros_componentes` filtrando por el campo `componente` (texto) en lugar de `capitulo_num` (entero).

**Architecture:** Dos cambios quirúrgicos: (1) `load_componentes` en `database.py` reemplaza el parámetro `capitulo_num` por `componente`; (2) `_componentes_base.py` reemplaza el mapeo `_CAPITULO_NUM` por `_COMPONENTE_VALOR` y actualiza la llamada. Sin cambios en BD, sin archivos nuevos.

**Tech Stack:** Python 3.11, Supabase Python SDK, Streamlit, pytest

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `streamlit/database.py` | Parámetro `capitulo_num → componente` en `load_componentes` |
| `streamlit/pages/_componentes_base.py` | Mapeo `_CAPITULO_NUM → _COMPONENTE_VALOR`, llamada actualizada |
| `streamlit/tests/test_componentes_filtro.py` | Test nuevo: cobertura del mapeo y del parámetro |

---

### Task 1: Test del mapeo `_COMPONENTE_VALOR`

**Files:**
- Create: `streamlit/tests/test_componentes_filtro.py`

- [ ] **Step 1: Crear el archivo de test**

```python
"""
Tests para el mapeo _COMPONENTE_VALOR y la firma de load_componentes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import inspect
import pytest


class TestComponenteValorMapping:
    """El mapeo filtro_tipo → valor del campo componente en Supabase."""

    def _get_mapping(self):
        # Importamos el símbolo directamente del módulo
        import importlib, types
        # Cargamos el módulo sin ejecutar Streamlit (solo necesitamos la constante)
        spec = importlib.util.spec_from_file_location(
            "_componentes_base",
            os.path.join(os.path.dirname(__file__), "..", "pages", "_componentes_base.py"),
        )
        # No podemos importar el módulo completo (depende de streamlit),
        # así que verificamos la constante leyendo el archivo fuente.
        src = open(os.path.join(os.path.dirname(__file__),
                                "..", "pages", "_componentes_base.py")).read()
        return src

    def test_ambiental_valor_exacto(self):
        src = self._get_mapping()
        assert "'ambiental': 'Ambiental- SST'" in src

    def test_social_valor_exacto(self):
        src = self._get_mapping()
        assert "'social':    'Social'" in src or "'social': 'Social'" in src

    def test_pmt_valor_exacto(self):
        src = self._get_mapping()
        assert "'pmt':       'PMT'" in src or "'pmt': 'PMT'" in src

    def test_capitulo_num_no_existe_en_mapeo(self):
        """El mapeo antiguo _CAPITULO_NUM no debe existir."""
        src = self._get_mapping()
        assert '_CAPITULO_NUM' not in src

    def test_componente_valor_existe_en_mapeo(self):
        src = self._get_mapping()
        assert '_COMPONENTE_VALOR' in src


class TestLoadComponentesFirma:
    """load_componentes debe aceptar `componente` y NO `capitulo_num`."""

    def _get_source(self):
        return open(os.path.join(os.path.dirname(__file__),
                                 "..", "database.py")).read()

    def test_parametro_componente_existe(self):
        src = self._get_source()
        assert 'componente: str | None' in src or 'componente=None' in src

    def test_parametro_capitulo_num_no_existe(self):
        src = self._get_source()
        assert 'capitulo_num' not in src

    def test_filtro_usa_campo_componente(self):
        src = self._get_source()
        assert "query.eq('componente', componente)" in src
```

- [ ] **Step 2: Ejecutar el test para verificar que falla**

```bash
cd streamlit && python -m pytest tests/test_componentes_filtro.py -v
```

Salida esperada: FAILED — `_CAPITULO_NUM` existe, `_COMPONENTE_VALOR` no existe, `capitulo_num` existe en `database.py`.

---

### Task 2: Cambiar `load_componentes` en `database.py`

**Files:**
- Modify: `streamlit/database.py:183-197`

- [ ] **Step 1: Reemplazar el parámetro y el filtro**

En `streamlit/database.py`, localizar la función `load_componentes` (líneas 182–197) y reemplazarla por:

```python
@st.cache_data(ttl=60)
def load_componentes(
    estados: list[str] | None = None,
    componente: str | None = None,
) -> pd.DataFrame:
    """Registros de componentes transversales."""
    def _q():
        sb    = get_supabase()
        query = sb.table('registros_componentes').select('*')
        if estados:
            query = query.in_('estado', estados)
        if componente is not None:
            query = query.eq('componente', componente)
        return _paginate(query.order('fecha_creacion', desc=True))

    return _safe_query(_q, context='load_componentes')
```

- [ ] **Step 2: Ejecutar los tests parciales**

```bash
cd streamlit && python -m pytest tests/test_componentes_filtro.py::TestLoadComponentesFirma -v
```

Salida esperada: todos los tests de `TestLoadComponentesFirma` en PASSED.

---

### Task 3: Cambiar el mapeo y la llamada en `_componentes_base.py`

**Files:**
- Modify: `streamlit/pages/_componentes_base.py:163-168` (mapeo)
- Modify: `streamlit/pages/_componentes_base.py:231-234` (llamada)

- [ ] **Step 1: Reemplazar el mapeo `_CAPITULO_NUM` por `_COMPONENTE_VALOR`**

Localizar el bloque (líneas 163–168):

```python
# Mapeo filtro_tipo → capitulo_num en presupuesto_componentes_bd
_CAPITULO_NUM: dict[str, int] = {
    'ambiental': 31,
    'social':    32,
    'pmt':       33,
}
```

Reemplazarlo por:

```python
# Mapeo filtro_tipo → valor exacto del campo componente en registros_componentes
_COMPONENTE_VALOR: dict[str, str] = {
    'ambiental': 'Ambiental- SST',
    'social':    'Social',
    'pmt':       'PMT',
}
```

- [ ] **Step 2: Actualizar la llamada a `load_componentes`**

Localizar en `panel_componentes` (alrededor de la línea 231):

```python
    df = load_componentes(
        estados=estados_q,
        capitulo_num=_CAPITULO_NUM.get(filtro_tipo) if filtro_tipo else None,
    )
```

Reemplazarlo por:

```python
    df = load_componentes(
        estados=estados_q,
        componente=_COMPONENTE_VALOR.get(filtro_tipo) if filtro_tipo else None,
    )
```

- [ ] **Step 3: Ejecutar todos los tests**

```bash
cd streamlit && python -m pytest tests/ -v
```

Salida esperada: todos los tests en PASSED (incluidos los de `test_reporte_cantidades_config.py`).

---

### Task 4: Commit

- [ ] **Step 1: Commit de los cambios**

```bash
git add streamlit/database.py streamlit/pages/_componentes_base.py streamlit/tests/test_componentes_filtro.py
git commit -m "fix: filtrar componentes por campo componente en lugar de capitulo_num

Los módulos Ambiental-SST, Social y PMT ahora filtran registros_componentes
usando el campo texto componente ('Ambiental- SST', 'Social', 'PMT') que
es el campo real sincronizado desde QField Cloud. El filtro anterior por
capitulo_num devolvía 0 resultados porque ese campo no identifica el tipo
de componente en el formulario Reporte_Componentes.gpkg."
```
