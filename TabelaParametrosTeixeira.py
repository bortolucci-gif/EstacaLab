import pandas as pd

def paramTeixeiraAlfaTab():
    # Valores de alfa (kPa) baseados na tabela de Teixeira
    dados = {
        'Tipo de Solo': [
            'Areia com pedregulho', 'Areia', 'Areia Siltosa', 'Areia Argilosa',
            'Silte Arenoso', 'Silte Argiloso', 'Argila Arenosa', 'Argila Siltosa'
        ],
        'Pré - moldadas e metálicas': [440, 400, 360, 300, 260, 160, 210, 110],
        'Tipo Franki': [380, 340, 300, 240, 210, 120, 160, 100],
        'Escavadas a céu aberto': [310, 270, 240, 200, 160, 110, 130, 100],
    }
    return pd.DataFrame(dados)

def paramTeixeiraBetaTab():
    # Valores de beta (kPa) baseados no tipo de estaca
    dados = {
        'Tipo de Estaca': [
            'Pré - moldadas e metálicas', 
            'Tipo Franki',
            'Escavadas a céu aberto', 
            'Estaca Raiz'
        ],
        'beta (kPa)': [4, 5, 4, 6]
    }
    return pd.DataFrame(dados)