"""
Punto de entrada para Streamlit Cloud
Ejecuta la aplicación principal desde 02_scripts/app.py
"""
import sys
import os

# Cambiar al directorio del proyecto
project_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(project_dir)

# Agregar el directorio de scripts al path
sys.path.insert(0, os.path.join(project_dir, '02_scripts'))

# Ejecutar la app principal
exec(open('02_scripts/app.py', encoding='utf-8').read())
