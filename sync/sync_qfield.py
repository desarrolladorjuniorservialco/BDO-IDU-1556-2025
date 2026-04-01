"""
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
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
GPKG_FILE       = 'Formulario_Cantidades.gpkg'
LAYER_NAME      = 'Formulario_Cantidades_V2'
BASE_URL        = 'https://app.qfield.cloud/api/v1'


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


def download_gpkg(token, project_id):
    urls = [
        f'{BASE_URL}/files/{project_id}/{GPKG_FILE}/',
        f'{BASE_URL}/files/{project_id}/files/{GPKG_FILE}/',
    ]
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=120)
        if r.status_code == 200:
            with open('/tmp/formulario.gpkg', 'wb') as f:
                f.write(r.content)
            print(f"✓ GeoPackage descargado ({len(r.content)/1024:.1f} KB)")
            return True
        print(f"  ⚠ {r.status_code} en: {url}")
    return False


def read_formulario():
    try:
        gdf = gpd.read_file('/tmp/formulario.gpkg', layer=LAYER_NAME)
    except Exception as e:
        print(f"  ⚠ Error leyendo capa {LAYER_NAME}: {e}")
        gdf = gpd.read_file('/tmp/formulario.gpkg')

    # Normaliza nombres de columnas — elimina espacios invisibles
    gdf.columns = [c.strip() for c in gdf.columns]

    # Reproyecta a WGS84 para lat/lon correctos
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print(f"  Reproyectando EPSG:{gdf.crs.to_epsg()} → WGS84...")
        gdf = gdf.to_crs(epsg=4326)

    print(f"✓ {len(gdf)} registros leídos")
    print(f"  Columnas: {list(gdf.columns)}")
    return gdf


def upload_photo(supabase, token, project_id, file_path, folio):
    if not file_path or str(file_path).strip() in ('', 'nan', 'None'):
        return None

    path_clean = str(file_path).strip()
    encoded    = requests.utils.quote(path_clean, safe='/')

    urls = [
        f'{BASE_URL}/files/{project_id}/{encoded}/',
        f'{BASE_URL}/files/{project_id}/files/{encoded}/',
    ]

    content = content_type = None
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=60)
        if r.status_code == 200:
            content      = r.content
            content_type = r.headers.get('Content-Type', 'image/jpeg')
            break

    if not content:
        print(f"  ⚠ No se pudo descargar foto: {path_clean}")
        return None

    filename     = path_clean.split('/')[-1]
    storage_path = f"{folio}/{filename}"

    try:
        supabase.storage.from_('fotos-obra').upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        url = f"{SUPABASE_URL}/storage/v1/object/public/fotos-obra/{storage_path}"
        print(f"  ✓ Foto subida: {filename}")
        return url
    except Exception as e:
        print(f"  ⚠ Error subiendo foto: {e}")
        return None


def folio_existe(supabase, folio):
    result = supabase.table('registros').select('folio').eq('folio', str(folio)).execute()
    return len(result.data) > 0


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


def insertar_registro(supabase, row, foto_urls):
    # Coordenadas desde geometría
    lat = lon = None
    geom = row.get('geometry')
    if geom is not None:
        try:
            if hasattr(geom, 'x') and hasattr(geom, 'y'):
                lon = geom.x
                lat = geom.y
                print(f"  ✓ Coordenadas: lat={lat:.6f}, lon={lon:.6f}")
        except Exception as e:
            print(f"  ⚠ Error extrayendo coordenadas: {e}")

    folio = safe(row.get('folio'))

    data = {
        'folio':              str(folio),
        'contrato_id':        'IDU-1556-2025',
        'usuario_qfield':     safe(row.get('usuario')),
        'tipo_infra':         safe(row.get('tipo_infra')),
        'id_tramo':           safe(row.get('id_tramo')),
        'tramo_descripcion':  safe(row.get('tramo_descripcion')),
        'civ':                safe(row.get('civ')),
        'codigo_elemento':    safe(row.get('codigo_elemento')),
        'latitud':            lat,
        'longitud':           lon,
        'fecha_inicio':       safe(row.get('fecha_inicio')),
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
        'estado':             'BORRADOR',
        'qfield_sync_id':     str(safe(row.get('fid', ''))),
    }

    data = {k: v for k, v in data.items() if v is not None}
    supabase.table('registros').upsert(data, on_conflict='folio').execute()
    print(f"  ✓ Registro insertado: {folio}")


def main():
    print(f"\n{'='*50}")
    print(f"SYNC BDO · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    token      = qfield_login()
    supabase   = get_supabase()
    project_id = get_project_id(token)

    if not download_gpkg(token, project_id):
        print("ℹ Sin GeoPackage disponible — abortando")
        return

    gdf = read_formulario()
    if gdf is None or gdf.empty:
        print("ℹ GeoPackage vacío")
        return

    nuevos = omitidos = 0

    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))

        if not folio:
            print("  ⚠ Sin folio — omitido")
            omitidos += 1
            continue

        if folio_existe(supabase, str(folio)):
            print(f"  · Ya existe: {folio}")
            omitidos += 1
            continue

        print(f"\nProcesando: {folio}")

        foto_urls = {}
        for campo in ['foto_1','foto_2','foto_3','foto_4','foto_5','documento_adj']:
            path = safe(row.get(campo))
            if path:
                foto_urls[campo] = upload_photo(supabase, token, project_id, path, folio)

        insertar_registro(supabase, row, foto_urls)
        nuevos += 1

    print(f"\n{'='*50}")
    print(f"✓ Completado: {nuevos} nuevos · {omitidos} omitidos")
    print(f"{'='*50}\n")


if __name__ == '__main__':
    main()
