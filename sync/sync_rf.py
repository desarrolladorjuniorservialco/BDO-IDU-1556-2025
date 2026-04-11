from .utils import safe
from .gpkg import download_gpkg, read_layer, delete_all
from .photos import upload_photo


def sync_rf_cantidades(supabase, token, project_id):
    print("\n── rf_cantidades ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_cantidades')

    rows = []
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        ruta = safe(row.get('ruta_destino_foto'))
        foto_url = upload_photo(supabase, token, project_id, ruta, folio) if ruta else None

        data = {
            'folio':             folio,
            'id_unico':          id_unico,
            'observacion':       safe(row.get('observacion')),
            'nombre_foto':       safe(row.get('nombre_foto')),
            'ruta_destino_foto': ruta,
            'foto_url':          foto_url,
        }
        rows.append({k: v for k, v in data.items() if v is not None})

    if rows:
        supabase.table('rf_cantidades').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_componentes(supabase, token, project_id):
    print("\n── rf_componentes ──")
    if not download_gpkg(token, project_id, 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg'):
        return
    gdf = read_layer('/tmp/rf_componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_componentes')

    rows = []
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        data = {
            'folio':         folio,
            'id_unico':      id_unico,
            'observaciones': safe(row.get('observaciones')),
            'foto':          foto_path,
            'foto_url':      foto_url,
        }
        rows.append({k: v for k, v in data.items() if v is not None})

    if rows:
        supabase.table('rf_componentes').insert(rows).execute()
    print(f"  → {len(rows)} insertados")


def sync_rf_reporte_diario(supabase, token, project_id):
    print("\n── rf_reporte_diario ──")
    if not download_gpkg(token, project_id, 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/rf_reporte_diario.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_reporte_diario')

    rows = []
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        data = {
            'folio':         folio,
            'id_unico':      id_unico,
            'observaciones': safe(row.get('observaciones')),
            'foto':          foto_path,
            'foto_url':      foto_url,
        }
        rows.append({k: v for k, v in data.items() if v is not None})

    if rows:
        supabase.table('rf_reporte_diario').insert(rows).execute()
    print(f"  → {len(rows)} insertados")
