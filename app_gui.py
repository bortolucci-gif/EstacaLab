"""
EstacaLab — Ponto de entrada da aplicação GUI.
Execute este arquivo com: python app_gui.py
"""

import sys
import os

# Garante que o diretório do projeto está no path para importar os módulos de cálculo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuração de encoding para Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

if __name__ == "__main__":
    from gui.app import AppEstacaLab

    app = AppEstacaLab()
    app.mainloop()
