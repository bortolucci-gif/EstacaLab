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

from gui.state import state
from gui.tela_projeto import TelaProjeto
from gui.tela_fundacao import TelaFundacao
from gui.tela_sondagem import TelaSondagem
from gui.tela_pilares import TelaPilares
from gui.tela_capacidade import TelaCapacidade
from gui.tela_recalque import TelaRecalque
from gui.tela_memoria import TelaMemoria
from gui.app import AppEstacaLab
import copy
import pandas as pd
import json

class TestAlteracoesNaoSalvas(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        state._callbacks = []
        state.reset()
        state.nome_projeto = "Projeto Teste"
        state.obra_name = "Obra Teste"
        state.tipo_estaca = "Hélice contínua"
        state.forma_estaca = "circular"
        state.dimensoes_estaca = {"diametro": 0.5}
        state.cota_inicio = -1.0
        state.criterio_ponta_metalica = None
        state.fundacao_preenchida = True
        state.camadas = [{'cota': -1, 'nspt': 10, 'cod_solo': 31}, {'cota': -2, 'nspt': 15, 'cod_solo': 31}]
        state.lista_pilares = [{"Pilar": "P1", "Carga (kN)": 100}]

    def tearDown(self):
        self.root.destroy()

    def test_01_capacidade_bloqueada_preserva_resultados(self):
        # 1. CAPACIDADE BLOQUEADA PRESERVA RESULTADOS
        df_aoki_mock = pd.DataFrame({"teste": [1, 2]})
        df_media_mock = pd.DataFrame({"teste": [3, 4]})
        state.df_aoki = df_aoki_mock.copy(deep=True)
        state.df_media = df_media_mock.copy(deep=True)
        
        tela = TelaCapacidade(self.root)
        tela.msg = MagicMock()
        run_id_antes = tela._run_id
        
        state.marcar_pendente("sondagem")
        
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            tela._executar()
            mock_warn.assert_called_once()
            
        self.assertFalse(tela._calculando)
        self.assertEqual(tela._run_id, run_id_antes)
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_mock)
        pd.testing.assert_frame_equal(state.df_media, df_media_mock)

    def test_02_recalque_bloqueado_preserva_resultado(self):
        # 2. RECALQUE BLOQUEADO PRESERVA RESULTADO ANTIGO
        df_recalque_mock = pd.DataFrame({"recalque": [10.5]})
        state.df_recalque = df_recalque_mock.copy(deep=True)
        state.df_aoki = pd.DataFrame({"fake": [1]})  # Para passar na validação de pre-requisito
        
        tela = TelaRecalque(self.root)
        tela.msg = MagicMock()
        
        state.marcar_pendente("sondagem")
        
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            tela._calcular()
            mock_warn.assert_called_once()
            
        pd.testing.assert_frame_equal(state.df_recalque, df_recalque_mock)

    def test_03_dimensionamento_bloqueado(self):
        # 3. DIMENSIONAMENTO BLOQUEADO
        state.df_aoki = pd.DataFrame({"fake": [1]})
        df_dim_mock = pd.DataFrame({"dim": [1]})
        state.df_dimensionamento = {"aoki": df_dim_mock.copy(deep=True)}
        
        tela = TelaPilares(self.root)
        tela.msg = MagicMock()
        
        state.marcar_pendente("fundacao")
        
        with patch('tkinter.messagebox.showwarning') as mock_warn:
            tela._dimensionar()
            mock_warn.assert_called_once()
            
        pd.testing.assert_frame_equal(state.df_dimensionamento["aoki"], df_dim_mock)

    def test_04_projeto_dirty_nao_bloqueia_capacidade(self):
        # 4. PROJETO DIRTY NÃO BLOQUEIA CAPACIDADE
        state.marcar_pendente("projeto")
        self.assertFalse(state.tem_pendencias(["fundacao", "sondagem"]))
        
        tela = TelaCapacidade(self.root)
        tela.msg = MagicMock()
        tela._chk_vars["aoki"].set(True)
        
        with patch('threading.Thread.start') as mock_thread, patch('gui.tela_capacidade.TelaCapacidade._agendar_processamento_queue'):
            tela._executar()
            mock_thread.assert_called_once()
            self.assertTrue(tela._calculando)

    def test_05_duas_linhas_de_pilares(self):
        # 5. DUAS LINHAS DE PILARES
        state.lista_pilares = [{"Pilar": "P1", "Carga (kN)": 100}, {"Pilar": "P2", "Carga (kN)": 200}]
        tela = TelaPilares(self.root)
        
        self.assertFalse(state.tem_pendencias(["pilares"]))
        
        # Editar P1 e P2
        tela._linhas_widgets[0]['var_carga'].set("150")
        tela._linhas_widgets[1]['var_carga'].set("250")
        self.assertTrue(state.tem_pendencias(["pilares"]))
        
        # Commitar P1
        tela._commit(0)
        self.assertTrue(state.tem_pendencias(["pilares"])) # CONTINUA pendente porque P2 ainda não foi commitado
        
        # Commitar P2
        tela._commit(1)
        self.assertFalse(state.tem_pendencias(["pilares"])) # Agora deixa de estar pendente

    def test_06_excluir_camada_e_salvar(self):
        # 6. EXCLUIR CAMADA
        state.camadas.append({'cota': -3, 'nspt': 20, 'cod_solo': 31})
        df_aoki_mock = pd.DataFrame({"fake": [1]})
        state.df_aoki = df_aoki_mock.copy(deep=True)
        
        tela = TelaSondagem(self.root)
        tela._selecionar(0)
        tela._excluir()
        
        self.assertTrue(state.tem_pendencias(["sondagem"]))
        # Não invalida imediatamente
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_mock)
        
        # Clicar Salvar Sondagem
        tela._salvar()
        self.assertFalse(state.tem_pendencias(["sondagem"]))
        self.assertIsNone(state.df_aoki) # df_aoki é invalidado SOMENTE nesse momento

    def test_07_salvar_estacalab_com_sondagem_dirty(self):
        # 7. SALVAR .ESTACALAB COM SONDAGEM DIRTY
        state.marcar_pendente("sondagem")
        
        with patch('tkinter.messagebox.showwarning') as mock_warn, patch('tkinter.filedialog.asksaveasfilename') as mock_ask:
            result = AppEstacaLab._acao_salvar_proj(None)
            mock_warn.assert_called_once()
            mock_ask.assert_not_called()
            self.assertFalse(result)
            self.assertTrue(state.tem_pendencias(["sondagem"])) # State permanece intacto

    def test_08_pdf_com_sondagem_dirty(self):
        # 8. PDF COM SONDAGEM DIRTY
        state.marcar_pendente("sondagem")
        tela_m = TelaMemoria(self.root)
        
        with patch('tkinter.messagebox.showwarning') as mock_warn, patch('tkinter.filedialog.asksaveasfilename') as mock_ask:
            tela_m._exportar_pdf()
            mock_warn.assert_called_once()
            mock_ask.assert_not_called()

    def test_09_abrir_projeto_limpa_dirty(self):
        # 9. ABRIR PROJETO LIMPA DIRTY
        state.alteracoes_pendentes = {"fundacao", "sondagem"}
        
        # Simular carregamento (app._acao_abrir_proj chama state.de_dict(dados_limpos))
        dados = state.para_dict()
        state.de_dict(dados)
        
        self.assertEqual(state.alteracoes_pendentes, set())

    def test_10_novo_projeto_limpa_dirty(self):
        # 10. NOVO PROJETO LIMPA DIRTY
        state.alteracoes_pendentes = {"fundacao", "sondagem", "projeto"}
        
        # Simular reset
        state.reset()
        
        self.assertEqual(state.alteracoes_pendentes, set())

    def test_11_salvar_com_validacao_invalida(self):
        # 11. SALVAR COM VALIDAÇÃO INVÁLIDA
        tela = TelaFundacao(self.root)
        tela.msg = MagicMock()
        
        # Editar D para valor inválido (ex: vazio ou string)
        tela._vars['dim_diametro'].set("invalido")
        self.assertTrue(state.tem_pendencias(["fundacao"]))
        
        tela._salvar()
        
        # Validação falha
        tela.msg.erro.assert_called_once()
        # Dirty CONTINUA ativo
        self.assertTrue(state.tem_pendencias(["fundacao"]))

    def test_12_falso_dirty_na_abertura(self):
        # Mantendo o teste base original para regressão
        tela = TelaProjeto(self.root)
        self.assertFalse(state.tem_pendencias(["projeto"]))
        tela_f = TelaFundacao(self.root)
        self.assertFalse(state.tem_pendencias(["fundacao"]))
        tela_s = TelaSondagem(self.root)
        self.assertFalse(state.tem_pendencias(["sondagem"]))

    def test_13_editar_na_sem_salvar(self):
        # A) editar N.A. sem salvar: dirty sondagem, capacidade antiga permanece
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 10, 'cod_solo': 1},
            {'cota': -3, 'nspt': 10, 'cod_solo': 1},
            {'cota': -4, 'nspt': 10, 'cod_solo': 1},
            {'cota': -5, 'nspt': 10, 'cod_solo': 1}
        ]
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy()
        
        tela_s = TelaSondagem(self.root)
        tela_s._vars['tem_na'].set(True)
        tela_s._vars['linha_agua'].set("-5")
        
        self.assertTrue(state.tem_pendencias(["sondagem"]))
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki)

    def test_14_salvar_apenas_na(self):
        # B) salvar alteração somente de N.A.: dirty limpa, capacidade permanece, recalque é invalidado
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 10, 'cod_solo': 1},
            {'cota': -3, 'nspt': 10, 'cod_solo': 1},
            {'cota': -4, 'nspt': 10, 'cod_solo': 1},
            {'cota': -5, 'nspt': 10, 'cod_solo': 1}
        ]
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy()
        state.df_recalque = pd.DataFrame({"teste": [2]})
        
        tela_s = TelaSondagem(self.root)
        tela_s.msg = MagicMock()
        tela_s._vars['tem_na'].set(True)
        tela_s._vars['linha_agua'].set("-3")
        
        tela_s._salvar()
        
        self.assertFalse(state.tem_pendencias(["sondagem"]))
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki)
        self.assertIsNone(state.df_recalque)

    def test_15_editar_nspt_sem_salvar(self):
        # C) editar NSPT sem salvar: dirty, capacidade permanece
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 10, 'cod_solo': 1},
            {'cota': -3, 'nspt': 10, 'cod_solo': 1},
            {'cota': -4, 'nspt': 10, 'cod_solo': 1},
            {'cota': -5, 'nspt': 10, 'cod_solo': 1}
        ]
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy()
        
        tela_s = TelaSondagem(self.root)
        tela_s._linhas_widgets[0]['var_nspt'].set("50")
        
        self.assertTrue(state.tem_pendencias(["sondagem"]))
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki)

    def test_16_salvar_nspt(self):
        # D) salvar NSPT: dirty limpa, invalidação total
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 10, 'cod_solo': 1},
            {'cota': -3, 'nspt': 10, 'cod_solo': 1},
            {'cota': -4, 'nspt': 10, 'cod_solo': 1},
            {'cota': -5, 'nspt': 10, 'cod_solo': 1}
        ]
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy()
        state.df_recalque = pd.DataFrame({"teste": [2]})
        
        tela_s = TelaSondagem(self.root)
        tela_s.msg = MagicMock()
        tela_s._linhas_widgets[0]['var_nspt'].set("50")
        
        tela_s._salvar()
        
        self.assertFalse(state.tem_pendencias(["sondagem"]))
        self.assertIsNone(state.df_aoki)
        self.assertIsNone(state.df_recalque)

    def test_17_alterar_sfl_e_salvar(self):
        # E) alterar SFL e salvar: invalidação total
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 10, 'cod_solo': 1},
            {'cota': -3, 'nspt': 10, 'cod_solo': 1},
            {'cota': -4, 'nspt': 10, 'cod_solo': 1},
            {'cota': -5, 'nspt': 10, 'cod_solo': 1}
        ]
        df_aoki = pd.DataFrame({"teste": [1]})
        state.df_aoki = df_aoki.copy()
        
        tela_s = TelaSondagem(self.root)
        tela_s.msg = MagicMock()
        tela_s._vars['solo_sfl'].set(1)
        
        tela_s._salvar()
        
        self.assertFalse(state.tem_pendencias(["sondagem"]))
        self.assertIsNone(state.df_aoki)

    def test_18_abrir_projeto_dirty_cancelar_modal(self):
        # A) dirty + cancelar modal
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._acao_abrir_proj = AppEstacaLab._acao_abrir_proj.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog, patch('tkinter.filedialog.askopenfilename') as mock_ask:
            # Configurar o mock do dialog para retornar 'cancelar'
            instancia_dialog = MagicMock()
            instancia_dialog.result = "cancelar"
            mock_dialog.return_value = instancia_dialog
            
            app._acao_abrir_proj()
            
            mock_dialog.assert_called_once()
            mock_ask.assert_not_called()
            self.assertTrue(state.tem_pendencias(["projeto"]))

    def test_19_abrir_projeto_dirty_confirmar_cancela_filedialog(self):
        # B) dirty + confirmar + cancelar FileDialog
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._acao_abrir_proj = AppEstacaLab._acao_abrir_proj.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog:
            instancia_dialog = MagicMock()
            instancia_dialog.result = "descartar"
            mock_dialog.return_value = instancia_dialog
            
            # askopenfilename retorna vazio (cancelado)
            app._escolher_projeto_para_abrir.return_value = ""
            
            app._acao_abrir_proj()
            
            app._escolher_projeto_para_abrir.assert_called_once()
            self.assertTrue(state.tem_pendencias(["projeto"]))

    def test_20_abrir_projeto_dirty_confirmar_arquivo_invalido(self):
        # C) dirty + confirmar + arquivo inválido
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._acao_abrir_proj = AppEstacaLab._acao_abrir_proj.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog, patch('gui.app.messagebox.showerror') as mock_err:
            instancia_dialog = MagicMock()
            instancia_dialog.result = "descartar"
            mock_dialog.return_value = instancia_dialog
            
            # askopenfilename retorna um caminho inválido (dispara erro)
            app._escolher_projeto_para_abrir.return_value = "invalido.json"
            
            # carregar projeto do caminho falso dispara o erro na logica do app? Nao, isso é feito por _carregar_projeto_do_caminho
            # Mas como mockamos _escolher_projeto_para_abrir e o teste mockava askopenfilename para retornar invalido.json, 
            # O comportamento original era: _carregar_projeto_do_caminho() seria executado!
            # Vamos fazer o _carregar_projeto_do_caminho disparar o erro.
            app._carregar_projeto_do_caminho = AppEstacaLab._carregar_projeto_do_caminho.__get__(app, AppEstacaLab)
            
            app._acao_abrir_proj()
            
            mock_err.assert_called_once()
            self.assertTrue(state.tem_pendencias(["projeto"]))

    def test_21_abrir_projeto_dirty_confirmar_valido(self):
        # D) dirty + confirmar + arquivo válido
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._acao_abrir_proj = AppEstacaLab._acao_abrir_proj.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog, patch('builtins.open', unittest.mock.mock_open(read_data='{}')), patch('gui.app.messagebox.showinfo'):
            instancia_dialog = MagicMock()
            instancia_dialog.result = "descartar"
            mock_dialog.return_value = instancia_dialog
            
            app._escolher_projeto_para_abrir.return_value = "valido.json"
            app._carregar_projeto_do_caminho = AppEstacaLab._carregar_projeto_do_caminho.__get__(app, AppEstacaLab)
            
            app._acao_abrir_proj()
            
            self.assertFalse(state.tem_pendencias(["projeto"]))
            app._navegar.assert_called_once_with("projeto")
        
    def test_22_abrir_projeto_sem_dirty(self):
        # E) sem dirty abre normalmente
        app = MagicMock()
        app._acao_abrir_proj = AppEstacaLab._acao_abrir_proj.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog:
            app._escolher_projeto_para_abrir.return_value = ""
            
            app._acao_abrir_proj()
            
            mock_dialog.assert_not_called()
            app._escolher_projeto_para_abrir.assert_called_once()

    def test_23_fechar_sem_dirty(self):
        # Sem dirty => fecha direto (encerrar_aplicacao)
        app = MagicMock()
        app._solicitar_fechamento = AppEstacaLab._solicitar_fechamento.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog:
            app._solicitar_fechamento()
            mock_dialog.assert_not_called()
            app._encerrar_aplicacao.assert_called_once()

    def test_24_fechar_dirty_cancelar(self):
        # G) dirty + Cancelar não fecha
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._solicitar_fechamento = AppEstacaLab._solicitar_fechamento.__get__(app, AppEstacaLab)
        app._telas_cache = {}
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog:
            instancia_dialog = MagicMock()
            instancia_dialog.result = "cancelar"
            mock_dialog.return_value = instancia_dialog
            
            app._solicitar_fechamento()
            
            mock_dialog.assert_called_once()
            app.destroy.assert_not_called()
            self.assertTrue(state.tem_pendencias(["projeto"]))

    def test_25_fechar_dirty_sair_sem_salvar(self):
        # Em test_25, return descartar => chama _encerrar_aplicacao
        state.marcar_pendente("projeto")
        app = MagicMock()
        app._solicitar_fechamento = AppEstacaLab._solicitar_fechamento.__get__(app, AppEstacaLab)
        
        with patch('gui.app.DialogDescartarPendente') as mock_dialog:
            instancia_dialog = MagicMock()
            instancia_dialog.result = "descartar"
            mock_dialog.return_value = instancia_dialog
            
            app._solicitar_fechamento()
            app._encerrar_aplicacao.assert_called_once()

    def test_26_wm_delete_window_protocol(self):
        # I) WM_DELETE_WINDOW aponta para o handler correto
        with patch.object(AppEstacaLab, '_construir_layout'), patch.object(AppEstacaLab, '_navegar'):
            app = AppEstacaLab()
            handler = app.protocol("WM_DELETE_WINDOW")
            self.assertTrue(bool(handler))
            app.destroy()

if __name__ == '__main__':
    unittest.main()
