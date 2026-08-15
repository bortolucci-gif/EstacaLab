import os
import sys
import unittest

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import customtkinter as ctk
from unittest.mock import patch, MagicMock

from gui.state import state
from gui.tela_sondagem import TelaSondagem

class TestCotaSondagem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        
    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        state.reset()
        
    def test_cota_sondagem_independente_fundacao_cota_5(self):
        state.cota_inicio = -5
        
        tela = TelaSondagem(self.root)
        
        # Simulate adding 10 layers
        for _ in range(10):
            tela._adicionar_camada()
            
        tela._salvar()
        
        expected_cotas = [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10]
        actual_cotas = [cam['cota'] for cam in state.camadas]
        
        self.assertEqual(expected_cotas, actual_cotas, "Cotas da sondagem devem ser sempre -1, -2, -3...")

    def test_cota_sondagem_independente_fundacao_cota_10(self):
        state.cota_inicio = -10
        
        tela = TelaSondagem(self.root)
        
        # Simulate adding 10 layers
        for _ in range(10):
            tela._adicionar_camada()
            
        tela._salvar()
        
        expected_cotas = [-1, -2, -3, -4, -5, -6, -7, -8, -9, -10]
        actual_cotas = [cam['cota'] for cam in state.camadas]
        
        self.assertEqual(expected_cotas, actual_cotas, "Cotas da sondagem devem ser sempre -1, -2, -3...")

if __name__ == '__main__':
    unittest.main()
