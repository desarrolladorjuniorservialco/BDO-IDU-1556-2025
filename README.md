# BDO · IDU-1556-2025

Sistema de sincronización **QFieldCloud → Supabase** para el seguimiento de obra del contrato IDU-1556-2025.

| | |
|---|---|
| **Contrato** | IDU-1556-2025 Grupo 4 |
| **Contratista** | URBACON SAS |
| **Interventoría** | CONSORCIO INTERCONSERVACION |
| **Supervisión** | IDU |
| **Vigencia** | 2025-12-26 → 2028-02-26 |
| **Valor** | $ 40.704.606.199 COP |

---

## Flujo general

```
Inspector / Residente (campo)
        │
        │  captura en QField (Android / iOS / Desktop)
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
                ├─▶  Streamlit          dashboards y aprobaciones
                └─▶  QGIS               SIG_IDU-1556-2025_cloud.qgs
```

---

## Estructura del repositorio

```
BDO-IDU-1556-2025/
├── sync/                          Paquete Python principal
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
├── migrations/                    Parches SQL incrementales (si aplican)
├── .github/workflows/
│   └── sync.yml                   Workflow de automatización
├── requirements.txt               Dependencias Python
├── packages.txt                   Paquetes del sistema (GDAL/Fiona)
└── README.md                      Este archivo
```

---

## Módulos — descripción detallada

### `sync_qfield.py` — Orquestador

Punto de entrada único. Autentica los servicios y llama a cada módulo en el orden correcto respetando las dependencias del esquema de base de datos.

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
> `registros_reporte_diario.folio`, que debe existir antes de insertar.
> Las fotos (paso 6) van al final porque son la operación más lenta
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
> QField (por ejemplo `../../../Pictures/imagen.jpg`), la foto no existe
> en QFieldCloud y no puede descargarse. El inspector debe usar fotos
> guardadas dentro de la carpeta del proyecto o capturadas con la cámara
> del dispositivo móvil.

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

Estas tablas se reconstruyen completamente en cada sync (`delete_all` + `insert`). Todas tienen FK a `registros_reporte_diario.folio`, por eso se ejecutan **después** del paso 4.

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

Usa **inserción incremental**: al inicio de cada función se hace **un solo SELECT** para obtener todos los `id_unico` ya existentes en Supabase. Los registros cuyo `id_unico` ya está en la tabla se saltan sin descargar, comprimir ni intentar subir la foto. Solo los registros **nuevos** pasan por `upload_photo()` + `INSERT`.

Si el archivo ya existe en Storage (error `Duplicate`) la URL se reutiliza directamente sin re-subir — esto permite recuperar registros cuya fila de BD fue eliminada pero cuya foto sigue vigente en el bucket.

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

**4. Ejecutar:**
```bash
# Desde la raíz del repositorio
python -m sync.sync_qfield

# Alternativa directa
python sync/sync_qfield.py
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

## Repositorio del esquema SQL

El DDL de la base de datos (tablas, RLS, triggers, índices) se mantiene en el repositorio separado **SupaBaseSQLEditor**. Para inicializar el esquema desde cero, ejecutar en el SQL Editor de Supabase en este orden:

1. `000_DROP_ALL.sql` — elimina todas las tablas y funciones
2. `001_TABLAS.sql` — crea tablas, seed data y triggers contractuales
3. `002_RLS.sql` — políticas de seguridad por rol (todas las tablas)
4. `003_FUNCIONES_TRIGGERS.sql` — lógica de negocio en BD
5. `004_INDICES.sql` — índices de rendimiento
6. `005_USUARIOS.sql` — solo en desarrollo

---

## Decisiones de diseño relevantes

**`folio` vs `id_unico`**
`folio` identifica el formulario completo; `id_unico` identifica cada fila dentro del GPKG. `registros_cantidades` puede tener múltiples filas con el mismo `folio` (una por ítem de pago). El sync hace upsert por `id_unico`, no por `folio`.

**FK ausentes en columnas de sync**
`id_tramo`, `codigo_elemento`, `tipo_infra` y `tipo_actividad` en `registros_*` son `TEXT` sin `REFERENCES`. El sync puede insertar formularios antes de que las tablas de referencia estén completamente sincronizadas, lo que causaría error 23503. La integridad se garantiza por el orden de sync, no por FK.

**`rf_*` sin FK en `id_unico`**
`id_unico` en las tablas de fotos es el identificador propio de cada foto, no una referencia al formulario padre. La relación foto↔formulario se navega por `folio`.

**`historial_estados` y `notificaciones` sin FK en `registro_id`**
Estas tablas auditan las tres tablas de formularios. Una FK a una sola tabla haría imposible auditar las otras dos. Se usa `tabla_origen TEXT CHECK(...)` para identificar la procedencia.

**Contadores contractuales mantenidos por trigger**
`contratos.prorrogas`, `.plazo_actual`, `.adiciones` y `.valor_actual` son mantenidos por `trg_sync_prorrogas` y `trg_sync_adiciones`. El sync de Excel solo escribe los campos base del contrato y el detalle de cada hoja.
