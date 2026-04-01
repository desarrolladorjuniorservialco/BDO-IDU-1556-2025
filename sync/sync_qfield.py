"""
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
Lee el GeoPackage directamente desde QFieldCloud files API
"""

import os
import requests
import geopandas as gpd
from supabase import create_client
from datetime import datetime

SUPABASE_URL    = os.environ['SUPABASE_URL']
SUPABASE_KEY    = os.environ['SUPABASE_KEY']
QFIELD_USER     = os.environ['QFIELD_USER']
QFIELD_PASSWORD = os.environ['QFIELD_PASSWORD']
PROJECT_ID      = 'SERVIALCO/BDO_IDU-1556-2025'
GPKG_FILE       = 'Formulario_Cantidades.gpkg'
LAYER_NAME      = 'Formulario_Cantidades'


def get_supabase():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Conectado a Supabase")
    return client


def qfield_login():
    r = requests.post(
        'https://app.qfield.cloud/api/v1/auth/login/',
        json={'username': QFIELD_USER, 'password': QFIELD_PASSWORD},
        timeout=30
    )
    r.raise_for_status()
    token = r.json().get('token')
    print("✓ QFieldCloud autenticado")
    return token


def qfield_headers(token):
    return {'Authorization': f'Token {token}'}


def download_gpkg(token):
    """Descarga el GeoPackage del formulario desde QFieldCloud"""
    urls = [
        f'https://app.qfield.cloud/api/v1/files/{PROJECT_ID}/files/{GPKG_FILE}/',
        f'https://app.qfield.cloud/api/v1/files/{PROJECT_ID}/{GPKG_FILE}/',
    ]
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=120)
        if r.status_code == 200:
            print(f"✓ GeoPackage descargado ({len(r.content)/1024:.1f} KB)")
            print(f"  URL usada: {url}")
            return r.content
        print(f"  ⚠ No encontrado en: {url}")
    return None


def read_features(gpkg_bytes):
    """Lee las features del GeoPackage en memoria"""
    with open('/tmp/formulario.gpkg', 'wb') as f:
        f.write(gpkg_bytes)
    try:
        gdf = gpd.read_file('/tmp/formulario.gpkg', layer=LAYER_NAME)
    except Exception:
        gdf = gpd.read_file('/tmp/formulario.gpkg')
    print(f"✓ {len(gdf)} registros leídos del GeoPackage")
    print(f"  Columnas: {list(gdf.columns)}")
    return gdf


def upload_photo(supabase, token, file_path, folio):
    """Descarga foto de QFieldCloud y la sube a Supabase Storage"""
    if not file_path or str(file_path) == 'nan':
        return None
    encoded = requests.utils.quote(str(file_path), safe='')
    urls = [
        f'https://app.qfield.cloud/api/v1/files/{PROJECT_ID}/files/{encoded}/',
        f'https://app.qfield.cloud/api/v1/files/{PROJECT_ID}/{encoded}/',
    ]
    content = None
    content_type = 'image/jpeg'
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=60)
        if r.status_code == 200:
            content = r.content
            content_type = r.headers.get('Content-Type', 'image/jpeg')
            break
    if not content:
        print(f"  ⚠ No se pudo descargar foto: {file_path}")
        return None
    filename     = str(file_path).split('/')[-1]
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
    """Convierte NaN y None a None para Supabase"""
    if val is None:
        return None
    try:
        import math
        if math.isnan(float(val)):
            return None
    except (TypeError, ValueError):
        pass
    return val


def insertar_registro(supabase, row, foto_urls):
    folio = safe(row.get('folio'))
    data = {
        'folio':              str(folio),
        'contrato_id':        'IDU-1556-2025',
        'usuario_qfield':     safe(row.get('usuario')),
        'tipo_infra':         safe(row.get('tipo_infra')),
        'id_tramo':           safe(row.get('id_tramo')),
        'tramo_descripcion':  safe(row.get('tramo_descripcion', '')),
        'civ':                safe(row.get('civ')),
        'codigo_elemento':    safe(row.get('codigo_elemento')),
        'fecha_inicio':       str(safe(row.get('fecha_inicio'))) if safe(row.get('fecha_inicio')) else None,
        'tipo_actividad':     safe(row.get('tipo_actividad')),
        'capitulo_num':       safe(row.get('capitulo_num')),
        'capitulo':           safe(row.get('capitulo')),
        'item_pago':          safe(row.get('item_pago')),
        'item_descripcion':   safe(row.get('item_descripcion')),
        'unidad':             safe(row.get('unidad')),
        'cantidad':           safe(row.get('cantidad')),
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

    token    = qfield_login()
    supabase = get_supabase()

    gpkg_bytes = download_gpkg(token)
    if not gpkg_bytes:
        print("ℹ Sin GeoPackage disponible — abortando")
        return

    gdf = read_features(gpkg_bytes)

    if gdf.empty:
        print("ℹ GeoPackage vacío — sin registros")
        return

    nuevos = omitidos = 0

    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))

        if not folio:
            print("  ⚠ Registro sin folio — omitido")
            omitidos += 1
            continue

        if folio_existe(supabase, str(folio)):
            omitidos += 1
            continue

        print(f"\nProcesando: {folio}")

        foto_urls = {}
        for campo in ['foto_1', 'foto_2', 'foto_3', 'foto_4', 'foto_5', 'documento_adj']:
            path = safe(row.get(campo))
            if path:
                foto_urls[campo] = upload_photo(supabase, token, path, folio)

        insertar_registro(supabase, row, foto_urls)
        nuevos += 1

    print(f"\n✓ Completado: {nuevos} nuevos · {omitidos} omitidos\n")


if __name__ == '__main__':
    main()
