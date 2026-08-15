import math
import pandas as pd
from TabelaParametrosMonteiro import paramMonteiroTab, fatorCorrMonteiro
from TradutorSolos import tradutor_berberian_para_monteiro, nome_solo_universal
from GeometriaEstacas import calcular_geometria

def searchParamMonteiro(tipoSoloMonteiro):
    df = paramMonteiroTab()
    df2 = df.loc[df['Código'] == tipoSoloMonteiro]
    return [df2['K (kPa)'].tolist()[0], df2['alfa'].tolist()[0]]

def mapear_estaca_monteiro(nome_estaca):
    mapa = {
        'Franki de fuste apiloado': 'Franki de fuste apiloado',
        'Franki de fuste vibrado': 'Franki de fuste vibrado',
        'Metálica': 'Metálica',
        'Pré-moldada de concreto cravada a percussão': 'Pré-moldada de concreto cravada a percussão',
        'Mega': 'Pré-moldada de concreto cravada por prensagem',
        'Escavada mecanicamente sem lama': 'Strauss',
        'Escavada com lama bentonítica': 'Escavada com lama bentonítica',
        'Strauss': 'Strauss',
        'Barrete': 'Escavada com lama bentonítica',
        'Escavada (Barrete)': 'Escavada com lama bentonítica',
        'Solo Cimento': 'Hélice contínua',
        'Estaca Broca': 'Strauss',
        'Raiz': 'Raiz',
        'Estaca Raiz': 'Raiz',
        'Injetada sob altas pressões': 'Raiz',
        'Ômega': 'Hélice contínua',
        'Hélice contínua': 'Hélice contínua'
    }
    return mapa.get(nome_estaca, 'Escavada com lama bentonítica')

def searchCorreMonteiro(tipoEstaca):
    estaca_corrigida = mapear_estaca_monteiro(tipoEstaca)
    df = fatorCorrMonteiro()
    df2 = df.loc[df['Tipo de Estaca'] == estaca_corrigida]
    return [df2['F1'].tolist()[0], df2['F2'].tolist()[0]]

def resultMonteiro(
    listaTipoSolo,
    listaNspt,
    tipoEstaca,
    dimensoes,
    cota_inicio=0,
    forma_estaca=None,
    criterio_ponta_metalica=None
):
    nomes_solo = [nome_solo_universal(cod) for cod in listaTipoSolo]
    listaTipoSoloMonteiro = [tradutor_berberian_para_monteiro(cod) for cod in listaTipoSolo]

    cotas = [-(i + 1) for i in range(len(listaTipoSolo))]
    L_list = [0 if cota >= cota_inicio else abs(cota - cota_inicio) for cota in cotas]

    # Geometria da estaca
    geometria = calcular_geometria(
        tipoEstaca,
        forma_estaca,
        dimensoes,
        criterio_ponta_metalica
    )

    perimetro = geometria['U']
    areaEst = geometria['Ap']
    D_influencia = geometria['D_influencia']
    
    nmed_list, al_list, rl_kpa_list, rl_kn_list, valoresK_list = [], [], [], [], []
    block_start_idx, sum_prev_blocks, temp_block_rl_kn = 0, 0, 0.0
    
    alfa_list, f1_list, f2_list = [], [], []
    np_s_list, np_i_list = [], []
    parcela_s_list, parcela_i_list, kpm_list = [], [], []
    
    valorF1, valorF2 = searchCorreMonteiro(tipoEstaca)
    
    # 1. Cálculo da resistência lateral
    for i in range(len(listaTipoSoloMonteiro)):
        cota_atual = cotas[i]
        param = searchParamMonteiro(listaTipoSoloMonteiro[i])
        
        valoresK_list.append(param[0])
        alfa_list.append(param[1])
        f1_list.append(valorF1)
        f2_list.append(valorF2)
        
        if cota_atual >= cota_inicio:
            nmed_list.append(0.0); al_list.append(0.0); rl_kpa_list.append(0.0); rl_kn_list.append(0.0)
            block_start_idx = i + 1

        else:
            if i > 0 and block_start_idx < i:
                if listaTipoSoloMonteiro[i] != listaTipoSoloMonteiro[i-1]:
                    sum_prev_blocks += temp_block_rl_kn
                    block_start_idx = i 
            
            block_len = i - block_start_idx + 1
            n_sublist = listaNspt[block_start_idx:i+1]
            nmed = round((sum(n_sublist) / block_len) + 1e-9, 1)
            nmed_list.append(nmed)
            
            al = round((perimetro * block_len) + 1e-9, 2)
            al_list.append(al)
            
            valorK, valorAlfa = param[0], param[1]
            
            rl_kpa = round(((valorK * nmed * valorAlfa) / valorF2) + 1e-9, 1)
            rl_kpa_list.append(rl_kpa)
            
            temp_block_rl_kn = round((rl_kpa * al) + 1e-9, 0)
            rl_kn_list.append(sum_prev_blocks + temp_block_rl_kn)

    # 2. Cálculo da resistência de ponta
    rp_kpa_list, rp_kn_list = [], []
    
    camadas_sup = max(1, math.ceil(7 * D_influencia))
    camadas_inf = max(1, math.ceil(3.5 * D_influencia))
    
    for i in range(len(listaTipoSoloMonteiro)):
        if cotas[i] >= cota_inicio:
            rp_kpa_list.append(0.0); rp_kn_list.append(0.0)
            np_s_list.append(0.0); np_i_list.append(0.0)
            parcela_s_list.append(0.0); parcela_i_list.append(0.0); kpm_list.append(0.0)

        else:
            # Parcela superior (7D)
            idx_inicio_sup = i - camadas_sup + 1
            
            if idx_inicio_sup >= 0:
                indices_sup = list(range(idx_inicio_sup, i + 1))
                indices_sup_validos = [j for j in indices_sup if cotas[j] < cota_inicio]
                
                if len(indices_sup_validos) == camadas_sup:
                    Np_S = sum(listaNspt[j] for j in indices_sup_validos) / len(indices_sup_validos)
                    Kp_S = searchParamMonteiro(listaTipoSoloMonteiro[i])[0]
                    parcela_S = Np_S * Kp_S
                    qtd_sup = len(indices_sup_validos)
                else:
                    Np_S, Kp_S, parcela_S, qtd_sup = 0.0, 0.0, 0.0, 0
            else:
                Np_S, Kp_S, parcela_S, qtd_sup = 0.0, 0.0, 0.0, 0
            
            # Parcela inferior (3,5D)
            indices_inf = list(range(i + 1, i + 1 + camadas_inf))
            
            if len(indices_inf) == camadas_inf and max(indices_inf) < len(listaNspt):
                Np_I = sum(listaNspt[j] for j in indices_inf) / len(indices_inf)
                Kp_I = searchParamMonteiro(listaTipoSoloMonteiro[i + 1])[0]
                parcela_I = Np_I * Kp_I
                qtd_inf = len(indices_inf)
            else:
                Np_I, Kp_I, parcela_I, qtd_inf = 0.0, 0.0, 0.0, 0
            
            total_camadas_validas = qtd_sup + qtd_inf
            
            if total_camadas_validas > 0:
                KP_M = ((qtd_sup * parcela_S) + (qtd_inf * parcela_I)) / total_camadas_validas
            else:
                KP_M = 0.0
            
            np_s_list.append(round(Np_S, 2))
            np_i_list.append(round(Np_I, 2))
            parcela_s_list.append(round(parcela_S, 1))
            parcela_i_list.append(round(parcela_I, 1))
            kpm_list.append(round(KP_M, 1))
            
            rp_kpa = round((KP_M / valorF1) + 1e-9, 1)
            rp_kpa_list.append(rp_kpa)
            rp_kn_list.append(round((rp_kpa * areaEst) + 1e-9, 0))

    # 3. Resultado final
    resistencia_total = [
        0 if cotas[i] >= cota_inicio else round((rl_kn_list[i] + rp_kn_list[i]) + 1e-9, 0)
        for i in range(len(listaTipoSoloMonteiro))
    ]

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
        'Rl (kN)': rl_kn_list, 
        'R. Total (kN)': resistencia_total,
        'Carga Adm. (kN)': carga_adm,
        'Tipo de Solo': nomes_solo
    })

    dfResult['Rl (kN)'] = dfResult['Rl (kN)'].astype(int)
    dfResult['Rp (kN)'] = dfResult['Rp (kN)'].astype(int)
    dfResult['R. Total (kN)'] = dfResult['R. Total (kN)'].astype(int)
    dfResult['Carga Adm. (kN)'] = dfResult['Carga Adm. (kN)'].astype(int)

    return dfResult