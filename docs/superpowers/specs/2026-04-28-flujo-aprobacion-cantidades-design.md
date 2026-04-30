# Diseño: Corrección del flujo de aprobación — Anotaciones Diario de Obra

**Fecha:** 2026-04-28  
**Proyecto:** BDO-IDU-React  
**Página principal:** `src/app/(dashboard)/anotaciones-diario/`  
**Componentes compartidos:** `ApprovalPanel`, `ApprovalHistory`, `approval.ts`  
**Referencia BD:** `SupaBaseSQLEditor/SupaBase/001_TABLAS.sql`, `002_RLS.sql`

---

## Contexto

La página `anotaciones-diario` usa el componente compartido `ApprovalPanel` para gestionar un flujo de aprobación de dos niveles sobre la tabla `registros_reporte_diario`. Los componentes compartidos también son usados por `reporte-cantidades`, por lo que los cambios en componentes compartidos benefician ambas páginas.

---

## Flujo de aprobación (fuente de verdad: negocio + RLS)

```
operativo crea  →  BORRADOR
                       │
    obra revisa   BORRADOR / DEVUELTO  →  REVISADO  (solo aprueba, no devuelve)
                                               │
                                   interventoria / admin
                                   REVISADO → APROBADO  (nivel 2, inmutable=TRUE)
                                           ↓ devolver
                                       DEVUELTO  ──→ regresa a obra para corrección
```

**Regla de negocio clave:** `obra` únicamente revisa y aprueba. El botón "Devolver" solo aparece para `interventoria` y `admin`.

**Roles y permisos:**

| Rol | Acción | Actúa sobre | Estado resultante | Puede devolver |
|-----|--------|-------------|-------------------|----------------|
| operativo | — | — | — | No |
| obra | Aprobar | BORRADOR, DEVUELTO | REVISADO | **No** |
| interventoria | Aprobar | REVISADO | APROBADO | Sí → DEVUELTO |
| supervision | — | — | — | No |
| admin | Aprobar | REVISADO | APROBADO | Sí → DEVUELTO |

---

## Bugs y gaps

### Bug 1 — `approval.ts` guarda email en columna UUID (FK violation)

**Archivo:** `src/lib/supabase/actions/approval.ts`  
**Columnas afectadas:** `aprobado_residente UUID REFERENCES perfiles(id)`, `aprobado_interventor UUID REFERENCES perfiles(id)`

```ts
// Actual — FALLA: intenta guardar email en columna UUID
[config.campos.campo_apr]: user?.email ?? user?.id,

// Correcto
[config.campos.campo_apr]: user?.id,
```

### Bug 2 — `approval.ts` guarda DATE en columna TIMESTAMPTZ

**Archivo:** `src/lib/supabase/actions/approval.ts`  
**Columnas afectadas:** `fecha_residente TIMESTAMPTZ`, `fecha_interventor TIMESTAMPTZ`

```ts
// Actual — trunca la hora
[config.campos.campo_fecha]: new Date().toISOString().slice(0, 10),

// Correcto
[config.campos.campo_fecha]: new Date().toISOString(),
```

> Nota: el trigger `tg_inmutable` auto-llena `fecha_interventor = NOW()` cuando `estado = 'APROBADO'`. Para nivel 2 la fecha manual es redundante pero inofensiva.

### Gap 3 — `obra` tiene acceso al botón devolver (incorrecto según negocio)

**Archivo:** `src/components/approval/ApprovalPanel.tsx` + `src/lib/config.ts`  
El panel renderiza el formulario "Devolver" para todos los roles con `puedeAccionar = true`, incluyendo obra. La lógica de negocio establece que obra **solo revisa**, nunca devuelve.

**Solución:** agregar `puedeDevolver: boolean` a `AprobacionConfig`. Solo `interventoria` y `admin` tienen `puedeDevolver: true`.

### Gap 4 — `obra.estadosAccion` no incluye DEVUELTO

**Archivo:** `src/lib/config.ts`  
Los registros DEVUELTOS (rechazados por interventoria) regresan a obra para corrección. La RLS `rd_obra_update` permite USING `estado IN ('BORRADOR','DEVUELTO')`, pero el config solo tiene `estadosAccion: ['BORRADOR']`.

```ts
// Actual
obra: { estadosAccion: ['BORRADOR'], ... }

// Correcto
obra: { estadosAccion: ['BORRADOR', 'DEVUELTO'], ... }
```

### Gap 5 — `ApprovalHistory` muestra UUID crudo en lugar de nombre

**Archivo:** `src/components/approval/ApprovalHistory.tsx` + `src/lib/supabase/actions/reporte-diario.ts`  
`aprobado_residente` y `aprobado_interventor` son UUID FK a `perfiles`. El componente los muestra directamente. Se necesita JOIN en `fetchReporteDiario` para obtener los nombres.

### Gap 6 — Cantidad por defecto ignora la validación previa del rol

**Archivo:** `src/components/approval/ApprovalPanel.tsx`  
El formulario de aprobación parte siempre de `registro.cantidad`. Debe usar la cantidad ya validada por el nivel que actúa (`cant_residente` para obra, `cant_interventor` para interventoria).

```ts
// Actual
defaultValues: { cantidad_validada: registro.cantidad ?? 0 }

// Correcto
defaultValues: {
  cantidad_validada: registro[config.campos.campo_cant] ?? registro.cantidad ?? 0
}
```

### Gap 7 — Sin feedback al usuario tras aprobar o devolver

**Archivo:** `src/components/approval/ApprovalPanel.tsx`  
Errores capturados con `console.error` únicamente. No hay mensaje visible para el usuario ni confirmación de éxito.

---

## Arquitectura de la solución

### Cambio 1 — `src/lib/config.ts`

Agregar `puedeDevolver: boolean` a la interfaz `AprobacionConfig`:

```ts
export interface AprobacionConfig {
  estadosAccion:    Estado[];
  estadoResultante: Estado;
  puedeDevolver:    boolean;   // nuevo
  campos:           AprobacionCampos;
}
```

Actualizar los tres roles:

```ts
obra: {
  estadosAccion:    ['BORRADOR', 'DEVUELTO'],  // agrega DEVUELTO
  estadoResultante: 'REVISADO',
  puedeDevolver:    false,                      // nuevo
  campos: { /* sin cambios */ }
},
interventoria: {
  estadosAccion:    ['REVISADO'],
  estadoResultante: 'APROBADO',
  puedeDevolver:    true,                       // nuevo
  campos: { /* sin cambios */ }
},
admin: {
  estadosAccion:    ['REVISADO'],
  estadoResultante: 'APROBADO',
  puedeDevolver:    true,                       // nuevo
  campos: { /* sin cambios */ }
},
```

### Cambio 2 — `src/lib/supabase/actions/approval.ts`

- `campo_apr`: `user?.id` (eliminar `user?.email ??`)
- `campo_fecha`: `new Date().toISOString()` (eliminar `.slice(0, 10)`)
- En `devolver`: agregar guardia `if (!config.puedeDevolver) throw new Error(...)` como defensa en el servidor
- Aplica a ambas funciones: `aprobar` y `devolver`

### Cambio 3 — `src/lib/supabase/actions/reporte-diario.ts`

`fetchReporteDiario` agrega embedded resources de PostgREST para nombres de aprobadores:

```ts
.select(`
  *,
  residente:perfiles!aprobado_residente(nombre),
  interventor:perfiles!aprobado_interventor(nombre)
`)
```

Sin cambio de esquema. Si el registro aún no tiene aprobador el objeto embedded es `null`.

### Cambio 4 — `src/components/approval/ApprovalHistory.tsx`

Usar `registro.residente?.nombre` y `registro.interventor?.nombre` en lugar de los UUIDs directos. Fallback al UUID si el perfil no se resuelve (caso defensivo).

### Cambio 5 — `src/components/approval/ApprovalPanel.tsx`

Tres cambios en el mismo archivo:

1. **Ocultar formulario devolver** cuando `!config.puedeDevolver`:
   ```tsx
   {config.puedeDevolver && (
     <form onSubmit={devForm.handleSubmit(handleDevolver)} ...>
       ...
     </form>
   )}
   ```

2. **Default de cantidad** usa campo del rol:
   ```ts
   defaultValues: {
     cantidad_validada: registro[config.campos.campo_cant] ?? registro.cantidad ?? 0
   }
   ```

3. **Feedback inline**: añadir `useState<string | null>` para `feedbackError` y `feedbackSuccess`. Mostrar mensaje bajo el botón de submit. Limpiar al iniciar la siguiente transición.

---

## Archivos modificados

| Archivo | Tipo de cambio | Impacto |
|---------|---------------|---------|
| `src/lib/config.ts` | Agrega `puedeDevolver`, actualiza 3 roles | Ambas páginas |
| `src/lib/supabase/actions/approval.ts` | Bug fix UUID + TIMESTAMPTZ + guardia devolver | Ambas páginas |
| `src/lib/supabase/actions/reporte-diario.ts` | JOIN con perfiles para nombres | Anotaciones diario |
| `src/components/approval/ApprovalHistory.tsx` | Muestra nombres en lugar de UUIDs | Ambas páginas |
| `src/components/approval/ApprovalPanel.tsx` | Oculta devolver para obra + cantidad + feedback | Ambas páginas |

---

## Restricciones

- Sin cambios de esquema SQL.
- Sin nuevas dependencias npm.
- La inmutabilidad (`inmutable = TRUE`) la gestiona el trigger `tg_inmutable`; el frontend no la verifica.
- `supervision` y `operativo` no tienen entrada en `APROBACION_CONFIG` — correcto: `puedeAccionar = false`, solo historial visible.
- Los cambios en componentes compartidos afectan también a `reporte-cantidades` de forma positiva, pero el `JOIN` de nombres solo se añade a `fetchReporteDiario` en este scope. `fetchCantidades` puede actualizarse en un paso posterior si se requiere.
