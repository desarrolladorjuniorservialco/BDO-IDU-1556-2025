"""
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
Alimenta todas las tablas definidas en 001_TABLAS.sql
desde los GeoPackages actualizados en QField Cloud.

Orden de ejecución (respeta FKs):
  0. Tablas lookup                  : tramos_aux_infra, presupuesto_aux_actividad
  1. Referencia geográfica          : localidades, tramos_bd
  2. Presupuesto                    : presupuesto_bd, presupuesto_componentes_bd
  3. Formularios principales        : registros_cantidades, registros_componentes,
                                      registros_reporteDiario, formulario_pmt
  4. Tablas secundarias BD_         : BD_PersonalObra, BD_CondicionClimatica,
                                      BD_MaquinariaObra, BD_SST_Ambiental
  5. Registros fotográficos         : RF_Cantidades, RF_Componentes, RF_ReporteDiario
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
    """Extrae (lat, lon) desde la geometría de una fila GeoDataFrame."""
    lat = lon = None
    geom = row.get('geometry')
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
    """Descarga un GeoPackage desde QFieldCloud. Retorna True si tuvo éxito."""
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
    """Lee una capa de un GeoPackage, normaliza columnas a minúsculas y reproyecta a WGS84."""
    try:
        gdf = gpd.read_file(tmp_path, layer=layer_name) if layer_name else gpd.read_file(tmp_path)
    except Exception as e:
        print(f"  ⚠ Error leyendo capa '{layer_name}': {e}")
        if layer_name:
            try:
                gdf = gpd.read_file(tmp_path)
            except Exception as e2:
                print(f"  ✗ Error fatal: {e2}")
                return None
        else:
            return None

    # Normalizar: minúsculas + sin espacios extremos
    # Garantiza compatibilidad sin importar el case del GPKG (ID_TRAMO, id_tramo, Id_Tramo…)
    gdf.columns = [c.strip().lower() for c in gdf.columns]

    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print(f"  Reproyectando EPSG:{gdf.crs.to_epsg()} → WGS84...")
        gdf = gdf.to_crs(epsg=4326)

    print(f"  · {len(gdf)} registros · columnas: {list(gdf.columns)}")
    return gdf


def delete_all(supabase, table):
    """Elimina todos los registros de una tabla sin clave única (truncate lógico)."""
    supabase.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()


# ─────────────────────────────────────────────────────────────────────────────
# Fotos (exclusivo de registros_cantidades)
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
# 0. TABLAS LOOKUP (deben poblarse ANTES que cualquier tabla con FK)
# ─────────────────────────────────────────────────────────────────────────────

# Mapeo nombre largo → código PK de tramos_aux_infra
# DDL: codigo TEXT PRIMARY KEY (EP/CI/MV), nombre TEXT NOT NULL
# La FK tramos_bd.infraestructura → tramos_aux_infra(codigo)
# El GPKG de tramos almacena el nombre largo ("Espacio Público"), no el código.
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
    """Convierte el nombre largo del GPKG al código PK de tramos_aux_infra."""
    if not valor:
        return None
    key = str(valor).strip().lower()
    # Si ya es un código conocido o desconocido, lo devuelve normalizado
    return _INFRA_NOMBRE_A_CODIGO.get(key, str(valor).strip())


def sync_tramos_aux_infra(supabase, token, project_id):
    """
    Asegura que tramos_aux_infra tenga todos los valores de infraestructura
    presentes en el GPKG de tramos.
    DDL: codigo TEXT PRIMARY KEY, nombre TEXT NOT NULL
    Los tres registros base (EP/CI/MV) ya los inserta el DDL con ON CONFLICT DO UPDATE;
    esta función agrega cualquier valor nuevo que aparezca en campo.
    """
    print("\n── tramos_aux_infra (TramosIDU15562025BDTRAMOS.gpkg → codigos) ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'TramosIDU15562025BDTRAMOS.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    # Recoger pares únicos {codigo: nombre} desde el GPKG
    pares = {}
    for _, row in gdf.iterrows():
        nombre = safe(row.get('infraestructura'))
        if nombre:
            codigo = _infra_a_codigo(nombre)
            if codigo:
                pares[codigo] = nombre   # último nombre visto para ese código

    count = 0
    for codigo, nombre in sorted(pares.items()):
        try:
            supabase.table('tramos_aux_infra').upsert(
                {'codigo': codigo, 'nombre': nombre},
                on_conflict='codigo'
            ).execute()
            count += 1
            print(f"  · {codigo} → {nombre}")
        except Exception as e:
            print(f"  ⚠ No se pudo insertar ({codigo}, {nombre}): {e}")

    print(f"  → {count} upserted")


def sync_presupuesto_aux_actividad(supabase, token, project_id):
    """
    Pre-pobla presupuesto_aux_actividad con los valores únicos de tipo_actividad
    presentes en el GPKG de presupuesto.
    DDL: tipo_actividad TEXT PRIMARY KEY
    FK consumidores: presupuesto_bd, registros_cantidades, registros_componentes
    """
    print("\n── presupuesto_aux_actividad (PresupuestoIDU15562025BDPRESUPUESTO.gpkg) ──")
    tmp = '/tmp/presupuesto_bd.gpkg'
    if not download_gpkg(token, project_id, 'PresupuestoIDU15562025BDPRESUPUESTO.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    valores = set()
    for _, row in gdf.iterrows():
        v = safe(row.get('tipo_actividad'))
        if v:
            valores.add(v)

    count = 0
    for v in sorted(valores):
        try:
            supabase.table('presupuesto_aux_actividad').upsert(
                {'tipo_actividad': v}, on_conflict='tipo_actividad'
            ).execute()
            count += 1
        except Exception as e:
            print(f"  ⚠ No se pudo insertar '{v}': {e}")
    print(f"  → {count} upserted: {sorted(valores)}")


# ─────────────────────────────────────────────────────────────────────────────
# 1. TABLAS DE REFERENCIA GEOGRÁFICA
# ─────────────────────────────────────────────────────────────────────────────

def sync_localidades(supabase, token, project_id):
    print("\n── localidades (loca.gpkg · Loca) ──")
    if not download_gpkg(token, project_id, 'loca.gpkg', '/tmp/loca.gpkg'):
        return
    gdf = read_layer('/tmp/loca.gpkg', 'Loca')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        # Columnas normalizadas a minúsculas: loccodigo, locnombre, locaadmini, locarea
        data = {
            'loc_codigo': safe(row.get('loc_codigo') or row.get('loccodigo') or row.get('field1')),
            'loc_nombre': safe(row.get('loc_nombre') or row.get('locnombre') or row.get('field2')),
            'loc_admin':  safe(row.get('loc_admin')  or row.get('locaadmini')),
            'loc_area':   safe_num(row.get('loc_area') or row.get('locarea')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('loc_codigo') and data.get('loc_nombre'):
            supabase.table('localidades').upsert(data, on_conflict='loc_codigo').execute()
            count += 1
    print(f"  → {count} upserted")


def sync_tramos_bd(supabase, token, project_id):
    """
    Sincroniza tramos_bd.
    infraestructura almacena el CÓDIGO (EP/CI/MV) — no el nombre largo —
    porque la FK apunta a tramos_aux_infra(codigo).
    _infra_a_codigo() convierte 'Espacio Público' → 'EP', etc.
    """
    print("\n── tramos_bd (TramosIDU15562025BDTRAMOS.gpkg) ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'TramosIDU15562025BDTRAMOS.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    count = 0
    for _, row in gdf.iterrows():
        data = {
            'id_tramo':          safe(row.get('id_tramo')          or row.get('field1')),
            'tramo_descripcion': safe(row.get('tramo_descripcion') or row.get('field2')),
            'via_principal':     safe(row.get('via_principal')),
            'via_desde':         safe(row.get('via_desde')),
            'via_hasta':         safe(row.get('via_hasta')),
            'localidad':         safe(row.get('localidad')),
            # Convertir nombre largo → código FK válido (EP/CI/MV)
            'infraestructura':   _infra_a_codigo(row.get('infraestructura')),
            'observaciones':     safe(row.get('observaciones')),
            'cicloruta_km':      safe_num(row.get('cicloruta_km')),
            'esp_publico_m2':    safe_num(row.get('esp_publico_m2')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('id_tramo'):
            supabase.table('tramos_bd').upsert(data, on_conflict='id_tramo').execute()
            count += 1
    print(f"  → {count} upserted")


# ─────────────────────────────────────────────────────────────────────────────
# 2. TABLAS DE PRESUPUESTO
# ─────────────────────────────────────────────────────────────────────────────

def sync_presupuesto_bd(supabase, token, project_id):
    print("\n── presupuesto_bd (PresupuestoIDU15562025BDPRESUPUESTO.gpkg) ──")
    # El GPKG ya fue descargado por sync_presupuesto_aux_actividad; se reutiliza.
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
            'codigo_idu':     safe(row.get('codigo_idu') or row.get('field1')),
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
    print("\n── presupuesto_componentes_bd (Presupuesto_Componentes.gpkg · ppto_componentes) ──")
    if not download_gpkg(token, project_id, 'Presupuesto_Componentes.gpkg', '/tmp/ppto_comp.gpkg'):
        return
    gdf = read_layer('/tmp/ppto_comp.gpkg', 'ppto_componentes')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        # 'Precio Unitario' en el GPKG → normalizado como 'precio unitario' (con espacio)
        data = {
            'capitulo_num':    safe(row.get('capitulo_num')   or row.get('capitulo')),
            'capitulo':        safe(row.get('capitulo')),
            'componente':      safe(row.get('componente')     or row.get('field2')),
            'tipo_actividad':  safe(row.get('tipo_actividad') or row.get('field3')),
            'codigo_idu':      safe(row.get('codigo_idu')     or row.get('field1')),
            'descripcion':     safe(row.get('descripcion')),
            'unidad':          safe(row.get('unidad')),
            'cantidad_ppto':   safe_num(row.get('cantidad_ppto')),
            'precio_unitario': safe_num(row.get('precio_unitario') or row.get('precio unitario')),
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
    Formulario_Cantidades.gpkg · Formulario_Cantidades_V2
    → registros_cantidades   (conflict: folio)
    Incluye subida de fotos al bucket fotos-obra.
    """
    print("\n── registros_cantidades (Formulario_Cantidades.gpkg · Formulario_Cantidades_V2) ──")
    if not download_gpkg(token, project_id, 'Formulario_Cantidades.gpkg', '/tmp/cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/cantidades.gpkg', 'Formulario_Cantidades_V2')
    if gdf is None or gdf.empty:
        return

    nuevos = omitidos = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        foto_urls = {}
        for campo in ['foto_1', 'foto_2', 'foto_3', 'foto_4', 'foto_5', 'documento_adj']:
            path = safe(row.get(campo))
            if path:
                foto_urls[campo] = upload_photo(supabase, token, project_id, path, folio)

        data = {
            'folio':              str(folio),
            'ID_Unico':           safe(row.get('id_unico')),
            'contrato_id':        CONTRATO_ID,
            'usuario_qfield':     safe(row.get('usuario')),
            'tipo_infra':         safe(row.get('tipo_infra')),
            'id_tramo':           safe(row.get('id_tramo')),
            'tramo_descripcion':  safe(row.get('tramo_descripcion')),
            'civ':                safe(row.get('civ')),
            'codigo_elemento':    safe(row.get('codigo_elemento')),
            'latitud':            lat,
            'longitud':           lon,
            'fecha_inicio':       safe(row.get('fecha_inicio')),
            'fecha_fin':          safe(row.get('fecha_fin')),
            'tipo_actividad':     safe(row.get('tipo_actividad')),
            'capitulo_num':       safe(row.get('capitulo_num')),
            'capitulo':           safe(row.get('capitulo')),
            'item_pago':          safe(row.get('item_pago')),
            'item_descripcion':   safe(row.get('item_descripcion')),
            'unidad':             safe(row.get('unidad')),
            'cantidad':           safe_num(row.get('cantidad')),
            'descripcion':        safe(row.get('descripcion')),
            'foto_1_path':        safe(row.get('foto_1')),
            'foto_1_url':         foto_urls.get('foto_1'),
            'foto_2_path':        safe(row.get('foto_2')),
            'foto_2_url':         foto_urls.get('foto_2'),
            'foto_3_path':        safe(row.get('foto_3')),
            'foto_3_url':         foto_urls.get('foto_3'),
            'foto_4_path':        safe(row.get('foto_4')),
            'foto_4_url':         foto_urls.get('foto_4'),
            'foto_5_path':        safe(row.get('foto_5')),
            'foto_5_url':         foto_urls.get('foto_5'),
            'documento_adj_path': safe(row.get('documento_adj')),
            'documento_adj_url':  foto_urls.get('documento_adj'),
            'observaciones':      safe(row.get('observaciones')),
            'CodigoInterventor':  safe(row.get('codigointerventor')),
            # En el GPKG normalizado a minúsculas: 'acompañamiento interventor' (con espacio)
            'AcompañamientoInterventor': safe(row.get('acompañamiento interventor')),
            'estado':             'BORRADOR',
            'qfield_sync_id':     safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        supabase.table('registros_cantidades').upsert(data, on_conflict='folio').execute()
        nuevos += 1
        print(f"  ✓ {folio}")

    print(f"  → {nuevos} upserted · {omitidos} sin folio")


def sync_registros_componentes(supabase, token, project_id):
    """
    Reporte_Componentes.gpkg
    → registros_componentes   (conflict: Folio)
    """
    print("\n── registros_componentes (Reporte_Componentes.gpkg) ──")
    if not download_gpkg(token, project_id, 'Reporte_Componentes.gpkg', '/tmp/componentes.gpkg'):
        return
    gdf = read_layer('/tmp/componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':              str(folio),
            'ID_Unico':           safe(row.get('id_unico')),
            'contrato_id':        CONTRATO_ID,
            'usuario_qfield':     safe(row.get('usuario')),
            'id_tramo':           safe(row.get('id_tramo')),
            'Tramo':              safe(row.get('tramo')),
            'CIV':                safe(row.get('civ')),
            'codigo_elemento':    safe(row.get('codigo_elemento')),
            'tipo_infra':         safe(row.get('tipo_infra')),
            'Componente':         safe(row.get('componente')),
            'latitud':            lat,
            'longitud':           lon,
            'Fecha':              safe(row.get('fecha')),
            'Fecha_Reporte':      safe(row.get('fecha_reporte')),
            'tipo_actividad':     safe(row.get('tipo_actividad')),
            'capitulo_num':       safe(row.get('capitulo_num')),
            'capitulo':           safe(row.get('capitulo')),
            'item_pago':          safe(row.get('item_pago')),
            'item_descripcion':   safe(row.get('item_descripcion')),
            'cantidad':           safe_num(row.get('cantidad')),
            'unidad':             safe(row.get('unidad')),
            'precio_unitario':    safe_num(row.get('precio_unitario')),
            'Observaciones':      safe(row.get('observaciones')),
            'Profesional':        safe(row.get('profesional')),
            'CodigoInterventor':  safe(row.get('codigointerventor')),
            'AcompañamientoInterventor': safe(row.get('acompañamiento interventor')),
            'estado':             'BORRADOR',
            'qfield_sync_id':     safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        supabase.table('registros_componentes').upsert(data, on_conflict='Folio').execute()
        count += 1

    print(f"  → {count} upserted · {omitidos} sin folio")


def sync_registros_reporte_diario(supabase, token, project_id):
    """
    Reporte_Diario.gpkg · Reporte_Diario
    → registros_reporteDiario   (conflict: Folio)
    """
    print("\n── registros_reporteDiario (Reporte_Diario.gpkg · Reporte_Diario) ──")
    if not download_gpkg(token, project_id, 'Reporte_Diario.gpkg', '/tmp/reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/reporte_diario.gpkg', 'Reporte_Diario')
    if gdf is None or gdf.empty:
        return

    count = omitidos = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':          str(folio),
            'ID_Unico':       safe(row.get('id_unico')),
            'contrato_id':    CONTRATO_ID,
            'usuario_qfield': safe(row.get('usuario')),
            'latitud':        lat,
            'longitud':       lon,
            'Fecha':          safe(row.get('fecha')),
            'Fecha_Reporte':  safe(row.get('fecha_reporte')),
            'Observaciones':  safe(row.get('observaciones')),
            'estado':         'BORRADOR',
            'qfield_sync_id': safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        supabase.table('registros_reporteDiario').upsert(data, on_conflict='Folio').execute()
        count += 1

    print(f"  → {count} upserted · {omitidos} sin folio")


def sync_formulario_pmt(supabase, token, project_id):
    """
    Formulario_PMT.gpkg
    → formulario_pmt   (conflict: Folio)
    """
    print("\n── formulario_pmt (Formulario_PMT.gpkg) ──")
    if not download_gpkg(token, project_id, 'Formulario_PMT.gpkg', '/tmp/pmt.gpkg'):
        return
    gdf = read_layer('/tmp/pmt.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':           str(folio),
            'contrato_id':     CONTRATO_ID,
            'descripcion':     safe(row.get('descripcion')),
            'CIV':             safe(row.get('civ')),
            'inicio_vigencia': safe(row.get('inicio_vigencia')),
            'fin_vigencia':    safe(row.get('fin_vigencia')),
            'usuario':         safe(row.get('usuario')),
            'latitud':         lat,
            'longitud':        lon,
        }
        data = {k: v for k, v in data.items() if v is not None}
        supabase.table('formulario_pmt').upsert(data, on_conflict='Folio').execute()
        count += 1

    print(f"  → {count} upserted · {omitidos} sin folio")


# ─────────────────────────────────────────────────────────────────────────────
# 4. TABLAS SECUNDARIAS DEL REPORTE DIARIO (BD_*)
#    Sin clave única → truncar y recargar en cada ejecución.
#    FK: Folio → registros_reporteDiario.Folio
# ─────────────────────────────────────────────────────────────────────────────

def sync_bd_personal(supabase, token, project_id):
    print("\n── BD_PersonalObra (BD_PersonalObra.gpkg) ──")
    if not download_gpkg(token, project_id, 'BD_PersonalObra.gpkg', '/tmp/personal.gpkg'):
        return
    gdf = read_layer('/tmp/personal.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'BD_PersonalObra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'Folio':             safe(row.get('folio')),
            'Inspectores':       safe_num(row.get('inspectores')),
            'PersonalOperativo': safe_num(row.get('personaloperativo')),
            'PersonalBOAL':      safe_num(row.get('personalboal')),
            'PersonalTransito':  safe_num(row.get('personaltransito')),
            'Longitud':          lon,
            'Latitud':           lat,
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('Folio'):
            rows.append(data)

    if rows:
        supabase.table('BD_PersonalObra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_climatica(supabase, token, project_id):
    print("\n── BD_CondicionClimatica (BD_CondicionClimatica.gpkg) ──")
    if not download_gpkg(token, project_id, 'BD_CondicionClimatica.gpkg', '/tmp/climatica.gpkg'):
        return
    gdf = read_layer('/tmp/climatica.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'BD_CondicionClimatica')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'Folio':         safe(row.get('folio')),
            'EstadoClima':   safe(row.get('estadoclima')),
            'Hora':          safe(row.get('hora')),
            'Observaciones': safe(row.get('observaciones')),
            'Longitud':      lon,
            'Latitud':       lat,
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('Folio'):
            rows.append(data)

    if rows:
        supabase.table('BD_CondicionClimatica').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_maquinaria(supabase, token, project_id):
    print("\n── BD_MaquinariaObra (BD_MaquinariaObra.gpkg) ──")
    if not download_gpkg(token, project_id, 'BD_MaquinariaObra.gpkg', '/tmp/maquinaria.gpkg'):
        return
    gdf = read_layer('/tmp/maquinaria.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'BD_MaquinariaObra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'Folio':                safe(row.get('folio')),
            'Operarios':            safe_num(row.get('operarios')),
            'Volquetas':            safe_num(row.get('volquetas')),
            'Vibrocompactador':     safe_num(row.get('vibrocompactador')),
            'EquiposEspeciales':    safe_num(row.get('equiposespeciales')),
            'Minicargador':         safe_num(row.get('minicargador')),
            'Ruteadora':            safe_num(row.get('ruteadora')),
            'Compresor':            safe_num(row.get('compresor')),
            'Retrocargador':        safe_num(row.get('retrocargador')),
            'ExtendedoraAsfalto':   safe_num(row.get('extendedoraasfalto')),
            'CompactadorNeumatico': safe_num(row.get('compactadorneumatico')),
            'Observaciones':        safe(row.get('observaciones')),
            'Longitud':             lon,
            'Latitud':              lat,
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('Folio'):
            rows.append(data)

    if rows:
        supabase.table('BD_MaquinariaObra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_sst(supabase, token, project_id):
    print("\n── BD_SST_Ambiental (BD_SST-Ambiental.gpkg · BBD_SST-Ambiental) ──")
    if not download_gpkg(token, project_id, 'BD_SST-Ambiental.gpkg', '/tmp/sst.gpkg'):
        return
    gdf = read_layer('/tmp/sst.gpkg', 'BBD_SST-Ambiental')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'BD_SST_Ambiental')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'Folio':            safe(row.get('folio')),
            'Observaciones':    safe(row.get('observaciones')),
            'Longitud':         lon,
            'Latitud':          lat,
            'Botiquin':         safe_num(row.get('botiquin')),
            'KitAntiderrames':  safe_num(row.get('kitantiderrames')),
            'PuntoHidratacion': safe_num(row.get('puntohidratacion')),
            'PuntoEcologico':   safe_num(row.get('puntoecologico')),
            'Extintor':         safe_num(row.get('extintor')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('Folio'):
            rows.append(data)

    if rows:
        supabase.table('BD_SST_Ambiental').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


# ─────────────────────────────────────────────────────────────────────────────
# 5. REGISTROS FOTOGRÁFICOS (RF_*)
#    Sin clave única → truncar y recargar.
#    FK: ID_Unico → [formulario].ID_Unico
# ─────────────────────────────────────────────────────────────────────────────

def sync_rf_cantidades(supabase, token, project_id):
    print("\n── RF_Cantidades (RF_Cantidades.gpkg) ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'RF_Cantidades')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'Folio':             safe(row.get('folio')),
            'ID_Unico':          safe(row.get('id_unico')),
            'Observacion':       safe(row.get('observacion')),
            'Nombre_Foto':       safe(row.get('nombre_foto')),
            'Ruta_Destino_Foto': safe(row.get('ruta_destino_foto')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('ID_Unico'):
            rows.append(data)

    if rows:
        supabase.table('RF_Cantidades').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_componentes(supabase, token, project_id):
    print("\n── RF_Componentes (RF_Componentes.gpkg) ──")
    if not download_gpkg(token, project_id, 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg'):
        return
    gdf = read_layer('/tmp/rf_componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'RF_Componentes')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'Folio':         safe(row.get('folio')),
            'ID_Unico':      safe(row.get('id_unico')),
            'Observaciones': safe(row.get('observaciones')),
            'Foto':          safe(row.get('foto')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('ID_Unico'):
            rows.append(data)

    if rows:
        supabase.table('RF_Componentes').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_reporte_diario(supabase, token, project_id):
    print("\n── RF_ReporteDiario (RF_ReporteDiario.gpkg) ──")
    if not download_gpkg(token, project_id, 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/rf_reporte_diario.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'RF_ReporteDiario')

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'Folio':         safe(row.get('folio')),
            'ID_Unico':      safe(row.get('id_unico')),
            'Observaciones': safe(row.get('observaciones')),
            'Foto':          safe(row.get('foto')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('ID_Unico'):
            rows.append(data)

    if rows:
        supabase.table('RF_ReporteDiario').insert(rows).execute()
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

    # 0. Tablas lookup (sin FKs propias; deben ir primero)
    sync_tramos_aux_infra(supabase, token, project_id)         # PK: codigo (EP/CI/MV)
    sync_presupuesto_aux_actividad(supabase, token, project_id) # PK: tipo_actividad

    # 1. Referencia geográfica
    sync_localidades(supabase, token, project_id)
    sync_tramos_bd(supabase, token, project_id)                # FK → tramos_aux_infra(codigo)

    # 2. Presupuesto
    sync_presupuesto_bd(supabase, token, project_id)           # FK → presupuesto_aux_actividad
    sync_presupuesto_componentes_bd(supabase, token, project_id)

    # 3. Formularios principales
    # FK → tramos_bd, presupuesto_bd, presupuesto_componentes_bd, presupuesto_aux_actividad
    sync_registros_cantidades(supabase, token, project_id)
    sync_registros_componentes(supabase, token, project_id)
    sync_registros_reporte_diario(supabase, token, project_id)
    sync_formulario_pmt(supabase, token, project_id)

    # 4. Tablas secundarias del Reporte Diario (FK → registros_reporteDiario.Folio)
    sync_bd_personal(supabase, token, project_id)
    sync_bd_climatica(supabase, token, project_id)
    sync_bd_maquinaria(supabase, token, project_id)
    sync_bd_sst(supabase, token, project_id)

    # 5. Registros fotográficos (FK → formularios principales via ID_Unico)
    sync_rf_cantidades(supabase, token, project_id)
    sync_rf_componentes(supabase, token, project_id)
    sync_rf_reporte_diario(supabase, token, project_id)

    print(f"\n{'='*60}")
    print(f"✓ Sincronización completa")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()