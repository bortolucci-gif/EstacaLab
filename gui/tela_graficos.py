"""
EstacaLab — Tela de Gráficos.
Integração dos gráficos matplotlib via FigureCanvasTkAgg.
"""

import tkinter as tk
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from gui.constants import *
from gui.components import (Card, CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador)
from gui.state import state
from PlotGraficos import plotar_comparativo_metodos


class TelaGraficos(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._grafico_ativo = ctk.StringVar(value="comparativo")
        self._canvas_mpl = None
        self._toolbar    = None
        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Gráficos",
                     subtitulo="Visualização gráfica dos resultados").pack(anchor="w")
        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Seletor de gráfico ────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color=COR_CARD,
                              border_color=COR_BORDA, border_width=1,
                              corner_radius=RAIO_BORDA)
        barra.grid(row=2, column=0, sticky="w", padx=24, pady=(0, 12))

        graficos = [
            ("comparativo", "Comparativo de Métodos"),
            ("profundidade", "Carga Adm. × Profundidade"),
            ("recalque",    "Recalque por Pilar"),
        ]
        for chave, nome in graficos:
            btn = ctk.CTkButton(
                barra, text=nome,
                font=FONTE_LABEL_SM,
                fg_color="transparent",
                text_color=COR_TEXTO_SECUNDARIO,
                hover_color="#EFF6FF",
                corner_radius=4, height=28,
                command=lambda c=chave: self._plotar(c)
            )
            btn.pack(side="left", padx=2, pady=2)
            setattr(self, f"_btn_graf_{chave}", btn)

        # ── Área do gráfico ───────────────────────────────────
        self.card_graf = CardTitulado(self,
                                       titulo="—",
                                       subtitulo="Use a barra de ferramentas para zoom e exportação")
        self.card_graf.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        self.card_graf.rowconfigure(2, weight=1)

        self.frame_graf = ctk.CTkFrame(self.card_graf.corpo, fg_color=COR_CARD)
        self.frame_graf.pack(fill="both", expand=True)

        # Mensagem inicial
        self.lbl_vazio = ctk.CTkLabel(
            self.frame_graf,
            text="Selecione um gráfico acima.\n\nNecessário calcular a capacidade de carga primeiro.",
            font=FONTE_LABEL, text_color=COR_TEXTO_SECUNDARIO)
        self.lbl_vazio.pack(expand=True)

    # ─────────────────────────────────────────────────────────
    def _plotar(self, chave):
        self._grafico_ativo.set(chave)

        # Atualiza visual dos botões
        graficos = ["comparativo", "profundidade", "recalque"]
        for c in graficos:
            btn = getattr(self, f"_btn_graf_{c}", None)
            if btn:
                btn.configure(
                    fg_color=COR_PRIMARIA if c == chave else "transparent",
                    text_color=COR_TEXTO_BRANCO if c == chave else COR_TEXTO_SECUNDARIO)

        # Limpa gráfico anterior
        self._limpar_canvas()

        if chave == "comparativo":
            self._plotar_comparativo()
        elif chave == "profundidade":
            self._plotar_profundidade()
        elif chave == "recalque":
            self._plotar_recalque()

    def _limpar_canvas(self):
        if self._canvas_mpl is not None:
            self._canvas_mpl.get_tk_widget().destroy()
            self._canvas_mpl = None
        if self._toolbar is not None:
            self._toolbar.destroy()
            self._toolbar = None
        if self.lbl_vazio.winfo_exists():
            self.lbl_vazio.pack_forget()

    def _embed_fig(self, fig, titulo="Gráfico"):
        """Embute uma Figure matplotlib no frame da GUI."""
        # Estilo consistente com a paleta da aplicação
        fig.patch.set_facecolor(COR_CARD)
        for ax in fig.get_axes():
            ax.set_facecolor("#FAFAFA")
            ax.grid(True, linestyle="--", alpha=0.5, color="#E2E8F0")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

        self._canvas_mpl = FigureCanvasTkAgg(fig, master=self.frame_graf)
        self._canvas_mpl.draw()
        self._canvas_mpl.get_tk_widget().pack(fill="both", expand=True, side="top")

        # Barra de ferramentas matplotlib (zoom, salvar, etc.)
        self._toolbar = NavigationToolbar2Tk(self._canvas_mpl, self.frame_graf)
        self._toolbar.update()

    # ─────────────────────────────────────────────────────────
    # Gráfico 1 — Comparativo de métodos (usa PlotGraficos.py intacto)
    # ─────────────────────────────────────────────────────────
    def _plotar_comparativo(self):
        dfs = {
            "aoki":      state.df_aoki,
            "decourt":   state.df_decourt,
            "teixeira":  state.df_teixeira,
            "monteiro":  state.df_monteiro,
            "berberian": state.df_berberian,
        }
        disponiveis = {k: v for k, v in dfs.items() if v is not None}

        if not disponiveis:
            self._mostrar_aviso("Nenhum método calculado ainda.")
            return

        # Se todos os 5 estão disponíveis, usa PlotGraficos.py original
        if len(disponiveis) == 5:
            fig = plotar_comparativo_metodos(
                state.df_aoki, state.df_decourt, state.df_teixeira,
                state.df_monteiro, state.df_berberian,
                state.df_media, state.cota_inicio, return_fig=True)
        else:
            # Para conjuntos parciais, usa o gráfico de profundidade
            self._plotar_profundidade()
            return

        self._embed_fig(fig, "Comparativo de Métodos")

    # ─────────────────────────────────────────────────────────
    # Gráfico 2 — Carga Adm. × Profundidade (métodos disponíveis)
    # ─────────────────────────────────────────────────────────
    def _plotar_profundidade(self):
        mapa = {
            "Aoki-Velloso":     (state.df_aoki,      "Carga Adm. (kN)"),
            "Décourt-Quaresma": (state.df_decourt,   "Carga Adm. Adotada (kN)"),
            "Teixeira":         (state.df_teixeira,  "Carga Adm. (kN)"),
            "Monteiro":         (state.df_monteiro,  "Carga Adm. (kN)"),
            "Berberian":        (state.df_berberian, "Carga Adm. (kN)"),
        }

        disponiveis = [(n, df, col) for n, (df, col) in mapa.items() if df is not None]
        if not disponiveis:
            self._mostrar_aviso("Nenhum método calculado ainda.")
            return

        fig, ax = plt.subplots(figsize=(9, 7))
        cores = ["#2563EB", "#16A34A", "#D97706", "#7C3AED", "#DC2626"]

        cotas = disponiveis[0][1]["Cota (m)"].tolist()

        for i, (nome, df, col) in enumerate(disponiveis):
            vals = df[col].tolist()
            ax.plot(vals, cotas,
                    label=nome,
                    marker="o", markersize=3,
                    linewidth=1.8,
                    color=cores[i % len(cores)])

        # Média dos Métodos Selecionados se disponível
        if state.df_media is not None:
            ax.plot(state.df_media["Carga Adm. (kN)"].tolist(), cotas,
                    label="Média dos Métodos Selecionados",
                    color="black", linewidth=2.5,
                    linestyle="--", marker="*", markersize=7)

        ax.axhline(y=0, color="#888", linewidth=1, linestyle=":", label="N.T.")
        ax.axhline(y=state.cota_inicio, color="#8B4513", linewidth=1.5,
                   linestyle="--", label=f"Cota de arrasamento ({state.cota_inicio}m)")

        ax.set_xlabel("Carga Admissível (kN)", fontsize=11)
        ax.set_ylabel("Cota (m)", fontsize=11)
        ax.set_title("Carga Admissível × Profundidade", fontsize=13, fontweight="bold")
        ax.legend(fontsize=9)
        fig.tight_layout()

        self._embed_fig(fig, "Carga Adm. × Profundidade")

    # ─────────────────────────────────────────────────────────
    # Gráfico 3 — Recalque por pilar
    # ─────────────────────────────────────────────────────────
    def _plotar_recalque(self):
        if state.df_recalque is None or state.df_recalque.empty:
            self._mostrar_aviso("Calcule o recalque na tela de Recalque primeiro.")
            return

        df = state.df_recalque
        pilares = df["Pilar"].astype(str).tolist()
        rho_e   = df["rho_e (mm)"].tolist()
        rho_s   = df["rho_s (mm)"].tolist()
        total   = df["Recalque Total (mm)"].tolist()

        x = np.arange(len(pilares))
        larg = 0.28

        fig, ax = plt.subplots(figsize=(max(8, len(pilares) * 0.6), 6))

        ax.bar(x - larg, rho_e, larg, label="Encurtamento Elástico (ρ_e)",
               color="#2563EB", alpha=0.85)
        ax.bar(x,        rho_s, larg, label="Recalque Solo (ρ_s)",
               color="#D97706", alpha=0.85)
        ax.bar(x + larg, total, larg, label="Recalque Total",
               color="#16A34A", alpha=0.85)

        ax.set_xticks(x)
        ax.set_xticklabels(pilares, rotation=45 if len(pilares) > 10 else 0,
                            ha="right", fontsize=9)
        ax.set_ylabel("Recalque (mm)", fontsize=11)
        ax.set_xlabel("Pilar", fontsize=11)
        ax.set_title("Estimativa de Recalque por Pilar", fontsize=13, fontweight="bold")
        ax.legend(fontsize=9)
        fig.tight_layout()

        self._embed_fig(fig, "Recalque por Pilar")

    def _mostrar_aviso(self, texto):
        self.lbl_vazio.configure(text=texto)
        self.lbl_vazio.pack(expand=True)
