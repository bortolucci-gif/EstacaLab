"""
EstacaLab — Tela de Capacidade de Carga.
Seleção de métodos, execução dos cálculos e exibição dos DataFrames resultantes.
"""

import threading
import queue
from copy import deepcopy
import customtkinter as ctk
from gui.constants import *
from gui.components import (Card, CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador, MensagemStatus, TabelaDataFrame)
from gui.state import state
from GeometriaEstacas import calcular_geometria

from FuncCapacidaCargaAoki import resultAoki
from FuncCapacidadeCargaDecourt import resultDecourt
from FuncCapacidadeCargaTeixeira import resultTeixeira
from FuncCapacidadeCargaMonteiro import resultMonteiro
from FuncCapacidadeCargaBerberian import resultBerberian
from DimensionamentoPilares import gerar_df_media_metodos


class TelaCapacidade(ctk.CTkFrame):

    METODOS_UI = [
        ("aoki",      "Aoki-Velloso (1975)"),
        ("decourt",   "Décourt-Quaresma (1978)"),
        ("teixeira",  "Teixeira (1996)"),
        ("monteiro",  "Monteiro (1997)"),
        ("berberian", "Berberian (2015)"),
    ]

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._chk_vars = {}
        self._metodo_exibido = ctk.StringVar(value="aoki")

        self._calculando = False
        self._run_id = 0
        self.queue = queue.Queue()
        self._after_queue_id = None
        self._disposed = False

        self._construir()

    def destroy(self):
        self._disposed = True
        self._run_id += 1

        if self._after_queue_id is not None:
            try:
                self.after_cancel(self._after_queue_id)
            except Exception:
                pass

            self._after_queue_id = None

        super().destroy()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))

        TituloPagina(
            header,
            titulo="Capacidade de Carga",
            subtitulo="Selecione os métodos e execute o cálculo"
        ).pack(anchor="w")

        Separador(self).grid(
            row=1, column=0, sticky="ew", padx=0, pady=12
        )

        # ── Painel de seleção + ação ─────────────────────────
        painel_top = ctk.CTkFrame(self, fg_color="transparent")
        painel_top.grid(
            row=2, column=0, sticky="ew", padx=24, pady=(0, 12)
        )
        painel_top.columnconfigure(0, weight=0)
        painel_top.columnconfigure(1, weight=0)
        painel_top.columnconfigure(2, weight=1)

        card_sel = CardTitulado(
            painel_top,
            titulo="Métodos Semiempíricos",
            subtitulo="Selecione um ou mais métodos para calcular"
        )
        card_sel.grid(row=0, column=0, sticky="w", padx=(0, 8))

        frame_checks = ctk.CTkFrame(
            card_sel.corpo,
            fg_color="transparent"
        )
        frame_checks.pack(anchor="w")

        for chave, nome in self.METODOS_UI:
            var = ctk.BooleanVar(
                value=(chave in state.metodos_selecionados)
            )
            self._chk_vars[chave] = var

            chk = ctk.CTkCheckBox(
                frame_checks,
                text=nome,
                variable=var,
                font=FONTE_LABEL,
                text_color=COR_TEXTO_PRIMARIO,
                command=self._sincronizar_selecao
            )
            chk.pack(anchor="w", pady=3)

        # Ação
        frame_acao = ctk.CTkFrame(
            painel_top,
            fg_color="transparent"
        )
        frame_acao.grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        self.btn_calcular = BotaoPrimario(
            frame_acao,
            texto="▶  Calcular Selecionados",
            comando=self._executar,
            width=180
        )
        self.btn_calcular.pack(pady=(0, 8))

        BotaoSecundario(
            frame_acao,
            texto="↺  Limpar Resultados",
            comando=self._limpar_resultados,
            width=180
        ).pack()

        self.barra_prog = ctk.CTkProgressBar(
            frame_acao,
            width=180
        )
        self.barra_prog.pack(pady=(8, 0))
        self.barra_prog.set(0)
        self.barra_prog.pack_forget()

        self.msg = MensagemStatus(frame_acao)
        self.msg.pack(pady=(6, 0))

        # ── Abas de resultado ────────────────────────────────
        frame_abas = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        frame_abas.grid(
            row=3, column=0, sticky="nsew",
            padx=24, pady=(0, 16)
        )
        frame_abas.columnconfigure(0, weight=1)
        frame_abas.rowconfigure(1, weight=1)

        barra_abas = ctk.CTkFrame(
            frame_abas,
            fg_color=COR_CARD,
            border_color=COR_BORDA,
            border_width=1,
            corner_radius=RAIO_BORDA
        )
        barra_abas.grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        abas = [
            ("aoki", "Aoki-Velloso"),
            ("decourt", "Décourt-Quaresma"),
            ("teixeira", "Teixeira"),
            ("monteiro", "Monteiro"),
            ("berberian", "Berberian")
        ]

        for chave, nome in abas:
            btn = ctk.CTkButton(
                barra_abas,
                text=nome,
                font=FONTE_LABEL_SM,
                fg_color="transparent",
                text_color=COR_TEXTO_SECUNDARIO,
                hover_color="#EFF6FF",
                corner_radius=4,
                height=28,
                command=lambda c=chave: self._trocar_aba(c)
            )
            btn.pack(side="left", padx=2, pady=2)
            setattr(self, f"_btn_aba_{chave}", btn)

        self.card_tabela = CardTitulado(
            frame_abas,
            titulo="—",
            subtitulo="Resultados completos por cota"
        )
        self.card_tabela.grid(
            row=1, column=0, sticky="nsew"
        )
        self.card_tabela.rowconfigure(2, weight=1)

        self.tabela = TabelaDataFrame(
            self.card_tabela.corpo
        )
        self.tabela.pack(fill="both", expand=True)
        
        self.tabela.canvas.bind("<Configure>", self._on_tabela_configure, add="+")
        self.tabela.frame_corpo.bind("<Configure>", self._on_tabela_configure, add="+")

        self._atualizar_exibicao()

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
    # Sincronização dos métodos selecionados
    # ─────────────────────────────────────────────────────────
    def _sincronizar_selecao(self):
        nova_selecao = [
            c for c, v in self._chk_vars.items()
            if v.get()
        ]

        if nova_selecao != state.metodos_selecionados:
            state.metodos_selecionados = nova_selecao
            state.marcar_projeto_modificado()

            state.df_media = None
            state.metodos_media = []
            state.df_dimensionamento.pop("media", None)

            state.notificar()

    # ─────────────────────────────────────────────────────────
    # Snapshot
    # ─────────────────────────────────────────────────────────
    def _capturar_snapshot_calculo(self):
        return {
            "tipo_estaca": state.tipo_estaca,
            "forma_estaca": state.forma_estaca,
            "dimensoes_estaca": deepcopy(
                state.dimensoes_estaca
            ),
            "criterio_ponta_metalica":
                state.criterio_ponta_metalica,
            "cota_inicio": state.cota_inicio,
            "linha_agua": state.linha_agua,
            "solo_sfl": state.solo_sfl,
            "camadas": deepcopy(state.camadas),
            "metodos_selecionados":
                list(state.metodos_selecionados),
            "lista_solo": state.get_lista_tipo_solo(),
            "lista_nspt": state.get_lista_nspt()
        }

    # ─────────────────────────────────────────────────────────
    # Execução dos cálculos
    # ─────────────────────────────────────────────────────────
    def _executar(self):
        if self._calculando:
            return

        if not state.fundacao_preenchida:
            self.msg.erro(
                "Preencha e salve os Dados da Estaca antes de calcular a capacidade de carga."
            )
            return

        if not state.camadas:
            self.msg.erro(
                "Cadastre as camadas na tela de Sondagem SPT."
            )
            return

        try:
            calcular_geometria(
                state.tipo_estaca,
                state.forma_estaca,
                state.dimensoes_estaca,
                state.criterio_ponta_metalica
            )
        except Exception as e:
            self.msg.erro(
                f"Geometria da estaca inválida. "
                f"Verifique a tela de Fundação.\n{e}"
            )
            return

        if state.cota_inicio is None:
            self.msg.erro(
                "Cota de arrasamento não definida. "
                "Verifique a tela de Fundação."
            )
            return

        from gui.validation import (
            validar_cota_vs_sondagem,
            ValidationError
        )

        try:
            validar_cota_vs_sondagem(
                state.cota_inicio,
                state.camadas
            )
        except ValidationError as e:
            self.msg.erro(str(e))
            return

        selecionados = [
            c for c, v in self._chk_vars.items()
            if v.get()
        ]

        if not selecionados:
            self.msg.alerta(
                "Selecione ao menos um método."
            )
            return

        if state.tem_pendencias(["fundacao", "sondagem"]):
            import tkinter.messagebox as messagebox

            messagebox.showwarning(
                "Alterações não salvas",
                "Existem alterações não salvas em:\n"
                "- Dados da Fundação ou\n"
                "- Sondagem SPT\n\n"
                "Salve essas alterações antes de calcular "
                "a capacidade de carga."
            )
            return

        self._calculando = True
        self.btn_calcular.configure(state="disabled")
        self._run_id += 1

        state.metodos_selecionados = selecionados

        self.msg.info("Calculando...")
        self.barra_prog.pack(pady=(8, 0))
        self.barra_prog.start()

        state.df_aoki = state.df_decourt = None
        state.df_teixeira = state.df_monteiro = None
        state.df_berberian = state.df_media = None
        state.metodos_media = []
        state.df_dimensionamento = {}
        state.df_recalque = None

        state.notificar()
        self._atualizar_exibicao()

        snapshot = self._capturar_snapshot_calculo()

        threading.Thread(
            target=self._worker_run,
            args=(self._run_id, snapshot),
            daemon=True
        ).start()

        self._agendar_processamento_queue()

    def _worker_run(self, run_id, snapshot):
        try:
            selecionados = snapshot[
                "metodos_selecionados"
            ]
            total = len(selecionados)
            resultados_locais = {}

            lista_solo = snapshot["lista_solo"]
            lista_nspt = snapshot["lista_nspt"]
            tipo_estaca = snapshot["tipo_estaca"]
            forma_estaca = snapshot["forma_estaca"]
            dimensoes = snapshot["dimensoes_estaca"]
            criterio_ponta = snapshot[
                "criterio_ponta_metalica"
            ]
            cota_inicio = snapshot["cota_inicio"]
            solo_sfl = snapshot["solo_sfl"]

            for idx, chave in enumerate(selecionados):

                if chave == "aoki":
                    resultados_locais["aoki"] = resultAoki(
                        lista_solo,
                        lista_nspt,
                        tipo_estaca,
                        dimensoes,
                        cota_inicio=cota_inicio,
                        forma_estaca=forma_estaca,
                        criterio_ponta_metalica=criterio_ponta
                    )

                elif chave == "decourt":
                    resultados_locais["decourt"] = resultDecourt(
                        lista_solo,
                        lista_nspt,
                        tipo_estaca,
                        dimensoes,
                        cota_inicio=cota_inicio,
                        forma_estaca=forma_estaca,
                        criterio_ponta_metalica=criterio_ponta
                    )

                elif chave == "teixeira":
                    resultados_locais["teixeira"] = resultTeixeira(
                        lista_solo,
                        lista_nspt,
                        tipo_estaca,
                        dimensoes,
                        forma_estaca=forma_estaca,
                        cota_inicio=cota_inicio,
                        solo_sfl=solo_sfl,
                        criterio_ponta_metalica=criterio_ponta
                    )

                elif chave == "monteiro":
                    resultados_locais["monteiro"] = resultMonteiro(
                        lista_solo,
                        lista_nspt,
                        tipo_estaca,
                        dimensoes,
                        cota_inicio=cota_inicio,
                        forma_estaca=forma_estaca,
                        criterio_ponta_metalica=criterio_ponta
                    )

                elif chave == "berberian":
                    resultados_locais["berberian"] = resultBerberian(
                        lista_solo,
                        lista_nspt,
                        tipo_estaca,
                        dimensoes,
                        cota_inicio=cota_inicio,
                        forma_estaca=forma_estaca,
                        criterio_ponta_metalica=criterio_ponta
                    )

                self.queue.put(
                    (
                        "progress",
                        run_id,
                        (idx + 1) / total
                    )
                )

            media_local = None

            if (
                len(resultados_locais)
                == len(selecionados)
                and len(selecionados) >= 2
            ):
                media_local = gerar_df_media_metodos(
                    resultados_locais
                )

            self.queue.put(
                (
                    "success",
                    run_id,
                    snapshot,
                    resultados_locais,
                    media_local
                )
            )

        except Exception as e:
            self.queue.put(
                ("error", run_id, str(e))
            )

    def _agendar_processamento_queue(self):
        if (
            self._after_queue_id is None
            and not self._disposed
        ):
            self._after_queue_id = self.after(
                100,
                self._processar_queue
            )

    def _processar_queue(self):
        self._after_queue_id = None

        if self._disposed:
            return

        while not self.queue.empty():
            try:
                evento = self.queue.get_nowait()
            except queue.Empty:
                break

            tipo = evento[0]
            event_run_id = evento[1]

            if event_run_id != self._run_id:
                continue

            if tipo == "progress":
                percent = evento[2]
                self.barra_prog.set(percent)

            elif tipo == "success":
                snapshot_antigo = evento[2]
                resultados_locais = evento[3]
                media_local = evento[4]

                snapshot_atual = (
                    self._capturar_snapshot_calculo()
                )

                if snapshot_antigo != snapshot_atual:
                    self._finalizar_execucao(
                        self.msg.erro,
                        "Os dados do projeto foram alterados "
                        "durante o cálculo.\n"
                        "Os resultados desta execução foram "
                        "descartados.\n"
                        "Execute o cálculo novamente."
                    )

                else:
                    state.df_aoki = resultados_locais.get(
                        "aoki"
                    )
                    state.df_decourt = resultados_locais.get(
                        "decourt"
                    )
                    state.df_teixeira = resultados_locais.get(
                        "teixeira"
                    )
                    state.df_monteiro = resultados_locais.get(
                        "monteiro"
                    )
                    state.df_berberian = resultados_locais.get(
                        "berberian"
                    )

                    if media_local is not None:
                        state.df_media = media_local
                        state.metodos_media = snapshot_atual[
                            "metodos_selecionados"
                        ]
                    else:
                        state.df_media = None
                        state.metodos_media = []

                    state.notificar()
                    self._atualizar_exibicao()

                    self._finalizar_execucao(
                        self.msg.ok,
                        "Cálculo concluído com sucesso."
                    )

            elif tipo == "error":
                msg_erro = evento[2]

                self._finalizar_execucao(
                    self.msg.erro,
                    f"Erro: {msg_erro}"
                )

        self._agendar_processamento_queue()

    def _finalizar_execucao(
        self,
        msg_func=None,
        msg_text=None
    ):
        self._calculando = False

        if not self._disposed:
            self.btn_calcular.configure(
                state="normal"
            )

            self.barra_prog.stop()
            self.barra_prog.pack_forget()

            if msg_func and msg_text:
                msg_func(msg_text)

    def _limpar_resultados(self):
        state.df_aoki = state.df_decourt = None
        state.df_teixeira = state.df_monteiro = None
        state.df_berberian = state.df_media = None

        state.metodos_media = []
        state.df_dimensionamento = {}
        state.df_recalque = None

        state.notificar()

        self.tabela.carregar(None)
        self.msg.info("Resultados limpos.")
        self._on_tabela_configure(None)

    # ─────────────────────────────────────────────────────────
    # Navegação de abas
    # ─────────────────────────────────────────────────────────
    def _trocar_aba(self, chave):
        self._metodo_exibido.set(chave)
        self._atualizar_exibicao()

    def _atualizar_exibicao(self):
        chave = self._metodo_exibido.get()

        for c, _ in self.METODOS_UI:
            btn = getattr(
                self,
                f"_btn_aba_{c}",
                None
            )

            if btn:
                if c == chave:
                    btn.configure(
                        fg_color=COR_PRIMARIA,
                        text_color=COR_TEXTO_BRANCO
                    )
                else:
                    btn.configure(
                        fg_color="transparent",
                        text_color=COR_TEXTO_SECUNDARIO
                    )

        mapa_df = {
            "aoki": state.df_aoki,
            "decourt": state.df_decourt,
            "teixeira": state.df_teixeira,
            "monteiro": state.df_monteiro,
            "berberian": state.df_berberian,
        }

        col_destaque = {
            "aoki": "Carga Adm. (kN)",
            "decourt": "Carga Adm. Adotada (kN)",
            "teixeira": "Carga Adm. (kN)",
            "monteiro": "Carga Adm. (kN)",
            "berberian": "Carga Adm. (kN)",
        }

        df = mapa_df.get(chave)

        self.tabela.carregar(
            df,
            colunas_destaque=[
                col_destaque.get(chave, "")
            ]
        )
        self._on_tabela_configure(None)