"""
EstacaLab — Tela de Dados do Projeto.
"""

import customtkinter as ctk
from gui.constants import *
from gui.components import (CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador, MensagemStatus, LinhaFormulario)
from gui.state import state

class TelaProjeto(ctk.CTkFrame):
    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self._vars = {}
        self._carregando_ui = False
        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Dados do Projeto",
                     subtitulo="Informações para identificação na memória de cálculo").pack(anchor="w")

        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Conteúdo ─────────────────────────────────────────
        corpo = ctk.CTkScrollableFrame(self, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nsew", padx=24, pady=0)
        corpo.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        card_info = CardTitulado(corpo, titulo="Informações da Obra",
                                 subtitulo="Os campos marcados com * são recomendados para um relatório completo.")
        card_info.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        
        self._construir_formulario(card_info.corpo)

        # ── Barra de ação ────────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))

        self.msg = MensagemStatus(barra)
        self.msg.pack(side="left")

        self.lbl_status = ctk.CTkLabel(barra, text="✓ Dados salvos", text_color=COR_SUCESSO, font=FONTE_LABEL)
        self.lbl_status.pack(side="right", padx=(10, 0))

        BotaoPrimario(barra, texto="💾  Salvar Dados",
                       comando=self._salvar, width=160).pack(side="right")
        BotaoSecundario(barra, texto="↻  Restaurar",
                         comando=self._restaurar, width=120).pack(side="right", padx=(0, 8))

        self._restaurar()

    def _construir_formulario(self, master):
        master.columnconfigure(1, weight=1)

        campos = [
            ("Nome do projeto *", "nome_projeto", state.nome_projeto),
            ("Nome da obra *", "obra_name", state.obra_name),
            ("Local da obra *", "local_obra", state.local_obra),
            ("Acadêmico/Aluno *", "responsavel_tecnico", state.responsavel_tecnico),
            ("Registro Acadêmico *", "registro_profissional", state.registro_profissional),
            ("Data da análise", "data_analise", state.data_analise),
            ("Observações", "observacoes", state.observacoes),
        ]

        for i, (label, chave, _) in enumerate(campos):
            ctk.CTkLabel(master, text=label, font=FONTE_LABEL,
                         text_color=COR_TEXTO_SECUNDARIO).grid(
                row=i, column=0, sticky="w", pady=10, padx=(0, 15))

            self._vars[chave] = ctk.StringVar()
            
            if chave == "observacoes":
                entry = ctk.CTkEntry(master, textvariable=self._vars[chave],
                                     font=FONTE_LABEL, width=400)
            else:
                entry = ctk.CTkEntry(master, textvariable=self._vars[chave],
                                     font=FONTE_LABEL, width=300)
            
            entry.grid(row=i, column=1, sticky="w", pady=10)
            
            self._vars[chave].trace_add("write", self._on_edit)

        # Aviso sobre o autor
        aviso = ctk.CTkFrame(master, fg_color="#EFF6FF",
                             border_color="#BFDBFE", border_width=1,
                             corner_radius=4)
        aviso.grid(row=len(campos), column=0, columnspan=2, sticky="ew", pady=(20, 0))
        ctk.CTkLabel(aviso,
                     text="ℹ  O desenvolvedor do software (Willian Bortolucci) será creditado automaticamente na memória de cálculo.",
                     font=FONTE_CAPTION,
                     text_color=COR_INFO,
                     wraplength=500, justify="left").pack(padx=10, pady=8, anchor="w")


    def _salvar(self):
        nome_projeto = self._vars['nome_projeto'].get().strip() or "Novo Projeto"
        obra_name = self._vars['obra_name'].get().strip()
        local_obra = self._vars['local_obra'].get().strip()
        responsavel_tecnico = self._vars['responsavel_tecnico'].get().strip()
        registro_profissional = self._vars['registro_profissional'].get().strip()
        data_analise = self._vars['data_analise'].get().strip()
        observacoes = self._vars['observacoes'].get().strip()

        mudou = (
            state.nome_projeto != nome_projeto or
            state.obra_name != obra_name or
            state.local_obra != local_obra or
            state.responsavel_tecnico != responsavel_tecnico or
            state.registro_profissional != registro_profissional or
            state.data_analise != data_analise or
            state.observacoes != observacoes
        )

        state.nome_projeto = nome_projeto
        state.obra_name = obra_name
        state.local_obra = local_obra
        state.responsavel_tecnico = responsavel_tecnico
        state.registro_profissional = registro_profissional
        state.data_analise = data_analise
        state.observacoes = observacoes
        
        if mudou:
            state.marcar_projeto_modificado()
            
        from gui.state import save_user_config
        save_user_config(state.responsavel_tecnico, state.registro_profissional)
        
        state.notificar()
        state.marcar_salvo("projeto")
        self._atualizar_header()
        self.msg.ok("Dados do projeto salvos com sucesso.")

    def _on_edit(self, *args):
        if self._carregando_ui:
            return
        state.marcar_pendente("projeto")
        self._atualizar_header()

    def _atualizar_header(self):
        if state.tem_pendencias(["projeto"]):
            self.lbl_status.configure(text="● Alterações não salvas", text_color=COR_ALERTA)
        else:
            self.lbl_status.configure(text="✓ Dados salvos", text_color=COR_SUCESSO)

    def _restaurar(self):
        self._carregando_ui = True
        try:
            self._vars['nome_projeto'].set(state.nome_projeto)
            self._vars['obra_name'].set(state.obra_name)
            self._vars['local_obra'].set(state.local_obra)
            self._vars['responsavel_tecnico'].set(state.responsavel_tecnico)
            self._vars['registro_profissional'].set(state.registro_profissional)
            self._vars['data_analise'].set(state.data_analise)
            self._vars['observacoes'].set(state.observacoes)
        finally:
            self._carregando_ui = False
            
        self._atualizar_header()
        self.msg.limpar()
