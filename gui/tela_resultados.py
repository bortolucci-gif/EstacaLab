"""
EstacaLab — Tela de Resultados.
Exibe os DataFrames de cada método com cards de resumo.
"""

import customtkinter as ctk
from gui.constants import *
from gui.components import (Card, CardTitulado, CardMetrica, BotaoSecundario,
                             TituloPagina, Separador, TabelaDataFrame)
from gui.state import state
from gui.formatters import formatar_valor_tabela


class TelaResultados(ctk.CTkFrame):

    METODOS = [
        ("aoki",      "Aoki-Velloso",     "Carga Adm. (kN)",        "Rp (kN)",  "Rl Acumulado (kN)"),
        ("decourt",   "Décourt-Quaresma", "Carga Adm. Adotada (kN)","Rb (kN)",  "Rl (kN)"),
        ("teixeira",  "Teixeira",         "Carga Adm. (kN)",        "Qp (kN)",  "Ql (kN)"),
        ("monteiro",  "Monteiro",         "Carga Adm. (kN)",        "Rp (kN)",  "Rl (kN)"),
        ("berberian", "Berberian",        "Carga Adm. (kN)",        "Qp (kN)",  "Ql (kN)"),
    ]

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._metodo_sel = ctk.StringVar(value="aoki")
        self._construir()
        state.registrar_callback(self.atualizar)

    def destroy(self):
        state.desregistrar_callback(self.atualizar)
        super().destroy()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Resultados",
                     subtitulo="Capacidade de carga por método e cota").pack(anchor="w")
        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Cards de resumo (máxima carga adm.) ──────────────
        frame_cards = ctk.CTkFrame(self, fg_color="transparent")
        frame_cards.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))

        self._cards_metrica = {}
        for i, (chave, nome, col_adm, col_rp, col_rl) in enumerate(self.METODOS):
            card = CardMetrica(frame_cards,
                               titulo=nome,
                               valor="—",
                               unidade="kN",
                               cor_valor=COR_PRIMARIA)
            card.grid(row=0, column=i, sticky="ew",
                      padx=(0, 6) if i < len(self.METODOS) - 1 else 0)
            frame_cards.columnconfigure(i, weight=1)
            self._cards_metrica[chave] = card

        # Card da média
        card_media = CardMetrica(frame_cards,
                                   titulo="Média dos Métodos Selecionados",
                                   valor="—",
                                   unidade="kN",
                                   cor_valor=COR_SUCESSO)
        card_media.grid(row=0, column=len(self.METODOS), sticky="ew", padx=(6, 0))
        frame_cards.columnconfigure(len(self.METODOS), weight=1)
        self._cards_metrica["media"] = card_media

        # ── Seletor + Tabela ──────────────────────────────────
        frame_tabela = ctk.CTkFrame(self, fg_color="transparent")
        frame_tabela.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        frame_tabela.columnconfigure(0, weight=1)
        frame_tabela.rowconfigure(1, weight=1)

        # Barra de seleção de método
        barra = ctk.CTkFrame(frame_tabela, fg_color=COR_CARD,
                              border_color=COR_BORDA, border_width=1,
                              corner_radius=RAIO_BORDA)
        barra.grid(row=0, column=0, sticky="w", pady=(0, 8))

        opcoes = [(c, n) for c, n, *_ in self.METODOS] + [("media", "Média Selecionados")]
        for chave, nome in opcoes:
            btn = ctk.CTkButton(
                barra, text=nome, font=FONTE_LABEL_SM,
                fg_color="transparent", text_color=COR_TEXTO_SECUNDARIO,
                hover_color="#EFF6FF", corner_radius=4, height=28,
                command=lambda c=chave: self._trocar_metodo(c))
            btn.pack(side="left", padx=2, pady=2)
            setattr(self, f"_btn_res_{chave}", btn)

        # Tabela de resultado
        self.card_tab = CardTitulado(frame_tabela,
                                      titulo="—",
                                      subtitulo="Resultados completos por cota de apoio")
        self.card_tab.grid(row=1, column=0, sticky="nsew")
        self.card_tab.rowconfigure(2, weight=1)

        self.tabela = TabelaDataFrame(self.card_tab.corpo)
        self.tabela.pack(fill="both", expand=True)
        self.tabela.canvas.bind("<Configure>", self._on_tabela_configure, add="+")
        self.tabela.frame_corpo.bind("<Configure>", self._on_tabela_configure, add="+")

        self.atualizar()

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

    # ─────────────────────────────────────────────────────────
    def atualizar(self):
        mapa = {
            "aoki":      (state.df_aoki,      "Carga Adm. (kN)"),
            "decourt":   (state.df_decourt,   "Carga Adm. Adotada (kN)"),
            "teixeira":  (state.df_teixeira,  "Carga Adm. (kN)"),
            "monteiro":  (state.df_monteiro,  "Carga Adm. (kN)"),
            "berberian": (state.df_berberian, "Carga Adm. (kN)"),
            "media":     (state.df_media,     "Carga Adm. (kN)"),
        }
        for chave, (df, col) in mapa.items():
            card = self._cards_metrica.get(chave)
            if card is None:
                continue
            if df is not None and col in df.columns:
                val = formatar_valor_tabela(col, df[col].max())
                card.set_valor(f"{val}")
            else:
                card.set_valor("—")

        self._trocar_metodo(self._metodo_sel.get())

    def _trocar_metodo(self, chave):
        self._metodo_sel.set(chave)

        opcoes = [(c, n) for c, n, *_ in self.METODOS] + [("media", "Média")]
        for c, _ in opcoes:
            btn = getattr(self, f"_btn_res_{c}", None)
            if btn:
                btn.configure(
                    fg_color=COR_PRIMARIA if c == chave else "transparent",
                    hover_color=COR_PRIMARIA_HOVER if c == chave else "#EFF6FF",
                    text_color=COR_TEXTO_BRANCO if c == chave else COR_TEXTO_SECUNDARIO)

        mapa_df = {
            "aoki":      (state.df_aoki,      "Carga Adm. (kN)"),
            "decourt":   (state.df_decourt,   "Carga Adm. Adotada (kN)"),
            "teixeira":  (state.df_teixeira,  "Carga Adm. (kN)"),
            "monteiro":  (state.df_monteiro,  "Carga Adm. (kN)"),
            "berberian": (state.df_berberian, "Carga Adm. (kN)"),
            "media":     (state.df_media,     "Carga Adm. (kN)"),
        }
        df, col = mapa_df.get(chave, (None, ""))
        nome = dict(opcoes).get(chave, chave)

        self.tabela.carregar(df, colunas_destaque=[col] if col else [])
        self._on_tabela_configure(None)
