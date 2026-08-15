import pandas as pd
from TabelaParametrosBerberian import paramBerberianEstacas, paramBerberianSolos
from GeometriaEstacas import calcular_geometria

def mapear_estaca_berberian(nome_estaca_main):
    mapa = {
        # Estacas de deslocamento
        'Franki de fuste apiloado': 'Franki de fuste apiloado',
        'Franki de fuste vibrado': 'Franki de fuste vibrado',
        'Metálica': 'Metálica',
        'Pré-moldada de concreto cravada a percussão': 'Pré-moldada de concreto cravada a percussão',
        'Mega': 'Mega',

        # Estacas escavadas em geral
        'Escavada mecanicamente sem lama': 'Escavada mecanicamente sem lama',
        'Strauss': 'Strauss',
        'Barrete': 'Escavada (Barrete)',
        'Solo Cimento': 'Solo. Cimento Plástico e Estaca Broca',
        'Estaca Broca': 'Solo. Cimento Plástico e Estaca Broca',

        # Estacas escavadas com bentonita
        'Escavada com lama bentonítica': 'Escavada com lama bentonítica',

        # Hélice contínua e Ômega
        'Ômega': 'Hélice contínua e Ômega',
        'Hélice contínua': 'Hélice contínua e Ômega',

        # Raiz e injetadas
        'Raiz': 'Raiz',
        'Estaca Raiz': 'Raiz',
        'Injetada sob altas pressões': 'Raiz'
    }
    
    return mapa.get(nome_estaca_main, 'Hélice contínua e Ômega')

def resultBerberian(
    listaTipoSolo,
    listaNspt,
    tipoEstaca,
    dimensoes,
    cota_inicio=0,
    forma_estaca=None,
    criterio_ponta_metalica=None
):
    tipoEstaca_Berberian = mapear_estaca_berberian(tipoEstaca)

    # Verifica se é estaca do tipo escavada/não-deslocamento
    estacas_deslocamento = [
        'Franki de fuste apiloado',
        'Franki de fuste vibrado',
        'Metálica',
        'Pré-moldada de concreto cravada a percussão',
        'Mega'
    ]
    is_estaca_escavada = tipoEstaca not in estacas_deslocamento

    # 1. Identificador dinâmico de casas decimais
    casas_decimais = 0
    for n in listaNspt:
        str_n = str(n)
        if '.' in str_n:
            partes = str_n.split('.')
            if partes[1] != '0':
                casas = max(casas_decimais, len(partes[1]))

    # 2. Configurações iniciais
    cotas = [-(i + 1) for i in range(len(listaTipoSolo))]
    L_list = [0 if c >= cota_inicio else abs(c - cota_inicio) for c in cotas]
    idx_inicio = next((i for i, c in enumerate(cotas) if c < cota_inicio), len(cotas))

    # Geometria da estaca
    geometria = calcular_geometria(
        tipoEstaca,
        forma_estaca,
        dimensoes,
        criterio_ponta_metalica
    )

    perimetro = geometria['U']
    area_ponta = geometria['Ap']
    D_nominal = geometria['D_nominal']
    
    # 3. Busca fatores de escala (Ep, El)
    dict_estacas = paramBerberianEstacas()
    ep_raw = dict_estacas[tipoEstaca_Berberian]['Ep']
    el_raw = dict_estacas[tipoEstaca_Berberian]['El']
    
    if isinstance(ep_raw, str):
        if D_nominal is None:
            raise ValueError(
                "O método de Berberian necessita do diâmetro ou lado "
                "nominal para esta estaca."
            )

        ep_val = round(1.0 + (1.25 * D_nominal), 2)
        el_val = round(1.75 + (2.19 * D_nominal), 2)

    else:
        ep_val = float(ep_raw)
        el_val = float(el_raw)

    # 4. Busca parâmetros do solo
    dict_solos = paramBerberianSolos()
    nomes_solo, kpdb_list, kldb_list = [], [], []
    
    for cod in listaTipoSolo:
        if cod in dict_solos:
            nomes_solo.append(dict_solos[cod][0])
            kpdb_list.append(dict_solos[cod][1])
            kldb_list.append(dict_solos[cod][2])
        else:
            nomes_solo.append("Desconhecido")
            kpdb_list.append(0.0)
            kldb_list.append(0.0)

    np_medio_list, nl_medio_list = [], []
    qp_kpa_list, qp_kn_list = [], []
    ql_kpa_list, ql_kn_list = [], []

    # 5. Processamento por cota
    for i in range(len(listaTipoSolo)):
        if cotas[i] >= cota_inicio:
            np_medio_list.append(0 if casas_decimais == 0 else 0.0)
            nl_medio_list.append(0 if casas_decimais == 0 else 0.0)
            qp_kpa_list.append(0.0)
            qp_kn_list.append(0)
            ql_kpa_list.append(0.0)
            ql_kn_list.append(0)

        else:
            # Cálculo do Np médio e resistência de ponta
            if i + 2 < len(listaNspt):
                val_i = kpdb_list[i] * listaNspt[i]
                val_ip1 = kpdb_list[i+1] * listaNspt[i+1]
                val_ip2 = kpdb_list[i+2] * listaNspt[i+2]
                
                media_kpdb_np = (val_i + val_ip1 + val_ip2) / 3.0
                
                if casas_decimais == 0:
                    np_medio = int(round(media_kpdb_np + 1e-9, 0))
                else:
                    np_medio = round(media_kpdb_np + 1e-9, casas_decimais)
                    
                qp_kpa = round(((9.81 * np_medio) / ep_val) + 1e-9, 1)
                qp_kn = int(round((qp_kpa * area_ponta) + 1e-9, 0))

            else:
                np_medio = 0 if casas_decimais == 0 else 0.0
                qp_kpa = 0.0
                qp_kn = 0

            np_medio_list.append(np_medio)

            # Cálculo do Nl médio e atrito lateral acumulado
            end_fuste_idx = i - 1
            
            if end_fuste_idx < idx_inicio:
                nl_medio_list.append(0 if casas_decimais == 0 else 0.0)
                ql_kpa_list.append(0.0)
                ql_kn = 0

            else:
                total_ql_kn = 0
                last_nl = 0
                last_ql_kpa = 0.0
                
                blocks = []
                current_block = [idx_inicio]
                
                for j in range(idx_inicio + 1, end_fuste_idx + 1):
                    if listaTipoSolo[j] == listaTipoSolo[j-1]:
                        current_block.append(j)
                    else:
                        blocks.append(current_block)
                        current_block = [j]

                blocks.append(current_block)
                
                for block in blocks:
                    nspt_block = [listaNspt[k] for k in block]
                    media_nl = sum(nspt_block) / len(block)
                    
                    if casas_decimais == 0:
                        nl_b = int(round(media_nl + 1e-9, 0))
                    else:
                        nl_b = round(media_nl + 1e-9, casas_decimais)
                    
                    kl_b = kldb_list[block[0]]
                    ql_kpa_b = round(((kl_b * 9.81 * nl_b) / el_val) + 1e-9, 1)
                    
                    L_block = len(block) * 1.0
                    ql_kn_b = int(round((ql_kpa_b * perimetro * L_block) + 1e-9, 0))
                    
                    total_ql_kn += ql_kn_b
                    last_nl = nl_b
                    last_ql_kpa = ql_kpa_b
                
                nl_medio_list.append(last_nl)
                ql_kpa_list.append(last_ql_kpa)
                ql_kn = total_ql_kn

            # Restrição para estacas escavadas
            if is_estaca_escavada:
                qp_max_kn = int(round((0.20 * ql_kn) + 1e-9, 0))

                if qp_kn > qp_max_kn:
                    qp_kn = qp_max_kn
                    qp_kpa = round((qp_kn / area_ponta) + 1e-9, 1) if area_ponta > 0 else 0.0

            qp_kpa_list.append(qp_kpa)
            qp_kn_list.append(qp_kn)
            ql_kn_list.append(ql_kn)

    # 6. Resistência total
    resistencia_total = [
        0 if cotas[i] >= cota_inicio else int(ql_kn_list[i] + qp_kn_list[i])
        for i in range(len(listaTipoSolo))
    ]

    carga_adm = [int(round((r / 2) + 1e-9, 0)) for r in resistencia_total]

    resultCompleto = {
        'Cota (m)': cotas,
        'L (m)': L_list,
        'Nspt': listaNspt,
        'KpDB (t/m²)': kpdb_list,
        'KlDB (t/m²)': kldb_list,
        'Ep': [ep_val] * len(cotas),
        'El': [el_val] * len(cotas),
        'qp (kPa)': qp_kpa_list,
        'Qp (kN)': qp_kn_list,
        'ql (kPa)': ql_kpa_list,
        'Ql (kN)': ql_kn_list,
        'R. Total (kN)': resistencia_total,
        'Carga Adm. (kN)': carga_adm,
        'Tipo de Solo': nomes_solo
    }

    return pd.DataFrame(resultCompleto)