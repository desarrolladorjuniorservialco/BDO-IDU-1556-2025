# PDF Bitácora Jerárquica — Diseño

**Fecha:** 2026-04-14
**Proyecto:** BDO IDU-1556-2025
**Archivos afectados:** `streamlit/pdf_generator.py`, `streamlit/pages/generar_pdf.py`

---

## Objetivo

Reemplazar el PDF plano actual por un formato jerárquico que agrupa los registros
por combinación `(fecha, tramo, CIV)`, mostrando encabezados compactos de una
sola línea seguidos de párrafos de contenido y una tabla de cantidades por sección.

---

## Estructura del PDF

### Encabezado del documento (sin cambios)
Bloque institucional existente: logo, contrato, rango de fechas, firmas al pie.

### Secciones de contenido (nuevo)

Por cada combinación única `(fecha, id_tramo, civ)` ordenada
ascendentemente por `(fecha, id_tramo, civ)`:

#### 1. Encabezado de grupo — una sola línea
```
14 de abril de 2026 – Tramo Carrera 26 entre Calle 6 y Calle 13 – CIV 154654
```
- Estilo: `Paragraph` bold 9pt, color `#0076B0`, `spaceBefore=10, spaceAfter=4`
- Formato fecha: español manual (`MESES_ES` dict), ej. `"14 de abril de 2026"`
- Si `id_tramo` es vacío/nulo: `"Sin Tramo"`
- `tramo_descripcion`: primer match de `df_cantidades[id_tramo == X]['tramo_descripcion']`; si no hay, se omite la descripción
- Si `civ` es vacío/nulo: `"Sin CIV"`

#### 2. Párrafos de contenido — uno por folio del grupo
Cada folio de `registros_reporte_diario` que pertenezca a esta combinación
genera un `Paragraph` con el formato:

```
PK {pk}. {clima}. Personal: {personal}. Maquinaria: {maquinaria}. SST: {sst}. {observaciones}
```

Reglas de cada campo:
- **PK:** campo `pk` o `civ_pk` de `registros_reporte_diario`; si es nulo se omite el prefijo
- **Clima:** de `bd_condicion_climatica` filtrado por `folio`; si hay varios registros: `"08:00 Soleado, 14:00 Nublado"`; si no hay: se omite
- **Personal:** de `bd_personal_obra` filtrado por `folio`; se muestra como `"Inspectores: N, Operativo: N, BOAL: N, Tránsito: N"`; cero se omite; si toda la fila es cero/vacío: se omite el campo
- **Maquinaria:** de `bd_maquinaria_obra` filtrado por `folio`; columnas no nulas/cero listadas como `"volquetas: N, vibrocompactador: N, …"`; si vacío: se omite
- **SST/Ambiental:** de `bd_sst_ambiental` filtrado por `folio`; igual que maquinaria; si vacío: se omite
- **Observaciones:** campo `observaciones` de `registros_reporte_diario`; si nulo/vacío: se omite

Estilo del párrafo: regular 8pt, `#4D4D4D`, `leftIndent=8, spaceAfter=3`

Si el grupo `(fecha, tramo, civ)` no tiene ningún folio en `registros_reporte_diario`
(solo tiene cantidades o componentes), se omite la sección de párrafos.

#### 3. Tabla de cantidades ejecutadas — al final de cada grupo
Columnas: **PK · Ítem · Descripción · Cantidad · Unidad · Observaciones**

Fuentes de datos (unión):
- `registros_cantidades` filtrado por `(fecha_creacion.date == fecha, id_tramo, civ)`
  → columnas: `pk`/`civ_pk`, `item_pago`, `item_descripcion`, `cantidad`, `unidad`, `observaciones`
- `registros_componentes` filtrado por `(fecha_creacion.date == fecha, id_tramo, civ)`
  → columnas: `pk`/`civ_pk`, `tipo_componente` (como ítem), `tipo_actividad` (como descripción), `cantidad`, `unidad`, `observaciones`

Anchos de columna (ancho útil ≈ 17.8 cm):

| PK | Ítem | Descripción | Cantidad | Unidad | Observaciones |
|---|---|---|---|---|---|
| 1.8 cm | 1.5 cm | 5.5 cm | 1.8 cm | 1.4 cm | resto (~5.8 cm) |

- Si una columna está vacía en todas las filas del grupo: se omite
- Cabecera: fondo `#0076B0`, texto blanco bold 7pt
- Filas: zebra blanco / `#F8FBFD`
- `repeatRows=1` para paginación
- Si no hay filas: se omite la tabla completa

---

## Cambios en `pdf_generator.py`

### Firma nueva de `generate_pdf_bitacora`
```python
def generate_pdf_bitacora(
    datos: dict[str, pd.DataFrame],   # claves: ver abajo
    contrato: dict,
    fi: date,
    ff: date,
    tipo_reporte: str,
    *,
    alerta: bool = False,
) -> bytes | None:
```

**Claves del dict `datos`:**
| Clave | Tabla fuente |
|---|---|
| `'cantidades'` | `registros_cantidades` |
| `'componentes'` | `registros_componentes` |
| `'diario'` | `registros_reporte_diario` |
| `'clima'` | `bd_condicion_climatica` |
| `'personal'` | `bd_personal_obra` |
| `'maquinaria'` | `bd_maquinaria_obra` |
| `'sst'` | `bd_sst_ambiental` |

Claves faltantes o DataFrames vacíos se tratan como `pd.DataFrame()` sin error.

### Helpers internos nuevos
- `_fecha_es(d: date) -> str` — formatea fecha en español sin locale
- `_build_group_header(fecha, tramo_id, tramo_desc, civ, styles) -> Paragraph`
- `_build_content_paragraphs(folios, df_diario, df_clima, df_personal, df_maquinaria, df_sst, styles) -> list`
- `_build_quantities_table(fecha, tramo_id, civ, df_cant, df_comp, styles, W, cm) -> Table | None`
- `_collect_groups(df_cant, df_comp, df_diario) -> list[tuple[date, str, str]]` — devuelve combinaciones únicas ordenadas

### Helpers internos eliminados
- `_build_photo_grid` — ya eliminado
- El bloque de observaciones planas y resumen estadístico del story actual — reemplazados por la nueva lógica jerárquica

---

## Cambios en `generar_pdf.py`

### Carga de datos adicionales
Cuando `formato == "PDF"`, cargar sub-tablas antes de llamar al generador:

```python
folios_diario = tuple(df_diario['folio'].dropna().tolist()) if not df_diario.empty else ()
df_clima     = load_bd_clima(folios_diario)
df_personal  = load_bd_personal(folios_diario)
df_maquinaria= load_bd_maquinaria(folios_diario)
df_sst       = load_bd_sst(folios_diario)

datos = {
    'cantidades':  frames.get('Cantidades de Obra',        pd.DataFrame()),
    'componentes': frames.get('Componentes Transversales', pd.DataFrame()),
    'diario':      frames.get('Reporte Diario',            pd.DataFrame()),
    'clima':       df_clima,
    'personal':    df_personal,
    'maquinaria':  df_maquinaria,
    'sst':         df_sst,
}
pdf_bytes = generate_pdf_bitacora(datos, contrato, fi, ff, "Bitácora Consolidada")
```

### Imports nuevos en `generar_pdf.py`
```python
from database import (
    load_cantidades, load_componentes, load_reporte_diario, load_contrato,
    load_bd_clima, load_bd_personal, load_bd_maquinaria, load_bd_sst,
)
```

---

## Manejo de errores

- Si `datos` está completamente vacío (todos los DataFrames vacíos): retornar `None`, mostrar `st.warning` en lugar de `st.error`
- Si un grupo no tiene datos suficientes para renderizar (sin folio diario Y sin cantidades): saltar el grupo silenciosamente
- Excepciones en `doc.build` → `_log.exception(...)`, retornar `None`

---

## Fuera de alcance

- Exportación CSV y Excel: sin cambios
- Filtros de la página `generar_pdf.py`: sin cambios
- Registro fotográfico: ya eliminado, no se reincorpora
- Sección de firmas: se mantiene al pie del documento
