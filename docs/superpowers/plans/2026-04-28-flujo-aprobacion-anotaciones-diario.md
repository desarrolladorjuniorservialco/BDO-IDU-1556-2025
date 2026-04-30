# Flujo de Aprobación — Anotaciones Diario Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir 2 bugs críticos y 4 gaps de consistencia en el flujo de aprobación de la página `anotaciones-diario`, alineando el código React con el esquema Supabase y la lógica de negocio.

**Architecture:** Los cambios se dividen en tres capas: (1) configuración de roles (`config.ts`), (2) acción de servidor compartida (`approval.ts`) y consulta de datos (`reporte-diario.ts`), (3) componentes compartidos de UI (`ApprovalPanel`, `ApprovalHistory`). Los cambios en componentes compartidos benefician también a `reporte-cantidades`.

**Tech Stack:** Next.js 15 App Router, TypeScript, Supabase (PostgREST), React Hook Form + Zod, Vitest + Testing Library

---

## File Map

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `src/lib/config.ts` | Modificar | Agrega `puedeDevolver`, actualiza `obra.estadosAccion` |
| `src/lib/config.test.ts` | Crear | Verifica estructura correcta de `APROBACION_CONFIG` |
| `src/lib/supabase/actions/approval.ts` | Modificar | Corrige UUID, TIMESTAMPTZ, agrega guardia devolver |
| `src/lib/supabase/actions/reporte-diario.ts` | Modificar | JOIN con perfiles para nombres de aprobadores |
| `src/components/approval/ApprovalHistory.tsx` | Modificar | Usa nombres resueltos en lugar de UUIDs |
| `src/components/approval/ApprovalPanel.tsx` | Modificar | Oculta devolver para obra, corrige cantidad, agrega feedback |
| `src/components/approval/ApprovalPanel.test.tsx` | Crear | Verifica renderizado condicional del formulario devolver |

---

## Task 1: Actualizar `config.ts` — `puedeDevolver` y `obra.estadosAccion`

**Files:**
- Modify: `src/lib/config.ts`
- Create: `src/lib/config.test.ts`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/lib/config.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { APROBACION_CONFIG } from './config';

describe('APROBACION_CONFIG', () => {
  it('obra no puede devolver', () => {
    expect(APROBACION_CONFIG.obra?.puedeDevolver).toBe(false);
  });

  it('obra actúa sobre BORRADOR y DEVUELTO', () => {
    expect(APROBACION_CONFIG.obra?.estadosAccion).toContain('BORRADOR');
    expect(APROBACION_CONFIG.obra?.estadosAccion).toContain('DEVUELTO');
  });

  it('interventoria puede devolver', () => {
    expect(APROBACION_CONFIG.interventoria?.puedeDevolver).toBe(true);
  });

  it('admin puede devolver', () => {
    expect(APROBACION_CONFIG.admin?.puedeDevolver).toBe(true);
  });

  it('todos los roles tienen puedeDevolver definido', () => {
    for (const [rol, cfg] of Object.entries(APROBACION_CONFIG)) {
      expect(cfg.puedeDevolver, `${rol} debe tener puedeDevolver definido`).toBeDefined();
    }
  });
});
```

- [ ] **Step 2: Ejecutar para confirmar que falla**

```bash
cd bdo_idu_react/BDO_React
npx vitest run src/lib/config.test.ts
```

Resultado esperado: FAIL — `puedeDevolver` no existe aún en el tipo.

- [ ] **Step 3: Actualizar `src/lib/config.ts`**

Reemplazar el contenido del archivo con:

```typescript
import type { Rol, Estado } from '@/types/database';

export const ROL_LABELS: Record<Rol, string> = {
  operativo:     'Inspector de Campo',
  obra:          'Residente de Obra',
  interventoria: 'Interventoría IDU',
  supervision:   'Supervisión IDU',
  admin:         'Administrador',
};

const TODOS: Rol[] = ['operativo', 'obra', 'interventoria', 'supervision', 'admin'];
const GESTION: Rol[] = ['obra', 'interventoria', 'supervision', 'admin'];

export const NAV_ACCESS: Record<string, Rol[]> = {
  'estado-actual':         TODOS,
  'anotaciones':           TODOS,
  'anotaciones-diario':    TODOS,
  'reporte-cantidades':    TODOS,
  'componente-ambiental':  TODOS,
  'componente-social':     TODOS,
  'componente-pmt':        TODOS,
  'seguimiento-pmts':      TODOS,
  'mapa-ejecucion':        GESTION,
  'presupuesto':           GESTION,
  'correspondencia':       GESTION,
  'generar-informe':       GESTION,
};

export interface NavCategory {
  label: string;
  highlight: boolean;
  pages: { label: string; href: string }[];
}

export const NAV_CATEGORIES: NavCategory[] = [
  {
    label: 'General',
    highlight: false,
    pages: [
      { label: 'Estado Actual',        href: '/estado-actual' },
      { label: 'Mapa Ejecución',       href: '/mapa-ejecucion' },
      { label: 'Presupuesto',          href: '/presupuesto' },
      { label: 'Correspondencia',      href: '/correspondencia' },
    ],
  },
  {
    label: 'Reportes',
    highlight: true,
    pages: [
      { label: 'Anotaciones',          href: '/anotaciones' },
      { label: 'Anotaciones Diario',   href: '/anotaciones-diario' },
      { label: 'Reporte Cantidades',   href: '/reporte-cantidades' },
    ],
  },
  {
    label: 'Componentes Transversales',
    highlight: true,
    pages: [
      { label: 'Comp. Ambiental',      href: '/componente-ambiental' },
      { label: 'Comp. Social',         href: '/componente-social' },
      { label: 'Comp. PMT',            href: '/componente-pmt' },
      { label: 'Seguimiento PMTs',     href: '/seguimiento-pmts' },
    ],
  },
  {
    label: 'Informe',
    highlight: true,
    pages: [
      { label: 'Generar Informe',      href: '/generar-informe' },
    ],
  },
];

export const PAGE_COLOR: Record<string, string> = {
  'estado-actual':        'blue',
  'anotaciones':          'purple',
  'anotaciones-diario':   'purple',
  'generar-informe':      'teal',
  'mapa-ejecucion':       'teal',
  'presupuesto':          'orange',
  'correspondencia':      'teal',
  'reporte-cantidades':   'blue',
  'componente-ambiental': 'green',
  'componente-social':    'orange',
  'componente-pmt':       'purple',
  'seguimiento-pmts':     'red',
};

export interface AprobacionCampos {
  campo_cant:   string;
  campo_estado: string;
  campo_apr:    string;
  campo_fecha:  string;
  campo_obs:    string;
}

export interface AprobacionConfig {
  estadosAccion:    Estado[];
  estadoResultante: Estado;
  puedeDevolver:    boolean;
  campos:           AprobacionCampos;
}

export const APROBACION_CONFIG: Partial<Record<Rol, AprobacionConfig>> = {
  obra: {
    estadosAccion:    ['BORRADOR', 'DEVUELTO'],
    estadoResultante: 'REVISADO',
    puedeDevolver:    false,
    campos: {
      campo_cant:   'cant_residente',
      campo_estado: 'estado_residente',
      campo_apr:    'aprobado_residente',
      campo_fecha:  'fecha_residente',
      campo_obs:    'obs_residente',
    },
  },
  interventoria: {
    estadosAccion:    ['REVISADO'],
    estadoResultante: 'APROBADO',
    puedeDevolver:    true,
    campos: {
      campo_cant:   'cant_interventor',
      campo_estado: 'estado_interventor',
      campo_apr:    'aprobado_interventor',
      campo_fecha:  'fecha_interventor',
      campo_obs:    'obs_interventor',
    },
  },
  admin: {
    estadosAccion:    ['REVISADO'],
    estadoResultante: 'APROBADO',
    puedeDevolver:    true,
    campos: {
      campo_cant:   'cant_interventor',
      campo_estado: 'estado_interventor',
      campo_apr:    'aprobado_interventor',
      campo_fecha:  'fecha_interventor',
      campo_obs:    'obs_interventor',
    },
  },
};
```

- [ ] **Step 4: Ejecutar test para confirmar que pasa**

```bash
npx vitest run src/lib/config.test.ts
```

Resultado esperado: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add src/lib/config.ts src/lib/config.test.ts
git commit -m "fix(config): add puedeDevolver, obra actua sobre BORRADOR y DEVUELTO"
```

---

## Task 2: Corregir `approval.ts` — UUID, TIMESTAMPTZ y guardia devolver

**Files:**
- Modify: `src/lib/supabase/actions/approval.ts`

No hay test unitario para esta acción (requeriría mockear `createClient` de `@supabase/ssr`, patrón no establecido en el proyecto). La corrección se verifica manualmente en Task 6.

- [ ] **Step 1: Reemplazar `src/lib/supabase/actions/approval.ts`**

```typescript
'use server';
import { APROBACION_CONFIG } from '@/lib/config';
import { createClient } from '@/lib/supabase/server';
import { aprobacionSchema, devolucionSchema } from '@/lib/validators/approval.schema';
import type { Rol } from '@/types/database';
import { revalidatePath } from 'next/cache';

export async function aprobar(
  registroId: string,
  tabla: string,
  rol: Rol,
  cantidadValidada: number,
  observacion: string | undefined,
  rutaRevalidar: string,
) {
  const parsed = aprobacionSchema.parse({ cantidad_validada: cantidadValidada, observacion });
  const config = APROBACION_CONFIG[rol];
  if (!config) throw new Error(`Rol ${rol} no puede aprobar`);

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: current, error: currentError } = await supabase
    .from(tabla)
    .select('estado')
    .eq('id', registroId)
    .single();
  if (currentError) throw new Error(currentError.message);
  if (!current || !config.estadosAccion.includes(current.estado)) {
    throw new Error(`Transicion invalida desde estado ${current?.estado ?? 'NULO'}`);
  }

  const payload: Record<string, unknown> = {
    estado:                        config.estadoResultante,
    [config.campos.campo_cant]:    parsed.cantidad_validada,
    [config.campos.campo_obs]:     parsed.observacion ?? null,
    [config.campos.campo_apr]:     user?.id,
    [config.campos.campo_estado]:  'aprobado',
    [config.campos.campo_fecha]:   new Date().toISOString(),
  };

  const { error } = await supabase.from(tabla).update(payload).eq('id', registroId);
  if (error) throw new Error(error.message);

  revalidatePath(rutaRevalidar);
  return { ok: true };
}

export async function devolver(
  registroId: string,
  tabla: string,
  rol: Rol,
  observacion: string,
  rutaRevalidar: string,
) {
  const parsed = devolucionSchema.parse({ observacion });
  const config = APROBACION_CONFIG[rol];
  if (!config) throw new Error(`Rol ${rol} no puede devolver`);
  if (!config.puedeDevolver) throw new Error(`Rol ${rol} no tiene permiso para devolver`);

  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  const { data: current, error: currentError } = await supabase
    .from(tabla)
    .select('estado')
    .eq('id', registroId)
    .single();
  if (currentError) throw new Error(currentError.message);
  if (!current || !config.estadosAccion.includes(current.estado)) {
    throw new Error(`Transicion invalida desde estado ${current?.estado ?? 'NULO'}`);
  }

  const payload: Record<string, unknown> = {
    estado:                       'DEVUELTO',
    [config.campos.campo_obs]:    parsed.observacion,
    [config.campos.campo_apr]:    user?.id,
    [config.campos.campo_estado]: 'devuelto',
    [config.campos.campo_fecha]:  new Date().toISOString(),
  };

  const { error } = await supabase.from(tabla).update(payload).eq('id', registroId);
  if (error) throw new Error(error.message);

  revalidatePath(rutaRevalidar);
  return { ok: true };
}
```

- [ ] **Step 2: Verificar que TypeScript compila sin errores**

```bash
npx tsc --noEmit
```

Resultado esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add src/lib/supabase/actions/approval.ts
git commit -m "fix(approval): guardar UUID en aprobado_*, TIMESTAMPTZ completo, guardia devolver"
```

---

## Task 3: Actualizar `fetchReporteDiario` — JOIN con perfiles

**Files:**
- Modify: `src/lib/supabase/actions/reporte-diario.ts`

- [ ] **Step 1: Leer el archivo actual**

Abrir `src/lib/supabase/actions/reporte-diario.ts` y localizar la función `fetchReporteDiario`.

- [ ] **Step 2: Actualizar solo la función `fetchReporteDiario`**

Reemplazar la función `fetchReporteDiario` existente con:

```typescript
export async function fetchReporteDiario(contratoId: string) {
  const supabase = await createClient();
  const { data } = await supabase
    .from('registros_reporte_diario')
    .select(`
      *,
      residente:perfiles!aprobado_residente(nombre),
      interventor:perfiles!aprobado_interventor(nombre)
    `)
    .eq('contrato_id', contratoId)
    .order('fecha', { ascending: false });
  return data ?? [];
}
```

Las funciones `fetchSubtablasDiario` y `fetchSubtablasDiarioByContrato` no se modifican.

- [ ] **Step 3: Verificar TypeScript**

```bash
npx tsc --noEmit
```

Resultado esperado: sin errores.

- [ ] **Step 4: Commit**

```bash
git add src/lib/supabase/actions/reporte-diario.ts
git commit -m "feat(reporte-diario): join perfiles para nombres de aprobadores"
```

---

## Task 4: Actualizar `ApprovalHistory.tsx` — mostrar nombres

**Files:**
- Modify: `src/components/approval/ApprovalHistory.tsx`

- [ ] **Step 1: Reemplazar `src/components/approval/ApprovalHistory.tsx`**

```typescript
import { formatDate } from '@/lib/utils';

interface ApprovalHistoryProps {
  registro: any;
}

export function ApprovalHistory({ registro }: ApprovalHistoryProps) {
  const items = [];

  if (registro.aprobado_residente) {
    items.push({
      nivel:  'Obra (Nivel 1)',
      quien:  registro.residente?.nombre ?? registro.aprobado_residente,
      estado: registro.estado_residente,
      fecha:  registro.fecha_residente,
      obs:    registro.obs_residente,
    });
  }

  if (registro.aprobado_interventor) {
    items.push({
      nivel:  'Interventoría (Nivel 2)',
      quien:  registro.interventor?.nombre ?? registro.aprobado_interventor,
      estado: registro.estado_interventor,
      fecha:  registro.fecha_interventor,
      obs:    registro.obs_interventor,
    });
  }

  if (!items.length) return null;

  return (
    <div className="space-y-2">
      <p
        className="text-[10px] font-mono tracking-widest uppercase"
        style={{ color: 'var(--text-muted)' }}
      >
        Trazabilidad
      </p>
      {items.map((item, i) => (
        <div
          key={i}
          className="rounded-md p-3 text-xs space-y-0.5"
          style={{ background: 'var(--muted)', border: '1px solid var(--border)' }}
        >
          <p className="font-semibold" style={{ color: 'var(--text-primary)' }}>
            {item.nivel} · {item.estado} · {formatDate(item.fecha)}
          </p>
          <p style={{ color: 'var(--text-muted)' }}>{item.quien}</p>
          {item.obs && (
            <p style={{ color: 'var(--accent-orange)' }}>↩ {item.obs}</p>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Verificar TypeScript**

```bash
npx tsc --noEmit
```

Resultado esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add src/components/approval/ApprovalHistory.tsx
git commit -m "fix(ApprovalHistory): mostrar nombre del perfil en lugar de UUID"
```

---

## Task 5: Actualizar `ApprovalPanel.tsx` — devolver condicional, cantidad correcta, feedback

**Files:**
- Modify: `src/components/approval/ApprovalPanel.tsx`
- Create: `src/components/approval/ApprovalPanel.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `src/components/approval/ApprovalPanel.test.tsx`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ApprovalPanel } from './ApprovalPanel';

vi.mock('@/lib/supabase/actions/approval', () => ({
  aprobar: vi.fn(),
  devolver: vi.fn(),
}));

const registroBorrador = {
  id: 'r1',
  estado: 'BORRADOR',
  cantidad: 10,
  cant_residente: null,
  cant_interventor: null,
  aprobado_residente: null,
  aprobado_interventor: null,
  estado_residente: null,
  estado_interventor: null,
  fecha_residente: null,
  fecha_interventor: null,
  obs_residente: null,
  obs_interventor: null,
  residente: null,
  interventor: null,
};

const registroRevisado = { ...registroBorrador, id: 'r2', estado: 'REVISADO' };

describe('ApprovalPanel', () => {
  it('obra ve formulario aprobar pero NO formulario devolver', () => {
    render(
      <ApprovalPanel
        registro={registroBorrador}
        rol="obra"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    expect(screen.getByText('Aprobar registro')).toBeInTheDocument();
    expect(screen.queryByText('Devolver registro')).not.toBeInTheDocument();
  });

  it('interventoria ve formulario aprobar Y formulario devolver', () => {
    render(
      <ApprovalPanel
        registro={registroRevisado}
        rol="interventoria"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    expect(screen.getByText('Aprobar registro')).toBeInTheDocument();
    expect(screen.getByText('Devolver registro')).toBeInTheDocument();
  });

  it('admin ve formulario aprobar Y formulario devolver', () => {
    render(
      <ApprovalPanel
        registro={registroRevisado}
        rol="admin"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    expect(screen.getByText('Aprobar registro')).toBeInTheDocument();
    expect(screen.getByText('Devolver registro')).toBeInTheDocument();
  });

  it('operativo no ve ningún formulario de acción', () => {
    render(
      <ApprovalPanel
        registro={registroBorrador}
        rol="operativo"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    expect(screen.queryByText('Aprobar registro')).not.toBeInTheDocument();
    expect(screen.queryByText('Devolver registro')).not.toBeInTheDocument();
  });

  it('obra: cantidad validada por defecto usa cant_residente si existe', () => {
    render(
      <ApprovalPanel
        registro={{ ...registroBorrador, cant_residente: 42 }}
        rol="obra"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    const input = screen.getByLabelText(/cantidad validada/i) as HTMLInputElement;
    expect(Number(input.value)).toBe(42);
  });

  it('obra: cantidad validada por defecto cae en cantidad si cant_residente es null', () => {
    render(
      <ApprovalPanel
        registro={{ ...registroBorrador, cant_residente: null, cantidad: 7 }}
        rol="obra"
        tabla="registros_reporte_diario"
        rutaRevalidar="/anotaciones-diario"
      />
    );
    const input = screen.getByLabelText(/cantidad validada/i) as HTMLInputElement;
    expect(Number(input.value)).toBe(7);
  });
});
```

- [ ] **Step 2: Ejecutar para confirmar que falla**

```bash
npx vitest run src/components/approval/ApprovalPanel.test.tsx
```

Resultado esperado: varios FAIL porque el panel aún muestra devolver para obra y usa `registro.cantidad` siempre.

- [ ] **Step 3: Reemplazar `src/components/approval/ApprovalPanel.tsx`**

```typescript
'use client';
import { useState, useTransition } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { APROBACION_CONFIG } from '@/lib/config';
import { aprobacionSchema, devolucionSchema } from '@/lib/validators/approval.schema';
import type { AprobacionInput, DevolucionInput } from '@/lib/validators/approval.schema';
import { aprobar, devolver } from '@/lib/supabase/actions/approval';
import { ApprovalHistory } from './ApprovalHistory';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import type { Rol } from '@/types/database';

interface ApprovalPanelProps {
  registro:      any;
  rol:           Rol;
  tabla:         string;
  rutaRevalidar: string;
}

export function ApprovalPanel({ registro, rol, tabla, rutaRevalidar }: ApprovalPanelProps) {
  const [isPending, startTransition] = useTransition();
  const [feedbackError, setFeedbackError]     = useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  const config = APROBACION_CONFIG[rol];

  const puedeAccionar =
    config &&
    (config.estadosAccion as string[]).includes(registro.estado);

  const cantidadDefault =
    (config ? (registro[config.campos.campo_cant] ?? null) : null) ??
    registro.cantidad ??
    0;

  const aprForm = useForm<AprobacionInput>({
    resolver: zodResolver(aprobacionSchema),
    defaultValues: { cantidad_validada: Number(cantidadDefault) },
  });
  const devForm = useForm<DevolucionInput>({
    resolver: zodResolver(devolucionSchema),
  });

  function handleAprobar(data: AprobacionInput) {
    setFeedbackError(null);
    setFeedbackSuccess(null);
    startTransition(async () => {
      try {
        await aprobar(registro.id, tabla, rol, data.cantidad_validada, data.observacion, rutaRevalidar);
        setFeedbackSuccess('Registro aprobado correctamente.');
      } catch (e) {
        setFeedbackError(e instanceof Error ? e.message : 'No fue posible aprobar el registro.');
      }
    });
  }

  function handleDevolver(data: DevolucionInput) {
    setFeedbackError(null);
    setFeedbackSuccess(null);
    startTransition(async () => {
      try {
        await devolver(registro.id, tabla, rol, data.observacion, rutaRevalidar);
        setFeedbackSuccess('Registro devuelto.');
      } catch (e) {
        setFeedbackError(e instanceof Error ? e.message : 'No fue posible devolver el registro.');
      }
    });
  }

  return (
    <div className="space-y-4">
      <ApprovalHistory registro={registro} />

      {puedeAccionar && (
        <div className="space-y-4">
          <p
            className="text-[10px] font-mono tracking-widest uppercase"
            style={{ color: 'var(--text-muted)' }}
          >
            Panel de aprobación
          </p>

          {/* Formulario Aprobar */}
          <form
            onSubmit={aprForm.handleSubmit(handleAprobar)}
            className="rounded-md p-3 space-y-3"
            style={{ background: '#F0FDF4', border: '1px solid #BBF7D0' }}
          >
            <p className="text-xs font-semibold" style={{ color: '#166534' }}>
              Aprobar registro
            </p>
            <div>
              <Label htmlFor={`cant-${registro.id}`}>Cantidad validada</Label>
              <Input
                id={`cant-${registro.id}`}
                type="number"
                step="any"
                {...aprForm.register('cantidad_validada')}
              />
              {aprForm.formState.errors.cantidad_validada && (
                <p className="text-xs text-red-600 mt-0.5">
                  {aprForm.formState.errors.cantidad_validada.message}
                </p>
              )}
            </div>
            <div>
              <Label>Observación (opcional)</Label>
              <Textarea rows={2} {...aprForm.register('observacion')} />
            </div>
            <Button
              type="submit"
              size="sm"
              disabled={isPending}
              style={{ background: 'var(--accent-green)', color: 'white' }}
            >
              {isPending ? 'Guardando…' : 'Aprobar'}
            </Button>
          </form>

          {/* Formulario Devolver — solo para roles con puedeDevolver */}
          {config?.puedeDevolver && (
            <form
              onSubmit={devForm.handleSubmit(handleDevolver)}
              className="rounded-md p-3 space-y-3"
              style={{ background: '#FEF2F2', border: '1px solid #FECACA' }}
            >
              <p className="text-xs font-semibold" style={{ color: '#991B1B' }}>
                Devolver registro
              </p>
              <div>
                <Label>Observación de devolución *</Label>
                <Textarea rows={2} {...devForm.register('observacion')} />
                {devForm.formState.errors.observacion && (
                  <p className="text-xs text-red-600 mt-0.5">
                    {devForm.formState.errors.observacion.message}
                  </p>
                )}
              </div>
              <Button
                type="submit"
                size="sm"
                variant="destructive"
                disabled={isPending}
              >
                {isPending ? 'Guardando…' : 'Devolver'}
              </Button>
            </form>
          )}

          {/* Feedback inline */}
          {feedbackError && (
            <p
              className="text-xs rounded-md px-3 py-2"
              style={{ background: '#FEF2F2', color: '#991B1B', border: '1px solid #FECACA' }}
            >
              {feedbackError}
            </p>
          )}
          {feedbackSuccess && (
            <p
              className="text-xs rounded-md px-3 py-2"
              style={{ background: '#F0FDF4', color: '#166534', border: '1px solid #BBF7D0' }}
            >
              {feedbackSuccess}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Ejecutar tests para confirmar que pasan**

```bash
npx vitest run src/components/approval/ApprovalPanel.test.tsx
```

Resultado esperado: PASS (6 tests).

- [ ] **Step 5: Ejecutar todos los tests del proyecto**

```bash
npx vitest run
```

Resultado esperado: todos los tests existentes siguen en PASS.

- [ ] **Step 6: Commit**

```bash
git add src/components/approval/ApprovalPanel.tsx src/components/approval/ApprovalPanel.test.tsx
git commit -m "fix(ApprovalPanel): ocultar devolver para obra, cantidad role-especifica, feedback inline"
```

---

## Task 6: Verificación final

- [ ] **Step 1: Build de producción sin errores**

```bash
npm run build
```

Resultado esperado: build exitoso, sin errores TypeScript ni warnings críticos.

- [ ] **Step 2: Verificar en dev server — flujo obra (BORRADOR)**

```bash
npm run dev
```

1. Iniciar sesión como usuario con rol `obra`
2. Ir a `/anotaciones-diario`
3. Expandir un registro en estado `BORRADOR`
4. Verificar: aparece "Aprobar registro", NO aparece "Devolver registro"
5. Verificar: el campo "Cantidad validada" muestra `cant_residente` si ya existe, o `cantidad` si es null
6. Aprobar el registro → verificar mensaje verde de éxito, registro pasa a REVISADO

- [ ] **Step 3: Verificar flujo interventoria (REVISADO)**

1. Iniciar sesión como usuario con rol `interventoria`
2. Expandir un registro en estado `REVISADO`
3. Verificar: aparece tanto "Aprobar registro" como "Devolver registro"
4. Verificar: el campo "Cantidad validada" muestra `cant_interventor` si ya existe
5. Devolver con observación → verificar mensaje naranja de éxito, registro pasa a DEVUELTO

- [ ] **Step 4: Verificar flujo obra (DEVUELTO)**

1. Iniciar sesión como usuario con rol `obra`
2. Expandir un registro en estado `DEVUELTO`
3. Verificar: aparece "Aprobar registro" (obra puede re-revisar), NO aparece "Devolver registro"
4. Aprobar → registro pasa a REVISADO nuevamente

- [ ] **Step 5: Verificar trazabilidad con nombres**

1. Abrir un registro que ya fue aprobado por alguien
2. Verificar que en "Trazabilidad" aparece el nombre del usuario (ej: "Juan Pérez") y no un UUID

- [ ] **Step 6: Verificar `supervision` y `operativo`**

1. Iniciar sesión como `supervision`
2. Expandir cualquier registro — verificar que NO aparece ningún formulario de acción, solo trazabilidad si existe
