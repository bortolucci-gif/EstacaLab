import subprocess
import sys
import os

def main():
    print("=== EXECUTOR DA SUÍTE ESTACALAB ===")
    
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    scripts = [
        "tests/teste_validacao.py",
        "tests/teste_novo_projeto.py",
        "tests/teste_header_e_prefs.py",
        "tests/teste_dependencias.py",
        "tests/teste_concorrencia_capacidade.py",
        "tests/teste_e2e.py",
        "tests/teste_alteracoes_nao_salvas.py",
        "tests/teste_cota_sondagem.py",
        "tests/teste_transacao.py",
        "tests/teste_projeto_modificado.py",
        "tests/teste_fundacao_preenchida.py"
    ]
    
    print(f"{'TESTE':<40} {'EXIT CODE':<12} {'STATUS'}")
    print("-" * 65)
    
    pass_count = 0
    fail_count = 0
    failed_scripts = []
    
    for script in scripts:
        script_path = os.path.join(ROOT, script)
        print(f"Executando {script}...", flush=True)
        cmd = [sys.executable, script_path]
        
        result = subprocess.run(cmd, cwd=ROOT)
        
        status = "PASS" if result.returncode == 0 else "FAIL"
        print(f"{script:<40} {result.returncode:<12} {status}", flush=True)
        
        if result.returncode == 0:
            pass_count += 1
        else:
            fail_count += 1
            failed_scripts.append(script)
            
    print("\n" + "=" * 65)
    print(f"TOTAL: {len(scripts)} scripts")
    print(f"PASS: {pass_count}")
    print(f"FAIL: {fail_count}")
    
    if fail_count > 0:
        print("\nScripts que falharam:")
        for fs in failed_scripts:
            print(f" - {fs}")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
