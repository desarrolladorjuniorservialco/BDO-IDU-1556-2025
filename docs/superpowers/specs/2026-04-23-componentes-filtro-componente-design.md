# Fix: Filtro por componente en páginas de Componentes Transversales

**Fecha:** 2026-04-23  
**Alcance:** `streamlit/pages/_componentes_base.py`

## Problema

`_COMPONENTE_VALOR` tenía dos defectos:

1. Clave `'ambiental'` no coincide con `filtro_tipo='ambiental-sst'` que pasa `componente_ambiental.py` → el `.get()` devolvía `None` y `load_componentes` cargaba todos los registros sin filtrar.
2. Valor `'Ambiental- SST'` (espacio antes de SST) no coincide con el valor real en BD `'Ambiental-SST'`.

Las páginas `componente_pmt.py` (`'pmt'`) y `componente_social.py` (`'social'`) ya usan las claves correctas.

## Solución (Opción A)

Corregir únicamente el dict `_COMPONENTE_VALOR` en `_componentes_base.py`:

```python
# Antes
_COMPONENTE_VALOR: dict[str, str] = {
    'ambiental': 'Ambiental- SST',
    'social':    'Social',
    'pmt':       'PMT',
}

# Después
_COMPONENTE_VALOR: dict[str, str] = {
    'ambiental-sst': 'Ambiental-SST',
    'social':        'Social',
    'pmt':           'PMT',
}
```

## Flujo de aprobación

`panel_aprobacion` en `_componentes_base.py` ya consume `APROBACION_CONFIG` correctamente y escribe contra `registros_componentes` con RLS activo. No requiere cambios.

## Archivos afectados

| Archivo | Cambio |
|---|---|
| `streamlit/pages/_componentes_base.py` | Corregir clave y valor en `_COMPONENTE_VALOR` |

## Verificación

Después del cambio, cada página debe mostrar únicamente registros con el valor de `componente` correspondiente:

| Página | `filtro_tipo` | Valor BD |
|---|---|---|
| `componente_ambiental.py` | `'ambiental-sst'` | `'Ambiental-SST'` |
| `componente_pmt.py` | `'pmt'` | `'PMT'` |
| `componente_social.py` | `'social'` | `'Social'` |
