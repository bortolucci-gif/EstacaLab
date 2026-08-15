"""
EstacaLab — Constantes visuais e de configuração da interface.
Paleta, fontes e dimensões centralizadas aqui para facilitar manutenção.
"""

# ============================================================
# PALETA DE CORES
# ============================================================
COR_FUNDO            = "#F5F7FA"
COR_SIDEBAR          = "#172B4D"
COR_SIDEBAR_HOVER    = "#1E3A6A"
COR_SIDEBAR_ATIVO    = "#2563EB"
COR_SIDEBAR_SECAO    = "#0F1E35"

COR_PRIMARIA         = "#2563EB"
COR_PRIMARIA_HOVER   = "#1D4ED8"
COR_SECUNDARIA       = "#64748B"

COR_CARD             = "#FFFFFF"
COR_BORDA            = "#E2E8F0"

COR_TEXTO_PRIMARIO   = "#1E293B"
COR_TEXTO_SECUNDARIO = "#64748B"
COR_TEXTO_BRANCO     = "#FFFFFF"
COR_TEXTO_SIDEBAR    = "#CBD5E1"

COR_SUCESSO          = "#16A34A"
COR_ALERTA           = "#D97706"
COR_ERRO             = "#DC2626"
COR_INFO             = "#0284C7"

COR_HEADER           = "#FFFFFF"
COR_HEADER_BORDA     = "#E2E8F0"

# ============================================================
# TIPOGRAFIA
# ============================================================
FONTE_FAMILIA        = "Segoe UI"
FONTE_MONO           = "Consolas"

FONTE_TITULO_APP     = (FONTE_FAMILIA, 15, "bold")
FONTE_TITULO         = (FONTE_FAMILIA, 16, "bold")
FONTE_SUBTITULO      = (FONTE_FAMILIA, 13, "bold")
FONTE_SECAO          = (FONTE_FAMILIA, 11, "bold")
FONTE_LABEL          = (FONTE_FAMILIA, 11)
FONTE_LABEL_SM       = (FONTE_FAMILIA, 10)
FONTE_LABEL_BOLD     = (FONTE_FAMILIA, 11, "bold")
FONTE_BOTAO          = (FONTE_FAMILIA, 11, "bold")
FONTE_SIDEBAR_ITEM   = (FONTE_FAMILIA, 11)
FONTE_SIDEBAR_SECAO  = (FONTE_FAMILIA, 9, "bold")
FONTE_TABELA         = (FONTE_MONO, 10)
FONTE_NUMERO_GRANDE  = (FONTE_FAMILIA, 24, "bold")
FONTE_NUMERO_MEDIO   = (FONTE_FAMILIA, 18, "bold")
FONTE_CAPTION        = (FONTE_FAMILIA, 9)

# ============================================================
# DIMENSÕES
# ============================================================
SIDEBAR_LARGURA      = 230
HEADER_ALTURA        = 60
PADDING_CARD         = 16
RAIO_BORDA           = 6
BTN_ALTURA           = 34
TABELA_LINHA_ALTURA  = 28

# ============================================================
# LISTAS DERIVADAS DOS DICIONÁRIOS EXISTENTES
# ============================================================
# Tipos de estaca (extraídos do Dicionario_Estacas.txt e mapeamentos internos)
LISTA_TIPOS_ESTACA = [
    "Franki de fuste apiloado",
    "Franki de fuste vibrado",
    "Metálica",
    "Pré-moldada de concreto cravada a percussão",
    "Mega",
    "Escavada mecanicamente sem lama",
    "Strauss",
    "Barrete",
    "Solo Cimento",
    "Estaca Broca",
    "Escavada com lama bentonítica",
    "Hélice contínua",
    "Ômega",
    "Raiz",
    "Injetada sob altas pressões",
]

# Tipos de solo (34 tipos do dicionário universal TradutorSolos.py)
LISTA_TIPOS_SOLO = {
    1:  "Areia",
    2:  "Areia Mto Pouco Siltosa",
    3:  "Areia Pouco Siltosa",
    4:  "Areia Siltosa",
    5:  "Areia Muito Siltosa",
    6:  "Areia Silto Argilosa",
    7:  "Areia Mto Pouco Argilosa",
    8:  "Areia Pouco Argilosa",
    9:  "Areia Argilosa",
    10: "Areia Muito Argilosa",
    11: "Areia Argilo Siltosa",
    12: "Silte",
    13: "Silte Muito Pouco Arenoso",
    14: "Silte Pouco Arenoso",
    15: "Silte Arenoso",
    16: "Silte Muito Arenoso",
    17: "Silte Areno Argiloso",
    18: "Silte Muito Pouco Argiloso",
    19: "Silte Pouco Argiloso",
    20: "Silte Argiloso",
    21: "Silte Muito Argiloso",
    22: "Silte Argilo Arenoso",
    23: "Argila",
    24: "Argila Mto Pouco Arenosa",
    25: "Argila Pouco Arenosa",
    26: "Argila Arenosa",
    27: "Argila Muito Arenosa",
    28: "Argila Areno Siltosa",
    29: "Argila Mto Pouco Siltosa",
    30: "Argila Pouco Siltosa",
    31: "Argila Siltosa",
    32: "Argila Muito Siltosa",
    33: "Argila Silto Arenosa",
    34: "Turfa",
}

# Dicionário inverso: nome -> código
SOLO_NOME_PARA_COD = {v: k for k, v in LISTA_TIPOS_SOLO.items()}

# Lista de nomes para comboboxes
LISTA_NOMES_SOLO = list(LISTA_TIPOS_SOLO.values())

from gui.validation import ValidationError

def solo_display_para_codigo(display_str: str) -> int:
    """Converte string 'Nome do Solo' para código inteiro validando-o."""
    nome = display_str.strip()
    cod = SOLO_NOME_PARA_COD.get(nome)
    
    if cod is None:
        raise ValidationError(f"Nome de solo inválido ou não reconhecido: '{display_str}'")
        
    return cod

def codigo_para_display(cod: int) -> str:
    """Converte código inteiro para string de exibição."""
    return LISTA_TIPOS_SOLO.get(cod, "Solo Desconhecido")

# Cores visuais das camadas (apenas recurso gráfico, não classificação normativa)
COR_CAMADA_AREIA  = "#F5DEB3"   # Trigo — areias (cód 1–11)
COR_CAMADA_SILTE  = "#C8B89A"   # Bege escuro — siltes (cód 12–22)
COR_CAMADA_ARGILA = "#9B7653"   # Terra — argilas (cód 23–33)
COR_CAMADA_TURFA  = "#4A3728"   # Marrom escuro — turfa (cód 34)

def cor_camada_por_codigo(cod: int) -> str:
    """Retorna cor gráfica da camada. Apenas uso visual, sem valor classificatório."""
    if 1 <= cod <= 11:
        return COR_CAMADA_AREIA
    elif 12 <= cod <= 22:
        return COR_CAMADA_SILTE
    elif 23 <= cod <= 33:
        return COR_CAMADA_ARGILA
    elif cod == 34:
        return COR_CAMADA_TURFA
    return "#CCCCCC"

# Nomes dos métodos
METODOS_NOMES = {
    "aoki":     "Aoki-Velloso (1975)",
    "decourt":  "Décourt-Quaresma (1978)",
    "teixeira": "Teixeira (1996)",
    "monteiro": "Monteiro (1997)",
    "berberian":"Berberian (2015)",
    "media":    "Média dos Métodos",
}

METODOS_CHAVE_CARGA = {
    "aoki":     "Carga Adm. (kN)",
    "decourt":  "Carga Adm. Adotada (kN)",
    "teixeira": "Carga Adm. (kN)",
    "monteiro": "Carga Adm. (kN)",
    "berberian":"Carga Adm. (kN)",
    "media":    "Carga Adm. (kN)",
}
