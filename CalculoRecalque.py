import math
import pandas as pd
from GeometriaEstacas import calcular_geometria, secao_padrao

def param_estaca_recalque(tipoEstaca):
    tipo = tipoEstaca.lower()
    
    ec_gpa = 20
    alfa = 4
    
    # Módulo de Elasticidade (Ec)
    if any(x in tipo for x in ['pré-moldada', 'pre-moldada', 'mega']):
        ec_gpa = 30
    elif any(x in tipo for x in ['hélice', 'helice', 'ômega', 'omega', 'raiz', 'injetada', 'franki', 'barrete', 'com lama']):
        ec_gpa = 21
    elif any(x in tipo for x in ['escavada', 'strauss', 'broca']):
        ec_gpa = 18
    elif 'solo cimento' in tipo or 'solo-cimento' in tipo:
        ec_gpa = 5
    elif 'metálica' in tipo or 'metalica' in tipo:
        ec_gpa = 210

    # Fator de descompressão do solo (alfa)
    if any(x in tipo for x in ['pré-moldada', 'pre-moldada', 'franki', 'mega', 'ômega', 'omega']):
        alfa = 6
    elif any(x in tipo for x in ['hélice', 'helice', 'metálica', 'metalica', 'raiz', 'injetada']):
        alfa = 4
    elif any(x in tipo for x in ['escavada', 'barrete', 'strauss', 'broca', 'solo cimento', 'solo-cimento', 'com lama']):
        alfa = 3
        
    return ec_gpa, alfa

def get_peso_especifico_str(estado_fisico, saturado=False):
    if estado_fisico == '-':
        return 0

    # Granulares
    if estado_fisico in ["Fofa", "Pouco compacta"]:
        gamma = 19 if saturado else 16
    elif estado_fisico == "Medianamente compacta":
        gamma = 20 if saturado else 17
    elif estado_fisico in ["Compacta", "Muito compacta"]:
        gamma = 21 if saturado else 18

    # Coesivos
    elif estado_fisico == "Muito mole":
        gamma = 13
    elif estado_fisico == "Mole":
        gamma = 15
    elif estado_fisico == "Média":
        gamma = 17
    elif estado_fisico == "Rija":
        gamma = 19
    elif estado_fisico in ["Muito rija", "Dura"]:
        gamma = 21
    else:
        gamma = 18
        
    return (gamma - 10) if saturado else gamma

def tensao_propagada(P, h, forma_estaca, largura, comprimento, D_influencia):
    if forma_estaca in ['circular', 'franki']:
        return (4 * P) / (math.pi * (D_influencia + h) ** 2)
    
    return P / ((largura + h) * (comprimento + h))

def calcular_recalque_pilares(
    df_aoki,
    df_dimensionamento,
    tipoEstaca,
    dimensoes,
    linha_agua=None,
    forma_estaca=None,
    cota_inicio=-1,
    criterio_ponta_metalica=None
):
    resultados = []
    
    ec_gpa, alfa = param_estaca_recalque(tipoEstaca)
    ec_kpa = ec_gpa * 1e6

    if forma_estaca is None:
        forma_estaca = secao_padrao(tipoEstaca)

    geometria = calcular_geometria(
        tipoEstaca,
        forma_estaca,
        dimensoes,
        criterio_ponta_metalica
    )

    area_estaca = geometria['Ae']
    D_influencia = geometria['D_influencia']
    largura_secao = geometria['largura_secao']
    comprimento_secao = geometria['comprimento_secao']
    
    cotas = df_aoki['Cota (m)'].tolist()
    nspt_list = df_aoki['Nspt'].tolist()
    k_kpa_list = df_aoki['K (kPa)'].tolist()
    
    # 1. Tensão geostática no meio de cada camada
    sigma_v0_mid = []
    current_sigma_top = 0.0
    
    for i in range(len(cotas)):
        cota_bottom = cotas[i]
        cota_top = 0 if i == 0 else cotas[i-1]
        thickness = abs(cota_top - cota_bottom)
        
        cota_mid = (cota_top + cota_bottom) / 2.0
        
        if linha_agua is not None:
            saturado = cota_mid <= linha_agua
        else:
            saturado = False
        
        estado = df_aoki['Estado Físico'].iloc[i]
        gamma_efetivo = get_peso_especifico_str(estado, saturado)
        
        delta_sigma_half = gamma_efetivo * (thickness / 2.0)
        sigma_mid = current_sigma_top + delta_sigma_half
        sigma_v0_mid.append(round(sigma_mid + 1e-9, 2))
        
        current_sigma_top += gamma_efetivo * thickness
        
    # 2. Recalque de cada pilar dimensionado
    idx_inicio = abs(int(cota_inicio))
    
    for idx, row in df_dimensionamento.iterrows():
        nome_pilar = row['Pilar']
        carga_pilar = row['Carga Pilar (kN)']
        qtd_estacas = row['Qtd. Estacas']
        cota_apoio = -row['Profundidade (m)']
        
        if pd.isna(cota_apoio) or qtd_estacas == 0:
            continue
            
        P_estaca = carga_pilar / qtd_estacas
        idx_apoio = abs(int(cota_apoio)) - 1
        
        # Encurtamento elástico
        rho_e_mm = 0.0
        carga_atual = P_estaca
        
        for i in range(idx_inicio, idx_apoio + 1):
            delta_Rl = df_aoki['ΔRl (kN)'].iloc[i]
            delta_Rl = max(0, delta_Rl)
            
            P_topo = carga_atual
            P_base = P_topo - delta_Rl

            if P_base < 0:
                P_base = 0
            
            P_medio = (P_topo + P_base) / 2.0
            L_trecho = 1.0
            
            rho_e_m = (P_medio * L_trecho) / (area_estaca * ec_kpa)
            rho_e_mm += rho_e_m * 1000.0
            
            carga_atual = P_base

            if carga_atual <= 0:
                break
                
        Pp_chega_na_ponta = max(0, carga_atual)
        
        # Recalque do solo
        rho_s_mm = 0.0
        
        for i in range(idx_apoio + 1, len(cotas)):
            cota_camada_centro = ((0 if i == 0 else cotas[i-1]) + cotas[i]) / 2.0
            
            # Efeito de grupo
            vizinhos = max(0, qtd_estacas - 1)
            r_vizinho = 3.0 * D_influencia
            
            # Carga de ponta
            h_p = abs(cota_apoio - cota_camada_centro)

            delta_sigma_p = tensao_propagada(
                Pp_chega_na_ponta,
                h_p,
                forma_estaca,
                largura_secao,
                comprimento_secao,
                D_influencia
            )
                
            if vizinhos > 0 and h_p > 0:
                delta_sigma_p += (
                    vizinhos * (3 * Pp_chega_na_ponta * h_p ** 3)
                    / (2 * math.pi * ((r_vizinho ** 2 + h_p ** 2) ** 2.5))
                )
                
            # Carga lateral
            delta_sigma_l = 0.0
            carga_rem_lat = P_estaca
            
            for j in range(idx_inicio, idx_apoio + 1):
                delta_Rl_j = df_aoki['ΔRl (kN)'].iloc[j]
                delta_Rl_j = max(0, delta_Rl_j)
                
                atrito_mobilizado = min(delta_Rl_j, carga_rem_lat)
                carga_rem_lat -= atrito_mobilizado
                
                if atrito_mobilizado > 0:
                    cota_centroide_j = ((0 if j == 0 else cotas[j-1]) + cotas[j]) / 2.0
                    h_j = abs(cota_centroide_j - cota_camada_centro)

                    delta_sigma_l += tensao_propagada(
                        atrito_mobilizado,
                        h_j,
                        forma_estaca,
                        largura_secao,
                        comprimento_secao,
                        D_influencia
                    )
                        
                    if vizinhos > 0 and h_j > 0:
                        delta_sigma_l += (
                            vizinhos * (3 * atrito_mobilizado * h_j ** 3)
                            / (2 * math.pi * ((r_vizinho ** 2 + h_j ** 2) ** 2.5))
                        )
                        
            delta_sigma_total = delta_sigma_p + delta_sigma_l
            
            if delta_sigma_total < 1e-3:
                break
                
            es_kpa = alfa * k_kpa_list[i] * nspt_list[i]

            if es_kpa <= 0:
                es_kpa = 1e-9
                
            sigma_0_camada = sigma_v0_mid[i]
            estado_camada = df_aoki['Estado Físico'].iloc[i]
            
            n_janbu = 0.5 if estado_camada in [
                "Fofa",
                "Pouco compacta",
                "Medianamente compacta",
                "Compacta",
                "Muito compacta"
            ] else 0.0
                
            if sigma_0_camada > 0:
                E_si = es_kpa * ((sigma_0_camada + delta_sigma_total) / sigma_0_camada) ** n_janbu
            else:
                E_si = es_kpa
                
            if E_si > 0:
                rho_s_m = (delta_sigma_total / E_si) * 1.0
                rho_s_mm += rho_s_m * 1000.0
                
        resultados.append({
            'Pilar': nome_pilar,
            'Carga Estaca (kN)': round(P_estaca + 1e-9, 1),
            'Cota Base (m)': cota_apoio,
            'rho_e (mm)': round(rho_e_mm + 1e-9, 1),
            'rho_s (mm)': round(rho_s_mm + 1e-9, 1),
            'Recalque Total (mm)': round(rho_e_mm + rho_s_mm + 1e-9, 1)
        })
        
    df_recalque = pd.DataFrame(resultados)
    return df_recalque