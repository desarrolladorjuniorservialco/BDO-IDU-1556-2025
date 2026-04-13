import geopandas as gpd
import requests
from .config import BASE_URL
from .connections import qfield_headers


def download_file(token, project_id, filename, tmp_path):
    """Descarga cualquier archivo del proyecto QFieldCloud (GPKG, XLSX, etc.)."""
    urls = [
        f'{BASE_URL}/files/{project_id}/{filename}/',
        f'{BASE_URL}/files/{project_id}/files/{filename}/',
    ]
    for url in urls:
        r = requests.get(url, headers=qfield_headers(token), timeout=120)
        if r.status_code == 200:
            with open(tmp_path, 'wb') as f:
                f.write(r.content)
            print(f"  ✓ Descargado {filename} ({len(r.content)/1024:.1f} KB)")
            return True
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
