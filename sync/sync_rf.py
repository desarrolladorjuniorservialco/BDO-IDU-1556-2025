"""
sync_rf.py — Sincronización de registros fotográficos (RF)

Estrategia por registro:
  - Si id_unico ya existe en la tabla RF → se salta (no re-sube la foto).
  - Si no existe → se sube la foto y se inserta la fila.

Esto evita re-subir fotos de registros ya aprobados/inmutables
y elimina la necesidad de delete_all() previo.
"""

from .utils import safe
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo


def _upsert_rf(supabase, tabla: str, id_unico: str, row_data: dict) -> str:
    """
    Inserta fila si id_unico no existe; la salta si ya existe.
    Devuelve 'insertado' | 'saltado' | 'error'.
    """
    try:
        chk = supabase.table(tabla).select('id_unico')\
                      .eq('id_unico', id_unico).execute()
        if chk.data:
            return 'saltado'
        supabase.table(tabla).insert(row_data).execute()
        return 'insertado'
    except Exception as e:
        return f'error: {e}'


def sync_rf_cantidades(supabase, token, project_id):
    print("\n── rf_cantidades ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        ruta     = safe(row.get('ruta_destino_foto'))
        foto_url = upload_photo(supabase, token, project_id, ruta, folio) if ruta else None

        resultado = _upsert_rf(supabase, 'rf_cantidades', id_unico, {
            'folio':             folio,
            'id_unico':          id_unico,
            'observacion':       safe(row.get('observacion')),
            'nombre_foto':       safe(row.get('nombre_foto')),
            'ruta_destino_foto': ruta,
            'foto_url':          foto_url,
        })

        if resultado == 'insertado':
            insertados += 1
        elif resultado == 'saltado':
            saltados += 1
        else:
            errores += 1
            print(f"  ✗ {id_unico}: {resultado}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")


def sync_rf_componentes(supabase, token, project_id):
    print("\n── rf_componentes ──")
    if not download_gpkg(token, project_id, 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg'):
        return
    gdf = read_layer('/tmp/rf_componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio     = safe(row.get('folio'))
        id_unico  = safe(row.get('id_unico'))
        if not id_unico:
            continue

        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        resultado = _upsert_rf(supabase, 'rf_componentes', id_unico, {
            'folio':         folio,
            'id_unico':      id_unico,
            'observaciones': safe(row.get('observaciones')),
            'foto':          foto_path,
            'foto_url':      foto_url,
        })

        if resultado == 'insertado':
            insertados += 1
        elif resultado == 'saltado':
            saltados += 1
        else:
            errores += 1
            print(f"  ✗ {id_unico}: {resultado}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")


def sync_rf_reporte_diario(supabase, token, project_id):
    print("\n── rf_reporte_diario ──")
    if not download_gpkg(token, project_id, 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/rf_reporte_diario.gpkg')
    if gdf is None or gdf.empty:
        return

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio     = safe(row.get('folio'))
        id_unico  = safe(row.get('id_unico'))
        if not id_unico:
            continue

        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        resultado = _upsert_rf(supabase, 'rf_reporte_diario', id_unico, {
            'folio':         folio,
            'id_unico':      id_unico,
            'observaciones': safe(row.get('observaciones')),
            'foto':          foto_path,
            'foto_url':      foto_url,
        })

        if resultado == 'insertado':
            insertados += 1
        elif resultado == 'saltado':
            saltados += 1
        else:
            errores += 1
            print(f"  ✗ {id_unico}: {resultado}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")
