""" cambio
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
Alimenta todas las tablas definidas en 001_TABLAS.sql
desde los GeoPackages actualizados en QField Cloud.

Orden de ejecución (respeta FKs):
  1. Referencia geográfica  : localidades, tramos_bd
  2. Presupuesto            : presupuesto_bd, presupuesto_componentes_bd
  3. Formularios principales: registros_cantidades, registros_componentes,
                              registros_reporteDiario, formulario_pmt
  4. Tablas secundarias BD_ : BD_PersonalObra, BD_CondicionClimatica,
                              BD_MaquinariaObra, BD_SST_Ambiental
  5. Registros fotográficos : RF_Cantidades, RF_Componentes, RF_ReporteDiario
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
    """Lee una capa de un GeoPackage, con fallback a la primera capa, y normaliza a WGS84."""
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
        data = {
            'loc_codigo': safe(row.get('loc_codigo') or row.get('Field1')),
            'loc_nombre': safe(row.get('loc_nombre') or row.get('Field2')),
            'loc_admin':  safe(row.get('loc_admin')),
            'loc_area':   safe_num(row.get('loc_area')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('loc_codigo') and data.get('loc_nombre'):
            supabase.table('localidades').upsert(data, on_conflict='loc_codigo').execute()
            count += 1
    print(f"  → {count} upserted")


def sync_tramos_bd(supabase, token, project_id):
    print("\n── tramos_bd (TramosIDU15562025BDTRAMOS.gpkg) ──")
    if not download_gpkg(token, project_id, 'TramosIDU15562025BDTRAMOS.gpkg', '/tmp/tramos_bd.gpkg'):
        return
    gdf = read_layer('/tmp/tramos_bd.gpkg')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'id_tramo':          safe(row.get('id_tramo') or row.get('Field1')),
            'tramo_descripcion': safe(row.get('tramo_descripcion') or row.get('Field2')),
            'via_principal':     safe(row.get('via_principal')),
            'via_desde':         safe(row.get('via_desde')),
            'via_hasta':         safe(row.get('via_hasta')),
            'localidad':         safe(row.get('localidad')),
            'infraestructura':   safe(row.get('infraestructura')),
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
            'codigo_idu':     safe(row.get('codigo_idu') or row.get('Field1')),
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
        data = {
            'capitulo_num':    safe(row.get('capitulo_num') or row.get('Capitulo')),
            'capitulo':        safe(row.get('capitulo')),
            'componente':      safe(row.get('componente') or row.get('Field2')),
            'tipo_actividad':  safe(row.get('tipo_actividad') or row.get('Field3')),
            'codigo_idu':      safe(row.get('codigo_idu') or row.get('Field1')),
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
            'ID_Unico':           safe(row.get('ID_Unico')),
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
            'CodigoInterventor':  safe(row.get('CodigoInterventor')),
            'AcompañamientoInterventor': safe(row.get('AcompañamientoInterventor')),
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
        folio = safe(row.get('Folio') or row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':              str(folio),
            'ID_Unico':           safe(row.get('ID_Unico')),
            'contrato_id':        CONTRATO_ID,
            'usuario_qfield':     safe(row.get('usuario')),
            'id_tramo':           safe(row.get('id_tramo')),
            'Tramo':              safe(row.get('Tramo')),
            'CIV':                safe(row.get('CIV') or row.get('civ')),
            'codigo_elemento':    safe(row.get('codigo_elemento')),
            'tipo_infra':         safe(row.get('tipo_infra')),
            'Componente':         safe(row.get('Componente')),
            'latitud':            lat,
            'longitud':           lon,
            'Fecha':              safe(row.get('Fecha')),
            'Fecha_Reporte':      safe(row.get('Fecha_Reporte')),
            'tipo_actividad':     safe(row.get('tipo_actividad')),
            'capitulo_num':       safe(row.get('capitulo_num')),
            'capitulo':           safe(row.get('capitulo')),
            'item_pago':          safe(row.get('item_pago')),
            'item_descripcion':   safe(row.get('item_descripcion')),
            'cantidad':           safe_num(row.get('cantidad')),
            'unidad':             safe(row.get('unidad')),
            'precio_unitario':    safe_num(row.get('precio_unitario')),
            'Observaciones':      safe(row.get('Observaciones') or row.get('observaciones')),
            'Profesional':        safe(row.get('Profesional')),
            'CodigoInterventor':  safe(row.get('CodigoInterventor')),
            'AcompañamientoInterventor': safe(row.get('AcompañamientoInterventor')),
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
        folio = safe(row.get('Folio') or row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':          str(folio),
            'ID_Unico':       safe(row.get('ID_Unico')),
            'contrato_id':    CONTRATO_ID,
            'usuario_qfield': safe(row.get('usuario')),
            'latitud':        lat,
            'longitud':       lon,
            'Fecha':          safe(row.get('Fecha')),
            'Fecha_Reporte':  safe(row.get('Fecha_Reporte')),
            'Observaciones':  safe(row.get('Observaciones') or row.get('observaciones')),
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
        folio = safe(row.get('Folio') or row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'Folio':           str(folio),
            'contrato_id':     CONTRATO_ID,
            'descripcion':     safe(row.get('descripcion')),
            'CIV':             safe(row.get('CIV') or row.get('civ')),
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
            'Folio':             safe(row.get('Folio')),
            'Inspectores':       safe_num(row.get('Inspectores')),
            'PersonalOperativo': safe_num(row.get('PersonalOperativo')),
            'PersonalBOAL':      safe_num(row.get('PersonalBOAL')),
            'PersonalTransito':  safe_num(row.get('PersonalTransito')),
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
            'Folio':         safe(row.get('Folio')),
            'EstadoClima':   safe(row.get('EstadoClima')),
            'Hora':          safe(row.get('Hora')),
            'Observaciones': safe(row.get('Observaciones')),
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
            'Folio':                safe(row.get('Folio')),
            'Operarios':            safe_num(row.get('Operarios')),
            'Volquetas':            safe_num(row.get('Volquetas')),
            'Vibrocompactador':     safe_num(row.get('Vibrocompactador')),
            'EquiposEspeciales':    safe_num(row.get('EquiposEspeciales')),
            'Minicargador':         safe_num(row.get('Minicargador')),
            'Ruteadora':            safe_num(row.get('Ruteadora')),
            'Compresor':            safe_num(row.get('Compresor')),
            'Retrocargador':        safe_num(row.get('Retrocargador')),
            'ExtendedoraAsfalto':   safe_num(row.get('ExtendedoraAsfalto')),
            'CompactadorNeumatico': safe_num(row.get('CompactadorNeumatico')),
            'Observaciones':        safe(row.get('Observaciones')),
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
            'Folio':            safe(row.get('Folio')),
            'Observaciones':    safe(row.get('Observaciones')),
            'Longitud':         lon,
            'Latitud':          lat,
            'Botiquin':         safe_num(row.get('Botiquin')),
            'KitAntiderrames':  safe_num(row.get('KitAntiderrames')),
            'PuntoHidratacion': safe_num(row.get('PuntoHidratacion')),
            'PuntoEcologico':   safe_num(row.get('PuntoEcologico')),
            'Extintor':         safe_num(row.get('Extintor')),
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
            'Folio':             safe(row.get('Folio')),
            'ID_Unico':          safe(row.get('ID_Unico')),
            'Observacion':       safe(row.get('Observacion')),
            'Nombre_Foto':       safe(row.get('Nombre_Foto')),
            'Ruta_Destino_Foto': safe(row.get('Ruta_Destino_Foto')),
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
            'Folio':        safe(row.get('Folio')),
            'ID_Unico':     safe(row.get('ID_Unico')),
            'Observaciones': safe(row.get('Observaciones')),
            'Foto':         safe(row.get('Foto')),
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
            'Folio':        safe(row.get('Folio')),
            'ID_Unico':     safe(row.get('ID_Unico')),
            'Observaciones': safe(row.get('Observaciones')),
            'Foto':         safe(row.get('Foto')),
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

    # 1. Referencia geográfica (sin FKs a otras tablas del proyecto)
    sync_localidades(supabase, token, project_id)
    sync_tramos_bd(supabase, token, project_id)

    # 2. Presupuesto
    sync_presupuesto_bd(supabase, token, project_id)
    sync_presupuesto_componentes_bd(supabase, token, project_id)

    # 3. Formularios principales
    sync_registros_cantidades(supabase, token, project_id)
    sync_registros_componentes(supabase, token, project_id)
    sync_registros_reporte_diario(supabase, token, project_id)
    sync_formulario_pmt(supabase, token, project_id)

    # 4. Tablas secundarias del Reporte Diario (FK → registros_reporteDiario)
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
