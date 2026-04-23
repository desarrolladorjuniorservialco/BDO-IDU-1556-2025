"""
sync_rf.py — Sincronización de registros fotográficos (RF)

Estrategia incremental (evita reprocesos):
  1. Al inicio de cada función se hace UN SOLO SELECT para obtener los
     id_unico ya existentes en Supabase (ventana incremental o full).
  2. Registros ya existentes se saltan SIN descargar ni comprimir la foto.
  3. Solo registros NUEVOS pasan por upload_photo() + INSERT.
  4. En modo incremental, registros fuera de la ventana se re-intentan;
     si ya existen (violación UNIQUE), se ignoran silenciosamente.

MODO INCREMENTAL — cómo deshabilitar
──────────────────────────────────────
Si necesitas regenerar la BD desde cero o forzar re-sync completo:
  · Cambia USE_INCREMENTAL_RF = False   (consulta TODOS los IDs existentes)
  · O amplía SINCE_DAYS a un valor mayor que la vida del proyecto.
Vuelve a True cuando termines para recuperar la velocidad normal.
"""

from datetime import datetime, timedelta

from .utils import safe
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INCREMENTAL
# ═══════════════════════════════════════════════════════════════════════════════
USE_INCREMENTAL_RF = True   # False → full sync (necesario al regenerar la BD)
SINCE_DAYS         = 7      # Ventana de IDs recientes que se consultan en Supabase
# ═══════════════════════════════════════════════════════════════════════════════


def _fetch_existing_ids(supabase, tabla: str) -> set:
    """
    Descarga id_unico existentes en 'tabla'.
    Incremental: solo los últimos SINCE_DAYS días (más rápido con datos históricos).
    Full (USE_INCREMENTAL_RF=False): todos los registros sin filtro de fecha.
    Devuelve set vacío si falla → intentará insertar todo el GPKG.
    """
    existentes = set()
    try:
        offset = 0
        chunk  = 1000
        since  = None
        if USE_INCREMENTAL_RF:
            since = (datetime.utcnow() - timedelta(days=SINCE_DAYS)).isoformat()
        while True:
            q = supabase.table(tabla).select('id_unico')
            if since:
                q = q.gte('created_at', since)
            resp  = q.range(offset, offset + chunk - 1).execute()
            batch = resp.data or []
            for row in batch:
                uid = row.get('id_unico')
                if uid:
                    existentes.add(uid)
            if len(batch) < chunk:
                break
            offset += chunk
        modo = f"incremental ({SINCE_DAYS}d)" if since else "full"
        print(f"  · {len(existentes)} IDs existentes en {tabla} [{modo}]")
    except Exception as e:
        print(f"  ⚠ No se pudo obtener registros existentes de {tabla}: {e}")
    return existentes


def _es_duplicado(exc: Exception) -> bool:
    """Detecta violación de restricción UNIQUE (código PG 23505)."""
    s = str(exc).lower()
    return '23505' in s or 'duplicate' in s or 'unique' in s


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
            if _es_duplicado(e):
                saltados += 1   # fuera de ventana incremental, ya existía
            else:
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
            if _es_duplicado(e):
                saltados += 1
            else:
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
            if _es_duplicado(e):
                saltados += 1
            else:
                errores += 1
                print(f"  ✗ {id_unico}: {e}")

    print(f"  → {insertados} insertados · {saltados} ya existían (saltados) · {errores} errores")
