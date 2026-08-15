# EstacaLab

Sistema Computacional para Análise de Fundações Profundas.

## Sobre

O EstacaLab é uma ferramenta computacional de apoio acadêmico desenvolvida no âmbito de um Trabalho de Conclusão de Curso (TCC) em Engenharia Civil. A aplicação sistematiza procedimentos de análise geotécnica de fundações por estacas a partir de dados de sondagem SPT, integrando métodos semiempíricos de capacidade de carga, pré-dimensionamento geotécnico, estimativa de recalques e recursos de comparação e documentação.

> [!IMPORTANT]
> O EstacaLab é uma ferramenta com caráter puramente acadêmico, educacional e de apoio à análise preliminar. O programa **não** substitui a elaboração de projeto executivo de fundações, investigações detalhadas de campo, provas de carga de campo, o cumprimento estrito das normas técnicas aplicáveis (como a ABNT NBR 6122) e tampouco prescinde do julgamento e da responsabilidade de um engenheiro civil habilitado.

---

## Funcionalidades

O sistema oferece recursos modulares organizados de forma a guiar o fluxo analítico de fundações:

*   **Entrada de Perfil SPT:** Cadastro de camadas de solo com até 34 classificações e respectivos valores de resistência à penetração ($N_{SPT}$).
*   **Diversidade Geométrica e Tipológica:** Tratamento de diferentes tipologias e geometrias de estacas, contemplando seções circulares, quadradas e retangulares, perfis metálicos I/H e representação específica da base alargada das estacas Franki.
*   **Capacidade de Carga:** Implementação paralela e modular de cinco métodos semiempíricos:
    *   Aoki-Velloso (1975)
    *   Décourt-Quaresma (1978)
    *   Teixeira (1996)
    *   Monteiro (1997)
    *   Berberian (2015)
*   **Comparativo de Métodos:** Visualização simultânea dos resultados de capacidade de carga ao longo das cotas analisadas.
*   **Média dos Métodos:** Média aritmética dos métodos selecionados utilizada exclusivamente como indicador comparativo visual no gráfico, não constituindo um novo método, não representando consenso geotécnico e não sendo utilizada como resultado necessariamente mais seguro ou correto.
*   **Pré-dimensionamento por Pilar:** Pré-dimensionamento geotécnico por pilar, com estimativa preliminar da quantidade de estacas, distribuição da carga por elemento, busca da primeira cota discretizada que atende à solicitação e cálculo do comprimento correspondente.
*   **Estimativa de Recalque:** Estimativa preliminar do recalque elástico ($\rho_e$), da parcela de recalque associada ao solo ($\rho_s$) e do recalque total sob a carga de serviço, tendo como referência metodológica Aoki (1984), com adaptações computacionais descritas no TCC.
*   **Nível d'Água:** Consideração do nível d’água na determinação das tensões efetivas empregadas na rotina de estimativa de recalques.
*   **Interação de Estacas Vizinhas:** Representação aproximada da influência de estacas vizinhas na estimativa de recalques, empregando a idealização de Boussinesq adotada na implementação (não correspondendo a uma análise completa de interação de grupo).
*   **Visualização Gráfica:** Gráficos comparativos gerados com Matplotlib que demonstram o nível do terreno, a cota de arrasamento, as curvas dos métodos e a média como referência visual.
*   **Memória de Cálculo:** Emissão de documento que reúne dados, parâmetros e resultados de cálculo, disponibilizando recursos de exportação e documentação.
*   **Gestão de Projetos:** Salvamento e abertura rápida de arquivos no formato de dados `.estacalab`.

---

## Estrutura do Projeto

Abaixo é apresentada a organização dos principais arquivos do diretório de desenvolvimento:

```text
EstacaLab/
├── app_gui.py                            # Ponto de entrada do aplicativo (GUI)
├── CalculoRecalque.py                    # Rotinas matemáticas para estimativa de recalque
├── DimensionamentoPilares.py             # Rotina de pré-dimensionamento geotécnico por pilar
├── GeometriaEstacas.py                   # Modelagem geométrica e de propriedades das seções das estacas
├── PlotGraficos.py                       # Funções para plotagem de gráficos com Matplotlib
├── TradutorSolos.py                      # Tradutor/mapeador entre os diferentes códigos e classificações de solos
├── FuncCapacidadeCarga[Autor].py         # Implementações matemáticas dos métodos de capacidade de carga
├── TabelaParametros[Autor].py            # Parâmetros geotécnicos tabelados dos respectivos autores
├── logo.png                              # Logotipo do software
├── gui/                                  # Componentes visuais CustomTkinter da interface
│   ├── app.py                            # Frame do container principal
│   ├── components.py                     # Classes customizadas de botões, cards e inputs
│   ├── constants.py                      # Definição de cores, fontes e leiaute
│   ├── state.py                          # Controlador de estados globais do software
│   └── tela_[recurso].py                 # Arquivos contendo o leiaute de cada aba/tela
├── tests/                                # Suíte de testes automatizados do sistema
│   ├── run_all.py                        # Script executor geral de testes
│   └── teste_[recurso].py                # Scripts de testes unitários e de integração
├── requirements.txt                      # Dependências externas do projeto
└── README.md                             # Documento de apresentação do sistema (este arquivo)
```

---

## Requisitos do Sistema

*   **Python:** Desenvolvido e verificado utilizando a versão **Python 3.14.6**.
*   **Bibliotecas Externas:**
    *   `customtkinter`
    *   `pandas`
    *   `numpy`
    *   `matplotlib`
    *   `Pillow`
    *   `reportlab`

---

## Instalação a partir do Código-Fonte

1.  **Obter o código-fonte:**
    ```bash
    git clone https://github.com/bortolucci-gif/EstacaLab.git
    cd EstacaLab
    ```

2.  **Criar e ativar o ambiente virtual (Recomendável):**
    *   **No Windows:**
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **No Linux/macOS:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```

3.  **Instalar as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Executar o software:**
    ```bash
    python app_gui.py
    ```

---

## Verificação Computacional

A implementação é acompanhada por uma suíte automatizada de verificação computacional destinada a conferir comportamentos e dependências previamente definidos nas rotinas do sistema. Esse resultado representa verificação computacional da implementação e não validação experimental ou geotécnica externa:

*   **Suíte automatizada:** 11 scripts de verificação.
*   **Resultado da versão candidata:**
    ```text
    PASS: 11
    FAIL: 0
    ```

---

## Uso, Limitações e Responsabilidade Técnica

A utilização desta ferramenta deve obedecer aos seguintes princípios:
*   Os resultados de capacidade de carga e recalque são estimativas de modelos teóricos e dependem inteiramente da qualidade, representatividade e precisão das informações fornecidas pelo usuário (investigação geotécnica).
*   As limitações e hipóteses próprias de cada metodologia permanecem aplicáveis e são discutidas no TCC associado.
*   A média aritmética dos métodos selecionados é utilizada exclusivamente como indicador comparativo visual, não devendo ser entendida como valor de dimensionamento.
*   O pré-dimensionamento por pilar possui natureza preliminar, estimando a quantidade geotécnica de estacas e a distribuição de cargas, o que não substitui o projeto executivo estrutural do bloco e as análises normativas.
*   A estimativa de recalques utiliza aproximações teóricas simplificadas e a idealização de Boussinesq para influência de estacas vizinhas, constituindo apenas uma indicação preliminar de deformabilidade.
*   Qualquer uso técnico profissional do software exige a devida responsabilidade técnica de engenheiro habilitado.

---

## Licença

O EstacaLab é disponibilizado sob a PolyForm Noncommercial License 1.0.0 (`PolyForm-Noncommercial-1.0.0`). A licença permite os usos não comerciais nela especificados e não concede autorização para utilização comercial do software. Consulte o arquivo `LICENSE` para os termos completos e aplicáveis.

O licenciamento do software não representa validação geotécnica ou certificação técnica e não dispensa as verificações, normas e responsabilidades profissionais aplicáveis.

---

## Versão Associada ao TCC

A versão do software correspondente à versão apresentada no Trabalho de Conclusão de Curso será identificada pela tag `v1.0.0` e pelo respectivo commit de congelamento. Essas informações serão preenchidas após a criação do repositório e da release.

*   **Versão atual:** 1.0.0 (Candidata a Congelamento)

---

## Autor

*   **Willian Bortolucci** - Engenharia Civil

---

## Referências Metodológicas

O EstacaLab implementa ou utiliza como referência procedimentos associados a Aoki-Velloso, Décourt-Quaresma, Teixeira, Monteiro, Berberian e Aoki, além de fundamentos de mecânica dos solos aplicados à estimativa de recalques. A formulação adotada, as adaptações computacionais, as limitações e as referências bibliográficas completas encontram-se documentadas no TCC associado ao software.
