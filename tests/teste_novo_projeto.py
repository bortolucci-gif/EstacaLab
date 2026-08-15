import os
import sys
import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# Importa a aplicação
from gui.app import AppEstacaLab, DialogNovoProjeto
from gui.state import state
import pandas as pd

class TestNovoProjeto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = AppEstacaLab()
        cls.app.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def setUp(self):
        state.reset()
        
    def preencher_projeto(self):
        state.reset()
        state.nome_projeto = "Projeto A"
        state.obra_name = "Obra Teste"
        state.camadas = [{"cod_solo": 1, "nspt": 10, "espessura": 1}]
        state.lista_pilares = [{"Pilar": "P1", "Carga (kN)": 100}]

    def test_a_salvar_e_novo(self):
        self.preencher_projeto()
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch('gui.app.filedialog.asksaveasfilename') as MockFile, \
             patch('gui.state.state.salvar_json') as MockSave, \
             patch('tkinter.messagebox.showinfo') as MockInfo, \
             patch.object(self.app, 'wait_window'):
            
            # Simula o diálogo retornando "salvar"
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "salvar"
            MockDialog.return_value = mock_dlg_instance
            
            # Simula escolher um arquivo
            MockFile.return_value = "caminho_teste.estacalab"
            
            self.app._novo_projeto()
            
            MockSave.assert_called_once_with("caminho_teste.estacalab")
            self.assertEqual(state.nome_projeto, "Novo Projeto")
            self.assertFalse(state.camadas)

    def test_b_cancelar_filedialog(self):
        self.preencher_projeto()
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch('gui.app.filedialog.asksaveasfilename') as MockFile, \
             patch.object(self.app, 'wait_window'):
            
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "salvar"
            MockDialog.return_value = mock_dlg_instance
            
            # Simula cancelar o filedialog (retorna vazio)
            MockFile.return_value = ""
            
            self.app._novo_projeto()
            
            self.assertEqual(state.nome_projeto, "Projeto A")
            self.assertTrue(state.camadas)

    def test_c_criar_sem_salvar(self):
        self.preencher_projeto()
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch('tkinter.messagebox.askyesno') as MockAsk, \
             patch.object(self.app, 'wait_window'):
            
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "descartar"
            MockDialog.return_value = mock_dlg_instance
            
            # Simula confirmar o descarte
            MockAsk.return_value = True
            
            self.app._novo_projeto()
            
            self.assertEqual(state.nome_projeto, "Novo Projeto")
            self.assertFalse(state.camadas)

    def test_d_cancelar(self):
        self.preencher_projeto()
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch.object(self.app, 'wait_window'):
            
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "cancelar"
            MockDialog.return_value = mock_dlg_instance
            
            self.app._novo_projeto()
            
            self.assertEqual(state.nome_projeto, "Projeto A")
            self.assertTrue(state.camadas)

    def test_e_erro_de_salvamento(self):
        self.preencher_projeto()
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch('gui.app.filedialog.asksaveasfilename') as MockFile, \
             patch('gui.state.state.salvar_json') as MockSave, \
             patch('tkinter.messagebox.showerror') as MockError, \
             patch.object(self.app, 'wait_window'):
            
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "salvar"
            MockDialog.return_value = mock_dlg_instance
            
            MockFile.return_value = "caminho_teste.estacalab"
            
            # Simula erro no save
            MockSave.side_effect = Exception("Disco cheio")
            
            self.app._novo_projeto()
            
            self.assertEqual(state.nome_projeto, "Projeto A")
            self.assertTrue(state.camadas)

    def test_f_salvar_e_novo_com_dirty(self):
        # CENÁRIO — SALVAR E CRIAR NOVO COM DIRTY
        self.preencher_projeto()
        
        # Cria dataframes preenchidos
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy(deep=True)
        
        # Suja a sondagem
        state.alteracoes_pendentes.add("sondagem")
        
        with patch('gui.app.DialogNovoProjeto') as MockDialog, \
             patch('tkinter.messagebox.showwarning') as MockWarn, \
             patch('gui.app.filedialog.asksaveasfilename') as MockFile, \
             patch('tkinter.messagebox.showerror') as MockError, \
             patch.object(self.app, 'wait_window'), \
             patch.object(state, 'reset') as MockReset:
             
            mock_dlg_instance = MagicMock()
            mock_dlg_instance.result = "salvar"
            MockDialog.return_value = mock_dlg_instance
            
            self.app._novo_projeto()
            
            # warning exibido
            MockWarn.assert_called_once()
            
            # filedialog de salvamento NÃO deve abrir
            MockFile.assert_not_called()
            
            # state.nome_projeto continua "Projeto A"
            self.assertEqual(state.nome_projeto, "Projeto A")
            
            # state.camadas permanecem
            self.assertTrue(state.camadas)
            
            # DataFrames permanecem
            pd.testing.assert_frame_equal(state.df_aoki, df_aoki)
            
            # state.alteracoes_pendentes continua contendo "sondagem"
            self.assertIn("sondagem", state.alteracoes_pendentes)
            
            # state.reset() NÃO é chamado
            MockReset.assert_not_called()

if __name__ == "__main__":
    result = unittest.main(exit=False)
    os._exit(not result.result.wasSuccessful())
