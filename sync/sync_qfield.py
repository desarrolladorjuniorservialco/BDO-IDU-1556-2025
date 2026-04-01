"""
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
Usa supabase-py (API REST) — compatible con plan Free de Supabase
"""

import os
import requests
from supabase import create_client, Client
from datetime import datetime, timezone

SUPABASE_URL    = os.environ['SUPABASE_URL']
SUPABASE_KEY    = os.environ['SUPABASE_KEY']
QFIELD_USER     = os.environ['QFIELD_USER']
QFIELD_PASSWORD = os.environ['QFIELD_PASSWORD']
PROJECT_ID      = 'BDO_IDU-1556-2025'

def get_supabase() -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Conectado a Supabase")
    return client

def qfield_login() -> str:
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

def get_qfield_features(token):
    r = requests.get(
        f'https://app.qfield.cloud/api/v1/projects/{PROJECT_ID}/packages/latest/',
        headers=qfield_headers(token),
        timeout=60
    )
    if r.status_code == 404:
        print("⚠ No hay paquete disponible aún")
        return []
    r.raise_for_status()
    package  = r.json()
    features = []
    for layer in package.get('layers', []):
        if 'Formulario_Cantidades' in layer.get('name', ''):
            lr       = requests.get(layer['url'], headers=qfield_headers(token), timeout=60)
            features = lr.json().get('features', [])
            print(f"✓ {len(features)} registros en QFieldCloud")
            break
    return features

def upload_photo(supabase, token, file_path, folio):
    if not file_path:
        return None
    encoded = requests.utils.quote(file_path, safe='')
    r = requests.get(
        f'https://app.qfield.cloud/api/v1/projects/{PROJECT_ID}/files/{encoded}/',
        headers=qfield_headers(token), timeout=60
    )
    if r.status_code != 200:
        print(f"  ⚠ No se pudo descargar: {file_path}")
        return None
    filename     = file_path.split('/')[-1]
    storage_path = f"{folio}/{filename}"
    try:
        supabase.storage.from_('fotos-obra').upload(
            path=storage_path,
            file=r.content,
            file_options={"content-type": r.headers.get('Content-Type','image/jpeg'), "upsert": "true"}
        )
        url = f"{SUPABASE_URL}/storage/v1/object/public/fotos-obra/{storage_path}"
        print(f"  ✓ Foto subida: {filename}")
        return url
    except Exception as e:
        print(f"  ⚠ Error subiendo foto: {e}")
        return None

def folio_existe(supabase, folio):
    result = supabase.table('registros').select('folio').eq('folio', folio).execute()
    return len(result.data) > 0

def insertar_registro(supabase, props, foto_urls):
    data = {
        'folio':              props.get('folio'),
        'contrato_id':        'IDU-1556-2025',
        'usuario_qfield':     props.get('usuario'),
        'tipo_infra':         props.get('tipo_infra'),
        'id_tramo':           props.get('id_tramo'),
        'tramo_descripcion':  props.get('tramo_descripcion',''),
        'civ':                props.get('civ'),
        'codigo_elemento':    props.get('codigo_elemento'),
        'fecha_inicio':       props.get('fecha_inicio'),
        'tipo_actividad':     props.get('tipo_actividad'),
        'capitulo_num':       props.get('capitulo_num'),
        'capitulo':           props.get('capitulo'),
        'item_pago':          props.get('item_pago'),
        'item_descripcion':   props.get('item_descripcion'),
        'unidad':             props.get('unidad'),
        'cantidad':           props.get('cantidad'),
        'descripcion':        props.get('descripcion'),
        'foto_1_path':        props.get('foto_1'),
        'foto_1_url':         foto_urls.get('foto_1'),
        'foto_2_path':        props.get('foto_2'),
        'foto_2_url':         foto_urls.get('foto_2'),
        'foto_3_path':        props.get('foto_3'),
        'foto_3_url':         foto_urls.get('foto_3'),
        'foto_4_path':        props.get('foto_4'),
        'foto_4_url':         foto_urls.get('foto_4'),
        'foto_5_path':        props.get('foto_5'),
        'foto_5_url':         foto_urls.get('foto_5'),
        'documento_adj_path': props.get('documento_adj'),
        'documento_adj_url':  foto_urls.get('documento_adj'),
        'observaciones':      props.get('observaciones'),
        'estado':             'BORRADOR',
        'qfield_sync_id':     str(props.get('fid','')),
    }
    data = {k: v for k, v in data.items() if v is not None}
    supabase.table('registros').upsert(data, on_conflict='folio').execute()
    print(f"  ✓ Registro insertado: {props.get('folio')}")

def main():
    print(f"\n{'='*50}")
    print(f"SYNC BDO · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    token    = qfield_login()
    supabase = get_supabase()
    features = get_qfield_features(token)
    if not features:
        print("ℹ Sin registros nuevos")
        return
    nuevos = omitidos = 0
    for feature in features:
        props = feature.get('properties', {})
        folio = props.get('folio')
        if not folio:
            omitidos += 1
            continue
        if folio_existe(supabase, folio):
            omitidos += 1
            continue
        print(f"\nProcesando: {folio}")
        foto_urls = {}
        for campo in ['foto_1','foto_2','foto_3','foto_4','foto_5','documento_adj']:
            if props.get(campo):
                foto_urls[campo] = upload_photo(supabase, token, props[campo], folio)
        insertar_registro(supabase, props, foto_urls)
        nuevos += 1
    print(f"\n✓ Completado: {nuevos} nuevos · {omitidos} omitidos\n")

if __name__ == '__main__':
    main()
