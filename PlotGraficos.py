import matplotlib.pyplot as plt
import numpy as np

def plotar_comparativo_metodos(df_aoki, df_decourt, df_teixeira, df_monteiro, df_berberian, df_media, cota_inicio, return_fig=False):
    # Extrair os eixos Y (Cota) - Usando o de Aoki como base já que são idênticos
    cotas = df_aoki['Cota (m)'].tolist()
    
    # Extrair as Cargas Admissíveis de cada método
    carga_aoki = df_aoki['Carga Adm. (kN)'].tolist()
    carga_decourt = df_decourt['Carga Adm. Adotada (kN)'].tolist()
    carga_teixeira = df_teixeira['Carga Adm. (kN)'].tolist()
    carga_monteiro = df_monteiro['Carga Adm. (kN)'].tolist()
    carga_berberian = df_berberian['Carga Adm. (kN)'].tolist()
    
    # Utiliza a média oficial (state.df_media passada como argumento)
    if df_media is not None and 'Carga Adm. (kN)' in df_media.columns:
        carga_media = df_media['Carga Adm. (kN)'].tolist()
    else:
        carga_media = [0] * len(cotas)
            
    # Cria a figura
    fig = plt.figure(figsize=(10, 8))
    
    # Plotar as linhas de cada método
    plt.plot(carga_aoki, cotas, label='Aoki-Velloso (1975)', marker='o', markersize=4, linestyle='-', linewidth=1.5)
    plt.plot(carga_decourt, cotas, label='Décourt-Quaresma (1978)', marker='s', markersize=4, linestyle='-', linewidth=1.5)
    plt.plot(carga_teixeira, cotas, label='Teixeira (1996)', marker='^', markersize=4, linestyle='-', linewidth=1.5)
    plt.plot(carga_monteiro, cotas, label='Monteiro (1997)', marker='d', markersize=4, linestyle='-', linewidth=1.5)
    plt.plot(carga_berberian, cotas, label='Berberian (2015)', marker='x', markersize=4, linestyle='-', linewidth=1.5)
    
    # Plotar a linha da média (destacada)
    if df_media is not None:
        plt.plot(carga_media, cotas, label='Média dos Métodos Selecionados', color='black', marker='*', markersize=8, linestyle='-', linewidth=2.5)
    
    # Configurar eixos X e Y
    todas_cargas = carga_aoki + carga_decourt + carga_teixeira + carga_monteiro + carga_berberian
    max_carga = max(todas_cargas) if todas_cargas else 100
    
    # Eixo X de 50 em 50 (se max_carga for menor que 800) ou 100 em 100
    passo_x = 50 if max_carga <= 800 else 100
    plt.xticks(np.arange(0, max_carga + passo_x, passo_x))
    
    # Eixo Y de 1 em 1 metro
    limite_inf = min(cotas) - 1
    limite_sup = 1
    plt.yticks(np.arange(limite_inf, limite_sup + 1, 1))
    

    # Plotar Linhas Horizontais de Referência
    plt.axhline(y=0, color='gray', linestyle=':', linewidth=1.5, label='N.T (Nível do Terreno)')
    
    # Cota de arrasamento (cota_inicio)
    plt.axhline(y=cota_inicio, color='brown', linestyle='--', linewidth=1.5, label='Cota de Arrasamento')
    
    # Configurações do Gráfico
    plt.title('Comparativo de Capacidade de Carga Admissível', fontsize=14, fontweight='bold')
    plt.xlabel('Carga Admissível (kN)', fontsize=12)
    plt.ylabel('Cotas (m)', fontsize=12)
    
    plt.ylim(limite_inf, limite_sup)
    
    # Grid e Legenda
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(loc='best', fontsize=10, shadow=True, fancybox=True)
    
    # Ajuste de layout e exibição
    plt.tight_layout()
    if return_fig:
        return fig
    else:
        plt.show()
