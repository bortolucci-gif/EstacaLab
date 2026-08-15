import math
import pandas as pd
from TabelaParametrosTeixeira import paramTeixeiraAlfaTab, paramTeixeiraBetaTab
from TradutorSolos import tradutor_berberian_para_aoki, tradutor_berberian_para_teixeira, nome_solo_universal
from GeometriaEstacas import calcular_geometria

def mapear_estaca_teixeira(nome_estaca):
    mapa = {
        'Franki de fuste apiloado': 'Tipo Franki', 'Franki de fuste vibrado': 'Tipo Franki',
        'Metálica': 'Pré - moldadas e metálicas',
        'Pré-moldada de concreto cravada a percussão': 'Pré - moldadas e metálicas',
        'Pré-Moldada de concreto cravada a percussão': 'Pré - moldadas e metálicas',
        'Mega': 'Pré - moldadas e metálicas',
        'Escavada mecanicamente sem lama': 'Escavadas a céu aberto',
        'Escavada com lama bentonítica': 'Escavadas a céu aberto',
        'Barrete': 'Escavadas a céu aberto', 'Escavada (Barrete)': 'Escavadas a céu aberto',
        'Strauss': 'Escavadas a céu aberto', 'Solo Cimento': 'Escavadas a céu aberto', 'Estaca Broca': 'Escavadas a céu aberto',
        'Ômega': 'Escavadas a céu aberto', 'Omega': 'Escavadas a céu aberto', 'Hélice contínua': 'Escavadas a céu aberto',
        'Raiz': 'Estaca Raiz', 'Estaca Raiz': 'Estaca Raiz',
        'Injetada sob altas pressões': 'Estaca Raiz'
    }
    return mapa.get(nome_estaca, 'Escavadas a céu aberto')

def resultTeixeira(
    listaTipoSolo,
    listaNspt,
    tipoEstaca,
    dimensoes,
    forma_estaca=None,
    cota_inicio=0,
    solo_sfl=False,
    criterio_ponta_metalica=None
):
    nomes_solo = [nome_solo_universal(cod) for cod in listaTipoSolo]
    solos_teixeira = [tradutor_berberian_para_teixeira(cod) for cod in listaTipoSolo]
    solos_aoki = [tradutor_berberian_para_aoki(cod) for cod in listaTipoSolo]

    tipoEstaca_Teixeira = mapear_estaca_teixeira(tipoEstaca)
    cotas = [-(i + 1) for i in range(len(listaTipoSolo))]
    L_list = [0 if c >= cota_inicio else abs(c - cota_inicio) for c in cotas]

    df_alfa, df_beta = paramTeixeiraAlfaTab(), paramTeixeiraBetaTab()
    
    # Busca segura do valor de Beta
    df_beta_filtered = df_beta.loc[df_beta['Tipo de Estaca'] == tipoEstaca_Teixeira, 'beta (kPa)']
    beta_val = df_beta_filtered.values[0] if not df_beta_filtered.empty else 0.0

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
    
    nl_medio_list, ql_kpa_list, ql_kn_list, soma_ql_acum = [], [], [], 0
    idx_inicio = next((i for i, c in enumerate(cotas) if c < cota_inicio), len(cotas))

    for i in range(len(listaTipoSolo)):
        if cotas[i] >= cota_inicio:
            nl_medio_list.append(0); ql_kpa_list.append(0.0); ql_kn_list.append(0.0)

        else:
            np_sublist = listaNspt[idx_inicio:i + 1]
            nl_medio = int(round((sum(np_sublist) / len(np_sublist)) + 1e-9, 0))
            nl_medio_list.append(nl_medio)
            
            comp_camada = L_list[i] - (L_list[i-1] if i > 0 else 0)
            area_camada = round(perimetro * comp_camada + 1e-9, 2)
            
            if solo_sfl and str(solos_aoki[i]).startswith('3') and listaNspt[i] <= 3 and abs(cotas[i]) <= 25:
                ql_kpa = 25.0
            else:
                ql_kpa = round((beta_val * listaNspt[i]) + 1e-9, 1)
            
            soma_ql_acum += round((ql_kpa * area_camada) + 1e-9, 0)
            ql_kpa_list.append(ql_kpa)
            ql_kn_list.append(soma_ql_acum)

    qp_kpa_list, qp_kn_list, np_medio_list, alfa_list = [], [], [], []

    # Região considerada para o NSPT da ponta
    camadas_acima = max(1, math.ceil(4 * D_influencia))
    camadas_abaixo = max(1, math.ceil(1 * D_influencia))
    
    for i in range(len(listaTipoSolo)):
        if cotas[i] >= cota_inicio:
            qp_kpa_list.append(0.0); qp_kn_list.append(0.0); np_medio_list.append(0); alfa_list.append(0.0)

        else:
            idx_ponta = i
            solo_teixeira_ponta = str(solos_teixeira[idx_ponta]).strip().lower()
            
            # Busca insensível a maiúsculas/minúsculas e espaços
            filtro_alfa = df_alfa[
                df_alfa['Tipo de Solo'].astype(str).str.strip().str.lower() == solo_teixeira_ponta
            ]
            
            if not filtro_alfa.empty and tipoEstaca_Teixeira in filtro_alfa.columns:
                alfa_val = filtro_alfa[tipoEstaca_Teixeira].values[0]

            else:
                filtro_parcial = df_alfa[
                    df_alfa['Tipo de Solo'].astype(str).str.strip().str.lower().apply(
                        lambda x: x in solo_teixeira_ponta or solo_teixeira_ponta in x
                    )
                ]

                if not filtro_parcial.empty and tipoEstaca_Teixeira in filtro_parcial.columns:
                    alfa_val = filtro_parcial[tipoEstaca_Teixeira].values[0]
                else:
                    alfa_val = 0.0
                     
            alfa_list.append(alfa_val)
            
            sub_np = listaNspt[
                max(0, i - camadas_acima + 1):
                min(len(listaNspt), i + camadas_abaixo + 1)
            ]

            np_medio = int(round((sum(sub_np) / len(sub_np)) + 1e-9, 0))
            np_medio_list.append(np_medio)
            
            qp_kpa = round((alfa_val * np_medio) + 1e-9, 1)
            qp_kpa_list.append(qp_kpa)
            qp_kn_list.append(round((qp_kpa * areaEst) + 1e-9, 0))

    resistencia_total = [
        0 if cotas[i] >= cota_inicio else round((ql_kn_list[i] + qp_kn_list[i]) + 1e-9, 0)
        for i in range(len(listaTipoSolo))
    ]

    carga_adm = [int(round((r / 2) + 1e-9, 0)) for r in resistencia_total]

    dfResult = pd.DataFrame({
        'Cota (m)': cotas, 'L (m)': L_list, 'Nspt': listaNspt, 'α (kPa)': alfa_list,
        'β (kPa)': [beta_val if c < cota_inicio else 0 for c in cotas],
        'qp (kPa)': qp_kpa_list, 'Qp (kN)': qp_kn_list,
        'ql (kPa)': ql_kpa_list, 'Ql (kN)': ql_kn_list, 'R. Total (kN)': resistencia_total,
        'Carga Adm. (kN)': carga_adm,
        'Tipo de Solo': nomes_solo
    })

    dfResult['Qp (kN)'] = dfResult['Qp (kN)'].astype(int)
    dfResult['Ql (kN)'] = dfResult['Ql (kN)'].astype(int)
    dfResult['R. Total (kN)'] = dfResult['R. Total (kN)'].astype(int)
    dfResult['Carga Adm. (kN)'] = dfResult['Carga Adm. (kN)'].astype(int)

    return dfResult