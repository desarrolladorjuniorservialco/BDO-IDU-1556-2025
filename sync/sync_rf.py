from .config import CONTRATO_ID
from .utils import safe
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo


def _fetch_existing_ids(supabase, tabla: str) -> set:
    """Descarga todos los id_unico del contrato actual en la tabla dada."""
    existentes = set()
    try:
        offset, chunk = 0, 1000
        while True:
            resp = (supabase.table(tabla)
                    .select('id_unico')
                    .eq('contrato_id', CONTRATO_ID)
                    .range(offset, offset + chunk - 1)
                    .execute())
            batch = resp.data or []
            existentes.update(row['id_unico'] for row in batch if row.get('id_unico'))
            if len(batch) < chunk:
                break
            offset += chunk
        print(f"  · {len(existentes)} IDs existentes en {tabla}")
    except Exception as e:
        print(f"  ⚠ No se pudo obtener registros existentes de {tabla}: {e}")
    return existentes


def _es_duplicado(exc: Exception) -> bool:
    s = str(exc).lower()
    return '23505' in s or 'duplicate' in s or 'unique' in s


def _sync_rf_table(supabase, token, project_id, table, gpkg_file, tmp_path, build_row):
    """Inserta registros fotográficos nuevos (omite los ya existentes por id_unico)."""
    print(f"\n── {table} ──")
    if not download_gpkg(token, project_id, gpkg_file, tmp_path):
        return
    gdf = read_layer(tmp_path)
    if gdf is None or gdf.empty:
        return

    existentes = _fetch_existing_ids(supabase, table)
    insertados = saltados = errores = 0

    for _, row in gdf.iterrows():
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue
        if id_unico in existentes:
            saltados += 1
            continue

        folio            = safe(row.get('folio'))
        data, foto_path  = build_row(row)
        foto_url         = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        data.update({
            'contrato_id': CONTRATO_ID,
            'folio':       folio,
            'id_unico':    id_unico,
            'foto_url':    foto_url,
        })

        try:
            supabase.table(table).insert(data).execute()
            insertados += 1
        except Exception as e:
            if _es_duplicado(e):
                saltados += 1
            else:
                errores += 1
                print(f"  ✗ {id_unico}: {e}")

    print(f"  → {insertados} insertados · {saltados} ya existían · {errores} errores")


def sync_rf_cantidades(supabase, token, project_id):
    def _row(row):
        ruta = safe(row.get('ruta_destino_foto'))
        return (
            {'observacion': safe(row.get('observacion')), 'nombre_foto': safe(row.get('nombre_foto')), 'ruta_destino_foto': ruta},
            ruta,
        )
    _sync_rf_table(supabase, token, project_id,
                   'rf_cantidades', 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg', _row)


def sync_rf_componentes(supabase, token, project_id):
    def _row(row):
        foto = safe(row.get('foto'))
        return ({'observaciones': safe(row.get('observaciones')), 'foto': foto}, foto)
    _sync_rf_table(supabase, token, project_id,
                   'rf_componentes', 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg', _row)


def sync_rf_reporte_diario(supabase, token, project_id):
    def _row(row):
        foto = safe(row.get('foto'))
        return ({'observaciones': safe(row.get('observaciones')), 'foto': foto}, foto)
    _sync_rf_table(supabase, token, project_id,
                   'rf_reporte_diario', 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg', _row)
