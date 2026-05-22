"""
main.py
Punto de entrada único de la aplicación.
"""

import os
import sys

# Asegurar que el directorio raíz del proyecto esté en el path
DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, DIR)

from menu.menu_principal import menu_principal


if __name__ == "__main__":
    menu_principal()
