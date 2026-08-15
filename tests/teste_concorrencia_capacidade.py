import sys
import os

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import os
import time
import queue
import traceback
import customtkinter as ctk
import pandas as pd
from unittest.mock import patch, MagicMock



from gui.state import state
from gui.tela_capacidade import TelaCapacidade

dummy_df = pd.DataFrame({"Cota (m)": [-1], "Carga Adm. (kN)": [100]})

def slow_mock(*args, **kwargs):
    time.sleep(0.1)
    return dummy_df

class AssertMixin:
    def assertTrue(self, expr, msg=None):
        if not expr: raise AssertionError(msg or f"Expected True, got {expr}")
    def assertFalse(self, expr, msg=None):
        if expr: raise AssertionError(msg or f"Expected False, got {expr}")
    def assertEqual(self, first, second, msg=None):
        if first != second: raise AssertionError(msg or f"{first} != {second}")
    def assertNotEqual(self, first, second, msg=None):
        if first == second: raise AssertionError(msg or f"{first} == {second}")
    def assertIsNone(self, obj, msg=None):
        if obj is not None: raise AssertionError(msg or f"{obj} is not None")
    def assertIsNotNone(self, obj, msg=None):
        if obj is None: raise AssertionError(msg or f"obj is None")

class TestSuite(AssertMixin):
    def __init__(self):
        self.app = ctk.CTk()

    def setUp(self):
        state.df_aoki = None
        state.df_decourt = None
        state.df_teixeira = None
        state.df_monteiro = None
        state.df_berberian = None
        state.df_media = None
        state.metodos_media = []
        state.metodos_selecionados = ["aoki", "decourt", "teixeira", "monteiro", "berberian"]
        
        state.cota_inicio = -1
        state.dimensoes_estaca = {"diametro": 0.25}
        state.fundacao_preenchida = True
        state.camadas = [{"cota": -2, "nspt": 10, "tipo_solo": "Argila", "cod_solo": 1}]
        state.linha_agua = None
        state.solo_sfl = 1
        state.tipo_estaca = "Escavada mecanicamente sem lama"
        state.forma_estaca = "Circular"
        state.marcar_salvo("fundacao")
        state.marcar_salvo("sondagem")
        
        self._notificar_original = getattr(state, "notificar", None)
        self.notificacoes = 0
        state.notificar = self.mock_notificar
        
        self.tela = TelaCapacidade(self.app)
        
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

    def tearDown(self):
        state.notificar = self._notificar_original
        if not getattr(self.tela, "_disposed", False):
            self.tela.destroy()
        
    def mock_notificar(self):
        self.notificacoes += 1

    def run_tk_events(self, duration_sec):
        end_time = time.time() + duration_sec
        while time.time() < end_time:
            self.app.update()
            time.sleep(0.01)

    # 1. Duplo Clique
    def test_01_duplo_clique(self):
        with patch("gui.tela_capacidade.resultAoki", side_effect=slow_mock):
            self.tela._executar()
            self.tela._executar() 
            self.assertEqual(self.tela._run_id, 1)
            self.assertTrue(self.tela._calculando)
            self.run_tk_events(0.8) 
            self.assertFalse(self.tela._calculando)

    # 2. Falha Parcial
    @patch("gui.tela_capacidade.resultAoki", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultDecourt", side_effect=Exception("Erro Forcado"))
    @patch("gui.tela_capacidade.resultTeixeira", return_value=dummy_df)
    def test_02_falha_parcial(self, mock_tei, mock_dec, mock_aoki):
        state.metodos_selecionados = ["aoki", "decourt", "teixeira"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

        self.tela._executar()
        self.run_tk_events(0.5)

        self.assertIsNone(state.df_aoki)
        self.assertIsNone(state.df_decourt)
        self.assertIsNone(state.df_teixeira)
        self.assertIsNone(state.df_media)
        self.assertEqual(state.metodos_media, [])

    # 3. Alteração de D
    @patch("gui.tela_capacidade.resultAoki", side_effect=slow_mock)
    @patch("gui.tela_capacidade.resultDecourt", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultTeixeira", return_value=dummy_df)
    def test_03_alteracao_d(self, mock_tei, mock_dec, mock_aoki):
        state.metodos_selecionados = ["aoki", "decourt", "teixeira"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

        self.tela._executar()
        state.dimensoes_estaca = {"diametro": 0.40}
        state.marcar_salvo("fundacao")
        self.run_tk_events(0.5)

        self.assertIsNone(state.df_aoki)
        self.assertIsNone(state.df_media)

    # 4. Alteração de Sondagem
    @patch("gui.tela_capacidade.resultAoki", side_effect=slow_mock)
    @patch("gui.tela_capacidade.resultDecourt", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultTeixeira", return_value=dummy_df)
    def test_04_alteracao_sondagem(self, mock_tei, mock_dec, mock_aoki):
        state.metodos_selecionados = ["aoki", "decourt", "teixeira"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

        self.tela._executar()
        state.camadas[0]["nspt"] = 15
        state.marcar_salvo("fundacao")
        self.run_tk_events(0.5)

        self.assertIsNone(state.df_aoki)

    # 5. Deepcopy
    def test_05_deepcopy(self):
        snapshot = self.tela._capturar_snapshot_calculo()
        nspt_original = snapshot["camadas"][0]["nspt"]
        state.camadas[0]["nspt"] = 55
        
        self.assertEqual(snapshot["camadas"][0]["nspt"], nspt_original)
        self.assertEqual(nspt_original, 10)

    # 6. Destroy
    @patch("gui.tela_capacidade.resultAoki", side_effect=slow_mock)
    @patch("gui.tela_capacidade.resultDecourt", side_effect=slow_mock)
    def test_06_destroy(self, mock_dec, mock_aoki):
        state.metodos_selecionados = ["aoki", "decourt"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

        self.tela._executar()
        run_id_antigo = self.tela._run_id
        
        self.tela.destroy()
        
        self.assertTrue(self.tela._disposed)
        self.assertNotEqual(self.tela._run_id, run_id_antigo)
        self.assertIsNone(self.tela._after_queue_id)
        
        self.run_tk_events(0.5)
        
        self.assertIsNone(state.df_aoki)
        self.assertIsNone(state.df_decourt)

    # 7. Projeto A -> Projeto B
    @patch("gui.tela_capacidade.resultAoki", side_effect=slow_mock)
    def test_07_projeto_a_b(self, mock_aoki):
        state.metodos_selecionados = ["aoki"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)

        self.tela._executar()
        self.tela.destroy()
        
        state.dimensoes_estaca = {"diametro": 0.40}
        state.marcar_salvo("fundacao")
        tela_b = TelaCapacidade(self.app)
        
        self.run_tk_events(0.3)
        self.assertIsNone(state.df_aoki)
        tela_b.destroy()

    # 8. Commit Completo
    @patch("gui.tela_capacidade.resultAoki", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultDecourt", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultTeixeira", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultMonteiro", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultBerberian", return_value=dummy_df)
    @patch("gui.tela_capacidade.gerar_df_media_metodos", return_value=dummy_df)
    def test_08_commit_completo(self, mock_med, mock_ber, mock_mon, mock_tei, mock_dec, mock_aoki):
        self.notificacoes = 0
        self.tela._executar()
        
        self.assertIsNone(state.df_aoki)
        self.assertIsNone(state.df_media)
        self.assertEqual(self.notificacoes, 1)
        
        self.run_tk_events(0.2)
        
        self.assertIsNotNone(state.df_aoki)
        self.assertIsNotNone(state.df_decourt)
        self.assertIsNotNone(state.df_teixeira)
        self.assertIsNotNone(state.df_monteiro)
        self.assertIsNotNone(state.df_berberian)
        self.assertIsNotNone(state.df_media)
        
        self.assertEqual(state.metodos_media, ["aoki", "decourt", "teixeira", "monteiro", "berberian"])
        self.assertEqual(self.notificacoes, 2)

    # 9. Media
    @patch("gui.tela_capacidade.resultAoki", return_value=dummy_df)
    @patch("gui.tela_capacidade.resultDecourt", return_value=dummy_df)
    @patch("gui.tela_capacidade.gerar_df_media_metodos", return_value=dummy_df)
    def test_09_media(self, mock_med, mock_dec, mock_aoki):
        # 1. Metodo único
        state.metodos_selecionados = ["aoki"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)
        self.tela._executar()
        self.run_tk_events(0.2)
        
        self.assertIsNotNone(state.df_aoki)
        self.assertIsNone(state.df_media)
        self.assertEqual(state.metodos_media, [])
        
        # 2. Múltiplos métodos
        state.df_aoki = None # reseta p/ segunda execucao
        state.metodos_selecionados = ["aoki", "decourt"]
        for k in self.tela._chk_vars:
            self.tela._chk_vars[k].set(k in state.metodos_selecionados)
        self.tela._executar()
        self.run_tk_events(0.2)
        
        self.assertIsNotNone(state.df_aoki)
        self.assertIsNotNone(state.df_decourt)
        self.assertIsNotNone(state.df_media)
        self.assertEqual(state.metodos_media, ["aoki", "decourt"])

    # 10. Evento Obsoleto
    def test_10_evento_obsoleto(self):
        self.tela._agendar_processamento_queue()
        self.tela.queue.put(("success", 999, {}, {}, None))
        
        self.notificacoes = 0
        self.run_tk_events(0.2)
        
        self.assertIsNone(state.df_aoki)
        self.assertEqual(self.notificacoes, 0)

    # 11. Polling Único
    def test_11_polling_unico(self):
        self.tela._agendar_processamento_queue()
        self.tela._agendar_processamento_queue()
        id1 = self.tela._after_queue_id
        self.assertIsNotNone(id1)
        self.tela._agendar_processamento_queue()
        id2 = self.tela._after_queue_id
        self.assertEqual(id1, id2)

def run():
    print(f"{'CENÁRIO':<30} | {'STATUS'}")
    print("-" * 45)
    
    suite = TestSuite()
    tests = [
        ("Duplo Clique", suite.test_01_duplo_clique),
        ("Falha Parcial", suite.test_02_falha_parcial),
        ("Alteração de D", suite.test_03_alteracao_d),
        ("Alteração de Sondagem", suite.test_04_alteracao_sondagem),
        ("Deepcopy", suite.test_05_deepcopy),
        ("Destroy", suite.test_06_destroy),
        ("Projeto A -> Projeto B", suite.test_07_projeto_a_b),
        ("Commit Completo", suite.test_08_commit_completo),
        ("Média", suite.test_09_media),
        ("Evento Obsoleto", suite.test_10_evento_obsoleto),
        ("Polling Único", suite.test_11_polling_unico),
    ]
    
    aprovados = 0
    falhos = 0
    erros = []
    
    for nome, func in tests:
        suite.setUp()
        try:
            func()
            print(f"{nome:<30} | OK")
            aprovados += 1
        except Exception as e:
            print(f"{nome:<30} | FALHA")
            falhos += 1
            erros.append((nome, traceback.format_exc()))
        finally:
            suite.tearDown()
            
    suite.app.destroy()
            
    print("-" * 45)
    print(f"Executados: {aprovados + falhos}")
    print(f"Aprovados : {aprovados}")
    print(f"Falhos    : {falhos}")
    
    if falhos > 0:
        print("\n=== ERROS ENCONTRADOS ===")
        for nome, err in erros:
            print(f"\n[{nome}]")
            print(err)
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    run()
