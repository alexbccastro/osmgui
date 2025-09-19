from cx_Freeze import setup, Executable
import sys
import os

# Nome do seu script principal
main_script = "osmgui.py"   # renomeie seu arquivo principal .py

# Adiciona ícones e imagens necessárias
include_files = [
    "osmgui_logo_square.ico",
    "osmgui_logo_txt_75.png"
]

# Dependências adicionais que o cx_Freeze pode não detectar automaticamente
build_exe_options = {
    "packages": ["tkinter", "osmnx", "PIL", "json", "re", "os"],
    "include_files": include_files,
    "includes": [],
    "excludes": [],
    "optimize": 2,
}

# Configuração do executável
base = None
if sys.platform == "win32":
    base = "Win32GUI"  # oculta a janela do console

setup(
    name="OSM.gui",
    version="1.0.0",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(main_script, base=base, icon="osmgui_logo_square.ico")
    ],
)
