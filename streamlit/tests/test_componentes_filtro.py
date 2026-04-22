"""
Tests para el mapeo _COMPONENTE_VALOR y la firma de load_componentes.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest


class TestComponenteValorMapping:
    """El mapeo filtro_tipo → valor del campo componente en Supabase."""

    def _get_source(self):
        return open(os.path.join(os.path.dirname(__file__),
                                 "..", "pages", "_componentes_base.py"), encoding='utf-8').read()

    def test_ambiental_valor_exacto(self):
        src = self._get_source()
        assert "'ambiental': 'Ambiental- SST'" in src

    def test_social_valor_exacto(self):
        src = self._get_source()
        assert "'social':    'Social'" in src or "'social': 'Social'" in src

    def test_pmt_valor_exacto(self):
        src = self._get_source()
        assert "'pmt':       'PMT'" in src or "'pmt': 'PMT'" in src

    def test_capitulo_num_no_existe_en_mapeo(self):
        """El mapeo antiguo _CAPITULO_NUM no debe existir."""
        src = self._get_source()
        assert '_CAPITULO_NUM' not in src

    def test_componente_valor_existe_en_mapeo(self):
        src = self._get_source()
        assert '_COMPONENTE_VALOR' in src


class TestLoadComponentesFirma:
    """load_componentes debe aceptar `componente` y NO `capitulo_num`."""

    def _get_source(self):
        return open(os.path.join(os.path.dirname(__file__),
                                 "..", "database.py"), encoding='utf-8').read()

    def test_parametro_componente_existe(self):
        src = self._get_source()
        assert 'componente: str | None' in src or 'componente=None' in src

    def test_parametro_capitulo_num_no_existe(self):
        src = self._get_source()
        assert 'capitulo_num' not in src

    def test_filtro_usa_campo_componente(self):
        src = self._get_source()
        assert "query.eq('componente', componente)" in src
