# Dark Mode Toggle + Password Visibility — Design

**Fecha:** 2026-04-29
**Proyecto:** BDO-IDU-React (Next.js / BDO_React)

---

## Alcance

Dos mejoras de UX independientes:

1. Botón de alternancia modo oscuro/claro en el Header del dashboard.
2. Botón de mostrar/ocultar contraseña en el formulario de login.

---

## 1. Toggle de Tema (Dark/Light Mode)

### Estado del tema — `themeStore`

**Archivo:** `src/stores/themeStore.ts`

- Store Zustand sin persistencia (solo estado en memoria de la sesión).
- Estado: `theme: 'light' | 'dark'`
- Inicialización: lee `window.matchMedia('(prefers-color-scheme: dark)').matches` para arrancar desde la preferencia del SO.
- Acción: `toggle()` alterna entre `'light'` y `'dark'`.
- Al recargar la página, el tema vuelve a la preferencia del SO (sin localStorage).

### Aplicación del tema — `ThemeApplier`

**Archivo:** `src/components/layout/ThemeApplier.tsx`

- Componente cliente (`'use client'`), sin UI visual (retorna `null`).
- Se monta en `src/app/(dashboard)/layout.tsx`.
- Usa `useEffect` para subscribirse al `themeStore` y aplicar/quitar el atributo `data-theme="dark"` en `document.documentElement`.

### CSS — `globals.css`

- Agregar selector `html[data-theme="dark"] { ... }` con las mismas variables que ya existen en `@media (prefers-color-scheme: dark)`. Este bloque se ubica después del bloque `:root` para que su especificidad igual pero posición posterior lo haga tomar precedencia.
- Ambos mecanismos conviven: el `@media` aplica cuando no hay atributo manual; el `html[data-theme="dark"]` toma precedencia cuando el usuario activa el toggle.

### Botón toggle — `Header.tsx`

**Archivo:** `src/components/layout/Header.tsx`

- Importar `Sun` y `Moon` de `lucide-react` (ya es dependencia del proyecto).
- Agregar botón entre Bell y LogOut:
  - Muestra `Moon` cuando `theme === 'light'` (acción: pasar a oscuro).
  - Muestra `Sun` cuando `theme === 'dark'` (acción: pasar a claro).
- Estilos idénticos al botón LogOut: `h-9 w-9 rounded-md hover:bg-white/10`, color `rgba(255,255,255,0.80)`.
- `title` descriptivo: `"Cambiar a modo oscuro"` / `"Cambiar a modo claro"`.

---

## 2. Toggle Visibilidad de Contraseña — Login

**Archivo:** `src/app/(auth)/login/page.tsx`

- Agregar `const [showPassword, setShowPassword] = useState(false)`.
- Envolver el `<Input>` de contraseña en `<div className="relative">`.
- Cambiar `type` del input dinámicamente: `type={showPassword ? 'text' : 'password'}`.
- Agregar `<button>` absoluto dentro del div:
  - Posición: `absolute right-3 top-1/2 -translate-y-1/2`
  - `type="button"` (no dispara submit).
  - Muestra `EyeOff` cuando la contraseña es visible, `Eye` cuando está oculta.
  - Color del icono: `var(--text-muted)` con `hover:text-[var(--text-primary)]`.
- El `<Input>` debe tener `pr-10` para no solaparse con el botón.

---

## Archivos afectados

| Acción | Archivo |
|--------|---------|
| Crear  | `src/stores/themeStore.ts` |
| Crear  | `src/components/layout/ThemeApplier.tsx` |
| Editar | `src/app/globals.css` |
| Editar | `src/components/layout/Header.tsx` |
| Editar | `src/app/(dashboard)/layout.tsx` |
| Editar | `src/app/(auth)/login/page.tsx` |

---

## Restricciones

- Sin dependencias nuevas (Lucide ya está en el proyecto).
- Sin `localStorage` ni cookies — el tema es solo de sesión.
- El toggle de tema solo existe en el Header del dashboard (no en login).
- El `ThemeApplier` no renderiza ningún elemento visual.
