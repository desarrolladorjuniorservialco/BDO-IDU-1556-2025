# BDO · IDU-1556-2025

Sistema integral de seguimiento de obra para el contrato IDU-1556-2025 Grupo 4. Integra captura en campo con QField, sincronización automática a Supabase/PostgreSQL y plataforma web Streamlit para consulta, aprobación y generación de informes.

| | |
|---|---|
| **Contrato** | IDU-1556-2025 Grupo 4 |
| **Contratista** | URBACON SAS |
| **Interventoría** | CONSORCIO INTERCONSERVACION |
| **Supervisión** | IDU |
| **Vigencia** | 2025-12-26 → 2028-02-26 |
| **Valor** | $ 40.704.606.199 COP |
| **Localidades** | Mártires · San Cristóbal · Rafael Uribe Uribe · Santafé · Antonio Nariño |

---

## Flujo general

```
Inspector de Campo (rol: operativo)
        │
        │  captura en QField (Android / iOS / Desktop)
        │  + anotaciones generales en plataforma Streamlit
        ▼
QFieldCloud
        │  GeoPackages (*.gpkg) + Excel contrato (*.xlsx) + fotos
        ▼
GitHub Actions  ──── cron: cada 20 min · lun–sáb · 11:00–23:00
sync/sync_qfield.py
        │
        ├─▶  PostgreSQL (Supabase)   ← tablas, registros, estados
        └─▶  Storage (Supabase)      ← fotos comprimidas · bucket: Registro_Obra
                │
                ├─▶  Streamlit (BDO Web)     dashboards, aprobaciones, informes PDF
                └─▶  QGIS                    SIG_IDU-1556-2025_cloud.qgs
```

---

## Roles y flujo de aprobación

| Rol | Descripción | Acceso |
|---|---|---|
| `operativo` | Inspectores de campo | Crea registros en QField; anotaciones generales; ve sus propios registros |
| `obra` | Residentes de obra | Revisión y aprobación **nivel 1** (BORRADOR → REVISADO) |
| `interventoria` | Interventoría IDU | Aprobación definitiva **nivel 2** (REVISADO → APROBADO) |
| `supervision` | Supervisión IDU | Solo lectura (todos los registros) |
| `admin` | Administrador del sistema | Aprobación nivel 2 + acceso total |

### Flujo escalonado

```
operativo crea registro  →  estado: BORRADOR
        │
        ▼
obra revisa (Nivel 1)
  · Aprueba  →  estado: REVISADO   (cant_residente, obs_residente)
  · Devuelve →  estado: DEVUELTO   (obs_residente obligatoria)
        │
        ▼
interventoria / admin aprueba definitivamente (Nivel 2)
  · Aprueba  →  estado: APROBADO   (cant_interventor, obs_interventor)
  · Devuelve →  estado: DEVUELTO   (obs_interventor obligatoria)
        │
        ▼
supervision — solo lectura en todos los estados
```

> Las columnas de BD (`cant_residente`, `cant_interventor`, `estado_residente`,
> `estado_interventor`, etc.) conservan sus nombres originales independientemente
> de los roles que las escriben. El cambio de roles solo afecta la capa Streamlit.

---

## Repositorios del proyecto

```
┌─ BDO-IDU-1556-2025  (este repositorio)
│    Scripts Python de sincronización QFieldCloud → Supabase.
│    Plataforma web Streamlit para gestión y aprobación.
│    GitHub Actions: ejecución automática cada 20 min.
│
└─ SupaBaseSQLEditor
     Esquema SQL completo: tablas, RLS, triggers, índices.
     Se ejecuta en el SQL Editor de Supabase o via psql.
```

---

## Estructura del repositorio

```
BDO-IDU-1556-2025/
├── sync/                          Paquete Python de sincronización
│   ├── sync_qfield.py             Orquestador (punto de entrada)
│   ├── config.py                  Variables de entorno y constantes
│   ├── connections.py             Login QFieldCloud + cliente Supabase
│   ├── gpkg.py                    Descarga archivos y lee GeoPackages
│   ├── photos.py                  Descarga, comprime y sube fotos a Storage
│   ├── utils.py                   Funciones auxiliares (safe, safe_num, coords)
│   ├── sync_contrato.py           Contrato: Excel → contratos / prorrogas / adiciones
│   ├── sync_lookup.py             Tablas catálogo (infra, tramos, actividad, capítulos)
│   ├── sync_geo.py                Referencia geográfica (localidades, tramos)
│   ├── sync_presupuesto.py        Presupuesto (ítems, componentes, auxiliar)
│   ├── sync_formularios.py        Formularios principales (cantidades, reporte…)
│   ├── sync_bd.py                 Tablas secundarias del reporte diario
│   ├── sync_rf.py                 Registros fotográficos (rf_*)
│   └── __init__.py
├── streamlit/                     Plataforma web BDO
│   ├── app.py                     Orquestador Streamlit (punto de entrada)
│   ├── auth.py                    Autenticación Supabase Auth + rate limiting
│   ├── config.py                  Roles, navegación y configuración de aprobaciones
│   ├── database.py                Queries a Supabase desde Streamlit
│   ├── sidebar.py                 Sidebar con navegación por rol
│   ├── session_store.py           Persistencia de sesión (URL sid)
│   ├── styles.py                  CSS global + overrides light/dark
│   ├── ui.py                      Componentes UI reutilizables
│   ├── pdf_generator.py           Generación de informes PDF
│   └── pages/
│       ├── estado_actual.py       Dashboard resumen del contrato
│       ├── anotaciones.py         Anotaciones de campo (rol operativo)
│       ├── anotaciones_diario.py  Reporte diario (personal, clima, maquinaria, SST)
│       ├── reporte_cantidades.py  Cantidades de obra + flujo de aprobación
│       ├── componente_ambiental.py Componente SST-Ambiental
│       ├── componente_social.py   Componente Social
│       ├── componente_pmt.py      Formulario PMT
│       ├── seguimiento_pmts.py    Dashboard seguimiento de PMTs
│       ├── presupuesto.py         Seguimiento presupuestal
│       ├── mapa.py                Mapa de ejecución (Folium/Pydeck)
│       ├── generar_pdf.py         Generación y descarga de informes
│       └── _componentes_base.py   Componentes UI base para formularios
├── migrations/                    Parches SQL incrementales
├── .github/workflows/
│   └── sync.yml                   Workflow de automatización
├── requirements.txt               Dependencias Python
├── packages.txt                   Paquetes del sistema (GDAL/Fiona)
└── README.md                      Este archivo
```

---

## Plataforma web — Streamlit

La aplicación Streamlit es la interfaz de gestión del contrato. Se conecta directamente a Supabase usando el JWT del usuario autenticado, de modo que las políticas RLS aplican en cada consulta.

### Inicio de sesión y seguridad

- Autenticación con **Supabase Auth** (email + contraseña).
- **Rate limiting server-side** por email: bloqueo de 15 minutos tras 3 intentos fallidos. El bloqueo es compartido entre todas las pestañas del servidor (`st.cache_resource` + `threading.Lock`), no solo por pestaña del navegador.
- Los mensajes de error son genéricos (no revelan si el correo existe).
- La contraseña nunca se almacena ni se loguea.
- El JWT del usuario se guarda en `session_state` para operaciones de escritura con RLS activo.
- La sesión persiste ante recarga del navegador via parámetro `?sid=` en la URL.
- **Control de acceso doble**: el sidebar no muestra páginas no autorizadas y `_authorized()` verifica el rol en el servidor antes de renderizar.

### Páginas y acceso por rol

| Página | operativo | obra | interventoria | supervision | admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Estado Actual | ✓ | ✓ | ✓ | ✓ | ✓ |
| Anotaciones | ✓ | ✓ | ✓ | ✓ | ✓ |
| Anotaciones Diario | ✓ | ✓ | ✓ | ✓ | ✓ |
| Reporte Cantidades | ✓ | ✓ | ✓ | ✓ | ✓ |
| Componente Ambiental - SST | ✓ | ✓ | ✓ | ✓ | ✓ |
| Componente Social | ✓ | ✓ | ✓ | ✓ | ✓ |
| Componente PMT | ✓ | ✓ | ✓ | ✓ | ✓ |
| Seguimiento PMTs | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mapa Ejecución | — | ✓ | ✓ | ✓ | ✓ |
| Seguimiento Presupuesto | — | ✓ | ✓ | ✓ | ✓ |
| Generar Informe | — | ✓ | ✓ | ✓ | ✓ |

> `operativo` accede únicamente a sus propios registros — el filtro se aplica
> en la BD por RLS (`creado_por = auth.uid()`). `obra+` ven todos los registros
> para el flujo de revisión. `formulario_pmt` no tiene filtro por `creado_por`
> en RLS → todos los roles ven todos los PMTs.

### Flujo de aprobación en Streamlit

| Rol | Acciona sobre | Estado resultante | Campos escritos |
|---|---|---|---|
| `obra` | BORRADOR | REVISADO | `cant_residente`, `estado_residente`, `aprobado_residente`, `fecha_residente`, `obs_residente` |
| `interventoria` | REVISADO | APROBADO | `cant_interventor`, `estado_interventor`, `aprobado_interventor`, `fecha_interventor`, `obs_interventor` |
| `admin` | REVISADO | APROBADO | mismos campos que interventoria |
| `operativo` / `supervision` | — | solo lectura | — |

### Módulos Streamlit

**`app.py`** — Orquestador principal. Configura la página, inyecta el CSS global (con detección de tema claro/oscuro), define el `PAGE_MAP` con todas las páginas y ejecuta el loop principal con verificación de autorización en cada carga.

**`auth.py`** — Autenticación. Login con Supabase Auth, validación de rol, rate limiting por email con `threading.Lock`, persistencia de sesión vía `session_store`.

**`config.py`** — Constantes globales: `ROL_LABELS`, `NAV_ACCESS` (control de acceso por página), `NAV_CATEGORIES` (estructura de navegación), `PAGE_COLOR` (acento por sección) y `APROBACION_CONFIG` (campos y estados del flujo de aprobación escalonado por rol).

**`database.py`** — Capa de datos. Queries a Supabase usando el cliente con JWT del usuario para que RLS aplique. Incluye `load_cantidades()` y demás funciones de carga usadas por las páginas.

**`sidebar.py`** — Sidebar con header de usuario, chips de estado rápido (total/aprobados/revisados/devueltos de cantidades), navegación por categorías filtrada por rol e ítem activo resaltado.

**`session_store.py`** — Persistencia de sesión entre recargas del navegador. Almacena `user`, `perfil`, `access_token` y `current_page` identificados por un `sid` único en la URL.

**`styles.py`** — CSS global del sistema de diseño BDO (variables, tipografía IBM Plex, componentes de tarjeta, chips, badges) + overrides para tema claro y oscuro.

**`pdf_generator.py`** — Generación de informes PDF descargables desde Streamlit.

**`pages/`** — Cada archivo es una vista independiente:

| Módulo | Descripción |
|---|---|
| `estado_actual.py` | Dashboard KPIs del contrato: avance de cantidades, estado de formularios, últimos registros |
| `anotaciones.py` | Anotaciones generales de campo; operativo crea, roles superiores consultan |
| `anotaciones_diario.py` | Reporte diario: datos de personal, condiciones climáticas, maquinaria y SST-Ambiental |
| `reporte_cantidades.py` | Vista principal de cantidades de obra con filtros, detalle de fotos y panel de aprobación |
| `componente_ambiental.py` | Registros del componente SST-Ambiental con flujo de aprobación escalonado |
| `componente_social.py` | Registros del componente Social con flujo de aprobación escalonado |
| `componente_pmt.py` | Formulario PMT: registro de Plan de Manejo de Tránsito por tramo |
| `seguimiento_pmts.py` | Dashboard de seguimiento y estado de todos los PMTs del contrato |
| `presupuesto.py` | Seguimiento presupuestal: ejecución por ítem, capítulo y tipo de infraestructura |
| `mapa.py` | Mapa interactivo de ejecución por tramo con estado y avance georreferenciado |
| `generar_pdf.py` | Configuración y descarga de informes periódicos en formato PDF |

---

## Base de datos — Supabase PostgreSQL

El esquema SQL completo se mantiene en el repositorio **SupaBaseSQLEditor**. Los scripts se ejecutan en el SQL Editor de Supabase o vía `psql`.

### Inicialización del esquema

Para crear el esquema desde cero (entorno nuevo o reset completo):

```sql
-- 1. Elimina TODAS las tablas y funciones
000_DROP_ALL.sql

-- 2. Crea tablas + seed data + triggers contractuales
001_TABLAS.sql

-- 3. Políticas de seguridad por rol (RLS)
002_RLS.sql

-- 4. Lógica de negocio: marcar_inmutable, log_cambio_estado, crear_notificacion
003_FUNCIONES_TRIGGERS.sql

-- 5. Índices de rendimiento
004_INDICES.sql

-- 6. Solo en desarrollo: perfiles de usuario demo
005_USUARIOS.sql
```

> `000_DROP_ALL.sql` elimina también las funciones (`get_rol`, `marcar_inmutable`,
> `log_cambio_estado`, `crear_notificacion`, `sync_contrato_*`). Si solo se quiere
> resetear datos sin recrear el esquema, **no ejecutar** el paso 000.

### Jerarquía de tablas (orden de FK)

```
perfiles
contratos
  ├─▶ contratos_prorrogas
  ├─▶ contratos_adiciones
  ├─▶ localidades
  ├─▶ tramos_aux_infra
  ├─▶ tramos_aux_tramos
  ├─▶ tramos_bd
  ├─▶ presupuesto_aux_actividad
  │     ├─▶ presupuesto_aux_capitulos
  │     └─▶ presupuesto_bd
  ├─▶ presupuesto_componentes_bd
  ├─▶ presupuesto_componentes_aux
  ├─▶ registros_cantidades          ← formulario principal
  ├─▶ registros_componentes         ← formulario principal
  ├─▶ registros_reporte_diario      ← formulario principal
  │     ├─▶ bd_personal_obra
  │     ├─▶ bd_condicion_climatica
  │     ├─▶ bd_maquinaria_obra
  │     └─▶ bd_sst_ambiental
  ├─▶ rf_cantidades                 ← fotos (sin FK por diseño)
  ├─▶ rf_componentes                ← fotos (sin FK por diseño)
  ├─▶ rf_reporte_diario             ← fotos (sin FK por diseño)
  ├─▶ formulario_pmt
  ├─▶ historial_estados             ← auditoría (sin FK por diseño)
  ├─▶ cierres_semanales
  │     └─▶ cierre_registros
  └─▶ notificaciones                ← genérico (sin FK por diseño)
```

### `001_TABLAS.sql` — DDL

Define todas las tablas del dominio en snake_case respetando el orden de FK. Incluye:
- Seed data de `contratos_aux_infra` (EP, CI, MV), `presupuesto_aux_actividad` y el registro inicial del contrato IDU-1556-2025.
- Bloques `DO` idempotentes de migración (PATCH-001, PATCH-002).
- Triggers de sincronización contractual:
  - `trg_sync_prorrogas` → actualiza `contratos.prorrogas` y `contratos.plazo_actual` automáticamente.
  - `trg_sync_adiciones` → actualiza `contratos.adiciones` y `contratos.valor_actual` automáticamente.

### `002_RLS.sql` — Seguridad por fila

RLS habilitado en todas las tablas. La función helper `get_rol()` evalúa el rol del usuario autenticado.

| Tabla / grupo | Política |
|---|---|
| `perfiles` | cada usuario ve su propio perfil; admin gestiona todos |
| `contratos`, `prorrogas`, `adiciones` | lectura: todos; escritura: admin/service_role |
| `registros_cantidades` / `componentes` / `reporte_diario` | operativo: crea/edita sus borradores; obra: aprueba nivel 1; interventoria: aprueba nivel 2; admin: acceso total |
| `formulario_pmt` | operativo crea; roles superiores leen todos |
| `historial_estados` | rol ≥ obra lee; roles escriben en cambios de estado |
| `cierres_semanales` | rol ≥ obra lee; interventoria/admin crea |
| `notificaciones` | cada usuario ve las propias |
| Tablas catálogo (`localidades`, `tramos_*`, `presupuesto_*`) | solo lectura (service_role escribe) |
| `rf_*`, `bd_*` | lectura todos; escritura solo service_role |

### `003_FUNCIONES_TRIGGERS.sql` — Lógica de negocio

Instalados sobre `registros_cantidades`, `registros_componentes` y `registros_reporte_diario`:

| Función | Trigger | Acción |
|---|---|---|
| `marcar_inmutable()` | `BEFORE UPDATE` | Cuando `estado → 'APROBADO'`: bloquea modificaciones posteriores y estampa `fecha_interventor` |
| `log_cambio_estado()` | `AFTER UPDATE` | Registra cada cambio de estado en `historial_estados` con `tabla_origen`, usuario y observación |
| `crear_notificacion()` | `AFTER INSERT OR UPDATE` | Genera entradas en `notificaciones` para todos los usuarios activos del contrato |

> Los triggers contractuales (`trg_sync_prorrogas`, `trg_sync_adiciones`) están
> definidos en `001_TABLAS.sql` junto a la DDL que los origina.

### `004_INDICES.sql` — Rendimiento

Índices sobre columnas de consulta frecuente en: `registros_cantidades`, `registros_componentes`, `registros_reporte_diario`, `historial_estados`, `cierres_semanales`, `notificaciones`, `contratos_prorrogas`, `contratos_adiciones`, `formulario_pmt`, `bd_personal_obra`, `bd_condicion_climatica`, `bd_maquinaria_obra`, `bd_sst_ambiental`, `rf_cantidades`, `rf_componentes`, `rf_reporte_diario`.

Columnas cubiertas: `folio`, `estado`, `contrato_id`, `(contrato_id, estado)`, `id_tramo`, `fecha`, `inspector`, `item_pago`, `semana`, `destinatario`.

### `005_USUARIOS.sql` — Solo desarrollo

Crea perfiles de usuario demo. Flujo: crear usuario en Supabase Auth → copiar UUID → insertar en `perfiles` con ese UUID.

---

## Módulos de sincronización — descripción detallada

### `sync_qfield.py` — Orquestador

Punto de entrada único. Autentica los servicios y llama a cada módulo en el orden correcto respetando las dependencias del esquema.

```
Paso 0 · Contrato         sync_contrato_excel
           └─ contratos, contratos_prorrogas, contratos_adiciones
              (debe ir primero: otras tablas referencian contratos.id)

Paso 1 · Tablas catálogo  sync_tramos_aux_infra
                          sync_tramos_aux_tramos
                          sync_presupuesto_aux_actividad
                          sync_presupuesto_aux_capitulos

Paso 2 · Referencia geo   sync_localidades
                          sync_tramos_bd

Paso 3 · Presupuesto      sync_presupuesto_bd
                          sync_presupuesto_componentes_bd
                          sync_presupuesto_componentes_aux

Paso 4 · Formularios      sync_registros_cantidades
                          sync_registros_componentes
                          sync_registros_reporte_diario
                          sync_formulario_pmt

Paso 5 · Secundarias      sync_bd_personal
                          sync_bd_climatica
                          sync_bd_maquinaria
                          sync_bd_sst

Paso 6 · Fotos            sync_rf_cantidades
                          sync_rf_componentes
                          sync_rf_reporte_diario
```

> El orden no es arbitrario: las tablas secundarias (paso 5) tienen FK a
> `registros_reporte_diario.folio` que debe existir antes de insertar.
> Las fotos (paso 6) van al final: son la operación más lenta
> (descarga + compresión Pillow + subida a Storage por cada registro).

---

### `config.py` — Configuración

Lee variables de entorno. En local las carga desde `sync/.env`; en GitHub Actions las inyecta el workflow desde los Secrets del repositorio.

| Constante | Descripción |
|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | `service_role` key (acceso total, solo en backend) |
| `QFIELD_USER` | Usuario de QFieldCloud |
| `QFIELD_PASSWORD` | Contraseña de QFieldCloud |
| `PROJECT_NAME` | `BDO_IDU-1556-2025` — nombre del proyecto en QFieldCloud |
| `BASE_URL` | `https://app.qfield.cloud/api/v1` |
| `CONTRATO_ID` | `IDU-1556-2025` |
| `STORAGE_BUCKET` | `Registro_Obra` — bucket de Supabase Storage |

---

### `connections.py` — Autenticación

| Función | Descripción |
|---|---|
| `qfield_login()` | Obtiene token Bearer de QFieldCloud |
| `get_supabase()` | Crea cliente Supabase con `service_role` key |
| `get_project_id(token)` | Busca el proyecto por nombre y retorna su UUID |
| `qfield_headers(token)` | Devuelve headers HTTP con el token |

---

### `gpkg.py` — Archivos y GeoPackages

| Función | Descripción |
|---|---|
| `download_file(token, project_id, filename, tmp_path)` | Descarga **cualquier archivo** del proyecto QFieldCloud (GPKG, XLSX, etc.) a `/tmp/` |
| `download_gpkg(token, project_id, gpkg_file, tmp_path)` | Alias de `download_file` para retrocompatibilidad |
| `read_layer(tmp_path, layer_name)` | Lee una capa con geopandas; normaliza columnas a minúsculas; reproyecta a WGS84 si es necesario |
| `delete_all(supabase, table)` | Borra todos los registros de una tabla (para tablas que se reconstruyen en cada sync) |

---

### `photos.py` — Fotos con compresión automática

Descarga fotos adjuntas desde QFieldCloud, las **comprime con Pillow** y las sube al bucket `Registro_Obra` de Supabase Storage. Retorna la URL pública que se guarda en la columna `foto_url` de cada tabla `rf_*`.

**Parámetros de compresión:**

| Parámetro | Valor | Descripción |
|---|---|---|
| `MAX_DIMENSION` | 2048 px | Lado mayor máximo; escala proporcional con LANCZOS |
| `JPEG_QUALITY` | 82 | Calidad JPEG (0–95); buena relación calidad/peso para fotos de obra |
| EXIF | descartado | Pillow no copia metadata al guardar → ahorro extra de 30-80 KB |
| Formato | JPEG | PNG y otros formatos se convierten a RGB JPEG |
| Extensión | `.jpg` | El archivo en Storage siempre queda con extensión `.jpg` |

> En la práctica una foto de 5 MB tomada con celular queda entre 400–900 KB
> (reducción de ~80-85%) sin diferencia visual perceptible para fotos de obra.
> Si Pillow falla por cualquier razón, el original se sube sin comprimir.

**Ruta en Storage:** `{folio}/{nombre}.jpg`
**URL pública:** `{SUPABASE_URL}/storage/v1/object/public/Registro_Obra/{folio}/{nombre}.jpg`

> Si la ruta almacenada en el GPKG apunta a un archivo fuera del proyecto
> QField (por ejemplo `../../../Pictures/imagen.jpg`), la foto no existe en
> QFieldCloud y no puede descargarse. El inspector debe usar fotos guardadas
> dentro de la carpeta del proyecto o capturadas con la cámara del dispositivo.

---

### `utils.py` — Auxiliares

| Función | Descripción |
|---|---|
| `safe(val)` | Convierte a string limpio; retorna `None` si vacío, `nan`, `NaT` |
| `safe_num(val)` | Convierte a float; retorna `None` si inválido o NaN |
| `coords_from_geom(row)` | Extrae `(lat, lon)` desde la columna `geometry` |

---

### `sync_contrato.py` — Seguimiento contractual (Excel)

Descarga `Contrato_IDU_1556_2025.xlsx` **una sola vez** desde QFieldCloud y sincroniza las tres hojas contractuales.

| Función interna | Hoja Excel | Tabla Supabase | Estrategia |
|---|---|---|---|
| `_sync_ini` | `BD_CTO_INI` | `contratos` | upsert por `id` |
| `_sync_pro` | `BD_CTO_PRO` | `contratos_prorrogas` | upsert por `(contrato_id, numero)` |
| `_sync_adi` | `BD_CTO_ADI` | `contratos_adiciones` | upsert por `(contrato_id, numero)` |

> Los campos `contratos.prorrogas`, `contratos.plazo_actual`, `contratos.adiciones`
> y `contratos.valor_actual` **no se escriben desde aquí** — los actualiza
> automáticamente el trigger `trg_sync_prorrogas` / `trg_sync_adiciones`
> en PostgreSQL cada vez que se inserta o modifica una fila en las tablas de detalle.

---

### `sync_lookup.py` — Tablas catálogo

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_tramos_aux_infra` | `TramosIDU15562025BDTRAMOS.gpkg` | `tramos_aux_infra` | upsert por `codigo` |
| `sync_tramos_aux_tramos` | `TramosIDU15562025AUXTRAMOS.gpkg` | `tramos_aux_tramos` | upsert por `codigo` |
| `sync_presupuesto_aux_actividad` | `PresupuestoIDU15562025BDPRESUPUESTO.gpkg` | `presupuesto_aux_actividad` | upsert por `tipo_actividad` |
| `sync_presupuesto_aux_capitulos` | `PresupuestoIDU15562025AUXCAPITULOS.gpkg` | `presupuesto_aux_capitulos` | upsert por `(tipo_actividad, capitulo_num)` |

Incluye mapeo de nombres a códigos de infraestructura (`Espacio Público → EP`, `Ciclorruta → CI`, `Malla Vial → MV`).

---

### `sync_geo.py` — Referencia geográfica

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_localidades` | `loca.gpkg` (capa `Loca`) | `localidades` | upsert por `loc_codigo` |
| `sync_tramos_bd` | `TramosIDU15562025BDTRAMOS.gpkg` | `tramos_bd` | upsert por `id_tramo` |

> Quirk [D-08]: la columna en el GPKG es `ciclorruta_km` (doble r);
> el código lee ambas variantes para tolerar correcciones futuras.

---

### `sync_presupuesto.py` — Presupuesto

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_presupuesto_bd` | `PresupuestoIDU15562025BDPRESUPUESTO.gpkg` | `presupuesto_bd` | upsert por `codigo_idu` |
| `sync_presupuesto_componentes_bd` | `Presupuesto_Componentes.gpkg` (capa `ppto_componentes`) | `presupuesto_componentes_bd` | upsert por `codigo_idu` |
| `sync_presupuesto_componentes_aux` | `ppto_componentes__aux_pptcomponentes.gpkg` | `presupuesto_componentes_aux` | delete + insert |

> Quirk [D-09]: columna `compenente` (typo) en lugar de `componente` en
> varios GPKGs de presupuesto. El código lee ambas variantes.

---

### `sync_formularios.py` — Formularios principales

| Función | GPKG origen | Tabla Supabase | `on_conflict` |
|---|---|---|---|
| `sync_registros_cantidades` | `Formulario_Cantidades.gpkg` (capa `Formulario_Cantidades_V2`) | `registros_cantidades` | `id_unico` |
| `sync_registros_componentes` | `Reporte_Componentes.gpkg` | `registros_componentes` | `folio` |
| `sync_registros_reporte_diario` | `Reporte_Diario.gpkg` (capa `Reporte_Diario`) | `registros_reporte_diario` | `folio` |
| `sync_formulario_pmt` | `Formulario_PMT.gpkg` | `formulario_pmt` | `folio` |

**Notas importantes:**
- `registros_cantidades` usa `on_conflict='id_unico'` (no `folio`) porque un mismo formulario puede tener varios ítems de pago con el mismo folio pero distinto `id_unico`.
- El campo `estado` **no se sobreescribe** durante el sync para no revertir registros ya aprobados por el residente o interventor.
- Quirk [D-03]: columna `feca_reporte` (typo) en `Reporte_Diario.gpkg`; el código lee ambas variantes.

---

### `sync_bd.py` — Tablas secundarias del reporte diario

Se reconstruyen completamente en cada sync (`delete_all` + `insert`). Todas tienen FK a `registros_reporte_diario.folio`, por eso se ejecutan **después** del paso 4.

| Función | GPKG origen | Tabla Supabase |
|---|---|---|
| `sync_bd_personal` | `BD_PersonalObra.gpkg` | `bd_personal_obra` |
| `sync_bd_climatica` | `BD_CondicionClimatica.gpkg` | `bd_condicion_climatica` |
| `sync_bd_maquinaria` | `BD_MaquinariaObra.gpkg` | `bd_maquinaria_obra` |
| `sync_bd_sst` | `BD_SST-Ambiental.gpkg` (capa `BBD_SST-Ambiental`) | `bd_sst_ambiental` |

> Quirks varios: `perosnal_boal` (typo en BD_PersonalObra), nombres de
> columnas con paréntesis en BD_MaquinariaObra, capa con doble B en
> BD_SST-Ambiental. El código maneja todos estos casos con lecturas OR.

---

### `sync_rf.py` — Registros fotográficos

Usa **inserción incremental**: al inicio de cada función se hace un solo SELECT para obtener todos los `id_unico` ya existentes en Supabase. Los registros ya presentes se saltan sin descargar ni comprimir. Solo los registros **nuevos** pasan por `upload_photo()` + `INSERT`.

Si el archivo ya existe en Storage (error `Duplicate`) la URL se reutiliza directamente sin re-subir — permite recuperar registros cuya fila fue eliminada pero cuya foto sigue vigente en el bucket.

| Función | GPKG origen | Tabla Supabase |
|---|---|---|
| `sync_rf_cantidades` | `RF_Cantidades.gpkg` | `rf_cantidades` |
| `sync_rf_componentes` | `RF_Componentes.gpkg` | `rf_componentes` |
| `sync_rf_reporte_diario` | `RF_ReporteDiario.gpkg` | `rf_reporte_diario` |

> `id_unico` en estas tablas es el identificador propio de cada foto,
> **no** una FK al formulario padre. La relación foto↔formulario se
> navega por `folio`.

---

## Estrategias de actualización por tabla

| Tabla | Estrategia | Motivo |
|---|---|---|
| `contratos` | upsert por `id` | dato maestro del Excel |
| `contratos_prorrogas` | upsert por `(contrato_id, numero)` | acumulativo |
| `contratos_adiciones` | upsert por `(contrato_id, numero)` | acumulativo |
| `tramos_aux_infra` | upsert | catálogo estable |
| `tramos_aux_tramos` | upsert | catálogo estable |
| `presupuesto_aux_actividad` | upsert | catálogo estable |
| `presupuesto_aux_capitulos` | upsert | catálogo estable |
| `localidades` | upsert | referencia geográfica |
| `tramos_bd` | upsert | puede crecer con adiciones |
| `presupuesto_bd` | upsert | puede crecer con adiciones |
| `presupuesto_componentes_bd` | upsert | puede crecer con adiciones |
| `presupuesto_componentes_aux` | delete + insert | sin clave única |
| `registros_cantidades` | upsert por `id_unico` | preserva estado de aprobación |
| `registros_componentes` | upsert por `folio` | preserva estado de aprobación |
| `registros_reporte_diario` | upsert por `folio` | preserva estado de aprobación |
| `formulario_pmt` | upsert por `folio` | preserva historial |
| `bd_personal_obra` | delete + insert | observación diaria, se reemplaza |
| `bd_condicion_climatica` | delete + insert | observación diaria, se reemplaza |
| `bd_maquinaria_obra` | delete + insert | observación diaria, se reemplaza |
| `bd_sst_ambiental` | delete + insert | observación diaria, se reemplaza |
| `rf_cantidades` | insert incremental (skip by `id_unico`) | evita reprocesar fotos ya sincronizadas |
| `rf_componentes` | insert incremental (skip by `id_unico`) | evita reprocesar fotos ya sincronizadas |
| `rf_reporte_diario` | insert incremental (skip by `id_unico`) | evita reprocesar fotos ya sincronizadas |

---

## Ejecución local (desarrollo y pruebas)

**1. Instalar dependencias del sistema** (Linux/Codespaces — GDAL para geopandas):
```bash
sudo apt-get install -y $(cat packages.txt)
```

**2. Instalar dependencias Python:**
```bash
pip install -r requirements.txt
# supabase · geopandas · requests · python-dotenv · openpyxl · Pillow
```

**3. Crear archivo de credenciales:**

`sync/.env` (está en `.gitignore` — nunca se sube al repositorio)
```env
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_KEY=<service_role_key>
QFIELD_USER=<usuario>
QFIELD_PASSWORD=<contraseña>
```

**4. Ejecutar la sincronización:**
```bash
# Desde la raíz del repositorio
python -m sync.sync_qfield

# Alternativa directa
python sync/sync_qfield.py
```

**5. Ejecutar la plataforma web:**
```bash
cd streamlit
streamlit run app.py
```

---

## Ejecución automática — GitHub Actions

Archivo: [`.github/workflows/sync.yml`](.github/workflows/sync.yml)

| Parámetro | Valor |
|---|---|
| Disparador | `cron: '*/20 11-23 * * 1-6'` |
| Frecuencia | Cada 20 minutos |
| Días | Lunes a sábado |
| Horario | 11:00 – 23:00 UTC (06:00 – 18:00 Colombia) |
| Runner | `ubuntu-latest` |

También puede ejecutarse manualmente desde **Actions → Sync QFieldCloud → Supabase → Run workflow**.

---

## Decisiones de diseño relevantes

**`folio` vs `id_unico`**
`folio` identifica el formulario completo; `id_unico` identifica cada fila dentro del GPKG. `registros_cantidades` puede tener múltiples filas con el mismo `folio` (una por ítem de pago). El sync hace upsert por `id_unico`, no por `folio`.

**FK ausentes en columnas de sync**
`id_tramo`, `codigo_elemento`, `tipo_infra` y `tipo_actividad` en `registros_*` son `TEXT` sin `REFERENCES`. El sync puede insertar formularios antes de que las tablas de referencia estén completamente sincronizadas, lo que causaría error 23503. La integridad se garantiza por el orden de sync, no por FK.

**`rf_*` sin FK en `id_unico`**
`id_unico` en las tablas de fotos es el identificador propio de cada foto, no una referencia al formulario padre. La relación foto↔formulario se navega por `folio`. Agregar FK causaba error 23503 en producción.

**`historial_estados` y `notificaciones` sin FK en `registro_id`**
Estas tablas auditan las tres tablas de formularios. Una FK a una sola tabla haría imposible auditar las otras dos. Se usa `tabla_origen TEXT CHECK(...)` para identificar la procedencia.

**Contadores contractuales mantenidos por trigger**
`contratos.prorrogas`, `.plazo_actual`, `.adiciones` y `.valor_actual` son mantenidos por `trg_sync_prorrogas` y `trg_sync_adiciones`. El sync de Excel solo escribe los campos base del contrato y el detalle de cada hoja.

**`intrventoria` (typo heredado)**
La columna se llama `intrventoria` (con typo) en el Excel `Contrato_IDU_1556_2025.xlsx` hoja `BD_CTO_INI` y en la BD. Se mantiene el nombre para garantizar compatibilidad exacta con el archivo fuente. El código de sync acepta tanto `intrventoria` como `interventoria` para tolerancia.

**`foto_url` en `rf_*` visible desde Streamlit**
Cada foto se sube al bucket `Registro_Obra` de Supabase Storage durante el sync, comprimida a JPEG quality=82 / máx 2048px. La URL pública en `foto_url` puede usarse directamente en Streamlit con `st.image(url)`.
