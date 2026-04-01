"""
sync_qfield.py
BDO IDU-1556-2025 · Sincronización QFieldCloud → Supabase
Corre automáticamente via GitHub Actions cada 20 minutos en jornada
"""

import os
import json
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

# ── Credenciales desde variables de entorno (GitHub Secrets) ──
SUPABASE_URL      = os.environ['SUPABASE_URL']
SUPABASE_KEY      = os.environ['SUPABASE_KEY']
SUPABASE_DB_PASS  = os.environ['SUPABASE_DB_PASSWORD']
QFIELD_USER       = os.environ['QFIELD_USER']
QFIELD_PASSWORD   = os.environ['QFIELD_PASSWORD']
PROJECT_ID        = 'BDO_IDU-1556-2025'

SUPABASE_HOST     = SUPABASE_URL.replace('https://', 'db.').split('.supabase')[0] + '.supabase.co'

# ══════════════════════════════════════════════════════════════
# 1. AUTENTICACIÓN QFIELDCLOUD
# ══════════════════════════════════════════════════════════════

def qfield_login():
    """Obtiene token de sesión con usuario y contraseña"""
    r = requests.post(
        'https://app.qfield.cloud/api/v1/auth/login/',
        json={'username': QFIELD_USER, 'password': QFIELD_PASSWORD},
        timeout=30
    )
    r.raise_for_status()
    token = r.json().get('token')
    print(f"✓ QFieldCloud autenticado")
    return token


def qfield_headers(token):
    return {'Authorization': f'Token {token}'}


# ══════════════════════════════════════════════════════════════
# 2. CONEXIÓN A SUPABASE (PostgreSQL)
# ══════════════════════════════════════════════════════════════

def get_db_conn():
    """Conexión directa a PostgreSQL de Supabase"""
    conn = psycopg2.connect(
        host=SUPABASE_HOST,
        database='postgres',
        user='postgres',
        password=SUPABASE_DB_PASS,
        port=5432,
        sslmode='require',
        connect_timeout=10
    )
    print(f"✓ Conectado a Supabase PostgreSQL")
    return conn


# ══════════════════════════════════════════════════════════════
# 3. OBTENER REGISTROS NUEVOS DE QFIELDCLOUD
# ══════════════════════════════════════════════════════════════

def get_last_sync(conn):
    """Obtiene el timestamp del último registro sincronizado"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(fecha_creacion) 
            FROM registros 
            WHERE qfield_sync_id IS NOT NULL
        """)
        result = cur.fetchone()[0]
        return result or datetime(2025, 1, 1, tzinfo=timezone.utc)


def get_qfield_features(token):
    """Descarga las features de la capa Formulario_Cantidades"""
    r = requests.get(
        f'https://app.qfield.cloud/api/v1/projects/{PROJECT_ID}/packages/latest/',
        headers=qfield_headers(token),
        timeout=60
    )
    if r.status_code == 404:
        print("⚠ No hay paquete disponible en QFieldCloud aún")
        return []
    r.raise_for_status()

    # Busca el archivo GeoJSON de la capa principal
    package = r.json()
    features = []

    for layer in package.get('layers', []):
        if 'Formulario_Cantidades' in layer.get('name', ''):
            layer_url = layer.get('url')
            if layer_url:
                lr = requests.get(layer_url, headers=qfield_headers(token), timeout=60)
                data = lr.json()
                features = data.get('features', [])
                print(f"✓ {len(features)} registros encontrados en QFieldCloud")
                break

    return features


# ══════════════════════════════════════════════════════════════
# 4. TRANSFERIR FOTOS A SUPABASE STORAGE
# ══════════════════════════════════════════════════════════════

def upload_photo(token, file_path, folio):
    """
    Descarga foto de QFieldCloud y la sube a Supabase Storage
    Retorna la URL pública en Supabase
    """
    if not file_path:
        return None

    # Descarga desde QFieldCloud
    encoded_path = requests.utils.quote(file_path, safe='')
    r = requests.get(
        f'https://app.qfield.cloud/api/v1/projects/{PROJECT_ID}/files/{encoded_path}/',
        headers=qfield_headers(token),
        timeout=60
    )

    if r.status_code != 200:
        print(f"  ⚠ No se pudo descargar: {file_path}")
        return None

    # Nombre del archivo en Storage (solo el basename)
    filename = file_path.split('/')[-1]
    storage_path = f"{folio}/{filename}"

    # Sube a Supabase Storage
    upload_r = requests.post(
        f"{SUPABASE_URL}/storage/v1/object/fotos-obra/{storage_path}",
        headers={
            'Authorization': f'Bearer {SUPABASE_KEY}',
            'Content-Type': r.headers.get('Content-Type', 'image/jpeg'),
            'x-upsert': 'true'
        },
        data=r.content,
        timeout=60
    )

    if upload_r.status_code in (200, 201):
        url = f"{SUPABASE_URL}/storage/v1/object/public/fotos-obra/{storage_path}"
        print(f"  ✓ Foto subida: {filename}")
        return url
    else:
        print(f"  ⚠ Error subiendo foto: {upload_r.text}")
        return None


# ══════════════════════════════════════════════════════════════
# 5. INSERTAR REGISTRO EN SUPABASE
# ══════════════════════════════════════════════════════════════

def folio_existe(conn, folio):
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM registros WHERE folio = %s", (folio,))
        return cur.fetchone() is not None


def insertar_registro(conn, props, foto_urls):
    """Inserta un registro nuevo en la tabla registros"""
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO registros (
                folio, contrato_id,
                usuario_qfield, tipo_infra,
                id_tramo, tramo_descripcion, civ, codigo_elemento,
                fecha_inicio,
                tipo_actividad, capitulo_num, capitulo,
                item_pago, item_descripcion,
                unidad, cantidad, descripcion,
                foto_1_path, foto_1_url,
                foto_2_path, foto_2_url,
                foto_3_path, foto_3_url,
                foto_4_path, foto_4_url,
                foto_5_path, foto_5_url,
                documento_adj_path, documento_adj_url,
                observaciones,
                estado, qfield_sync_id
            ) VALUES (
                %(folio)s, 'IDU-1556-2025',
                %(usuario)s, %(tipo_infra)s,
                %(id_tramo)s, %(tramo_descripcion)s, %(civ)s, %(codigo_elemento)s,
                %(fecha_inicio)s,
                %(tipo_actividad)s, %(capitulo_num)s, %(capitulo)s,
                %(item_pago)s, %(item_descripcion)s,
                %(unidad)s, %(cantidad)s, %(descripcion)s,
                %(foto_1_path)s, %(foto_1_url)s,
                %(foto_2_path)s, %(foto_2_url)s,
                %(foto_3_path)s, %(foto_3_url)s,
                %(foto_4_path)s, %(foto_4_url)s,
                %(foto_5_path)s, %(foto_5_url)s,
                %(documento_adj_path)s, %(documento_adj_url)s,
                %(observaciones)s,
                'BORRADOR', %(sync_id)s
            )
            ON CONFLICT (folio) DO NOTHING
        """, {
            'folio':              props.get('folio'),
            'usuario':            props.get('usuario'),
            'tipo_infra':         props.get('tipo_infra'),
            'id_tramo':           props.get('id_tramo'),
            'tramo_descripcion':  props.get('tramo_descripcion', ''),
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
            'sync_id':            props.get('fid', ''),
        })
    conn.commit()
    print(f"  ✓ Registro insertado: {props.get('folio')}")


# ══════════════════════════════════════════════════════════════
# 6. FLUJO PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*50}")
    print(f"SYNC BDO IDU-1556-2025 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")

    # Autenticación
    token = qfield_login()
    conn  = get_db_conn()

    try:
        # Obtiene registros de QFieldCloud
        features = get_qfield_features(token)

        if not features:
            print("ℹ No hay registros nuevos para sincronizar")
            return

        nuevos = 0
        omitidos = 0

        for feature in features:
            props = feature.get('properties', {})
            folio = props.get('folio')

            if not folio:
                print(f"  ⚠ Registro sin folio — omitido")
                omitidos += 1
                continue

            # Evita duplicados
            if folio_existe(conn, folio):
                omitidos += 1
                continue

            print(f"\nProcesando: {folio}")

            # Transfiere fotos a Supabase Storage
            foto_urls = {}
            for campo in ['foto_1','foto_2','foto_3','foto_4','foto_5','documento_adj']:
                path = props.get(campo)
                if path:
                    foto_urls[campo] = upload_photo(token, path, folio)

            # Inserta registro en Supabase
            insertar_registro(conn, props, foto_urls)
            nuevos += 1

        print(f"\n{'='*50}")
        print(f"✓ Sync completado: {nuevos} nuevos · {omitidos} omitidos")
        print(f"{'='*50}\n")

    except Exception as e:
        print(f"\n✗ Error durante sync: {e}")
        raise

    finally:
        conn.close()


if __name__ == '__main__':
    main()
