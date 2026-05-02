import os
import sys

# Adiciona o diretório raiz ao sys.path para permitir imports do diretório 'app'
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)