import requests
from .config import BASE_URL, SUPABASE_URL, STORAGE_BUCKET
from .connections import qfield_headers


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
        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return f"{SUPABASE_URL}/storage/v1/object/public/{STORAGE_BUCKET}/{storage_path}"
    except Exception as e:
        print(f"    ⚠ Error subiendo foto: {e}")
        return None
