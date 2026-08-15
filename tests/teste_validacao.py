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
assert df_media["Carga Adm. (kN)"].max() == 120.0, "Falha na Media"
assert df_aoki["Carga Adm. (kN)"].max() == 90.0, "Falha Aoki"
assert df_decourt["Carga Adm. Adotada (kN)"].max() == 121.0, "Falha Decourt"
assert df_teixeira["Carga Adm. (kN)"].max() == 233.0, "Falha Teixeira"
assert df_monteiro["Carga Adm. (kN)"].max() == 149.0, "Falha Monteiro"
assert df_berberian["Carga Adm. (kN)"].max() == 73.0, "Falha Berberian"

assert df_dim.loc[df_dim['Pilar'] == 1, 'Profundidade (m)'].iloc[0] == 6, "Falha Dimensionamento Pilar 1"
assert df_dim.loc[df_dim['Pilar'] == 4, 'Comprimento Estaca (m)'].iloc[0] == 7, "Falha Dimensionamento Pilar 4"

assert df_rec.loc[df_rec['Pilar'] == 1, 'Recalque Total (mm)'].iloc[0] == 4.4, "Falha Recalque Pilar 1"
assert df_rec.loc[df_rec['Pilar'] == 5, 'Recalque Total (mm)'].iloc[0] == 1.0, "Falha Recalque Pilar 5"

print('=== TODOS OS CALCULOS OK ===')
