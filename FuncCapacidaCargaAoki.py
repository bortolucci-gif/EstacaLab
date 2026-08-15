import math
import pandas as pd
from TabelaParametrosAoki import paramAokiTab, fatorCorrAoki
from TradutorSolos import tradutor_berberian_para_aoki, nome_solo_universal
from GeometriaEstacas import calcular_geometria

def searchParamAoki(tipoSoloAoki):
    df = paramAokiTab()
    df2 = df.loc[df['Código'] == tipoSoloAoki]
    return [df2['K (kPa)'].tolist()[0], df2['alfa'].tolist()[0]]

def mapear_estaca_aoki(nome_estaca):
    mapa = {
        # Categoria: Franki
        'Franki de fuste apiloado': 'Franki',
        'Franki de fuste vibrado': 'Franki',
        
        # Categoria: Metálica
        'Metálica': 'Metálica',
        
        # Categoria: Pré-moldada
        'Pré-moldada de concreto cravada a percussão': 'Pré-moldada',
        'Mega': 'Pré-moldada',
        
        # Categoria: Escavada
        'Escavada mecanicamente sem lama': 'Escavada',
        'Strauss': 'Escavada',
        'Barrete': 'Escavada',
        'Escavada (Barrete)': 'Escavada',
        'Escavada com lama bentonítica': 'Escavada',
        'Solo Cimento': 'Escavada',
        'Estaca Broca': 'Escavada',
        
        # Categoria: Raiz, Hélice contínua e Ômega
        'Raiz': 'Raiz, Hélice contínua e Ômega',
        'Estaca Raiz': 'Raiz, Hélice contínua e Ômega',
        'Ômega': 'Raiz, Hélice contínua e Ômega',
        'Hélice contínua': 'Raiz, Hélice contínua e Ômega',
        'Injetada sob altas pressões': 'Raiz, Hélice contínua e Ômega'
    }
    return mapa.get(nome_estaca, 'Escavada')

def searchCorreAoki(tipoEstaca, D_nominal=None):
    estaca_corrigida = mapear_estaca_aoki(tipoEstaca)

    # Apenas a pré-moldada possui F1 e F2 dependentes de D
    if estaca_corrigida == 'Pré-moldada':
        if D_nominal is None:
            raise ValueError(
                "O método de Aoki-Velloso necessita do diâmetro ou lado "
                "nominal para estacas pré-moldadas e Mega."
            )
        D = D_nominal
    else:
        D = 0.0

    df = fatorCorrAoki(D)
    df2 = df.loc[df['Tipo de Estaca'] == estaca_corrigida]
    return [df2['F1'].tolist()[0], df2['F2'].tolist()[0]]

# Mantida temporariamente para compatibilidade com o cálculo de recalque
def propGeomEst(D, forma_estaca='circular'):
    if forma_estaca.lower() == 'quadrada':
        perimetro = round((D * 4) + 1e-9, 2)
        area = round((pow(D, 2)) + 1e-9, 2)
    else:
        perimetro = round((D * math.pi) + 1e-9, 2)
        area = round(((pow(D, 2) * math.pi) / 4) + 1e-9, 2)
    
    return [D, perimetro, area]

def resultAoki(
    listaTipoSolo,
    listaNspt,
    tipoEstaca,
    dimensoes,
    cota_inicio=0,
    forma_estaca=None,
    criterio_ponta_metalica=None
):
    nomes_solo = [nome_solo_universal(cod) for cod in listaTipoSolo]
    listaTipoSoloAoki = [tradutor_berberian_para_aoki(cod) for cod in listaTipoSolo]

    # Geometria da estaca
    geometria = calcular_geometria(
        tipoEstaca,
        forma_estaca,
        dimensoes,
        criterio_ponta_metalica
    )

    perimetro = geometria['U']
    areaEst = geometria['Ap']
    D_nominal = geometria['D_nominal']

    F1, F2 = searchCorreAoki(tipoEstaca, D_nominal)

    estados_fisicos = []
    contagem = 0
    soma_nspt = 0

    for i in range(len(listaTipoSolo)):
        cota_atual = -(i + 1)

        if cota_atual >= cota_inicio:
            estados_fisicos.append('-')
        else:
            contagem += 1
            soma_nspt += listaNspt[i]
            mu_nspt = int(round((soma_nspt / contagem) + 1e-9, 0))
            
            codigo_solo = listaTipoSolo[i]

            # Se for Areia (1-11) ou Silte Arenoso (12-17), usa tabela de Compacidade
            if 1 <= codigo_solo <= 17:
                if mu_nspt < 5:
                    estado = "Fofa"
                elif mu_nspt <= 8:
                    estado = "Pouco compacta"
                elif mu_nspt <= 18:
                    estado = "Medianamente compacta"
                elif mu_nspt <= 40:
                    estado = "Compacta"
                else:
                    estado = "Muito compacta"

            # Se for Silte Argiloso (18-22) ou Argila/Turfa (23-34), usa tabela de Consistência
            else:
                if mu_nspt <= 2:
                    estado = "Muito mole"
                elif mu_nspt <= 5:
                    estado = "Mole"
                elif mu_nspt <= 10:
                    estado = "Média"
                elif mu_nspt <= 19:
                    estado = "Rija"
                elif mu_nspt <= 30:
                    estado = "Muito rija"
                else:
                    estado = "Dura"
            
            estados_fisicos.append(estado)

    cotas = [-(i + 1) for i in range(len(listaTipoSolo))]
    L_list = [0 if cota >= cota_inicio else abs(cota - cota_inicio) for cota in cotas]

    nmed_list, al_list, rl_kpa_list, rl_kn_list, valoresK_list = [], [], [], [], []
    alfa_list, f1_list, f2_list = [], [], []
    block_start_idx, sum_prev_blocks, temp_block_rl_kn = 0, 0, 0.0
    
    for i in range(len(listaTipoSoloAoki)):
        cota_atual = cotas[i]
        param = searchParamAoki(listaTipoSoloAoki[i])

        valoresK_list.append(param[0])
        alfa_list.append(param[1])
        f1_list.append(F1)
        f2_list.append(F2)
        
        if cota_atual >= cota_inicio:
            nmed_list.append(0.0)
            al_list.append(0.0)
            rl_kpa_list.append(0.0)
            rl_kn_list.append(0.0)
            block_start_idx = i + 1

        else:
            if i > 0 and block_start_idx < i:
                if (listaTipoSoloAoki[i] != listaTipoSoloAoki[i-1]) or (estados_fisicos[i] != estados_fisicos[i-1]):
                    sum_prev_blocks += temp_block_rl_kn
                    block_start_idx = i 
            
            block_len = i - block_start_idx + 1
            n_sublist = listaNspt[block_start_idx:i+1]
            nmed = round((sum(n_sublist) / block_len) + 1e-9, 1)
            nmed_list.append(nmed)
            
            al = perimetro * block_len
            al_list.append(round(al + 1e-9, 2))
            
            valorK, valorAlfa = param[0], param[1]
            
            rl_kpa = round(((valorK * nmed * valorAlfa) / F2) + 1e-9, 1)
            rl_kpa_list.append(rl_kpa)
            
            temp_block_rl_kn = round((rl_kpa * al) + 1e-9, 0)
            rl_kn_list.append(sum_prev_blocks + temp_block_rl_kn)

    rp_kpa_list, rp_kn_list = [], []
    
    for i in range(len(listaTipoSoloAoki)):
        if cotas[i] >= cota_inicio or i == len(listaTipoSoloAoki) - 1:
            rp_kpa_list.append(0.0)
            rp_kn_list.append(0.0)

        else:
            param = searchParamAoki(listaTipoSoloAoki[i+1])
            valorK = param[0]
            
            rp_kpa = round(((valorK * listaNspt[i+1]) / F1) + 1e-9, 1)
            rp_kpa_list.append(rp_kpa)
            rp_kn_list.append(round((rp_kpa * areaEst) + 1e-9, 0))

    resistencia_total = [
        0 if cotas[i] >= cota_inicio else round((rl_kn_list[i] + rp_kn_list[i]) + 1e-9, 0)
        for i in range(len(listaTipoSoloAoki))
    ]

    delta_rl_kn_list = [0.0] * len(listaTipoSoloAoki)

    for i in range(len(listaTipoSoloAoki)):
        if cotas[i] < cota_inicio:
            if i > 0 and cotas[i-1] < cota_inicio:
                delta_rl_kn_list[i] = round(rl_kn_list[i] - rl_kn_list[i-1], 2)
            else:
                delta_rl_kn_list[i] = round(rl_kn_list[i], 2)

    carga_adm = [int(round((r / 2) + 1e-9, 0)) for r in resistencia_total]

    dfResult = pd.DataFrame({
        'Cota (m)': cotas,
        'L (m)': L_list,
        'Nspt': listaNspt, 
        'K (kPa)': valoresK_list,
        'α': alfa_list,
        'F1': f1_list,
        'F2': f2_list,
        'rp (kPa)': rp_kpa_list,
        'Rp (kN)': rp_kn_list,
        'rl (kPa)': rl_kpa_list,
        'ΔRl (kN)': delta_rl_kn_list,
        'Rl Acumulado (kN)': rl_kn_list, 
        'R. Total (kN)': resistencia_total,
        'Carga Adm. (kN)': carga_adm,
        'Tipo de Solo': nomes_solo,
        'Estado Físico': estados_fisicos
    })

    dfResult['ΔRl (kN)'] = dfResult['ΔRl (kN)'].astype(int)
    dfResult['Rl Acumulado (kN)'] = dfResult['Rl Acumulado (kN)'].astype(int)
    dfResult['Rp (kN)'] = dfResult['Rp (kN)'].astype(int)
    dfResult['R. Total (kN)'] = dfResult['R. Total (kN)'].astype(int)
    dfResult['Carga Adm. (kN)'] = dfResult['Carga Adm. (kN)'].astype(int)

    return dfResult