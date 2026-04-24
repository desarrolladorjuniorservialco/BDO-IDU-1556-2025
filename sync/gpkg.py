import geopandas as gpd
import requests
from .config import BASE_URL
from .connections import qfield_headers

_file_cache: dict[str, list[dict]] = {}


def list_project_files(token, project_id) -> list[dict]:
    """Retorna la lista de archivos del proyecto (con caché por project_id)."""
    if project_id in _file_cache:
        return _file_cache[project_id]
    urls = [
        f'{BASE_URL}/files/{project_id}/',
        f'{BASE_URL}/projects/{project_id}/files/',
    ]
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=30)
        if r.status_code == 200:
            data = r.json()
            files = data if isinstance(data, list) else data.get('results', data.get('files', []))
            _file_cache[project_id] = files
            return files
    return []


def _find_file_url(token, project_id, filename) -> str | None:
    """
    Busca la URL de descarga de un archivo por nombre exacto o parcial.
    Prueba primero project-files; si fallan, intenta packages (archivos
    generados por QField al sincronizar desde la app).
    """
    name_lower = filename.lower()

    # 1. Project files — endpoint estándar
    candidates = [
        f'{BASE_URL}/files/{project_id}/{filename}/',
        f'{BASE_URL}/projects/{project_id}/files/{filename}/',
    ]
    for url in candidates:
        r = requests.head(url, headers=qfield_headers(token), timeout=30)
        if r.status_code == 200:
            return url

    # 2. Búsqueda en el listado del proyecto — confiar en el listado sin HEAD
    files = list_project_files(token, project_id)
    for f in files:
        path = f.get('name') or f.get('path') or f.get('filename') or ''
        if path.lower().endswith(name_lower) or name_lower in path.lower():
            return f'{BASE_URL}/files/{project_id}/{path}/'

    # 3. Package files — archivos generados por QField al sincronizar
    return f'{BASE_URL}/packages/{project_id}/latest/files/{filename}/'


def download_file(token, project_id, filename, tmp_path):
    """Descarga cualquier archivo del proyecto QFieldCloud (GPKG, XLSX, etc.)."""
    pkg_url = f'{BASE_URL}/packages/{project_id}/latest/files/{filename}/'

    url = _find_file_url(token, project_id, filename)
    r = requests.get(url, headers=qfield_headers(token), timeout=120)
    if r.status_code == 200:
        with open(tmp_path, 'wb') as f:
            f.write(r.content)
        print(f"  ✓ Descargado {filename} ({len(r.content)/1024:.1f} KB)")
        return True

    # Fallback: packages endpoint (archivos sincronizados desde la app QField).
    # Necesario cuando el rol QFIELD_USER no tiene acceso a project-files pero
    # sí al paquete generado por la última sincronización desde la app.
    if r.status_code in (401, 403) and url != pkg_url:
        r2 = requests.get(pkg_url, headers=qfield_headers(token), timeout=120)
        if r2.status_code == 200:
            with open(tmp_path, 'wb') as f:
                f.write(r2.content)
            print(f"  ✓ Descargado {filename} vía packages ({len(r2.content)/1024:.1f} KB)")
            return True
        print(f"  ⚠ packages también falló: {r2.status_code}")

    print(f"  ⚠ {r.status_code} en {url}")
    print(f"  ✗ No se pudo descargar {filename} — omitido")
    return False


def download_gpkg(token, project_id, gpkg_file, tmp_path):
    """Alias de download_file para retrocompatibilidad."""
    return download_file(token, project_id, gpkg_file, tmp_path)


def read_layer(tmp_path, layer_name=None):
    """Lee capa de GeoPackage y normaliza columnas a minúsculas."""
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
