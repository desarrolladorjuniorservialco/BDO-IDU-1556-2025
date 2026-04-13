from .utils import safe, safe_num, coords_from_geom
from .gpkg import download_gpkg, read_layer, delete_all


def sync_bd_personal(supabase, token, project_id):
    """
    [D-04] Columnas corregidas. Estructura constante para evitar PGRST102.
    """
    print("\n── bd_personal_obra ──")
    if not download_gpkg(token, project_id, 'BD_PersonalObra.gpkg', '/tmp/personal.gpkg'):
        return
    gdf = read_layer('/tmp/personal.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_personal_obra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'folio':              safe(row.get('folio')),
            'inspectores':        safe_num(row.get('inspectores')),
            'personal_operativo': safe_num(row.get('personal_operativo') or row.get('personaloperativo')),
            'personal_boal':      safe_num(row.get('perosnal_boal') or row.get('personal_boal')),
            'personal_transito':  safe_num(row.get('personal_transito') or row.get('personaltransito')),
            'longitud':           lon,
            'latitud':            lat,
        }
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_personal_obra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_climatica(supabase, token, project_id):
    """
    [D-05] Columna 'estado_clima' corregida. Estructura constante para evitar PGRST102.
    """
    print("\n── bd_condicion_climatica ──")
    if not download_gpkg(token, project_id, 'BD_CondicionClimatica.gpkg', '/tmp/climatica.gpkg'):
        return
    gdf = read_layer('/tmp/climatica.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_condicion_climatica')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
            'folio':         safe(row.get('folio')),
            'estado_clima':  safe(row.get('estado_clima') or row.get('estadoclima')),
            'hora':          safe(row.get('hora')),
            'observaciones': safe(row.get('observaciones')),
            'longitud':      lon,
            'latitud':       lat,
        }
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_condicion_climatica').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_maquinaria(supabase, token, project_id):
    """
    [D-06] Nombres con paréntesis corregidos. Estructura constante para evitar PGRST102.
    """
    print("\n── bd_maquinaria_obra ──")
    if not download_gpkg(token, project_id, 'BD_MaquinariaObra.gpkg', '/tmp/maquinaria.gpkg'):
        return
    gdf = read_layer('/tmp/maquinaria.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_maquinaria_obra')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
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
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_maquinaria_obra').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_bd_sst(supabase, token, project_id):
    """
    [D-07] Layer 'BBD_SST-Ambiental' (doble B — nombre real del GPKG).
    Estructura constante para evitar PGRST102.
    """
    print("\n── bd_sst_ambiental ──")
    if not download_gpkg(token, project_id, 'BD_SST-Ambiental.gpkg', '/tmp/sst.gpkg'):
        return
    gdf = read_layer('/tmp/sst.gpkg', 'BBD_SST-Ambiental')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'bd_sst_ambiental')

    rows = []
    for _, row in gdf.iterrows():
        lat, lon = coords_from_geom(row)
        data = {
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
        if data.get('folio'):
            rows.append(data)

    if rows:
        supabase.table('bd_sst_ambiental').insert(rows).execute()
    print(f"  → {len(rows)} insertados")
