import sys
import os
import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.state import state, normalizar_dados_projeto
from gui.tela_fundacao import TelaFundacao
from gui.tela_capacidade import TelaCapacidade

class TestFundacaoPreenchida(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        state.reset()

    def tearDown(self):
        self.root.destroy()

    def test_01_novo_projeto_nao_preenchido(self):
        # 1. NOVO PROJETO NÃO PREENCHIDO
        self.assertFalse(state.fundacao_preenchida)

    def test_02_capacidade_bloqueada(self):
        # 2. CAPACIDADE BLOQUEADA
        tela_cap = TelaCapacidade(self.root)
        tela_cap.msg = MagicMock()
        
        with patch('threading.Thread.start') as mock_thread:
            tela_cap._executar()
            
            # Worker NÃO inicia
            mock_thread.assert_not_called()
            
            # Nenhum DataFrame é produzido
            self.assertIsNone(state.df_aoki)
            self.assertIsNone(state.df_media)
            
            # Mensagem informa para preencher e salvar Dados da Estaca
            tela_cap.msg.erro.assert_called_once_with(
                "Preencha e salve os Dados da Estaca antes de calcular a capacidade de carga."
            )

    def test_03_primeiro_salvamento(self):
        # 3. PRIMEIRO SALVAMENTO
        tela_fund = TelaFundacao(self.root)
        tela_fund.msg = MagicMock()
        
        # Preencher propositalmente D=0,25 e Cota=-1
        tela_fund._vars['tipo_estaca'].set("Escavada mecanicamente sem lama")
        tela_fund._vars['forma_estaca'].set("circular")
        tela_fund._vars['dim_diametro'].set("0,25")
        tela_fund._vars['cota_inicio'].set("-1")
        
        # State antes
        self.assertFalse(state.fundacao_preenchida)
        self.assertFalse(state.projeto_modificado)
        
        # Mock para evitar falha de validação com sondagem não salva (já que não há sondagem)
        with patch('gui.tela_fundacao.validar_cota_vs_sondagem'):
            tela_fund._salvar()
            
        # Esperado
        self.assertTrue(state.fundacao_preenchida)
        self.assertTrue(state.projeto_modificado)

    def test_04_restaurar_novo_projeto(self):
        # 4. RESTAURAR NOVO PROJETO
        tela_fund = TelaFundacao(self.root)
        tela_fund.msg = MagicMock()
        
        tela_fund._vars['tipo_estaca'].set("Escavada mecanicamente sem lama")
        tela_fund._vars['forma_estaca'].set("circular")
        
        # Digitar sem salvar
        tela_fund._vars['dim_diametro'].set("0,35")
        tela_fund._vars['cota_inicio'].set("-2")
        
        # Restaurar
        tela_fund._restaurar()
        
        # Esperado: campos voltam a vazio
        self.assertEqual(tela_fund._vars['dim_diametro'].get(), "")
        self.assertEqual(tela_fund._vars['cota_inicio'].get(), "")

    def test_05_restaurar_fundacao_salva(self):
        # 5. RESTAURAR FUNDAÇÃO SALVA
        tela_fund = TelaFundacao(self.root)
        tela_fund.msg = MagicMock()
        
        # Salvar D=0,30, Cota=-2
        tela_fund._vars['tipo_estaca'].set("Escavada mecanicamente sem lama")
        tela_fund._vars['forma_estaca'].set("circular")
        tela_fund._vars['dim_diametro'].set("0,30")
        tela_fund._vars['cota_inicio'].set("-2")
        
        with patch('gui.tela_fundacao.validar_cota_vs_sondagem'):
            tela_fund._salvar()
            
        # Alterar sem salvar
        tela_fund._vars['dim_diametro'].set("0,40")
        tela_fund._vars['cota_inicio'].set("-3")
        
        # Restaurar
        tela_fund._restaurar()
        
        # Esperado: D=0,30, Cota=-2
        self.assertEqual(tela_fund._vars['dim_diametro'].get(), "0,3") # ou 0,30, o sistema remove trailing zeros as vezes? A UI guarda como string com vírgula do state que converte.
        self.assertEqual(tela_fund._vars['cota_inicio'].get(), "-2")

    def test_06_projeto_legado(self):
        # 6. PROJETO LEGADO
        dados_antigos = {
            "obra": "Teste",
            "tipo_estaca": "Escavada mecanicamente sem lama",
            "forma_estaca": "circular",
            "dimensoes_estaca": {"diametro": 0.25},
            "criterio_ponta_metalica": None,
            "cota_inicio": -1.0,
            "linha_agua": None,
            "solo_sfl": False,
            "camadas": [],
            "lista_pilares": []
        }
        # NÃO possui fundacao_preenchida
        norm = normalizar_dados_projeto(dados_antigos)
        
        # Esperado
        self.assertTrue(norm["fundacao_preenchida"])

    def test_07_projeto_novo_persistido(self):
        # 7. PROJETO NOVO PERSISTIDO
        dados = {
            "obra": "Teste",
            "tipo_estaca": "Escavada mecanicamente sem lama",
            "forma_estaca": "circular",
            "dimensoes_estaca": {"diametro": 0.25},
            "criterio_ponta_metalica": None,
            "cota_inicio": -1.0,
            "linha_agua": None,
            "solo_sfl": False,
            "camadas": [],
            "lista_pilares": [],
            "fundacao_preenchida": False
        }
        norm = normalizar_dados_projeto(dados)
        
        # Esperado
        self.assertFalse(norm["fundacao_preenchida"])

if __name__ == '__main__':
    unittest.main()
