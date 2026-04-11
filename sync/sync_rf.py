from .utils import safe
from .gpkg import download_gpkg, read_layer, delete_all


def _valid_ids(supabase, table, column='id_unico'):
    """Devuelve el conjunto de valores existentes en table.column."""
    result = supabase.table(table).select(column).execute()
    return {r[column] for r in result.data if r.get(column)}


def sync_rf_cantidades(supabase, token, project_id):
    print("\n── rf_cantidades ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    delete_all(supabase, 'rf_cantidades')

    # Solo insertar filas cuyo id_unico exista en registros_cantidades (FK)
    valid = _valid_ids(supabase, 'registros_cantidades')

    rows = []
    omitidos = 0
    for _, row in gdf.iterrows():
        data = {
            'folio':             safe(row.get('folio')),
            'id_unico':          safe(row.get('id_unico')),
            'observacion':       safe(row.get('observacion')),
            'nombre_foto':       safe(row.get('nombre_foto')),
            'ruta_destino_foto': safe(row.get('ruta_destino_foto')),
        }
        if not data.get('id_unico'):
            continue
        if data['id_unico'] not in valid:
            print(f"  ⚠ id_unico {data['id_unico']} no existe en registros_cantidades — omitido")
            omitidos += 1
            continue
        rows.append(data)

    if rows:
        supabase.table('rf_cantidades').insert(rows).execute()
    print(f"  → {len(rows)} insertados · {omitidos} omitidos por FK")


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
        data = {
            'folio':         safe(row.get('folio')),
            'id_unico':      safe(row.get('id_unico')),
            'observaciones': safe(row.get('observaciones')),
            'foto':          safe(row.get('foto')),
        }
        if data.get('id_unico'):
            rows.append(data)

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
        data = {
            'folio':         safe(row.get('folio')),
            'id_unico':      safe(row.get('id_unico')),
            'observaciones': safe(row.get('observaciones')),
            'foto':          safe(row.get('foto')),
        }
        if data.get('id_unico'):
            rows.append(data)

    if rows:
        supabase.table('rf_reporte_diario').insert(rows).execute()
    print(f"  → {len(rows)} insertados")
