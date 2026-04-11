"""
sync_qfield.py — Punto de entrada · BDO IDU-1556-2025
Sincronización QFieldCloud → Supabase

Uso:
  python -m sync.sync_qfield       (desde la raíz del repositorio)
  python sync/sync_qfield.py       (ejecución directa, compatible con workflow)

Módulos
───────
  config.py            Variables de entorno y constantes
  utils.py             safe(), safe_num(), coords_from_geom()
  connections.py       Autenticación QFieldCloud y Supabase
  gpkg.py              Descarga y lectura de GeoPackages
  photos.py            Subida de fotos a Supabase Storage
  sync_lookup.py       Tablas lookup: tramos_aux_infra, presupuesto_aux_actividad
  sync_geo.py          Referencia geográfica: localidades, tramos_bd
  sync_presupuesto.py  Presupuesto: presupuesto_bd, presupuesto_componentes_bd
  sync_formularios.py  Formularios: registros_cantidades, componentes, reporte_diario, pmt
  sync_bd.py           Tablas secundarias: personal, climatica, maquinaria, sst
  sync_rf.py           Registros fotográficos: rf_cantidades, rf_componentes, rf_reporte_diario
"""
import os
import sys

# Permite ejecutar directamente: python sync/sync_qfield.py
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = 'sync'

from datetime import datetime

from .connections import qfield_login, get_supabase, get_project_id
from .sync_lookup import sync_tramos_aux_infra, sync_presupuesto_aux_actividad
from .sync_geo import sync_localidades, sync_tramos_bd
from .sync_presupuesto import sync_presupuesto_bd, sync_presupuesto_componentes_bd
from .sync_formularios import (
    sync_registros_cantidades,
    sync_registros_componentes,
    sync_registros_reporte_diario,
    sync_formulario_pmt,
)
from .sync_bd import sync_bd_personal, sync_bd_climatica, sync_bd_maquinaria, sync_bd_sst
from .sync_rf import sync_rf_cantidades, sync_rf_componentes, sync_rf_reporte_diario


def main():
    print(f"\n{'='*60}")
    print(f"SYNC BDO IDU-1556-2025 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    token      = qfield_login()
    supabase   = get_supabase()
    project_id = get_project_id(token)

    # 0. Tablas lookup
    sync_tramos_aux_infra(supabase, token, project_id)
    sync_presupuesto_aux_actividad(supabase, token, project_id)

    # 1. Referencia geográfica
    sync_localidades(supabase, token, project_id)
    sync_tramos_bd(supabase, token, project_id)

    # 2. Presupuesto
    sync_presupuesto_bd(supabase, token, project_id)
    sync_presupuesto_componentes_bd(supabase, token, project_id)

    # 3. Formularios principales
    sync_registros_cantidades(supabase, token, project_id)
    sync_registros_componentes(supabase, token, project_id)
    sync_registros_reporte_diario(supabase, token, project_id)
    sync_formulario_pmt(supabase, token, project_id)

    # 4. Tablas secundarias
    sync_bd_personal(supabase, token, project_id)
    sync_bd_climatica(supabase, token, project_id)
    sync_bd_maquinaria(supabase, token, project_id)
    sync_bd_sst(supabase, token, project_id)

    # 5. Registros fotográficos (dependen de formularios principales)
    sync_rf_cantidades(supabase, token, project_id)
    sync_rf_componentes(supabase, token, project_id)
    sync_rf_reporte_diario(supabase, token, project_id)

    print(f"\n{'='*60}")
    print(f"✓ Sincronización completa")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
