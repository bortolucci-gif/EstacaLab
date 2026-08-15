"""
EstacaLab — Tela de Sondagem SPT.
Tabela editável de camadas + perfil geotécnico visual lateral.
"""

import tkinter as tk
import customtkinter as ctk
import copy
from gui.constants import *
from gui.components import (Card, CardTitulado, BotaoPrimario, BotaoSecundario,
                             BotaoPerigo, TituloPagina, Separador, MensagemStatus)
from gui.state import state
from gui.validation import (
    validar_nspt, validar_na, validar_na_vs_sondagem,
    validar_cota_vs_sondagem, ValidationError
)


class TelaSondagem(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=1)

        self._linhas_widgets = []  # lista de dicts com os widgets de cada linha
        self._selecionada    = None
        self._vars = {}
        self._carregando_ui = False
        
        # Snapshot do estado "limpo" para comparar depois no Salvar
        import copy
        self._estado_salvo = {
            'camadas': copy.deepcopy(state.camadas),
            'linha_agua': state.linha_agua,
            'solo_sfl': state.solo_sfl
        }

        self._carregando_ui = True
        try:
            self._construir()
        finally:
            self._carregando_ui = False

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Sondagem SPT",
                     subtitulo="Cadastro das camadas de solo e valores de NSPT").pack(anchor="w")
        Separador(self).grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=12)

        # ── Parâmetros Adicionais ─────────────────────────────
        card_add = CardTitulado(self, titulo="Parâmetros Adicionais",
                                 subtitulo="Nível d'água e solo especial (Teixeira)")
        card_add.grid(row=2, column=0, columnspan=2, sticky="ew", padx=24, pady=(0, 12))
        self._construir_adicionais(card_add.corpo)

        # ── Painel Esquerdo — Tabela ──────────────────────────
        frame_esq = ctk.CTkFrame(self, fg_color="transparent")
        frame_esq.grid(row=3, column=0, sticky="nsew", padx=(24, 8), pady=(0, 12))
        frame_esq.columnconfigure(0, weight=1)
        frame_esq.rowconfigure(1, weight=1)

        # Barra de ferramentas
        toolbar = ctk.CTkFrame(frame_esq, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        BotaoPrimario(toolbar, texto="+ Camada", comando=self._adicionar_camada,
                       width=110).pack(side="left", padx=(0, 6))
        BotaoSecundario(toolbar, texto="Duplicar", comando=self._duplicar,
                         width=90).pack(side="left", padx=(0, 6))
        BotaoSecundario(toolbar, texto="Aplicar Solo", comando=self._aplicar_solo,
                         width=110).pack(side="left", padx=(0, 6))
        BotaoPerigo(toolbar, texto="Excluir", comando=self._excluir,
                     width=80).pack(side="left", padx=(0, 6))
        BotaoSecundario(toolbar, texto="↑ Mover Acima", comando=self._mover_acima,
                         width=115).pack(side="left", padx=(0, 6))
        BotaoSecundario(toolbar, texto="↓ Mover Abaixo", comando=self._mover_abaixo,
                         width=120).pack(side="left")

        # Card da tabela
        card_tab = Card(frame_esq)
        card_tab.grid(row=1, column=0, sticky="nsew")
        card_tab.columnconfigure(0, weight=1)
        card_tab.rowconfigure(1, weight=1)

        # Cabeçalho da tabela
        self._construir_cabecalho(card_tab)

        # Área de scroll das linhas
        self.canvas_tab = tk.Canvas(card_tab, bg=COR_CARD, highlightthickness=0)
        vsb = ctk.CTkScrollbar(card_tab, orientation="vertical",
                                command=self.canvas_tab.yview)
        self.canvas_tab.configure(yscrollcommand=vsb.set)
        vsb.grid(row=1, column=1, sticky="ns")
        self.canvas_tab.grid(row=1, column=0, sticky="nsew")
        self.canvas_tab.bind("<Configure>", self._on_canvas_resize)
        self.canvas_tab.bind("<MouseWheel>", self._on_mousewheel)

        self.frame_linhas = tk.Frame(self.canvas_tab, bg=COR_CARD)
        self._cw = self.canvas_tab.create_window((0, 0), window=self.frame_linhas,
                                                  anchor="nw")
        self.frame_linhas.bind("<Configure>",
                               lambda e: self.canvas_tab.configure(
                                   scrollregion=self.canvas_tab.bbox("all")))

        # ── Painel Direito — Perfil Visual + Status ───────────
        frame_dir = ctk.CTkFrame(self, fg_color="transparent")
        frame_dir.grid(row=3, column=1, sticky="nsew", padx=(0, 24), pady=(0, 12))
        frame_dir.columnconfigure(0, weight=1)
        frame_dir.rowconfigure(0, weight=1)

        card_perf = CardTitulado(frame_dir,
                                  titulo="Perfil Visual",
                                  subtitulo="Cores apenas visuais, sem classificação normativa")
        card_perf.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        card_perf.rowconfigure(0, weight=1)

        self.canvas_perfil = tk.Canvas(card_perf.corpo, bg=COR_CARD,
                                        highlightthickness=0, width=220)
        self.canvas_perfil.pack(fill="both", expand=True)
        self.canvas_perfil.bind("<Configure>", self._on_canvas_perfil_resize)

        # Mensagem de status
        self.msg = MensagemStatus(frame_dir)
        self.msg.grid(row=1, column=0, sticky="w", pady=(0, 4))
        
        self.lbl_status = ctk.CTkLabel(frame_dir, text="✓ Dados salvos", text_color=COR_SUCESSO, font=FONTE_LABEL)
        self.lbl_status.grid(row=2, column=0, sticky="w", pady=(0, 4))

        # Botão salvar
        BotaoPrimario(frame_dir, texto="💾  Salvar Sondagem",
                       comando=self._salvar, width=180).grid(
            row=3, column=0, sticky="w")

        # Popula com dados existentes
        self._recarregar_tabela()

    def _construir_adicionais(self, master):
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=1)

        # Nível d'água
        frame_na = ctk.CTkFrame(master, fg_color="transparent")
        frame_na.grid(row=0, column=0, sticky="w")

        self._vars['tem_na'] = ctk.BooleanVar(value=(state.linha_agua is not None))
        self._vars['tem_na'].trace_add("write", self._on_edit)
        chk_na = ctk.CTkCheckBox(frame_na,
                                  text="Presença de Nível d'Água (N.A.)",
                                  variable=self._vars['tem_na'],
                                  font=FONTE_LABEL,
                                  command=self._toggle_na)
        chk_na.pack(anchor="w")

        self.frame_na_depth = ctk.CTkFrame(master, fg_color="transparent")
        self.frame_na_depth.grid(row=1, column=0, sticky="w", pady=(4, 0))

        ctk.CTkLabel(self.frame_na_depth,
                     text="Cota do N.A. [m]:", font=FONTE_LABEL_SM,
                     text_color=COR_TEXTO_SECUNDARIO).pack(side="left")
        self._vars['linha_agua'] = ctk.StringVar(
            value=str(state.linha_agua) if state.linha_agua is not None else ""
        )
        self._vars['linha_agua'].trace_add("write", self._on_na_edit)
        self.entry_na = ctk.CTkEntry(self.frame_na_depth,
                     textvariable=self._vars['linha_agua'],
                     width=90, font=FONTE_LABEL_SM,
                     placeholder_text="Ex.: -5")
        self.entry_na.pack(side="left", padx=8)
        ctk.CTkLabel(self.frame_na_depth, text="Informe cota inteira negativa (ex.: -3).",
                     font=FONTE_CAPTION, text_color=COR_TEXTO_SECUNDARIO).pack(side="left", padx=(0, 8))
        self._toggle_na()

        # Solo fluviolagunar (Teixeira)
        frame_sfl = ctk.CTkFrame(master, fg_color="transparent")
        frame_sfl.grid(row=0, column=1, sticky="w", padx=20)

        self._vars['solo_sfl'] = ctk.BooleanVar(value=state.solo_sfl)
        self._vars['solo_sfl'].trace_add("write", self._on_edit)
        ctk.CTkCheckBox(frame_sfl,
                         text="Solo Fluviolagunar (Teixeira — SFL)",
                         variable=self._vars['solo_sfl'],
                         font=FONTE_LABEL).pack(anchor="w", pady=(0, 4))
        ctk.CTkLabel(frame_sfl,
                     text="Aplica ql = 25 kPa para argilas moles (NSPT ≤ 3) até 25 m\n"
                          "conforme critério do método de Teixeira (1996).",
                     font=FONTE_CAPTION,
                     text_color=COR_TEXTO_SECUNDARIO,
                     justify="left").pack(anchor="w", padx=28)

    def _toggle_na(self):
        if self._vars['tem_na'].get():
            self.frame_na_depth.grid()
            self.entry_na.focus()
        else:
            self._vars['linha_agua'].set("")
            self.frame_na_depth.grid_remove()
            
        if hasattr(self, "canvas_perfil"):
            self._desenhar_perfil()

    def _construir_cabecalho(self, master):
        cols = ["#", "Cota (m)", "NSPT", "Tipo de Solo"]
        larguras = [30, 70, 70, 280]
        frame_h = ctk.CTkFrame(master, fg_color="#EFF6FF", corner_radius=0)
        frame_h.grid(row=0, column=0, columnspan=2, sticky="ew")
        for i, (col, larg) in enumerate(zip(cols, larguras)):
            tk.Label(frame_h, text=col,
                     font=(FONTE_FAMILIA, 9, "bold"),
                     bg="#EFF6FF", fg=COR_TEXTO_PRIMARIO,
                     width=larg // 7, anchor="center",
                     pady=6).grid(row=0, column=i, sticky="nsew", padx=1)
            frame_h.columnconfigure(i, weight=1 if i == 3 else 0)

    def _on_canvas_resize(self, event):
        self.canvas_tab.itemconfig(self._cw, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas_tab.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_perfil_resize(self, event):
        if getattr(self, '_id_debounce_perfil', None):
            self.after_cancel(self._id_debounce_perfil)
        self._id_debounce_perfil = self.after(100, self._desenhar_perfil)

    # ─────────────────────────────────────────────────────────
    # Renderização das linhas
    # ─────────────────────────────────────────────────────────
    def _recarregar_tabela(self):
        self._carregando_ui = True
        try:
            for w in self.frame_linhas.winfo_children():
                w.destroy()
            self._linhas_widgets = []
            self._selecionada = None

            for i, cam in enumerate(state.camadas):
                self._adicionar_linha_widget(i, cam)

            self._desenhar_perfil()
        finally:
            self._carregando_ui = False
            self._atualizar_header()
            
            # Se for um novo carregamento vindo do state (ex: abrir projeto), 
            # não deve haver pendências e o snapshot deve espelhar o state.
            if not state.tem_pendencias(["sondagem"]):
                import copy
                self._estado_salvo = {
                    'camadas': copy.deepcopy(state.camadas),
                    'linha_agua': state.linha_agua,
                    'solo_sfl': state.solo_sfl
                }

    def _adicionar_linha_widget(self, idx, cam):
        bg = "#F8FAFC" if idx % 2 == 0 else COR_CARD

        row_f = tk.Frame(self.frame_linhas, bg=bg, cursor="hand2")
        row_f.grid(row=idx, column=0, sticky="ew")
        self.frame_linhas.columnconfigure(0, weight=1)

        row_f.bind("<Button-1>", lambda e, i=idx: self._selecionar(i))

        # Número da camada
        tk.Label(row_f, text=str(idx + 1), bg=bg,
                 fg=COR_TEXTO_SECUNDARIO, font=(FONTE_FAMILIA, 9),
                 width=3, anchor="center").grid(row=0, column=0, padx=4, pady=3)

        # Cota (calculada automaticamente, somente leitura)
        tk.Label(row_f, text=f"{-(idx + 1)}", bg=bg,
                 fg=COR_TEXTO_PRIMARIO, font=(FONTE_MONO, 9),
                 width=7, anchor="center").grid(row=0, column=1, padx=4)

        # NSPT — Entry editável
        var_nspt = tk.StringVar(value=str(cam['nspt']).replace('.', ','))
        var_nspt.trace_add("write", self._on_edit)
        entry_nspt = tk.Entry(row_f, textvariable=var_nspt,
                               font=(FONTE_MONO, 9),
                               width=6, relief="flat",
                               bg="#FAFAFA", fg=COR_TEXTO_PRIMARIO,
                               bd=1, highlightthickness=1,
                               highlightbackground=COR_BORDA)
        entry_nspt.grid(row=0, column=2, padx=4, pady=2)
        entry_nspt.bind("<FocusOut>", lambda e, i=idx: self._commit_nspt(i))
        entry_nspt.bind("<Return>",   lambda e, i=idx: self._commit_nspt(i))

        # Solo — Combobox
        var_solo = tk.StringVar(value=codigo_para_display(cam['cod_solo']))
        var_solo.trace_add("write", self._on_edit)
        cb_solo = ctk.CTkComboBox(row_f,
                                   variable=var_solo,
                                   values=LISTA_NOMES_SOLO,
                                   font=(FONTE_FAMILIA, 9),
                                   dropdown_font=(FONTE_FAMILIA, 9),
                                   width=270, state="readonly",
                                   fg_color=bg,
                                   border_color=COR_BORDA,
                                   button_color=COR_BORDA,
                                   command=lambda val, i=idx: self._commit_solo(i, val))
        cb_solo.grid(row=0, column=3, padx=4, pady=2, sticky="ew")
        row_f.columnconfigure(3, weight=1)

        self._linhas_widgets.append({
            'frame':    row_f,
            'var_nspt': var_nspt,
            'var_solo': var_solo,
            'bg':       bg,
        })

    def _selecionar(self, idx):
        # Deselect anterior
        if self._selecionada is not None and self._selecionada < len(self._linhas_widgets):
            prev = self._linhas_widgets[self._selecionada]
            prev['frame'].configure(bg=prev['bg'])

        self._selecionada = idx
        if idx < len(self._linhas_widgets):
            self._linhas_widgets[idx]['frame'].configure(bg="#DBEAFE")

    def _commit_nspt(self, idx):
        wdg = self._linhas_widgets[idx]
        try:
            val = validar_nspt(wdg['var_nspt'].get(), idx + 1)
            state.camadas[idx]['nspt'] = val
            self._on_edit()
            self._desenhar_perfil()
        except ValidationError as e:
            # Desfaz
            wdg['var_nspt'].set(str(state.camadas[idx]['nspt']).replace('.', ','))
            self.msg.erro(str(e))

    def _commit_solo(self, idx, val):
        wdg = self._linhas_widgets[idx]
        try:
            cod = solo_display_para_codigo(val)
            state.camadas[idx]['cod_solo'] = cod
            self._on_edit()
            self._desenhar_perfil()
        except ValidationError as e:
            # Desfaz
            wdg['var_solo'].set(codigo_para_display(state.camadas[idx]['cod_solo']))
            self.msg.erro(str(e))

    # ─────────────────────────────────────────────────────────
    # Ações da toolbar
    # ─────────────────────────────────────────────────────────
    def _adicionar_camada(self):
        n = len(state.camadas)
        cod_default = state.camadas[-1]['cod_solo'] if state.camadas else 31
        state.camadas.append({'cota': -(n + 1), 'nspt': 0, 'cod_solo': cod_default})
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionar(n)
        self.msg.ok(f"Camada {n + 1} adicionada.")

    def _duplicar(self):
        if self._selecionada is None or self._selecionada >= len(state.camadas):
            self.msg.alerta("Selecione uma camada para duplicar.")
            return
        original = state.camadas[self._selecionada].copy()
        idx_insert = self._selecionada + 1
        state.camadas.insert(idx_insert, original)
        # Recalcula cotas
        for i, cam in enumerate(state.camadas):
            cam['cota'] = -(i + 1)
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionar(idx_insert)
        self.msg.ok("Camada duplicada.")

    def _excluir(self):
        if self._selecionada is None or self._selecionada >= len(state.camadas):
            self.msg.alerta("Selecione uma camada para excluir.")
            return
        state.camadas.pop(self._selecionada)
        for i, cam in enumerate(state.camadas):
            cam['cota'] = -(i + 1)
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionada = None
        self.msg.ok("Camada excluída.")

    def _aplicar_solo(self):
        """Replica o tipo de solo da camada selecionada para todas as camadas abaixo."""
        if self._selecionada is None or self._selecionada >= len(state.camadas):
            self.msg.alerta("Selecione a camada de referência.")
            return
        cod = state.camadas[self._selecionada]['cod_solo']
        for i in range(self._selecionada, len(state.camadas)):
            state.camadas[i]['cod_solo'] = cod
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionar(self._selecionada)
        self.msg.ok(f"Solo '{LISTA_TIPOS_SOLO.get(cod)}' aplicado a partir da camada {self._selecionada + 1}.")

    def _mover_acima(self):
        if self._selecionada is None or self._selecionada <= 0:
            return
        idx = self._selecionada
        state.camadas[idx], state.camadas[idx - 1] = state.camadas[idx - 1], state.camadas[idx]
        for i, cam in enumerate(state.camadas):
            cam['cota'] = -(i + 1)
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionar(idx - 1)

    def _mover_abaixo(self):
        if self._selecionada is None or self._selecionada >= len(state.camadas) - 1:
            return
        idx = self._selecionada
        state.camadas[idx], state.camadas[idx + 1] = state.camadas[idx + 1], state.camadas[idx]
        for i, cam in enumerate(state.camadas):
            cam['cota'] = -(i + 1)
        self._on_edit()
        state.notificar()
        self._recarregar_tabela()
        self._selecionar(idx + 1)

    def _invalida_calculos(self):
        state.df_aoki = state.df_decourt = state.df_teixeira = None
        state.df_monteiro = state.df_berberian = state.df_media = None
        state.metodos_media = []
        state.df_dimensionamento = {}
        state.df_recalque = None

    def _extrair_dados(self) -> dict:
        """
        Extrai e normaliza os dados da interface sem modificar o AppState.
        Pode levantar ValidationError.
        """
        if not self._linhas_widgets:
            raise ValidationError("Nenhuma camada cadastrada na sondagem.")

        novas_camadas = []
        for i, wdg in enumerate(self._linhas_widgets):
            nspt_val = validar_nspt(wdg['var_nspt'].get(), i + 1)
            cod_solo = solo_display_para_codigo(wdg['var_solo'].get())
            cota = state.camadas[i]['cota'] if i < len(state.camadas) else -(i + 1)
            novas_camadas.append({
                'cota': cota,
                'nspt': nspt_val,
                'cod_solo': cod_solo
            })
            
        novo_solo_sfl = self._vars['solo_sfl'].get()
        
        nova_linha_agua = None
        if self._vars['tem_na'].get():
            valor_na = self._vars['linha_agua'].get().strip()
            if not valor_na:
                raise ValidationError("Informe a Cota do N.A. ou desmarque a opção de presença de Nível d'Água.")
            nova_linha_agua = validar_na(valor_na)
            
        return {
            "camadas": novas_camadas,
            "solo_sfl": novo_solo_sfl,
            "linha_agua": nova_linha_agua
        }

    def _salvar(self):
        try:
            dados = self._extrair_dados()
            
            novas_camadas = dados["camadas"]
            nova_linha_agua = dados["linha_agua"]
            novo_solo_sfl = dados["solo_sfl"]
            
            if nova_linha_agua is not None:
                validar_na_vs_sondagem(nova_linha_agua, novas_camadas)

            # Valida cota de arrasamento preexistente contra nova sondagem
            if state.cota_inicio is not None:
                validar_cota_vs_sondagem(state.cota_inicio, novas_camadas)

        except ValidationError as e:
            self.msg.erro(str(e))
            return
        except Exception as e:
            self.msg.erro(f"Erro inesperado: {e}")
            return

        import copy
        
        # 1. Capturar estado antigo (o último snapshot salvo/carregado)
        camadas_antigas = self._estado_salvo['camadas']
        linha_agua_antiga = self._estado_salvo['linha_agua']
        solo_sfl_antigo = self._estado_salvo['solo_sfl']

        # 3. Calcular diferenças semânticas
        mudou_camadas = (novas_camadas != camadas_antigas)
        mudou_na = (nova_linha_agua != linha_agua_antiga)
        mudou_sfl = (novo_solo_sfl != solo_sfl_antigo)
        
        nenhuma_alteracao = not (mudou_camadas or mudou_na or mudou_sfl)

        # 4. Atualizar AppState
        state.camadas = novas_camadas
        state.linha_agua = nova_linha_agua
        state.solo_sfl = novo_solo_sfl

        if not nenhuma_alteracao:
            state.marcar_projeto_modificado()

        # 5. Executar invalidação correspondente
        if nenhuma_alteracao:
            # Se a tela estava "dirty", mas os valores reais não mudaram,
            # apenas limpa o dirty sem invalidar nada, e não precisa notificar.
            if state.tem_pendencias(["sondagem"]):
                state.marcar_salvo("sondagem")
                self._atualizar_header()
        else:
            if mudou_camadas or mudou_sfl:
                self._invalida_calculos()
            elif mudou_na:
                state.df_recalque = None
                
            state.marcar_salvo("sondagem")
            
            # Atualiza o snapshot para o novo estado salvo
            self._estado_salvo = {
                'camadas': copy.deepcopy(state.camadas),
                'linha_agua': state.linha_agua,
                'solo_sfl': state.solo_sfl
            }
            
            self._atualizar_header()
            state.notificar()

        self.msg.ok(f"{len(state.camadas)} camada(s) salvas.")

    def _on_edit(self, *args):
        if self._carregando_ui:
            return
        state.marcar_pendente("sondagem")
        self._atualizar_header()

    def _on_na_edit(self, *args):
        self._on_edit()
        if hasattr(self, 'canvas_perfil'):
            self._desenhar_perfil()

    def _atualizar_header(self):
        if state.tem_pendencias(["sondagem"]):
            self.lbl_status.configure(text="● Alterações não salvas", text_color=COR_ALERTA)
        else:
            self.lbl_status.configure(text=f"✓ {len(state.camadas)} camada(s) salvas.", text_color=COR_SUCESSO)

    # ─────────────────────────────────────────────────────────
    # Perfil visual
    # ─────────────────────────────────────────────────────────
    def _desenhar_perfil(self):
        c = self.canvas_perfil
        c.delete("all")
        c.update_idletasks()

        largura = c.winfo_width() or 220
        altura  = c.winfo_height() or 400
        camadas = state.camadas

        if not camadas:
            c.create_text(largura // 2, altura // 2,
                          text="Sem camadas", fill=COR_TEXTO_SECUNDARIO,
                          font=(FONTE_FAMILIA, 9))
            return

        n = len(camadas)
        marg_top = 24
        marg_bot = 12
        marg_esq = 40
        marg_dir = 36
        h_area = max(20, altura - marg_top - marg_bot)
        w_area = largura - marg_esq - marg_dir
        px_m = h_area / n

        # Nível do terreno
        c.create_line(marg_esq - 5, marg_top, largura - marg_dir, marg_top,
                      fill="#666", width=1.5, dash=(5, 3))
        c.create_text(marg_esq - 6, marg_top, text="0m", fill="#666",
                      font=(FONTE_FAMILIA, 7), anchor="e")

        for i, cam in enumerate(camadas):
            cod = cam['cod_solo']
            cor = cor_camada_por_codigo(cod)
            y1 = marg_top + i * px_m
            y2 = y1 + px_m

            c.create_rectangle(marg_esq, y1, marg_esq + w_area, y2,
                                fill=cor, outline=COR_BORDA, width=0.5)

            # Cota no fim da camada
            c.create_text(marg_esq - 3, y2, text=f"{-(i + 1)}m",
                          fill=COR_TEXTO_SECUNDARIO, font=(FONTE_FAMILIA, 6), anchor="e")

            # Nome do solo centralizado
            nome_solo = LISTA_TIPOS_SOLO.get(cod, "")
            try:
                if cor.startswith("#") and len(cor) == 7:
                    r, g, b = int(cor[1:3], 16), int(cor[3:5], 16), int(cor[5:7], 16)
                    brilho = (r * 299 + g * 587 + b * 114) / 1000
                    cor_txt = "#FFFFFF" if brilho < 128 else "#111827"
                else:
                    cor_txt = "#111827"
            except Exception:
                cor_txt = "#111827"
                
            c.create_text(marg_esq + w_area / 2, (y1 + y2) / 2,
                          text=nome_solo, fill=cor_txt,
                          font=(FONTE_FAMILIA, 8), anchor="center",
                          width=max(10, w_area - 4))

            # NSPT
            nspt_str = str(int(cam['nspt'])) if cam['nspt'] == int(cam['nspt']) else str(cam['nspt'])
            c.create_text(marg_esq + w_area + 3, (y1 + y2) / 2,
                          text=nspt_str, fill=COR_TEXTO_PRIMARIO,
                          font=(FONTE_FAMILIA, 7), anchor="w")

        # Cota de arrasamento
        arr = abs(int(state.cota_inicio))
        if arr <= n:
            y_arr = marg_top + arr * px_m
            c.create_line(marg_esq, y_arr, marg_esq + w_area, y_arr,
                          fill="#8B4513", width=1.5, dash=(8, 4))

        # Nível d'água (N.A.)
        if self._vars.get('tem_na') and self._vars['tem_na'].get():
            try:
                cota_na_str = self._vars.get('linha_agua').get()
                if cota_na_str:
                    cota_na = int(cota_na_str)
                    if cota_na < 0 and abs(cota_na) <= n:
                        y_na = marg_top + abs(cota_na) * px_m
                        c.create_line(marg_esq, y_na, marg_esq + w_area, y_na,
                                      fill="#2563EB", width=2)
                        c.create_text(marg_esq + 4, y_na - 6, text="N.A.", fill="#2563EB",
                                      font=(FONTE_FAMILIA, 7, "bold"), anchor="w")
            except ValueError:
                pass

        # Legenda no rodapé
        c.create_text(largura // 2, altura - 4,
                      text="Cores visuais | direita = NSPT",
                      fill=COR_TEXTO_SECUNDARIO, font=(FONTE_FAMILIA, 6),
                      anchor="center")
