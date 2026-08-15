import math


REGRAS_GEOMETRIA = {
    'Franki de fuste apiloado': {
        'secoes': ['franki'],
        'secao_padrao': 'franki'
    },

    'Franki de fuste vibrado': {
        'secoes': ['franki'],
        'secao_padrao': 'franki'
    },

    'Metálica': {
        'secoes': ['perfil_i', 'perfil_h'],
        'secao_padrao': 'perfil_h'
    },

    'Pré-moldada de concreto cravada a percussão': {
        'secoes': ['circular', 'quadrada'],
        'secao_padrao': 'circular'
    },

    'Mega': {
        'secoes': ['circular', 'quadrada'],
        'secao_padrao': 'circular'
    },

    'Escavada mecanicamente sem lama': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Strauss': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Barrete': {
        'secoes': ['retangular'],
        'secao_padrao': 'retangular'
    },

    'Solo Cimento': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Estaca Broca': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Escavada com lama bentonítica': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Hélice contínua': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Ômega': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Raiz': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    },

    'Injetada sob altas pressões': {
        'secoes': ['circular'],
        'secao_padrao': 'circular'
    }
}


NOMES_SECOES = {
    'circular': 'Circular',
    'quadrada': 'Quadrada',
    'retangular': 'Retangular',
    'franki': 'Circular com base alargada',
    'perfil_i': 'Perfil I',
    'perfil_h': 'Perfil H'
}


CAMPOS_SECOES = {
    'circular': [
        ('diametro', 'Diâmetro [m]')
    ],

    'quadrada': [
        ('lado', 'Lado [m]')
    ],

    'retangular': [
        ('largura', 'Largura [m]'),
        ('comprimento_secao', 'Comprimento da seção [m]')
    ],

    'franki': [
        ('diametro', 'Diâmetro do fuste [m]')
    ],

    'perfil_i': [
        ('altura_secao', 'Altura da seção [m]'),
        ('largura_mesa', 'Largura da mesa [m]'),
        ('esp_alma', 'Espessura da alma [m]'),
        ('esp_mesa', 'Espessura da mesa [m]')
    ],

    'perfil_h': [
        ('altura_secao', 'Altura da seção [m]'),
        ('largura_mesa', 'Largura da mesa [m]'),
        ('esp_alma', 'Espessura da alma [m]'),
        ('esp_mesa', 'Espessura da mesa [m]')
    ]
}


TABELA_FRANKI = [
    (0.35, 0.18),
    (0.40, 0.27),
    (0.45, 0.36),
    (0.52, 0.45),
    (0.60, 0.60)
]


def secoes_permitidas(tipoEstaca):
    if tipoEstaca not in REGRAS_GEOMETRIA:
        raise ValueError(f"Tipo de estaca não reconhecido: {tipoEstaca}")

    return REGRAS_GEOMETRIA[tipoEstaca]['secoes']


def secao_padrao(tipoEstaca):
    if tipoEstaca not in REGRAS_GEOMETRIA:
        raise ValueError(f"Tipo de estaca não reconhecido: {tipoEstaca}")

    return REGRAS_GEOMETRIA[tipoEstaca]['secao_padrao']


def campos_secao(forma_estaca):
    if forma_estaca not in CAMPOS_SECOES:
        raise ValueError(f"Forma de seção não reconhecida: {forma_estaca}")

    return CAMPOS_SECOES[forma_estaca]


def validar_dimensao(valor, nome):
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nome} deve ser um valor numérico.")

    if valor <= 0:
        raise ValueError(f"{nome} deve ser maior que zero.")

    return valor


def dimensao_equivalente(area, perimetro):
    return 4 * area / perimetro


def interpolar_volume_franki(D):
    D = validar_dimensao(D, 'Diâmetro da estaca Franki')

    D_min = TABELA_FRANKI[0][0]
    D_max = TABELA_FRANKI[-1][0]

    if D < D_min or D > D_max:
        raise ValueError(
            f"Para a estaca Franki, informe um diâmetro entre "
            f"{D_min:.2f} m e {D_max:.2f} m."
        )

    for diametro, volume in TABELA_FRANKI:
        if math.isclose(D, diametro, abs_tol=1e-10):
            return volume

    for i in range(len(TABELA_FRANKI) - 1):
        D1, V1 = TABELA_FRANKI[i]
        D2, V2 = TABELA_FRANKI[i + 1]

        if D1 <= D <= D2:
            V = V1 + (V2 - V1) * (D - D1) / (D2 - D1)
            return V

    raise ValueError("Não foi possível determinar o volume da base Franki.")


def area_ponta_franki(V):
    V = validar_dimensao(V, 'Volume da base Franki')

    return math.pi * ((3 * V) / (4 * math.pi)) ** (2 / 3)


def calcular_geometria(
    tipoEstaca,
    forma_estaca,
    dimensoes,
    criterio_ponta_metalica=None
):
    if tipoEstaca not in REGRAS_GEOMETRIA:
        raise ValueError(f"Tipo de estaca não reconhecido: {tipoEstaca}")

    if forma_estaca is None:
        forma_estaca = secao_padrao(tipoEstaca)

    forma_estaca = forma_estaca.lower()

    permitidas = secoes_permitidas(tipoEstaca)

    if forma_estaca not in permitidas:
        nomes = [NOMES_SECOES[s] for s in permitidas]

        raise ValueError(
            f"A seção '{forma_estaca}' não é permitida para "
            f"'{tipoEstaca}'. Seções permitidas: {', '.join(nomes)}."
        )

    if forma_estaca == 'circular':
        D = validar_dimensao(
            dimensoes.get('diametro'),
            'Diâmetro'
        )

        Ap = math.pi * D ** 2 / 4
        U = math.pi * D
        Ae = Ap

        return {
            'Ap': Ap,
            'U': U,
            'Ae': Ae,
            'D_nominal': D,
            'D_influencia': D,
            'largura_secao': D,
            'comprimento_secao': D,
            'volume_base': None,
            'criterio_ponta': 'seção circular'
        }

    if forma_estaca == 'quadrada':
        lado = validar_dimensao(
            dimensoes.get('lado'),
            'Lado'
        )

        Ap = lado ** 2
        U = 4 * lado
        Ae = Ap

        return {
            'Ap': Ap,
            'U': U,
            'Ae': Ae,
            'D_nominal': lado,
            'D_influencia': lado,
            'largura_secao': lado,
            'comprimento_secao': lado,
            'volume_base': None,
            'criterio_ponta': 'seção quadrada'
        }

    if forma_estaca == 'retangular':
        largura = validar_dimensao(
            dimensoes.get('largura'),
            'Largura'
        )

        comprimento = validar_dimensao(
            dimensoes.get('comprimento_secao'),
            'Comprimento da seção'
        )

        Ap = largura * comprimento
        U = 2 * (largura + comprimento)
        Ae = Ap

        D_influencia = dimensao_equivalente(Ap, U)

        return {
            'Ap': Ap,
            'U': U,
            'Ae': Ae,
            'D_nominal': None,
            'D_influencia': D_influencia,
            'largura_secao': largura,
            'comprimento_secao': comprimento,
            'volume_base': None,
            'criterio_ponta': 'seção retangular'
        }

    if forma_estaca == 'franki':
        D = validar_dimensao(
            dimensoes.get('diametro'),
            'Diâmetro do fuste'
        )

        V = interpolar_volume_franki(D)

        Ap = area_ponta_franki(V)
        U = math.pi * D
        Ae = math.pi * D ** 2 / 4

        return {
            'Ap': Ap,
            'U': U,
            'Ae': Ae,
            'D_nominal': D,
            'D_influencia': D,
            'largura_secao': D,
            'comprimento_secao': D,
            'volume_base': V,
            'criterio_ponta': 'base alargada Franki'
        }

    if forma_estaca in ['perfil_i', 'perfil_h']:
        altura = validar_dimensao(
            dimensoes.get('altura_secao'),
            'Altura da seção'
        )

        largura_mesa = validar_dimensao(
            dimensoes.get('largura_mesa'),
            'Largura da mesa'
        )

        esp_alma = validar_dimensao(
            dimensoes.get('esp_alma'),
            'Espessura da alma'
        )

        esp_mesa = validar_dimensao(
            dimensoes.get('esp_mesa'),
            'Espessura da mesa'
        )

        if 2 * esp_mesa >= altura:
            raise ValueError(
                "A soma das espessuras das mesas deve ser menor "
                "que a altura da seção."
            )

        if esp_alma >= largura_mesa:
            raise ValueError(
                "A espessura da alma deve ser menor que a largura da mesa."
            )

        area_real = (
            2 * largura_mesa * esp_mesa
            + (altura - 2 * esp_mesa) * esp_alma
        )

        perimetro_perfil = (
            4 * largura_mesa
            + 2 * altura
            - 2 * esp_alma
        )

        area_envolvente = largura_mesa * altura
        perimetro_envolvente = 2 * (largura_mesa + altura)

        if criterio_ponta_metalica == 'area_real':
            Ap = area_real
            criterio = 'área real do perfil'

        elif criterio_ponta_metalica == 'retangulo_envolvente':
            Ap = area_envolvente
            criterio = 'retângulo envolvente'

        else:
            raise ValueError(
                "Para estaca metálica, informe o critério da ponta como "
                "'area_real' ou 'retangulo_envolvente'."
            )

        U = perimetro_perfil
        Ae = area_real

        D_influencia = dimensao_equivalente(
            area_envolvente,
            perimetro_envolvente
        )

        return {
            'Ap': Ap,
            'U': U,
            'Ae': Ae,
            'D_nominal': None,
            'D_influencia': D_influencia,
            'largura_secao': largura_mesa,
            'comprimento_secao': altura,
            'volume_base': None,
            'criterio_ponta': criterio,
            'area_real_perfil': area_real,
            'area_envolvente': area_envolvente,
            'perimetro_perfil': perimetro_perfil,
            'perimetro_envolvente': perimetro_envolvente
        }

    raise ValueError(
        f"A geometria '{forma_estaca}' ainda não foi implementada."
    )


def obter_D_nominal(geometria, metodo='Método'):
    D = geometria['D_nominal']

    if D is None:
        raise ValueError(
            f"{metodo}: a seção selecionada não possui um único "
            f"diâmetro ou lado nominal."
        )

    return D


def obter_D_influencia(geometria):
    return geometria['D_influencia']