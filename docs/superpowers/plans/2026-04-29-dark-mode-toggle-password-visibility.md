# Dark Mode Toggle + Password Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar toggle de modo oscuro/claro en el Header del dashboard y botón de visibilidad de contraseña en el formulario de login.

**Architecture:** Se crea un Zustand store (`themeStore`) sin persistencia que inicializa el tema desde la preferencia del SO. Un componente cliente `ThemeApplier` aplica `data-theme="dark"` al elemento `<html>` según el store. El CSS ya tiene variables para modo oscuro en `@media`; se agrega el selector `html[data-theme="dark"]` para que el toggle manual también las active. El login solo necesita estado local `useState`.

**Tech Stack:** Next.js App Router, React, TypeScript, Zustand, Tailwind CSS, Lucide React, Vitest

---

## Archivos a crear/modificar

| Acción | Archivo | Responsabilidad |
|--------|---------|----------------|
| Crear  | `src/stores/themeStore.ts` | Estado del tema (light/dark) y toggle |
| Crear  | `src/components/layout/ThemeApplier.tsx` | Aplica `data-theme` al DOM |
| Modificar | `src/app/globals.css` | Agregar selector `html[data-theme="dark"]` |
| Modificar | `src/components/layout/Header.tsx` | Botón Sun/Moon toggle |
| Modificar | `src/app/(dashboard)/layout.tsx` | Montar ThemeApplier |
| Modificar | `src/app/(auth)/login/page.tsx` | Botón Eye/EyeOff en campo contraseña |

---

## Task 1: themeStore

**Files:**
- Create: `src/stores/themeStore.ts`
- Create: `src/stores/themeStore.test.ts`

- [ ] **Step 1: Escribir el test**

Crear `src/stores/themeStore.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useThemeStore } from './themeStore';

describe('themeStore', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'light' });
  });

  it('toggle cambia de light a dark', () => {
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().theme).toBe('dark');
  });

  it('toggle cambia de dark a light', () => {
    useThemeStore.setState({ theme: 'dark' });
    useThemeStore.getState().toggle();
    expect(useThemeStore.getState().theme).toBe('light');
  });
});
```

- [ ] **Step 2: Ejecutar el test para verificar que falla**

```bash
cd bdo_idu_react/BDO_React && npx vitest run src/stores/themeStore.test.ts
```

Esperado: FAIL — `themeStore` no existe aún.

- [ ] **Step 3: Crear el store**

Crear `src/stores/themeStore.ts`:

```typescript
import { create } from 'zustand';

type Theme = 'light' | 'dark';

interface ThemeStore {
  theme: Theme;
  toggle: () => void;
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export const useThemeStore = create<ThemeStore>((set) => ({
  theme: getInitialTheme(),
  toggle: () => set((s) => ({ theme: s.theme === 'light' ? 'dark' : 'light' })),
}));
```

- [ ] **Step 4: Ejecutar el test para verificar que pasa**

```bash
cd bdo_idu_react/BDO_React && npx vitest run src/stores/themeStore.test.ts
```

Esperado: PASS — 2 tests passed.

- [ ] **Step 5: Commit**

```bash
git add bdo_idu_react/BDO_React/src/stores/themeStore.ts bdo_idu_react/BDO_React/src/stores/themeStore.test.ts
git commit -m "feat: add themeStore for dark/light mode toggle"
```

---

## Task 2: ThemeApplier component

**Files:**
- Create: `src/components/layout/ThemeApplier.tsx`

- [ ] **Step 1: Crear el componente**

Crear `src/components/layout/ThemeApplier.tsx`:

```typescript
'use client';
import { useEffect } from 'react';
import { useThemeStore } from '@/stores/themeStore';

export function ThemeApplier() {
  const theme = useThemeStore((s) => s.theme);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
  }, [theme]);

  return null;
}
```

- [ ] **Step 2: Commit**

```bash
git add bdo_idu_react/BDO_React/src/components/layout/ThemeApplier.tsx
git commit -m "feat: add ThemeApplier client component"
```

---

## Task 3: Agregar selector CSS para dark mode manual

**Files:**
- Modify: `src/app/globals.css`

- [ ] **Step 1: Agregar bloque `html[data-theme="dark"]` en globals.css**

Agregar este bloque al final del archivo `src/app/globals.css`, justo después del bloque `@media (prefers-color-scheme: dark)` (después de la línea 126):

```css
/* ── Dark mode manual (toggle de usuario) ──────────────────── */
html[data-theme="dark"] {
  --corp-primary: #8ab52e;
  --corp-dark: #6b8e23;
  --corp-gold: #e5b84d;
  --corp-gold-lt: #2d2200;
  --corp-green-lt: #0d2010;

  --idu-blue-lt: #0d2744;
  --idu-blue-lt-fg: #a8cfef;
  --idu-red-lt: #3d0507;
  --idu-red-lt-fg: #ff8c8c;
  --idu-yellow-lt: #2d2400;
  --idu-yellow-lt-fg: #ffd200;
  --idu-green-lt: #1a2409;
  --idu-green-lt-fg: #a8c46a;

  --bg-app: #0d1520;
  --bg-card: #12233d;
  --bg-sidebar: #0a1628;

  --sidebar-header-bg: #060e1a;
  --sidebar-text: #94a3b8;
  --sidebar-text-muted: #64748b;
  --sidebar-active-bg: rgba(139, 181, 46, 0.15);
  --sidebar-footer-bg: #060e1a;

  --text-primary: #e8f0fb;
  --text-muted: #699bd8;
  --border: #1a2e4a;

  --card: #12233d;
  --card-foreground: #e8f0fb;
  --background: #0d1520;
  --foreground: #e8f0fb;
  --muted: #12233d;
  --muted-foreground: #7a96b8;
  --primary: #8ab52e;
  --primary-foreground: #0d1520;
  --secondary: #12233d;
  --secondary-foreground: #e8f0fb;
  --input: #1a2e4a;
  --ring: #8ab52e;
}
```

- [ ] **Step 2: Commit**

```bash
git add bdo_idu_react/BDO_React/src/app/globals.css
git commit -m "feat: add html[data-theme=dark] CSS selector for manual toggle"
```

---

## Task 4: Botón toggle en Header

**Files:**
- Modify: `src/components/layout/Header.tsx`

- [ ] **Step 1: Modificar Header.tsx**

Reemplazar el contenido completo de `src/components/layout/Header.tsx` con:

```typescript
'use client';
import { Button } from '@/components/ui/button';
import { ROL_LABELS } from '@/lib/config';
import { createClient } from '@/lib/supabase/client';
import { useAuthStore } from '@/stores/authStore';
import { useNotifStore } from '@/stores/notifStore';
import { useThemeStore } from '@/stores/themeStore';
import type { Perfil } from '@/types/database';
import { Bell, LogOut, Moon, Sun } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface HeaderProps {
  perfil: Perfil;
}

export function Header({ perfil }: HeaderProps) {
  const router = useRouter();
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const clearNotifs = useNotifStore((s) => s.clearNotifs);
  const notifs = useNotifStore((s) => s.notifs);
  const unread = notifs.filter((n) => !n.leida).length;
  const theme = useThemeStore((s) => s.theme);
  const toggleTheme = useThemeStore((s) => s.toggle);

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    clearAuth();
    clearNotifs();
    router.push('/login');
    router.refresh();
  }

  return (
    <header
      className="sticky top-0 z-40 flex items-center justify-between h-14 px-6"
      style={{
        background: 'linear-gradient(to right, var(--corp-primary), var(--corp-dark))',
        borderBottom: '3px solid var(--corp-gold)',
      }}
    >
      <div className="flex items-center gap-2.5">
        <span className="text-sm font-semibold" style={{ color: '#FFFFFF' }}>
          {perfil.nombre}
        </span>
        <span
          className="text-[11px] px-2 py-0.5 rounded-full tracking-wide uppercase font-medium"
          style={{
            background: 'rgba(255,255,255,0.15)',
            color: 'rgba(255,255,255,0.90)',
            border: '1px solid rgba(255,255,255,0.20)',
          }}
        >
          {ROL_LABELS[perfil.rol]}
        </span>
      </div>

      <div className="flex items-center gap-1">
        {unread > 0 && (
          <div className="relative mr-1">
            <Bell className="h-5 w-5" style={{ color: 'rgba(255,255,255,0.85)' }} />
            <span
              className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full text-white text-[9px] font-bold"
              style={{ background: 'var(--corp-gold)' }}
            >
              {unread}
            </span>
          </div>
        )}
        <button
          type="button"
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
          className="flex items-center justify-center h-9 w-9 rounded-md transition-colors duration-150 hover:bg-white/10"
          style={{ color: 'rgba(255,255,255,0.80)' }}
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>
        <button
          type="button"
          onClick={handleLogout}
          title="Cerrar sesión"
          className="flex items-center justify-center h-9 w-9 rounded-md transition-colors duration-150 hover:bg-white/10"
          style={{ color: 'rgba(255,255,255,0.80)' }}
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add bdo_idu_react/BDO_React/src/components/layout/Header.tsx
git commit -m "feat: add dark/light mode toggle button to Header"
```

---

## Task 5: Montar ThemeApplier en DashboardLayout

**Files:**
- Modify: `src/app/(dashboard)/layout.tsx`

- [ ] **Step 1: Modificar layout.tsx**

Reemplazar el contenido completo de `src/app/(dashboard)/layout.tsx` con:

```typescript
import { Header } from '@/components/layout/Header';
import { PageWrapper } from '@/components/layout/PageWrapper';
import { Sidebar } from '@/components/layout/Sidebar';
import { ThemeApplier } from '@/components/layout/ThemeApplier';
import { getCachedPerfil, getCachedSession, getCachedUser } from '@/lib/supabase/cached-queries';
import type { Perfil } from '@/types/database';
import { redirect } from 'next/navigation';
import { AuthInitializer } from './AuthInitializer';

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getCachedUser();

  if (!user) redirect('/login');

  const [perfil, session] = await Promise.all([getCachedPerfil(user.id), getCachedSession()]);

  if (!perfil) redirect('/login');

  const accessToken = session?.access_token ?? '';

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-app)' }}>
      <ThemeApplier />
      <AuthInitializer perfil={perfil as Perfil} accessToken={accessToken} />
      <Sidebar perfil={perfil as Perfil} />

      <div className="flex flex-col flex-1 min-w-0">
        <Header perfil={perfil as Perfil} />
        <main className="flex-1 p-6 overflow-auto">
          <PageWrapper>{children}</PageWrapper>
        </main>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add bdo_idu_react/BDO_React/src/app/(dashboard)/layout.tsx
git commit -m "feat: mount ThemeApplier in dashboard layout"
```

---

## Task 6: Toggle de visibilidad de contraseña en Login

**Files:**
- Modify: `src/app/(auth)/login/page.tsx`

- [ ] **Step 1: Modificar login/page.tsx**

Reemplazar el contenido completo de `src/app/(auth)/login/page.tsx` con:

```typescript
'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Eye, EyeOff } from 'lucide-react';
import { createClient } from '@/lib/supabase/client';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import type { Perfil } from '@/types/database';

const loginSchema = z.object({
  email:    z.string().email('Correo inválido').max(100),
  password: z.string().min(6, 'Mínimo 6 caracteres').max(128),
});
type LoginInput = z.infer<typeof loginSchema>;

const ROLES_VALIDOS = new Set(['operativo', 'obra', 'interventoria', 'supervision', 'admin']);

export default function LoginPage() {
  const router    = useRouter();
  const setPerfil = useAuthStore((s) => s.setPerfil);
  const [serverError, setServerError]     = useState<string | null>(null);
  const [showPassword, setShowPassword]   = useState(false);

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
  });

  async function onSubmit(data: LoginInput) {
    setServerError(null);
    const supabase = createClient();

    const { data: authData, error } = await supabase.auth.signInWithPassword({
      email:    data.email,
      password: data.password,
    });

    if (error || !authData.user) {
      setServerError('Correo o contraseña incorrectos.');
      return;
    }

    const { data: perfil, error: perfilError } = await supabase
      .from('perfiles')
      .select('id, nombre, rol, empresa, contrato_id')
      .eq('id', authData.user.id)
      .single();

    if (perfilError || !perfil) {
      setServerError('Cuenta sin perfil configurado. Contacta al administrador.');
      return;
    }

    if (!ROLES_VALIDOS.has(perfil.rol)) {
      setServerError('Rol no reconocido. Contacta al administrador.');
      return;
    }

    const accessToken = authData.session?.access_token ?? '';
    setPerfil(perfil as Perfil, accessToken);
    router.push('/estado-actual');
    router.refresh();
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'var(--bg-app)' }}
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-sm"
      >
        <div
          className="rounded-xl p-8 shadow-lg"
          style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
        >
          {/* Encabezado */}
          <div className="mb-7">
            <p
              className="text-[10px] font-mono tracking-widest uppercase mb-1"
              style={{ color: 'var(--accent-blue)' }}
            >
              BOB · Sistema de Bitácora Digital
            </p>
            <h1 className="text-2xl font-bold mb-1" style={{ color: 'var(--idu-blue)' }}>
              BDO · IDU-1556-2025
            </h1>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
              Contrato de obra · Grupo 4<br />
              Mártires · San Cristóbal · Rafael Uribe Uribe · Santafé · Antonio Nariño
            </p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <Label htmlFor="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="usuario@empresa.com"
                autoComplete="email"
                {...register('email')}
              />
              {errors.email && (
                <p className="text-xs mt-1" style={{ color: 'var(--idu-red)' }}>
                  {errors.email.message}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="password">Contraseña</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className="pr-10"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                  className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                  style={{ color: 'var(--text-muted)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs mt-1" style={{ color: 'var(--idu-red)' }}>
                  {errors.password.message}
                </p>
              )}
            </div>

            {serverError && (
              <div
                className="rounded-md px-3 py-2 text-sm"
                style={{ background: '#FEE2E2', color: 'var(--idu-red)', border: '1px solid #FECACA' }}
              >
                {serverError}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Ingresando…' : 'Ingresar al sistema'}
            </Button>
          </form>
        </div>
      </motion.div>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add bdo_idu_react/BDO_React/src/app/(auth)/login/page.tsx
git commit -m "feat: add password visibility toggle to login form"
```

---

## Task 7: Verificación final

- [ ] **Step 1: Ejecutar todos los tests**

```bash
cd bdo_idu_react/BDO_React && npx vitest run
```

Esperado: todos los tests pasan, incluyendo los 2 nuevos de `themeStore.test.ts`.

- [ ] **Step 2: Verificar build de producción**

```bash
cd bdo_idu_react/BDO_React && npx next build
```

Esperado: build exitoso sin errores de TypeScript.

- [ ] **Step 3: Verificar manualmente en el navegador**

1. Abrir la app en `http://localhost:3000/login`
2. Verificar que el botón de ojo en el campo contraseña muestra/oculta el texto
3. Iniciar sesión y navegar al dashboard
4. Verificar que el botón Moon/Sun en el header alterna el tema correctamente
5. Verificar que al recargar la página el tema vuelve al del SO
