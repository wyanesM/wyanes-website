# %%
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import FuncFormatter
#import sns as sns # Asegúrate de usar import seaborn as sns si 'sns' da error
import seaborn as sns
import unicodedata
import os

# --- 1. PATH CONFIGURATION ---
BASE_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
IMG_DIR = os.path.join(BASE_DIR, "images", "CENSO2024")

# --- 2. DATA LOADING ---
try:
    df_mapa_data = pd.read_csv(os.path.join(DATA_DIR, "resumen_deptos.csv"))
    df_edad_data = pd.read_csv(os.path.join(DATA_DIR, "resumen_edades.csv"))
    total_pais_oficial = df_mapa_data['Poblacion'].sum()
except FileNotFoundError as e:
    print(f"❌ ERROR: {e}")
    exit()

# --- 3. CLEANING & CALCULATIONS ---
df_mapa_data.dropna(subset=['Nombre_Depto'], inplace=True)
df_mapa_data['Nombre_Depto'] = df_mapa_data['Nombre_Depto'].astype(str)

df_mapa_data['Pct_Mujeres'] = (df_mapa_data['Mujeres'] / df_mapa_data['Poblacion']) * 100
df_mapa_data['Pct_Hombres'] = (df_mapa_data['Hombres'] / df_mapa_data['Poblacion']) * 100

# --- 4. MAP GEOMETRY ---
url_mapa = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SLV_1.json"
gdf_mapa = gpd.read_file(url_mapa)

def normalizar(texto):
    if not isinstance(texto, str): return "NO_DATA"
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').upper().replace(" ", "").strip()

df_mapa_data['match_key'] = df_mapa_data['Nombre_Depto'].apply(normalizar)
gdf_mapa['match_key'] = gdf_mapa['NAME_1'].apply(normalizar)
mapa_final = gdf_mapa.merge(df_mapa_data, on='match_key', how='left')

# --- 5. HIGH-RESOLUTION VISUALIZATION ---
fig = plt.figure(figsize=(24, 14), facecolor='white')

# === A) MAP ===
ax1 = fig.add_axes([0.02, 0.05, 0.68, 0.88]) 
mapa_final.plot(column='Poblacion', cmap='OrRd', linewidth=0.8, ax=ax1, edgecolor='black')

for idx, row in mapa_final.iterrows():
    centroid = row['geometry'].representative_point()
    pob = row['Poblacion']
    if pd.notna(pob):
        txt_num = f"{pob/1e6:.1f}M" if pob >= 1e6 else f"{pob/1e3:.0f}K"
        # Etiquetas en inglés: M para Male, F para Female (o puedes dejar H/M si prefieres)
        label_text = f"{row['Nombre_Depto']}\n{txt_num}\nM:{row['Pct_Hombres']:.0f}% F:{row['Pct_Mujeres']:.0f}%"
        ax1.annotate(text=label_text, xy=(centroid.x, centroid.y), ha='center', 
                     fontsize=9.5, fontweight='bold', color='black',
                     path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])

# Cuadro de población total en inglés
ax1.text(x=0.05, y=0.05, transform=ax1.transAxes, s=f"TOTAL POPULATION\n{total_pais_oficial/1e6:.2f} Million",
         fontsize=20, fontweight='bold', color='white', 
         bbox=dict(facecolor='#d62728', alpha=0.9, boxstyle='round,pad=0.8'))
ax1.set_title("GEOGRAPHIC DISTRIBUTION", fontsize=18, fontweight='bold')
ax1.axis('off')

# === B) DONUT CHART (GENDER) ===
ax2 = fig.add_axes([0.74, 0.60, 0.22, 0.22]) 
ax2.pie([df_mapa_data['Hombres'].sum(), df_mapa_data['Mujeres'].sum()], 
        labels=['Male', 'Female'], autopct='%1.0f%%', startangle=90, 
        colors=['#4A90E2', '#E94E77'], pctdistance=0.75, explode=(0.04, 0.04),
        textprops={'fontsize': 15, 'fontweight': 'bold'})
ax2.add_artist(plt.Circle((0,0),0.60,fc='white'))
ax2.set_title("GENDER DISTRIBUTION", fontsize=16, fontweight='bold')

# === C) HISTOGRAM (AGE) ===
ax3 = fig.add_axes([0.74, 0.12, 0.22, 0.28])
sns.barplot(data=df_edad_data, x='Edad', y='Frecuencia', color='#2ecc71', ax=ax3)

promedio_edad = (df_edad_data['Edad'] * df_edad_data['Frecuencia']).sum() / df_edad_data['Frecuencia'].sum()
ax3.axvline(x=promedio_edad, color='red', linestyle='--', linewidth=3, label=f'Avg: {promedio_edad:.1f}')

ax3.legend(fontsize=12)
ax3.set_xticks(range(0, 101, 20)) 
ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x*1e-3:.0f}K'))
ax3.set_title("AGE STRUCTURE", fontsize=16, fontweight='bold')
ax3.set_xlabel("Age", fontsize=12)
ax3.set_ylabel("Frequency", fontsize=12)

# Título Principal
plt.suptitle('DEMOGRAPHIC DASHBOARD: 2024 EL SALVADOR CENSUS', fontsize=28, fontweight='bold', y=0.97)

# --- 6. SAVING ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)
save_path = os.path.join(IMG_DIR, "dashboard_population_en.png")
fig.savefig(save_path, dpi=400, bbox_inches='tight')
print(f"✅ English Dashboard saved at:\n{save_path}")

plt.show()