import pandas as pd

def paramMonteiroTab():
    """
    Retorna o DataFrame com os parâmetros K (convertido para kPa) e alfa (decimal)
    segundo Monteiro (1997).
    """
    dados = {
        'Solo': [
            'Areia', 'Areia siltosa', 'Areia siltoargilosa', 'Areia argilossiltosa', 'Areia argilosa',
            'Silte arenoso', 'Silte arenoargiloso', 'Silte', 'Silte argiloarenoso', 'Silte argiloso',
            'Argila arenosa', 'Argila arenossiltosa', 'Argila siltoarenosa', 'Argila siltosa', 'Argila'
        ],
        'Código': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        # Valores originais multiplicados por 100 (kgf/cm² -> kPa)
        'K (kPa)': [730.0, 680.0, 630.0, 570.0, 540.0, 500.0, 450.0, 480.0, 400.0, 320.0, 440.0, 300.0, 330.0, 260.0, 250.0],
        # Valores originais divididos por 100 (porcentagem -> decimal)
        'alfa': [0.021, 0.023, 0.024, 0.029, 0.028, 0.030, 0.032, 0.032, 0.033, 0.036, 0.024, 0.028, 0.030, 0.040, 0.060]
    }
    return pd.DataFrame(dados)

def fatorCorrMonteiro():
    """
    Retorna o DataFrame de coeficientes F1 e F2 de Monteiro.
    Diferente de Aoki, Monteiro não aplica equação variável (1 + D/0.8) para pré-moldadas.
    """
    dados = {
        'Tipo de Estaca': [
            'Franki de fuste apiloado',
            'Franki de fuste vibrado',
            'Metálica',
            'Pré-moldada de concreto cravada a percussão',
            'Pré-moldada de concreto cravada por prensagem',
            'Escavada com lama bentonítica',
            'Raiz',
            'Strauss',
            'Hélice contínua'
        ],
        'F1': [2.3, 2.3, 1.75, 2.5, 1.2, 3.5, 2.2, 4.2, 3.0],
        'F2': [3.0, 3.2, 3.5, 3.5, 2.3, 4.5, 2.4, 3.9, 3.8]
    }
    return pd.DataFrame(dados)