import os
import sys

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

tipoEstaca = 'Escavada mecanicamente sem lama'
D = {"diametro": 0.25}
forma_estaca = 'circular'
cota_inicio = -1
linha_agua = None
obra_em_solo_sfl = False

listaNspt =     [0, 1.8, 3, 4, 8, 6.5, 9.5, 10, 12.5, 13, 19, 14.5, 17.5]
listaTipoSolo = [31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31, 31]

lista_pilares = [
    {'Pilar': 1, 'Carga (kN)': 30},
    {'Pilar': 2, 'Carga (kN)': 53},
    {'Pilar': 3, 'Carga (kN)': 73},
    {'Pilar': 4, 'Carga (kN)': 92},
    {'Pilar': 5, 'Carga (kN)': 83},
]

from FuncCapacidaCargaAoki import resultAoki
from FuncCapacidadeCargaTeixeira import resultTeixeira
from FuncCapacidadeCargaBerberian import resultBerberian
from FuncCapacidadeCargaDecourt import resultDecourt
from FuncCapacidadeCargaMonteiro import resultMonteiro
from DimensionamentoPilares import dimensionar_pilares_metodo, gerar_df_media_metodos
from CalculoRecalque import calcular_recalque_pilares

print('=== TESTE DE VALIDACAO ===')

df_aoki = resultAoki(listaTipoSolo, listaNspt, tipoEstaca, D, cota_inicio, forma_estaca=forma_estaca)
df_decourt = resultDecourt(listaTipoSolo, listaNspt, tipoEstaca, D, cota_inicio, forma_estaca=forma_estaca)
df_teixeira = resultTeixeira(listaTipoSolo, listaNspt, tipoEstaca, D, cota_inicio=cota_inicio, solo_sfl=obra_em_solo_sfl, forma_estaca=forma_estaca)
df_monteiro = resultMonteiro(listaTipoSolo, listaNspt, tipoEstaca, D, cota_inicio, forma_estaca=forma_estaca)
df_berberian = resultBerberian(listaTipoSolo, listaNspt, tipoEstaca, D, cota_inicio, forma_estaca=forma_estaca)

print('--- Carga Adm. maxima por metodo ---')
aoki_max = df_aoki['Carga Adm. (kN)'].max()
dec_max  = df_decourt['Carga Adm. Adotada (kN)'].max()
tei_max  = df_teixeira['Carga Adm. (kN)'].max()
mon_max  = df_monteiro['Carga Adm. (kN)'].max()
ber_max  = df_berberian['Carga Adm. (kN)'].max()

print(f'  Aoki-Velloso:     {aoki_max}')
print(f'  Decourt-Quaresma: {dec_max}')
print(f'  Teixeira:         {tei_max}')
print(f'  Monteiro:         {mon_max}')
print(f'  Berberian:        {ber_max}')

df_media = gerar_df_media_metodos({
    "aoki":      df_aoki,
    "decourt":   df_decourt,
    "teixeira":  df_teixeira,
    "monteiro":  df_monteiro,
    "berberian": df_berberian,
})
print(f'  Media:            {df_media["Carga Adm. (kN)"].max()}')

print('')
print('--- Dimensionamento (Aoki) ---')
df_dim = dimensionar_pilares_metodo(df_aoki, lista_pilares, cota_inicio)
print(df_dim.to_string(index=False))

print('')
print('--- Recalque ---')
df_rec = calcular_recalque_pilares(
    df_aoki=df_aoki,
    df_dimensionamento=df_dim,
    tipoEstaca=tipoEstaca,
    dimensoes=D,
    linha_agua=linha_agua,
    forma_estaca=forma_estaca,
    cota_inicio=cota_inicio
)
print(df_rec.to_string(index=False))

print('')

# --- ASSERTS DE REGRESSÃO ---
assert df_media["Carga Adm. (kN)"].max() == 121.0, "Falha na Media"
assert df_aoki["Carga Adm. (kN)"].max() == 90.0, "Falha Aoki"
assert df_decourt["Carga Adm. Adotada (kN)"].max() == 121.0, "Falha Decourt"
assert df_teixeira["Carga Adm. (kN)"].max() == 233.0, "Falha Teixeira"
assert df_monteiro["Carga Adm. (kN)"].max() == 149, "Falha Monteiro Max"
assert df_berberian["Carga Adm. (kN)"].max() == 76, "Falha Berberian Max"

assert df_dim.loc[df_dim['Pilar'] == 1, 'Profundidade (m)'].iloc[0] == 6, "Falha Dimensionamento Pilar 1"
assert df_dim.loc[df_dim['Pilar'] == 4, 'Comprimento Estaca (m)'].iloc[0] == 7, "Falha Dimensionamento Pilar 4"

assert df_rec.loc[df_rec['Pilar'] == 1, 'Recalque Total (mm)'].iloc[0] == 4.4, "Falha Recalque Pilar 1"
assert df_rec.loc[df_rec['Pilar'] == 5, 'Recalque Total (mm)'].iloc[0] == 1.0, "Falha Recalque Pilar 5"

# Regressão numérica — caso padrão
import math
from GeometriaEstacas import calcular_geometria

# Proteger Geometria
geom_circ = calcular_geometria('Escavada mecanicamente sem lama', 'circular', {'diametro': 0.25})
assert math.isclose(geom_circ['Ap'], math.pi * 0.25**2 / 4), "Falha Geometria Circular Ap"
assert math.isclose(geom_circ['U'], math.pi * 0.25), "Falha Geometria Circular U"

geom_quad = calcular_geometria('Pré-moldada de concreto cravada a percussão', 'quadrada', {'lado': 0.30})
assert math.isclose(geom_quad['Ap'], 0.09), "Falha Geometria Quadrada Ap"
assert math.isclose(geom_quad['U'], 1.20), "Falha Geometria Quadrada U"

# Checkpoints Aoki
def chk_aoki(cota, l, rp, rl, rtot, adm):
    row = df_aoki.loc[df_aoki['Cota (m)'] == cota].iloc[0]
    assert row['L (m)'] == l
    assert row['Rp (kN)'] == rp
    assert row['Rl Acumulado (kN)'] == rl
    assert row['R. Total (kN)'] == rtot
    assert row['Carga Adm. (kN)'] == adm

chk_aoki(-2, 1, 11, 2, 13, 7)
chk_aoki(-3, 2, 14, 5, 19, 10)
chk_aoki(-6, 5, 34, 26, 60, 30)
chk_aoki(-10, 9, 68, 78, 146, 73)
chk_aoki(-12, 11, 63, 116, 179, 90)
chk_aoki(-13, 12, 0, 136, 136, 68)

# Checkpoints Demais Metodos (Raso: -2, Intermediario: -6, Profundo: -13)
def chk_metodo(df, cota, rtot, adm, col_adm='Carga Adm. (kN)'):
    row = df.loc[df['Cota (m)'] == cota].iloc[0]
    assert row['R. Total (kN)'] == rtot
    assert row[col_adm] == adm

# Decourt
chk_metodo(df_decourt, -2, 15, 8, 'Carga Adm. Adotada (kN)')
chk_metodo(df_decourt, -6, 123, 54, 'Carga Adm. Adotada (kN)')
chk_metodo(df_decourt, -13, 311, 78, 'Carga Adm. Adotada (kN)')

# Teixeira
chk_metodo(df_teixeira, -2, 16, 8)
chk_metodo(df_teixeira, -6, 113, 57)
chk_metodo(df_teixeira, -13, 466, 233)

# Monteiro
chk_metodo(df_monteiro, -2, 13, 7)
chk_metodo(df_monteiro, -6, 73, 37)
chk_metodo(df_monteiro, -13, 298, 149)

# Berberian
chk_metodo(df_berberian, -2, 0, 0)
chk_metodo(df_berberian, -6, 30, 15)
chk_metodo(df_berberian, -13, 151, 76)

# ==========================================
# TESTES DE PROTEÇÃO CONTRA REGRESSÕES (HETEROGÊNEOS E DECIMAIS)
# ==========================================
nspt_het = [0, 1.8, 3, 4, 8, 6.5, 9.5, 10, 12.5, 13, 19, 14.5, 17.5]
solos_het = [1, 1, 1, 1, 15, 15, 15, 15, 31, 31, 31, 31, 31]

# 1. Proteção de detector dinâmico Berberian (sem mascaramento Qp_max)
df_berb_dec = resultBerberian(
    [31]*7, [0, 1.8, 3, 4, 8, 6.5, 9.5], 
    'Pré-moldada de concreto cravada a percussão', 
    {'diametro': 0.25}, cota_inicio=-1, forma_estaca='circular'
)
# Se falhar cota -4 com 112, significa que o detector bugou voltando a usar casa=0
assert df_berb_dec.loc[df_berb_dec['Cota (m)'] == -4, 'R. Total (kN)'].iloc[0] == 114, "Regressao Berberian Decimal"
assert df_berb_dec.loc[df_berb_dec['Cota (m)'] == -6, 'R. Total (kN)'].iloc[0] == 50, "Regressao Berberian Decimal"

# 2. Proteção de blocos Monteiro (Transição de solos)
df_mont_het = resultMonteiro(
    solos_het, nspt_het, 'Escavada mecanicamente sem lama', 
    {'diametro': 0.25}, cota_inicio=-1, forma_estaca='circular'
)
# Cota imediatamente antes da mudança (Silte Arenoso)
assert df_mont_het.loc[df_mont_het['Cota (m)'] == -8, 'R. Total (kN)'].iloc[0] == 181, "Regressao Monteiro Het. Cota -8"
# Cota na mudança (Interface Silte Arenoso para Argila Siltosa)
assert df_mont_het.loc[df_mont_het['Cota (m)'] == -9, 'R. Total (kN)'].iloc[0] == 192, "Regressao Monteiro Het. Cota -9"
# Cota após mudança
assert df_mont_het.loc[df_mont_het['Cota (m)'] == -10, 'R. Total (kN)'].iloc[0] == 229, "Regressao Monteiro Het. Cota -10"

# 3. Proteção de blocos Berberian (Transição de solos)
df_berb_het = resultBerberian(
    solos_het, nspt_het, 'Escavada mecanicamente sem lama', 
    {'diametro': 0.25}, cota_inicio=-1, forma_estaca='circular'
)
assert df_berb_het.loc[df_berb_het['Cota (m)'] == -5, 'R. Total (kN)'].iloc[0] == 24, "Regressao Berberian Het. Bloco 2"
assert df_berb_het.loc[df_berb_het['Cota (m)'] == -10, 'R. Total (kN)'].iloc[0] == 127, "Regressao Berberian Het. Bloco 3"

print('=== TODOS OS CALCULOS OK ===')
