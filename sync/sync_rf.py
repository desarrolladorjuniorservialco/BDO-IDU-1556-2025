"""
sync_rf.py — Sincronización de registros fotográficos (RF)

Estrategia incremental (evita reprocesos):
  1. Al inicio de cada función se hace UN SOLO SELECT para obtener todos los
     id_unico ya existentes en Supabase → O(1) en vez de O(N) queries.
  2. Registros ya existentes se saltan SIN descargar, comprimir ni intentar
     subir la foto (elimina errores "Duplicate" y carga computacional inútil).
  3. Solo registros NUEVOS pasan por upload_photo() + INSERT.

Comparado con la versión anterior:
  Antes : N foto-compressions + N upload-attempts + N SELECT individuales
  Ahora : 1 SELECT batch + K foto-compressions + K INSERTs  (K = registros nuevos)
"""

from .utils import safe
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo


def _fetch_existing_ids(supabase, tabla: str) -> set:
    """
    Descarga todos los id_unico existentes en 'tabla' en una sola query.
    Soporta tablas con más de 1 000 filas mediante paginación automática.
    Devuelve un set vacío si falla (comportamiento conservador: intentará
    insertar todos los registros del GPKG).
    """
    existentes = set()
    try:
        offset = 0
        chunk  = 1000
        while True:
            resp = (
                supabase.table(tabla)
                .select('id_unico')
                .range(offset, offset + chunk - 1)
                .execute()
            )
            batch = resp.data or []
            for row in batch:
                uid = row.get('id_unico')
                if uid:
                    existentes.add(uid)
            if len(batch) < chunk:
                break
            offset += chunk
    except Exception as e:
        print(f"  ⚠ No se pudo obtener registros existentes de {tabla}: {e}")
    return existentes


# ── rf_cantidades ──────────────────────────────────────────────────────────────

def sync_rf_cantidades(supabase, token, project_id):
    print("\n── rf_cantidades ──")
    if not download_gpkg(token, project_id, 'RF_Cantidades.gpkg', '/tmp/rf_cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/rf_cantidades.gpkg')
    if gdf is None or gdf.empty:
        return

    # Pre-fetch incremental: 1 query para toda la tabla
    existentes = _fetch_existing_ids(supabase, 'rf_cantidades')

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        # Saltar sin tocar la foto si el registro ya existe
        if id_unico in existentes:
            saltados += 1
            continue

        # Solo para registros NUEVOS: descargar y subir foto
        ruta     = safe(row.get('ruta_destino_foto'))
        foto_url = upload_photo(supabase, token, project_id, ruta, folio) if ruta else None

        try:
            supabase.table('rf_cantidades').insert({
                'folio':             folio,
                'id_unico':          id_unico,
                'observacion':       safe(row.get('observacion')),
                'nombre_foto':       safe(row.get('nombre_foto')),
                'ruta_destino_foto': ruta,
                'foto_url':          foto_url,
            }).execute()
            insertados += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {id_unico}: {e}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")


# ── rf_componentes ─────────────────────────────────────────────────────────────

def sync_rf_componentes(supabase, token, project_id):
    print("\n── rf_componentes ──")
    if not download_gpkg(token, project_id, 'RF_Componentes.gpkg', '/tmp/rf_componentes.gpkg'):
        return
    gdf = read_layer('/tmp/rf_componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    existentes = _fetch_existing_ids(supabase, 'rf_componentes')

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        if id_unico in existentes:
            saltados += 1
            continue

        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        try:
            supabase.table('rf_componentes').insert({
                'folio':         folio,
                'id_unico':      id_unico,
                'observaciones': safe(row.get('observaciones')),
                'foto':          foto_path,
                'foto_url':      foto_url,
            }).execute()
            insertados += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {id_unico}: {e}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")


# ── rf_reporte_diario ──────────────────────────────────────────────────────────

def sync_rf_reporte_diario(supabase, token, project_id):
    print("\n── rf_reporte_diario ──")
    if not download_gpkg(token, project_id, 'RF_ReporteDiario.gpkg', '/tmp/rf_reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/rf_reporte_diario.gpkg')
    if gdf is None or gdf.empty:
        return

    # Pre-fetch incremental: 1 query para toda la tabla
    existentes = _fetch_existing_ids(supabase, 'rf_reporte_diario')

    insertados = saltados = errores = 0
    for _, row in gdf.iterrows():
        folio    = safe(row.get('folio'))
        id_unico = safe(row.get('id_unico'))
        if not id_unico:
            continue

        # Saltar sin tocar la foto si el registro ya existe
        if id_unico in existentes:
            saltados += 1
            continue

        # Solo para registros NUEVOS: descargar y subir foto
        foto_path = safe(row.get('foto'))
        foto_url  = upload_photo(supabase, token, project_id, foto_path, folio) if foto_path else None

        try:
            supabase.table('rf_reporte_diario').insert({
                'folio':         folio,
                'id_unico':      id_unico,
                'observaciones': safe(row.get('observaciones')),
                'foto':          foto_path,
                'foto_url':      foto_url,
            }).execute()
            insertados += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {id_unico}: {e}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")
