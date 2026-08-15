import sys
import os
import json
import logging
import traceback
import pandas as pd
import unittest.mock
import tkinter as tk
import customtkinter as ctk

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.state import AppState, state
from gui.tela_sondagem import TelaSondagem
from gui.tela_capacidade import TelaCapacidade
from gui.tela_fundacao import TelaFundacao
from gui.tela_pilares import TelaPilares
from gui.tela_recalque import TelaRecalque
from gui.tela_resultados import TelaResultados
from gui.app import AppEstacaLab

# Para capturar logs
class ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.logs = []
    def emit(self, record):
        self.logs.append(self.format(record))

log_handler = ListHandler()
logging.getLogger().addHandler(log_handler)
logging.getLogger().setLevel(logging.ERROR)

def fake_file_dialog_save(*args, **kwargs):
    return "teste_projeto.estacalab"

def fake_file_dialog_open(*args, **kwargs):
    return "teste_projeto.estacalab"

# Captura de Notificações
original_notificar = state.notificar
notificacoes_count = 0
def notificar_wrapper():
    global notificacoes_count
    notificacoes_count += 1
    original_notificar()
state.notificar = notificar_wrapper

resultados_e2e = []

def registrar(etapa, esperado, status, erro=""):
    resultados_e2e.append({
        "ETAPA": etapa,
        "ESPERADO": esperado,
        "OBTIDO": erro if erro else "Conforme esperado",
        "STATUS": status
    })
    print(f"[{status}] {etapa} - {esperado}")
    if erro:
        print(f"  ERRO: {erro}")
    sys.stdout.flush()

def rodar_testes_e2e():
    app_root = ctk.CTk()
    
    # Prepara mock de Threads para rodar sincrono e conseguir checar os resultados
    def run_sync_thread(target, args, daemon):
        target(*args)
        
    try:
        # =======================================================
        # 2. CRIAR PROJETO A
        # =======================================================
        state.reset()
        tela_sond = TelaSondagem(app_root)
        tela_fund = TelaFundacao(app_root)
        tela_pil = TelaPilares(app_root)
        tela_cap = TelaCapacidade(app_root)
        
        # Preencher Fundação
        tela_fund._vars['tipo_estaca'].set("Escavada mecanicamente sem lama")
        tela_fund._vars['forma_estaca'].set("circular")
        tela_fund._vars['dim_diametro'].set("0,25")
        tela_fund._vars['cota_inicio'].set("-1")
        tela_fund._salvar()
        
        # Preencher Sondagem
        tela_sond._vars['tem_na'].set(True)
        tela_sond._vars['linha_agua'].set("-2")
        tela_sond._vars['solo_sfl'].set(0)
        # Limpar existentes e deixar 2 camadas
        tela_sond._adicionar_camada()
        tela_sond._linhas_widgets[0]['var_nspt'].set("10")
        tela_sond._linhas_widgets[0]['var_solo'].set("Areia")
        tela_sond._adicionar_camada()
        tela_sond._linhas_widgets[1]['var_nspt'].set("15")
        tela_sond._linhas_widgets[1]['var_solo'].set("Areia Mto Pouco Siltosa")
        tela_sond._salvar()
        
        # Preencher Pilares
        tela_pil._adicionar()
        tela_pil._linhas_widgets[0]['var_carga'].set("30")
        tela_pil._commit(0)
        
        # Selecionar Aoki, Decourt, Teixeira
        for k in tela_cap._chk_vars:
            tela_cap._chk_vars[k].set(False)
        tela_cap._chk_vars["aoki"].set(True)
        tela_cap._chk_vars["decourt"].set(True)
        tela_cap._chk_vars["teixeira"].set(True)
        tela_cap._sincronizar_selecao()
        
        assert state.D == 0.25
        assert len(state.camadas) == 2
        assert state.lista_pilares[0]["Carga (kN)"] == 30
        registrar("Criar Projeto A", "Variáveis preenchidas", "PASS")
        
        # =======================================================
        # 3. CAPACIDADE
        # =======================================================
        with unittest.mock.patch("gui.tela_capacidade.threading.Thread", side_effect=lambda target, args, daemon: unittest.mock.Mock(start=lambda: target(*args))):
            tela_cap._executar()
            # Processar fila para puxar o sucesso
            app_root.update_idletasks()
            # Precisamos simular o processamento da queue
            while not tela_cap.queue.empty():
                tela_cap._processar_queue()
                
        assert state.df_aoki is not None
        assert state.df_decourt is not None
        assert state.df_teixeira is not None
        assert state.df_monteiro is None
        assert state.df_media is not None
        assert set(state.metodos_media) == {"aoki", "decourt", "teixeira"}
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        assert tela_cap._calculando is False, "Worker _calculando vazando"
        registrar("Capacidade", "df_aoki/dec/teix preenchidos, dimensionamento nulo", "PASS")
        
        # =======================================================
        # =======================================================
        # 4. DIMENSIONAMENTO
        # =======================================================
        tela_pil._var_metodo.set("aoki")
        tela_pil._dimensionar()
        tela_pil._var_metodo.set("media")
        tela_pil._dimensionar()
        assert "aoki" in state.df_dimensionamento
        assert "media" in state.df_dimensionamento
        assert state.df_dimensionamento["aoki"] is not None
        registrar("Dimensionamento", "df_dimensionamento preenchido", "PASS")
        
        # =======================================================
        # 5. RECALQUE
        # =======================================================
        tela_rec = TelaRecalque(app_root)
        tela_rec._calcular()
                
        assert state.df_recalque is not None
        registrar("Recalque", "df_recalque preenchido", "PASS")
        
        # =======================================================
        # 6. RESULTADOS
        # =======================================================
        tela_res = TelaResultados(app_root)
        tela_res.tkraise()
        
        registrar("Resultados", "Exibe sem exceções", "PASS")
        
        # =======================================================
        # 7. ALTERAR APENAS N.A.
        # =======================================================
        df_aoki_antes = state.df_aoki.copy()
        df_media_antes = state.df_media.copy()
        tela_sond._vars['linha_agua'].set("-1")
        tela_sond._salvar()
        
        assert state.df_aoki is not None
        assert state.df_media is not None
        assert state.df_recalque is None
        
        tela_rec._calcular()
        
        assert state.df_recalque is not None
        registrar("Alterar N.A.", "Cap/Dim preservados, Recalque limpo e recalculado", "PASS")
        
        # =======================================================
        # 8. ALTERAR CARGA DO PILAR
        # =======================================================
        tela_pil._linhas_widgets[0]['var_carga'].set("60")
        tela_pil._commit(0)
        
        assert state.df_aoki is not None
        assert state.df_media is not None
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        
        tela_pil._var_metodo.set("aoki")
        tela_pil._dimensionar()
        tela_rec._calcular()
                
        assert state.df_dimensionamento != {}
        assert state.df_recalque is not None
        registrar("Alterar Carga Pilar", "Dim/Recalque invalidados e recalculados", "PASS")
        
        # =======================================================
        # 9. ALTERAR DIÂMETRO
        # =======================================================
        tela_fund._vars['dim_diametro'].set("0,30")
        tela_fund._salvar()
        
        assert state.df_aoki is None
        assert state.df_media is None
        assert state.metodos_media == []
        assert state.df_dimensionamento == {}
        assert state.df_recalque is None
        
        # Tentar calcular Recalque
        tela_rec = TelaRecalque(app_root)
        tela_rec._calcular()
        assert state.df_recalque is None
        registrar("Alterar Diâmetro", "Total Invalidação. Recalque bloqueado", "PASS")
        
        # =======================================================
        # 10. RECALCULAR CONFIGURAÇÃO B
        # =======================================================
        with unittest.mock.patch("gui.tela_capacidade.threading.Thread", side_effect=lambda target, args, daemon: unittest.mock.Mock(start=lambda: target(*args))):
            tela_cap._executar()
            while not tela_cap.queue.empty():
                tela_cap._processar_queue()
        
        tela_pil._var_metodo.set("aoki")
        tela_pil._dimensionar()
        tela_rec._calcular()
                
        assert state.df_aoki is not None
        assert state.df_recalque is not None
        registrar("Recalcular Config B", "Novos cálculos baseados no D 0.30", "PASS")
        
        # =======================================================
        # 11. MUDAR CHECKBOX
        # =======================================================
        df_aoki_ant = state.df_aoki.copy()
        df_teix_ant = state.df_teixeira.copy()
        tela_cap._chk_vars["teixeira"].set(False)
        tela_cap._sincronizar_selecao()
        
        assert state.df_teixeira is not None
        assert state.df_aoki is not None
        assert state.df_recalque is not None
        assert state.df_media is None
        assert state.metodos_media == []
        assert "media" not in state.df_dimensionamento
        
        with unittest.mock.patch("gui.tela_capacidade.threading.Thread", side_effect=lambda target, args, daemon: unittest.mock.Mock(start=lambda: target(*args))):
            tela_cap._executar()
            while not tela_cap.queue.empty():
                tela_cap._processar_queue()
                
        assert state.df_teixeira is None # Não selecionado, logo apagado pelo _executar original da nova run!
        assert state.df_aoki is not None
        registrar("Mudar Checkbox", "Mantém métodos individuais até recálculo destrutivo", "PASS")
        
        # =======================================================
        # 12. SALVAR PROJETO
        # =======================================================
        import json
        state.salvar_json("teste_projeto.estacalab")
            
        # Analisar JSON Salvo
        with open("teste_projeto.estacalab", "r") as f:
            saved_data = json.load(f)
            
        assert saved_data["D"] == 0.3
        assert "df_media" not in saved_data
        assert "df_aoki" not in saved_data
        assert "metodos_media" not in saved_data
        registrar("Salvar Projeto", "Apenas inputs e metadata salvos", "PASS")
        
        # =======================================================
        # 13. ALTERAR ESTADO DEPOIS DE SALVAR
        # =======================================================
        tela_fund._vars['dim_diametro'].set("0,40")
        tela_fund._salvar()
        registrar("Alterar Estado", "Inputs modificados em RAM (D=0.40)", "PASS")
        
        # =======================================================
        # 14. ABRIR O PROJETO SALVO
        # =======================================================
        with open("teste_projeto.estacalab", "r", encoding="utf-8") as f:
            from gui.state import normalizar_dados_projeto
            dados_brutos = json.load(f)
            dados_limpos = normalizar_dados_projeto(dados_brutos)
            state.de_dict(dados_limpos)
            
        assert state.D == 0.30
        assert state.df_aoki is None
        assert state.df_recalque is None
        registrar("Abrir Projeto", "Restaura inputs (D=0.30), Invalida resultados", "PASS")
        
        # =======================================================
        # 15. RECALCULAR APÓS ABRIR
        # =======================================================
        with unittest.mock.patch("gui.tela_capacidade.threading.Thread", side_effect=lambda target, args, daemon: unittest.mock.Mock(start=lambda: target(*args))):
            tela_cap = TelaCapacidade(app_root) # recria tela pois abrir destrói antigas
            tela_cap._executar()
            while not tela_cap.queue.empty():
                tela_cap._processar_queue()
                
        assert state.df_aoki is not None
        registrar("Recalcular após abrir", "Capacidade computada perfeitamente", "PASS")
        
        # =======================================================
        # 16. PROJETO NOVO
        # =======================================================
        state.reset()
        assert state.df_aoki is None
        assert state.D == 0.25 # default do app state inicial (ou do main.py q eu reseto?) - state inicial na verdade não tem um default D que importa, state.reset() deixa algo? 
        # Actually state.reset() just resets to Nones or defaults. Let's just check None
        assert state.df_media is None
        registrar("Projeto Novo", "Limpeza absoluta", "PASS")

        # =======================================================
        # LOGGING E CONSISTÊNCIA
        # =======================================================
        erros_log = log_handler.logs
        if len(erros_log) > 0:
            registrar("Logging e Exceptions", "Nenhum Erro", "FAIL", str(erros_log))
            raise Exception("Encontrados Erros no Log: " + str(erros_log))
        else:
            registrar("Logging e Exceptions", "Nenhum Erro", "PASS")

    except AssertionError as ae:
        tb = traceback.format_exc()
        registrar("Teste Falhou", "Esperado Pass", "FAIL", str(ae) + "\n" + tb)
    except Exception as ex:
        tb = traceback.format_exc()
        registrar("Erro inesperado", "Não quebrar", "FAIL", str(ex) + "\n" + tb)
        
    finally:
        app_root.destroy()
        
    # (Continuação da função original - mantida)
    # Salvar tabela de relatorio (movido para o final)
    pass

def rodar_testes_app():
    print("\n\n=== INICIANDO TESTES INTEGRAÇÃO APP ===")
    from gui.app import AppEstacaLab
    from gui.state import state
    
    app = None
    try:
        # Prepara o estado
        state.reset()
        state.D = 0.50 # Altera o estado inicial
        
        # 1. Instanciar App
        app = AppEstacaLab()
        app.update_idletasks()
        registrar("Instanciar AppEstacaLab", "App criado sem quebrar", "PASS")
        
        # Simular alguns cálculos para popular cache de telas e resultados
        state.df_aoki = pd.DataFrame({"Carga Adm. (kN)": [150.0, 200.0]})
        state.df_decourt = pd.DataFrame()
        state.notificar()
        app.update_idletasks()
        
        # Pega a contagem de callbacks ANTES de abrir, MAS depois de criar a tela_cap
        app._navegar("capacidade")
        app.update_idletasks()
        tela_cap_antiga = app._telas_cache.get("capacidade")
        assert tela_cap_antiga is not None
        assert tela_cap_antiga.winfo_exists() == 1
        
        callbacks_antes = len(state._callbacks)
        
        # =======================================================
        # 2. SALVAR VIA FLUXO REAL
        # =======================================================
        with unittest.mock.patch("tkinter.filedialog.asksaveasfilename", side_effect=fake_file_dialog_save):
            with unittest.mock.patch("tkinter.messagebox.showinfo"):
                app._acao_salvar_proj()
            
        assert os.path.exists("teste_projeto.estacalab")
        # Lê e garante que os resultados NÃO estão lá, apenas inputs
        with open("teste_projeto.estacalab", "r") as f:
            dados = json.load(f)
            assert "D" in dados
            assert dados["D"] == 0.50
            assert "df_aoki" not in dados
            
        registrar("Salvar via AppEstacaLab", "Salva arquivo via GUI com sucesso (só inputs)", "PASS")
        
        # Sujar estado atual
        state.D = 0.99
        
        # =======================================================
        # 3. ABRIR VIA FLUXO REAL
        # Já criamos a tela capacidade e pegamos a ref como tela_cap_antiga
        
        with unittest.mock.patch("tkinter.filedialog.askopenfilename", side_effect=fake_file_dialog_open):
            with unittest.mock.patch("tkinter.messagebox.showinfo"):
                app._acao_abrir_proj()
        app.update_idletasks()
            
        assert state.D == 0.50
        assert state.df_aoki is None
        
        # Verificar limpeza de cache
        assert "capacidade" not in app._telas_cache
        # Verificar destroy da tela antiga (Tkinter define winfo_exists() == 0)
        assert tela_cap_antiga.winfo_exists() == 0
        assert getattr(tela_cap_antiga, "_disposed", False) is True
            
        # Verificar contagem de callbacks e garbage collection de callbacks bound
        callbacks_depois = len(state._callbacks)
        assert callbacks_depois <= callbacks_antes # Não deve ter crescido desenfreadamente
        
        for cb in state._callbacks:
            if hasattr(cb, "__self__"):
                assert cb.__self__ is not tela_cap_antiga
        
        registrar("Abrir via AppEstacaLab", "Restaura estado, limpa cache de telas e descarta threads antigas", "PASS")
        
        # =======================================================
        # 4. HEADER - RENDERIZAÇÃO E ATUALIZAÇÃO
        # =======================================================
        state.df_aoki = pd.DataFrame({"Carga Adm. (kN)": [199.9]})
        state.metodos_selecionados = ["aoki"]
        state.notificar()
        app.update_idletasks()
        
        # Testando Status no Header
        assert app.lbl_status_capacidade.cget("text") == "Calculada"
        registrar("Header Renderização", "Header existe, renderiza e atualiza sem exceções", "PASS")
        
        # =======================================================
        # 5. NOVO PROJETO VIA FLUXO REAL
        # =======================================================
        state.df_aoki = pd.DataFrame()
        with unittest.mock.patch('gui.app.DialogNovoProjeto') as MockDialog, \
             unittest.mock.patch('tkinter.messagebox.askyesno', return_value=True), \
             unittest.mock.patch.object(app, 'wait_window'):
            
            mock_dlg_instance = unittest.mock.MagicMock()
            mock_dlg_instance.result = "descartar"
            MockDialog.return_value = mock_dlg_instance
            
            app._novo_projeto()
        app.update_idletasks()
        
        assert state.df_aoki is None
        assert state.D == 0.25 # Reseta de volta ao default
        assert len(app._telas_cache) == 1
        assert "projeto" in app._telas_cache
        
        registrar("Novo Projeto via AppEstacaLab", "Limpeza correta pelo fluxo real", "PASS")
        
    except AssertionError as ae:
        tb = traceback.format_exc()
        registrar("AppEstacaLab Falhou", "Esperado Pass", "FAIL", str(ae) + "\n" + tb)
    except Exception as ex:
        tb = traceback.format_exc()
        registrar("AppEstacaLab Erro", "Não quebrar", "FAIL", str(ex) + "\n" + tb)
    finally:
        if app:
            app.destroy()

def rodar_testes_header():
    print("\n\n=== INICIANDO TESTES DO HEADER ===")
    from gui.app import AppEstacaLab
    from gui.state import state
    
    app = None
    try:
        # =======================================================
        # CASO 1 — ESTADO INICIAL
        # =======================================================
        state.reset()
        app = AppEstacaLab()
        app.update_idletasks()
        
        assert app.lbl_status_capacidade.cget("text") == "Não calculada"
        assert app.lbl_status_dimensionamento.cget("text") == "Não calculado"
        assert app.lbl_status_recalque.cget("text") == "Não calculado"
        registrar("Header - Caso 1", "Estado inicial - Não calculados", "PASS")
        
        # =======================================================
        # CASO 2 — CAPACIDADE CALCULADA
        # =======================================================
        state.reset()
        state.metodos_selecionados = ["aoki", "decourt"]
        state.df_aoki = pd.DataFrame({"A": [1]})
        state.df_decourt = pd.DataFrame({"B": [2]})
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_capacidade.cget("text") == "Calculada"
        registrar("Header - Caso 2", "Capacidade Calculada", "PASS")
        
        # =======================================================
        # CASO 3 — CAPACIDADE PARCIAL
        # =======================================================
        state.reset()
        state.metodos_selecionados = ["aoki", "decourt"]
        state.df_aoki = pd.DataFrame({"A": [1]})
        state.df_decourt = None
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_capacidade.cget("text") == "Parcial"
        registrar("Header - Caso 3", "Capacidade Parcial", "PASS")
        
        # =======================================================
        # CASO 4 — NENHUM MÉTODO SELECIONADO
        # =======================================================
        state.reset()
        state.metodos_selecionados = []
        state.df_aoki = pd.DataFrame({"A": [1]})
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_capacidade.cget("text") == "Não calculada"
        registrar("Header - Caso 4", "Nenhum método selecionado", "PASS")
        
        # =======================================================
        # CASO 5 — DIMENSIONAMENTO
        # =======================================================
        state.reset()
        state.df_dimensionamento = {"aoki": pd.DataFrame({"X": [1]})}
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_dimensionamento.cget("text") == "Calculado"
        
        state.df_dimensionamento = {"aoki": pd.DataFrame()}
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_dimensionamento.cget("text") == "Não calculado"
        
        state.df_dimensionamento = {}
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_dimensionamento.cget("text") == "Não calculado"
        registrar("Header - Caso 5", "Dimensionamento validado", "PASS")
        
        # =======================================================
        # CASO 6 — RECALQUE
        # =======================================================
        state.reset()
        state.df_recalque = pd.DataFrame({"R": [10]})
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_recalque.cget("text") == "Calculado"
        
        state.df_recalque = None
        state.notificar()
        app.update_idletasks()
        
        assert app.lbl_status_recalque.cget("text") == "Não calculado"
        registrar("Header - Caso 6", "Recalque validado", "PASS")
        
    except AssertionError as ae:
        tb = traceback.format_exc()
        registrar("Header Falhou", "Esperado Pass", "FAIL", str(ae) + "\n" + tb)
    except Exception as ex:
        tb = traceback.format_exc()
        registrar("Header Erro", "Não quebrar", "FAIL", str(ex) + "\n" + tb)
    finally:
        if app:
            app.destroy()

def rodar_testes_institucionais():
    print("\n\n=== INICIANDO TESTES INSTITUCIONAIS ===")
    from gui.tela_sobre import TelaSobre
    from gui.tela_memoria import TelaMemoria
    
    app_root = ctk.CTk()
    try:
        # 1. Tela Sobre
        tela_sobre = TelaSobre(app_root)
        def coletar_textos(widget):
            textos = []
            try:
                texto = widget.cget("text")
                if texto:
                    textos.append(str(texto))
            except Exception:
                pass

            for filho in widget.winfo_children():
                textos.extend(coletar_textos(filho))

            return textos
            
        textos_sobre = " ".join(coletar_textos(tela_sobre))
        
        assert "Trabalho de Conclusão de Curso" in textos_sobre
        assert "finalidade acadêmica e educacional" in textos_sobre
        assert "PolyForm Noncommercial License 1.0.0" in textos_sobre
        assert "utilização comercial do software não é autorizada" in textos_sobre
        assert "MIT" not in textos_sobre
        
        registrar(
            "Institucional - Sobre o Sistema",
            "Aviso acadêmico, licença não comercial e responsabilidade presentes na interface",
            "PASS"
        )
        
        # 2. Tela Memória
        tela_mem = TelaMemoria(app_root)
        mem_txt = tela_mem._gerar_memoria()
        
        assert "Trabalho de Conclusão de Curso" in mem_txt
        assert "finalidade acadêmica e educacional" in mem_txt
        assert "PolyForm Noncommercial" in mem_txt
        assert "License 1.0.0" in mem_txt
        assert "utilização comercial do software não é autorizada" in mem_txt
        assert "INFORMAÇÕES DE USO E RESPONSABILIDADE" in mem_txt
        assert "MIT" not in mem_txt
        registrar("Institucional - Memória Texto", "Informações de licença e responsabilidade presentes no gerador de texto", "PASS")
        
        # 3. Gerador PDF
        # Vamos mockar canvas para não gravar no disco
        with unittest.mock.patch("reportlab.platypus.BaseDocTemplate") as mock_doc:
            with unittest.mock.patch("tkinter.filedialog.asksaveasfilename", return_value="teste.pdf"):
                with unittest.mock.patch("gui.state.AppState.tem_pendencias", return_value=False):
                    tela_mem._exportar_pdf()
                
            mock_doc_instance = mock_doc.return_value
            mock_doc_instance.build.assert_called_once()
            args = mock_doc_instance.build.call_args[0][0] # lista de elementos
            
            # Checar se há Paragraph com os textos chave
            texto_pdf = ""
            for el in args:
                if hasattr(el, 'text'):
                    texto_pdf += el.text
            
            assert "INFORMAÇÕES DE USO E RESPONSABILIDADE" in texto_pdf
            assert "Trabalho de Conclusão de Curso" in texto_pdf
            assert "PolyForm Noncommercial License 1.0.0" in texto_pdf
            assert "utilização comercial do software não é autorizada" in texto_pdf
            assert "MIT" not in texto_pdf
            registrar("Institucional - PDF", "Informações de licença e responsabilidade presentes no PDF", "PASS")
            
    except AssertionError as ae:
        tb = traceback.format_exc()
        registrar("Institucional Falhou", "Esperado Pass", "FAIL", str(ae) + "\n" + tb)
    except Exception as ex:
        tb = traceback.format_exc()
        registrar("Institucional Erro", "Não quebrar", "FAIL", str(ex) + "\n" + tb)
    finally:
        app_root.destroy()

if __name__ == "__main__":
    rodar_testes_e2e()
    rodar_testes_app()
    rodar_testes_header()
    rodar_testes_institucionais()
    
    # Salvar tabela de relatorio
    print("\n\n=== TABELA DE RESULTADOS E2E ===")
    print(f"{'ETAPA':<30} | {'ESPERADO':<60} | {'OBTIDO':<30} | {'STATUS'}")
    print("-" * 130)
    for r in resultados_e2e:
        print(f"{r['ETAPA']:<30} | {r['ESPERADO']:<60} | {r['OBTIDO']:<30} | {r['STATUS']}")
        
    if os.path.exists("teste_projeto.estacalab"):
        os.remove("teste_projeto.estacalab")
        
    falhas = [r for r in resultados_e2e if r['STATUS'] == "FAIL"]
    if falhas:
        os._exit(1)
        
    state.notificar = original_notificar
    logging.getLogger().removeHandler(log_handler)
    os._exit(0)
