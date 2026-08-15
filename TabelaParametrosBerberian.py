def paramBerberianSolos():
    """
    Retorna o dicionário com mapeamento completo de solos segundo Berberian.
    Formato: código: ['Nome_do_solo', KpDB (t/m²), KlDB (t/m²)]
    Valores 100% revisados e fiéis às tabelas originais do método.
    """
    return {
        # --- CÓDIGOS DE 1 A 11 (AREIAS) ---
        1:  ['Areia (Sand)', 100.0, 1.40],
        2:  ['Areia Mto Pouco Siltosa', 80.0, 1.28],
        3:  ['Areia Pouco Siltosa', 84.0, 1.50],
        4:  ['Areia Siltosa', 80.0, 1.60],
        5:  ['Areia Muito Siltosa', 75.0, 1.64],
        6:  ['Areia Silto Argilosa', 70.0, 1.68],
        7:  ['Areia Mto Pouco Argilosa', 60.0, 1.68],
        8:  ['Areia Pouco Argilosa', 58.0, 1.62],
        9:  ['Areia Argilosa', 60.0, 1.80],
        10: ['Areia Muito Argilosa', 50.0, 1.50],
        11: ['Areia Argilo Siltosa', 50.0, 1.40],

        # --- CÓDIGOS DE 12 A 22 (SILTES) ---
        12: ['Silte (Mó)', 40.0, 1.20],
        13: ['Silte Muito Pouco Arenoso', 45.0, 1.26],
        14: ['Silte Pouco Arenoso', 50.0, 1.24],
        15: ['Silte Arenoso', 55.0, 1.20],
        16: ['Silte Muito Arenoso', 60.0, 1.20],
        17: ['Silte Areno Argiloso', 45.0, 1.26],
        18: ['Silte Muito Pouco Argiloso', 38.0, 1.14],
        19: ['Silte Pouco Argiloso', 30.0, 0.96],
        20: ['Silte Argiloso', 23.0, 0.78],
        21: ['Silte Muito Argiloso', 20.0, 0.72],
        22: ['Silte Argilo Arenoso', 23.0, 0.74],

        # --- CÓDIGOS DE 23 A 34 (ARGILAS E TURFA) ---
        23: ['Argila (Clay)', 40.0, 1.20],
        24: ['Argila Mto Pouco Arenosa', 50.0, 1.20],
        25: ['Argila Pouco Arenosa', 60.0, 1.08],
        26: ['Argila Arenosa', 70.0, 0.84],
        27: ['Argila Muito Arenosa', 80.0, 0.56],
        28: ['Argila Areno Siltosa', 60.0, 0.84],
        29: ['Argila Mto Pouco Siltosa', 40.0, 1.04],
        30: ['Argila Pouco Siltosa', 42.0, 0.96],
        31: ['Argila Siltosa', 44.0, 0.88],
        32: ['Argila Muito Siltosa', 46.0, 0.78],
        33: ['Argila Silto Arenosa', 66.0, 0.98],
        34: ['Turfa', 0.0, 0.0]
    }

def paramBerberianEstacas():
    """
    Retorna o dicionário de fatores de escala do método Berberian.
    Os valores representam FPP (Ep) e FPL (El) extraídos rigorosamente da tabela.
    Nota: Quando "dinamico" for retornado, a função principal fará 
    o cálculo conforme a equação do diâmetro para a estaca Mega.
    """
    return {
        'Hélice contínua e Ômega': {'Ep': 3.00, 'El': 3.80},
        'Pré-moldada de concreto cravada a percussão': {'Ep': 'dinamico', 'El': 'dinamico'},
        'Franki de fuste apiloado': {'Ep': 2.40, 'El': 4.00},
        'Franki de fuste vibrado': {'Ep': 2.40, 'El': 4.20},
        'Metálica': {'Ep': 2.00, 'El': 3.20},
        'Escavada mecanicamente sem lama': {'Ep': 4.00, 'El': 4.60},
        'Mega': {'Ep': 'dinamico', 'El': 'dinamico'},
        'Escavada com lama bentonítica': {'Ep': 3.50, 'El': 5.00},
        'Escavada (Barrete)': {'Ep': 4.50, 'El': 5.00},
        'Raiz': {'Ep': 2.80, 'El': 2.40},
        'Strauss': {'Ep': 4.00, 'El': 3.00},
        'Solo. Cimento Plástico e Estaca Broca': {'Ep': 3.00, 'El': 5.00}
    }