import os
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.state import state
from gui.project_commit import confirmar_fundacao_sondagem
from gui.validation import ValidationError

class TestTransacaoConjunta(unittest.TestCase):
    def setUp(self):
        state.reset()
        state.cota_inicio = -5
        state.camadas = [{'cota': -1, 'nspt': 5, 'cod_solo': 31},
                         {'cota': -2, 'nspt': 5, 'cod_solo': 31},
                         {'cota': -3, 'nspt': 5, 'cod_solo': 31},
                         {'cota': -4, 'nspt': 5, 'cod_solo': 31},
                         {'cota': -5, 'nspt': 5, 'cod_solo': 31},
                         {'cota': -6, 'nspt': 5, 'cod_solo': 31}]
        self.snapshot_fund = {
            "tipo_estaca": state.tipo_estaca,
            "forma_estaca": state.forma_estaca,
            "D": state.D,
            "cota_inicio": state.cota_inicio
        }
        import copy
        self.snapshot_sond = {
            "camadas": copy.deepcopy(state.camadas),
            "linha_agua": state.linha_agua,
            "solo_sfl": state.solo_sfl
        }

    def test_a_fundacao_nova_sondagem_nova(self):
        # A) Fundação -5 -> -10 e simultaneamente Sondagem até -15
        dados_fund = self.snapshot_fund.copy()
        dados_fund["cota_inicio"] = -10
        
        dados_sond = self.snapshot_sond.copy()
        for i in range(7, 16):
            dados_sond["camadas"].append({'cota': -i, 'nspt': 5, 'cod_solo': 31})
            
        sucesso = confirmar_fundacao_sondagem(state, dados_fund, dados_sond, self.snapshot_fund, self.snapshot_sond)
        self.assertTrue(sucesso)
        self.assertEqual(state.cota_inicio, -10)
        self.assertEqual(len(state.camadas), 15)
        self.assertTrue(state.projeto_modificado)

    def test_b_fundacao_reduzida_sondagem_reduzida(self):
        # B) Fundação -10 (vamos simular que estava em -10) -> -2
        # Sondagem reduzida compatível com -2 (ex: até -4)
        state.cota_inicio = -10
        for i in range(7, 12):
            state.camadas.append({'cota': -i, 'nspt': 5, 'cod_solo': 31})
        self.snapshot_fund["cota_inicio"] = -10
        self.snapshot_sond["camadas"] = state.camadas.copy()
        
        dados_fund = self.snapshot_fund.copy()
        dados_fund["cota_inicio"] = -2
        
        dados_sond = self.snapshot_sond.copy()
        dados_sond["camadas"] = dados_sond["camadas"][:4] # até -4
        
        sucesso = confirmar_fundacao_sondagem(state, dados_fund, dados_sond, self.snapshot_fund, self.snapshot_sond)
        self.assertTrue(sucesso)
        self.assertEqual(state.cota_inicio, -2)
        self.assertEqual(len(state.camadas), 4)

    def test_c_combinacao_invalida(self):
        # C) combinação realmente inválida
        # Ex: Fundação em -6, Sondagem reduzida para até -4
        dados_fund = self.snapshot_fund.copy()
        dados_fund["cota_inicio"] = -6
        
        dados_sond = self.snapshot_sond.copy()
        dados_sond["camadas"] = dados_sond["camadas"][:4]
        
        with self.assertRaises(ValidationError):
            confirmar_fundacao_sondagem(state, dados_fund, dados_sond, self.snapshot_fund, self.snapshot_sond)
            
        # O state não deve ter sido alterado
        self.assertEqual(state.cota_inicio, -5)
        self.assertEqual(len(state.camadas), 6)
        self.assertFalse(state.projeto_modificado)

    def test_d_na_invalido_contra_nova_sondagem(self):
        # D) N.A. candidato inválido contra nova Sondagem
        dados_fund = self.snapshot_fund.copy()
        dados_fund["cota_inicio"] = -2
        
        dados_sond = self.snapshot_sond.copy()
        dados_sond["camadas"] = dados_sond["camadas"][:4]
        dados_sond["linha_agua"] = -6 # Inválido! Sondagem vai só até -4
        
        with self.assertRaises(ValidationError):
            confirmar_fundacao_sondagem(state, dados_fund, dados_sond, self.snapshot_fund, self.snapshot_sond)
            
        # O state não deve ter sido alterado
        self.assertIsNone(state.linha_agua)
        self.assertEqual(state.cota_inicio, -5)

    def test_e_na_valido_contra_nova_sondagem(self):
        # E) N.A. válido
        dados_fund = self.snapshot_fund.copy()
        dados_fund["cota_inicio"] = -2
        
        dados_sond = self.snapshot_sond.copy()
        dados_sond["camadas"] = dados_sond["camadas"][:4]
        dados_sond["linha_agua"] = -3 
        
        sucesso = confirmar_fundacao_sondagem(state, dados_fund, dados_sond, self.snapshot_fund, self.snapshot_sond)
        self.assertTrue(sucesso)
        self.assertEqual(state.linha_agua, -3)

if __name__ == '__main__':
    unittest.main()
