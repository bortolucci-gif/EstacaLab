import os
import sys
import tempfile
import json
import tkinter as tk
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from gui.app import AppEstacaLab
from gui.state import state, save_user_config, normalizar_dados_projeto

def run_tests():
    print("=== INICIANDO TESTES HEADER E PREFERÊNCIAS ===")
    
    # Prepara diretório temporário para ser o %APPDATA% mockado
    temp_dir = tempfile.TemporaryDirectory()
    temp_config_path = os.path.join(temp_dir.name, "config.json")
    
    app = AppEstacaLab()
    app.withdraw()

    # ---------------------------------------------------------
    # TESTE A: Nome do projeto salvo -> header muda
    # ---------------------------------------------------------
    print("\n--- A) NOME DO PROJETO -> HEADER ---")
    state.nome_projeto = "Fundação Edifício A"
    state.notificar() # Simula o que Salvar Dados faz ao final
    
    # O header no app é app.lbl_projeto
    assert app.lbl_projeto.cget("text") == "Fundação Edifício A", "Header não foi atualizado após state.notificar()"
    print("[OK] Header atualizado imediatamente.")
    
    # ---------------------------------------------------------
    # TESTE B: Responsável/registro salvos no config local
    # ---------------------------------------------------------
    print("\n--- B) SALVAR NO CONFIG LOCAL ---")
    state.responsavel_tecnico = "Willian"
    state.registro_profissional = "CREA-PR 1608928"
    
    with patch('gui.state.get_config_path', return_value=temp_config_path):
        save_user_config(state.responsavel_tecnico, state.registro_profissional)
        
        assert os.path.exists(temp_config_path), "Configuração não foi criada no caminho esperado"
        with open(temp_config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        assert cfg.get("responsavel_tecnico") == "Willian", "Responsável não salvo"
        assert cfg.get("registro_profissional") == "CREA-PR 1608928", "Registro não salvo"
        print("[OK] Preferências salvas corretamente.")

    # ---------------------------------------------------------
    # TESTE C: Nova sessão -> defaults reaparecem
    # ---------------------------------------------------------
    print("\n--- C) NOVA SESSÃO / NOVO PROJETO ---")
    # Limpa state
    state.reset()
    assert state.responsavel_tecnico == "", "Reset não limpou state"
    
    with patch('gui.state.get_config_path', return_value=temp_config_path):
        state.aplicar_defaults_usuario()
        
        assert state.responsavel_tecnico == "Willian", "Responsável default não recarregou"
        assert state.registro_profissional == "CREA-PR 1608928", "Registro default não recarregou"
        print("[OK] Valores padrão reaplicados após reset.")

    # ---------------------------------------------------------
    # TESTE D: Abrir projeto com outro responsável prevalece
    # ---------------------------------------------------------
    print("\n--- D) ABRIR PROJETO EXISTENTE ---")
    
    # Prepara um .estacalab falso
    fake_project_path = os.path.join(temp_dir.name, "projeto.estacalab")
    dados_projeto = {
        "nome_projeto": "Projeto Antigo",
        "responsavel_tecnico": "João",
        "registro_profissional": "CREA 123"
    }
    with open(fake_project_path, "w", encoding="utf-8") as f:
        json.dump(dados_projeto, f)
        
    with patch('gui.state.get_config_path', return_value=temp_config_path):
        state.reset()
        state.aplicar_defaults_usuario() # como se fosse novo
        
        # Simula abrir
        with open(fake_project_path, "r", encoding="utf-8") as f:
            dados_brutos = json.load(f)
        dados_limpos = normalizar_dados_projeto(dados_brutos)
        state.de_dict(dados_limpos)
        
        assert state.responsavel_tecnico == "João", "O responsável do projeto foi sobrescrito pelas preferências"
        assert state.registro_profissional == "CREA 123", "O registro do projeto foi sobrescrito"
        print("[OK] Dados do projeto prevalecem.")

    # ---------------------------------------------------------
    # TESTE E: Config inexistente
    # ---------------------------------------------------------
    print("\n--- E) CONFIG INEXISTENTE ---")
    nao_existe_path = os.path.join(temp_dir.name, "nao_existe.json")
    
    state.reset()
    try:
        with patch('gui.state.get_config_path', return_value=nao_existe_path):
            state.aplicar_defaults_usuario()
            assert state.responsavel_tecnico == "", "Deveria estar vazio"
            print("[OK] Inicialização normal sem arquivo de configuração.")
    except Exception as e:
        assert False, f"Crashou com config inexistente: {e}"

    # ---------------------------------------------------------
    # TESTE F: Config corrompido
    # ---------------------------------------------------------
    print("\n--- F) CONFIG CORROMPIDO ---")
    corrompido_path = os.path.join(temp_dir.name, "corrompido.json")
    with open(corrompido_path, "w", encoding="utf-8") as f:
        f.write("{ json_quebrado,")
        
    state.reset()
    try:
        with patch('gui.state.get_config_path', return_value=corrompido_path):
            state.aplicar_defaults_usuario()
            assert state.responsavel_tecnico == "", "Deveria estar vazio"
            print("[OK] Inicialização normal com arquivo corrompido.")
    except Exception as e:
        assert False, f"Crashou com config corrompido: {e}"


    app.destroy()
    temp_dir.cleanup()
    print("\n=== TODOS OS TESTES PASSARAM ===")

if __name__ == "__main__":
    run_tests()
