import sys
import os
from copy import deepcopy
import pandas as pd
import unittest.mock

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.state import AppState, state
from gui.tela_sondagem import TelaSondagem
from gui.tela_capacidade import TelaCapacidade
from gui.tela_pilares import TelaPilares
import tkinter as tk
import customtkinter as ctk

def run_tests():
    print("=== INICIANDO TESTES DE DEPENDÊNCIAS ===")

    app = ctk.CTk()
    
    # Instrumentation for notificar
    original_notificar = state.notificar
    notificacoes = 0
    def mock_notificar():
        nonlocal notificacoes
        notificacoes += 1
        original_notificar()
    state.notificar = mock_notificar

    def reset_state():
        state.reset()
        state.dimensoes_estaca = {"diametro": 0.40}
        state.cota_inicio = -1
        state.fundacao_preenchida = True
        state.linha_agua = -2
        state.camadas = [
            {'cota': -1, 'nspt': 10, 'cod_solo': 1},
            {'cota': -2, 'nspt': 15, 'cod_solo': 2},
        ]
        state.solo_sfl = 0
        state.lista_pilares = [{"Pilar": "P1", "Carga (kN)": 500}]

    df_mock = pd.DataFrame({"dummy": [1]})
    
    def populate_state():
        state.df_aoki = df_mock.copy()
        state.df_decourt = df_mock.copy()
        state.df_teixeira = df_mock.copy()
        state.df_monteiro = df_mock.copy()
        state.df_berberian = df_mock.copy()
        state.df_media = df_mock.copy()
        state.metodos_media = ["aoki", "decourt", "teixeira"]
        state.df_dimensionamento = {"aoki": df_mock.copy(), "media": df_mock.copy()}
        state.df_recalque = df_mock.copy()
        state.metodos_selecionados = ["aoki", "decourt", "teixeira"]

    resultados = {"aprovados": 0, "falhos": 0}
    cenarios = []

    def log_sucesso(nome):
        resultados["aprovados"] += 1
        cenarios.append((nome, "OK"))
        print(f"[OK] {nome}")

    def log_falha(nome, erro):
        resultados["falhos"] += 1
        cenarios.append((nome, f"FALHA: {erro}"))
        print(f"[FALHA] {nome} -> {erro}")

    mock_solos = {1: "Areia", 2: "Areia Mto Pouco Siltosa"}

    try:
        # ─────────────────────────────────────────────────────────
        # 1. TESTE N.A. ISOLADO & NOTIFICAÇÕES
        reset_state()
        populate_state()
        tela_sond = TelaSondagem(app)

        # Teste Salvar sem alterações
        notificacoes = 0
        tela_sond._salvar()
        assert notificacoes == 0, f"Esperado 0 notificações ao não alterar nada, teve {notificacoes}"
        
        df_aoki_antes = state.df_aoki.copy()
        df_decourt_antes = state.df_decourt.copy()
        df_teixeira_antes = state.df_teixeira.copy()
        df_media_antes = state.df_media.copy()
        df_dim_antes = deepcopy(state.df_dimensionamento)
        metodos_media_antes = deepcopy(state.metodos_media)
        
        # Teste Salvar com apenas N.A. alterado
        tela_sond._vars['linha_agua'].set("-1")
        notificacoes = 0
        tela_sond._salvar()
        
        assert notificacoes == 1, f"Esperado 1 notificação ao alterar NA, teve {notificacoes}"
        
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_antes)
        pd.testing.assert_frame_equal(state.df_decourt, df_decourt_antes)
        pd.testing.assert_frame_equal(state.df_teixeira, df_teixeira_antes)
        pd.testing.assert_frame_equal(state.df_media, df_media_antes)
        assert state.metodos_media == metodos_media_antes
        assert state.df_dimensionamento.keys() == df_dim_antes.keys()
        for k in state.df_dimensionamento:
            pd.testing.assert_frame_equal(state.df_dimensionamento[k], df_dim_antes[k])
            
        assert state.df_recalque is None, "Recalque deveria ser None"
        log_sucesso("1. N.A. Isolado & 2. N.A. Notificações")
    except Exception as e:
        log_falha("1. N.A. Isolado & 2. N.A. Notificações", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 1.5. TESTE SFL (INVALIDAÇÃO TOTAL)
        reset_state()
        populate_state()
        tela_sond = TelaSondagem(app)
        
        # Altera somente SFL
        tela_sond._vars['solo_sfl'].set(1)
        tela_sond._salvar()
        
        assert state.df_aoki is None
        assert state.df_decourt is None
        assert state.df_teixeira is None
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        log_sucesso("1.5. SFL (Invalidação Total)")
    except Exception as e:
        log_falha("1.5. SFL (Invalidação Total)", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 3. NSPT (INVALIDAÇÃO TOTAL)
        reset_state()
        populate_state()
        tela_sond = TelaSondagem(app)
            
        tela_sond._linhas_widgets[0]['var_nspt'].set("20") # Muda NSPT
        tela_sond._salvar()

        assert state.df_aoki is None, "Aoki deveria ser None"
        assert state.df_decourt is None, "Decourt deveria ser None"
        assert state.df_teixeira is None, "Teixeira deveria ser None"
        assert state.df_media is None, "Media deveria ser None"
        assert state.metodos_media == [], "metodos_media deveria ser []"
        assert state.df_dimensionamento == {}, "dimensionamento deveria ser vazio"
        assert state.df_recalque is None, "recalque deveria ser None"
        log_sucesso("3. NSPT Invalidação Total")
    except Exception as e:
        log_falha("3. NSPT Invalidação Total", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 4. CHECKBOX — REMOVER TEIXEIRA
        reset_state()
        populate_state()
        tela_cap = TelaCapacidade(app)
        
        df_aoki_antes = state.df_aoki.copy()
        df_decourt_antes = state.df_decourt.copy()
        df_teixeira_antes = state.df_teixeira.copy()
        df_recalque_antes = state.df_recalque.copy()

        tela_cap._chk_vars["teixeira"].set(False)
        tela_cap._sincronizar_selecao()
        
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_antes)
        pd.testing.assert_frame_equal(state.df_decourt, df_decourt_antes)
        pd.testing.assert_frame_equal(state.df_teixeira, df_teixeira_antes)
        pd.testing.assert_frame_equal(state.df_recalque, df_recalque_antes)
        
        assert state.df_media is None
        assert state.metodos_media == []
        assert "media" not in state.df_dimensionamento
        assert "aoki" in state.df_dimensionamento
        log_sucesso("4. CHECKBOX Remover Teixeira")
    except Exception as e:
        log_falha("4. CHECKBOX Remover Teixeira", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 5. DESMARCAR AOKI
        reset_state()
        populate_state()
        tela_cap = TelaCapacidade(app)
        
        df_aoki_antes = state.df_aoki.copy()
        df_recalque_antes = state.df_recalque.copy()

        tela_cap._chk_vars["aoki"].set(False)
        tela_cap._sincronizar_selecao()
        
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_antes)
        pd.testing.assert_frame_equal(state.df_recalque, df_recalque_antes)
        
        assert state.df_media is None
        assert state.metodos_media == []
        assert "media" not in state.df_dimensionamento
        log_sucesso("5. DESMARCAR AOKI (Somente check)")
    except Exception as e:
        log_falha("5. DESMARCAR AOKI (Somente check)", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 6. RECALCULAR SEM AOKI
        reset_state()
        populate_state()
        tela_cap = TelaCapacidade(app)
        
        tela_cap._chk_vars["aoki"].set(False)
        tela_cap._sincronizar_selecao()
        
        with unittest.mock.patch("gui.tela_capacidade.threading.Thread") as mock_thread:
            tela_cap._executar()
            
        assert state.df_aoki is None
        assert state.df_recalque is None
        log_sucesso("6. RECALCULAR SEM AOKI")
    except Exception as e:
        log_falha("6. RECALCULAR SEM AOKI", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 7. CARGA DO PILAR
        reset_state()
        populate_state()
        tela_pil = TelaPilares(app)
        
        df_aoki_antes = state.df_aoki.copy()
        df_media_antes = state.df_media.copy()
        
        # Teste do Helper
        tela_pil._invalidar_resultados_pilares()
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_antes)
        pd.testing.assert_frame_equal(state.df_media, df_media_antes)
        
        # Integração Real
        reset_state()
        populate_state()
        tela_pil = TelaPilares(app)
        tela_pil._linhas_widgets[0]['var_carga'].set("600")
        tela_pil._commit(0)
        
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        pd.testing.assert_frame_equal(state.df_aoki, df_aoki_antes)
        pd.testing.assert_frame_equal(state.df_media, df_media_antes)
        log_sucesso("7. CARGA DO PILAR")
    except Exception as e:
        log_falha("7. CARGA DO PILAR", str(e))

    try:
        # ─────────────────────────────────────────────────────────
        # 8. TESTAR N.A. + NSPT AO MESMO TEMPO
        reset_state()
        populate_state()
        tela_sond = TelaSondagem(app)
        # Altera N.A. e NSPT simultaneamente
        tela_sond._vars['linha_agua'].set("-1")
        tela_sond._linhas_widgets[0]['var_nspt'].set("20")
        tela_sond._salvar()

        assert state.df_aoki is None
        assert state.df_decourt is None
        assert state.df_recalque is None
        assert state.df_media is None
        log_sucesso("8. N.A. + NSPT AO MESMO TEMPO")
    except Exception as e:
        log_falha("8. N.A. + NSPT AO MESMO TEMPO", str(e))

    # ─────────────────────────────────────────────────────────
    # 9. CLEANUP
    try:
        if 'tela_sond' in locals(): tela_sond.destroy()
        if 'tela_cap' in locals(): tela_cap.destroy()
        if 'tela_pil' in locals(): tela_pil.destroy()
        state.notificar = original_notificar
        app.destroy()
        log_sucesso("9. CLEANUP")
    except Exception as e:
        log_falha("9. CLEANUP", str(e))

    # ─────────────────────────────────────────────────────────
    # 10. RESULTADO FINAL
    print("\n=== RESULTADO DOS TESTES ===")
    for nome, status in cenarios:
        print(f"{nome:40} | {status}")
    print(f"\nAprovados: {resultados['aprovados']}")
    print(f"Falhos:    {resultados['falhos']}")

    if resultados['falhos'] > 0:
        sys.exit(1)
        
if __name__ == "__main__":
    run_tests()
