from .config import CONTRATO_ID
from .utils import safe, safe_num, coords_from_geom
from .gpkg import download_gpkg, read_layer


def _sync_bd_table(supabase, token, project_id, table, gpkg_file, tmp_path, layer, build_row):
    """Descarga un GPKG, reemplaza todos los registros del contrato y los re-inserta."""
    print(f"\n── {table} ──")
    if not download_gpkg(token, project_id, gpkg_file, tmp_path):
        return
    gdf = read_layer(tmp_path, layer)
    if gdf is None or gdf.empty:
        return

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = build_row(row, lat, lon)
        if data.get('folio'):
            rows.append(data)

    try:
        supabase.table(table).delete().eq('contrato_id', CONTRATO_ID).execute()
        if rows:
            supabase.table(table).insert(rows).execute()
        print(f"  → {len(rows)} insertados")
    except Exception as e:
        print(f"  ✗ Error en {table}: {e}")


def sync_bd_personal(supabase, token, project_id):
    def _row(row, lat, lon):
        return {
            'contrato_id':        CONTRATO_ID,
            'folio':              safe(row.get('folio')),
            'inspectores':        safe_num(row.get('inspectores')),
            'personal_operativo': safe_num(row.get('personal_operativo') or row.get('personaloperativo')),
            'personal_boal':      safe_num(row.get('perosnal_boal') or row.get('personal_boal')),
            'personal_transito':  safe_num(row.get('personal_transito') or row.get('personaltransito')),
            'longitud':           lon,
            'latitud':            lat,
        }
    _sync_bd_table(supabase, token, project_id,
                   'bd_personal_obra', 'BD_PersonalObra.gpkg', '/tmp/personal.gpkg', None, _row)


def sync_bd_climatica(supabase, token, project_id):
    def _row(row, lat, lon):
        return {
            'contrato_id':   CONTRATO_ID,
            'folio':         safe(row.get('folio')),
            'estado_clima':  safe(row.get('estado_clima') or row.get('estadoclima')),
            'hora':          safe(row.get('hora')),
            'observaciones': safe(row.get('observaciones')),
            'longitud':      lon,
            'latitud':       lat,
        }
    _sync_bd_table(supabase, token, project_id,
                   'bd_condicion_climatica', 'BD_CondicionClimatica.gpkg', '/tmp/climatica.gpkg', None, _row)


def sync_bd_maquinaria(supabase, token, project_id):
    def _row(row, lat, lon):
        return {
            'contrato_id':           CONTRATO_ID,
            'folio':                 safe(row.get('folio')),
            'operarios':             safe_num(row.get('operarios')),
            'volquetas':             safe_num(row.get('volquetas')),
            'vibrocompactador':      safe_num(row.get('vibrocompactador')),
            'equipos_especiales':    safe_num(row.get('equipos_especiales') or row.get('equiposespeciales')),
            'minicargador':          safe_num(row.get('minicargador_(con_aditamento_martillo)') or row.get('minicargador')),
            'ruteadora':             safe_num(row.get('ruteadora_(rortadora_de_pavimento)') or row.get('ruteadora')),
            'compresor':             safe_num(row.get('compresor_de_aire') or row.get('compresor')),
            'retrocargador':         safe_num(row.get('retrocargador_(con_aditamento_martillo)') or row.get('retrocargador')),
            'extendedora_asfalto':   safe_num(row.get('extendedora_de_asfalto_(finisher)') or row.get('extendedora_asfalto')),
            'compactador_neumatico': safe_num(row.get('compactador_neumatico') or row.get('compactadorneumatico')),
            'observaciones':         safe(row.get('observaciones')),
            'longitud':              lon,
            'latitud':               lat,
        }
    _sync_bd_table(supabase, token, project_id,
                   'bd_maquinaria_obra', 'BD_MaquinariaObra.gpkg', '/tmp/maquinaria.gpkg', None, _row)


def sync_bd_sst(supabase, token, project_id):
    def _row(row, lat, lon):
        return {
            'contrato_id':       CONTRATO_ID,
            'folio':             safe(row.get('folio')),
            'observaciones':     safe(row.get('observaciones')),
            'longitud':          lon,
            'latitud':           lat,
            'botiquin':          safe_num(row.get('botiquin')),
            'kit_antiderrames':  safe_num(row.get('kit_antiderrames') or row.get('kitantiderrames')),
            'punto_hidratacion': safe_num(row.get('punto_de_hidratacion') or row.get('punto_hidratacion')),
            'punto_ecologico':   safe_num(row.get('punto_ecologico')),
            'extintor':          safe_num(row.get('extintor')),
        }
    _sync_bd_table(supabase, token, project_id,
                   'bd_sst_ambiental', 'BD_SST-Ambiental.gpkg', '/tmp/sst.gpkg', 'BD_SST-Ambiental', _row)
