import os
import json
import urllib.parse
import subprocess
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(BASE_DIR, "datos.geojson")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# Ruta estándar de Git en Windows para entornos aislados (WinPython)
GIT_PATH = r"C:\Users\dsanchez\Documentación\geotagged-image-viewer\git\cmd\git.exe"
if not os.path.exists(GIT_PATH):
    GIT_PATH = "git"

def cargar_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"sharepoint_url": ""}

def guardar_config(url):
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump({"sharepoint_url": url}, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def obtener_fecha_desde_nombre(nombre_archivo):
    """Failsafe: Extrae la fecha y hora del nombre (ej: TimePhoto_20261014_114056.jpg)"""
    try:
        # Busca un patrón de 8 dígitos (YYYYMMDD) _ 6 dígitos (HHMMSS)
        match = re.search(r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})', nombre_archivo)
        if match:
            anio, mes, dia, hora, minuto, segundo = match.groups()
            return f"{anio}:{mes}:{dia} {hora}:{minuto}:{segundo}"
    except Exception:
        pass
    return None

def obtener_datos_exif(ruta_imagen, nombre_archivo):
    try:
        image = Image.open(ruta_imagen)
        exif_data = image._getexif()
        
        gps_info = {}
        fecha = None

        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    for t in value:
                        sub_tag = GPSTAGS.get(t, t)
                        gps_info[sub_tag] = value[t]
                if tag == "DateTimeOriginal":
                    fecha = value

        # Si el EXIF no tiene fecha, aplicamos el failsafe del nombre del archivo
        if not fecha:
            fecha = obtener_fecha_desde_nombre(nombre_archivo)

        if not gps_info:
            return None, None, fecha, None

        def convertir_a_grados(valor_gps, ref):
            try:
                grados = float(valor_gps[0])
                minutos = float(valor_gps[1])
                segundos = float(valor_gps[2])
                resultado = grados + (minutos / 60.0) + (segundos / 3600.0)
                if ref in ['S', 'W']:
                    resultado = -resultado
                return resultado
            except Exception:
                return None

        lat = convertir_a_grados(gps_info.get('GPSLatitude'), gps_info.get('GPSLatitudeRef'))
        lon = convertir_a_grados(gps_info.get('GPSLongitude'), gps_info.get('GPSLongitudeRef'))
        
        azimuth = None
        raw_dir = gps_info.get('GPSImgDirection')
        if raw_dir is not None:
            try:
                if isinstance(raw_dir, (tuple, list)):
                    azimuth = float(raw_dir[0]) / float(raw_dir[1]) if len(raw_dir) > 1 and float(raw_dir[1]) != 0 else float(raw_dir[0])
                else:
                    azimuth = float(raw_dir)
            except Exception:
                azimuth = None

        return lat, lon, fecha, azimuth
    except Exception as e:
        return None, None, None, None

class AppGestorGISPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor Profesional de Catálogo GIS - SharePoint & GitHub")
        self.root.geometry("620x700")
        self.root.config(bg="#f8fafc")
        self.root.resizable(False, False)

        self.config_actual = cargar_config()
        self.all_features = []
        self.checkbox_vars = {}

        self.cargar_geojson_inicial()
        self.crear_interfaz()
        self.actualizar_lista_proyectos()

    def cargar_geojson_inicial(self):
        if os.path.exists(GEOJSON_PATH):
            try:
                with open(GEOJSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.all_features = data.get("features", [])
            except Exception:
                self.all_features = []

    def crear_interfaz(self):
        titulo = tk.Label(self.root, text="🌐 Panel de Control y Catálogo GIS", font=("Arial", 13, "bold"), bg="#f8fafc", fg="#1e293b")
        titulo.pack(pady=10)

        # SharePoint URL
        lbl_sp = tk.Label(self.root, text="URL Web de la Biblioteca en SharePoint:", font=("Arial", 9, "bold"), bg="#f8fafc", fg="#334155", anchor="w")
        lbl_sp.pack(fill="x", padx=25)
        
        self.entry_sp = tk.Entry(self.root, font=("Arial", 10), width=65)
        self.entry_sp.pack(pady=3, padx=25)
        if self.config_actual.get("sharepoint_url"):
            self.entry_sp.insert(0, self.config_actual["sharepoint_url"])

        # Botón para añadir nuevo proyecto acumulativamente
        frame_cargar = tk.Frame(self.root, bg="#f8fafc")
        frame_cargar.pack(fill="x", padx=25, pady=8)

        btn_cargar = tk.Button(frame_cargar, text="📁 1. Añadir Fotos de un Proyecto (Carpeta Local)", command=self.agregar_proyecto_carpeta, 
                               font=("Arial", 10, "bold"), bg="#0056b3", fg="white", padx=10, pady=8, cursor="hand2")
        btn_cargar.pack(side="left")

        lbl_info_cargar = tk.Label(frame_cargar, text="Suma puntos sin borrar lo anterior", font=("Arial", 8, "italic"), bg="#f8fafc", fg="#64748b")
        lbl_info_cargar.pack(side="left", padx=10)

        # Listado de proyectos detectados en memoria con checkboxes
        lbl_lista = tk.Label(self.root, text="☑️ Proyectos en memoria (Marca los que deseas EXPORTAR al mapa final):", font=("Arial", 9, "bold"), bg="#f8fafc", fg="#334155", anchor="w")
        lbl_lista.pack(fill="x", padx=25, pady=(5, 2))

        # Contenedor con scroll para los proyectos
        frame_canvas = tk.Frame(self.root, bg="white", bd=1, relief="solid")
        frame_canvas.pack(fill="both", expand=True, padx=25, pady=5)

        self.canvas = tk.Canvas(frame_canvas, bg="white", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(frame_canvas, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Botones de selección rápida
        frame_acciones_lista = tk.Frame(self.root, bg="#f8fafc")
        frame_acciones_lista.pack(fill="x", padx=25, pady=2)

        tk.Button(frame_acciones_lista, text="Marcar Todos", command=self.marcar_todos, font=("Arial", 8), bg="#e2e8f0", fg="#334155", cursor="hand2").pack(side="left")
        tk.Button(frame_acciones_lista, text="Desmarcar Todos", command=self.desmarcar_todos, font=("Arial", 8), bg="#e2e8f0", fg="#334155", cursor="hand2").pack(side="left", padx=5)

        # Botón 2: Guardar GeoJSON final con la selección de casillas
        btn_guardar = tk.Button(self.root, text="⚙️ 2. Generar y Guardar 'datos.geojson' Final", command=self.guardar_geojson_final, 
                                 font=("Arial", 10, "bold"), bg="#0284c7", fg="white", padx=10, pady=8, cursor="hand2")
        btn_guardar.pack(fill="x", padx=25, pady=8)

        # Botón 3: Desplegar a GitHub
        btn_git = tk.Button(self.root, text="🚀 3. Subir Cambios a GitHub (Desplegar Web)", command=self.desplegar_github, 
                            font=("Arial", 10, "bold"), bg="#16a34a", fg="white", padx=10, pady=8, cursor="hand2")
        btn_git.pack(fill="x", padx=25, pady=2)

        # Estado
        self.lbl_estado = tk.Label(self.root, text="Listo. Añade proyectos o gestiona los puntos existentes.", font=("Arial", 9), bg="#f8fafc", fg="#64748b", justify="center")
        self.lbl_estado.pack(pady=8)

    def actualizar_lista_proyectos(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        resumen_proyectos = {}
        for feature in self.all_features:
            proj = feature.get("properties", {}).get("proyecto", "Desconocido")
            resumen_proyectos[proj] = resumen_proyectos.get(proj, 0) + 1

        if not resumen_proyectos:
            lbl = tk.Label(self.scrollable_frame, text="No hay proyectos en memoria actualmente.", bg="white", fg="#94a3b8", font=("Arial", 9))
            lbl.pack(padx=10, pady=10)
            self.lbl_estado.config(text="Catálogo vacío. Añade fotos de algún proyecto.", fg="#64748b")
            return

        for proj, count in sorted(resumen_proyectos.items()):
            var = tk.BooleanVar(value=True)
            texto_chk = f"📁 {proj}  ({count} puntos geolocalizados)"
            
            chk = tk.Checkbutton(self.scrollable_frame, text=texto_chk, variable=var, bg="white", font=("Arial", 10), anchor="w", cursor="hand2")
            chk.pack(fill="x", padx=10, pady=3)
            self.checkbox_vars[proj] = var

        self.lbl_estado.config(text=f"Catálogo cargado: {len(resumen_proyectos)} proyectos en memoria ({len(self.all_features)} puntos totales).", fg="#0056b3")

    def marcar_todos(self):
        for var in self.checkbox_vars.values():
            var.set(True)

    def desmarcar_todos(self):
        for var in self.checkbox_vars.values():
            var.set(False)

    def agregar_proyecto_carpeta(self):
        sp_base_url = self.entry_sp.get().strip()
        if not sp_base_url:
            messagebox.showerror("Dato requerido", "Por favor, introduce la URL base de SharePoint.")
            return

        guardar_config(sp_base_url)
        if not sp_base_url.endswith('/'):
            sp_base_url += '/'

        ruta_proyecto = filedialog.askdirectory(title="Selecciona la carpeta local del proyecto a añadir")
        if not ruta_proyecto:
            return

        nombre_proyecto = os.path.basename(os.path.normpath(ruta_proyecto))

        self.lbl_estado.config(text=f"⏳ Leyendo metadatos de [{nombre_proyecto}]...", fg="#0056b3")
        self.root.update()

        nuevas_features = []
        contador = 0

        for root_dir, dirs, files in os.walk(ruta_proyecto):
            rel_path = os.path.relpath(root_dir, ruta_proyecto)
            
            if rel_path == ".":
                rel_subpath = ""
            else:
                partes = os.path.normpath(rel_path).split(os.sep)
                rel_subpath = "/".join(partes)

            for file in files:
                if not file.lower().endswith(('.jpg', '.jpeg', '.heic')):
                    continue

                ruta_origen = os.path.join(root_dir, file)
                lat, lon, fecha, azimuth = obtener_datos_exif(ruta_origen, file)

                if lat is not None and lon is not None:
                    if rel_subpath:
                        ruta_relativa_archivo = f"{nombre_proyecto}/{rel_subpath}/{file}"
                    else:
                        ruta_relativa_archivo = f"{nombre_proyecto}/{file}"
                    
                    ruta_codificada = urllib.parse.quote(ruta_relativa_archivo, safe='/')
                    imagen_url = sp_base_url + ruta_codificada

                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": {
                            "nombre_archivo": file,
                            "proyecto": nombre_proyecto,
                            "origen": rel_subpath if rel_subpath else "General",
                            "fecha": fecha or "Desconocida",
                            "imagen_url": imagen_url,
                            "azimuth": azimuth
                        }
                    }
                    nuevas_features.append(feature)
                    contador += 1

        self.all_features = [
            f for f in self.all_features 
            if f["properties"].get("proyecto") != nombre_proyecto
        ] + nuevas_features

        self.actualizar_lista_proyectos()
        messagebox.showinfo("Proyecto Añadido", f"Se han cargado {contador} imágenes de '{nombre_proyecto}' al catálogo en memoria.\n(Las fotos sin metadatos EXIF han extraído su fecha del nombre del archivo automáticamente).")

    def guardar_geojson_final(self):
        proyectos_marcados = [proj for proj, var in self.checkbox_vars.items() if var.get()]

        features_a_exportar = [
            f for f in self.all_features
            if f["properties"].get("proyecto") in proyectos_marcados
        ]

        geojson_data = {
            "type": "FeatureCollection",
            "features": features_a_exportar
        }

        with open(GEOJSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=4)

        self.lbl_estado.config(text=f"✅ 'datos.geojson' guardado con {len(features_a_exportar)} puntos de {len(proyectos_marcados)} proyectos.", fg="#16a34a")
        messagebox.showinfo("GeoJSON Guardado", f"Se han exportado {len(features_a_exportar)} puntos al archivo 'datos.geojson'.\nLos proyectos desmarcados se han omitido del mapa final.")

    def desplegar_github(self):
        try:
            self.lbl_estado.config(text="🚀 Subiendo cambios a GitHub...", fg="#0056b3")
            self.root.update()

            if not os.path.exists(os.path.join(BASE_DIR, ".git")):
                messagebox.showerror("Error", "No se encuentra el repositorio Git en este directorio.")
                self.lbl_estado.config(text="❌ Falta repositorio Git.", fg="#ef4444")
                return

            subprocess.run([GIT_PATH, "add", "datos.geojson"], check=True, cwd=BASE_DIR)
            
            status = subprocess.run([GIT_PATH, "status", "--porcelain"], capture_output=True, text=True, cwd=BASE_DIR)
            if not status.stdout.strip():
                messagebox.showinfo("Sin cambios", "No hay cambios pendientes en datos.geojson para subir.")
                self.lbl_estado.config(text="ℹ️ El catálogo ya está actualizado en GitHub.", fg="#64748b")
                return

            subprocess.run([GIT_PATH, "commit", "-m", "Actualización de catálogo GIS desde app"], check=True, cwd=BASE_DIR)
            resultado_push = subprocess.run([GIT_PATH, "push"], capture_output=True, text=True, cwd=BASE_DIR, timeout=30)

            if resultado_push.returncode == 0:
                self.lbl_estado.config(text="✨ ¡Desplegado en GitHub con éxito!", fg="#16a34a")
                messagebox.showinfo("Despliegue Completado", "Los cambios se han subido a GitHub correctamente. Cloudflare actualizará la web.")
            else:
                raise Exception(resultado_push.stderr)

        except Exception as e:
            messagebox.showerror("Error de Despliegue", f"No se pudo completar el push a GitHub:\n{e}")
            self.lbl_estado.config(text="❌ Error al subir a GitHub.", fg="#ef4444")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGestorGISPro(root)
    root.mainloop()