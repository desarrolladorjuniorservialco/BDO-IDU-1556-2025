from .config import CONTRATO_ID
from .utils import safe, safe_num
from .gpkg import download_gpkg, read_layer


def sync_presupuesto_bd(supabase, token, project_id):
    print("\n── presupuesto_bd ──")
    if not download_gpkg(token, project_id, 'BD_Presupuesto.gpkg', '/tmp/presupuesto_bd.gpkg'):
        return
    gdf = read_layer('/tmp/presupuesto_bd.gpkg')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'contrato_id':    CONTRATO_ID,
            'tipo_actividad': safe(row.get('tipo_actividad')),
            'capitulo_num':   safe(row.get('capitulo_num')),
            'capitulo':       safe(row.get('capitulo')),
            'codigo_idu':     safe(row.get('codigo_idu')),
            'item_pago':      safe(row.get('item_pago')),
            'descripcion':    safe(row.get('descripcion')),
            'unidad':         safe(row.get('unidad')),
            'cantidad_ppto':  safe_num(row.get('cantidad_ppto')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('codigo_idu'):
            supabase.table('presupuesto_bd').upsert(
                data, on_conflict='contrato_id,codigo_idu'
            ).execute()
            count += 1
    print(f"  → {count} upserted")


def sync_presupuesto_componentes_bd(supabase, token, project_id):
    print("\n── presupuesto_componentes_bd ──")
    if not download_gpkg(token, project_id, 'Presupuesto_Componentes.gpkg', '/tmp/ppto_comp.gpkg'):
        return
    gdf = read_layer('/tmp/ppto_comp.gpkg', 'ppto_componentes')
    if gdf is None or gdf.empty:
        return
    count = 0
    for _, row in gdf.iterrows():
        data = {
            'contrato_id':     CONTRATO_ID,
            'capitulo_num':    safe(row.get('capitulo_num')),
            'capitulo':        safe(row.get('capitulo')),
            'componente':      safe(row.get('compenente') or row.get('componente')),
            'tipo_actividad':  safe(row.get('tipo_actividad')),
            'codigo_idu':      safe(row.get('codigo_idu')),
            'descripcion':     safe(row.get('descripcion')),
            'unidad':          safe(row.get('unidad')),
            'cantidad_ppto':   safe_num(row.get('cantidad_ppto')),
            'precio_unitario': safe_num(row.get('precio_unitario')),
            'item_pago':       safe(row.get('item_pago')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data.get('codigo_idu'):
            supabase.table('presupuesto_componentes_bd').upsert(
                data, on_conflict='contrato_id,codigo_idu'
            ).execute()
            count += 1
    print(f"  → {count} upserted")


def sync_presupuesto_componentes_aux(supabase, token, project_id):
    print("\n── presupuesto_componentes_aux ──")
    tmp = '/tmp/ppto_comp_aux.gpkg'
    if not download_gpkg(token, project_id, 'AUX_Componentes.gpkg', tmp):
        return
    gdf = read_layer(tmp)
    if gdf is None or gdf.empty:
        return

    supabase.table('presupuesto_componentes_aux').delete().eq('contrato_id', CONTRATO_ID).execute()

    rows = []
    for _, row in gdf.iterrows():
        data = {
            'contrato_id':    CONTRATO_ID,
            'codigo_idu':     safe(row.get('codigo_idu')),
            'componente':     safe(row.get('compenente') or row.get('componente')),
            'tipo_actividad': safe(row.get('tipo_actividad')),
            'capitulo':       safe(row.get('capitulo')),
        }
        data = {k: v for k, v in data.items() if v is not None}
        if data:
            rows.append(data)

    if rows:
        supabase.table('presupuesto_componentes_aux').insert(rows).execute()
    print(f"  → {len(rows)} insertados")
