"""
EstacaLab — Ponto de entrada da aplicação GUI.
Execute este arquivo com: python app_gui.py
"""

import sys
import os

# Garante que o diretório do projeto está no path para importar os módulos de cálculo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuração de encoding para execução com console.
# Em executáveis GUI (--windowed), stdout/stderr podem ser None.
def _configurar_utf8(stream):
    if stream is None:
        return

    try:
        if getattr(stream, "encoding", None) != "utf-8":
            stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError, OSError):
        pass


_configurar_utf8(sys.stdout)
_configurar_utf8(sys.stderr)

if __name__ == "__main__":
    from gui.app import AppEstacaLab

    app = AppEstacaLab()
    app.mainloop()
