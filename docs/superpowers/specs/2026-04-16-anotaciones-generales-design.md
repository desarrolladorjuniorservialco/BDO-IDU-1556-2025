# Diseño: Anotaciones Generales

**Fecha:** 2026-04-16  
**Proyecto:** BDO IDU-1556-2025  
**Archivo afectado principal:** `streamlit/pages/anotaciones.py`

---

## Contexto

La página `anotaciones.py` actualmente muestra registros de cantidades aprobados provenientes de QFieldCloud. Se reemplaza completamente por un sistema de **anotaciones generales de bitácora**, desvinculado de reportes de campo, que permite a todos los roles (excepto `supervisor`) escribir notas libres con referencia opcional a tramo, CIV y PK.

---

## Requisitos funcionales

| # | Requisito |
|---|-----------|
| 1 | Todos los roles autenticados pueden **leer** el historial de anotaciones |
| 2 | El rol `supervisor` puede leer pero **no puede crear** anotaciones |
| 3 | Campos del formulario: Fecha (requerida), Tramo, CIV, PK (opcionales), Anotación (requerida) |
| 4 | El historial se muestra como un **chat estilo red social**: burbuja por anotación, más reciente abajo |
| 5 | Cada burbuja muestra: nombre del autor, rol, empresa, fecha de la anotación, pills de Tramo/CIV/PK si aplican, y el texto |
| 6 | El compositor de nueva anotación está en la parte **inferior de la página** |
| 7 | Los campos Fecha/Tramo/CIV/PK se llenan en una fila compacta encima de `st.chat_input()` |
| 8 | `st.chat_input()` se fija al fondo de la página (comportamiento nativo de Streamlit) |
| 9 | El envío requiere fecha + anotación; si falta alguno, se muestra advertencia sin recargar |
| 10 | El historial se recarga automáticamente tras enviar una anotación (`st.rerun()`) |

---

## Arquitectura de la página

### Layout

```
section_badge("Anotaciones Generales", "purple")
h3 "Bitácora General"

[st.container(height=500)]          ← historial chat scrollable
  por cada anotación (ASC created_at):
    st.chat_message(name=usuario_nombre, avatar="user")
      pills: rol · empresa · fecha
      pills opcionales: Tramo · CIV · PK
      texto de anotación

── solo si rol != "supervisor" ──

[fila compacta de metadatos]        ← session_state, fuera de form
  col1: date_input("Fecha", key="ag_fecha")
  col2: text_input("Tramo", key="ag_tramo")
  col3: text_input("CIV",   key="ag_civ")
  col4: text_input("PK",    key="ag_pk")

st.chat_input("Escribe tu anotación...")   ← fijo al fondo de página
  → al enviar: lee session_state para metadata
  → valida: fecha presente (date_input siempre tiene valor, OK)
  → inserta en Supabase vía get_user_client()
  → limpia session_state de tramo/civ/pk (fecha vuelve a hoy por defecto)
  → clear_cache() + st.rerun()
```

### Control de acceso

- Rol `supervisor`: renderiza el historial únicamente; la fila de metadatos y el `st.chat_input()` **no se renderizan** (no se deshabilitan, simplemente no existen en el DOM).
- Todos los demás roles: historial + compositor.

---

## Base de datos — Supabase

### Tabla `anotaciones_generales`

```sql
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
```

**Justificación de desnormalización:** `usuario_nombre`, `usuario_rol` y `usuario_empresa` se copian del perfil al insertar. Esto sigue el patrón existente en el proyecto (e.g. `usuario_qfield` en otras tablas) y evita JOINs al cargar el historial.

### Row Level Security

```sql
ALTER TABLE anotaciones_generales ENABLE ROW LEVEL SECURITY;

-- Lectura: todos los usuarios autenticados
CREATE POLICY "ag_select_authenticated"
ON anotaciones_generales
FOR SELECT TO authenticated
USING (true);

-- Inserción: autenticados con rol distinto de 'supervisor'
CREATE POLICY "ag_insert_non_supervisor"
ON anotaciones_generales
FOR INSERT TO authenticated
WITH CHECK (
    (SELECT rol FROM perfiles WHERE id = auth.uid()) != 'supervisor'
);

-- No se permiten UPDATE ni DELETE: el registro es inmutable (bitácora)
```

### Índice recomendado

```sql
CREATE INDEX IF NOT EXISTS idx_ag_created_at
ON anotaciones_generales (created_at ASC);
```

---

## Módulo `database.py` — nuevo loader

```python
@st.cache_data(ttl=30)
def load_anotaciones_generales(limit: int = 300) -> pd.DataFrame:
    """Anotaciones generales de bitácora, ordenadas ASC por created_at.
    Carga las últimas `limit` anotaciones (default 300).
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

TTL de 30 s (más bajo que otros loaders) para que el historial se sienta responsivo. Límite de 300 registros para evitar payloads grandes; suficiente para una bitácora activa.

---

## Módulos a modificar

| Archivo | Cambio |
|---------|--------|
| `streamlit/pages/anotaciones.py` | Reescritura completa de `page_anotaciones()` |
| `streamlit/database.py` | Agregar `load_anotaciones_generales()` |
| `streamlit/config.py` | Sin cambios necesarios (`NAV_ACCESS["Anotaciones"]` ya incluye todos los roles) |

---

## Seguridad

- Inserción vía `get_user_client(access_token)` → RLS activo.
- `st.chat_input()` tiene límite de caracteres configurado (`max_chars=2000`).
- El texto de anotación se inserta como parámetro Supabase (sin concatenación SQL directa).
- Rol verificado en RLS a nivel de base de datos; la restricción UI (no renderizar el compositor para `supervisor`) es una capa adicional, no la única.

---

## Fuera de alcance

- Edición o eliminación de anotaciones.
- Filtrado del historial por fecha/tramo/usuario.
- Adjuntar fotos a las anotaciones.
