from cx_Freeze import setup, Executable
import sys
import os

main_script = "osmgui.py"

include_files = [
    "osmgui_logo_square.ico",
    "osmgui_logo_txt_75.png"
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
        "html",  # <-- incluímos explicitamente
    ],
    "includes": [
        "tkinter.ttk",
        "tkinter.filedialog",
        "tkinter.messagebox",
        "PIL.Image",
        "PIL.ImageTk",
        "html.parser",  # <-- reforço opcional
    ],
    "include_files": include_files,
    "excludes": ["unittest", "pydoc"],  # <-- removidos "html" e "http"
    "optimize": 2,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

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
