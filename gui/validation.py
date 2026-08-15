import math
from typing import Optional

class ValidationError(ValueError):
    pass

def parse_float(valor: str) -> float:
    """
    Converte string para float.
    - Remove espaços
    - Aceita ',' ou '.'
    - Rejeita string vazia, texto não numérico, NaN e infinitos.
    """
    if not isinstance(valor, str):
        valor = str(valor)
    
    val_limpo = valor.strip()
    if not val_limpo:
        raise ValidationError("O campo não pode estar vazio.")
        
    # Prevenção contra separadores de milhar (ambiguidade multi-separador)
    qtd_sep = val_limpo.count('.') + val_limpo.count(',')
    if qtd_sep > 1:
        raise ValidationError("Não utilize separador de milhar. Use apenas uma vírgula ou ponto para decimal.")
            
    val_limpo = val_limpo.replace(',', '.')
    
    try:
        f = float(val_limpo)
    except ValueError:
        raise ValidationError("O valor informado não é um número válido.")
        
    if not math.isfinite(f):
        raise ValidationError("O valor não pode ser infinito ou NaN.")
        
    return f

def validar_cota_arrasamento(valor: str) -> int:
    """
    Cota de arrasamento deve ser inteira e negativa.
    """
    try:
        f = parse_float(valor)
    except ValidationError:
        raise ValidationError("Cota de arrasamento inválida.\nInforme um valor numérico.")

    if f >= 0:
        raise ValidationError("Cota de arrasamento inválida.\nInforme um valor inteiro negativo, como -1, -2 ou -3.")
        
    if not f.is_integer():
        raise ValidationError("Cota de arrasamento inválida.\nInforme um valor inteiro negativo, como -1, -2 ou -3.")
        
    return int(f)

import decimal

def validar_dimensao_estaca(valor: str, nome_campo: str) -> float:
    val_limpo = str(valor).strip()
    if not val_limpo:
        raise ValidationError("O campo não pode estar vazio.")
    
    qtd_sep = val_limpo.count('.') + val_limpo.count(',')
    if qtd_sep > 1:
        raise ValidationError("Não utilize separador de milhar. Use apenas uma vírgula ou ponto para decimal.")
        
    val_limpo = val_limpo.replace(',', '.')
    
    try:
        d = decimal.Decimal(val_limpo)
    except decimal.InvalidOperation:
        raise ValidationError(f"{nome_campo} inválido.\nInforme um valor numérico.")
        
    if d <= 0:
        raise ValidationError(f"{nome_campo} inválido.\nInforme um valor maior que zero, em metros.")
        
    d_norm = d.normalize()
    if d_norm.as_tuple().exponent < -2:
        raise ValidationError(f"{nome_campo} inválido.\nInforme no máximo 2 casas decimais.\nExemplos válidos: 0,25 ou 0.30.")
        
    return float(d)

def validar_diametro(valor: str) -> float:
    return validar_dimensao_estaca(valor, "Diâmetro")

def validar_lado(valor: str) -> float:
    return validar_dimensao_estaca(valor, "Lado")

def validar_nspt(valor: str, camada_idx: int) -> float:
    val_limpo = str(valor).strip()
    if not val_limpo:
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    qtd_sep = val_limpo.count('.') + val_limpo.count(',')
    if qtd_sep > 1:
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    val_limpo = val_limpo.replace(',', '.')
    
    try:
        d = decimal.Decimal(val_limpo)
    except decimal.InvalidOperation:
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    if not d.is_finite():
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    if d < 0:
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    d_norm = d.normalize()
    if d_norm.as_tuple().exponent < -1:
        raise ValidationError(f"NSPT inválido na camada {camada_idx}.\nInforme um valor maior ou igual a zero com no máximo uma casa decimal.\nExemplos válidos: 6 ou 6,5.")
        
    return float(d)

def validar_na(valor: str) -> Optional[int]:
    val_limpo = str(valor).strip()
    if not val_limpo:
        return None
        
    qtd_sep = val_limpo.count('.') + val_limpo.count(',')
    if qtd_sep > 1:
        raise ValidationError("Não utilize separador de milhar. Use apenas uma vírgula ou ponto para decimal.")
        
    val_limpo = val_limpo.replace(',', '.')
    
    try:
        f = float(val_limpo)
    except ValueError:
        raise ValidationError("Nível d'água inválido.\nInforme uma cota inteira negativa (ex: -5) ou deixe vazio.")
        
    if f >= 0:
        raise ValidationError("Nível d'água inválido.\nA cota deve ser estritamente negativa (abaixo do nível do terreno).")
        
    if not f.is_integer():
        raise ValidationError("Nível d'água inválido.\nA cota deve ser um número inteiro negativo (ex: -5).")
    
    return int(f)

def validar_carga(valor: str, pilar_id: str) -> float:
    val_limpo = str(valor).strip()
    qtd_sep = val_limpo.count('.') + val_limpo.count(',')
    
    if qtd_sep == 1:
        sep = '.' if '.' in val_limpo else ','
        partes = val_limpo.split(sep)
        inteiro = partes[0].lstrip('-')
        casas = partes[1]
        
        if len(casas) == 3 and 1 <= len(inteiro) <= 3 and inteiro != "0" and not all(c == '0' for c in inteiro):
            raise ValidationError("Carga inválida.\nO valor informado é ambíguo.\nNão utilize separador de milhar.\nPara mil quilonewtons, informe 1000.\nPara valor decimal, informe o valor sem formatação de milhar.")
            
    try:
        f = parse_float(valor)
    except ValidationError:
        raise ValidationError(f"Carga inválida para o pilar {pilar_id}.\nInforme um valor numérico maior que zero.")
        
    if f <= 0:
        raise ValidationError(f"Carga inválida para o pilar {pilar_id}.\nInforme um valor numérico maior que zero.")
    return f

def validar_cota_vs_sondagem(cota_arrasamento: int, camadas: list):
    """
    A cota de arrasamento é válida somente se existir pelo menos uma camada
    investigada ABAIXO dela.
    """
    if not camadas:
        return # Nada para validar ainda
        
    tem_camada_abaixo = any(cam["cota"] < cota_arrasamento for cam in camadas)
    
    if not tem_camada_abaixo:
        cota_final = min(cam["cota"] for cam in camadas)
        raise ValidationError(f"Cota de arrasamento incompatível com a sondagem.\nA sondagem cadastrada se estende até a cota {cota_final} m.\nInforme uma cota de arrasamento acima desse limite (ex: se termina em -10, use -9).")

def validar_na_vs_sondagem(na_cota: int, camadas: list):
    """
    O N.A. deve pertencer à sondagem.
    A cota informada para o N.A. deve corresponder a uma cota/camada existente na sondagem.
    """
    if not camadas or na_cota is None:
        return
        
    cotas_existentes = {cam["cota"] for cam in camadas}
    if na_cota not in cotas_existentes:
        cota_final = min(cotas_existentes)
        raise ValidationError(f"Cota do N.A. incompatível com a sondagem.\nA cota {na_cota} não existe no perfil investigado (limite: {cota_final} m).")
