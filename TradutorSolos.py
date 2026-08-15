def nome_solo_universal(codigo):
    """
    Retorna o nome EXATO da tabela de Berberian para ser impresso no DataFrame de TODOS os métodos.
    """
    nomes = {
        1: 'Areia', 2: 'Areia Mto Pouco Siltosa', 3: 'Areia Pouco Siltosa', 
        4: 'Areia Siltosa', 5: 'Areia Muito Siltosa', 6: 'Areia Silto Argilosa', 
        7: 'Areia Mto Pouco Argilosa', 8: 'Areia Pouco Argilosa', 9: 'Areia Argilosa', 
        10: 'Areia Muito Argilosa', 11: 'Areia Argilo Siltosa',
        
        12: 'Silte', 13: 'Silte Muito Pouco Arenoso', 14: 'Silte Pouco Arenoso', 
        15: 'Silte Arenoso', 16: 'Silte Muito Arenoso', 17: 'Silte Areno Argiloso', 
        18: 'Silte Muito Pouco Argiloso', 19: 'Silte Pouco Argiloso', 20: 'Silte Argiloso', 
        21: 'Silte Muito Argiloso', 22: 'Silte Argilo Arenoso',
        
        23: 'Argila', 24: 'Argila Mto Pouco Arenosa', 25: 'Argila Pouco Arenosa', 
        26: 'Argila Arenosa', 27: 'Argila Muito Arenosa', 28: 'Argila Areno Siltosa', 
        29: 'Argila Mto Pouco Siltosa', 30: 'Argila Pouco Siltosa', 31: 'Argila Siltosa', 
        32: 'Argila Muito Siltosa', 33: 'Argila Silto Arenosa', 34: 'Turfa'
    }
    return nomes.get(codigo, 'Solo Desconhecido')

def tradutor_berberian_para_decourt(codigo):
    """
    Remaneja os 34 solos do Berberian para as 3 categorias macro do método de Décourt.
    Retorna a Categoria Base e a Classe para buscar o Alfa e Beta.
    """
    if 1 <= codigo <= 11: 
        return 'Areia', 'Areias'
    elif 12 <= codigo <= 22: 
        # Décourt trata Siltes como Solos Intermediários
        return 'Silte arenoso' if codigo <= 17 else 'Silte argiloso', 'Solos intermediários'
    else: 
        return 'Argila', 'Argilas'

def tradutor_berberian_para_aoki(codigo):
    """
    Remaneja os 34 solos de Berberian diretamente para os códigos ESPECÍFICOS da tabela Aoki-Velloso.
    """
    
    # ==========================================
    # GRUPO 1: AREIAS 
    # ==========================================
    if codigo == 1: 
        return 1  # Areia (código 1)
    elif 2 <= codigo <= 5: 
        return 12  # Areia Siltosa (código 12)
    elif codigo == 6:
        return 123 # Areia siltoargilosa (código 123)
    elif 7 <= codigo <= 10: 
        return 13  # Areia Argilosa (código 13)
    elif codigo == 11:
        return 132 # Areia argilossiltosa (código 132)
        
    # ==========================================
    # GRUPO 2: SILTES 
    # ==========================================
    elif codigo == 12: 
        return 2  # Silte (código 2)
    elif 13 <= codigo <= 16: 
        return 21  # Silte Arenoso (código 21)
    elif codigo == 17:
        return 213 # Silte arenoargiloso (código 213)
    elif 18 <= codigo <= 21: 
        return 23  # Silte Argiloso (código 23)
    elif codigo == 22:
        return 231 # Silte argiloarenoso (código 231)
        
    # ==========================================
    # GRUPO 3: ARGILAS E TURFA
    # ==========================================
    elif codigo == 23: 
        return 3  # Argila (código 3)
    elif 24 <= codigo <= 27: 
        return 31  # Argila Arenosa (código 31)
    elif codigo == 28:
        return 312 # Argila arenossiltosa (código 312)
    elif 29 <= codigo <= 32: 
        return 32  # Argila Siltosa (código 32)
    elif codigo == 33:
        return 321 # Argila siltoarenosa (código 321)
    elif codigo == 34:
        return 32  # Turfa (Default segurança)
        
    return 32  # Default de segurança (Argila Siltosa)

def tradutor_berberian_para_teixeira(codigo):
    """
    Remaneja os 34 solos de Berberian diretamente para as 8 categorias exatas de Teixeira.
    Essa versão elimina buscas parciais perigosas e adota agrupamentos conservadores a favor da segurança.
    """
    
    # ==========================================
    # GRUPO 1: AREIAS (Códigos 1 a 11)
    # ==========================================
    if codigo == 1: 
        return 'Areia'
    elif 2 <= codigo <= 6: 
        return 'Areia Siltosa'
    elif 7 <= codigo <= 11: 
        return 'Areia Argilosa'
        
    # ==========================================
    # GRUPO 2: SILTES (Códigos 12 a 22)
    # ==========================================
    elif 12 <= codigo <= 17: 
        return 'Silte Arenoso'
    elif 18 <= codigo <= 22: 
        return 'Silte Argiloso'
        
    # ==========================================
    # GRUPO 3: ARGILAS E TURFAS (Códigos 23 a 34)
    # ==========================================
    elif 24 <= codigo <= 28: 
        return 'Argila Arenosa'
    elif codigo == 23 or (29 <= codigo <= 34): 
        return 'Argila Siltosa'
        
    # Default de segurança caso um código fora de 1-34 seja inserido
    return 'Argila Siltosa'

def tradutor_berberian_para_monteiro(codigo):
    """
    Remaneja os 34 solos de Berberian para os 15 códigos originais de Monteiro (1997).
    """
    if codigo == 1: return 1 # Areia
    elif 2 <= codigo <= 5: return 2 # Areia Siltosa
    elif codigo == 6: return 3 # Areia Silto-argilosa
    elif 7 <= codigo <= 10: return 5 # Areia Argilosa
    elif codigo == 11: return 4 # Areia Argilo-siltosa
    elif codigo == 12: return 8 # Silte
    elif 13 <= codigo <= 16: return 6 # Silte Arenoso
    elif codigo == 17: return 7 # Silte Areno-argiloso
    elif 18 <= codigo <= 21: return 10 # Silte Argiloso
    elif codigo == 22: return 9 # Silte Argilo-arenoso
    elif codigo == 23: return 15 # Argila
    elif 24 <= codigo <= 27: return 11 # Argila Arenosa
    elif codigo == 28: return 12 # Argila Areno-siltosa
    elif 29 <= codigo <= 32: return 14 # Argila Siltosa
    elif codigo == 33: return 13 # Argila Silto-arenosa
    elif codigo == 34: return 14 # Turfa -> Argila Siltosa
    
    return 14 # Default de segurança