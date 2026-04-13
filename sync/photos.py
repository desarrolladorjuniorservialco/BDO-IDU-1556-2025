"""
photos.py — Descarga y subida de fotos · BDO IDU-1556-2025

Compresión automática antes de subir a Supabase Storage:
  · Redimensiona a MAX_DIMENSION px en el lado mayor (por defecto 2048)
  · Guarda como JPEG con JPEG_QUALITY (por defecto 82)
  · Descarta metadata EXIF (reduce tamaño adicional sin afectar la imagen)
  · Convierte PNG/HEIC/otros formatos a JPEG transparentemente
  · Si Pillow falla por cualquier razón sube el original sin comprimir
"""
import io
import requests
from PIL import Image

from .config import BASE_URL, SUPABASE_URL, STORAGE_BUCKET
from .connections import qfield_headers

# ── configuración de compresión ────────────────────────────────────────────
MAX_DIMENSION = 2048   # px máximo en el lado mayor
JPEG_QUALITY  = 82     # 0-95; 82 da buena relación calidad/peso para fotos de obra


# ── helpers ────────────────────────────────────────────────────────────────

def _compress(content, content_type):
    """
    Abre la imagen con Pillow, redimensiona si es necesario y re-codifica
    como JPEG.  Devuelve (bytes_comprimidos, 'image/jpeg').
    Si ocurre cualquier error devuelve el original intacto.
    """
    try:
        img = Image.open(io.BytesIO(content))

        # Convertir modos no compatibles con JPEG (RGBA, P, L con alpha, etc.)
        if img.mode not in ('RGB',):
            img = img.convert('RGB')

        # Redimensionar si alguna dimensión supera MAX_DIMENSION
        w, h = img.size
        if max(w, h) > MAX_DIMENSION:
            ratio    = MAX_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            img      = img.resize(new_size, Image.LANCZOS)
            print(f"    · Redimensionada: {w}×{h} → {new_size[0]}×{new_size[1]}")

        buf = io.BytesIO()
        # optimize=True aplica un pase extra de Huffman sin pérdida adicional
        img.save(buf, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        compressed = buf.getvalue()

        orig_kb = len(content)    / 1024
        comp_kb = len(compressed) / 1024
        pct     = comp_kb / orig_kb * 100 if orig_kb else 100
        print(f"    · Compresión: {orig_kb:.0f} KB → {comp_kb:.0f} KB ({pct:.0f}%)")
        return compressed, 'image/jpeg'

    except Exception as e:
        print(f"    ⚠ No se pudo comprimir imagen: {e} — se sube sin comprimir")
        return content, content_type


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


# ── función principal ───────────────────────────────────────────────────────

def upload_photo(supabase, token, project_id, file_path, folio):
    if not file_path or str(file_path).strip() in ('', 'nan', 'None'):
        return None

    # 1. Descargar desde QFieldCloud
    candidate_urls = build_photo_urls(token, project_id, file_path)
    content = content_type = None
    for url in candidate_urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=60)
        if r.status_code == 200:
            content      = r.content
            content_type = r.headers.get('Content-Type', 'image/jpeg')
            break

    if not content:
        ruta = str(file_path)
        if any(ruta.startswith(p) for p in ['../../../', '../../', 'C:/', 'D:/']):
            print(f"    ⚠ Foto fuera del proyecto QField (ruta local PC): {file_path}")
            print(f"       → El inspector debe guardar la foto dentro de la carpeta del proyecto.")
        else:
            print(f"    ⚠ Foto no encontrada en QFieldCloud: {file_path}")
        return None

    # 2. Comprimir antes de subir
    content, content_type = _compress(content, content_type)

    # 3. Subir a Supabase Storage
    filename     = str(file_path).strip().replace('\\', '/').split('/')[-1]
    # Forzar extensión .jpg después de comprimir a JPEG
    base         = filename.rsplit('.', 1)[0] if '.' in filename else filename
    storage_name = f"{base}.jpg"
    storage_path = f"{folio}/{storage_name}"

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
