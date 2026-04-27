from .utils import safe, safe_num, coords_from_geom
from .gpkg import download_gpkg, read_layer
from .photos import upload_photo
from .config import CONTRATO_ID


def sync_registros_cantidades(supabase, token, project_id):
    print("\n── registros_cantidades ──")
    if not download_gpkg(token, project_id, 'Formulario_Cantidades.gpkg', '/tmp/cantidades.gpkg'):
        return
    gdf = read_layer('/tmp/cantidades.gpkg', 'Formulario_Cantidades')
    if gdf is None or gdf.empty:
        return

    nuevos = omitidos = errores = 0
    for idx, (_, row) in enumerate(gdf.iterrows()):
        folio = safe(row.get('folio'))
        if not folio:
            omitidos += 1
            continue

        # id_unico: usar valor del GPKG si es válido, sino folio__fid o folio__idx
        id_unico_raw = safe(row.get('id_unico'))
        fid_val      = safe(row.get('fid'))
        if id_unico_raw and id_unico_raw != 'folio':
            id_unico = id_unico_raw
        elif fid_val:
            id_unico = f"{folio}__{fid_val}"
        else:
            id_unico = f"{folio}__{idx}"

        lat, lon = coords_from_geom(row)

        doc_path = safe(row.get('documento_adj'))
        doc_url  = upload_photo(supabase, token, project_id, doc_path, folio) if doc_path else None

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
            'documento_adj_path':        doc_path,
            'documento_adj_url':         doc_url,
            'observaciones':             safe(row.get('observaciones')),
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor') or row.get('acompañamiento interventor')),
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            chk = (supabase.table('registros_cantidades').select('inmutable')
                   .eq('contrato_id', CONTRATO_ID).eq('id_unico', id_unico).execute())
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                print(f"  ⊘ {folio} (inmutable, saltado)")
                continue
            supabase.table('registros_cantidades').upsert(data, on_conflict='contrato_id,id_unico').execute()
            nuevos += 1
            print(f"  ✓ {folio}")
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {nuevos} upserted · {omitidos} sin folio/id_unico · {errores} errores")


def sync_registros_componentes(supabase, token, project_id):
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
            'codigointerventor':         safe(row.get('codigo_interventor') or row.get('codigointerventor')),
            'acompañamientointerventor': safe(row.get('acompañamiento_interventor') or row.get('acompañamiento interventor')),
            'qfield_sync_id':            safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            chk = (supabase.table('registros_componentes').select('inmutable')
                   .eq('contrato_id', CONTRATO_ID).eq('folio', folio).execute())
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                continue
            supabase.table('registros_componentes').upsert(data, on_conflict='contrato_id,folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")


def sync_registros_reporte_diario(supabase, token, project_id):
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

        # id_unico: usar valor del GPKG si es válido, sino folio__pk_id o folio__idx
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
            # 'feca_reporte' es typo real en el GPKG; el OR cubre si lo corrigen
            'fecha_reporte':  safe(row.get('feca_reporte') or row.get('fecha_reporte')),
            'observaciones':  safe(row.get('observaciones')),
            'qfield_sync_id': safe(row.get('fid')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        try:
            chk = (supabase.table('registros_reporte_diario').select('inmutable')
                   .eq('contrato_id', CONTRATO_ID).eq('id_unico', id_unico).execute())
            if chk.data and chk.data[0].get('inmutable'):
                omitidos += 1
                continue
            supabase.table('registros_reporte_diario').upsert(data, on_conflict='contrato_id,id_unico').execute()
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
            supabase.table('formulario_pmt').upsert(data, on_conflict='contrato_id,folio').execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ✗ {folio}: {e}")

    print(f"  → {count} upserted · {omitidos} sin folio · {errores} errores")
