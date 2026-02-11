# %%
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import unicodedata
import os

# --- 1. CONFIGURACIÓN DE RUTAS ABSOLUTAS ---
BASE_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
# Ruta donde el Script 01 guarda los CSV
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
# Nueva ruta organizada para imágenes
IMG_DIR = os.path.join(BASE_DIR, "images", "CENSO2024")

# --- 2. CARGA DE DATOS ---
try:
    df_mapa_data = pd.read_csv(os.path.join(DATA_DIR, "resumen_deptos.csv"))
    df_edad_data = pd.read_csv(os.path.join(DATA_DIR, "resumen_edades.csv"))
    
    # === EL TRUCO PARA LOS 6.03M ===
    # Calculamos el total ANTES de limpiar los datos incompletos
    total_pais_oficial = df_mapa_data['Poblacion'].sum()
    
    print(f"✅ Datos cargados. Población Total Detectada: {total_pais_oficial/1e6:.2f}M")
except FileNotFoundError as e:
    print(f"❌ ERROR: No se encuentran los archivos en {DATA_DIR}. {e}")
    exit()

# --- 3. LIMPIEZA PARA EL MAPA ---
# Eliminamos los registros sin departamento para que Matplotlib no falle
df_mapa_data.dropna(subset=['Nombre_Depto'], inplace=True)
df_mapa_data['Nombre_Depto'] = df_mapa_data['Nombre_Depto'].astype(str)

# Cálculos por departamento
df_mapa_data['Pct_Mujeres'] = (df_mapa_data['Mujeres'] / df_mapa_data['Poblacion']) * 100
df_mapa_data['Pct_Hombres'] = (df_mapa_data['Hombres'] / df_mapa_data['Poblacion']) * 100

# --- 4. GEOMETRÍA DEL MAPA ---
print("🗺️ Descargando geometría...")
url_mapa = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SLV_1.json"
gdf_mapa = gpd.read_file(url_mapa)

def normalizar(texto):
    if not isinstance(texto, str): return "SIN_DATO"
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').upper().replace(" ", "").strip()

df_mapa_data['match_key'] = df_mapa_data['Nombre_Depto'].apply(normalizar)
gdf_mapa['match_key'] = gdf_mapa['NAME_1'].apply(normalizar)
mapa_final = gdf_mapa.merge(df_mapa_data, on='match_key', how='left')

# --- 5. VISUALIZACIÓN ---
fig = plt.figure(figsize=(20, 11))

# === A) MAPA ===
ax1 = fig.add_axes([0.02, 0.05, 0.65, 0.90]) 
mapa_final.plot(column='Poblacion', cmap='OrRd', linewidth=0.6, ax=ax1, edgecolor='black', legend=False)

for idx, row in mapa_final.iterrows():
    centroid = row['geometry'].representative_point()
    pob = row['Poblacion']
    if pd.notna(pob):
        txt_num = f"{pob/1e6:.1f}M" if pob >= 1e6 else f"{pob/1e3:.0f}K"
        label_text = f"{row['Nombre_Depto']}\n{txt_num}\nH:{row['Pct_Hombres']:.0f}% M:{row['Pct_Mujeres']:.0f}%"
        ax1.annotate(text=label_text, xy=(centroid.x, centroid.y), ha='center', fontsize=7, fontweight='bold',
                     path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

# USAMOS EL TOTAL OFICIAL (6.03M) AQUÍ
ax1.text(x=0.05, y=0.05, transform=ax1.transAxes, s=f"POBLACIÓN TOTAL\n{total_pais_oficial/1e6:.2f} Millones",
         fontsize=16, fontweight='bold', color='white', bbox=dict(facecolor='#d62728', alpha=0.9, boxstyle='round,pad=0.8'))
ax1.set_title("DISTRIBUCIÓN GEOGRÁFICA", fontsize=14, fontweight='bold')
ax1.axis('off')

# === B) DONA ===
ax2 = fig.add_axes([0.72, 0.58, 0.22, 0.22]) 
ax2.pie([df_mapa_data['Hombres'].sum(), df_mapa_data['Mujeres'].sum()], 
        labels=['Hombres', 'Mujeres'], autopct='%1.1f%%', startangle=90, 
        colors=['#4A90E2', '#E94E77'], pctdistance=0.75, explode=(0.03, 0.03))
ax2.add_artist(plt.Circle((0,0),0.60,fc='white'))
ax2.set_title("DISTRIBUCIÓN POR SEXO", fontsize=12, fontweight='bold')

# === C) HISTOGRAMA ===
ax3 = fig.add_axes([0.72, 0.10, 0.22, 0.25])
sns.barplot(data=df_edad_data, x='Edad', y='Frecuencia', color='#2ecc71', ax=ax3)
promedio_edad = (df_edad_data['Edad'] * df_edad_data['Frecuencia']).sum() / df_edad_data['Frecuencia'].sum()
ax3.axvline(x=promedio_edad, color='red', linestyle='--', linewidth=2, label=f'Prom: {promedio_edad:.1f}')
ax3.legend(fontsize=9)
ax3.set_xticks(range(0, 101, 20)) 
ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x*1e-3:.0f}K'))
ax3.set_title("DISTRIBUCIÓN POR EDAD", fontsize=12, fontweight='bold')

plt.suptitle('DASHBOARD DEMOGRÁFICO: CENSO EL SALVADOR 2024', fontsize=22, fontweight='bold', y=0.96)

# --- 6. GUARDADO ORGANIZADO ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

save_path = os.path.join(IMG_DIR, "dashboard_poblacion.png")
fig.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"✅ Dashboard guardado en:\n{save_path}")

plt.show()