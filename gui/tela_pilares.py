"""
EstacaLab — Tela de Mapa de Pilares.
Cadastro de pilares, representação esquemática e dimensionamento por método.
"""

import tkinter as tk
import customtkinter as ctk
from gui.constants import *
from gui.components import (Card, CardTitulado, BotaoPrimario, BotaoSecundario,
                             BotaoPerigo, TituloPagina, Separador, MensagemStatus,
                             TabelaDataFrame)
from gui.state import state
from gui.validation import validar_carga, ValidationError
from DimensionamentoPilares import dimensionar_pilares_metodo


class TelaPilares(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=3)
        self.rowconfigure(2, weight=1)

        self._selecionado = None
        self._linhas_widgets = []
        self._linhas_pendentes = set()
        self._carregando_ui = False

        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Mapa de Pilares",
                     subtitulo="Cadastro das cargas verticais e dimensionamento das estacas").pack(anchor="w")
        Separador(self).grid(row=1, column=0, columnspan=2,
                             sticky="ew", padx=0, pady=12)

        # ── Painel Esquerdo — Cadastro ────────────────────────
        frame_esq = ctk.CTkFrame(self, fg_color="transparent")
        frame_esq.grid(row=2, column=0, sticky="nsew",
                       padx=(24, 8), pady=(0, 12))
        frame_esq.columnconfigure(0, weight=1)
        frame_esq.rowconfigure(1, weight=1)

        # Toolbar
        tb = ctk.CTkFrame(frame_esq, fg_color="transparent")
        tb.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        BotaoPrimario(tb, texto="+ Pilar", comando=self._adicionar,
                       width=90).pack(side="left", padx=(0, 6))
        BotaoPerigo(tb, texto="Excluir", comando=self._excluir,
                     width=80).pack(side="left")

        # Tabela de cadastro
        card_tab = Card(frame_esq)
        card_tab.grid(row=1, column=0, sticky="nsew")
        card_tab.columnconfigure(0, weight=1)
        card_tab.rowconfigure(1, weight=1)

        # Cabeçalho tabela
        cab = ctk.CTkFrame(card_tab, fg_color="#EFF6FF", corner_radius=0)
        cab.grid(row=0, column=0, sticky="ew")
        for col_idx, txt in enumerate(["ID Pilar", "Carga (kN)"]):
            tk.Label(cab, text=txt,
                     font=(FONTE_FAMILIA, 9, "bold"),
                     bg="#EFF6FF", fg=COR_TEXTO_PRIMARIO,
                     width=14, anchor="center", pady=6).grid(
                row=0, column=col_idx, padx=1)
            cab.columnconfigure(col_idx, weight=1)

        # Linhas com scroll
        self.canvas_tab = tk.Canvas(card_tab, bg=COR_CARD, highlightthickness=0)
        self.vsb_pilares = ctk.CTkScrollbar(card_tab, orientation="vertical",
                                command=self.canvas_tab.yview)
        self.canvas_tab.configure(yscrollcommand=self.vsb_pilares.set)
        self.vsb_pilares.grid(row=1, column=1, sticky="ns")
        self.canvas_tab.grid(row=1, column=0, sticky="nsew")
        self.canvas_tab.bind("<Configure>", self._on_canvas_tab_configure)
        self.canvas_tab.bind("<MouseWheel>",
                             lambda e: self.canvas_tab.yview_scroll(
                                 int(-1 * (e.delta / 120)), "units"))

        self.frame_linhas = tk.Frame(self.canvas_tab, bg=COR_CARD)
        self._cw = self.canvas_tab.create_window((0, 0), window=self.frame_linhas,
                                                  anchor="nw")
        self.frame_linhas.bind("<Configure>", self._on_frame_linhas_configure)

        # ── Painel Direito — Planta + Dimensionamento ─────────
        frame_dir = ctk.CTkFrame(self, fg_color="transparent")
        frame_dir.grid(row=2, column=1, sticky="nsew",
                       padx=(0, 24), pady=(0, 12))
        frame_dir.columnconfigure(0, weight=1)
        frame_dir.rowconfigure(0, weight=1)
        frame_dir.rowconfigure(1, weight=2)

        # Planta esquemática
        card_planta = CardTitulado(frame_dir,
                                    titulo="Planta Esquemática",
                                    subtitulo="Representação gráfica esquemática — não é planta estrutural")
        card_planta.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        self.canvas_planta = tk.Canvas(card_planta.corpo, bg=COR_CARD,
                                        highlightthickness=0, height=200)
        self.canvas_planta.pack(fill="both", expand=True)
        self.canvas_planta.bind("<Button-1>", self._clicar_planta)

        # Dimensionamento
        frame_dim = ctk.CTkFrame(frame_dir, fg_color="transparent")
        frame_dim.grid(row=1, column=0, sticky="nsew")
        frame_dim.columnconfigure(0, weight=1)
        frame_dim.rowconfigure(1, weight=1)

        # Barra de controle do dimensionamento
        ctrl = ctk.CTkFrame(frame_dim, fg_color="transparent")
        ctrl.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ctk.CTkLabel(ctrl, text="Método:", font=FONTE_LABEL,
                     text_color=COR_TEXTO_SECUNDARIO).pack(side="left", padx=(0, 8))
        self._var_metodo = ctk.StringVar(value="aoki")
        opcoes_metodo = list(METODOS_NOMES.keys())
        cb_metodo = ctk.CTkComboBox(ctrl,
                                     variable=self._var_metodo,
                                     values=opcoes_metodo,
                                     width=200,
                                     font=FONTE_LABEL,
                                     state="readonly")
        cb_metodo.pack(side="left", padx=(0, 12))

        BotaoPrimario(ctrl, texto="▶  Dimensionar",
                       comando=self._dimensionar, width=150).pack(side="left")

        self.msg = MensagemStatus(ctrl)
        self.msg.pack(side="left", padx=(10, 0))

        card_dim_result = CardTitulado(frame_dim,
                                        titulo="Resultado do Dimensionamento",
                                        subtitulo="Cota final = cota de arrasamento − comprimento")
        card_dim_result.grid(row=1, column=0, sticky="nsew")
        card_dim_result.rowconfigure(2, weight=1)

        self.tabela_dim = TabelaDataFrame(card_dim_result.corpo)
        self.tabela_dim.pack(fill="both", expand=True)

        self.tabela_dim.canvas.bind("<Configure>", self._on_tabela_dim_configure, add="+")
        self.tabela_dim.frame_corpo.bind("<Configure>", self._on_tabela_dim_configure, add="+")

        self._recarregar_tabela()

    def _on_canvas_tab_configure(self, e):
        self.canvas_tab.itemconfig(self._cw, width=e.width)
        if getattr(self, '_id_deb_scroll_p', None):
            self.after_cancel(self._id_deb_scroll_p)
        self._id_deb_scroll_p = self.after(50, self._atualizar_scroll_pilares)

    def _on_frame_linhas_configure(self, e):
        self.canvas_tab.configure(scrollregion=self.canvas_tab.bbox("all"))
        if getattr(self, '_id_deb_scroll_p', None):
            self.after_cancel(self._id_deb_scroll_p)
        self._id_deb_scroll_p = self.after(50, self._atualizar_scroll_pilares)

    def _atualizar_scroll_pilares(self):
        bbox = self.canvas_tab.bbox("all")
        vsb_gridded = bool(self.vsb_pilares.winfo_manager())
        if not bbox:
            need_vsb = False
        else:
            altura_conteudo = bbox[3] - bbox[1]
            altura_canvas = self.canvas_tab.winfo_height()
            if altura_canvas <= 1:
                return
            need_vsb = altura_conteudo > altura_canvas
            
        if need_vsb != vsb_gridded:
            if need_vsb:
                self.vsb_pilares.grid(row=1, column=1, sticky="ns")
            else:
                self.vsb_pilares.grid_remove()

    def _on_tabela_dim_configure(self, event):
        if getattr(self, '_id_deb_scroll_dim', None):
            self.after_cancel(self._id_deb_scroll_dim)
        self._id_deb_scroll_dim = self.after(50, self._atualizar_scrollbars_dimensionamento)

    def _atualizar_scrollbars_dimensionamento(self):
        canvas = self.tabela_dim.canvas
        bbox = canvas.bbox("all")
        
        hsb_packed = bool(self.tabela_dim.hsb.winfo_manager())
        vsb_packed = bool(self.tabela_dim.vsb.winfo_manager())
        
        if not bbox:
            need_hsb = False
            need_vsb = False
        else:
            largura_conteudo = bbox[2] - bbox[0]
            altura_conteudo = bbox[3] - bbox[1]
            
            largura_canvas = canvas.winfo_width()
            altura_canvas = canvas.winfo_height()
            
            if largura_canvas <= 1 or altura_canvas <= 1:
                return
                
            need_hsb = largura_conteudo > largura_canvas
            need_vsb = altura_conteudo > altura_canvas
            
        if need_hsb != hsb_packed or need_vsb != vsb_packed:
            self.tabela_dim.canvas.pack_forget()
            self.tabela_dim.hsb.pack_forget()
            self.tabela_dim.vsb.pack_forget()
            
            if need_hsb:
                self.tabela_dim.hsb.pack(side="bottom", fill="x")
            if need_vsb:
                self.tabela_dim.vsb.pack(side="right", fill="y")
            self.tabela_dim.canvas.pack(side="left", fill="both", expand=True)

    def on_show(self):
        chave = self._var_metodo.get()
        if state.df_dimensionamento.get(chave) is None:
            self.tabela_dim.carregar(None)
            self._on_tabela_dim_configure(None)
            if hasattr(self, 'msg'): self.msg.limpar()

    def _invalidar_resultados_pilares(self):
        state.df_dimensionamento = {}
        state.df_recalque = None
        self.tabela_dim.carregar(None)
        self._on_tabela_dim_configure(None)
        if hasattr(self, 'msg'): self.msg.limpar()
        state.notificar()

    # ─────────────────────────────────────────────────────────
    # Gestão dos pilares
    # ─────────────────────────────────────────────────────────
    def _recarregar_tabela(self):
        self._carregando_ui = True
        try:
            for w in self.frame_linhas.winfo_children():
                w.destroy()
            self._linhas_widgets = []
            self._linhas_pendentes.clear()
            self._selecionado = None

            for i, pilar in enumerate(state.lista_pilares):
                self._adicionar_linha(i, pilar)

            self._desenhar_planta()
        finally:
            self._carregando_ui = False
            state.marcar_salvo("pilares")

    def _adicionar_linha(self, idx, pilar):
        bg = "#F8FAFC" if idx % 2 == 0 else COR_CARD
        row_f = tk.Frame(self.frame_linhas, bg=bg, cursor="hand2")
        row_f.grid(row=idx, column=0, sticky="ew")
        self.frame_linhas.columnconfigure(0, weight=1)
        row_f.bind("<Button-1>", lambda e, i=idx: self._selecionar(i))

        # ID do pilar
        var_id = tk.StringVar(value=str(pilar.get("Pilar", idx + 1)))
        var_id.trace_add("write", lambda *a, i=idx: self._on_edit_pilar(i))
        entry_id = tk.Entry(row_f, textvariable=var_id,
                             font=(FONTE_FAMILIA, 9), width=10,
                             relief="flat", bg=bg, bd=1,
                             highlightthickness=1, highlightbackground=COR_BORDA)
        entry_id.grid(row=0, column=0, padx=8, pady=3, sticky="ew")
        entry_id.bind("<FocusOut>", lambda e, i=idx: self._commit(i))
        row_f.columnconfigure(0, weight=1)

        # Carga
        var_carga = tk.StringVar(value=str(pilar.get("Carga (kN)", 0)).replace('.', ','))
        var_carga.trace_add("write", lambda *a, i=idx: self._on_edit_pilar(i))
        entry_carga = tk.Entry(row_f, textvariable=var_carga,
                                font=(FONTE_MONO, 9), width=10,
                                relief="flat", bg=bg, bd=1,
                                highlightthickness=1, highlightbackground=COR_BORDA)
        entry_carga.grid(row=0, column=1, padx=8, pady=3, sticky="ew")
        entry_carga.bind("<FocusOut>", lambda e, i=idx: self._commit(i))
        row_f.columnconfigure(1, weight=1)

        self._linhas_widgets.append({
            'frame': row_f, 'var_id': var_id,
            'var_carga': var_carga, 'bg': bg
        })

    def _selecionar(self, idx):
        if self._selecionado is not None and self._selecionado < len(self._linhas_widgets):
            prev = self._linhas_widgets[self._selecionado]
            prev['frame'].configure(bg=prev['bg'])
        self._selecionado = idx
        if idx < len(self._linhas_widgets):
            self._linhas_widgets[idx]['frame'].configure(bg="#DBEAFE")

    def _on_edit_pilar(self, idx):
        if self._carregando_ui:
            return
        self._linhas_pendentes.add(idx)
        state.marcar_pendente("pilares")

    def _commit(self, idx):
        wdg = self._linhas_widgets[idx]
        try:
            val_carga = validar_carga(wdg['var_carga'].get(), wdg['var_id'].get())
            novo_id = wdg['var_id'].get()
            
            pilar = state.lista_pilares[idx]
            if pilar["Pilar"] != novo_id or pilar["Carga (kN)"] != val_carga:
                pilar["Pilar"] = novo_id
                pilar["Carga (kN)"] = val_carga
                self._desenhar_planta()
                self._invalidar_resultados_pilares()
                state.marcar_projeto_modificado()
                
            self._linhas_pendentes.discard(idx)
            if not self._linhas_pendentes:
                state.marcar_salvo("pilares")
                
        except ValidationError as e:
            # Desfaz
            wdg['var_carga'].set(str(state.lista_pilares[idx]["Carga (kN)"]).replace('.', ','))
            self.msg.erro(str(e))

    def _confirmar_pendencias(self) -> bool:
        """Força o commit de todas as linhas pendentes.
        Retorna True se todos os commits foram bem-sucedidos (nenhuma pendência restou)."""
        for idx in list(self._linhas_pendentes):
            self._commit(idx)
        return not state.tem_pendencias(["pilares"])

    def _adicionar(self):
        n = len(state.lista_pilares) + 1
        state.lista_pilares.append({"Pilar": f"P{n}", "Carga (kN)": 100.0})
        self._invalidar_resultados_pilares()
        state.marcar_projeto_modificado()
        self._recarregar_tabela()

    def _excluir(self):
        if self._selecionado is None or self._selecionado >= len(state.lista_pilares):
            self.msg.alerta("Selecione um pilar para excluir.")
            return
        state.lista_pilares.pop(self._selecionado)
        self._invalidar_resultados_pilares()
        state.marcar_projeto_modificado()
        self._recarregar_tabela()

    # ─────────────────────────────────────────────────────────
    # Planta esquemática
    # ─────────────────────────────────────────────────────────
    def _desenhar_planta(self):
        c = self.canvas_planta
        c.delete("all")
        c.update_idletasks()
        W = c.winfo_width() or 400
        H = c.winfo_height() or 200

        pilares = state.lista_pilares
        if not pilares:
            c.create_text(W // 2, H // 2,
                          text="Nenhum pilar cadastrado",
                          fill=COR_TEXTO_SECUNDARIO, font=(FONTE_FAMILIA, 9))
            return

        n = len(pilares)
        cols = max(1, min(8, int(n ** 0.5) + 1))
        rows = (n + cols - 1) // cols

        max_carga = max(p.get("Carga (kN)", 1) for p in pilares) or 1
        cell_w = (W - 20) / cols
        cell_h = (H - 20) / rows

        c.create_text(W // 2, 8,
                      text="Representação esquemática — não é planta estrutural",
                      fill=COR_TEXTO_SECUNDARIO, font=(FONTE_FAMILIA, 7))

        self._pilares_pos = []
        for i, pilar in enumerate(pilares):
            col_i = i % cols
            row_i = i // cols
            cx = 16 + col_i * cell_w + cell_w / 2
            cy = 20 + row_i * cell_h + cell_h / 2

            carga = pilar.get("Carga (kN)", 0)
            tamanho = 8 + int(22 * carga / max_carga)

            cor = "#2563EB" if i == self._selecionado else "#4B89D4"
            c.create_rectangle(cx - tamanho, cy - tamanho,
                                cx + tamanho, cy + tamanho,
                                fill=cor, outline="#1A2B4A", width=1.5)
            c.create_text(cx, cy, text=str(pilar.get("Pilar", i + 1)),
                          fill="white", font=(FONTE_FAMILIA, 7, "bold"))

            self._pilares_pos.append((cx, cy, tamanho, i))

    def _clicar_planta(self, event):
        for (cx, cy, tam, idx) in getattr(self, '_pilares_pos', []):
            if abs(event.x - cx) <= tam and abs(event.y - cy) <= tam:
                self._selecionar(idx)
                self._desenhar_planta()
                return

    # ─────────────────────────────────────────────────────────
    # Dimensionamento
    # ─────────────────────────────────────────────────────────
    def _dimensionar(self):
        if not state.lista_pilares:
            self.msg.erro("Cadastre os pilares antes de dimensionar.")
            return

        chave = self._var_metodo.get()

        mapa_df = {
            "aoki":      state.df_aoki,
            "decourt":   state.df_decourt,
            "teixeira":  state.df_teixeira,
            "monteiro":  state.df_monteiro,
            "berberian": state.df_berberian,
        }

        if chave == "media":
            if state.df_media is None:
                self.msg.erro("Calcule a capacidade de carga com 2 ou mais métodos para usar a média.")
                return
            df_base = state.df_media
        else:
            df_base = mapa_df.get(chave)

        if df_base is None:
            self.msg.erro(f"Calcule o método '{METODOS_NOMES.get(chave, chave)}' primeiro.")
            return

        try:
            # Commit das edições pendentes
            teve_alteracao = False
            for i, wdg in enumerate(self._linhas_widgets):
                if i < len(state.lista_pilares):
                    val_carga = validar_carga(wdg['var_carga'].get(), wdg['var_id'].get())
                    novo_id = wdg['var_id'].get()
                    
                    pilar = state.lista_pilares[i]
                    if pilar["Pilar"] != novo_id or pilar["Carga (kN)"] != val_carga:
                        pilar["Pilar"] = novo_id
                        pilar["Carga (kN)"] = val_carga
                        teve_alteracao = True
                        
            if teve_alteracao:
                self._invalidar_resultados_pilares()
                self._desenhar_planta()

            self._linhas_pendentes.clear()
            state.marcar_salvo("pilares")

            if state.tem_pendencias(["fundacao", "sondagem"]):
                import tkinter.messagebox as messagebox
                messagebox.showwarning("Alterações não salvas",
                                       "Existem alterações não salvas em:\n- Dados da Fundação ou\n- Sondagem SPT\n\nSalve essas alterações antes de calcular a capacidade de carga ou dimensionamento.")
                return

            df_dim = dimensionar_pilares_metodo(
                df_base, state.lista_pilares, state.cota_inicio)

            # Adiciona cota final
            df_dim = df_dim.copy()
            df_dim["Cota Final (m)"] = df_dim["Profundidade (m)"].apply(
                lambda p: round(-p, 1))

            state.df_dimensionamento[chave] = df_dim
            state.notificar()

            self.tabela_dim.carregar(
                df_dim,
                colunas_destaque=["Qtd. Estacas", "Comprimento Estaca (m)"]
            )
            self._on_tabela_dim_configure(None)
            self.msg.ok(f"Dimensionamento concluído — {METODOS_NOMES.get(chave, chave)}")

        except ValidationError as e:
            self.msg.erro(str(e))
        except Exception as e:
            self.msg.erro(f"Erro no dimensionamento: {e}")

