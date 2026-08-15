"""
EstacaLab — Componentes reutilizáveis da interface.
Cards, botões, tabelas, labels e outros widgets padronizados.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import pandas as pd

from gui.constants import *
from gui.formatters import formatar_valor_tabela


# ============================================================
# CARD BASE
# ============================================================
class Card(ctk.CTkFrame):
    """Frame com estilo de card (fundo branco, borda sutil)."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            fg_color=COR_CARD,
            border_color=COR_BORDA,
            border_width=1,
            corner_radius=RAIO_BORDA,
            **kwargs
        )


# ============================================================
# CARD COM TÍTULO E CONTEÚDO
# ============================================================
class CardTitulado(Card):
    def __init__(self, master, titulo="", subtitulo="", **kwargs):
        super().__init__(master, **kwargs)
        self.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PADDING_CARD, pady=(PADDING_CARD, 6))

        ctk.CTkLabel(header, text=titulo, font=FONTE_SUBTITULO,
                     text_color=COR_TEXTO_PRIMARIO).pack(anchor="w")
        if subtitulo:
            ctk.CTkLabel(header, text=subtitulo, font=FONTE_LABEL_SM,
                         text_color=COR_TEXTO_SECUNDARIO).pack(anchor="w")

        # Linha divisória
        sep = ctk.CTkFrame(self, height=1, fg_color=COR_BORDA)
        sep.grid(row=1, column=0, sticky="ew", padx=0, pady=0)

        self.corpo = ctk.CTkFrame(self, fg_color="transparent")
        self.corpo.grid(row=2, column=0, sticky="nsew", padx=PADDING_CARD, pady=PADDING_CARD)
        self.rowconfigure(2, weight=1)


# ============================================================
# CARD MÉTRICA (número grande + label)
# ============================================================
class CardMetrica(Card):
    def __init__(self, master, titulo="", valor="—", unidade="", cor_valor=COR_PRIMARIA, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(width=180, height=100)

        ctk.CTkLabel(self, text=titulo, font=FONTE_LABEL_SM,
                     text_color=COR_TEXTO_SECUNDARIO).pack(anchor="w", padx=14, pady=(12, 0))

        frame_val = ctk.CTkFrame(self, fg_color="transparent")
        frame_val.pack(anchor="w", padx=14, pady=(2, 0))

        self.lbl_valor = ctk.CTkLabel(frame_val, text=valor,
                                       font=FONTE_NUMERO_MEDIO, text_color=cor_valor)
        self.lbl_valor.pack(side="left")

        if unidade:
            ctk.CTkLabel(frame_val, text=f" {unidade}", font=FONTE_LABEL_SM,
                         text_color=COR_TEXTO_SECUNDARIO).pack(side="left", anchor="s", pady=(0, 2))

    def set_valor(self, valor):
        self.lbl_valor.configure(text=str(valor))


# ============================================================
# BOTÕES PADRONIZADOS
# ============================================================
class BotaoPrimario(ctk.CTkButton):
    def __init__(self, master, texto="", comando=None, **kwargs):
        super().__init__(
            master,
            text=texto,
            command=comando,
            fg_color=COR_PRIMARIA,
            hover_color=COR_PRIMARIA_HOVER,
            text_color=COR_TEXTO_BRANCO,
            font=FONTE_BOTAO,
            height=BTN_ALTURA,
            corner_radius=RAIO_BORDA,
            **kwargs
        )


class BotaoSecundario(ctk.CTkButton):
    def __init__(self, master, texto="", comando=None, **kwargs):
        super().__init__(
            master,
            text=texto,
            command=comando,
            fg_color="transparent",
            hover_color=COR_BORDA,
            text_color=COR_TEXTO_PRIMARIO,
            border_color=COR_BORDA,
            border_width=1,
            font=FONTE_BOTAO,
            height=BTN_ALTURA,
            corner_radius=RAIO_BORDA,
            **kwargs
        )


class BotaoPerigo(ctk.CTkButton):
    def __init__(self, master, texto="", comando=None, **kwargs):
        super().__init__(
            master,
            text=texto,
            command=comando,
            fg_color="transparent",
            hover_color="#FEE2E2",
            text_color=COR_ERRO,
            border_color="#FCA5A5",
            border_width=1,
            font=FONTE_BOTAO,
            height=BTN_ALTURA,
            corner_radius=RAIO_BORDA,
            **kwargs
        )


# ============================================================
# TÍTULO DE SEÇÃO (PÁGINA)
# ============================================================
class TituloPagina(ctk.CTkFrame):
    def __init__(self, master, titulo="", subtitulo="", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=titulo, font=FONTE_TITULO,
                     text_color=COR_TEXTO_PRIMARIO).pack(anchor="w")
        if subtitulo:
            ctk.CTkLabel(self, text=subtitulo, font=FONTE_LABEL,
                         text_color=COR_TEXTO_SECUNDARIO).pack(anchor="w", pady=(2, 0))


# ============================================================
# TABELA (usando tk.Frame + tk.Text para renderização eficiente)
# ============================================================
class TabelaDataFrame(ctk.CTkFrame):
    """
    Exibe um pd.DataFrame como tabela com cabeçalho fixo e linhas alternadas.
    Adequado para DataFrames de resultados (somente leitura).
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COR_CARD, border_color=COR_BORDA,
                         border_width=1, corner_radius=RAIO_BORDA, **kwargs)
        self._construir()

    def _construir(self):
        # Canvas + Scrollbar para o corpo
        self.canvas = tk.Canvas(self, bg=COR_CARD, highlightthickness=0)
        self.vsb = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)
        self.hsb = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.hsb.pack(side="bottom", fill="x")
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.frame_corpo = tk.Frame(self.canvas, bg=COR_CARD)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.frame_corpo, anchor="nw")

        self.frame_corpo.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Binding do MouseWheel para diferentes plataformas
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._ajustar_largura()

    def _on_canvas_configure(self, event=None):
        self._ajustar_largura(event.width)
        
    def _ajustar_largura(self, canvas_width=None):
        if canvas_width is None:
            canvas_width = self.canvas.winfo_width()
        
        req_width = self.frame_corpo.winfo_reqwidth()
        if req_width < canvas_width:
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        else:
            # Ao definir uma largura maior, o frame assume o tamanho necessário
            self.canvas.itemconfig(self.canvas_window, width=req_width)

    def _on_mousewheel(self, event):
        # Evita scroll se o mouse não estiver sobre a tabela
        try:
            widget_sob_mouse = self.winfo_containing(event.x_root, event.y_root)
            if not str(widget_sob_mouse).startswith(str(self)):
                return
        except Exception:
            pass
            
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def carregar(self, df, colunas_destaque=None, max_linhas=500):
        """Carrega um pd.DataFrame na tabela."""
        import pandas as pd

        # Limpar conteúdo anterior
        for w in self.frame_corpo.winfo_children():
            w.destroy()

        if df is None or df.empty:
            ctk.CTkLabel(self.frame_corpo, text="Sem dados para exibir.",
                         font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO).grid(
                row=0, column=0, padx=16, pady=16)
            return

        colunas = list(df.columns)
        colunas_destaque = colunas_destaque or []

        # ── Cabeçalho ───────────────────────────────────────
        for col_idx, col in enumerate(colunas):
            destaque = col in colunas_destaque
            bg = "#DBEAFE" if destaque else "#EFF6FF"
            fg = COR_PRIMARIA if destaque else COR_TEXTO_PRIMARIO
            lbl = tk.Label(
                self.frame_corpo, text=col,
                font=(FONTE_MONO, 9, "bold"),
                bg=bg, fg=fg,
                padx=10, pady=6,
                relief="flat", anchor="center",
                borderwidth=0
            )
            lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
            self.frame_corpo.columnconfigure(col_idx, weight=0) # Não expande forçadamente

        # ── Linhas ──────────────────────────────────────────
        linhas = df.head(max_linhas)
        for row_idx, (_, row) in enumerate(linhas.iterrows()):
            bg = "#F8FAFC" if row_idx % 2 == 0 else COR_CARD
            for col_idx, col in enumerate(colunas):
                texto = formatar_valor_tabela(col, row[col])
                destaque = col in colunas_destaque
                fg = COR_PRIMARIA if destaque else COR_TEXTO_PRIMARIO
                lbl = tk.Label(
                    self.frame_corpo, text=texto,
                    font=(FONTE_MONO, 9),
                    bg=bg, fg=fg,
                    padx=10, pady=4,
                    relief="flat", anchor="center"
                )
                lbl.grid(row=row_idx + 1, column=col_idx, sticky="nsew", padx=1, pady=0)


# ============================================================
# BADGE DE STATUS
# ============================================================
class Badge(ctk.CTkLabel):
    """Pequena etiqueta colorida de status."""

    ESTILOS = {
        "ok":       (COR_SUCESSO,  "#DCFCE7"),
        "alerta":   (COR_ALERTA,   "#FEF3C7"),
        "erro":     (COR_ERRO,     "#FEE2E2"),
        "info":     (COR_INFO,     "#E0F2FE"),
        "neutro":   (COR_SECUNDARIA, "#F1F5F9"),
    }

    def __init__(self, master, texto="", estilo="neutro", **kwargs):
        fg_txt, fg_bg = self.ESTILOS.get(estilo, self.ESTILOS["neutro"])
        super().__init__(
            master,
            text=texto,
            font=FONTE_CAPTION,
            text_color=fg_txt,
            fg_color=fg_bg,
            corner_radius=4,
            **kwargs
        )

    def set_estilo(self, texto, estilo="neutro"):
        fg_txt, fg_bg = self.ESTILOS.get(estilo, self.ESTILOS["neutro"])
        self.configure(text=texto, text_color=fg_txt, fg_color=fg_bg)


# ============================================================
# SEPARADOR HORIZONTAL
# ============================================================
class Separador(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=1, fg_color=COR_BORDA, **kwargs)


# ============================================================
# LINHA DE FORMULÁRIO (label + widget)
# ============================================================
class LinhaFormulario(ctk.CTkFrame):
    def __init__(self, master, label="", widget_cls=ctk.CTkEntry,
                 largura_label=160, **kwargs_widget):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(1, weight=1)

        ctk.CTkLabel(self, text=label, font=FONTE_LABEL,
                     text_color=COR_TEXTO_PRIMARIO,
                     width=largura_label, anchor="w").grid(
            row=0, column=0, padx=(0, 10), sticky="w")

        self.widget = widget_cls(self, **kwargs_widget)
        self.widget.grid(row=0, column=1, sticky="ew")


# ============================================================
# MENSAGEM DE STATUS
# ============================================================
class MensagemStatus(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._lbl = ctk.CTkLabel(self, text="", font=FONTE_LABEL_SM,
                                  text_color=COR_TEXTO_SECUNDARIO)
        self._lbl.pack(anchor="w")

    def ok(self, texto):
        self._lbl.configure(text=f"✓ {texto}", text_color=COR_SUCESSO)

    def erro(self, texto):
        self._lbl.configure(text=f"✗ {texto}", text_color=COR_ERRO)

    def alerta(self, texto):
        self._lbl.configure(text=f"⚠ {texto}", text_color=COR_ALERTA)

    def info(self, texto):
        self._lbl.configure(text=f"ℹ {texto}", text_color=COR_INFO)

    def limpar(self):
        self._lbl.configure(text="")
