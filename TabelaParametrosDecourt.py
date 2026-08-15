def paramDecourtAlfaBeta():
    """
    Dicionário contendo os valores de (alfa, beta) para as estacas de substituição.
    As estacas de Deslocamento (Pré-moldada, Metálica, Franki, Mega) têm alfa=1 e beta=1 
    e serão tratadas na função principal.
    """
    return {
        'Escavada em geral': {
            'Argilas': (0.85, 0.80),
            'Solos intermediários': (0.60, 0.65),
            'Areias': (0.50, 0.50)
        },
        'Escavada (bentonita)': {
            'Argilas': (0.85, 0.90),
            'Solos intermediários': (0.60, 0.75),
            'Areias': (0.50, 0.60)
        },
        'Hélice contínua': {
            'Argilas': (0.30, 1.00),
            'Solos intermediários': (0.30, 1.00),
            'Areias': (0.30, 1.00)
        },
        'Raiz': {
            'Argilas': (0.85, 1.50),
            'Solos intermediários': (0.60, 1.50),
            'Areias': (0.50, 1.50)
        },
        'Injetada sob altas pressões': {
            'Argilas': (1.00, 3.00),
            'Solos intermediários': (1.00, 3.00),
            'Areias': (1.00, 3.00)
        }
    }

def paramDecourtC():
    """
    Dicionário contendo os valores do parâmetro C (em kPa) em função do tipo de solo.
    """
    return {
        'Areia': 400,
        'Silte arenoso': 250,
        'Silte argiloso': 200,
        'Argila': 120
    }