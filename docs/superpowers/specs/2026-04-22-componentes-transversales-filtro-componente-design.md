# Diseño: Filtro por campo `componente` en módulos transversales

**Fecha:** 2026-04-22
**Estado:** Aprobado

---

## Problema

Los módulos de Componentes Transversales en Streamlit (Ambiental-SST, Social, PMT) muestran 0 registros a pesar de que la tabla `registros_componentes` en Supabase sí contiene datos sincronizados desde QField Cloud (`Reporte_Componentes.gpkg`).

**Causa raíz:** `load_componentes` filtra por `capitulo_num` (entero: 31, 32, 33), pero los registros de QField almacenan el tipo de componente en el campo `componente` (texto: `"Ambiental- SST"`, `"PMT"`, `"Social"`). El campo `capitulo_num` en estos registros corresponde al ítem de presupuesto de la actividad específica, no al tipo de componente. El filtro por `capitulo_num` no encuentra coincidencias → 0 registros.

---

## Solución

Reemplazar el filtro por `capitulo_num` con un filtro por el campo `componente` (texto exacto). Dos archivos afectados:

### 1. `streamlit/database.py` — `load_componentes`

Cambiar la firma y el filtro:

```python
# Antes
def load_componentes(estados=None, capitulo_num=None):
    ...
    if capitulo_num is not None:
        query = query.eq('capitulo_num', capitulo_num)

# Después
def load_componentes(estados=None, componente=None):
    ...
    if componente is not None:
        query = query.eq('componente', componente)
```

**Compatibilidad:** `generar_pdf.py` y `mapa.py` llaman a `load_componentes` solo con `estados=`, por lo que no se ven afectados.

### 2. `streamlit/pages/_componentes_base.py` — `panel_componentes`

Reemplazar el mapeo `_CAPITULO_NUM` por `_COMPONENTE_VALOR`:

```python
# Antes
_CAPITULO_NUM: dict[str, int] = {
    'ambiental': 31,
    'social':    32,
    'pmt':       33,
}
# ... panel_componentes llama:
df = load_componentes(estados=estados_q, capitulo_num=_CAPITULO_NUM.get(filtro_tipo))

# Después
_COMPONENTE_VALOR: dict[str, str] = {
    'ambiental': 'Ambiental- SST',
    'social':    'Social',
    'pmt':       'PMT',
}
# ... panel_componentes llama:
df = load_componentes(estados=estados_q, componente=_COMPONENTE_VALOR.get(filtro_tipo))
```

Los valores de `_COMPONENTE_VALOR` son los valores exactos (case-sensitive) del campo `componente` en Supabase, tal como los escribe QField Cloud.

---

## Alcance

- **2 archivos modificados:** `database.py`, `_componentes_base.py`
- **0 archivos nuevos**
- **0 cambios en la base de datos** (se usa el campo `componente` que ya existe)
- **0 cambios en el sync** (el campo `componente` ya se sincroniza en `sync_registros_componentes`)

---

## Archivos no afectados

| Archivo | Razón |
|---|---|
| `generar_pdf.py` | Llama `load_componentes(estados=...)` sin parámetro de tipo |
| `mapa.py` | Ídem |
| `componente_ambiental.py` | Solo pasa `filtro_tipo='ambiental'` — sin cambio |
| `componente_social.py` | Solo pasa `filtro_tipo='social'` — sin cambio |
| `componente_pmt.py` | Solo pasa `filtro_tipo='pmt'` — sin cambio |
| `sync_formularios.py` | Ya sincroniza el campo `componente` correctamente |

---

## Criterios de éxito

1. Módulo "Componente Ambiental - SST" muestra los registros con `componente = 'Ambiental- SST'`
2. Módulo "Componente Social" muestra los registros con `componente = 'Social'`
3. Módulo "Componente PMT" muestra los registros con `componente = 'PMT'`
4. `generar_pdf.py` y `mapa.py` continúan funcionando sin cambios
