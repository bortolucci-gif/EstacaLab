"""
EstacaLab — Tela de Memória de Cálculo.
Exibe dados de entrada, parâmetros e resultados dos cálculos.
Permite exportação em PDF e CSV.
"""

import os
import csv
import datetime
import customtkinter as ctk
from gui.constants import *
from gui.components import (CardTitulado, BotaoPrimario, BotaoSecundario,
                             TituloPagina, Separador, MensagemStatus)
from gui.state import state
from gui.formatters import formatar_valor_tabela
from CalculoRecalque import param_estaca_recalque
from GeometriaEstacas import NOMES_SECOES, campos_secao, calcular_geometria


class TelaMemoria(ctk.CTkFrame):

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

    def _dados_estaca_memoria(self):
        forma = state.forma_estaca
        dados = [
            ["Tipo de estaca", state.tipo_estaca],
            ["Forma da seção", NOMES_SECOES.get(forma, forma)]
        ]

        for chave, label in campos_secao(forma):
            valor = state.dimensoes_estaca.get(chave)
            if valor is not None:
                dados.append([label.replace(" [m]", ""), f"{valor} m"])

        geometria = calcular_geometria(
            state.tipo_estaca, state.forma_estaca, state.dimensoes_estaca,
            state.criterio_ponta_metalica
        )

        if forma in ['perfil_i', 'perfil_h']:
            criterio = {
                "area_real": "Área real do perfil",
                "retangulo_envolvente": "Retângulo envolvente"
            }.get(state.criterio_ponta_metalica, state.criterio_ponta_metalica)
            dados.append(["Critério da área de ponta", criterio])

        if geometria.get("volume_base") is not None:
            dados.append(["Volume da base Franki", f"{geometria['volume_base']:.3f} m³"])

        dados.append(["Área de ponta, Ap", f"{geometria['Ap']:.4f} m²"])
        dados.append(["Perímetro do fuste, U", f"{geometria['U']:.4f} m"])
        dados.append(["Área estrutural, Ae", f"{geometria['Ae']:.4f} m²"])

        if geometria.get("D_nominal") is not None:
            dados.append(["Dimensão nominal", f"{geometria['D_nominal']:.4f} m"])

        dados.append(["Dimensão de influência", f"{geometria['D_influencia']:.4f} m"])
        dados.append(["Cota de arrasamento", f"{state.cota_inicio} m"])
        dados.append(["Nível d'água", "Não informado" if state.linha_agua is None else f"{state.linha_agua} m"])
        dados.append(["Solo fluviolagunar (SFL)", "Sim" if state.solo_sfl else "Não"])
        return dados

    def _construir(self):
        # ── Cabeçalho ────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 0))
        TituloPagina(header,
                     titulo="Memória de Cálculo",
                     subtitulo="Dados de entrada, parâmetros e resultados dos métodos").pack(anchor="w")
        Separador(self).grid(row=1, column=0, sticky="ew", padx=0, pady=12)

        # ── Barra de ações ────────────────────────────────────
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 8))

        BotaoPrimario(barra, texto="📄  Exportar PDF",
                       comando=self._exportar_pdf, width=160).pack(side="left", padx=(0, 8))
        BotaoSecundario(barra, texto="📊  Exportar CSV",
                         comando=self._exportar_csv, width=160).pack(side="left", padx=(0, 8))
        BotaoSecundario(barra, texto="↻  Atualizar",
                         comando=self.atualizar, width=120).pack(side="left")

        self.msg = MensagemStatus(barra)
        self.msg.pack(side="left", padx=(12, 0))

        # ── Área de texto da memória ──────────────────────────
        card = CardTitulado(self,
                             titulo="Memória de Cálculo Completa",
                             subtitulo="Dados reais utilizados pelas funções de cálculo")
        card.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 16))
        card.rowconfigure(2, weight=1)

        self.txt = ctk.CTkTextbox(card.corpo,
                                   font=(FONTE_MONO, 10),
                                   fg_color=COR_CARD,
                                   text_color=COR_TEXTO_PRIMARIO,
                                   wrap="none",
                                   corner_radius=0)
        self.txt.pack(fill="both", expand=True)

        self.atualizar()

    # ─────────────────────────────────────────────────────────
    def atualizar(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        conteudo = self._gerar_memoria()
        self.txt.insert("1.0", conteudo)
        self.txt.configure(state="disabled")

    def _gerar_memoria(self) -> str:
        """Gera o texto completo da memória de cálculo."""
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        linhas = []

        def h1(txt):  linhas.append(f"\n{'='*70}\n  {txt}\n{'='*70}")
        def h2(txt):  linhas.append(f"\n{'─'*60}\n  {txt}\n{'─'*60}")
        def par(txt): linhas.append(f"  {txt}")
        def sep():    linhas.append("")

        h1("EstacaLab — MEMÓRIA DE CÁLCULO")
        sep()
        
        h1("1. DADOS DO PROJETO")
        par(f"Projeto: {state.nome_projeto}")
        par(f"Obra: {state.obra_name}")
        par(f"Local: {state.local_obra}")
        par(f"Responsável técnico: {state.responsavel_tecnico}")
        par(f"Registro profissional: {state.registro_profissional}")
        par(f"Data da análise: {state.data_analise}")
        par(f"Observações: {state.observacoes}")
        sep()

        # ── Dados de Entrada ─────────────────────────────────
        h1("2. DADOS DA FUNDAÇÃO")

        h2("2.1 Dados da Estaca")
        for nome, valor in self._dados_estaca_memoria():
            par(f"{nome}: {valor}")
        sep()

        h1("3. PERFIL GEOTÉCNICO")
        if state.camadas:
            linha_cab = f"  {'Camada':>7}  {'Cota (m)':>8}  {'NSPT':>6}  {'Código':>6}  Tipo de Solo"
            linhas.append(linha_cab)
            linhas.append("  " + "-" * 65)
            for i, cam in enumerate(state.camadas):
                nome = LISTA_TIPOS_SOLO.get(cam['cod_solo'], "?")
                linhas.append(f"  {i+1:>7}  {-(i+1):>8.0f}  {cam['nspt']:>6.1f}  "
                               f"{cam['cod_solo']:>6}  {nome}")
        else:
            par("Nenhuma camada cadastrada.")
        sep()

        h2("2.2 Mapa de Pilares")
        if state.lista_pilares:
            linhas.append(f"  {'Pilar':>8}  {'Carga (kN)':>12}")
            linhas.append("  " + "-" * 25)
            for p in state.lista_pilares:
                linhas.append(f"  {str(p.get('Pilar','')):>8}  {p.get('Carga (kN)', 0):>12.1f}")
        else:
            par("Nenhum pilar cadastrado.")
        sep()

        # ── Resultados por Método ─────────────────────────────
        h1("4. MÉTODOS DE CAPACIDADE DE CARGA")

        mapa = {
            "Aoki-Velloso (1975)":    (state.df_aoki,      "Carga Adm. (kN)"),
            "Décourt-Quaresma (1978)":(state.df_decourt,   "Carga Adm. Adotada (kN)"),
            "Teixeira (1996)":        (state.df_teixeira,  "Carga Adm. (kN)"),
            "Monteiro (1997)":        (state.df_monteiro,  "Carga Adm. (kN)"),
            "Berberian (2015)":       (state.df_berberian, "Carga Adm. (kN)"),
        }

        for idx, (nome, (df, col)) in enumerate(mapa.items(), start=1):
            h2(f"4.{idx} {nome}")
            if df is not None:
                max_carga = formatar_valor_tabela(col, df[col].max())
                max_cota = formatar_valor_tabela("Cota (m)", df.loc[df[col].idxmax(), 'Cota (m)'])
                par(f"Carga admissível máxima: {max_carga} kN")
                par(f"Cota de apoio máxima   : {max_cota} m")
                sep()
                # Tabela completa
                linhas.append("  " + "  ".join(f"{c:>18}" for c in df.columns))
                linhas.append("  " + "-" * (20 * len(df.columns)))
                for _, row in df.iterrows():
                    linha_vals = []
                    for c_name in df.columns:
                        v = row[c_name]
                        texto = formatar_valor_tabela(c_name, v)
                        linha_vals.append(f"{texto:>18}")
                    linhas.append("  " + "  ".join(linha_vals))
            else:
                par("Não calculado.")
            sep()

        # Média dos Métodos Selecionados
        NOMES_MEMORIA = {
            "aoki":      "Aoki-Velloso (1975)",
            "decourt":   "Décourt-Quaresma (1978)",
            "teixeira":  "Teixeira (1996)",
            "monteiro":  "Monteiro (1997)",
            "berberian": "Berberian (2015)",
        }
        h2("4.6 Média dos Métodos Selecionados")
        if state.df_media is not None:
            if state.metodos_media:
                par("Métodos considerados:")
                for chave in state.metodos_media:
                    par(f"  - {NOMES_MEMORIA.get(chave, chave)}")
                sep()
            max_media = formatar_valor_tabela('Carga Adm. (kN)', state.df_media['Carga Adm. (kN)'].max())
            par(f"Carga admissível média máxima: {max_media} kN")
            for _, row in state.df_media.iterrows():
                cota_str = formatar_valor_tabela('Cota (m)', row['Cota (m)'])
                carga_str = formatar_valor_tabela('Carga Adm. (kN)', row['Carga Adm. (kN)'])
                linhas.append(f"  Cota {cota_str:>5} m  |  {carga_str:>6} kN")
        else:
            par("Não disponível (execute a capacidade de carga com 2 ou mais métodos).")
        sep()

        # ── Dimensionamento ───────────────────────────────────
        h1("5. DIMENSIONAMENTO DOS PILARES")
        if state.df_dimensionamento:
            for chave, df in state.df_dimensionamento.items():
                if df is None or df.empty:
                    continue
                h2(f"Método: {METODOS_NOMES.get(chave, chave)}")
                linhas.append("  " + "  ".join(f"{c:>22}" for c in df.columns))
                linhas.append("  " + "-" * (24 * len(df.columns)))
                for _, row in df.iterrows():
                    vals = []
                    for c_name in df.columns:
                        texto = formatar_valor_tabela(c_name, row[c_name])
                        vals.append(f"{texto:>22}")
                    linhas.append("  " + "  ".join(vals))
                sep()
        else:
            par("Dimensionamento não executado.")
        sep()

        # ── Recalque ─────────────────────────────────────────
        h1("6. ESTIMATIVA DE RECALQUE")
        h2("6.1 Parâmetros da Metodologia")
        par("Método base: Aoki-Velloso")
        if state.tipo_estaca:
            _ec_gpa, _alfa = param_estaca_recalque(state.tipo_estaca)
            par(f"Módulo de elasticidade adotado, Ec = {_ec_gpa} GPa")
            par(f"Fator α adotado = {_alfa}")
        par("Obs.: Os parâmetros Ec e α são definidos automaticamente em função do tipo de estaca"
            " informado nos dados da fundação.")
        sep()
        h2("6.2 Resultados por Pilar")
        if state.df_recalque is not None and not state.df_recalque.empty:
            linhas.append("  " + "  ".join(f"{c:>22}" for c in state.df_recalque.columns))
            linhas.append("  " + "-" * (24 * len(state.df_recalque.columns)))
            for _, row in state.df_recalque.iterrows():
                vals = []
                for c_name in state.df_recalque.columns:
                    texto = formatar_valor_tabela(c_name, row[c_name])
                    vals.append(f"{texto:>22}")
                linhas.append("  " + "  ".join(vals))
            par("\n  NOTA: A avaliação de aceitabilidade do recalque depende do critério")
            par("  adotado no projeto e nas normas aplicáveis.")
        else:
            par("Recalque não calculado.")
        sep()

        h1("7. INFORMAÇÕES DO SOFTWARE")
        par("EstacaLab")
        par("Sistema Computacional para Análise de Fundações Profundas")
        sep()
        par("Versão: 1.0")
        par("Ano: 2026")
        sep()
        par("Desenvolvido por:")
        par("Willian Bortolucci")
        sep()
        
        h1("INFORMAÇÕES DE USO E RESPONSABILIDADE")
        par("Esta memória de cálculo foi gerada pelo EstacaLab, software desenvolvido")
        par("originalmente no âmbito de um Trabalho de Conclusão de Curso (TCC) em")
        par("Engenharia Civil, com finalidade acadêmica e educacional. O software é")
        par("disponibilizado para utilização não comercial sob a PolyForm Noncommercial")
        par("License 1.0.0. Os resultados dependem dos dados de entrada, das hipóteses")
        par("e das metodologias adotadas e não substituem investigação geotécnica,")
        par("verificações normativas, provas de carga, projeto executivo ou responsabilidade")
        par("técnica profissional. A utilização comercial do software não é autorizada")
        par("nos termos da licença adotada.")
        sep()

        h1("FIM DA MEMÓRIA DE CÁLCULO")
        return "\n".join(linhas)

    # ─────────────────────────────────────────────────────────
    # Exportação PDF
    # ─────────────────────────────────────────────────────────
    def _exportar_pdf(self):
        if state.tem_pendencias(["projeto", "fundacao", "sondagem", "pilares"]):
            import tkinter.messagebox as messagebox
            messagebox.showwarning("Alterações não salvas",
                                   "Existem alterações não salvas no projeto.\nSalve todas as abas antes de exportar o PDF para garantir a integridade dos dados.")
            return

        try:
            from tkinter import filedialog
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                             Table, TableStyle, HRFlowable, NextPageTemplate, PageBreak)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_LEFT, TA_CENTER

            caminho = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                title="Salvar Memória de Cálculo como PDF",
                initialfile=f"memoria_{state.nome_projeto.replace(' ', '_')}.pdf"
            )
            if not caminho:
                return

            doc = BaseDocTemplate(caminho, leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
                                  
            frame_portrait = Frame(doc.leftMargin, doc.bottomMargin, 
                                   doc.width, doc.height, id='portrait_frame')
            template_portrait = PageTemplate(id='portrait', frames=[frame_portrait], pagesize=A4)
            
            w_landscape, h_landscape = landscape(A4)
            frame_landscape = Frame(doc.leftMargin, doc.bottomMargin, 
                                    w_landscape - doc.leftMargin - doc.rightMargin, 
                                    h_landscape - doc.topMargin - doc.bottomMargin, 
                                    id='landscape_frame')
            template_landscape = PageTemplate(id='landscape', frames=[frame_landscape], pagesize=landscape(A4))
            
            doc.addPageTemplates([template_portrait, template_landscape])

            estilos = getSampleStyleSheet()
            est_titulo = ParagraphStyle('Titulo', parent=estilos['Title'],
                                         fontSize=16, textColor=colors.HexColor("#1A2B4A"),
                                         spaceAfter=8)
            est_h1 = ParagraphStyle('H1', parent=estilos['Heading1'],
                                     fontSize=12, textColor=colors.HexColor("#2563EB"),
                                     spaceAfter=4, spaceBefore=12)
            est_h2 = ParagraphStyle('H2', parent=estilos['Heading2'],
                                     fontSize=10, textColor=colors.HexColor("#1E293B"),
                                     spaceAfter=3, spaceBefore=8)
            est_corpo = ParagraphStyle('Corpo', parent=estilos['Normal'],
                                        fontSize=9, leading=14)
            est_mono = ParagraphStyle('Mono', parent=estilos['Code'],
                                       fontSize=7.5, leading=11, fontName='Courier')
            est_cab_tab = ParagraphStyle('CabTab', parent=estilos['Normal'],
                                         fontName='Helvetica-Bold', fontSize=7.5, leading=9,
                                         alignment=TA_CENTER, textColor=colors.white)
            est_cel_txt = ParagraphStyle('CelTxt', parent=estilos['Normal'],
                                         fontName='Helvetica', fontSize=7.5, leading=9,
                                         alignment=TA_CENTER, textColor=colors.black)

            elementos = []
            now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

            # Cabeçalho
            elementos.append(Paragraph("ESTACALAB", est_titulo))
            elementos.append(Paragraph("Sistema Computacional para Análise<br/>de Fundações Profundas", est_corpo))
            elementos.append(Spacer(1, 0.2*cm))
            elementos.append(Paragraph("<b>MEMÓRIA DE CÁLCULO</b>", est_h1))
            elementos.append(HRFlowable(width="100%", thickness=1,
                                         color=colors.HexColor("#2563EB")))
            elementos.append(Spacer(1, 0.3*cm))

            # Dados do Projeto
            elementos.append(Paragraph("1. DADOS DO PROJETO", est_h1))
            
            dados_projeto = [
                ["Projeto:", state.nome_projeto],
                ["Obra:", state.obra_name],
                ["Local:", state.local_obra],
                ["Responsável técnico:", state.responsavel_tecnico],
                ["Registro profissional:", state.registro_profissional],
                ["Data:", state.data_analise],
                ["Observações:", state.observacoes],
            ]
            t_proj = Table(dados_projeto, colWidths=[4*cm, 11*cm])
            t_proj.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elementos.append(t_proj)
            elementos.append(Spacer(1, 0.3*cm))

            # Dados de Entrada
            elementos.append(Paragraph("2. DADOS DA FUNDAÇÃO", est_h1))
            elementos.append(Paragraph("2.1 Dados da Estaca", est_h2))
            dados_estaca = self._dados_estaca_memoria()
            t = Table(dados_estaca, colWidths=[5*cm, 10*cm])
            t.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ]))
            elementos.append(t)
            elementos.append(Spacer(1, 0.3*cm))

            # Sondagem SPT
            if state.camadas:
                elementos.append(Paragraph("3. PERFIL GEOTÉCNICO", est_h1))
                cab_spt = [["Camada", "Cota (m)", "NSPT", "Código", "Tipo de Solo"]]
                rows_spt = [[str(i+1), str(-(i+1)), str(c['nspt']),
                              str(c['cod_solo']), LISTA_TIPOS_SOLO.get(c['cod_solo'], "?")]
                             for i, c in enumerate(state.camadas)]
                t_spt = Table(cab_spt + rows_spt,
                               colWidths=[1.5*cm, 2*cm, 1.8*cm, 2*cm, 7*cm], repeatRows=1)
                t_spt.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A2B4A")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#F8FAFC")]),
                ]))
                elementos.append(t_spt)
                elementos.append(Spacer(1, 0.3*cm))

            # Muda para landscape para tabelas de capacidade largas
            elementos.append(NextPageTemplate('landscape'))
            elementos.append(PageBreak())

            def quebrar_nome_coluna(nome):
                n = str(nome)
                if " (m)" in n: n = n.replace(" (m)", "<br/>(m)")
                elif " (kPa)" in n: n = n.replace(" (kPa)", "<br/>(kPa)")
                elif " (kN)" in n: n = n.replace(" (kN)", "<br/>(kN)")
                n = n.replace("Rl Acumulado", "Rl<br/>Acumulado")
                n = n.replace("Carga Adm.", "Carga<br/>Adm.")
                n = n.replace("R. Total", "R.<br/>Total")
                n = n.replace("Tipo de Solo", "Tipo de<br/>Solo")
                n = n.replace("Estado Físico", "Estado<br/>Físico")
                return n

            def calcular_larguras(colunas, largura_util):
                w_peq = 1.2 * cm
                w_med = 1.7 * cm
                w_solo = 4.5 * cm
                w_estado = 3.2 * cm
                
                larguras = []
                for c in colunas:
                    c_low = str(c).lower()
                    if any(x in c_low for x in ['cota', 'l (', 'nspt', 'α', 'β', 'f1', 'f2']):
                        larguras.append(w_peq)
                    elif 'tipo de solo' in c_low:
                        larguras.append(w_solo)
                    elif 'estado físico' in c_low:
                        larguras.append(w_estado)
                    else:
                        larguras.append(w_med)
                
                soma = sum(larguras)
                if soma > largura_util:
                    fator = largura_util / soma
                    larguras = [w * fator for w in larguras]
                return larguras

            # Resultados por método
            elementos.append(Paragraph("4. MÉTODOS DE CAPACIDADE DE CARGA", est_h1))
            mapa = {
                "Aoki-Velloso (1975)":     (state.df_aoki,      "Carga Adm. (kN)"),
                "Décourt-Quaresma (1978)": (state.df_decourt,   "Carga Adm. Adotada (kN)"),
                "Teixeira (1996)":         (state.df_teixeira,  "Carga Adm. (kN)"),
                "Monteiro (1997)":         (state.df_monteiro,  "Carga Adm. (kN)"),
                "Berberian (2015)":        (state.df_berberian, "Carga Adm. (kN)"),
            }
            largura_util = w_landscape - doc.leftMargin - doc.rightMargin

            for nome, (df, col) in mapa.items():
                elementos.append(Paragraph(nome, est_h2))
                if df is not None:
                    colunas = list(df.columns)
                    cab = [[Paragraph(quebrar_nome_coluna(c), est_cab_tab) for c in colunas]]
                    
                    rows_df = []
                    for _, row in df.iterrows():
                        linha_formatada = []
                        for c in colunas:
                            v = row[c]
                            if str(c) in ["Tipo de Solo", "Estado Físico"]:
                                linha_formatada.append(Paragraph(str(v), est_cel_txt))
                            else:
                                if not isinstance(v, float):
                                    linha_formatada.append(str(v))
                                else:
                                    linha_formatada.append(f"{v:.2f}")
                        rows_df.append(linha_formatada)
                    
                    larguras = calcular_larguras(colunas, largura_util)
                    
                    t_df = Table(cab + rows_df, colWidths=larguras, repeatRows=1)
                    t_df.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 2),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A2B4A")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.2, colors.HexColor("#E2E8F0")),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [colors.white, colors.HexColor("#F8FAFC")]),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elementos.append(t_df)
                else:
                    elementos.append(Paragraph("Não calculado.", est_corpo))
                elementos.append(Spacer(1, 0.2*cm))

            # Volta para portrait para o restante
            elementos.append(NextPageTemplate('portrait'))
            elementos.append(PageBreak())

            # Dimensionamento
            if state.df_dimensionamento:
                elementos.append(Paragraph("5. DIMENSIONAMENTO DOS PILARES", est_h1))
                
                def quebrar_nome_dim(nome):
                    n = str(nome)
                    if " (m)" in n: n = n.replace(" (m)", "<br/>(m)")
                    elif " (kN)" in n: n = n.replace(" (kN)", "<br/>(kN)")
                    n = n.replace("Carga Pilar", "Carga<br/>Pilar")
                    n = n.replace("Qtd. Estacas", "Qtd.<br/>Estacas")
                    n = n.replace("Comprimento Estaca", "Comprimento<br/>Estaca")
                    n = n.replace("Cota Final", "Cota<br/>Final")
                    return n

                for chave, df in state.df_dimensionamento.items():
                    if df is None or df.empty:
                        continue
                    elementos.append(Paragraph(METODOS_NOMES.get(chave, chave), est_h2))
                    colunas = list(df.columns)
                    cab = [[Paragraph(quebrar_nome_dim(c), est_cab_tab) for c in colunas]]
                    
                    rows_df = []
                    for _, row in df.iterrows():
                        linha_formatada = []
                        for c in colunas:
                            v = row[c]
                            linha_formatada.append(str(v))
                        rows_df.append(linha_formatada)
                    
                    largura_util_port = A4[0] - doc.leftMargin - doc.rightMargin
                    larguras_dim = []
                    for c in colunas:
                        c_low = str(c).lower()
                        if 'pilar' in c_low and 'carga' not in c_low:
                            larguras_dim.append(1.5 * cm)
                        elif 'comprimento' in c_low:
                            larguras_dim.append(2.6 * cm)
                        elif 'profundidade' in c_low:
                            larguras_dim.append(2.4 * cm)
                        else:
                            larguras_dim.append(2.1 * cm)
                    
                    soma_dim = sum(larguras_dim)
                    if soma_dim > largura_util_port:
                        fator = largura_util_port / soma_dim
                        larguras_dim = [w * fator for w in larguras_dim]
                    
                    assert len(larguras_dim) == len(colunas), "Mismatch nas colunas de dimensionamento"
                    
                    t_dim = Table(cab + rows_df, colWidths=larguras_dim, repeatRows=1)
                    t_dim.setStyle(TableStyle([
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A2B4A")),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                         [colors.white, colors.HexColor("#F8FAFC")]),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elementos.append(t_dim)
                    elementos.append(Spacer(1, 0.2*cm))

            # Recalque
            if state.df_recalque is not None and not state.df_recalque.empty:
                elementos.append(Paragraph("6. ESTIMATIVA DE RECALQUE", est_h1))
                elementos.append(Paragraph("6.1 Parâmetros da Metodologia", est_h2))
                _met_base = "Aoki-Velloso"
                dados_rec_params = [["Método base", _met_base]]
                if state.tipo_estaca:
                    _ec_gpa_pdf, _alfa_pdf = param_estaca_recalque(state.tipo_estaca)
                    dados_rec_params.append(["Ec adotado", f"{_ec_gpa_pdf} GPa"])
                    dados_rec_params.append(["α adotado", str(_alfa_pdf)])
                t_rp = Table(dados_rec_params, colWidths=[5*cm, 10*cm])
                t_rp.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#EFF6FF")),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ]))
                elementos.append(t_rp)
                elementos.append(Paragraph(
                    "<i>Os parâmetros Ec e α são definidos automaticamente em função do tipo de estaca "
                    "informado nos dados da fundação.</i>",
                    est_corpo))
                elementos.append(Spacer(1, 0.2*cm))
                elementos.append(Paragraph("6.2 Resultados por Pilar", est_h2))
                colunas = list(state.df_recalque.columns)
                cab = [colunas]
                rows_r = [[str(v) if not isinstance(v, float)
                             else f"{v:.2f}" for v in row]
                            for _, row in state.df_recalque.iterrows()]
                n_cols = len(colunas)
                col_w = (A4[0] - doc.leftMargin - doc.rightMargin) / n_cols
                t_rec = Table(cab + rows_r, colWidths=[col_w]*n_cols)
                t_rec.setStyle(TableStyle([
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1A2B4A")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor("#F8FAFC")]),
                ]))
                elementos.append(t_rec)
                elementos.append(Paragraph(
                    "<i>NOTA: A avaliação de aceitabilidade do recalque depende do "
                    "critério adotado no projeto e nas normas aplicáveis.</i>",
                    est_corpo))
            
            elementos.append(Spacer(1, 0.5*cm))
            elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
            elementos.append(Paragraph("INFORMAÇÕES DO SOFTWARE", est_h1))
            elementos.append(Paragraph("EstacaLab – versão 1.0 – 2026<br/><br/>Desenvolvido por:<br/><b>Willian Bortolucci</b>", est_corpo))
            
            elementos.append(Spacer(1, 0.5*cm))
            elementos.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
            elementos.append(Paragraph("INFORMAÇÕES DE USO E RESPONSABILIDADE", est_h2))
            elementos.append(Paragraph("Esta memória de cálculo foi gerada pelo EstacaLab, software desenvolvido "
                                       "originalmente no âmbito de um Trabalho de Conclusão de Curso (TCC) em "
                                       "Engenharia Civil. O software é disponibilizado para utilização não comercial "
                                       "sob a PolyForm Noncommercial License 1.0.0. Os resultados dependem dos dados "
                                       "de entrada, das hipóteses e das metodologias adotadas e não substituem "
                                       "investigação geotécnica, verificações normativas, provas de carga, projeto "
                                       "executivo ou responsabilidade técnica profissional. A utilização comercial "
                                       "do software não é autorizada nos termos da licença adotada.", est_corpo))

            doc.build(elementos)
            self.msg.ok(f"PDF exportado: {os.path.basename(caminho)}")

        except Exception as e:
            self.msg.erro(f"Erro ao gerar PDF: {e}")

    # ─────────────────────────────────────────────────────────
    # Exportação CSV
    # ─────────────────────────────────────────────────────────
    def _exportar_csv(self):
        try:
            from tkinter import filedialog
            pasta = filedialog.askdirectory(title="Selecione a pasta para os arquivos CSV")
            if not pasta:
                return

            now = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            n_arquivos = 0

            mapa = {
                "aoki":     (state.df_aoki,      "aoki_velloso"),
                "decourt":  (state.df_decourt,   "decourt_quaresma"),
                "teixeira": (state.df_teixeira,  "teixeira"),
                "monteiro": (state.df_monteiro,  "monteiro"),
                "berberian":(state.df_berberian, "berberian"),
            }
            for _, (df, sufixo) in mapa.items():
                if df is not None:
                    caminho = os.path.join(pasta, f"cap_carga_{sufixo}_{now}.csv")
                    df.to_csv(caminho, index=False, encoding="utf-8-sig", sep=";")
                    n_arquivos += 1

            for chave, df in state.df_dimensionamento.items():
                if df is not None and not df.empty:
                    caminho = os.path.join(pasta, f"dim_{chave}_{now}.csv")
                    df.to_csv(caminho, index=False, encoding="utf-8-sig", sep=";")
                    n_arquivos += 1

            if state.df_recalque is not None and not state.df_recalque.empty:
                caminho = os.path.join(pasta, f"recalque_{now}.csv")
                state.df_recalque.to_csv(caminho, index=False, encoding="utf-8-sig", sep=";")
                n_arquivos += 1

            self.msg.ok(f"{n_arquivos} arquivo(s) CSV exportados em: {pasta}")

        except Exception as e:
            self.msg.erro(f"Erro ao exportar CSV: {e}")