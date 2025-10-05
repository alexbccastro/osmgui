import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import osmnx as ox
from PIL import Image, ImageTk
import re
import json
import os
import webbrowser

ox.settings.log_console = True
ox.settings.max_query_area_size = 25e12


# ---------------- Funções auxiliares ----------------

def sanitize_filename(text):
    """Remove espaços e caracteres estranhos para nomes de arquivos."""
    return re.sub(r"[^a-zA-Z0-9_-]", "_", text)

def format_coords(coord):
    """Formata latitude e longitude em string curta para arquivo."""
    lat, lon = coord
    return f"{lat:.5f}_{lon:.5f}"

def download_feature_from_place(place_name, tags, filepath):
    try:
        gdf = ox.features_from_place(place_name, tags=tags)

        if gdf is None or gdf.empty:
            messagebox.showwarning("Warning", f"No data found for {os.path.basename(filepath)}.")
            return False

        if "nodes" in gdf.columns:
            gdf = gdf.drop(columns=["nodes"])

        geom_col = gdf.geometry.name
        for col in gdf.columns:
            if col == geom_col:
                continue
            if gdf[col].apply(lambda x: isinstance(x, (list, dict))).any():
                gdf[col] = gdf[col].apply(lambda x: json.dumps(x) if x is not None else None)

        gdf.to_file(filepath, driver="GPKG")
        return True

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download {filepath}: {e}")
        return False

def download_feature_from_point(coord, radius, tags, filepath):
    try:
        gdf = ox.features_from_point(coord, dist=radius, tags=tags)

        if gdf is None or gdf.empty:
            messagebox.showwarning("Warning", f"No data found for {os.path.basename(filepath)}.")
            return False

        if "nodes" in gdf.columns:
            gdf = gdf.drop(columns=["nodes"])

        geom_col = gdf.geometry.name
        for col in gdf.columns:
            if col == geom_col:
                continue
            if gdf[col].apply(lambda x: isinstance(x, (list, dict))).any():
                gdf[col] = gdf[col].apply(lambda x: json.dumps(x) if x is not None else None)

        gdf.to_file(filepath, driver="GPKG")
        return True

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download {filepath}: {e}")
        return False



# ---------------- Dicionário global de camadas ----------------

layers = {
    "aerialway": {"tags": {"aerialway": True}, "filename": "aerialway"},
    "aeroway": {"tags": {"aeroway": True}, "filename": "aeroway"},
    "amenity": {"tags": {"amenity": True}, "filename": "amenities"},
    "barrier": {"tags": {"barrier": True}, "filename": "barrier"},
    "boundary": {"tags": {"boundary": True}, "filename": "boundary"},
    "building": {"tags": {"building": True}, "filename": "building"},
    "craft": {"tags": {"craft": True}, "filename": "craft"},
    "cycleway": {
        "tags": {
            "highway": "cycleway",
            "cycleway:right": True,
            "cycleway:left": True,
            "cycleway:both": True,
            "cycleway:buffer": True,
            "cycleway:foot": True,
            "cycleway:lane": True,
            "cyclestreet": True,
            "cycleway:segregated": True,
            "cycleway:surface": True,
            "cycle highway": True
        },
        "filename": "cycleway"
    },
    "emergency": {"tags": {"emergency": True}, "filename": "emergency"},
    "geological": {"tags": {"geological": True}, "filename": "geological"},
    "healthcare": {"tags": {"healthcare": True}, "filename": "healthcare"},
    "historic": {"tags": {"historic": True}, "filename": "historic"},
    "landuse": {"tags": {"landuse": True}, "filename": "landuse"},
    "leisure": {"tags": {"leisure": True}, "filename": "leisure"},
    "manmade": {"tags": {"man_made": True}, "filename": "manmade"},
    "military": {"tags": {"military": True}, "filename": "military"},
    "natural": {"tags": {"natural": True}, "filename": "natural"},
    "office": {"tags": {"office": True}, "filename": "office"},
    "park": {
        "tags": {
            "leisure": ["dog_park", "park"],
            "tourism": ["zoo"]
        },
        "filename": "park"
    },
    "place": {"tags": {"place": True}, "filename": "place"},
    "power": {"tags": {"power": True}, "filename": "power"},
    "publictransport": {"tags": {"public_transport": True}, "filename": "public_transport"},
    "railway": {"tags": {"railway": True}, "filename": "railway"},
    "shop": {"tags": {"shop": True}, "filename": "shop"},
    "telecom": {"tags": {"telecom": True}, "filename": "telecom"},
    "tourism": {"tags": {"tourism": True}, "filename": "tourism"},
    "water": {
        "tags": {
            "water": True,
            "natural": "water"
        },
        "filename": "water"
    },
    "waterway": {"tags": {"waterway": True}, "filename": "waterway"},
}


# ---------------- Função principal de download ----------------

def download_data():
    download_button.config(state="disabled")
    status_txt.config(text="Status: Download in progress")
    progress_bar_var.set(0)
    progress_bar.config(style="Blue.Horizontal.TProgressbar")  # default blue
    root.update_idletasks()

    place_name = name_entry_var.get()
    road_type = highway_type_combobox_var.get()
    simpl = highway_simpl_checkbutton_var.get()
    path = saveas_entry_var.get()
    safe_place = sanitize_filename(place_name)

    # ---------------- count tasks ----------------
    total_tasks = 0
    if highway_checkbutton_var.get():
        total_tasks += 1
    for key in layers.keys():
        var = globals()[f"{key}_checkbutton_var"]
        if var.get():
            total_tasks += 1

    if total_tasks == 0:
        messagebox.showerror("Error", "Please select at least one layer to download.")
        download_button.config(state="normal")
        return

    completed = 0
    error_occurred = False

    # ---------------- update progress ----------------
    def update_progress(task_name="", success=True):
        nonlocal completed, error_occurred
        completed += 1
        percent = (completed / total_tasks) * 100
        progress_bar_var.set(percent)

        if not success:
            error_occurred = True

        status_txt.config(text=f"Status: {task_name} ({percent:.0f}%)")
        root.update_idletasks()

    # ---------------- animate during task ----------------
    def animate_task(func, *args, task_name=""):
        progress_bar.config(mode="indeterminate")
        progress_bar.start(15)  # animation speed
        root.update_idletasks()

        success = func(*args)

        progress_bar.stop()
        progress_bar.config(mode="determinate")
        update_progress(task_name, success=success)

    # ---------------- download by place name ----------------
    if name_checkbutton_var.get():
        if highway_checkbutton_var.get():
            def dl_highway():
                try:
                    graph = ox.graph_from_place(place_name, network_type=highway_type_dict[road_type], simplify=highway_simpl_checkbutton_var.get(), retain_all=retain_all_var.get(), truncate_by_edge=truncate_var.get())
                    ox.save_graph_geopackage(graph, filepath=f"{path}/highway_{safe_place}_{road_type}.gpkg")
                    return True
                except Exception as e:
                    messagebox.showerror("Error", f"Could not download streets: {e}")
                    return False

            animate_task(dl_highway, task_name="Streets")

        for key, conf in layers.items():
            var = globals()[f"{key}_checkbutton_var"]
            if var.get():
                filepath = f"{path}/{conf['filename']}_{safe_place}.gpkg"
                animate_task(download_feature_from_place, place_name, conf["tags"], filepath, task_name=conf["filename"])

    # ---------------- download by point and radius ----------------
    elif point_checkbutton_var.get():
        coord = (float(lat_entry_var.get()), float(long_entry_var.get()))
        radius = int(radius_entry_var.get())
        coord_str = format_coords(coord)

        if highway_checkbutton_var.get():
            def dl_highway():
                try:
                    graph = ox.graph_from_point(coord, dist=radius, network_type=highway_type_dict[road_type], simplify=highway_simpl_checkbutton_var.get(), retain_all=retain_all_var.get(), truncate_by_edge=truncate_var.get())
                    ox.save_graph_geopackage(graph, filepath=f"{path}/highway_{coord_str}_{road_type}_r{radius}m.gpkg")
                    return True
                except Exception as e:
                    messagebox.showerror("Error", f"Could not download streets: {e}")
                    return False

            animate_task(dl_highway, task_name="Streets")

        for key, conf in layers.items():
            var = globals()[f"{key}_checkbutton_var"]
            if var.get():
                filepath = f"{path}/{conf['filename']}_{coord_str}_r{radius}m.gpkg"
                animate_task(download_feature_from_point, coord, radius, conf["tags"], filepath, task_name=conf["filename"])

    else:
        messagebox.showerror("Error", "Please select Name or Point as geographic reference.")

    # ---------------- finalize ----------------
    progress_bar_var.set(100)
    if error_occurred:
        progress_bar.config(style="Red.Horizontal.TProgressbar")
        status_txt.config(text="Status: Completed with errors (100%)")
        messagebox.showwarning("Warning", "Download finished, but some layers failed.")
    else:
        progress_bar.config(style="Green.Horizontal.TProgressbar")
        status_txt.config(text="Status: Download completed (100%)")
        messagebox.showinfo("Info", "Download completed successfully.")

    download_button.config(state="normal")
    root.update_idletasks()


# ---------------- Funções de controle da interface ----------------

def name_select():
    if name_checkbutton_var.get():
        name_entry.config(state='normal')
        point_checkbutton_var.set(False)
        lat_txt.config(foreground='#808080')
        lat_entry.delete(0, tk.END)
        lat_entry.config(state='disabled')
        long_txt.config(foreground='#808080')
        long_entry.delete(0, tk.END)
        long_entry.config(state='disabled')
        radius_txt.config(foreground='#808080')
        radius_entry.delete(0, tk.END)
        radius_entry.config(state='disabled')
    else:
        name_entry.delete(0, tk.END)
        name_entry.config(state='disabled')

def point_select():
    if point_checkbutton_var.get():
        name_entry.delete(0, tk.END)
        name_entry.config(state='disabled')
        name_checkbutton_var.set(False)
        lat_txt.config(foreground='#000000')
        lat_entry.config(state='normal')
        long_txt.config(foreground='#000000')
        long_entry.config(state='normal')
        radius_txt.config(foreground='#000000')
        radius_entry.config(state='normal')
    else:
        lat_txt.config(foreground='#808080')
        lat_entry.delete(0, tk.END)
        lat_entry.config(state='disabled')
        long_txt.config(foreground='#808080')
        long_entry.delete(0, tk.END)
        long_entry.config(state='disabled')
        radius_txt.config(foreground='#808080')
        radius_entry.delete(0, tk.END)
        radius_entry.config(state='disabled')

def road_select():
    if highway_checkbutton_var.get():
        highway_type_txt.config(foreground='#000000')
        highway_type_combobox.config(state='readonly')
        highway_simpl_checkbutton.config(state='normal')
        retain_all_chk.config(state='normal')
        truncate_chk.config(state='normal')
    else:
        highway_type_txt.config(foreground='#808080')
        highway_type_combobox.set('')
        highway_type_combobox.config(state='disabled')
        highway_simpl_checkbutton_var.set(False)
        highway_simpl_checkbutton.config(state='disabled')
        retain_all_var.set(False)
        retain_all_chk.config(state='disabled')
        truncate_var.set(False)
        truncate_chk.config(state='disabled')


# ---------------- Funções de seleção automática ----------------

def select_all():
    if all_checkbutton_var.get():
        for key in layers.keys():
            globals()[f"{key}_checkbutton_var"].set(True)

        # highway
        highway_checkbutton_var.set(True)
        highway_type_txt.config(foreground='#000000')
        highway_type_combobox.config(state='readonly')
        highway_simpl_checkbutton.config(state='normal')

        # novos checkbuttons ficam disponíveis mas desmarcados
        retain_all_chk.config(state='normal')
        retain_all_var.set(False)
        truncate_chk.config(state='normal')
        truncate_var.set(False)


    else:
        for key in layers.keys():
            globals()[f"{key}_checkbutton_var"].set(False)

        # highway
        highway_checkbutton_var.set(False)
        highway_type_txt.config(foreground='#808080')
        highway_type_combobox.set('')
        highway_type_combobox.config(state='disabled')
        highway_simpl_checkbutton_var.set(False)
        highway_simpl_checkbutton.config(state='disabled')

        # novos checkbuttons voltam a desmarcados e desabilitados
        retain_all_var.set(False)
        retain_all_chk.config(state='disabled')
        truncate_var.set(False)
        truncate_chk.config(state='disabled')


def select_all_from_menu():
    all_checkbutton_var.set(True)   # força o checkbox a ficar ligado
    select_all()


def clear_all():
    # referência geográfica (igual ao seu código) ...

    # features
    all_checkbutton_var.set(False)
    for key in layers.keys():
        globals()[f"{key}_checkbutton_var"].set(False)

    # rodovias
    highway_checkbutton_var.set(False)
    highway_type_txt.config(foreground='#808080')
    highway_type_combobox.set('')
    highway_type_combobox.config(state='disabled')
    highway_simpl_checkbutton_var.set(False)
    highway_simpl_checkbutton.config(state='disabled')
    retain_all_var.set(False)
    retain_all_chk.config(state='disabled')
    truncate_var.set(False)
    truncate_chk.config(state='disabled')


def saveas_dir():
    path = filedialog.askdirectory()
    if path:
        saveas_entry_var.set(path)

#--------------------------------------------- Interface Gráfica ------------------------------------------------------

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tipwindow or not self.text:
            return
        # Pega posição do widget na tela
        x, y, _, h = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + h + 20

        # Cria janela sem borda
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("Segoe UI", 9)
        )
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None

# janela principal
root = tk.Tk()
root.title('OSM.gui, v1.0.0')
root.iconbitmap('osmgui_logo_square.ico')
root.resizable(width=False, height=False)

# ---------------- Menu Superior ----------------
def about_osmgui():
    messagebox.showinfo(
        "About OSM.gui",
        "OSM.gui v1.0.0\n\n"
        "Developed by:\n"
        "- Alexandre Augusto Bezerra da Cunha Castro\n"
        "- Matheus Batista Simões\n"
        "- Paulo Vítor Nascimento de Freitas\n\n"
        "October | 2025\n\n"
        "Based in Python + Tkinter + OSMnx"
    )

def open_github():
    webbrowser.open("https://github.com/alexbccastro/osmgui")  # coloque aqui o link da documentação

def open_documentation():
    webbrowser.open("https://seudominio.com/osmgui-docs")  # coloque aqui o link da documentação

menu_bar = tk.Menu(root)


# --- Arquivo ---
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Save as...", command=saveas_dir)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# --- Ferramentas ---
tools_menu = tk.Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Clear All", command=clear_all)
tools_menu.add_command(label="Select All", command=select_all_from_menu)
menu_bar.add_cascade(label="Tools", menu=tools_menu)

# --- Ajuda ---
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About OSM.gui", command=about_osmgui)
help_menu.add_command(label="OSM.gui on GitHub", command=open_github)
help_menu.add_command(label="Documentation", command=open_documentation)
menu_bar.add_cascade(label="Help", menu=help_menu)

# aplicar menu na janela
root.config(menu=menu_bar)

image = Image.open('osmgui_logo_txt_75.png')
image_tk = ImageTk.PhotoImage(image)
image_label = ttk.Label(root, image=image_tk)
image_label.grid(row=0, column=6, columnspan=3, pady=(5,0), sticky='nsew')

# labelframe e widgets da referência geográfica
ref_labelframe = ttk.Labelframe(root, text='Geographic Reference')
ref_labelframe.grid(row=0, column=0, columnspan=6, padx=10, pady=10, sticky='ew')
ref_labelframe.columnconfigure(0, weight=1)
ref_labelframe.columnconfigure(1, weight=1)
ref_labelframe.columnconfigure(2, weight=1)
ref_labelframe.columnconfigure(3, weight=1)
ref_labelframe.columnconfigure(4, weight=1)
ref_labelframe.columnconfigure(5, weight=1)
ref_labelframe.columnconfigure(6, weight=1)
ref_labelframe.rowconfigure(0, weight=1)
ref_labelframe.rowconfigure(1, weight=1)
ref_labelframe.rowconfigure(2, weight=1)

name_checkbutton_var = tk.BooleanVar()
name_checkbutton = ttk.Checkbutton(ref_labelframe, text='Name', variable=name_checkbutton_var, command=name_select)
name_checkbutton.grid(row=0, column=0, padx=10, pady=(5, 10), sticky='ew')
ToolTip(name_checkbutton, 'Insert a valid name, acording to OSM Nominatin (e.g.: "Brasília, Brazil")')
name_entry_var = tk.StringVar()
name_entry = ttk.Entry(ref_labelframe, textvariable=name_entry_var, state='disabled')
name_entry.grid(row=0, column=1, columnspan=6, padx=(0, 10), pady=(5, 10), sticky='ew')

point_checkbutton_var = tk.BooleanVar()
point_checkbutton = ttk.Checkbutton(ref_labelframe, text='Point (Decimal Degrees)', variable=point_checkbutton_var, command=point_select)
point_checkbutton.grid(row=1, column=0, padx=10, pady=(0, 10), sticky='ew')
ToolTip(point_checkbutton, 'Insert latitude and longitude in decimal degrees (e.g.: -15,7939869, -47,8828000)')
lat_txt = ttk.Label(ref_labelframe, text='Latitude:', foreground='#808080', justify='left', anchor='w')
lat_txt.grid(row=1, column=1, padx=(0, 5), pady=(0, 10), sticky='ew')
lat_entry_var = tk.StringVar()
lat_entry = ttk.Entry(ref_labelframe, textvariable=lat_entry_var, state='disabled')
lat_entry.grid(row=1, column=2, padx=(0, 10), pady=(0, 10), sticky='ew')
long_txt = ttk.Label(ref_labelframe, text='Longitude:', foreground='#808080', justify='left', anchor='w')
long_txt.grid(row=1, column=3, padx=(0, 5), pady=(0, 10), sticky='ew')
long_entry_var = tk.StringVar()
long_entry = ttk.Entry(ref_labelframe, textvariable=long_entry_var, state='disabled')
long_entry.grid(row=1, column=4, padx=(0, 10), pady=(0, 10), sticky='ew')
radius_txt = ttk.Label(ref_labelframe, text='Radius (m):', foreground='#808080', justify='left', anchor='w')
radius_txt.grid(row=1, column=5, padx=(0, 5), pady=(0, 10), sticky='ew')
ToolTip(radius_txt, 'Enter the coverage radius of the data downloads in metres')
radius_entry_var = tk.IntVar()
radius_entry_var.set('')
radius_entry = ttk.Entry(ref_labelframe, textvariable=radius_entry_var, state='disabled')
radius_entry.grid(row=1, column=6, padx=(0,10), pady=(0,10), sticky='ew')

# labelframe e widgets dos dados
features_labelframe = ttk.Labelframe(root, text='Features')
features_labelframe.grid(row=1, column=0, columnspan=9, padx=10, pady=(0, 10), sticky='ew')
features_labelframe.columnconfigure(0, weight=1)
features_labelframe.columnconfigure(1, weight=1)
features_labelframe.columnconfigure(2, weight=1)
features_labelframe.columnconfigure(3, weight=1)
features_labelframe.columnconfigure(4, weight=1)
features_labelframe.columnconfigure(5, weight=1)
features_labelframe.columnconfigure(6, weight=1)

all_checkbutton_var = tk.BooleanVar()
all_checkbutton = ttk.Checkbutton(features_labelframe, text='Select All', variable=all_checkbutton_var, command=select_all, width=15)
all_checkbutton.grid(row=0, column=0, padx=(10,0), pady=(0,5), sticky='w')

aerialway_checkbutton_var = tk.BooleanVar()
aerialway_checkbutton = ttk.Checkbutton(features_labelframe, text='Aerialway', variable=aerialway_checkbutton_var, width=15)
aerialway_checkbutton.grid(row=1, column=0, padx=(10,0), pady=(0,5), sticky='w')
aeroway_checkbutton_var = tk.BooleanVar()
aeroway_checkbutton = ttk.Checkbutton(features_labelframe, text='Aeroway', variable=aeroway_checkbutton_var, width=15)
aeroway_checkbutton.grid(row=1, column=1, pady=(0,5), sticky='w')
amenity_checkbutton_var = tk.BooleanVar()
amenity_checkbutton = ttk.Checkbutton(features_labelframe, text='Amenity', variable=amenity_checkbutton_var, width=15)
amenity_checkbutton.grid(row=1, column=2, pady=(0,5), sticky='w')
barrier_checkbutton_var = tk.BooleanVar()
barrier_checkbutton = ttk.Checkbutton(features_labelframe, text='Barrier', variable=barrier_checkbutton_var, width=15)
barrier_checkbutton.grid(row=1, column=3, pady=(0,5), sticky='w')
boundary_checkbutton_var = tk.BooleanVar()
boundary_checkbutton = ttk.Checkbutton(features_labelframe, text='Boundary', variable=boundary_checkbutton_var, width=15)
boundary_checkbutton.grid(row=1, column=4, pady=(0,5), sticky='w')
building_checkbutton_var = tk.BooleanVar()
building_checkbutton = ttk.Checkbutton(features_labelframe, text='Building', variable=building_checkbutton_var, width=15)
building_checkbutton.grid(row=1, column=5, pady=(0,5), sticky='w')

craft_checkbutton_var = tk.BooleanVar()
craft_checkbutton = ttk.Checkbutton(features_labelframe, text='Craft', variable=craft_checkbutton_var, width=15)
craft_checkbutton.grid(row=2, column=0, padx=(10,0), pady=(0,5), sticky='w')
cycleway_checkbutton_var = tk.BooleanVar()
cycleway_checkbutton = ttk.Checkbutton(features_labelframe, text='Cycleway', variable=cycleway_checkbutton_var, width=15)
cycleway_checkbutton.grid(row=2, column=1, pady=(0,5), sticky='w')
emergency_checkbutton_var = tk.BooleanVar()
emergency_checkbutton = ttk.Checkbutton(features_labelframe, text='Emergency', variable=emergency_checkbutton_var, width=15)
emergency_checkbutton.grid(row=2, column=2, pady=(0,5), sticky='w')
geological_checkbutton_var = tk.BooleanVar()
geological_checkbutton = ttk.Checkbutton(features_labelframe, text='Geological', variable=geological_checkbutton_var, width=15)
geological_checkbutton.grid(row=2, column=3, pady=(0,5), sticky='w')
healthcare_checkbutton_var = tk.BooleanVar()
healthcare_checkbutton = ttk.Checkbutton(features_labelframe, text='Healthcare', variable=healthcare_checkbutton_var, width=15)
healthcare_checkbutton.grid(row=2, column=4, pady=(0,5), sticky='w')
highway_checkbutton_var = tk.BooleanVar()
highway_checkbutton = ttk.Checkbutton(features_labelframe, text='Highway', variable=highway_checkbutton_var, command=road_select, width=15)
highway_checkbutton.grid(row=2, column=5, pady=(0,5), sticky='w')

historic_checkbutton_var = tk.BooleanVar()
historic_checkbutton = ttk.Checkbutton(features_labelframe, text='Historic', variable=historic_checkbutton_var, width=15)
historic_checkbutton.grid(row=3, column=0, padx=(10,0), pady=(0,5), sticky='w')
landuse_checkbutton_var = tk.BooleanVar()
landuse_checkbutton = ttk.Checkbutton(features_labelframe, text='Landuse', variable=landuse_checkbutton_var, width=15)
landuse_checkbutton.grid(row=3, column=1, pady=(0,5), sticky='w')
leisure_checkbutton_var = tk.BooleanVar()
leisure_checkbutton = ttk.Checkbutton(features_labelframe, text='Leisure', variable=leisure_checkbutton_var, width=15)
leisure_checkbutton.grid(row=3, column=2, pady=(0,5), sticky='w')
manmade_checkbutton_var = tk.BooleanVar()
manmade_checkbutton = ttk.Checkbutton(features_labelframe, text='Man Made', variable=manmade_checkbutton_var, width=15)
manmade_checkbutton.grid(row=3, column=3, pady=(0,5), sticky='w')
military_checkbutton_var = tk.BooleanVar()
military_checkbutton = ttk.Checkbutton(features_labelframe, text='Military', variable=military_checkbutton_var, width=15)
military_checkbutton.grid(row=3, column=4, pady=(0,5), sticky='w')
natural_checkbutton_var = tk.BooleanVar()
natural_checkbutton = ttk.Checkbutton(features_labelframe, text='Natural', variable=natural_checkbutton_var, width=15)
natural_checkbutton.grid(row=3, column=5, pady=(0,5), sticky='w')

office_checkbutton_var = tk.BooleanVar()
office_checkbutton = ttk.Checkbutton(features_labelframe, text='Office', variable=office_checkbutton_var, width=15)
office_checkbutton.grid(row=4, column=0, padx=(10,0), pady=(0,5), sticky='w')
park_checkbutton_var = tk.BooleanVar()
park_checkbutton = ttk.Checkbutton(features_labelframe, text='Park', variable=park_checkbutton_var, width=15)
park_checkbutton.grid(row=4, column=1, pady=(0,5), sticky='w')
place_checkbutton_var = tk.BooleanVar()
place_checkbutton = ttk.Checkbutton(features_labelframe, text='Place', variable=place_checkbutton_var, width=15)
place_checkbutton.grid(row=4, column=2, pady=(0,5), sticky='w')
power_checkbutton_var = tk.BooleanVar()
power_checkbutton = ttk.Checkbutton(features_labelframe, text='Power', variable=power_checkbutton_var, width=15)
power_checkbutton.grid(row=4, column=3, pady=(0,5), sticky='w')
publictransport_checkbutton_var = tk.BooleanVar()
publictransport_checkbutton = ttk.Checkbutton(features_labelframe, text='Public Transport', variable=publictransport_checkbutton_var, width=15)
publictransport_checkbutton.grid(row=4, column=4, pady=(0,5), sticky='w')
railway_checkbutton_var = tk.BooleanVar()
railway_checkbutton = ttk.Checkbutton(features_labelframe, text='Railway', variable=railway_checkbutton_var, width=15)
railway_checkbutton.grid(row=4, column=5, pady=(0,5), sticky='w')

shop_checkbutton_var = tk.BooleanVar()
shop_checkbutton = ttk.Checkbutton(features_labelframe, text='Shop', variable=shop_checkbutton_var, width=15)
shop_checkbutton.grid(row=5, column=0, padx=(10,0), pady=(0,5), sticky='w')
telecom_checkbutton_var = tk.BooleanVar()
telecom_checkbutton = ttk.Checkbutton(features_labelframe, text='Telecom', variable=telecom_checkbutton_var, width=15)
telecom_checkbutton.grid(row=5, column=1, pady=(0,5), sticky='w')
tourism_checkbutton_var = tk.BooleanVar()
tourism_checkbutton = ttk.Checkbutton(features_labelframe, text='Tourism', variable=tourism_checkbutton_var, width=15)
tourism_checkbutton.grid(row=5, column=2, pady=(0,5), sticky='w')
water_checkbutton_var = tk.BooleanVar()
water_checkbutton = ttk.Checkbutton(features_labelframe, text='Water', variable=water_checkbutton_var, width=15)
water_checkbutton.grid(row=5, column=3, pady=(0,5), sticky='w')
waterway_checkbutton_var = tk.BooleanVar()
waterway_checkbutton = ttk.Checkbutton(features_labelframe, text='Waterway', variable=water_checkbutton_var, width=15)
waterway_checkbutton.grid(row=5, column=4, pady=(0,5), sticky='w')

checkbutton_vars = [aerialway_checkbutton_var.get(), aeroway_checkbutton_var.get(), amenity_checkbutton_var.get(),
                    barrier_checkbutton_var.get(), boundary_checkbutton_var.get(), building_checkbutton_var.get(),
                    craft_checkbutton_var.get(), cycleway_checkbutton_var.get(), emergency_checkbutton_var.get(),
                    geological_checkbutton_var.get(), healthcare_checkbutton_var.get(), highway_checkbutton_var.get(),
                    historic_checkbutton_var.get(), landuse_checkbutton_var.get(), leisure_checkbutton_var.get(),
                    manmade_checkbutton_var.get(), military_checkbutton_var.get(), natural_checkbutton_var.get(),
                    office_checkbutton_var.get(), park_checkbutton_var.get(), place_checkbutton_var.get(),
                    power_checkbutton_var.get(), publictransport_checkbutton_var.get(), railway_checkbutton_var.get(),
                    shop_checkbutton_var.get(), telecom_checkbutton_var.get(), tourism_checkbutton_var.get(),
                    water_checkbutton_var.get(), waterway_checkbutton_var.get()]

road_data_labelframe = ttk.Labelframe(features_labelframe, text='Highway Parameters')
road_data_labelframe.grid(row=0, column=6, rowspan=7, padx=(0, 10), pady=(0, 10), sticky='nsew')
road_data_labelframe.rowconfigure(0, weight=1)
road_data_labelframe.rowconfigure(1, weight=1)
road_data_labelframe.rowconfigure(2, weight=1)
road_data_labelframe.rowconfigure(3, weight=1)
road_data_labelframe.rowconfigure(4, weight=1)
road_data_labelframe.columnconfigure(0, weight=1)
road_data_labelframe.columnconfigure(1, weight=1)

highway_type_txt = ttk.Label(road_data_labelframe, text='Highway Type', foreground='#808080', anchor='w')
highway_type_txt.grid(row=0, column=0, padx=10, pady=(0,5), sticky='w')
ToolTip(highway_type_txt, 'Select the highway type you want to download')
highway_type_dict = {'Walk': 'walk', 'Bike': 'bike', 'Drive': 'drive', 'All Public': 'all_public', 'All': 'all'}
highway_type_combobox_var = tk.StringVar()
highway_type_combobox = ttk.Combobox(road_data_labelframe, textvariable=highway_type_combobox_var, values=list(highway_type_dict.keys()), state='disabled', width=15)
highway_type_combobox.grid(row=0, column=1, padx=(0,5), pady=(0,5), sticky='e')
highway_simpl_checkbutton_var = tk.BooleanVar()
highway_simpl_checkbutton = ttk.Checkbutton(road_data_labelframe, text='Simplify Lines', variable=highway_simpl_checkbutton_var, state='disabled')
highway_simpl_checkbutton.grid(row=1, column=0, columnspan=2, padx=10, pady=(0,5), sticky='ew')
ToolTip(highway_simpl_checkbutton, 'Simplify the road network by removing intermediate nodes from the roads.')
retain_all_var = tk.BooleanVar(value=False)
retain_all_chk = ttk.Checkbutton(road_data_labelframe, text="Retain All Components", variable=retain_all_var, state="disabled")
retain_all_chk.grid(row=2, column=0, columnspan=2, padx=10, pady=(0,5), sticky='w')
ToolTip(retain_all_chk, 'Keeps all components of the graph (does not discard disconnected subgraphs).')
truncate_var = tk.BooleanVar(value=False)
truncate_chk = ttk.Checkbutton(road_data_labelframe, text="Truncate by Edge", variable=truncate_var, state="disabled")
truncate_chk.grid(row=3, column=0, columnspan=2, padx=10, pady=(0,5), sticky='w')
ToolTip(truncate_chk, 'Expands until the edges cross the boundary of the area, rather than cutting off at the exact boundary.')


# labelframe e widgets para exportação
export_labelframe = ttk.Labelframe(root, text='Export')
export_labelframe.grid(row=2, column=0, columnspan=9, padx=10, pady=(0, 10), sticky='ew')
export_labelframe.columnconfigure(0, weight=1)
export_labelframe.columnconfigure(1, weight=1)
export_labelframe.columnconfigure(2, weight=1)
export_labelframe.columnconfigure(3, weight=10)
export_labelframe.columnconfigure(4, weight=1)
export_labelframe.columnconfigure(5, weight=1)
export_labelframe.columnconfigure(6, weight=1)

style = ttk.Style()
style.configure('TButton', anchor='center', justify='left')

saveas_button = ttk.Button(export_labelframe, style='TButton', text='Save As', width=15, command=saveas_dir)
saveas_button.grid(row=3, column=0, columnspan=1, padx=(10,0), pady=5, sticky='w')
saveas_entry_var = tk.StringVar()
saveas_entry = ttk.Entry(export_labelframe, textvariable=saveas_entry_var)
saveas_entry.grid(row=3, column=1, columnspan=3, pady=5, sticky='ew')
download_button = ttk.Button(export_labelframe, text='Download', width=10, command=download_data)
download_button.grid(row=3, column=5, padx=(0,10), pady=5, sticky='ew')
clean_button = ttk.Button(export_labelframe, text='Clear', width=10, command=clear_all)
clean_button.grid(row=3, column=6, padx=(5,10), pady=5, sticky='ew')

progress_frame = ttk.Frame(export_labelframe, borderwidth=10)
progress_frame.grid(row=4, column=0, columnspan=7, sticky="ew")
progress_frame.columnconfigure(0, weight=1)
progress_frame.columnconfigure(1, weight=1)
progress_frame.columnconfigure(2, weight=2)
progress_frame.columnconfigure(3, weight=2)
progress_frame.columnconfigure(4, weight=2)
progress_frame.columnconfigure(5, weight=2)
progress_frame.columnconfigure(6, weight=2)

# progress bar styles
style = ttk.Style()
style.configure("Blue.Horizontal.TProgressbar", troughcolor="white", background="#1E90FF")
style.configure("Green.Horizontal.TProgressbar", troughcolor="white", background="#32CD32")
style.configure("Red.Horizontal.TProgressbar", troughcolor="white", background="#DC143C")

# progress bar
progress_bar_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_bar_var, style="Blue.Horizontal.TProgressbar")
progress_bar.grid(row=4, column=0, columnspan=7, sticky="ew")

# status label
status_txt = ttk.Label(progress_frame, text="Status: Waiting", width=35, justify="left", anchor="w")
status_txt.grid(row=5, column=0, columnspan=7, pady=(5,0), sticky='w')

# loop
root.mainloop()
