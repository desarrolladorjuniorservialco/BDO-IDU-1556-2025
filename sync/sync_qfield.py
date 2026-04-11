"""
sync_qfield.py  v2  — columnas corregidas contra GPKGs reales
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase

═══════════════════════════════════════════════════════════════
DISCREPANCIAS ENCONTRADAS AL INSPECCIONAR LOS GPKG LOCALES
(carpeta SERVIALCO__BDO_IDU-1556-2025)
═══════════════════════════════════════════════════════════════

[D-01] Formulario_Cantidades.gpkg
  · foto_1…foto_5 NO existen como columnas; las fotos van en RF_Cantidades.gpkg
  · fecha_inicio / fecha_fin no existen; solo existe 'fecha'
    → fecha se mapea a fecha_inicio; fecha_fin queda NULL
  · 'codigointerventor' → columna real: 'codigo_interventor'
  · 'acompañamiento interventor' (con espacio) → real: 'acompañamiento_interventor'

[D-02] Reporte_Componentes.gpkg
  · Layer real: 'PMT - Plan de Manejo del Transito' (nombre interno del GPKG)
    El script lee sin especificar layer → toma la primera, que es esa. OK.
  · Mismo problema codigointerventor / acompañamiento_interventor que D-01

[D-03] Reporte_Diario.gpkg
  · TYPO en columna: 'feca_reporte' (le falta la 'h') en lugar de 'fecha_reporte'
    → el script debe leer 'feca_reporte' OR 'fecha_reporte' (compatibilidad futura)

[D-04] BD_PersonalObra.gpkg
  · 'personaloperativo'  → real: 'personal_operativo'
  · 'personalboal'       → real: 'perosnal_boal'  (¡TYPO en GPKG: 'perosnal'!)
  · 'personaltransito'   → real: 'personal_transito'

[D-05] BD_CondicionClimatica.gpkg
  · 'estadoclima'  → real: 'estado_clima'

[D-06] BD_MaquinariaObra.gpkg  — nombres descriptivos completos con paréntesis
  · 'equiposespeciales'    → real: 'equipos_especiales'
  · 'minicargador'         → real: 'minicargador_(con_aditamento_martillo)'
  · 'ruteadora'            → real: 'ruteadora_(rortadora_de_pavimento)'
    (ojo: 'rortadora' es un typo del GPKG)
  · 'compresor'            → real: 'compresor_de_aire'
  · 'retrocargador'        → real: 'retrocargador_(con_aditamento_martillo)'
  · 'extendedoraasfalto'   → real: 'extendedora_de_asfalto_(finisher)'
  · 'compactadorneumatico' → real: 'compactador_neumatico'

[D-07] BD_SST-Ambiental.gpkg
  · Layer real: 'BBD_SST-Ambiental' (doble B — NO es typo, es el nombre real)
    La versión corregida anterior cambió esto incorrectamente a 'BD_SST-Ambiental'.
    Se revierte a 'BBD_SST-Ambiental'.
  · 'kitantiderrames'   → real: 'kit_antiderrames'
  · 'puntohidratacion'  → real: 'punto_de_hidratacion'

[D-08] TramosIDU15562025BDTRAMOS.gpkg
  · 'cicloruta_km'   → real: 'ciclorruta_km'  (doble 'r' en el GPKG)

[D-09] Presupuesto_Componentes.gpkg
  · 'componente'  → real: 'compenente'  (TYPO en GPKG: le falta una 'o')
    Se lee el typo real; cuando el GPKG sea corregido, el OR cubre ambos.

[D-10] GPKGs en carpeta NO sincronizados (presentes pero no usados):
  · TramosIDU15562025AUXINFRA.gpkg     → tramos_aux_infra  (el script la puebla
  · PresupuestoIDU15562025AUXACTIVIDAD.gpkg  desde los BD gpkg, no desde aux)
  · PresupuestoIDU15562025AUXCAPITULOS.gpkg → presupuesto_aux_capitulos (no sincronizado)
  · TramosIDU15562025AUXTRAMOS.gpkg    → tramos_aux_tramos (no sincronizado)
  · Ciclorrutas_Tramos_15562025.gpkg, Espacio_Publico_*.gpkg, Tramos_15562025.gpkg
    → capas geográficas visuales, no van a Supabase

[BUG-PY-001] (de versión anterior) estado sobreescrito → CORREGIDO: sin 'estado' en dict
[BUG-PY-002] (de versión anterior) layer SST con typo → REVERTIDO: 'BBD_SST-Ambiental'
═══════════════════════════════════════════════════════════════
"""

import os
import math
import requests
import geopandas as gpd
from supabase import create_client
from datetime import datetime

SUPABASE_URL    = os.environ['SUPABASE_URL']
SUPABASE_KEY    = os.environ['SUPABASE_KEY']
QFIELD_USER     = os.environ['QFIELD_USER']
QFIELD_PASSWORD = os.environ['QFIELD_PASSWORD']
PROJECT_NAME    = 'BDO_IDU-1556-2025'
BASE_URL        = 'https://app.qfield.cloud/api/v1'
CONTRATO_ID     = 'IDU-1556-2025'


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

def safe(val):
    if val is None:
        return None
    try:
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return None if s in ('', 'nan', 'None', 'NaT') else s


def safe_num(val):
    if val is None:
        return None
    try:
        f = float(val)
        return None if math.isnan(f) else f
    except (TypeError, ValueError):
        return None


def coords_from_geom(row):
    lat = lon = None
    geom = row.get('geometry') or row.get('geom')
    if geom is not None:
        try:
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                lon, lat = geom.x, geom.y
        except Exception:
            pass
    return lat, lon


# ─────────────────────────────────────────────────────────────────────────────
# Conexiones
# ─────────────────────────────────────────────────────────────────────────────

def get_supabase():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Conectado a Supabase")
    return client


def qfield_login():
    r = requests.post(
        f'{BASE_URL}/auth/login/',
        json={'username': QFIELD_USER, 'password': QFIELD_PASSWORD},
        timeout=30
    )
    r.raise_for_status()
    token = r.json().get('token')
    print("✓ QFieldCloud autenticado")
    return token


def qfield_headers(token):
    return {'Authorization': f'Token {token}'}


def get_project_id(token):
    r = requests.get(f'{BASE_URL}/projects/', headers=qfield_headers(token), timeout=30)
    r.raise_for_status()
    for p in r.json():
        if PROJECT_NAME in p.get('name', ''):
            pid = p.get('id')
            print(f"✓ Proyecto: {p.get('name')} → {pid}")
            return pid
    raise Exception(f"Proyecto '{PROJECT_NAME}' no encontrado")


# ─────────────────────────────────────────────────────────────────────────────
# Descarga y lectura de GeoPackages
# ─────────────────────────────────────────────────────────────────────────────

def download_gpkg(token, project_id, gpkg_file, tmp_path):
    urls = [
        f'{BASE_URL}/files/{project_id}/{gpkg_file}/',
        f'{BASE_URL}/files/{project_id}/files/{gpkg_file}/',
    ]
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=120)
        if r.status_code == 200:
            with open(tmp_path, 'wb') as f:
                f.write(r.content)
            print(f"  ✓ Descargado {gpkg_file} ({len(r.content)/1024:.1f} KB)")
            return True
        print(f"  ⚠ {r.status_code} en {url}")
    print(f"  ✗ No se pudo descargar {gpkg_file} — tabla omitida")
    return False


def read_layer(tmp_path, layer_name=None):
    """Lee capa de GeoPackage y normaliza columnas a minúsculas sin espacios extremos."""
    try:
        gdf = gpd.read_file(tmp_path, layer=layer_name) if layer_name else gpd.read_file(tmp_path)
    except Exception as e:
        print(f"  ⚠ Error leyendo capa '{layer_name}': {e}")
        if layer_name:
            try:
                print(f"  · Reintentando sin especificar capa...")
                gdf = gpd.read_file(tmp_path)
            except Exception as e2:
                print(f"  ✗ Error fatal: {e2}")
                return None
        else:
            return None

    gdf.columns = [c.strip().lower() for c in gdf.columns]

    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print(f"  Reproyectando EPSG:{gdf.crs.to_epsg()} → WGS84...")
        gdf = gdf.to_crs(epsg=4326)

    print(f"  · {len(gdf)} registros · columnas: {list(gdf.columns)}")
    return gdf


def delete_all(supabase, table):
    supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()


# ─────────────────────────────────────────────────────────────────────────────
# Fotos
# ─────────────────────────────────────────────────────────────────────────────

def build_photo_urls(token, project_id, path_raw):
    if not path_raw:
        return []
    path = str(path_raw).strip().replace('\\', '/')
    for prefix in ['../../../../', '../../../', '../../', '../']:
        if path.startswith(prefix):
            path = path[len(prefix):]
    if len(path) > 2 and path[1] == ':':
        path = path[2:].lstrip('/')
    encoded = requests.utils.quote(path, safe='/')
    if path.startswith('files/'):
        return [f'{BASE_URL}/files/{project_id}/{encoded}/']
    return [
        f'{BASE_URL}/files/{project_id}/files/{encoded}/',
        f'{BASE_URL}/files/{project_id}/{encoded}/',
    ]


def upload_photo(supabase, token, project_id, file_path, folio):
    if not file_path or str(file_path).strip() in ('', 'nan', 'None'):
        return None
    candidate_urls = build_photo_urls(token, project_id, file_path)
    content = content_type = None
    for url in candidate_urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=60)
        if r.status_code == 200:
            content = r.content
            content_type = r.headers.get('Content-Type', 'image/jpeg')
            break
    if not content:
        print(f"    ⚠ Foto no descargada: {file_path}")
        return None
    filename = str(file_path).strip().replace('\\', '/').split('/')[-1]
    storage_path = f"{folio}/{filename}"
    try:
        supabase.storage.from_('fotos-obra').upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return f"{SUPABASE_URL}/storage/v1/object/public/fotos-obra/{storage_path}"
    except Exception as e:
        print(f"    ⚠ Error subiendo foto: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 0. TABLAS LOOKUP
# ─────────────────────────────────────────────────────────────────────────────

_INFRA_NOMBRE_A_CODIGO = {
    'espacio público': 'EP',
    'espacio publico': 'EP',
    'ep':              'EP',
    'ciclorruta':      'CI',
    'cicloruta':       'CI',
    'ci':              'CI',
    'malla vial':      'MV',
    'mv':              'MV',
}


def _infra_a_codigo(valor):
    if not valor:
        return None
    key = str(valor).strip().lower()
    return _INFRA_NOMBRE_A_CODIGO.get(key, str(valor).strip())


def sync_tramos_aux_infra(supabase, token, project_id):
    print("\n── tramos_aux_infra ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'TramosIDU15562025BDTRAMOS.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    pares = {}
    for _, row in gdf.iterrows():
        nombre = safe(row.get('infraestructura'))
        if nombre:
            codigo = _infra_a_codigo(nombre)
            if codigo:
                pares[codigo] = nombre

    count = 0
    for codigo, nombre in sorted(pares.items()):
        try:
            supabase.table('tramos_aux_infra').upsert(
                {'codigo': codigo, 'nombre': nombre}, on_conflict='codigo'
            ).execute()
            count += 1
            print(f"  · {codigo} → {nombre}")
        except Exception as e:
            print(f"  ⚠ ({codigo}, {nombre}): {e}")
    print(f"  → {count} upserted")


def sync_presupuesto_aux_actividad(supabase, token, project_id):
    print("\n── presupuesto_aux_actividad ──")
    tmp = '/tmp/presupuesto_bd.gpkg'
    if not download_gpkg(token, project_id, 'PresupuestoIDU15562025BDPRESUPUESTO.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    valores = {safe(row.get('tipo_actividad')) for _, row in gdf.iterrows()} - {None}
    count = 0
    for v in sorted(valores):
        try:
            supabase.table('presupuesto_aux_actividad').upsert(
                {'tipo_actividad': v}, on_conflict='tipo_actividad'
            ).execute()
            count += 1
        except Exception as e:
            print(f"  ⚠ '{v}': {e}")
    print(f"  → {count} upserted: {sorted(valores)}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. REFERENCIA GEOGRÁFICA
# ─────────────────────────────────────────────────────────────────────────────

def sync_localidades(supabase, token, project_id):
    print("\n── localidades ──")
    if not download_gpkg(token, project_id, 'loca.gpkg', '/tmp/loca.gpkg'):
        return
    # Layer 'Loca' con columnas en PascalCase → normalizadas a minúsculas por read_layer
    # loccodigo, locnombre, locaadmini, locarea  (después de lower())
    gdf = read_layer('/tmp/loca.gpkg', 'Loca')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'loc_codigo': safe(row.get('loccodigo')  or row.get('loc_codigo')),
            'loc_nombre': safe(row.get('locnombre')  or row.get('loc_nombre')),
            'loc_admin':  safe(row.get('locaadmini') or row.get('loc_admin')),
            'loc_area':   safe_num(row.get('locarea') or row.get('loc_area')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('loc_codigo') and data.get('loc_nombre'):
            supabase.table('localidades').upsert(data, on_conflict='loc_codigo').execute()
            count += 1
    print(f"  → {count} upserted")


def sync_tramos_bd(supabase, token, project_id):
    """
    [D-08] GPKG tiene 'ciclorruta_km' (con doble r), NO 'cicloruta_km'.
    """
    print("\n── tramos_bd ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'TramosIDU15562025BDTRAMOS.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'id_tramo':          safe(row.get('id_tramo')),
            'tramo_descripcion': safe(row.get('tramo_descripcion')),
            'via_principal':     safe(row.get('via_principal')),
            'via_desde':         safe(row.get('via_desde')),
            'via_hasta':         safe(row.get('via_hasta')),
            'localidad':         safe(row.get('localidad')),
            'infraestructura':   _infra_a_codigo(row.get('infraestructura')),
            'observaciones':     safe(row.get('observaciones')),
            # [D-08] columna real: 'ciclorruta_km' (doble r)
            'cicloruta_km':      safe_num(row.get('ciclorruta_km') or row.get('cicloruta_km')),
            'esp_publico_m2':    safe_num(row.get('esp_publico_m2')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('id_tramo'):
            supabase.table('tramos_bd').upsert(data, on_conflict='id_tramo').execute()
            count += 1
    print(f"  → {count} upserted")


# ─────────────────────────────────────────────────────────────────────────────
# 2. PRESUPUESTO
# ─────────────────────────────────────────────────────────────────────────────

def sync_presupuesto_bd(supabase, token, project_id):
    print("\n── presupuesto_bd ──")
    if not download_gpkg(token, project_id, 'PresupuestoIDU15562025BDPRESUPUESTO.gpkg', '/tmp/presupuesto_bd.gpkg'):
        return
    gdf = read_layer('/tmp/presupuesto_bd.gpkg')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'tipo_actividad': safe(row.get('tipo_actividad')),
            'capitulo_num':   safe(row.get('capitulo_num')),
            'capitulo':       safe(row.get('capitulo')),
            'codigo_idu':     safe(row.get('codigo_idu')),
            'item_pago':      safe(row.get('item_pago')),
            'descripcion':    safe(row.get('descripcion')),
            'unidad':         safe(row.get('unidad')),
            'cantidad_ppto':  safe_num(row.get('cantidad_ppto')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('codigo_idu'):
            supabase.table('presupuesto_bd').upsert(data, on_conflict='codigo_idu').execute()
            count += 1
    print(f"  → {count} upserted")


def sync_presupuesto_componentes_bd(supabase, token, project_id):
    """
    [D-09] GPKG tiene TYPO 'compenente' en lugar de 'componente'.
    Se lee con OR para cubrir cuando corrijan el GPKG.
    """
    print("\n── presupuesto_componentes_bd ──")
    if not download_gpkg(token, project_id, 'Presupuesto_Componentes.gpkg', '/tmp/ppto_comp.gpkg'):
        return
    gdf = read_layer('/tmp/ppto_comp.gpkg', 'ppto_componentes')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'capitulo_num':    safe(row.get('capitulo_num')),
            'capitulo':        safe(row.get('capitulo')),
            # [D-09] typo real en GPKG: 'compenente'; OR para versión corregida futura
            'componente':      safe(row.get('compenente') or row.get('componente')),
            'tipo_actividad':  safe(row.get('tipo_actividad')),
            'codigo_idu':      safe(row.get('codigo_idu')),
            'descripcion':     safe(row.get('descripcion')),
            'unidad':          safe(row.get('unidad')),
            'cantidad_ppto':   safe_num(row.get('cantidad_ppto')),
            'precio_unitario': safe_num(row.get('precio_unitario')),
            'item_pago':       safe(row.get('item_pago')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('codigo_idu'):
            supabase.table('presupuesto_componentes_bd').upsert(data, on_conflict='codigo_idu').execute()
            count += 1
    print(f"  → {count} upserted")


# ─────────────────────────────────────────────────────────────────────────────
# 3. FORMULARIOS PRINCIPALES
# ─────────────────────────────────────────────────────────────────────────────

def sync_registros_cantidades(supabase, token, project_id):
    """
    [D-01] Columnas corregidas:
      · foto_1…foto_5 NO existen en el GPKG → se eliminan del mapeo
        (las fotos de cantidades van en RF_Cantidades.gpkg)
      · documento_adj sí existe → se sube como foto
      · fecha_inicio / fecha_fin no existen → se mapea 'fecha' a fecha_inicio
      · codigo_interventor (GPKG) → codigointerventor (Supabase)
      · acompañamiento_interventor (GPKG, con guión bajo) → acompañamientointerventor (Supabase)
    [BUG-PY-001] 'estado' eliminado del dict para no sobreescribir registros aprobados
    """
    print("\n── registros_cantidades ──")
    if not download_gpkg(token, project_id, 'Formulario_Cantidades.gpkg', '/tmp/cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/cantidades.gpkg', 'Formulario_Cantidades_V2')
    if gdf is None or gdf.empty:
        return

    nuevos = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        # Solo documento_adj existe como adjunto en cantidades
        doc_url = None
        doc_path = safe(row.get('documento_adj'))
        if doc_path:
            doc_url = upload_photo(supabase, token, project_id, doc_path, folio)

        data = {
            'folio':                     str(folio),
            'id_unico':                  safe(row.get('id_unico')),
            'contrato_id':               CONTRATO_ID,
            'usuario_qfield':            safe(row.get('usuario')),
            'tipo_infra':                safe(row.get('tipo_infra')),
            'id_tramo':                  safe(row.get('id_tramo')),
            'tramo_descripcion':         safe(row.get('tramo_descripcion')),
            'civ':                       safe(row.get('civ')),
            'codigo_elemento':           safe(row.get('codigo_elemento')),
            'latitud':                   lat,
            'longitud':                  lon,
            # [D-01] 'fecha' → fecha_inicio; fecha_fin no existe en GPKG
            'fecha_inicio':              safe(row.get('fecha_inicio') or row.get('fecha')),
            'fecha_fin':                 safe(row.get('fecha_fin')),
            'tipo_actividad':            safe(row.get('tipo_actividad')),
            'capitulo_num':              safe(row.get('capitulo_num')),
            'capitulo':                  safe(row.get('capitulo')),
            'item_pago':                 safe(row.get('item_pago')),
            'item_descripcion':          safe(row.get('item_descripcion')),
            'unidad':                    safe(row.get('unidad')),
            'cantidad':                  safe_num(row.get('cantidad')),
            'descripcion':               safe(row.get('descripcion')),
            # [D-01] foto_1…foto_5 no existen; solo documento_adj
            'documento_adj_path':        doc_path,
            'documento_adj_url':         doc_url,
            'observaciones':             safe(row.get('observaciones')),
            # [D-01] columna real: 'codigo_interventor' → campo DB: 'codigointerventor'
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            # [D-01] columna real: 'acompañamiento_interventor' (guión bajo)
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor')
                                             or row.get('acompañamiento interventor')),
            # [BUG-PY-001] sin 'estado': DEFAULT 'BORRADOR' aplica solo en INSERT
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            supabase.table('registros_cantidades').upsert(data, on_conflict='folio').execute()
            nuevos += 1
            print(f"  ✓ {folio}")
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {nuevos} upserted · {omitidos} sin folio · {errores} errores")


def sync_registros_componentes(supabase, token, project_id):
    """
    [D-02] Layer real: 'PMT - Plan de Manejo del Transito'
      El script NO especifica layer_name → geopandas toma la primera capa.
      Columnas de interventor corregidas igual que D-01.
    """
    print("\n── registros_componentes ──")
    if not download_gpkg(token, project_id, 'Reporte_Componentes.gpkg', '/tmp/componentes.gpkg'):
        return
    # No se especifica layer_name: gpd lee la primera capa disponible
    gdf = read_layer('/tmp/componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'folio':                     str(folio),
            'id_unico':                  safe(row.get('id_unico')),
            'contrato_id':               CONTRATO_ID,
            'usuario_qfield':            safe(row.get('usuario')),
            'id_tramo':                  safe(row.get('id_tramo')),
            'tramo':                     safe(row.get('tramo')),
            'civ':                       safe(row.get('civ')),
            'codigo_elemento':           safe(row.get('codigo_elemento')),
            'tipo_infra':                safe(row.get('tipo_infra')),
            'componente':                safe(row.get('componente')),
            'latitud':                   lat,
            'longitud':                  lon,
            'fecha':                     safe(row.get('fecha')),
            'fecha_reporte':             safe(row.get('fecha_reporte')),
            'tipo_actividad':            safe(row.get('tipo_actividad')),
            'capitulo_num':              safe(row.get('capitulo_num')),
            'capitulo':                  safe(row.get('capitulo')),
            'item_pago':                 safe(row.get('item_pago')),
            'item_descripcion':          safe(row.get('item_descripcion')),
            'cantidad':                  safe_num(row.get('cantidad')),
            'unidad':                    safe(row.get('unidad')),
            'precio_unitario':           safe_num(row.get('precio_unitario')),
            'observaciones':             safe(row.get('observaciones')),
            'profesional':               safe(row.get('profesional')),
            # [D-02] columna real: 'codigo_interventor'
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            # [D-02] columna real: 'acompañamiento_interventor' (guión bajo)
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor')
                                             or row.get('acompañamiento interventor')),
            # [BUG-PY-001] sin 'estado'
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            supabase.table('registros_componentes').upsert(data, on_conflict='folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


def sync_registros_reporte_diario(supabase, token, project_id):
    """
    [D-03] TYPO en GPKG: 'feca_reporte' en lugar de 'fecha_reporte'.
      Se lee con OR para cubrir cuando lo corrijan en QField.
    """
    print("\n── registros_reporte_diario ──")
    if not download_gpkg(token, project_id, 'Reporte_Diario.gpkg', '/tmp/reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/reporte_diario.gpkg', 'Reporte_Diario')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'folio':          str(folio),
            'id_unico':       safe(row.get('id_unico')),
            'contrato_id':    CONTRATO_ID,
            'usuario_qfield': safe(row.get('usuario')),
            'latitud':        lat,
            'longitud':       lon,
            'fecha':          safe(row.get('fecha')),
            # [D-03] typo real en GPKG: 'feca_reporte'; OR cubre corrección futura
            'fecha_reporte':  safe(row.get('feca_reporte') or row.get('fecha_reporte')),
            'observaciones':  safe(row.get('observaciones')),
            # [BUG-PY-001] sin 'estado'
            'qfield_sync_id': safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            supabase.table('registros_reporte_diario').upsert(data, on_conflict='folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


def sync_formulario_pmt(supabase, token, project_id):
    print("\n── formulario_pmt ──")
    if not download_gpkg(token, project_id, 'Formulario_PMT.gpkg', '/tmp/pmt.gpkg'):
        return
    # Layer real: 'formulario_pmt' — read_layer sin layer_name lo toma automáticamente
    gdf = read_layer('/tmp/pmt.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'folio':           str(folio),
            'contrato_id':     CONTRATO_ID,
            'descripcion':     safe(row.get('descripcion')),
            'civ':             safe(row.get('civ')),
            'inicio_vigencia': safe(row.get('inicio_vigencia')),
            'fin_vigencia':    safe(row.get('fin_vigencia')),
            'usuario':         safe(row.get('usuario')),
            'latitud':         lat,
            'longitud':        lon,
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            supabase.table('formulario_pmt').upsert(data, on_conflict='folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


# ─────────────────────────────────────────────────────────────────────────────
# 4. TABLAS SECUNDARIAS (bd_*)
# ─────────────────────────────────────────────────────────────────────────────

def sync_bd_personal(supabase, token, project_id):
    """
    [D-04] Corregido: Mantiene estructura constante para evitar PGRST102.
    """
    print("\n── bd_personal_obra ──")
    if not download_gpkg(token, project_id, 'BD_PersonalObra.gpkg', '/tmp/personal.gpkg'):
        return
    gdf = read_layer('/tmp/personal.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_personal_obra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        # Se definen todas las llaves explícitamente
        data = {
            'folio':              safe(row.get('folio')),
            'inspectores':        safe_num(row.get('inspectores')),
            'personal_operativo': safe_num(row.get('personal_operativo') or row.get('personaloperativo')),
            'personal_boal':      safe_num(row.get('perosnal_boal') or row.get('personal_boal')),
            'personal_transito':  safe_num(row.get('personal_transito') or row.get('personaltransito')),
            'longitud':           lon,
            'latitud':            lat,
        }
        # Solo filtramos el registro completo si no tiene folio
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_personal_obra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_climatica(supabase, token, project_id):
    """
    [D-05] Corregido: Mantiene estructura constante para evitar PGRST102.
    """
    print("\n── bd_condicion_climatica ──")
    if not download_gpkg(token, project_id, 'BD_CondicionClimatica.gpkg', '/tmp/climatica.gpkg'):
        return
    gdf = read_layer('/tmp/climatica.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_condicion_climatica')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'folio':         safe(row.get('folio')),
            'estado_clima':  safe(row.get('estado_clima') or row.get('estadoclima')),
            'hora':          safe(row.get('hora')),
            'observaciones': safe(row.get('observaciones')),
            'longitud':      lon,
            'latitud':       lat,
        }
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_condicion_climatica').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_maquinaria(supabase, token, project_id):
    """
    [D-06] Corregido: Mantiene estructura constante para evitar PGRST102.
    """
    print("\n── bd_maquinaria_obra ──")
    if not download_gpkg(token, project_id, 'BD_MaquinariaObra.gpkg', '/tmp/maquinaria.gpkg'):
        return
    gdf = read_layer('/tmp/maquinaria.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_maquinaria_obra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'folio':                 safe(row.get('folio')),
            'operarios':             safe_num(row.get('operarios')),
            'volquetas':             safe_num(row.get('volquetas')),
            'vibrocompactador':      safe_num(row.get('vibrocompactador')),
            'equipos_especiales':    safe_num(row.get('equipos_especiales') or row.get('equiposespeciales')),
            'minicargador':          safe_num(row.get('minicargador_(con_aditamento_martillo)') or row.get('minicargador')),
            'ruteadora':             safe_num(row.get('ruteadora_(rortadora_de_pavimento)') or row.get('ruteadora')),
            'compresor':             safe_num(row.get('compresor_de_aire') or row.get('compresor')),
            'retrocargador':         safe_num(row.get('retrocargador_(con_aditamento_martillo)') or row.get('retrocargador')),
            'extendedora_asfalto':   safe_num(row.get('extendedora_de_asfalto_(finisher)') or row.get('extendedora_asfalto')),
            'compactador_neumatico': safe_num(row.get('compactador_neumatico') or row.get('compactadorneumatico')),
            'observaciones':         safe(row.get('observaciones')),
            'longitud':              lon,
            'latitud':               lat,
        }
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_maquinaria_obra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_sst(supabase, token, project_id):
    """
    [D-07] Corregido: Mantiene estructura constante para evitar PGRST102.
    """
    print("\n── bd_sst_ambiental ──")
    if not download_gpkg(token, project_id, 'BD_SST-Ambiental.gpkg', '/tmp/sst.gpkg'):
        return
    gdf = read_layer('/tmp/sst.gpkg', 'BBD_SST-Ambiental')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_sst_ambiental')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'folio':              safe(row.get('folio')),
            'observaciones':      safe(row.get('observaciones')),
            'longitud':           lon,
            'latitud':            lat,
            'botiquin':           safe_num(row.get('botiquin')),
            'kit_antiderrames':   safe_num(row.get('kit_antiderrames') or row.get('kitantiderrames')),
            'punto_hidratacion':  safe_num(row.get('punto_de_hidratacion') or row.get('punto_hidratacion')),
            'punto_ecologico':    safe_num(row.get('punto_ecologico')),
            'extintor':           safe_num(row.get('extintor')),
        }
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_sst_ambiental').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


# ─────────────────────────────────────────────────────────────────────────────
# 5. REGISTROS FOTOGRÁFICOS (rf_*)
# ─────────────────────────────────────────────────────────────────────────────

def sync_rf_cantidades(supabase, token, project_id):
    print("\n── rf_cantidades ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_cantidades')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'folio':             safe(row.get('folio')),
            'id_unico':          safe(row.get('id_unico')),
            'observacion':       safe(row.get('observacion')),
            'nombre_foto':       safe(row.get('nombre_foto')),
            'ruta_destino_foto': safe(row.get('ruta_destino_foto')),
        }
        # IMPORTANTE: No filtramos llaves individuales, solo el registro si falta id_unico
        if data.get('id_unico'):
            rows.append(data)

    if rows:
        supabase.table('rf_cantidades').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_componentes(supabase, token, project_id):
    print("\n── rf_componentes ──")
    if not download_gpkg(token, project_id, 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg'):
        return
    gdf = read_layer('/tmp/rf_componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_componentes')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'folio':         safe(row.get('folio')),
            'id_unico':      safe(row.get('id_unico')),
            'observaciones': safe(row.get('observaciones')),
            'foto':          safe(row.get('foto')),
        }
        if data.get('id_unico'):
            rows.append(data)

    if rows:
        supabase.table('rf_componentes').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_reporte_diario(supabase, token, project_id):
    print("\n── rf_reporte_diario ──")
    if not download_gpkg(token, project_id, 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/rf_reporte_diario.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_reporte_diario')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'folio':         safe(row.get('folio')),
            'id_unico':      safe(row.get('id_unico')),
            'observaciones': safe(row.get('observaciones')),
            'foto':          safe(row.get('foto')),
        }
        if data.get('id_unico'):
            rows.append(data)

    if rows:
        supabase.table('rf_reporte_diario').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"SYNC BDO IDU-1556-2025 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    token      = qfield_login()
    supabase   = get_supabase()
    project_id = get_project_id(token)

    sync_tramos_aux_infra(supabase, token, project_id)
    sync_presupuesto_aux_actividad(supabase, token, project_id)
    sync_localidades(supabase, token, project_id)
    sync_tramos_bd(supabase, token, project_id)
    sync_presupuesto_bd(supabase, token, project_id)
    sync_presupuesto_componentes_bd(supabase, token, project_id)
    sync_registros_cantidades(supabase, token, project_id)
    sync_registros_componentes(supabase, token, project_id)
    sync_registros_reporte_diario(supabase, token, project_id)
    sync_formulario_pmt(supabase, token, project_id)
    sync_bd_personal(supabase, token, project_id)
    sync_bd_climatica(supabase, token, project_id)
    sync_bd_maquinaria(supabase, token, project_id)
    sync_bd_sst(supabase, token, project_id)
    sync_rf_cantidades(supabase, token, project_id)
    sync_rf_componentes(supabase, token, project_id)
    sync_rf_reporte_diario(supabase, token, project_id)

    print(f"\n{'='*60}")
    print(f"✓ Sincronización completa")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
