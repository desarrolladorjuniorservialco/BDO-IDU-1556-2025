from .utils import safe, safe_num, coords_from_geom
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo
from .config import CONTRATO_ID


def sync_registros_cantidades(supabase, token, project_id):
    """
    [D-01] Columnas corregidas:
      · foto_1…foto_5 NO existen en el GPKG (van en RF_Cantidades.gpkg)
      · fecha_inicio / fecha_fin no existen → 'fecha' se mapea a fecha_inicio
      · codigo_interventor (GPKG) → codigointerventor (Supabase)
      · acompañamiento_interventor (GPKG) → acompañamientointerventor (Supabase)
    [BUG-PY-001] 'estado' eliminado para no sobreescribir registros aprobados.
    [FIX-FK-001] on_conflict='id_unico' en lugar de 'folio':
                 el GPKG puede tener varios items con el mismo folio pero distinto
                 id_unico. Al upsertear sobre folio el segundo item sobreescribía
                 el id_unico del primero, causando la violación de FK 23503 en
                 rf_cantidades (rf_cantidades_id_unico_fkey).
    """
    print("\n── registros_cantidades ──")
    if not download_gpkg(token, project_id, 'Formulario_Cantidades.gpkg', '/tmp/cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/cantidades.gpkg', 'Formulario_Cantidades_V2')
    if gdf is None or gdf.empty:
        return

    nuevos = omitidos = errores = 0
    for idx, (_, row) in enumerate(gdf.iterrows()):
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        # [FIX-CAN-001] Fallback id_unico igual que reporte_diario: si el GPKG
        # devuelve null o la cadena literal 'folio' (error de config QField),
        # se genera folio__fid o folio__idx en lugar de omitir la fila.
        id_unico_raw = safe(row.get('id_unico'))
        fid_val      = safe(row.get('fid'))
        if id_unico_raw and id_unico_raw != 'folio':
            id_unico = id_unico_raw
        elif fid_val:
            id_unico = f"{folio}__{fid_val}"
        else:
            id_unico = f"{folio}__{idx}"

        lat, lon = coords_from_geom(row)

        doc_url = None
        doc_path = safe(row.get('documento_adj'))
        if doc_path:
            doc_url = upload_photo(supabase, token, project_id, doc_path, folio)

        data = {
            'folio':                     str(folio),
            'id_unico':                  id_unico,
            'contrato_id':               CONTRATO_ID,
            'usuario_qfield':            safe(row.get('usuario')),
            'tipo_infra':                safe(row.get('tipo_infra')),
            'id_tramo':                  safe(row.get('id_tramo')),
            'tramo_descripcion':         safe(row.get('tramo_descripcion')),
            'civ':                       safe(row.get('civ')),
            'codigo_elemento':           safe(row.get('codigo_elemento')),
            'latitud':                   lat,
            'longitud':                  lon,
            # [D-01] 'fecha' → fecha_inicio; fecha_fin no existe en GPKG
            'fecha_inicio':              safe(row.get('fecha_inicio') or row.get('fecha')),
            'fecha_fin':                 safe(row.get('fecha_fin')),
            'tipo_actividad':            safe(row.get('tipo_actividad')),
            'capitulo_num':              safe(row.get('capitulo_num')),
            'capitulo':                  safe(row.get('capitulo')),
            'item_pago':                 safe(row.get('item_pago')),
            'item_descripcion':          safe(row.get('item_descripcion')),
            'unidad':                    safe(row.get('unidad')),
            'cantidad':                  safe_num(row.get('cantidad')),
            'descripcion':               safe(row.get('descripcion')),
            # [D-01] foto_1…foto_5 no existen; solo documento_adj
            'documento_adj_path':        doc_path,
            'documento_adj_url':         doc_url,
            'observaciones':             safe(row.get('observaciones')),
            # [D-01] columna real: 'codigo_interventor'
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            # [D-01] columna real: 'acompañamiento_interventor'
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor')
                                             or row.get('acompañamiento interventor')),
            # [BUG-PY-001] sin 'estado': DEFAULT 'BORRADOR' aplica solo en INSERT
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            # [FIX-INM-002] .eq() no es soportado después de .upsert() en supabase-py.
            # Se hace un SELECT previo para verificar inmutabilidad antes de upsertear.
            chk = supabase.table('registros_cantidades').select('inmutable')\
                          .eq('id_unico', id_unico).execute()
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                print(f"  ⊘ {folio} (inmutable, saltado)")
                continue
            # [FIX-FK-001] upsert por id_unico para preservar todos los items del mismo folio
            supabase.table('registros_cantidades').upsert(
                data, on_conflict='id_unico'
            ).execute()
            nuevos += 1
            print(f"  ✓ {folio}")
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {nuevos} upserted · {omitidos} sin folio/id_unico · {errores} errores")


def sync_registros_componentes(supabase, token, project_id):
    """
    [D-02] Layer real: 'PMT - Plan de Manejo del Transito'.
    gpd lee la primera capa sin necesidad de especificar layer_name.
    """
    print("\n── registros_componentes ──")
    if not download_gpkg(token, project_id, 'Reporte_Componentes.gpkg', '/tmp/componentes.gpkg'):
        return
    gdf = read_layer('/tmp/componentes.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'folio':                     str(folio),
            'id_unico':                  safe(row.get('id_unico')),
            'contrato_id':               CONTRATO_ID,
            'usuario_qfield':            safe(row.get('usuario')),
            'id_tramo':                  safe(row.get('id_tramo')),
            'tramo':                     safe(row.get('tramo')),
            'civ':                       safe(row.get('civ')),
            'codigo_elemento':           safe(row.get('codigo_elemento')),
            'tipo_infra':                safe(row.get('tipo_infra')),
            'componente':                safe(row.get('componente')),
            'latitud':                   lat,
            'longitud':                  lon,
            'fecha':                     safe(row.get('fecha')),
            'fecha_reporte':             safe(row.get('fecha_reporte')),
            'tipo_actividad':            safe(row.get('tipo_actividad')),
            'capitulo_num':              safe(row.get('capitulo_num')),
            'capitulo':                  safe(row.get('capitulo')),
            'item_pago':                 safe(row.get('item_pago')),
            'item_descripcion':          safe(row.get('item_descripcion')),
            'cantidad':                  safe_num(row.get('cantidad')),
            'unidad':                    safe(row.get('unidad')),
            'precio_unitario':           safe_num(row.get('precio_unitario')),
            'observaciones':             safe(row.get('observaciones')),
            'profesional':               safe(row.get('profesional')),
            # [D-02] columna real: 'codigo_interventor'
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            # [D-02] columna real: 'acompañamiento_interventor'
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor')
                                             or row.get('acompañamiento interventor')),
            # [BUG-PY-001] sin 'estado'
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            # [FIX-INM-002] SELECT previo para verificar inmutabilidad
            chk = supabase.table('registros_componentes').select('inmutable')\
                          .eq('folio', folio).execute()
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                continue
            supabase.table('registros_componentes').upsert(
                data, on_conflict='folio'
            ).execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


def sync_registros_reporte_diario(supabase, token, project_id):
    """
    [D-03] TYPO en GPKG: 'feca_reporte' en lugar de 'fecha_reporte'.
    Se lee con OR para cubrir cuando lo corrijan en QField.
    [FIX-RD-002] El GPKG tiene múltiples filas por folio (una por elemento
    pk_id/civ). Se usa on_conflict='id_unico' para almacenar todos los ítems.
    id_unico se deriva de folio__pk_id cuando el GPKG no provee un valor válido
    (null o la cadena literal 'folio' por error de configuración en QField).
    [PATCH-006] requiere que registros_reporte_diario.folio NO tenga UNIQUE.
    Ejecutar 006_FIX_REPORTE_DIARIO_MULTI_ITEM.sql en Supabase antes de esto.
    """
    print("\n── registros_reporte_diario ──")
    if not download_gpkg(token, project_id, 'Reporte_Diario.gpkg', '/tmp/reporte_diario.gpkg'):
        return
    gdf = read_layer('/tmp/reporte_diario.gpkg', 'Reporte_Diario')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for idx, (_, row) in enumerate(gdf.iterrows()):
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        # [FIX-RD-002] Generar id_unico robusto:
        # 1. Usar el valor del GPKG si es válido (no nulo, no la cadena 'folio')
        # 2. Si pk_id está disponible: folio__pk_id  (único entre ítems del mismo folio)
        # 3. Fallback: folio__idx  (índice de la fila en el GeoDataFrame, siempre único)
        id_unico_raw = safe(row.get('id_unico'))
        pk_val       = safe(row.get('pk_id'))
        if id_unico_raw and id_unico_raw != 'folio':
            id_unico = id_unico_raw
        elif pk_val:
            id_unico = f"{folio}__{pk_val}"
        else:
            id_unico = f"{folio}__{idx}"

        data = {
            'folio':          str(folio),
            'id_unico':       id_unico,
            'contrato_id':    CONTRATO_ID,
            'usuario_qfield': safe(row.get('usuario')),
            'latitud':        lat,
            'longitud':       lon,
            'fecha':          safe(row.get('fecha')),
            'id_tramo':       safe(row.get('tramo_id')),
            'civ':            safe(row.get('civ')),
            'pk_id':          pk_val,
            'cantidad':       safe_num(row.get('cantidad')),
            'unidad':         safe(row.get('unidad')),
            # [D-03] typo real en GPKG: 'feca_reporte'; OR cubre corrección futura
            'fecha_reporte':  safe(row.get('feca_reporte') or row.get('fecha_reporte')),
            'observaciones':  safe(row.get('observaciones')),
            # [BUG-PY-001] sin 'estado'
            'qfield_sync_id': safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            # [FIX-INM-002] SELECT previo para verificar inmutabilidad (por id_unico)
            chk = supabase.table('registros_reporte_diario').select('inmutable')\
                          .eq('id_unico', id_unico).execute()
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                continue
            # [FIX-RD-002] upsert por id_unico para preservar todos los ítems del folio
            supabase.table('registros_reporte_diario').upsert(
                data, on_conflict='id_unico'
            ).execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio} ({id_unico}): {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


def sync_formulario_pmt(supabase, token, project_id):
    print("\n── formulario_pmt ──")
    if not download_gpkg(token, project_id, 'Formulario_PMT.gpkg', '/tmp/pmt.gpkg'):
        return
    gdf = read_layer('/tmp/pmt.gpkg')
    if gdf is None or gdf.empty:
        return

    count = omitidos = errores = 0
    for _, row in gdf.iterrows():
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        lat, lon = coords_from_geom(row)

        data = {
            'folio':           str(folio),
            'contrato_id':     CONTRATO_ID,
            'descripcion':     safe(row.get('descripcion')),
            'civ':             safe(row.get('civ')),
            'inicio_vigencia': safe(row.get('inicio_vigencia')),
            'fin_vigencia':    safe(row.get('fin_vigencia')),
            'usuario':         safe(row.get('usuario')),
            'latitud':         lat,
            'longitud':        lon,
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            supabase.table('formulario_pmt').upsert(data, on_conflict='folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")
