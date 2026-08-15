"""
EstacaLab — Tela de Comparação entre Métodos.
Tabela comparativa e diferença percentual entre os cinco métodos + média.
"""

import customtkinter as ctk
import pandas as pd
from gui.constants import *
from gui.components import (Card, CardTitulado, TituloPagina, Separador, TabelaDataFrame)
from gui.state import state


class TelaComparacao(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._construir()
        state.registrar_callback(self.atualizar)

    def destroy(self):
        state.desregistrar_callback(self.atualizar)
        super().destroy()

    def _construir(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Comparação entre Métodos",
                     subtitulo="Carga admissível por cota — diferença percentual em relação à Média dos Métodos Selecionados").pack(anchor="w")
        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # Tabela comparativa
        card = CardTitulado(self,
                             titulo="Tabela Comparativa — Carga Admissível (kN)",
                             subtitulo="Δ% = diferença percentual em relação à Média dos Métodos Selecionados")
        card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        card.rowconfigure(2, weight=1)
        self.rowconfigure(2, weight=1)

        self.tabela = TabelaDataFrame(card.corpo)
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

    def atualizar(self):
        df = self._montar_comparativo()
        if df is not None:
            colunas_dest = [c for c in df.columns if "Δ%" in c]
            colunas_dest += ["Média (kN)"]
            self.tabela.carregar(df, colunas_destaque=colunas_dest)
        else:
            self.tabela.carregar(None)
        self._on_tabela_configure(None)

    def _montar_comparativo(self):
        """
        Monta DataFrame comparativo com as cargas admissíveis de cada método por cota.
        Calcula a diferença percentual em relação à média dos métodos disponíveis.
        """
        mapa = {
            "Aoki-Velloso":     (state.df_aoki,      "Carga Adm. (kN)"),
            "Décourt-Quaresma": (state.df_decourt,   "Carga Adm. Adotada (kN)"),
            "Teixeira":         (state.df_teixeira,  "Carga Adm. (kN)"),
            "Monteiro":         (state.df_monteiro,  "Carga Adm. (kN)"),
            "Berberian":        (state.df_berberian, "Carga Adm. (kN)"),
        }

        # Verifica qual DataFrame usar como referência de cotas
        df_ref = None
        for _, (df, _) in mapa.items():
            if df is not None:
                df_ref = df
                break

        if df_ref is None:
            return None

        cotas = df_ref["Cota (m)"].tolist()
        dados = {"Cota (m)": cotas}

        # Coluna de NSPT (base: Aoki se disponível)
        if state.df_aoki is not None and "Nspt" in state.df_aoki.columns:
            dados["NSPT"] = state.df_aoki["Nspt"].tolist()

        # Preenche as colunas de carga por método
        for nome, (df, col) in mapa.items():
            if df is not None and col in df.columns:
                dados[nome] = df[col].tolist()

        df_comp = pd.DataFrame(dados)

        # Usa a média oficial calculada centralmente
        colunas_metodos = [n for n in mapa.keys() if n in df_comp.columns]

        if state.df_media is not None and "Carga Adm. (kN)" in state.df_media.columns:
            df_comp["Média (kN)"] = state.df_media["Carga Adm. (kN)"].tolist()
        else:
            # Sem média para calcular a diferença
            return df_comp

        # Calcula Δ% para cada método em relação à média
        for nome in colunas_metodos:
            # Apenas mostra delta se o método fez parte da média
            chave_interna = ""
            for k, (nome_mapa, _) in zip(["aoki", "decourt", "teixeira", "monteiro", "berberian"], mapa.items()):
                if nome_mapa == nome:
                    chave_interna = k
                    break

            if chave_interna not in state.metodos_media:
                continue

            delta_col = f"Δ% {nome[:4]}"
            df_comp[delta_col] = df_comp.apply(
                lambda row, n=nome: (
                    round(((row[n] - row["Média (kN)"]) / row["Média (kN)"]) * 100 + 1e-9, 1)
                    if row["Média (kN)"] > 0 and row[n] > 0 else 0
                ),
                axis=1
            )

        return df_comp
