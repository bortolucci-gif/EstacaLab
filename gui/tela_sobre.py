"""
EstacaLab — Tela Sobre o Sistema.
"""

import customtkinter as ctk
from gui.constants import *
from gui.components import TituloPagina, Separador, CardTitulado

class TelaSobre(ctk.CTkFrame):
    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.columnconfigure(0, weight=1)
        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Sobre o Sistema",
                     subtitulo="Informações sobre o software").pack(anchor="w")

        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Conteúdo ─────────────────────────────────────────
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nsew", padx=24, pady=0)
        corpo.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        card_sobre = CardTitulado(corpo, titulo="ESTACALAB",
                                  subtitulo="Sistema Computacional para Análise de Fundações Profundas")
        card_sobre.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        
        info_frame = ctk.CTkFrame(card_sobre.corpo, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(info_frame, text="Versão 1.0 – 2026", font=FONTE_LABEL_BOLD, text_color=COR_TEXTO_PRIMARIO).pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(info_frame, text="Desenvolvido por:", font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO).pack(anchor="w")
        ctk.CTkLabel(info_frame, text="Willian Bortolucci", font=FONTE_LABEL_BOLD, text_color=COR_TEXTO_PRIMARIO).pack(anchor="w", pady=(0, 15))

        ctk.CTkLabel(info_frame, text="Finalidade:", font=FONTE_LABEL_SM, text_color=COR_TEXTO_SECUNDARIO).pack(anchor="w")
        ctk.CTkLabel(info_frame, 
                     text="O EstacaLab é uma ferramenta computacional desenvolvida originalmente no âmbito de um Trabalho de Conclusão de Curso (TCC) em Engenharia Civil, com finalidade acadêmica e educacional. O software é disponibilizado para utilização não comercial sob a PolyForm Noncommercial License 1.0.0. A utilização do EstacaLab não substitui investigação geotécnica, verificações normativas, provas de carga, projeto executivo ou o julgamento e a responsabilidade técnica do profissional habilitado. A utilização comercial do software não é autorizada nos termos da licença adotada.", 
                     font=FONTE_LABEL, 
                     text_color=COR_TEXTO_PRIMARIO, 
                     wraplength=800, 
                     justify="left").pack(anchor="w", pady=(0, 10))
