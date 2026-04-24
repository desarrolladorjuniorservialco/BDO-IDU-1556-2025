from .config import CONTRATO_ID
from .utils import safe, safe_num
from .gpkg import download_gpkg, read_layer
from .sync_lookup import _infra_a_codigo


def sync_localidades(supabase, token, project_id):
    print("\n── localidades ──")
    if not download_gpkg(token, project_id, 'loca.gpkg', '/tmp/loca.gpkg'):
        return
    gdf = read_layer('/tmp/loca.gpkg', 'Loca')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'contrato_id': CONTRATO_ID,
            'loc_codigo':  safe(row.get('loccodigo')  or row.get('loc_codigo')),
            'loc_nombre':  safe(row.get('locnombre')  or row.get('loc_nombre')),
            'loc_admin':   safe(row.get('locaadmini') or row.get('loc_admin')),
            'loc_area':    safe_num(row.get('locarea') or row.get('loc_area')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('loc_codigo') and data.get('loc_nombre'):
            supabase.table('localidades').upsert(
                data, on_conflict='contrato_id,loc_codigo'
            ).execute()
            count += 1
    print(f"  → {count} upserted")


def sync_tramos_bd(supabase, token, project_id):
    """
    [D-08] GPKG tiene 'ciclorruta_km' (con doble r), NO 'cicloruta_km'.
    """
    print("\n── tramos_bd ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'BD_Tramos.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'contrato_id':       CONTRATO_ID,
            'id_tramo':          safe(row.get('id_tramo')),
            'tramo_descripcion': safe(row.get('tramo_descripcion')),
            'via_principal':     safe(row.get('via_principal')),
            'via_desde':         safe(row.get('via_desde')),
            'via_hasta':         safe(row.get('via_hasta')),
            'localidad':         safe(row.get('localidad')),
            'infraestructura':   _infra_a_codigo(row.get('infraestructura')),
            'observaciones':     safe(row.get('observaciones')),
            # [D-08] columna real en GPKG: 'ciclorruta_km' (doble r)
            'cicloruta_km':      safe_num(row.get('ciclorruta_km') or row.get('cicloruta_km')),
            'esp_publico_m2':    safe_num(row.get('esp_publico_m2')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('id_tramo'):
            supabase.table('tramos_bd').upsert(
                data, on_conflict='contrato_id,id_tramo'
            ).execute()
            count += 1
    print(f"  → {count} upserted")
