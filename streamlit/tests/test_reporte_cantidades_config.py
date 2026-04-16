"""
Tests unitarios para APROBACION_CONFIG y la lógica de visibilidad/acción
del Reporte de Cantidades.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from config import APROBACION_CONFIG


def _cfg(rol):
    """Devuelve la tupla de 4 elementos para un rol."""
    assert rol in APROBACION_CONFIG, f"Rol desconocido: {rol!r}"
    return APROBACION_CONFIG[rol]


# ── Estructura de la tupla ───────────────────────────────────────────────────

class TestTuplaConfig:
    def test_todos_los_roles_tienen_4_elementos(self):
        for rol, cfg in APROBACION_CONFIG.items():
            assert len(cfg) == 4, f"Rol '{rol}' tiene {len(cfg)} elementos, se esperan 4"

    def test_rol_obra_existe(self):
        assert 'obra' in APROBACION_CONFIG

    def test_rol_interventoria_existe(self):
        assert 'interventoria' in APROBACION_CONFIG

    def test_rol_operativo_existe(self):
        assert 'operativo' in APROBACION_CONFIG

    def test_rol_supervision_existe(self):
        assert 'supervision' in APROBACION_CONFIG

    def test_rol_admin_existe(self):
        assert 'admin' in APROBACION_CONFIG


# ── Visibilidad: todos los roles activos ven todos los estados ───────────────

class TestVisibilidad:
    @pytest.mark.parametrize("rol", ['obra', 'interventoria', 'supervision', 'admin'])
    def test_estados_vis_es_none_para_roles_activos(self, rol):
        estados_vis, _, _, _ = _cfg(rol)
        assert estados_vis is None, (
            f"Rol '{rol}' tiene estados_vis={estados_vis!r}, se espera None (todos los estados)"
        )

    def test_operativo_estados_vis_es_none(self):
        estados_vis, _, _, _ = _cfg('operativo')
        assert estados_vis is None


# ── Accionabilidad: solo el estado correcto habilita el panel ────────────────

class TestAccionabilidad:
    def test_obra_acciona_solo_borrador(self):
        _, _, _, estados_accion = _cfg('obra')
        assert estados_accion == ['BORRADOR']

    def test_interventoria_acciona_solo_revisado(self):
        _, _, _, estados_accion = _cfg('interventoria')
        assert estados_accion == ['REVISADO']

    def test_operativo_sin_panel(self):
        _, _, campos, estados_accion = _cfg('operativo')
        assert campos is None
        assert estados_accion is None

    def test_supervision_sin_panel(self):
        _, _, campos, estados_accion = _cfg('supervision')
        assert campos is None
        assert estados_accion is None

    def test_admin_acciona_solo_revisado(self):
        _, _, _, estados_accion = _cfg('admin')
        assert estados_accion == ['REVISADO']


# ── Estado de aprobación ─────────────────────────────────────────────────────

class TestEstadoAprobacion:
    def test_obra_aprueba_a_revisado(self):
        _, estado_apr, _, _ = _cfg('obra')
        assert estado_apr == 'REVISADO'

    def test_interventoria_aprueba_a_aprobado(self):
        _, estado_apr, _, _ = _cfg('interventoria')
        assert estado_apr == 'APROBADO'

    def test_admin_aprueba_a_aprobado(self):
        _, estado_apr, _, _ = _cfg('admin')
        assert estado_apr == 'APROBADO'

    def test_operativo_no_aprueba(self):
        _, estado_apr, _, _ = _cfg('operativo')
        assert estado_apr is None

    def test_supervision_no_aprueba(self):
        _, estado_apr, _, _ = _cfg('supervision')
        assert estado_apr is None


# ── Campos de BD ─────────────────────────────────────────────────────────────

class TestCamposBD:
    def test_obra_usa_campos_residente(self):
        _, _, campos, _ = _cfg('obra')
        assert campos['campo_cant']   == 'cant_residente'
        assert campos['campo_estado'] == 'estado_residente'
        assert campos['campo_apr']    == 'aprobado_residente'
        assert campos['campo_fecha']  == 'fecha_residente'
        assert campos['campo_obs']    == 'obs_residente'

    def test_interventoria_usa_campos_interventor(self):
        _, _, campos, _ = _cfg('interventoria')
        assert campos['campo_cant']   == 'cant_interventor'
        assert campos['campo_estado'] == 'estado_interventor'
        assert campos['campo_apr']    == 'aprobado_interventor'
        assert campos['campo_fecha']  == 'fecha_interventor'
        assert campos['campo_obs']    == 'obs_interventor'

    def test_admin_campos_son_identicos_a_interventoria(self):
        _, _, campos_admin, _ = _cfg('admin')
        _, _, campos_int,   _ = _cfg('interventoria')
        assert campos_admin == campos_int
