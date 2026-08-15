import pandas as pd
import math

def dimensionar_pilares_metodo(df_metodo, lista_pilares, cota_inicio):
    """
    Dimensiona os pilares para um dataframe de método específico.
    df_metodo deve conter 'Cota (m)' e a coluna da carga admissível de projeto.
    Para métodos normais, é 'Carga Adm. (kN)'.
    Para Décourt, é 'Carga Adm. Adotada (kN)'.
    """
    
    # Identificar a coluna de capacidade de carga correta
    coluna_carga = 'Carga Adm. Adotada (kN)' if 'Carga Adm. Adotada (kN)' in df_metodo.columns else 'Carga Adm. (kN)'
    
    # Extrair cotas e cargas, garantindo que pegaremos apenas as cotas cuja carga é > 0
    dados_validos = df_metodo[df_metodo[coluna_carga] > 0].copy()
    if dados_validos.empty:
        return pd.DataFrame()
        
    pa_max = dados_validos[coluna_carga].max()
    
    resultados = []
    
    for pilar in lista_pilares:
        nome_pilar = pilar['Pilar']
        carga_total = pilar['Carga (kN)']
        
        # 1. Quantidade de estacas
        # Arredonda para cima: Carga total / Capacidade máxima do método
        qtd_estacas = math.ceil(carga_total / pa_max) if pa_max > 0 else 1
        
        # Se por acaso der 0 (carga 0), ajusta para 1 estaca no mínimo
        qtd_estacas = max(1, qtd_estacas)
        
        # 2. Carga por estaca
        carga_por_estaca = carga_total / qtd_estacas
        
        # 3. Descobrir a cota e o comprimento
        # Varre os dados de cima para baixo
        cota_escolhida = None
        for index, row in dados_validos.iterrows():
            if row[coluna_carga] >= carga_por_estaca:
                cota_escolhida = row['Cota (m)']
                break
                
        # Se não achou nenhuma cota que aguente (ex: arredondamento), assume a última (profundidade máxima)
        if cota_escolhida is None:
            cota_escolhida = dados_validos['Cota (m)'].iloc[-1]
            
        comprimento = abs(cota_escolhida - cota_inicio)
        profundidade = abs(cota_escolhida)
        
        resultados.append({
            'Pilar': nome_pilar,
            'Carga Pilar (kN)': carga_total,
            'Qtd. Estacas': qtd_estacas,
            'Comprimento Estaca (m)': comprimento,
            'Profundidade (m)': profundidade
        })
        
    df_resultados = pd.DataFrame(resultados)
    return df_resultados



def gerar_df_media_metodos(dfs_dict: dict):
    """
    Gera um DataFrame com a média das cargas admissíveis para cada cota.

    Parâmetros
    ----------
    dfs_dict : dict
        Dicionário {chave_metodo: DataFrame} com os métodos participantes.
        Chaves válidas: 'aoki', 'decourt', 'teixeira', 'monteiro', 'berberian'.
        Aceita de 2 a 5 entradas.

    Retorna
    -------
    pd.DataFrame com colunas ['Cota (m)', 'Carga Adm. (kN)'].
    Retorna None se dict vazio ou com apenas 1 método.

    Regras preservadas (inalteradas em relação à versão anterior):
    - Média calculada COTA A COTA.
    - Apenas valores > 0 entram na média de cada cota.
    - Arredondamento: int(round(media + 1e-9, 0)).
    """
    # Coluna de carga admissível correta por método
    COL_CARGA = {
        "aoki":      "Carga Adm. (kN)",
        "decourt":   "Carga Adm. Adotada (kN)",
        "teixeira":  "Carga Adm. (kN)",
        "monteiro":  "Carga Adm. (kN)",
        "berberian": "Carga Adm. (kN)",
    }

    if len(dfs_dict) < 2:
        return None  # média não definida para 0 ou 1 método

    # Usa as cotas do primeiro DataFrame disponível como referência
    df_ref = next(iter(dfs_dict.values()))
    cotas = df_ref["Cota (m)"].tolist()
    n_cotas = len(cotas)

    # Extrai listas de carga para cada método participante
    listas_carga = []
    for chave, df in dfs_dict.items():
        col = COL_CARGA.get(chave, "Carga Adm. (kN)")
        if col not in df.columns:
            continue
        listas_carga.append(df[col].tolist())

    if len(listas_carga) < 2:
        return None

    carga_media = []
    for i in range(n_cotas):
        valores_cota = [lst[i] for lst in listas_carga]
        valores_validos = [v for v in valores_cota if v > 0]
        if valores_validos:
            media = sum(valores_validos) / len(valores_validos)
            # Preserva exatamente o arredondamento já utilizado no projeto
            carga_media.append(int(round(media + 1e-9, 0)))
        else:
            carga_media.append(0)

    return pd.DataFrame({
        "Cota (m)":        cotas,
        "Carga Adm. (kN)": carga_media,
    })
