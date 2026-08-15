"""
EstacaLab — Janela principal da aplicação.
Sidebar de navegação + header + área de conteúdo dinâmico.
"""

import sys
import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox

from gui.constants import *
from gui.state import state

# Telas
from gui.tela_projeto    import TelaProjeto
from gui.tela_fundacao   import TelaFundacao
from gui.tela_sondagem   import TelaSondagem
from gui.tela_capacidade import TelaCapacidade
from gui.tela_pilares    import TelaPilares
from gui.tela_recalque   import TelaRecalque
from gui.tela_resultados import TelaResultados
from gui.tela_comparacao import TelaComparacao
from gui.tela_memoria    import TelaMemoria
from gui.tela_graficos   import TelaGraficos
from gui.tela_sobre      import TelaSobre


# ─────────────────────────────────────────────────────────────
# Configuração global do customtkinter
# ─────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class DialogNovoProjeto(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Novo Projeto")
        self.geometry("480x200")
        self.resizable(False, False)
        
        self.transient(master)
        self.grab_set()
        
        self.result = "cancelar"
        
        lbl = ctk.CTkLabel(self, text="Deseja salvar o projeto atual antes de iniciar um novo projeto?", 
                           font=("Helvetica", 14), wraplength=420)
        lbl.pack(pady=20, padx=20)
        
        frame_btns = ctk.CTkFrame(self, fg_color="transparent")
        frame_btns.pack(pady=15, fill="x", padx=20)
        
        btn_salvar = ctk.CTkButton(frame_btns, text="Salvar e criar novo", 
                                   command=lambda: self._set_result("salvar"), width=130)
        btn_salvar.pack(side="left", padx=5)
        
        btn_descartar = ctk.CTkButton(frame_btns, text="Criar sem salvar", 
                                      command=lambda: self._set_result("descartar"), width=130, 
                                      fg_color="transparent", border_width=1, text_color=("black", "white"))
        btn_descartar.pack(side="left", padx=5)
        
        btn_cancelar = ctk.CTkButton(frame_btns, text="Cancelar", 
                                     command=lambda: self._set_result("cancelar"), width=90, 
                                     fg_color="transparent", text_color="gray")
        btn_cancelar.pack(side="right", padx=5)
        
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
    def _set_result(self, res):
        self.result = res
        self.destroy()

class DialogDescartarPendente(ctk.CTkToplevel):
    def __init__(self, master, pendencias, tipo="abrir", projeto_modificado=False):
        super().__init__(master)
        
        self.title("Alterações Não Salvas")
        self.geometry("760x330")
        self.minsize(760, 330)
        
        self.result = "cancelar"
        
        mapa_abas = {
            "projeto": "Dados do Projeto",
            "fundacao": "Dados da Fundação",
            "sondagem": "Sondagem SPT",
            "pilares": "Mapa de Pilares"
        }
        
        texto_linhas = []
        if pendencias:
            nomes = [mapa_abas.get(p, p) for p in pendencias]
            lista_str = "\n".join(f"- {n}" for n in nomes)
            texto_linhas.append("Existem alterações nas seguintes abas que ainda não foram confirmadas:\n")
            texto_linhas.append(f"{lista_str}\n")
        
        if projeto_modificado:
            texto_linhas.append("O projeto possui alterações que ainda não foram gravadas em um arquivo .estacalab.\n")
            
        if tipo == "abrir":
            texto_linhas.append("Ao abrir outro projeto, essas alterações serão descartadas.")
            btn_descartar_text = "Descartar alterações e abrir projeto"
            btn_salvar_text = "Salvar alterações e abrir projeto"
        else:
            texto_linhas.append("Deseja sair e descartar essas alterações?")
            btn_descartar_text = "Sair sem salvar"
            btn_salvar_text = "Salvar alterações e sair"
            
        texto = "\n".join(texto_linhas)
            
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        
        frame_conteudo = ctk.CTkFrame(self, fg_color="transparent")
        frame_conteudo.grid(row=0, column=0, sticky="nsew", padx=20, pady=(18, 8))
            
        lbl = ctk.CTkLabel(frame_conteudo, text=texto, font=("Helvetica", 13), wraplength=700, justify="left")
        lbl.pack(anchor="w")
        
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.grid(row=1, column=0, sticky="ew", padx=20, pady=(8, 18))
        
        frame_botoes.grid_columnconfigure(0, weight=1)
        frame_botoes.grid_columnconfigure(1, weight=1)
        frame_botoes.grid_columnconfigure(2, weight=1)
        
        self.btn_descartar = ctk.CTkButton(frame_botoes, text=btn_descartar_text, 
                                      command=lambda: self._set_result("descartar"),
                                      fg_color=COR_ERRO, hover_color="#B91C1C")
        self.btn_descartar.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_salvar = ctk.CTkButton(frame_botoes, text=btn_salvar_text, 
                                      command=lambda: self._set_result("salvar"),
                                      fg_color=COR_PRIMARIA)
        self.btn_salvar.grid(row=0, column=1, sticky="ew", padx=5)
        
        self.btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", 
                                     command=lambda: self._set_result("cancelar"),
                                     fg_color=COR_SECUNDARIA, hover_color="#475569", text_color="#FFFFFF")
        self.btn_cancelar.grid(row=0, column=2, sticky="ew", padx=(5, 0))
        
        self.update_idletasks()
        
        x = master.winfo_x() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.transient(master)
        self.grab_set()

    def _set_result(self, res):
        self.result = res
        self.destroy()

class AppEstacaLab(ctk.CTk):

    ITENS_SIDEBAR = [
        # (chave_tela, ícone, label, is_secao)
        ("__secao_projeto", "", "PROJETO", True),
        ("projeto",        "📝", "Dados do Projeto", False),

        ("__secao_fund",   "", "FUNDAÇÃO", True),
        ("fundacao",       "🏗", "Dados da Estaca", False),
        ("sondagem",       "🧱", "Sondagem SPT", False),

        ("__secao_anal",   "", "ANÁLISE", True),
        ("capacidade",     "⚙", "Capacidade de Carga", False),
        ("pilares",        "🏢", "Mapa de Pilares", False),
        ("recalque",       "📐", "Recalque", False),

        ("__secao_res",    "", "RESULTADOS", True),
        ("resultados",     "📊", "Resultados", False),
        ("comparacao",     "↔", "Comparação", False),
        ("graficos",       "📈", "Gráficos", False),
        ("memoria",        "📄", "Memória de Cálculo", False),
    ]

    def __init__(self):
        super().__init__()

        self.title("EstacaLab — Sistema de Análise de Fundações Profundas")
        self.geometry("1280x800")
        self.minsize(1180, 720)
        self.configure(fg_color=COR_FUNDO)

        self._tela_ativa = None
        self._telas_cache: dict = {}
        self._btn_sidebar: dict = {}

        self._construir_layout()
        self._navegar("projeto")
        
        # Interceptar fechamento da janela (Alt+F4 ou botão X)
        self.protocol("WM_DELETE_WINDOW", self._solicitar_fechamento)

    # ─────────────────────────────────────────────────────────
    # Layout principal
    # ─────────────────────────────────────────────────────────
    def _construir_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_sidebar()
        self._construir_header()
        self._construir_area_conteudo()

    # ─────────────────────────────────────────────────────────
    # Sidebar
    # ─────────────────────────────────────────────────────────
    def _construir_sidebar(self):
        self.sidebar = ctk.CTkFrame(self,
                                     width=SIDEBAR_LARGURA,
                                     fg_color=COR_SIDEBAR,
                                     corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.columnconfigure(0, weight=1)

        # Logo / Nome do App
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color=COR_SIDEBAR_SECAO,
                                   corner_radius=0, height=HEADER_ALTURA)
        logo_frame.grid(row=0, column=0, sticky="ew")
        logo_frame.grid_propagate(False)

        import os
        from PIL import Image

        caminho_logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png")
        
        if os.path.exists(caminho_logo):
            img_pil = Image.open(caminho_logo).convert("RGBA")
            
            # Crop manual seguro (bounding box do conteúdo real)
            # Dimensões originais: 1536x1024
            # Margens excessivas removidas para maximizar exibição
            bbox = (130, 240, 1435, 755)
            img_crop = img_pil.crop(bbox)
            
            # Redimensionar mantendo proporção 
            largura_max = 200
            altura_max = 52
            
            scale = min(largura_max / img_crop.width, altura_max / img_crop.height)
            novo_w = int(img_crop.width * scale)
            novo_h = int(img_crop.height * scale)
            
            img_logo = ctk.CTkImage(light_image=img_crop,
                                    dark_image=img_crop,
                                    size=(novo_w, novo_h))
            
            lbl_img = ctk.CTkLabel(logo_frame, image=img_logo, text="")
            lbl_img.place(relx=0.5, rely=0.5, anchor="center")
            
            # Se a imagem tem fundo branco e a sidebar é escura, mudamos a cor de fundo do logo_frame 
            # para se integrar melhor à imagem (fundo branco)
            logo_frame.configure(fg_color="white")
        else:
            ctk.CTkLabel(logo_frame, text="ESTACALAB",
                         font=FONTE_TITULO_APP,
                         text_color=COR_TEXTO_BRANCO).place(relx=0.5, rely=0.38, anchor="center")
            ctk.CTkLabel(logo_frame, text="Análise de Fundações",
                         font=FONTE_CAPTION,
                         text_color=COR_TEXTO_SIDEBAR).place(relx=0.5, rely=0.72, anchor="center")

        # Itens de navegação
        nav_frame = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        nav_frame.columnconfigure(0, weight=1)
        self.sidebar.rowconfigure(1, weight=1)

        row_nav = 0
        for chave, icone, label, is_secao in self.ITENS_SIDEBAR:
            if is_secao:
                ctk.CTkLabel(nav_frame, text=label,
                              font=FONTE_SIDEBAR_SECAO,
                              text_color="#94A3B8",
                              anchor="w").grid(row=row_nav, column=0,
                                               sticky="w", padx=16,
                                               pady=(10, 2))
            else:
                btn = ctk.CTkButton(
                    nav_frame,
                    text=f"  {icone}  {label}",
                    font=FONTE_SIDEBAR_ITEM,
                    fg_color="transparent",
                    text_color=COR_TEXTO_SIDEBAR,
                    hover_color=COR_SIDEBAR_HOVER,
                    anchor="w",
                    height=36,
                    corner_radius=6,
                    command=lambda c=chave: self._navegar(c)
                )
                btn.grid(row=row_nav, column=0, sticky="ew",
                         padx=8, pady=1)
                self._btn_sidebar[chave] = btn

            row_nav += 1

        # Separador
        ctk.CTkFrame(nav_frame, height=1,
                     fg_color="#2D4570").grid(
            row=row_nav, column=0, sticky="ew", padx=16, pady=8)
        row_nav += 1

        # Rodapé da sidebar
        rodape = [
            ("salvar_proj", "💾", "Salvar Projeto"),
            ("abrir_proj",  "📂", "Abrir Projeto"),
            ("sobre",       "ℹ", "Sobre o Sistema"),
        ]
        for chave, icone, label in rodape:
            btn_r = ctk.CTkButton(
                nav_frame,
                text=f"  {icone}  {label}",
                font=FONTE_SIDEBAR_ITEM,
                fg_color="transparent",
                text_color="#94A3B8",
                hover_color=COR_SIDEBAR_HOVER,
                anchor="w",
                height=32,
                corner_radius=6,
                command=getattr(self, f"_acao_{chave}") if chave != "sobre" else lambda: self._navegar("sobre")
            )
            btn_r.grid(row=row_nav, column=0, sticky="ew", padx=8, pady=1)
            row_nav += 1

        # Desenvolvedor
        dev_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        dev_frame.grid(row=row_nav, column=0, pady=(15, 8), sticky="sw", padx=16)
        
        ctk.CTkLabel(dev_frame, text="v1.0 • 2026",
                     font=FONTE_CAPTION,
                     text_color="#475569").pack(anchor="w")
        ctk.CTkLabel(dev_frame, text="Desenvolvido por:",
                     font=FONTE_CAPTION,
                     text_color="#475569").pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(dev_frame, text="Willian Bortolucci",
                     font=("Segoe UI", 10, "bold"),
                     text_color="#94A3B8").pack(anchor="w")

    # ─────────────────────────────────────────────────────────
    # Header superior
    # ─────────────────────────────────────────────────────────
    def _construir_header(self):
        self.header = ctk.CTkFrame(self,
                                    fg_color=COR_HEADER,
                                    border_color=COR_HEADER_BORDA,
                                    border_width=1,
                                    corner_radius=0,
                                    height=HEADER_ALTURA)
        self.header.grid(row=0, column=1, sticky="ew")
        self.header.grid_propagate(False)
        self.header.columnconfigure(1, weight=1)

        # Nome da tela ativa
        self.lbl_tela = ctk.CTkLabel(self.header, text="Dados do Projeto",
                                      font=FONTE_SUBTITULO,
                                      text_color=COR_TEXTO_PRIMARIO)
        self.lbl_tela.grid(row=0, column=0, padx=24, pady=0, sticky="w")

        # Lado direito: projeto + status + botão
        frame_dir = ctk.CTkFrame(self.header, fg_color="transparent")
        frame_dir.grid(row=0, column=2, sticky="e", padx=16)

        ctk.CTkLabel(frame_dir, text="Projeto:",
                     font=FONTE_LABEL_SM,
                     text_color=COR_TEXTO_SECUNDARIO).pack(side="left", padx=(0, 4))

        self.lbl_projeto = ctk.CTkLabel(frame_dir,
                                         text=state.nome_projeto,
                                         font=FONTE_LABEL_BOLD,
                                         text_color=COR_TEXTO_PRIMARIO)
        self.lbl_projeto.pack(side="left", padx=(0, 16))

        # Status das Análises
        self.frame_status_analises = ctk.CTkFrame(self.header, fg_color="transparent")
        self.frame_status_analises.grid(row=0, column=1, sticky="nsew", padx=16)
        
        # Centralizando o frame de status na coluna 1
        self.frame_status_analises.columnconfigure(0, weight=1)
        self.frame_status_analises.rowconfigure(0, weight=1)
        
        # Container interno para os labels
        container_status = ctk.CTkFrame(self.frame_status_analises, fg_color="transparent")
        container_status.grid(row=0, column=0)
        
        # Labels de Status
        ctk.CTkLabel(container_status, text="Capacidade: ", font=FONTE_LABEL_SM, text_color=COR_TEXTO_PRIMARIO).pack(side="left", padx=(0, 0))
        self.lbl_status_capacidade = ctk.CTkLabel(container_status, text="Não calculada", font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO)
        self.lbl_status_capacidade.pack(side="left", padx=(0, 16))
        
        ctk.CTkLabel(container_status, text="Dimensionamento: ", font=FONTE_LABEL_SM, text_color=COR_TEXTO_PRIMARIO).pack(side="left", padx=(0, 0))
        self.lbl_status_dimensionamento = ctk.CTkLabel(container_status, text="Não calculado", font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO)
        self.lbl_status_dimensionamento.pack(side="left", padx=(0, 16))
        
        ctk.CTkLabel(container_status, text="Recalque: ", font=FONTE_LABEL_SM, text_color=COR_TEXTO_PRIMARIO).pack(side="left", padx=(0, 0))
        self.lbl_status_recalque = ctk.CTkLabel(container_status, text="Não calculado", font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO)
        self.lbl_status_recalque.pack(side="left", padx=(0, 0))

        ctk.CTkButton(frame_dir, text="+ Novo Projeto",
                      font=FONTE_BOTAO,
                      fg_color=COR_PRIMARIA,
                      hover_color=COR_PRIMARIA_HOVER,
                      text_color=COR_TEXTO_BRANCO,
                      height=32,
                      corner_radius=RAIO_BORDA,
                      command=self._novo_projeto).pack(side="left")

        state.registrar_callback(self._atualizar_header)
        # Força atualização inicial
        self._atualizar_header()

    def _atualizar_header(self):
        self.lbl_projeto.configure(text=state.nome_projeto)
        
        # 1. Capacidade
        selecionados = state.metodos_selecionados
        if len(selecionados) == 0:
            self.lbl_status_capacidade.configure(text="Não calculada", text_color=COR_TEXTO_SECUNDARIO)
        else:
            qtd_calculados = 0
            mapa_df = {
                "aoki": state.df_aoki,
                "decourt": state.df_decourt,
                "teixeira": state.df_teixeira,
                "monteiro": state.df_monteiro,
                "berberian": state.df_berberian
            }
            for metodo in selecionados:
                df = mapa_df.get(metodo)
                if df is not None:
                    qtd_calculados += 1
            
            if qtd_calculados == 0:
                self.lbl_status_capacidade.configure(text="Não calculada", text_color=COR_TEXTO_SECUNDARIO)
            elif qtd_calculados == len(selecionados):
                self.lbl_status_capacidade.configure(text="Calculada", text_color=COR_SUCESSO)
            else:
                self.lbl_status_capacidade.configure(text="Parcial", text_color=COR_ALERTA)
                
        # 2. Dimensionamento
        dim_calculado = any(
            df is not None and not df.empty
            for df in state.df_dimensionamento.values()
        )
        if dim_calculado:
            self.lbl_status_dimensionamento.configure(text="Calculado", text_color=COR_SUCESSO)
        else:
            self.lbl_status_dimensionamento.configure(text="Não calculado", text_color=COR_TEXTO_SECUNDARIO)
            
        # 3. Recalque
        if state.df_recalque is not None:
            self.lbl_status_recalque.configure(text="Calculado", text_color=COR_SUCESSO)
        else:
            self.lbl_status_recalque.configure(text="Não calculado", text_color=COR_TEXTO_SECUNDARIO)

    # ─────────────────────────────────────────────────────────
    # Área de conteúdo
    # ─────────────────────────────────────────────────────────
    def _construir_area_conteudo(self):
        self.frame_conteudo = ctk.CTkFrame(self,
                                            fg_color=COR_FUNDO,
                                            corner_radius=0)
        self.frame_conteudo.grid(row=1, column=1, sticky="nsew")
        self.frame_conteudo.columnconfigure(0, weight=1)
        self.frame_conteudo.rowconfigure(0, weight=1)

    # ─────────────────────────────────────────────────────────
    # Navegação
    # ─────────────────────────────────────────────────────────
    def _navegar(self, chave: str):
        # Esconde tela atual
        if self._tela_ativa is not None:
            self._tela_ativa.grid_remove()

        # Cria tela se não está em cache
        if chave not in self._telas_cache:
            self._telas_cache[chave] = self._criar_tela(chave)

        tela = self._telas_cache[chave]
        tela.grid(row=0, column=0, sticky="nsew")
        self._tela_ativa = tela

        # Notifica a tela de que está sendo exibida (permite atualização sem recriar)
        if hasattr(tela, "on_show"):
            tela.on_show()

        # Atualiza sidebar
        for c, btn in self._btn_sidebar.items():
            btn.configure(
                fg_color=COR_SIDEBAR_ATIVO if c == chave else "transparent",
                text_color=COR_TEXTO_BRANCO
            )

        # Atualiza header
        nomes = {
            "projeto":    "Dados do Projeto",
            "fundacao":   "Dados da Fundação",
            "sondagem":   "Sondagem SPT",
            "capacidade": "Capacidade de Carga",
            "pilares":    "Mapa de Pilares",
            "recalque":   "Recalque",
            "resultados": "Resultados",
            "comparacao": "Comparação entre Métodos",
            "memoria":    "Memória de Cálculo",
            "graficos":   "Gráficos",
            "sobre":      "Sobre o Sistema",
        }
        self.lbl_tela.configure(text=nomes.get(chave, chave))

    def _criar_tela(self, chave: str) -> ctk.CTkFrame:
        kwargs = {"master": self.frame_conteudo, "nav_callback": self._navegar}
        mapa = {
            "projeto":    TelaProjeto,
            "fundacao":   TelaFundacao,
            "sondagem":   TelaSondagem,
            "capacidade": TelaCapacidade,
            "pilares":    TelaPilares,
            "recalque":   TelaRecalque,
            "resultados": TelaResultados,
            "comparacao": TelaComparacao,
            "memoria":    TelaMemoria,
            "graficos":   TelaGraficos,
            "sobre":      TelaSobre,
        }
        cls = mapa.get(chave)
        if cls is None:
            raise ValueError(f"Tela desconhecida: {chave}")
        return cls(**kwargs)

    # ─────────────────────────────────────────────────────────
    # Ações do rodapé da sidebar
    # ─────────────────────────────────────────────────────────
    def _novo_projeto(self):
        dialog = DialogNovoProjeto(self)
        self.wait_window(dialog)
        
        if dialog.result == "cancelar":
            return
            
        if dialog.result == "salvar":
            sucesso = self._acao_salvar_proj()
            if not sucesso:
                return
                
        if dialog.result == "descartar":
            resposta = messagebox.askyesno(
                "Atenção",
                "Os dados não salvos do projeto atual serão descartados.\nDeseja continuar?"
            )
            if not resposta:
                return

        # Destrói cache PRIMEIRO para desregistrar callbacks
        for tela in list(self._telas_cache.values()):
            tela.destroy()
        self._telas_cache = {}
        self._tela_ativa = None
        
        # Só depois reseta os dados
        state.reset()
        state.aplicar_defaults_usuario()
        state.notificar()
        self._navegar("projeto")

    def _confirmar_alteracoes_pendentes(self) -> bool:
        pendencias = state.obter_pendencias()
        if not pendencias:
            return True

        from tkinter import messagebox

        # 1. Projeto
        if "projeto" in pendencias:
            tela_proj = self._telas_cache.get("projeto")
            if tela_proj:
                tela_proj._salvar()
                if "projeto" in state.obter_pendencias():
                    self._navegar("projeto")
                    return False

        # 2. Fundação e Sondagem
        pendencias = state.obter_pendencias()
        has_fund = "fundacao" in pendencias
        has_sond = "sondagem" in pendencias

        if has_fund and has_sond:
            tela_fund = self._telas_cache.get("fundacao")
            tela_sond = self._telas_cache.get("sondagem")
            
            try:
                dados_fund = tela_fund._extrair_dados()
            except Exception as e:
                messagebox.showerror("Erro na Fundação", str(e))
                self._navegar("fundacao")
                return False
                
            try:
                dados_sond = tela_sond._extrair_dados()
            except Exception as e:
                messagebox.showerror("Erro na Sondagem", str(e))
                self._navegar("sondagem")
                return False

            from gui.project_commit import confirmar_fundacao_sondagem
            from gui.validation import ValidationError
            snapshot_fund = {
                "tipo_estaca": state.tipo_estaca,
                "forma_estaca": state.forma_estaca,
                "dimensoes_estaca": state.dimensoes_estaca.copy(),
                "criterio_ponta_metalica": state.criterio_ponta_metalica,
                "cota_inicio": state.cota_inicio
            }
            snapshot_sond = tela_sond._estado_salvo
            
            try:
                sucesso = confirmar_fundacao_sondagem(state, dados_fund, dados_sond, snapshot_fund, snapshot_sond)
                if sucesso:
                    state.marcar_salvo("fundacao")
                    state.marcar_salvo("sondagem")
                    tela_fund._atualizar_header()
                    import copy
                    tela_sond._estado_salvo = {
                        "camadas": copy.deepcopy(state.camadas),
                        "linha_agua": state.linha_agua,
                        "solo_sfl": state.solo_sfl
                    }
                    tela_sond._atualizar_header()
            except ValidationError as e:
                messagebox.showerror("Validação", str(e))
                self._navegar("fundacao")
                return False
                
        elif has_fund:
            tela_fund = self._telas_cache.get("fundacao")
            if tela_fund:
                tela_fund._salvar()
                if "fundacao" in state.obter_pendencias():
                    self._navegar("fundacao")
                    return False
                
        elif has_sond:
            tela_sond = self._telas_cache.get("sondagem")
            if tela_sond:
                tela_sond._salvar()
                if "sondagem" in state.obter_pendencias():
                    self._navegar("sondagem")
                    return False

        # 3. Pilares
        if "pilares" in state.obter_pendencias():
            tela_pilares = self._telas_cache.get("pilares")
            if tela_pilares:
                sucesso = tela_pilares._confirmar_pendencias()
                if not sucesso:
                    self._navegar("pilares")
                    return False
                    
        return True

    def _encerrar_aplicacao(self):
        for tela in list(self._telas_cache.values()):
            if isinstance(tela, TelaCapacidade):
                if hasattr(tela, '_after_queue_id') and tela._after_queue_id:
                    tela.after_cancel(tela._after_queue_id)
            tela.destroy()
        self._telas_cache = {}
        self.destroy()

    def _solicitar_fechamento(self):
        pendencias = state.obter_pendencias()
        modificado = state.projeto_modificado
        
        if pendencias or modificado:
            dialog = DialogDescartarPendente(self, pendencias, tipo="fechar", projeto_modificado=modificado)
            self.wait_window(dialog)
            
            if dialog.result == "cancelar":
                return
            
            if dialog.result == "salvar":
                sucesso_conf = self._confirmar_alteracoes_pendentes()
                if not sucesso_conf:
                    return
                sucesso_salvar = self._acao_salvar_proj()
                if not sucesso_salvar:
                    return
            
            # Se descartar (Sair sem salvar) ou se salvar com sucesso
            self._encerrar_aplicacao()
        else:
            self._encerrar_aplicacao()

    def _acao_salvar_proj(self):
        pendencias = state.obter_pendencias()
        if pendencias:
            messagebox.showwarning(
                "Atenção",
                "Você possui alterações em abas que não foram confirmadas.\n"
                "Acesse as abas correspondentes e salve-as antes de salvar o projeto."
            )
            return False
            
        caminho = filedialog.asksaveasfilename(
            defaultextension=".estacalab",
            filetypes=[("Projeto ESTACALAB", "*.estacalab"), ("JSON", "*.json")],
            title="Salvar Projeto",
            initialfile=f"{state.nome_projeto}.estacalab"
        )
        if caminho:
            try:
                state.salvar_json(caminho)
                messagebox.showinfo("Projeto Salvo", f"Projeto salvo em:\n{caminho}")
                return True
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar projeto:\n{e}")
                return False
        return False

    def _acao_abrir_proj(self):
        pendencias = state.obter_pendencias()
        modificado = state.projeto_modificado
        
        if pendencias or modificado:
            dialog = DialogDescartarPendente(self, pendencias, tipo="abrir", projeto_modificado=modificado)
            self.wait_window(dialog)
            
            if dialog.result == "cancelar":
                return
                
            if dialog.result == "salvar":
                sucesso_conf = self._confirmar_alteracoes_pendentes()
                if not sucesso_conf:
                    return
                sucesso_salvar = self._acao_salvar_proj()
                if not sucesso_salvar:
                    return
            
            # Se descartar ou se salvou OK, prosseguir para escolher arquivo
            
        caminho = self._escolher_projeto_para_abrir()
        if caminho:
            self._carregar_projeto_do_caminho(caminho)

    def _escolher_projeto_para_abrir(self):
        return filedialog.askopenfilename(
            filetypes=[("Projeto ESTACALAB", "*.estacalab"), ("JSON", "*.json")],
            title="Abrir Projeto"
        )

    def _carregar_projeto_do_caminho(self, caminho):
        try:
            import json
            from gui.state import normalizar_dados_projeto
            
            with open(caminho, "r", encoding="utf-8") as f:
                dados_brutos = json.load(f)
            
            dados_limpos = normalizar_dados_projeto(dados_brutos)
            
            for tela in list(self._telas_cache.values()):
                tela.destroy()
            self._telas_cache = {}
            self._tela_ativa = None
            
            state.reset()
            state.aplicar_defaults_usuario()
            
            state.de_dict(dados_limpos)
            
            state.notificar()
            self._navegar("projeto")
            messagebox.showinfo("Projeto Aberto",
                                f"Projeto '{state.nome_projeto}' carregado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro ao Abrir",
                                 f"Não foi possível abrir o arquivo:\n{e}")
