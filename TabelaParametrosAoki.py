import pandas as pd

def paramAokiTab():
    """
    Retorna o DataFrame com os parâmetros K (kPa) e alfa (decimal)
    segundo Aoki & Velloso (1975).
    """
    dados = {
        'Solo': [
            'Areia',
            'Areia siltosa',
            'Areia siltoargilosa',
            'Areia argilosa',
            'Areia argilossiltosa',
            'Silte',
            'Silte arenoso',
            'Silte arenoargiloso',
            'Silte argiloso',
            'Silte argiloarenoso',
            'Argila',
            'Argila arenosa',
            'Argila arenossiltosa',
            'Argila siltosa',
            'Argila siltoarenosa'
        ],
        'Código': [1, 12, 123, 13, 132, 2, 21, 213, 23, 231, 3, 31, 312, 32, 321],
        'K (kPa)': [1000.0, 800.0, 700.0, 600.0, 500.0, 400.0, 550.0, 450.0, 230.0, 250.0, 200.0, 350.0, 300.0, 220.0, 330.0],
        'alfa': [0.014, 0.020, 0.024, 0.030, 0.028, 0.030, 0.022, 0.028, 0.034, 0.030, 0.060, 0.024, 0.028, 0.040, 0.030]
    }
    return pd.DataFrame(dados)

def fatorCorrAoki(D):
    # Fórmula de F1 para Pré-moldada baseada na imagem fornecida
    f1_pre = 1 + (D / 0.8)
    
    dados = {
        'Tipo de Estaca': [
            'Franki', 
            'Metálica', 
            'Pré-moldada', 
            'Escavada', 
            'Raiz, Hélice contínua e Ômega'
        ],
        'F1': [2.50, 1.75, round(f1_pre, 2), 3.00, 2.00],
        'F2': [5.00, 3.50, round(2 * f1_pre, 2), 6.00, 4.00]
    }
    return pd.DataFrame(dados)