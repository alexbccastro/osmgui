from cx_Freeze import setup, Executable
import sys
import os

# Script principal
main_script = "osmgui.py"  # renomeie se o arquivo tiver outro nome real

# Ícones e imagens necessários
include_files = [
    "osmgui_logo_square.ico",
    "osmgui_logo_txt_75.png"
]

# Dependências adicionais detectadas no código
build_exe_options = {
    "packages": [
        "tkinter",
        "osmnx",
        "PIL",
        "json",
        "re",
        "os",
        "webbrowser",
        "geopandas",
        "networkx",
        "shapely",
        "matplotlib",
    ],
    "includes": [
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "PIL.Image",
        "PIL.ImageTk",
    ],
    "include_files": include_files,
    "excludes": ["unittest", "email", "html", "http", "pydoc"],
    "optimize": 2,
}

# Base para Windows (sem console)
base = None
if sys.platform == "win32":
    base = "Win32GUI"

# Configuração do executável
setup(
    name="OSM.gui",
    version="1.0.0",
    description="Graphical interface for OSMnx data download",
    author="Alexandre Castro, Matheus Simões, Paulo Freitas",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            main_script,
            base=base,
            icon="osmgui_logo_square.ico",
            target_name="OSMgui.exe"
        )
    ],
)
