from .config import CONTRATO_ID
from .utils import safe
from .gpkg import download_gpkg, read_layer

_INFRA_NOMBRE_A_CODIGO = {
    'espacio público': 'EP',
    'espacio publico': 'EP',
    'ep':              'EP',
    'ciclorruta':      'CI',
    'cicloruta':       'CI',
    'ci':              'CI',
    'malla vial':      'MV',
    'mv':              'MV',
}


def _infra_a_codigo(valor):
    if not valor:
        return None
    key = str(valor).strip().lower()
    return _INFRA_NOMBRE_A_CODIGO.get(key, str(valor).strip())


def sync_tramos_aux_infra(supabase, token, project_id):
    print("\n── tramos_aux_infra ──")
    tmp = '/tmp/tramos_bd.gpkg'
    if not download_gpkg(token, project_id, 'BD_Tramos.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    pares = {}
    for _, row in gdf.iterrows():
        nombre = safe(row.get('infraestructura'))
        if nombre:
            codigo = _infra_a_codigo(nombre)
            if codigo:
                pares[codigo] = nombre

    count = 0
    for codigo, nombre in sorted(pares.items()):
        try:
            supabase.table('tramos_aux_infra').upsert(
                {'contrato_id': CONTRATO_ID, 'codigo': codigo, 'nombre': nombre},
                on_conflict='contrato_id,codigo'
            ).execute()
            count += 1
            print(f"  · {codigo} → {nombre}")
        except Exception as e:
            print(f"  ⚠ ({codigo}, {nombre}): {e}")
    print(f"  → {count} upserted")


def sync_tramos_aux_tramos(supabase, token, project_id):
    print("\n── tramos_aux_tramos ──")
    tmp = '/tmp/tramos_aux_tramos.gpkg'
    if not download_gpkg(token, project_id, 'AUX_Tramos.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    count = errores = 0
    for _, row in gdf.iterrows():
        codigo = safe(row.get('codigo'))
        descripcion = safe(row.get('descripcion'))
        if not codigo or not descripcion:
            continue
        try:
            supabase.table('tramos_aux_tramos').upsert(
                {'contrato_id': CONTRATO_ID, 'codigo': codigo, 'descripcion': descripcion},
                on_conflict='contrato_id,codigo'
            ).execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ⚠ '{codigo}': {e}")
    print(f"  → {count} upserted · {errores} errores")


def sync_presupuesto_aux_actividad(supabase, token, project_id):
    print("\n── presupuesto_aux_actividad ──")
    tmp = '/tmp/presupuesto_bd.gpkg'
    if not download_gpkg(token, project_id, 'BD_Presupuesto.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    valores = {safe(row.get('tipo_actividad')) for _, row in gdf.iterrows()} - {None}
    count = 0
    for v in sorted(valores):
        try:
            supabase.table('presupuesto_aux_actividad').upsert(
                {'contrato_id': CONTRATO_ID, 'tipo_actividad': v},
                on_conflict='contrato_id,tipo_actividad'
            ).execute()
            count += 1
        except Exception as e:
            print(f"  ⚠ '{v}': {e}")
    print(f"  → {count} upserted: {sorted(valores)}")


def sync_presupuesto_aux_capitulos(supabase, token, project_id):
    print("\n── presupuesto_aux_capitulos ──")
    tmp = '/tmp/presupuesto_aux_cap.gpkg'
    if not download_gpkg(token, project_id, 'AUX_Capitulos.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    count = errores = 0
    for _, row in gdf.iterrows():
        tipo = safe(row.get('tipo_actividad'))
        cap_num = safe(row.get('capitulo_num'))
        capitulo = safe(row.get('capitulo'))
        if not tipo or not cap_num:
            continue
        try:
            supabase.table('presupuesto_aux_capitulos').upsert(
                {'contrato_id': CONTRATO_ID, 'tipo_actividad': tipo,
                 'capitulo_num': cap_num, 'capitulo': capitulo},
                on_conflict='contrato_id,tipo_actividad,capitulo_num'
            ).execute()
            count += 1
        except Exception as e:
            errores += 1
            print(f"  ⚠ ({tipo}, {cap_num}): {e}")
    print(f"  → {count} upserted · {errores} errores")
