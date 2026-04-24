"""
sync_qfield.py — Punto de entrada · BDO IDU-1556-2025
Sincronización QFieldCloud → Supabase

Uso:
  python -m sync.sync_qfield       (desde la raíz del repositorio)
  python sync/sync_qfield.py       (ejecución directa, compatible con workflow)

Módulos
───────
  config.py             Variables de entorno y constantes
  utils.py              safe(), safe_num(), coords_from_geom()
  connections.py        Autenticación QFieldCloud y Supabase
  gpkg.py               Descarga (GPKG/XLSX) y lectura de GeoPackages
  photos.py             Subida de fotos a Supabase Storage
  sync_contrato.py      Contractual: contratos, prorrogas, adiciones (Excel)
  sync_lookup.py        Tablas lookup: tramos_aux_infra/tramos,
                          presupuesto_aux_actividad/capitulos
  sync_geo.py           Referencia geográfica: localidades, tramos_bd
  sync_presupuesto.py   Presupuesto: presupuesto_bd, componentes_bd, componentes_aux
  sync_formularios.py   Formularios: cantidades, componentes, reporte_diario, pmt
  sync_bd.py            Tablas secundarias: personal, climatica, maquinaria, sst
  sync_rf.py            Registros fotográficos: rf_cantidades, rf_componentes,
                          rf_reporte_diario

Tablas Supabase cubiertas
─────────────────────────
  contratos                    ← sync_contrato  (Excel BD_CTO_INI)
  contratos_prorrogas          ← sync_contrato  (Excel BD_CTO_PRO)
  contratos_adiciones          ← sync_contrato  (Excel BD_CTO_ADI)
  tramos_aux_infra             ← sync_lookup
  tramos_aux_tramos            ← sync_lookup
  presupuesto_aux_actividad    ← sync_lookup
  presupuesto_aux_capitulos    ← sync_lookup
  localidades                  ← sync_geo
  tramos_bd                    ← sync_geo
  presupuesto_bd               ← sync_presupuesto
  presupuesto_componentes_bd   ← sync_presupuesto
  presupuesto_componentes_aux  ← sync_presupuesto
  registros_cantidades         ← sync_formularios
  registros_componentes        ← sync_formularios
  registros_reporte_diario     ← sync_formularios
  formulario_pmt               ← sync_formularios
  bd_personal_obra             ← sync_bd
  bd_condicion_climatica       ← sync_bd
  bd_maquinaria_obra           ← sync_bd
  bd_sst_ambiental             ← sync_bd
  rf_cantidades                ← sync_rf
  rf_componentes               ← sync_rf
  rf_reporte_diario            ← sync_rf

Tablas gestionadas por la aplicación (no se sincronizan aquí):
  perfiles · historial_estados · cierres_semanales ·
  cierre_registros · notificaciones
"""
import os
import sys

# Permite ejecutar directamente: python sync/sync_qfield.py
if __name__ == '__main__' and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = 'sync'

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .config import CONTRATO_ID
from .connections import qfield_login, get_supabase, get_project_id
from .gpkg import list_project_files
from .sync_contrato import ensure_contrato, sync_contrato_excel
from .sync_lookup import (
    sync_tramos_aux_infra,
    sync_tramos_aux_tramos,
    sync_presupuesto_aux_actividad,
    sync_presupuesto_aux_capitulos,
)
from .sync_geo import sync_localidades, sync_tramos_bd
from .sync_presupuesto import (
    sync_presupuesto_bd,
    sync_presupuesto_componentes_bd,
    sync_presupuesto_componentes_aux,
)
from .sync_formularios import (
    sync_registros_cantidades,
    sync_registros_componentes,
    sync_registros_reporte_diario,
    sync_formulario_pmt,
)
from .sync_bd import sync_bd_personal, sync_bd_climatica, sync_bd_maquinaria, sync_bd_sst
from .sync_rf import sync_rf_cantidades, sync_rf_componentes, sync_rf_reporte_diario


def _run(nombre, fn, *args):
    try:
        fn(*args)
    except Exception as exc:
        print(f"\n  ✗ [{nombre}] error no controlado: {exc}")


def _run_group(tasks: list[tuple]) -> None:
    """
    Ejecuta una lista de tareas (nombre, fn, *args) en paralelo.
    Espera a que todas terminen antes de retornar.
    Con una sola tarea evita el overhead del executor.
    """
    if len(tasks) == 1:
        nombre, fn, *args = tasks[0]
        _run(nombre, fn, *args)
        return
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {pool.submit(_run, nombre, fn, *args): nombre
                   for nombre, fn, *args in tasks}
        for f in as_completed(futures):
            f.result()  # propaga excepciones no capturadas (no debería haber)


def main():
    print(f"\n{'='*60}")
    print(f"SYNC {CONTRATO_ID} · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    token      = qfield_login()
    supabase   = get_supabase()
    project_id = get_project_id(token)

    A = (supabase, token, project_id)   # args comunes

    # 0a. Listar archivos disponibles (diagnóstico)
    files = list_project_files(token, project_id)
    if files:
        print(f"\nArchivos en el proyecto ({len(files)}):")
        for f in files:
            path = f.get('name') or f.get('path') or f.get('filename') or str(f)
            print(f"  · {path}")
    else:
        print("\n⚠ No se pudieron listar los archivos del proyecto")

    # 0b. Garantizar fila base en contratos (FK padre de todas las tablas)
    print("\n── ensure_contrato ──")
    ensure_contrato(supabase)

    # 0c. Contrato Excel — enriquece la fila con datos reales del archivo
    _run('sync_contrato_excel', sync_contrato_excel, *A)

    # 1. Lookup — 4 catálogos independientes en paralelo
    _run_group([
        ('sync_tramos_aux_infra',          sync_tramos_aux_infra,          *A),
        ('sync_tramos_aux_tramos',         sync_tramos_aux_tramos,         *A),
        ('sync_presupuesto_aux_actividad', sync_presupuesto_aux_actividad, *A),
        ('sync_presupuesto_aux_capitulos', sync_presupuesto_aux_capitulos, *A),
    ])

    # 2. Geo + Presupuesto — ambos dependen de lookup, son independientes entre sí
    _run_group([
        ('sync_localidades',                sync_localidades,                *A),
        ('sync_tramos_bd',                  sync_tramos_bd,                  *A),
        ('sync_presupuesto_bd',             sync_presupuesto_bd,             *A),
        ('sync_presupuesto_componentes_bd', sync_presupuesto_componentes_bd, *A),
        ('sync_presupuesto_componentes_aux',sync_presupuesto_componentes_aux,*A),
    ])

    # 3. Formularios principales — 4 entidades independientes en paralelo
    _run_group([
        ('sync_registros_cantidades',     sync_registros_cantidades,     *A),
        ('sync_registros_componentes',    sync_registros_componentes,    *A),
        ('sync_registros_reporte_diario', sync_registros_reporte_diario, *A),
        ('sync_formulario_pmt',           sync_formulario_pmt,           *A),
    ])

    # 4. Tablas secundarias + fotos — todos dependen de formularios, independientes entre sí
    _run_group([
        ('sync_bd_personal',        sync_bd_personal,        *A),
        ('sync_bd_climatica',       sync_bd_climatica,       *A),
        ('sync_bd_maquinaria',      sync_bd_maquinaria,      *A),
        ('sync_bd_sst',             sync_bd_sst,             *A),
        ('sync_rf_cantidades',      sync_rf_cantidades,      *A),
        ('sync_rf_componentes',     sync_rf_componentes,     *A),
        ('sync_rf_reporte_diario',  sync_rf_reporte_diario,  *A),
    ])

    print(f"\n{'='*60}")
    print(f"✓ Sincronización completa")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
