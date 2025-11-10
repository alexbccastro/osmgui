from cx_Freeze import setup, Executable
import sys
import os
import pyproj  # para localizar o diretório do PROJ no seu ambiente

main_script = "osmgui.py"

# Descobre automaticamente onde está o PROJ (para evitar erros de caminho)
proj_dir = pyproj.datadir.get_data_dir()

include_files = [
    "osmgui_logo_square.ico",
    "osmgui_logo_txt_75.png",
    (proj_dir, "proj"),  # inclui o diretório de dados do PROJ
]

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
        "pyproj",     # <--- faltava
        "fiona",      # <--- faltava
        "pandas",     # <--- faltava
        "rtree",      # <--- faltava
        "threading",  # <--- usado no app
        "time",       # <--- usado no app
        "html",
    ],
    "includes": [
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "PIL.Image",
        "PIL.ImageTk",
        "html.parser",
        "matplotlib.backends.backend_tkagg",  # <--- importante para gráficos Tkinter
    ],
    "include_files": include_files,
    "excludes": ["unittest", "pydoc", "email"],  # <--- evita conflitos
    "optimize": 1,  # mais seguro para builds complexos
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="OSM.gui",
    version="1.0.0",
    description="Graphical interface for OSMnx data download",
    author="Alexandre Castro, Matheus Simões, Thereza Monteiro",
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
