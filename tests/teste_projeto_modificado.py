import os
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.state import state

class TestProjetoModificado(unittest.TestCase):
    def setUp(self):
        state.reset()
        state.aplicar_defaults_usuario()

    def test_abrir_vazio_nao_modificado(self):
        self.assertFalse(state.projeto_modificado)
        self.assertFalse(state.obter_pendencias())

    def test_marcar_como_modificado(self):
        state.marcar_projeto_modificado()
        self.assertTrue(state.projeto_modificado)
        
    def test_de_dict_limpa_modificado(self):
        state.marcar_projeto_modificado()
        
        # Simulando de_dict com dados limpos
        dados = state.para_dict()
        state.de_dict(dados)
        
        self.assertFalse(state.projeto_modificado)
        self.assertFalse(state.obter_pendencias())

    def test_salvar_json_limpa_modificado(self):
        state.marcar_projeto_modificado()
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".estacalab", delete=False) as f:
            caminho = f.name
            
        try:
            state.salvar_json(caminho)
            self.assertFalse(state.projeto_modificado)
        finally:
            if os.path.exists(caminho):
                os.remove(caminho)

if __name__ == '__main__':
    unittest.main()
