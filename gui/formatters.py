import math

def formatar_valor_tabela(nome_coluna: str, valor: any) -> str:
    """
    Mecanismo central de formatação visual do EstacaLab.
    Aplica as regras baseadas na prioridade do nome da grandeza/coluna.
    Retorna apenas a string para ser exibida.
    """
    # 1. Valores Nulos / NaN
    if valor is None:
        return "—"
    if isinstance(valor, float) and math.isnan(valor):
        return "—"

    # Conversão segura para string dependendo do tipo (apenas para não estourar)
    # Se for string, tentamos converter para float, mas caso falhe, devolvemos a própria string.
    val_num = valor
    if isinstance(valor, str):
        try:
            val_num = float(valor.replace(',', '.'))
        except ValueError:
            return valor # Se não for número, retorna como está.

    # Regras por prioridade:
    col = nome_coluna.lower()

    # 2. Qtd. Estacas e Índices inteiros puros
    if "qtd. estacas" in col or "pilar" in col:
        # Pilar geralmente é string (ex: "P1"), então val_num pode ser str ou int
        if isinstance(val_num, (int, float)):
            return f"{int(val_num)}"
        return str(val_num)

    # 3. NSPT (preservar decimais relevantes, sem zeros finais)
    if "nspt" in col:
        # Ex: 15.0 -> 15, 6.5 -> 6,5
        return f"{val_num:g}".replace('.', ',')

    # 4. Porcentagem (Variação / Δ%)
    if "Δ%" in col or "%" in col:
        return f"{val_num:.1f}".replace('.', ',')

    # 5. mm / Recalque
    if "(mm)" in col:
        # A auditoria indicou que Recalque em CalculoRecalque.py usa 1 casa decimal (round(..., 1)).
        return f"{val_num:.1f}".replace('.', ',')

    # 6. kPa
    if "(kpa)" in col:
        # Padrão brasileiro: milhar com ponto, decimal com vírgula
        texto_us = f"{val_num:,.1f}" # ex: "2,450.0"
        return texto_us.replace(',', 'X').replace('.', ',').replace('X', '.')

    # 7. kN (Forças, Cargas, Resistências)
    if "(kn)" in col:
        # Cargas já vêm como int ou float equivalente a int. Formatar com separador de milhar.
        # Ex: 1500.0 -> 1500 -> "1,500" -> "1.500"
        try:
            val_int = int(round(val_num)) # round() p/ previnir floats corrompidos, mas dados já devem estar ok
            # F-string format ',' coloca vírgula nos milhares.
            return f"{val_int:,}".replace(',', '.')
        except (ValueError, TypeError):
            return str(val_num)

    # 8. m² (Áreas)
    if "(m²)" in col:
        texto_us = f"{val_num:,.2f}"
        if texto_us.endswith(".00"):
            texto_us = texto_us[:-3]
        elif texto_us[-1] == "0":
            texto_us = texto_us[:-1]
        return texto_us.replace(',', 'X').replace('.', ',').replace('X', '.')

    # 9. Grandezas dimensionais em Metros (m)
    if "(m)" in col:
        # Especificidades de grandezas dimensionais
        if "diâmetro" in col or "lado" in col or "dimensão" in col:
            return f"{val_num:g}".replace('.', ',')
        
        # Cotas, comprimentos e profundidade são inteiros no modelo discretizado do EstacaLab
        if "cota" in col or "profundidade" in col or "comprimento" in col or "n.a" in col:
            return f"{int(round(val_num))}"

    # 10. Fallback numérico genérico para qualquer float/int não classificado (Conservador)
    if isinstance(val_num, int):
        return str(val_num)
    elif isinstance(val_num, float):
        # Apenas converte para string com vírgula e tenta não ser destrutivo
        return str(val_num).replace('.', ',')
        
    return str(val_num)
