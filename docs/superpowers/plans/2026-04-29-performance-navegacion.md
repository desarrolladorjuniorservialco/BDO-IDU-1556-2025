# Optimización de Rendimiento en Navegación — BDO React App

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reducir la latencia de cambio de página de ~800-1100ms a ~350-600ms eliminando round-trips innecesarios a Supabase y añadiendo feedback visual inmediato con skeletons.

**Architecture:** Tres frentes de ataque: (1) eliminar la query de `perfiles` del middleware usando una cookie de rol cacheada, (2) hacer persistente el caché del perfil entre requests con `unstable_cache`, (3) añadir archivos `loading.tsx` en cada ruta para mostrar skeletons de forma instantánea mientras el servidor procesa.

**Tech Stack:** Next.js 14 App Router, Supabase SSR, Zustand, TypeScript. No se requieren nuevas dependencias.

---

## Análisis de la causa raíz

Cada navegación entre páginas dispara esta cadena de llamadas de red:

| Capa | Llamadas actuales | Tiempo estimado |
|------|------------------|----------------|
| Middleware | `getUser()` + `getPerfil(rol)` | ~300ms |
| Page.tsx | `getUser()` + `getPerfil()` + queries específicas | ~400-800ms |
| **Total por navegación** | **4-8 llamadas Supabase** | **~700-1100ms** |

Después de este plan:

| Capa | Llamadas optimizadas | Tiempo estimado |
|------|---------------------|----------------|
| Middleware | `getUser()` + lectura de cookie (0ms) | ~150ms |
| Page.tsx | `getUser()` + `getPerfil()` (caché, ~1ms) + queries | ~350-600ms |
| **Percepción del usuario** | **Skeleton aparece en ~0ms** | **Sensación inmediata** |

---

## Mapa de archivos

| Archivo | Acción | Responsabilidad |
|---------|--------|----------------|
| `src/middleware.ts` | Modificar | Eliminar query DB de `perfiles`; leer cookie `bdo-rol`; escribir cookie al primer login |
| `src/lib/supabase/cached-queries.ts` | Modificar | Reemplazar `cache()` de React por `unstable_cache` en `getCachedPerfil` |
| `src/components/layout/PageSkeleton.tsx` | Crear | Skeleton compartido para todas las páginas del dashboard |
| `src/app/(dashboard)/estado-actual/loading.tsx` | Crear | Suspense boundary para estado-actual |
| `src/app/(dashboard)/anotaciones/loading.tsx` | Crear | Suspense boundary para anotaciones |
| `src/app/(dashboard)/anotaciones-diario/loading.tsx` | Crear | Suspense boundary para anotaciones-diario |
| `src/app/(dashboard)/reporte-cantidades/loading.tsx` | Crear | Suspense boundary para reporte-cantidades |
| `src/app/(dashboard)/componente-ambiental/loading.tsx` | Crear | Suspense boundary para componente-ambiental |
| `src/app/(dashboard)/componente-social/loading.tsx` | Crear | Suspense boundary para componente-social |
| `src/app/(dashboard)/componente-pmt/loading.tsx` | Crear | Suspense boundary para componente-pmt |
| `src/app/(dashboard)/seguimiento-pmts/loading.tsx` | Crear | Suspense boundary para seguimiento-pmts |
| `src/app/(dashboard)/mapa-ejecucion/loading.tsx` | Crear | Suspense boundary para mapa-ejecucion |
| `src/app/(dashboard)/presupuesto/loading.tsx` | Crear | Suspense boundary para presupuesto |
| `src/app/(dashboard)/correspondencia/loading.tsx` | Crear | Suspense boundary para correspondencia |
| `src/app/(dashboard)/generar-informe/loading.tsx` | Crear | Suspense boundary para generar-informe |

---

## Task 1: Optimizar el middleware — eliminar query de perfiles

**Problema:** El middleware llama `supabase.from('perfiles').select('rol')` en CADA request, incluyendo
cada navegación suave (click en un Link de Next.js). Esta es 1 round-trip a la base de datos (~150ms)
que se puede evitar guardando el rol en una cookie HttpOnly la primera vez que se consulta.

**Estrategia:**
- Si la request tiene la cookie `bdo-rol` → usar ese valor, sin consultar la DB
- Si no tiene la cookie → consultar DB (comportamiento actual), y luego escribir el rol en la cookie de respuesta
- La cookie tiene `maxAge: 3600` (1 hora), consistente con la duración habitual de sesión

**Files:**
- Modify: `src/middleware.ts`

- [ ] **Step 1: Leer el estado actual del middleware**

  Confirmar el contenido actual antes de editar:
  ```
  File: src/middleware.ts (ya leído — ver análisis arriba)
  Líneas clave: 53-57 (query a perfiles), 8-28 (setup supabase)
  ```

- [ ] **Step 2: Modificar el middleware para usar cookie de rol**

  Reemplazar el bloque completo de verificación de rol (líneas 52-65) con la siguiente lógica:

  ```typescript
  // Verificar control de acceso por rol
  const segment = pathname.split('/')[1];
  const rolesPermitidos = NAV_ACCESS[segment];

  if (rolesPermitidos) {
    const rolEnCookie = request.cookies.get('bdo-rol')?.value as Rol | undefined;

    let rol: Rol | undefined = rolEnCookie;

    if (!rol) {
      // Primera vez (sin cookie): consultar DB y guardar en cookie
      const { data: perfil } = await supabase
        .from('perfiles')
        .select('rol')
        .eq('id', user.id)
        .single();
      rol = perfil?.rol as Rol | undefined;
      if (rol) {
        supabaseResponse.cookies.set('bdo-rol', rol, {
          httpOnly: true,
          sameSite: 'lax',
          maxAge: 3600,
          path: '/',
        });
      }
    }

    if (!rol || !rolesPermitidos.includes(rol)) {
      const url = request.nextUrl.clone();
      url.pathname = '/estado-actual';
      return NextResponse.redirect(url);
    }
  }
  ```

  El archivo final completo de `src/middleware.ts` debe quedar:

  ```typescript
  import { createServerClient } from '@supabase/ssr';
  import { NextResponse, type NextRequest } from 'next/server';
  import { NAV_ACCESS } from '@/lib/config';
  import type { Rol } from '@/types/database';

  export async function middleware(request: NextRequest) {
    let supabaseResponse = NextResponse.next({ request });

    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll() {
            return request.cookies.getAll();
          },
          setAll(cookiesToSet: { name: string; value: string; options?: object }[]) {
            cookiesToSet.forEach(({ name, value }) =>
              request.cookies.set(name, value)
            );
            supabaseResponse = NextResponse.next({ request });
            cookiesToSet.forEach(({ name, value, options }) =>
              supabaseResponse.cookies.set(name, value, options as any)
            );
          },
        },
      }
    );

    const {
      data: { user },
    } = await supabase.auth.getUser();

    const { pathname } = request.nextUrl;

    if (pathname.startsWith('/login') || pathname.startsWith('/_next') || pathname.startsWith('/api')) {
      return supabaseResponse;
    }

    if (!user) {
      const url = request.nextUrl.clone();
      url.pathname = '/login';
      return NextResponse.redirect(url);
    }

    const segment = pathname.split('/')[1];
    const rolesPermitidos = NAV_ACCESS[segment];

    if (rolesPermitidos) {
      const rolEnCookie = request.cookies.get('bdo-rol')?.value as Rol | undefined;

      let rol: Rol | undefined = rolEnCookie;

      if (!rol) {
        const { data: perfil } = await supabase
          .from('perfiles')
          .select('rol')
          .eq('id', user.id)
          .single();
        rol = perfil?.rol as Rol | undefined;
        if (rol) {
          supabaseResponse.cookies.set('bdo-rol', rol, {
            httpOnly: true,
            sameSite: 'lax',
            maxAge: 3600,
            path: '/',
          });
        }
      }

      if (!rol || !rolesPermitidos.includes(rol)) {
        const url = request.nextUrl.clone();
        url.pathname = '/estado-actual';
        return NextResponse.redirect(url);
      }
    }

    return supabaseResponse;
  }

  export const config = {
    matcher: [
      '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    ],
  };
  ```

- [ ] **Step 3: Verificar build sin errores TypeScript**

  ```bash
  cd bdo_idu_react/BDO_React && npx tsc --noEmit
  ```

  Expected: sin errores de tipos.

- [ ] **Step 4: Commit**

  ```bash
  git add src/middleware.ts
  git commit -m "perf: cache rol en cookie para eliminar query DB del middleware en navegaciones"
  ```

---

## Task 2: Cache persistente del perfil con unstable_cache

**Problema:** `getCachedPerfil` usa `cache()` de React, que solo deduplica dentro del mismo render
request. En cada nueva navegación a una página (que sí re-ejecuta el `page.tsx` en el servidor),
se hace una nueva query a `supabase.from('perfiles')`.

**Solución:** Reemplazar `cache()` por `unstable_cache` de Next.js, que persiste el resultado
entre requests (hasta 60 segundos). La clave de caché incluye el `userId` para evitar mezclar
datos entre usuarios.

**Nota:** `getCachedUser()` y `getCachedSession()` se mantienen con `cache()` de React porque
devuelven datos de autenticación que deben estar frescos en cada request.

**Files:**
- Modify: `src/lib/supabase/cached-queries.ts`

- [ ] **Step 1: Actualizar cached-queries.ts con unstable_cache para el perfil**

  El archivo completo debe quedar así:

  ```typescript
  import { unstable_cache } from 'next/cache';
  import { cache } from 'react';
  import { createClient } from './server';

  export const getCachedUser = cache(async () => {
    const supabase = await createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    return user;
  });

  export const getCachedSession = cache(async () => {
    const supabase = await createClient();
    const {
      data: { session },
    } = await supabase.auth.getSession();
    return session;
  });

  export const getCachedPerfil = cache(async (userId: string) => {
    return unstable_cache(
      async () => {
        const supabase = await createClient();
        const { data } = await supabase
          .from('perfiles')
          .select('id, nombre, rol, empresa, contrato_id')
          .eq('id', userId)
          .single();
        return data;
      },
      [`perfil-${userId}`],
      { revalidate: 60 }
    )();
  });
  ```

  **Por qué este patrón (cache + unstable_cache anidados):**
  - El `cache()` de React externo deduplica llamadas concurrentes *dentro del mismo render*
    (ej: si `layout.tsx` y `page.tsx` llaman `getCachedPerfil` en el mismo request, solo
    ejecuta la función interna una vez)
  - El `unstable_cache` interno persiste el resultado entre requests distintos (60s)
  - Resultado: primer request del día → 1 query a DB; los siguientes 60 segundos → 0 queries

- [ ] **Step 2: Verificar tipos**

  ```bash
  cd bdo_idu_react/BDO_React && npx tsc --noEmit
  ```

  Expected: sin errores.

- [ ] **Step 3: Commit**

  ```bash
  git add src/lib/supabase/cached-queries.ts
  git commit -m "perf: usar unstable_cache para perfil (TTL 60s entre requests)"
  ```

---

## Task 3: Skeleton compartido y archivos loading.tsx por página

**Problema:** Cuando el usuario hace click en un enlace del sidebar, la UI parece "congelada"
durante ~700ms hasta que el servidor responde con el HTML de la nueva página. No hay ningún
indicador de que algo está pasando.

**Solución:** Next.js App Router soporta `loading.tsx` en cada directorio de ruta. Si existe,
Next.js muestra su contenido INMEDIATAMENTE al navegar (incluso antes de que el servidor
responda), usando un Suspense boundary automático. Esto hace que la navegación se sienta
instantánea.

**Files:**
- Create: `src/components/layout/PageSkeleton.tsx`
- Create: `src/app/(dashboard)/estado-actual/loading.tsx`
- Create: `src/app/(dashboard)/anotaciones/loading.tsx`
- Create: `src/app/(dashboard)/anotaciones-diario/loading.tsx`
- Create: `src/app/(dashboard)/reporte-cantidades/loading.tsx`
- Create: `src/app/(dashboard)/componente-ambiental/loading.tsx`
- Create: `src/app/(dashboard)/componente-social/loading.tsx`
- Create: `src/app/(dashboard)/componente-pmt/loading.tsx`
- Create: `src/app/(dashboard)/seguimiento-pmts/loading.tsx`
- Create: `src/app/(dashboard)/mapa-ejecucion/loading.tsx`
- Create: `src/app/(dashboard)/presupuesto/loading.tsx`
- Create: `src/app/(dashboard)/correspondencia/loading.tsx`
- Create: `src/app/(dashboard)/generar-informe/loading.tsx`

- [ ] **Step 1: Crear el componente PageSkeleton compartido**

  Crear `src/components/layout/PageSkeleton.tsx`:

  ```tsx
  export function PageSkeleton() {
    return (
      <div className="space-y-6 animate-pulse">
        {/* Badge de título */}
        <div className="h-7 w-48 rounded-lg bg-[var(--border)]" />

        {/* Card principal */}
        <div
          className="rounded-xl p-5 space-y-4"
          style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div className="h-4 w-64 rounded bg-[var(--border)]" />
          <div className="h-4 w-full rounded bg-[var(--border)]" />
          <div className="h-4 w-3/4 rounded bg-[var(--border)]" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-16 rounded-lg bg-[var(--border)]" />
            ))}
          </div>
        </div>

        {/* Card secundaria */}
        <div
          className="rounded-xl p-5 space-y-3"
          style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          <div className="h-4 w-40 rounded bg-[var(--border)]" />
          <div className="h-4 w-full rounded bg-[var(--border)]" />
          <div className="h-4 w-5/6 rounded bg-[var(--border)]" />
          <div className="h-4 w-2/3 rounded bg-[var(--border)]" />
        </div>
      </div>
    );
  }
  ```

- [ ] **Step 2: Crear loading.tsx para cada ruta del dashboard**

  Todos los archivos son idénticos — solo importan y re-exportan `PageSkeleton`.

  Crear `src/app/(dashboard)/estado-actual/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/anotaciones/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/anotaciones-diario/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/reporte-cantidades/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/componente-ambiental/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/componente-social/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/componente-pmt/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/seguimiento-pmts/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/mapa-ejecucion/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/presupuesto/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/correspondencia/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

  Crear `src/app/(dashboard)/generar-informe/loading.tsx`:
  ```tsx
  import { PageSkeleton } from '@/components/layout/PageSkeleton';
  export default function Loading() { return <PageSkeleton />; }
  ```

- [ ] **Step 3: Verificar build**

  ```bash
  cd bdo_idu_react/BDO_React && npx tsc --noEmit
  ```

  Expected: sin errores.

- [ ] **Step 4: Probar visualmente en dev**

  ```bash
  cd bdo_idu_react/BDO_React && npm run dev
  ```

  Navegar entre páginas en el browser. Verificar que aparece el skeleton antes del contenido.
  Si el skeleton aparece y desaparece tan rápido que no se ve, eso es correcto — significa
  que el servidor responde rápido. Para verlo en dev, abrir DevTools > Network > throttle a
  "Slow 3G" y navegar entre páginas.

- [ ] **Step 5: Commit**

  ```bash
  git add src/components/layout/PageSkeleton.tsx \
    "src/app/(dashboard)/estado-actual/loading.tsx" \
    "src/app/(dashboard)/anotaciones/loading.tsx" \
    "src/app/(dashboard)/anotaciones-diario/loading.tsx" \
    "src/app/(dashboard)/reporte-cantidades/loading.tsx" \
    "src/app/(dashboard)/componente-ambiental/loading.tsx" \
    "src/app/(dashboard)/componente-social/loading.tsx" \
    "src/app/(dashboard)/componente-pmt/loading.tsx" \
    "src/app/(dashboard)/seguimiento-pmts/loading.tsx" \
    "src/app/(dashboard)/mapa-ejecucion/loading.tsx" \
    "src/app/(dashboard)/presupuesto/loading.tsx" \
    "src/app/(dashboard)/correspondencia/loading.tsx" \
    "src/app/(dashboard)/generar-informe/loading.tsx"
  git commit -m "perf: añadir loading.tsx a todas las rutas del dashboard para feedback visual inmediato"
  ```

---

## Task 4: Corregir estrategia de revalidación en páginas de datos

**Problema:** Varias páginas tienen `export const revalidate = 0` o `force-dynamic`, lo que
significa que el servidor las re-renderiza completamente en CADA visita sin ningún caché. Para
páginas donde los datos cambian solo cuando el usuario hace una acción (crear/editar/aprobar),
la estrategia correcta es cachear los datos y revalidar solo cuando cambian.

**Páginas afectadas:**
- `anotaciones/page.tsx` → `revalidate = 0`
- `anotaciones-diario/page.tsx` → `revalidate = 0`
- `reporte-cantidades/page.tsx` → `revalidate = 0`
- `componente-ambiental/page.tsx` → `revalidate = 0`
- `componente-social/page.tsx` → `revalidate = 0` (asumido)
- `componente-pmt/page.tsx` → `revalidate = 0` (asumido)
- `correspondencia/page.tsx` → `revalidate = 0`
- `mapa-ejecucion/page.tsx` → `force-dynamic`
- `generar-informe/page.tsx` → `force-dynamic`

**Estrategia:** Para `generar-informe` que tiene 9 queries, mover la carga de datos al cliente
usando el `accessToken` del `authStore`. Para las demás páginas, cambiar a `revalidate = 30`.

**Nota:** Cambiar `revalidate = 0` a `revalidate = 30` tiene un efecto limitado en páginas que
usan `cookies()` via `createClient`, porque Next.js las trata como dinámicas. La optimización real
aquí es en `generar-informe` por ser la página más lenta.

**Files:**
- Modify: `src/app/(dashboard)/generar-informe/page.tsx`
- Modify: `src/app/(dashboard)/generar-informe/GenerarInformeClient.tsx`

- [ ] **Step 1: Leer GenerarInformeClient.tsx para entender su interfaz actual**

  ```bash
  cat src/app/(dashboard)/generar-informe/GenerarInformeClient.tsx
  ```

  Buscar: ¿el componente recibe `data` como prop? ¿Hace algún fetch propio?

- [ ] **Step 2: Refactorizar generar-informe para carga lazy en el cliente**

  **Modificar `src/app/(dashboard)/generar-informe/page.tsx`:**

  Cambiar de cargar los 9 datasets en el servidor a pasar solo el `contratoId` al cliente:

  ```tsx
  import { getCachedPerfil, getCachedUser } from '@/lib/supabase/cached-queries';
  import GenerarInformeClient from './GenerarInformeClient';

  export default async function Page() {
    const user = await getCachedUser();
    const perfil = await getCachedPerfil(user!.id);

    return <GenerarInformeClient contratoId={perfil!.contrato_id} />;
  }
  ```

  **Modificar `src/app/(dashboard)/generar-informe/GenerarInformeClient.tsx`:**

  El cliente recibe `contratoId` y carga los datos desde el browser usando `createClient()` del
  cliente de Supabase (que ya tiene la sesión activa en cookies). Adaptar la interfaz de props:

  ```tsx
  'use client';
  // Cambiar prop de { data: InformeData } a { contratoId: string }
  // El componente carga los datos localmente con useEffect + el createClient del browser
  ```

  **Nota importante:** Antes de implementar este step, leer el contenido completo de
  `GenerarInformeClient.tsx` para entender qué hace con `data` (filtros de fecha, etc.).
  Si el componente tiene lógica de filtrado compleja que depende de los datos completos,
  adaptar el fetch del cliente para respetar esa lógica.

- [ ] **Step 3: Verificar que la página de generar-informe carga correctamente**

  ```bash
  cd bdo_idu_react/BDO_React && npm run dev
  ```

  Navegar a `/generar-informe` y verificar:
  - La página carga (skeleton visible mientras se obtienen datos)
  - Los datos aparecen correctamente
  - Los filtros de fecha (si existen) funcionan

- [ ] **Step 4: Commit**

  ```bash
  git add "src/app/(dashboard)/generar-informe/page.tsx" \
    "src/app/(dashboard)/generar-informe/GenerarInformeClient.tsx"
  git commit -m "perf: mover fetch de datos en generar-informe al cliente para evitar 9 queries en server"
  ```

---

## Resultado esperado

Después de completar los 4 tasks:

| Métrica | Antes | Después |
|---------|-------|---------|
| Llamadas Supabase por navegación (middleware) | 2 | 1 (solo `getUser`) |
| Llamadas Supabase por navegación (page, perfil) | 1 DB call | ~0 (unstable_cache hit) |
| Tiempo hasta primer feedback visual | ~700ms | ~0ms (skeleton inmediato) |
| Tiempo hasta contenido completo | ~800-1100ms | ~400-700ms |
| `generar-informe` server render | 9 queries paralelas | 0 queries en server |

## Notas de seguridad

- **Cookie `bdo-rol`**: es HttpOnly (no accesible por JS), SameSite=Lax, escrita por el servidor.
  Si el rol de un usuario cambia en la DB, el efecto se verá en la próxima hora (cuando expira
  la cookie) o cuando el usuario cierre sesión y vuelva a entrar.

- **`unstable_cache` para perfil**: cachea por `userId`. No hay riesgo de mezclar datos entre
  usuarios. Si el `contrato_id` de un usuario cambia, el efecto se verá en ~60 segundos.

- **Supabase RLS**: sigue siendo la capa de seguridad real para todos los datos. Estas
  optimizaciones solo afectan el routing y el auth overhead, no los permisos de datos.
