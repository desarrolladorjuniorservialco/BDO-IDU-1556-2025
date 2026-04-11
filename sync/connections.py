import requests
from supabase import create_client
from .config import SUPABASE_URL, SUPABASE_KEY, QFIELD_USER, QFIELD_PASSWORD, PROJECT_NAME, BASE_URL


def get_supabase():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Conectado a Supabase")
    return client


def qfield_login():
    r = requests.post(
        f'{BASE_URL}/auth/login/',
        json={'username': QFIELD_USER, 'password': QFIELD_PASSWORD},
        timeout=30,
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
