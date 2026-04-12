# BDO · IDU-1556-2025

Sistema de sincronización **QFieldCloud → Supabase** para el seguimiento de obra del contrato IDU-1556-2025.
Consorcio Obras Peatonales 2025 · Contratista: SERVIALCO S.A.S.

---

## Flujo general

```
Inspector / Residente (campo)
        │
        │  captura en QField (Android / iOS / Desktop)
        ▼
QFieldCloud
        │  archivos GeoPackage (*.gpkg) + fotos adjuntas
        ▼
GitHub Actions  ──── cron: cada 20 min · lun–sáb · 11:00–23:00
sync/sync_qfield.py
        │
        ├─▶  PostgreSQL (Supabase)   ← tablas, registros, estados
        └─▶  Storage (Supabase)      ← fotos, bucket: Registro_Obra
                │
                ├─▶  Streamlit          dashboards y aprobaciones
                └─▶  QGIS               SIG_IDU-1556-2025_cloud.qgs
```

---

## Estructura del repositorio

```
BDO-IDU-1556-2025/
├── sync/                       Paquete Python principal
│   ├── sync_qfield.py          Orquestador (punto de entrada)
│   ├── config.py               Variables de entorno y constantes
│   ├── connections.py          Login QFieldCloud + cliente Supabase
│   ├── gpkg.py                 Descarga y lectura de GeoPackages
│   ├── photos.py               Descarga fotos y las sube a Storage
│   ├── utils.py                Funciones auxiliares (safe, safe_num, coords)
│   ├── sync_lookup.py          Tablas catálogo (infra, actividad)
│   ├── sync_geo.py             Referencia geográfica (localidades, tramos)
│   ├── sync_presupuesto.py     Presupuesto (ítems y componentes)
│   ├── sync_formularios.py     Formularios principales (cantidades, reporte…)
│   ├── sync_bd.py              Tablas secundarias del reporte diario
│   ├── sync_rf.py              Registros fotográficos (rf_*)
│   └── __init__.py
├── migrations/                 Parches SQL incrementales (si aplican)
├── .github/workflows/
│   └── sync.yml                Workflow de automatización
├── requirements.txt            Dependencias Python
├── packages.txt                Paquetes del sistema (GDAL/Fiona)
├── .devcontainer/              Configuración Codespaces
├── .gitignore
└── README.md                   Este archivo
```

---

## Módulos — descripción detallada

### `sync_qfield.py` — Orquestador

Punto de entrada único. Autentica los servicios y llama a cada módulo en el orden correcto respetando las dependencias del esquema de base de datos.

```python
# Orden de ejecución
0. Tablas catálogo    sync_tramos_aux_infra, sync_presupuesto_aux_actividad
1. Referencia geo     sync_localidades, sync_tramos_bd
2. Presupuesto        sync_presupuesto_bd, sync_presupuesto_componentes_bd
3. Formularios        sync_registros_cantidades, sync_registros_componentes,
                      sync_registros_reporte_diario, sync_formulario_pmt
4. Tablas secundarias sync_bd_personal, sync_bd_climatica,
                      sync_bd_maquinaria, sync_bd_sst
5. Fotos              sync_rf_cantidades, sync_rf_componentes,
                      sync_rf_reporte_diario
```

> El orden no es arbitrario: las tablas secundarias (paso 4) tienen FK a
> `registros_reporte_diario.folio`, que debe existir antes de insertar.
> Las fotos (paso 5) van al final porque la subida a Storage es la
> operación más lenta.

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

### `gpkg.py` — GeoPackages

| Función | Descripción |
|---|---|
| `download_gpkg(token, project_id, gpkg_file, tmp_path)` | Descarga un GPKG de QFieldCloud a `/tmp/` |
| `read_layer(tmp_path, layer_name)` | Lee una capa con geopandas; normaliza columnas a minúsculas; reproyecta a WGS84 si es necesario |
| `delete_all(supabase, table)` | Borra todos los registros de una tabla (para tablas que se reconstruyen en cada sync) |

---

### `photos.py` — Fotos

Descarga fotos adjuntas desde QFieldCloud y las sube al bucket `Registro_Obra` de Supabase Storage. Retorna la URL pública que se guarda en la columna `foto_url` de cada tabla `rf_*`.

**Ruta en Storage:** `{folio}/{nombre_archivo}`
**URL pública:** `{SUPABASE_URL}/storage/v1/object/public/Registro_Obra/{folio}/{nombre_archivo}`

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

### `sync_lookup.py` — Tablas catálogo

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_tramos_aux_infra` | `TramosIDU15562025BDTRAMOS.gpkg` | `tramos_aux_infra` | upsert por `codigo` |
| `sync_presupuesto_aux_actividad` | `PresupuestoIDU15562025BDPRESUPUESTO.gpkg` | `presupuesto_aux_actividad` | upsert por `tipo_actividad` |

Incluye mapeo de nombres a códigos de infraestructura (`Espacio Público → EP`, `Ciclorruta → CI`, `Malla Vial → MV`).

---

### `sync_geo.py` — Referencia geográfica

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_localidades` | `loca.gpkg` (capa `Loca`) | `localidades` | upsert por `loc_codigo` |
| `sync_tramos_bd` | `TramosIDU15562025BDTRAMOS.gpkg` | `tramos_bd` | upsert por `id_tramo` |

> Quirk [D-08]: la columna en el GPKG es `ciclorruta_km` (doble r),
> el código lee ambas variantes para tolerar correcciones futuras.

---

### `sync_presupuesto.py` — Presupuesto

| Función | GPKG origen | Tabla Supabase | Estrategia |
|---|---|---|---|
| `sync_presupuesto_bd` | `PresupuestoIDU15562025BDPRESUPUESTO.gpkg` | `presupuesto_bd` | upsert por `codigo_idu` |
| `sync_presupuesto_componentes_bd` | `Presupuesto_Componentes.gpkg` (capa `ppto_componentes`) | `presupuesto_componentes_bd` | upsert por `codigo_idu` |

En adiciones al contrato (nuevos ítems o ajuste de cantidades/precios), el upsert actualiza automáticamente los registros existentes e inserta los nuevos. Los ítems eliminados del GPKG permanecen en Supabase; si se requiere limpieza ejecutar `TRUNCATE presupuesto_bd CASCADE` antes del siguiente sync.

> Quirk [D-09]: columna `compenente` (typo) en lugar de `componente` en
> `Presupuesto_Componentes.gpkg`. El código lee ambas.

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

Estas tablas se reconstruyen completamente en cada sync (`delete_all` + `insert`). Todas tienen FK a `registros_reporte_diario.folio`, por eso se ejecutan **después** del paso 3.

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

Reconstruye completamente en cada sync (`delete_all` + `insert`). Para cada registro descarga la foto de QFieldCloud, la sube al bucket `Registro_Obra` y guarda la URL pública en `foto_url`.

| Función | GPKG origen | Tabla Supabase |
|---|---|---|
| `sync_rf_cantidades` | `RF_Cantidades.gpkg` | `rf_cantidades` |
| `sync_rf_componentes` | `RF_Componentes.gpkg` | `rf_componentes` |
| `sync_rf_reporte_diario` | `RF_ReporteDiario.gpkg` | `rf_reporte_diario` |

> `id_unico` en estas tablas es el identificador propio de cada foto,
> **no** una FK al formulario padre. La relación foto↔formulario se
> navega por `folio`.

---

## Ejecución local (desarrollo y pruebas)

**1. Instalar dependencias del sistema** (Linux/Codespaces — GDAL para geopandas):
```bash
sudo apt-get install -y $(cat packages.txt)
```

**2. Instalar dependencias Python:**
```bash
pip install -r requirements.txt
```

**3. Crear archivo de credenciales:**
```
sync/.env
```
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

> `sync/.env` está en `.gitignore` — nunca se sube al repositorio.

---

## Ejecución automática — GitHub Actions

Archivo: [`.github/workflows/sync.yml`](.github/workflows/sync.yml)

| Parámetro | Valor |
|---|---|
| Disparador | `cron: '*/20 11-23 * * 1-6'` |
| Frecuencia | Cada 20 minutos |
| Días | Lunes a sábado |
| Horario | 11:00 – 23:00 UTC (06:00 – 18:00 Colombia) |
| Timeout | 15 minutos por ejecución |
| Runner | `ubuntu-latest` |

También puede ejecutarse manualmente desde **Actions → Sync QFieldCloud → Supabase → Run workflow**.

---

## Estrategias de actualización por tabla

| Tabla | Estrategia | Motivo |
|---|---|---|
| `tramos_aux_infra` | upsert | catálogo estable |
| `presupuesto_aux_actividad` | upsert | catálogo estable |
| `localidades` | upsert | referencia geográfica |
| `tramos_bd` | upsert | puede crecer con adiciones |
| `presupuesto_bd` | upsert | puede crecer con adiciones |
| `presupuesto_componentes_bd` | upsert | puede crecer con adiciones |
| `registros_cantidades` | upsert por `id_unico` | preserva estado de aprobación |
| `registros_componentes` | upsert por `folio` | preserva estado de aprobación |
| `registros_reporte_diario` | upsert por `folio` | preserva estado de aprobación |
| `formulario_pmt` | upsert por `folio` | preserva historial |
| `bd_personal_obra` | delete + insert | observación diaria, se reemplaza |
| `bd_condicion_climatica` | delete + insert | observación diaria, se reemplaza |
| `bd_maquinaria_obra` | delete + insert | observación diaria, se reemplaza |
| `bd_sst_ambiental` | delete + insert | observación diaria, se reemplaza |
| `rf_cantidades` | delete + insert | fotos se re-suben con URL fresca |
| `rf_componentes` | delete + insert | fotos se re-suben con URL fresca |
| `rf_reporte_diario` | delete + insert | fotos se re-suben con URL fresca |

---

## Repositorio del esquema SQL

El DDL de la base de datos (tablas, RLS, triggers, índices) se mantiene en el repositorio separado **SupaBaseSQLEditor**. Para inicializar el esquema desde cero ejecutar en el SQL Editor de Supabase en este orden:

1. `000_DROP_ALL.sql` — elimina todas las tablas
2. `001_TABLAS.sql` — crea tablas y seed data
3. `002_RLS.sql` — políticas de seguridad por rol
4. `003_FUNCIONES_TRIGGERS.sql` — lógica de negocio en BD
5. `004_INDICES.sql` — índices de rendimiento
