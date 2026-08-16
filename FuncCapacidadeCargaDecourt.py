import pandas as pd
from TabelaParametrosDecourt import paramDecourtAlfaBeta, paramDecourtC
from TradutorSolos import nome_solo_universal
from GeometriaEstacas import calcular_geometria

def mapear_solo_decourt(codigo_berberian):
    if 1 <= codigo_berberian <= 11: return 'Areia', 'Areias'
    elif 12 <= codigo_berberian <= 17: return 'Silte arenoso', 'Solos intermediários'
    elif 18 <= codigo_berberian <= 22: return 'Silte argiloso', 'Solos intermediários'
    else: return 'Argila', 'Argilas'

def mapear_estaca_decourt(nome_estaca):
    mapa = {
        'Franki de fuste apiloado': 'Deslocamento', 'Franki de fuste vibrado': 'Deslocamento',
        'Metálica': 'Deslocamento',
        'Pré-moldada de concreto cravada a percussão': 'Deslocamento',
        'Mega': 'Deslocamento',
        'Escavada mecanicamente sem lama': 'Escavada em geral',
        'Strauss': 'Escavada em geral', 'Barrete': 'Escavada em geral', 'Escavada (Barrete)': 'Escavada em geral',
        'Solo Cimento': 'Escavada em geral',
        'Estaca Broca': 'Escavada em geral',
        'Escavada com lama bentonítica': 'Escavada (bentonita)',
        'Ômega': 'Hélice contínua', 'Hélice contínua': 'Hélice contínua',
        'Raiz': 'Raiz', 'Estaca Raiz': 'Raiz',
        'Injetada sob altas pressões': 'Injetada sob altas pressões'
    }
    return mapa.get(nome_estaca, 'Escavada em geral')

def resultDecourt(
    listaTipoSolo,
    listaNspt,
    tipoEstaca,
    dimensoes,
    cota_inicio=0,
    forma_estaca=None,
    criterio_ponta_metalica=None
):
    # 1. Identificador Dinâmico de Casas Decimais com base na listaNspt
    casas_decimais = 0
    for n in listaNspt:
        str_n = str(n)
        if '.' in str_n:
            partes = str_n.split('.')
            if partes[1] != '0':
                casas = len(partes[1])
                if casas > casas_decimais:
                    casas_decimais = casas

    tipoEstaca_Decourt = mapear_estaca_decourt(tipoEstaca)
    dict_alfa_beta, dict_c = paramDecourtAlfaBeta(), paramDecourtC()

    lim_min, lim_max = (3, 15) if any(x in tipoEstaca for x in ['Strauss', 'Broca']) else (3, 50)
    forcar_limite = lambda n: max(lim_min, min(lim_max, n))

    # Geometria da estaca
    geometria = calcular_geometria(
        tipoEstaca,
        forma_estaca,
        dimensoes,
        criterio_ponta_metalica
    )

    U = geometria['U']
    Ab = geometria['Ap']

    cotas = [-(i + 1) for i in range(len(listaTipoSolo))]
    L_list = [0 if c >= cota_inicio else abs(c - cota_inicio) for c in cotas]
    idx_inicio = next((i for i, c in enumerate(cotas) if c < cota_inicio), len(cotas))

    c_list, alfa_list, beta_list, nl_medio_list, np_list = [], [], [], [], []
    rb_kpa_list, rb_kn_list, rl_kpa_list, rl_kn_list = [], [], [], []
    nomes_solo = [nome_solo_universal(cod) for cod in listaTipoSolo]

    for i in range(len(listaTipoSolo)):
        if cotas[i] >= cota_inicio:
            c_list.append(0); alfa_list.append(0.0); beta_list.append(0.0)
            nl_medio_list.append(0); np_list.append(0)
            rb_kpa_list.append(0.0); rb_kn_list.append(0)
            rl_kpa_list.append(0.0); rl_kn_list.append(0)

        else:
            nome_base, classe_solo = mapear_solo_decourt(listaTipoSolo[i])
            C_val = dict_c[nome_base]
            c_list.append(C_val)

            alfa_val, beta_val = (1.0, 1.0) if tipoEstaca_Decourt == 'Deslocamento' else dict_alfa_beta[tipoEstaca_Decourt][classe_solo]
            alfa_list.append(alfa_val); beta_list.append(beta_val)

            # Ponta (Nb)
            if i + 2 < len(listaNspt):
                media_np = sum(listaNspt[i:i+3]) / 3.0

                if casas_decimais == 0:
                    Nb = int(round(media_np + 1e-9, 0))
                else:
                    Nb = round(media_np + 1e-9, casas_decimais)

                np_list.append(Nb)

                rb_kpa = round((C_val * Nb) + 1e-9, 1)
                rb_kpa_list.append(rb_kpa)

                rb_kn = int(round((alfa_val * rb_kpa * Ab) + 1e-9, 0))
                rb_kn_list.append(rb_kn)

            else:
                np_list.append(0)
                rb_kpa_list.append(0.0)
                rb_kn_list.append(0)

            # Lateral (Nl)
            ns_validos = [forcar_limite(listaNspt[k]) for k in range(idx_inicio, i)]

            if ns_validos:
                media_nl = sum(ns_validos) / len(ns_validos)

                if casas_decimais == 0:
                    Nl_medio = int(round(media_nl + 1e-9, 0))
                else:
                    Nl_medio = round(media_nl + 1e-9, casas_decimais)

                rl_kpa = round(10.0 * ((Nl_medio / 3.0) + 1.0) + 1e-9, 1)
                Rl_kn = round((rl_kpa * beta_val * (U * L_list[i])) + 1e-9, 0)

            else:
                Nl_medio, rl_kpa, Rl_kn = 0, 0.0, 0.0

            nl_medio_list.append(Nl_medio)
            rl_kpa_list.append(rl_kpa)
            rl_kn_list.append(int(Rl_kn))

    resistencia_total = [
        0 if cotas[i] >= cota_inicio else int(rl_kn_list[i] + rb_kn_list[i])
        for i in range(len(listaTipoSolo))
    ]

    criterio_1 = [int(round((r / 2) + 1e-9, 0)) for r in resistencia_total]

    criterio_2 = [
        int(round(((rl_kn_list[i] / 1.3) + (rb_kn_list[i] / 4)) + 1e-9, 0))
        for i in range(len(listaTipoSolo))
    ]

    carga_adm = [
        min(c1, c2) if cotas[i] < cota_inicio else 0
        for i, (c1, c2) in enumerate(zip(criterio_1, criterio_2))
    ]

    return pd.DataFrame({
        'Cota (m)': cotas, 'L (m)': L_list, 'Nspt': listaNspt, 'α': alfa_list, 'β': beta_list,
        'C (kPa)': c_list, 'rb (kPa)': rb_kpa_list,
        'Rb (kN)': rb_kn_list, 'rl (kPa)': rl_kpa_list, 'Rl (kN)': rl_kn_list,
        'R. Total (kN)': resistencia_total,
        'Critério R. Total/2 (kN)': criterio_1,
        'Critério Rl/1,3 + Rp/4 (kN)': criterio_2,
        'Carga Adm. Adotada (kN)': carga_adm,
        'Tipo de Solo': nomes_solo
    })