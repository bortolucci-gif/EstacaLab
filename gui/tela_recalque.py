"""
EstacaLab — Tela de Recalque.
Executa calcular_recalque_pilares() com os dados do estado atual e exibe resultados.
"""

import customtkinter as ctk
from gui.constants import *
from gui.components import (Card, CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador, MensagemStatus, TabelaDataFrame)
from gui.state import state
from CalculoRecalque import calcular_recalque_pilares, param_estaca_recalque
from DimensionamentoPilares import dimensionar_pilares_metodo


class TelaRecalque(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))

        TituloPagina(
            header,
            titulo="Estimativa de Recalque",
            subtitulo="Estimativa de recalque com base na metodologia de Aoki (1984)"
        ).pack(anchor="w")

        Separador(self).grid(
            row=1, column=0, sticky="ew", padx=0, pady=12
        )

        # ── Controles ────────────────────────────────────────
        painel_ctrl = ctk.CTkFrame(self, fg_color="transparent")
        painel_ctrl.grid(
            row=2, column=0, sticky="ew", padx=24, pady=(0, 12)
        )
        painel_ctrl.columnconfigure(0, weight=1)

        card_ctrl = CardTitulado(
            painel_ctrl,
            titulo="Configuração do Recalque",
            subtitulo="Dimensionamento utilizado: Aoki-Velloso (1975) (obrigatório)"
        )
        card_ctrl.grid(row=0, column=0, sticky="ew")

        frame_form = ctk.CTkFrame(
            card_ctrl.corpo,
            fg_color="transparent"
        )
        frame_form.pack(anchor="w", fill="x")

        # ── Card de parâmetros adotados ──────────────────────
        card_params = ctk.CTkFrame(
            frame_form,
            fg_color="#EFF6FF",
            border_color="#BFDBFE",
            border_width=1,
            corner_radius=6
        )
        card_params.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            card_params,
            text="Parâmetros adotados",
            font=(FONTE_LABEL[0], FONTE_LABEL[1], "bold"),
            text_color="#1E40AF"
        ).pack(anchor="w", padx=12, pady=(8, 4))

        self._lbl_ec = ctk.CTkLabel(
            card_params,
            text="Ec adotado: —",
            font=FONTE_LABEL,
            text_color=COR_TEXTO_PRIMARIO
        )
        self._lbl_ec.pack(anchor="w", padx=12)

        self._lbl_alfa = ctk.CTkLabel(
            card_params,
            text="α adotado: —",
            font=FONTE_LABEL,
            text_color=COR_TEXTO_PRIMARIO
        )
        self._lbl_alfa.pack(anchor="w", padx=12)

        ctk.CTkLabel(
            card_params,
            text="Os parâmetros são definidos automaticamente pelo programa em função do tipo de estaca selecionado.",
            font=FONTE_CAPTION,
            text_color=COR_TEXTO_SECUNDARIO,
            wraplength=680,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(4, 8))

        # ── Botão de calcular ────────────────────────────────
        BotaoPrimario(
            frame_form,
            texto="▶  Calcular Recalque",
            comando=self._calcular,
            width=200
        ).pack(anchor="w")

        self.msg = MensagemStatus(card_ctrl.corpo)
        self.msg.pack(anchor="w", pady=(8, 0))

        # Aviso metodológico
        aviso = ctk.CTkFrame(
            card_ctrl.corpo,
            fg_color="#FFF7ED",
            border_color="#FED7AA",
            border_width=1,
            corner_radius=4
        )
        aviso.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            aviso,
            text="ℹ  A estimativa de recalque utiliza como referência a metodologia de Aoki (1984), com adaptações computacionais descritas no TCC.\n"
                 "A avaliação de aceitabilidade depende do critério adotado no projeto e nas normas aplicáveis.",
            font=FONTE_CAPTION,
            text_color=COR_ALERTA,
            wraplength=700,
            justify="left"
        ).pack(padx=10, pady=8, anchor="w")

        # ── Tabela de resultados ─────────────────────────────
        frame_res = ctk.CTkFrame(self, fg_color="transparent")
        frame_res.grid(
            row=3, column=0, sticky="nsew",
            padx=24, pady=(0, 16)
        )
        frame_res.columnconfigure(0, weight=1)
        frame_res.rowconfigure(0, weight=1)

        self.card_tab = CardTitulado(
            frame_res,
            titulo="Resultados do Recalque por Pilar",
            subtitulo="ρ_e = encurtamento elástico | ρ_s = recalque no solo"
        )
        self.card_tab.grid(row=0, column=0, sticky="nsew")
        self.card_tab.rowconfigure(2, weight=1)

        self.tabela = TabelaDataFrame(self.card_tab.corpo)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.canvas.bind("<Configure>", self._on_tabela_configure, add="+")
        self.tabela.frame_corpo.bind("<Configure>", self._on_tabela_configure, add="+")

        if state.df_recalque is not None:
            self.tabela.carregar(
                state.df_recalque,
                colunas_destaque=["Recalque Total (mm)"]
            )
            self._on_tabela_configure(None)

        self._atualizar_params()

    def _on_tabela_configure(self, event):
        if getattr(self, '_id_deb_scroll', None):
            self.after_cancel(self._id_deb_scroll)
        self._id_deb_scroll = self.after(50, self._atualizar_scrollbars_resultados)

    def _atualizar_scrollbars_resultados(self):
        canvas = self.tabela.canvas
        bbox = canvas.bbox("all")
        
        hsb_packed = bool(self.tabela.hsb.winfo_manager())
        vsb_packed = bool(self.tabela.vsb.winfo_manager())
        
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
            self.tabela.canvas.pack_forget()
            self.tabela.hsb.pack_forget()
            self.tabela.vsb.pack_forget()
            
            if need_hsb:
                self.tabela.hsb.pack(side="bottom", fill="x")
            if need_vsb:
                self.tabela.vsb.pack(side="right", fill="y")
            self.tabela.canvas.pack(side="left", fill="both", expand=True)

    def _atualizar_params(self):
        tipo = state.tipo_estaca or ""

        if tipo:
            ec_gpa, alfa = param_estaca_recalque(tipo)
            self._lbl_ec.configure(
                text=f"Ec adotado: {ec_gpa} GPa"
            )
            self._lbl_alfa.configure(
                text=f"α adotado: {alfa}"
            )
        else:
            self._lbl_ec.configure(
                text="Ec adotado: — (tipo de estaca não definido)"
            )
            self._lbl_alfa.configure(
                text="α adotado: —"
            )

    def on_show(self):
        self._atualizar_params()

        if state.df_recalque is None:
            self.tabela.carregar(None)
            self._on_tabela_configure(None)

            if hasattr(self, 'msg'):
                self.msg.limpar()

    def _calcular(self):
        self._atualizar_params()

        if state.df_aoki is None:
            self.msg.erro(
                "Calcule a Capacidade de Carga (Aoki-Velloso) primeiro."
            )
            return

        if state.tem_pendencias(
            ["fundacao", "sondagem", "pilares"]
        ):
            import tkinter.messagebox as messagebox

            messagebox.showwarning(
                "Alterações não salvas",
                "Existem alterações não salvas em:\n"
                "- Dados da Fundação ou\n"
                "- Sondagem SPT ou\n"
                "- Pilares\n\n"
                "Salve essas alterações antes de calcular o recalque."
            )
            return

        if not state.lista_pilares:
            self.msg.erro(
                "Cadastre os pilares no Mapa de Pilares."
            )
            return

        try:
            # Obtém o dimensionamento pelo método de Aoki
            df_dim = state.df_dimensionamento.get("aoki")

            if df_dim is None:
                df_dim = dimensionar_pilares_metodo(
                    state.df_aoki,
                    state.lista_pilares,
                    state.cota_inicio
                )

            df_recalque = calcular_recalque_pilares(
                df_aoki=state.df_aoki,
                df_dimensionamento=df_dim,
                tipoEstaca=state.tipo_estaca,
                dimensoes=state.dimensoes_estaca,
                linha_agua=state.linha_agua,
                forma_estaca=state.forma_estaca,
                cota_inicio=state.cota_inicio,
                criterio_ponta_metalica=state.criterio_ponta_metalica
            )

            state.df_recalque = df_recalque
            state.notificar()

            self.tabela.carregar(
                df_recalque,
                colunas_destaque=["Recalque Total (mm)"]
            )
            self._on_tabela_configure(None)

            self.msg.ok(
                "Cálculo de recalque concluído."
            )

        except Exception as e:
            self.msg.erro(f"Erro: {e}")