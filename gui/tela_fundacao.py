import customtkinter as ctk
from gui.constants import *
from gui.components import (CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador, MensagemStatus)
from gui.state import state
from gui.validation import (parse_float, validar_cota_arrasamento,
                            validar_cota_vs_sondagem, ValidationError)
from GeometriaEstacas import (
    NOMES_SECOES, secoes_permitidas, secao_padrao,
    campos_secao, calcular_geometria,
    interpolar_volume_franki, area_ponta_franki
)
import os
import tkinter as tk
from PIL import Image

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.bind("<Enter>", self.mostrar)
        self.widget.bind("<Leave>", self.esconder)
        self.widget.bind("<Destroy>", self.esconder)

    def mostrar(self, event=None):
        if self.tw:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 5
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 3
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        self.tw.attributes("-topmost", True)
        
        frame = ctk.CTkFrame(self.tw, fg_color="#F8FAFC", border_color="#CBD5E1", border_width=1, corner_radius=0)
        frame.pack(fill="both", expand=True)
        
        lbl = ctk.CTkLabel(
            frame, text=self.text, font=FONTE_CAPTION,
            text_color=COR_TEXTO_PRIMARIO, justify="left", wraplength=240
        )
        lbl.pack(padx=8, pady=8, anchor="w")

    def esconder(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None


IMAGENS_GEOMETRIA = {
    "circular": "secao_circular.png",
    "quadrada": "secao_quadrada.png",
    "franki": "estaca_franki.png",
    "retangular": "barrete.png",
    "perfil_i": "perfil_metalico_i_h.png",
    "perfil_h": "perfil_metalico_i_h.png",
}


class TelaFundacao(ctk.CTkFrame):

    def __init__(self, master, nav_callback=None, **kwargs):
        super().__init__(master, fg_color=COR_FUNDO, **kwargs)
        self.nav_callback = nav_callback
        self.columnconfigure(0, weight=1)

        self._vars = {}
        self._carregando_ui = False
        self._forma_atual = None
        self._cache_dimensoes = {}

        self._construir()

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))

        TituloPagina(
            header,
            titulo="Dados da Fundação",
            subtitulo="Defina o tipo de estaca e parâmetros geométricos"
        ).pack(anchor="w")

        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Conteúdo ─────────────────────────────────────────
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.grid(row=2, column=0, sticky="nsew", padx=24, pady=0)
        corpo.columnconfigure(0, weight=1)
        corpo.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        card_tipo = CardTitulado(
            corpo,
            titulo="Tipo de Estaca",
            subtitulo="Selecione o tipo conforme o Dicionário de Estacas do projeto"
        )
        card_tipo.grid(row=0, column=0, sticky="nsew",
                       padx=(0, 8), pady=(0, 12))

        self._construir_tipo_estaca(card_tipo.corpo)

        card_geom = CardTitulado(
            corpo,
            titulo="Parâmetros Geométricos",
            subtitulo="Dimensões e cotas"
        )
        card_geom.grid(row=0, column=1, sticky="nsew",
                       padx=(8, 0), pady=(0, 12))

        self._construir_geometria(card_geom.corpo)

        # ── Barra de ação ────────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 16))

        self.msg = MensagemStatus(barra)
        self.msg.pack(side="left")

        self.lbl_status = ctk.CTkLabel(
            barra,
            text="✓ Dados salvos",
            text_color=COR_SUCESSO,
            font=FONTE_LABEL
        )
        self.lbl_status.pack(side="right", padx=(10, 0))

        BotaoPrimario(
            barra,
            texto="💾  Salvar Dados",
            comando=self._salvar,
            width=160
        ).pack(side="right")

        BotaoSecundario(
            barra,
            texto="↻  Restaurar",
            comando=self._restaurar,
            width=120
        ).pack(side="right", padx=(0, 8))

        self._restaurar()

    def _construir_tipo_estaca(self, master):
        master.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            master,
            text="Tipo de Estaca",
            font=FONTE_LABEL,
            text_color=COR_TEXTO_SECUNDARIO
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._vars['tipo_estaca'] = ctk.StringVar(value=state.tipo_estaca)
        self._vars['tipo_estaca'].trace_add("write", self._on_edit)

        cb = ctk.CTkComboBox(
            master,
            variable=self._vars['tipo_estaca'],
            values=LISTA_TIPOS_ESTACA,
            width=300,
            font=FONTE_LABEL,
            dropdown_font=FONTE_LABEL,
            state="readonly",
            command=self._tipo_alterado
        )
        cb.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        ctk.CTkLabel(
            master,
            text="Forma da Seção Transversal",
            font=FONTE_LABEL,
            text_color=COR_TEXTO_SECUNDARIO
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        self._vars['forma_estaca'] = ctk.StringVar(value=state.forma_estaca)
        self._vars['forma_estaca'].trace_add("write", self._on_edit)

        self.frame_radio = ctk.CTkFrame(master, fg_color="transparent")
        self.frame_radio.grid(row=3, column=0, sticky="w")

        self._atualizar_secoes()

        info = ctk.CTkFrame(
            master,
            fg_color="#EFF6FF",
            border_color="#BFDBFE",
            border_width=1,
            corner_radius=4
        )
        info.grid(row=4, column=0, sticky="ew", pady=(16, 0))

        ctk.CTkLabel(
            info,
            text="ℹ  As formas disponíveis dependem do tipo de estaca selecionado.",
            font=FONTE_CAPTION,
            text_color=COR_INFO,
            wraplength=280,
            justify="left"
        ).pack(padx=10, pady=8, anchor="w")

    def _construir_geometria(self, master):
        master.columnconfigure(0, weight=1)
        master.columnconfigure(1, weight=0)

        self.frame_imagem_geometria = ctk.CTkFrame(master, fg_color="transparent")
        self.frame_imagem_geometria.grid(row=0, column=1, rowspan=4, sticky="n", padx=(20, 0))
        
        self.lbl_imagem_geometria = ctk.CTkLabel(self.frame_imagem_geometria, text="")
        self.lbl_imagem_geometria.pack(anchor="n")

        self.frame_geometria = ctk.CTkFrame(master, fg_color="transparent")
        self.frame_geometria.grid(row=0, column=0, sticky="ew")

        self._vars['cota_inicio'] = ctk.StringVar(value="")
        self._vars['cota_inicio'].trace_add("write", self._on_edit)

        self._atualizar_campos_geometria()

    def _atualizar_secoes(self):
        for widget in self.frame_radio.winfo_children():
            widget.destroy()

        tipo = self._vars['tipo_estaca'].get()
        secoes = secoes_permitidas(tipo)

        if self._vars['forma_estaca'].get() not in secoes:
            self._vars['forma_estaca'].set(secao_padrao(tipo))

        for forma in secoes:
            ctk.CTkRadioButton(
                self.frame_radio,
                text=NOMES_SECOES[forma],
                variable=self._vars['forma_estaca'],
                value=forma,
                command=self._forma_alterada,
                font=FONTE_LABEL
            ).pack(side="left", padx=(0, 18))

    def _salvar_cache_geometria(self):
        if self._forma_atual is None:
            return

        valores = {}

        for chave, _ in campos_secao(self._forma_atual):
            var = self._vars.get(f'dim_{chave}')
            if var is not None:
                valores[chave] = var.get()

        if valores:
            self._cache_dimensoes[self._forma_atual] = valores

    def _atualizar_campos_geometria(self, salvar_cache=True):
        if salvar_cache:
            self._salvar_cache_geometria()

        for widget in self.frame_geometria.winfo_children():
            widget.destroy()

        for chave in list(self._vars.keys()):
            if chave.startswith('dim_') or chave == 'criterio_ponta':
                del self._vars[chave]

        forma = self._vars['forma_estaca'].get()
        self._forma_atual = forma

        valores = self._cache_dimensoes.get(forma, {})

        for i, (chave, label) in enumerate(campos_secao(forma)):
            if forma in ['perfil_i', 'perfil_h']:
                pady_label = (0, 2)
                pady_entry = (0, 4)
            else:
                pady_label = (0, 3)
                pady_entry = (0, 8)

            ctk.CTkLabel(
                self.frame_geometria,
                text=label,
                font=FONTE_LABEL,
                text_color=COR_TEXTO_SECUNDARIO
            ).grid(row=i * 2, column=0, sticky="w", pady=pady_label)

            valor = valores.get(chave, self._valor_padrao(forma, chave))

            self._vars[f'dim_{chave}'] = ctk.StringVar(value=valor)
            self._vars[f'dim_{chave}'].trace_add("write", self._on_edit)

            ctk.CTkEntry(
                self.frame_geometria,
                textvariable=self._vars[f'dim_{chave}'],
                font=FONTE_LABEL,
                width=120
            ).grid(row=i * 2 + 1, column=0, sticky="w", pady=pady_entry)

        linha = len(campos_secao(forma)) * 2

        if forma == 'franki':
            self.lbl_franki = ctk.CTkLabel(
                self.frame_geometria,
                text="Volume da base: —",
                font=FONTE_CAPTION,
                text_color=COR_INFO,
                justify="left"
            )
            self.lbl_franki.grid(row=linha, column=0, sticky="w", pady=(2, 0))

            self.lbl_franki_faixa = ctk.CTkLabel(
                self.frame_geometria,
                text="Faixa válida: 0,35 m ≤ Df ≤ 0,60 m",
                font=FONTE_CAPTION,
                text_color=COR_INFO,
                justify="left"
            )
            self.lbl_franki_faixa.grid(row=linha + 1, column=0, sticky="w", pady=(0, 8))

            self._vars['dim_diametro'].trace_add(
                "write", self._atualizar_franki
            )
            self._atualizar_franki()
            linha += 2

        if forma in ['perfil_i', 'perfil_h']:
            ctk.CTkLabel(
                self.frame_geometria,
                text="Área considerada na ponta",
                font=FONTE_LABEL,
                text_color=COR_TEXTO_SECUNDARIO
            ).grid(row=linha, column=0, sticky="w", pady=(3, 2))

            self._vars['criterio_ponta'] = ctk.StringVar(
                value=state.criterio_ponta_metalica or ""
            )
            self._vars['criterio_ponta'].trace_add("write", self._on_edit)

            frame_area_real = ctk.CTkFrame(self.frame_geometria, fg_color="transparent")
            frame_area_real.grid(row=linha + 1, column=0, sticky="w", pady=(0, 2))
            
            ctk.CTkRadioButton(
                frame_area_real,
                text="Área real do perfil",
                variable=self._vars['criterio_ponta'],
                value="area_real",
                font=FONTE_LABEL
            ).pack(side="left")
            
            lbl_info1 = ctk.CTkLabel(
                frame_area_real, text="ⓘ", font=(FONTE_FAMILIA, 13),
                text_color=COR_INFO, cursor="hand2"
            )
            lbl_info1.pack(side="left", padx=(4, 0))
            Tooltip(lbl_info1, "Considera somente a área efetiva de aço da seção I/H na ponta.")

            frame_retangulo = ctk.CTkFrame(self.frame_geometria, fg_color="transparent")
            frame_retangulo.grid(row=linha + 2, column=0, sticky="w")
            
            ctk.CTkRadioButton(
                frame_retangulo,
                text="Retângulo envolvente",
                variable=self._vars['criterio_ponta'],
                value="retangulo_envolvente",
                font=FONTE_LABEL
            ).pack(side="left")
            
            lbl_info2 = ctk.CTkLabel(
                frame_retangulo, text="ⓘ", font=(FONTE_FAMILIA, 13),
                text_color=COR_INFO, cursor="hand2"
            )
            lbl_info2.pack(side="left", padx=(4, 0))
            Tooltip(lbl_info2, "Considera a área externa h × bf que envolve o perfil.")
            
            linha += 3

        if forma in ['perfil_i', 'perfil_h']:
            pady_cota_label = (4, 2)
            pady_cota_entry = (0, 6)
        else:
            pady_cota_label = (8, 3)
            pady_cota_entry = (0, 12)

        ctk.CTkLabel(
            self.frame_geometria,
            text="Cota de Arrasamento [m]",
            font=FONTE_LABEL,
            text_color=COR_TEXTO_SECUNDARIO
        ).grid(row=linha, column=0, sticky="w", pady=pady_cota_label)

        ctk.CTkEntry(
            self.frame_geometria,
            textvariable=self._vars['cota_inicio'],
            font=FONTE_LABEL,
            width=120
        ).grid(row=linha + 1, column=0, sticky="w", pady=pady_cota_entry)

        nota = ctk.CTkFrame(
            self.frame_geometria,
            fg_color="#FFF7ED",
            border_color="#FED7AA",
            border_width=1,
            corner_radius=4
        )
        nota.grid(row=linha + 2, column=0, sticky="ew")

        ctk.CTkLabel(
            nota,
            text="⚠️ A cota de arrasamento deve ser um valor inteiro negativo\n"
                 "(ex: -1 significa 1 m abaixo do nível do terreno).",
            font=FONTE_CAPTION,
            text_color=COR_ALERTA,
            wraplength=280,
            justify="left"
        ).pack(padx=10, pady=8, anchor="w")

        self._atualizar_imagem_geometria()

    def _atualizar_imagem_geometria(self):
        forma = self._vars['forma_estaca'].get()
        nome_arquivo = IMAGENS_GEOMETRIA.get(forma)

        if not nome_arquivo:
            self.lbl_imagem_geometria.configure(image="", text="Imagem não disponível")
            self._imagem_geometria_ctk = None
            return

        caminho = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets",
            "estacas",
            nome_arquivo
        )

        if not os.path.exists(caminho):
            self.lbl_imagem_geometria.configure(image="", text="Imagem não disponível")
            self._imagem_geometria_ctk = None
            return

        try:
            imagem = Image.open(caminho)

            largura_original, altura_original = imagem.size

            max_w = 250
            max_h = 340

            escala = min(
                max_w / largura_original,
                max_h / altura_original
            )

            largura = max(1, int(largura_original * escala))
            altura = max(1, int(altura_original * escala))

            self._imagem_geometria_ctk = ctk.CTkImage(
                light_image=imagem,
                dark_image=imagem,
                size=(largura, altura)
            )

            self.lbl_imagem_geometria.configure(
                image=self._imagem_geometria_ctk,
                text=""
            )

        except Exception:
            self._imagem_geometria_ctk = None
            self.lbl_imagem_geometria.configure(image="", text="Imagem não disponível")

    def _valor_padrao(self, forma, chave):
        return ""

    def _tipo_alterado(self, escolha=None):
        self._atualizar_secoes()
        self._atualizar_campos_geometria()

    def _forma_alterada(self):
        self._atualizar_campos_geometria()

    def _atualizar_franki(self, *args):
        try:
            D = parse_float(self._vars['dim_diametro'].get())
            V = interpolar_volume_franki(D)
            Ap = area_ponta_franki(V)

            self.lbl_franki.configure(
                text=f"Volume interpolado: {V:.3f} m³ | Ap: {Ap:.3f} m²"
            )
        except Exception:
            self.lbl_franki.configure(
                text="Diâmetro Franki permitido: 0,35 a 0,60 m"
            )

    def _validar_dimensao(self, valor, nome):
        try:
            valor = parse_float(valor)
        except ValidationError:
            raise ValidationError(f"{nome} inválido.")

        if valor <= 0:
            raise ValidationError(f"{nome} deve ser maior que zero.")

        return valor

    # ─────────────────────────────────────────────────────────
    # Salvar / Restaurar
    # ─────────────────────────────────────────────────────────
    def _extrair_dados(self) -> dict:
        tipo = self._vars['tipo_estaca'].get()
        forma = self._vars['forma_estaca'].get()
        dimensoes = {}

        for chave, label in campos_secao(forma):
            dimensoes[chave] = self._validar_dimensao(
                self._vars[f'dim_{chave}'].get(),
                label.replace(" [m]", "")
            )

        criterio = None

        if forma in ['perfil_i', 'perfil_h']:
            criterio = self._vars['criterio_ponta'].get()

            if criterio not in ['area_real', 'retangulo_envolvente']:
                raise ValidationError(
                    "Selecione a área considerada na ponta da estaca metálica."
                )

        cota = validar_cota_arrasamento(
            self._vars['cota_inicio'].get()
        )

        try:
            calcular_geometria(tipo, forma, dimensoes, criterio)
        except ValueError as e:
            raise ValidationError(str(e))

        return {
            "tipo_estaca": tipo,
            "forma_estaca": forma,
            "dimensoes_estaca": dimensoes,
            "criterio_ponta_metalica": criterio,
            "cota_inicio": cota
        }

    def _salvar(self):
        try:
            dados = self._extrair_dados()

            validar_cota_vs_sondagem(
                dados['cota_inicio'],
                state.camadas
            )

            mudou = (
                not state.fundacao_preenchida or
                state.tipo_estaca != dados['tipo_estaca'] or
                state.forma_estaca != dados['forma_estaca'] or
                state.dimensoes_estaca != dados['dimensoes_estaca'] or
                state.criterio_ponta_metalica != dados['criterio_ponta_metalica'] or
                state.cota_inicio != dados['cota_inicio']
            )

            state.tipo_estaca = dados['tipo_estaca']
            state.forma_estaca = dados['forma_estaca']
            state.dimensoes_estaca = dados['dimensoes_estaca'].copy()
            state.criterio_ponta_metalica = dados['criterio_ponta_metalica']
            state.cota_inicio = dados['cota_inicio']
            state.fundacao_preenchida = True

            if mudou:
                state.marcar_projeto_modificado()
                state.df_aoki = state.df_decourt = state.df_teixeira = None
                state.df_monteiro = state.df_berberian = state.df_media = None
                state.metodos_media = []
                state.df_dimensionamento = {}
                state.df_recalque = None

            state.marcar_salvo("fundacao")
            self._atualizar_header()
            state.notificar()
            self.msg.ok("Dados salvos com sucesso.")

        except ValidationError as e:
            self.msg.erro(str(e))
        except Exception as e:
            self.msg.erro(f"Erro inesperado: {e}")

    def _on_edit(self, *args):
        if self._carregando_ui:
            return

        state.marcar_pendente("fundacao")
        self._atualizar_header()

    def _atualizar_header(self):
        if state.tem_pendencias(["fundacao"]):
            self.lbl_status.configure(
                text="● Alterações não salvas",
                text_color=COR_ALERTA
            )
        else:
            self.lbl_status.configure(
                text="✓ Dados salvos",
                text_color=COR_SUCESSO
            )

    def _restaurar(self):
        self._carregando_ui = True

        try:
            self._vars['tipo_estaca'].set(state.tipo_estaca)
            self._vars['forma_estaca'].set(state.forma_estaca)

            if state.fundacao_preenchida:
                self._cache_dimensoes = {
                    state.forma_estaca: {
                        chave: str(valor).replace('.', ',')
                        for chave, valor in state.dimensoes_estaca.items()
                    }
                }
            else:
                self._cache_dimensoes = {}

            self._atualizar_secoes()
            self._atualizar_campos_geometria(salvar_cache=False)

            if state.fundacao_preenchida:
                if 'criterio_ponta' in self._vars:
                    self._vars['criterio_ponta'].set(
                        state.criterio_ponta_metalica or ""
                    )
                self._vars['cota_inicio'].set(str(state.cota_inicio))
            else:
                if 'criterio_ponta' in self._vars:
                    self._vars['criterio_ponta'].set("")
                self._vars['cota_inicio'].set("")

        finally:
            self._carregando_ui = False

        self._atualizar_header()
        self.msg.limpar()