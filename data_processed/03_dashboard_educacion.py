# %%
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import unicodedata
import os

# --- 1. PATH CONFIGURATION ---
BASE_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
IMG_DIR = os.path.join(BASE_DIR, "images", "CENSO2024")

# --- 2. DATA LOADING ---
try:
    df_educ = pd.read_csv(os.path.join(DATA_DIR, "resumen_educacion.csv"))
    df_ingles = pd.read_csv(os.path.join(DATA_DIR, "resumen_ingles.csv"))
    
    # Detección automática de columnas para evitar KeyError
    col_depto = 'Dept_Name' if 'Dept_Name' in df_ingles.columns else 'Nombre_Depto'
    col_educ = 'Education_Level' if 'Education_Level' in df_educ.columns else 'Nivel_Educativo'
    col_count = 'Count' if 'Count' in df_educ.columns else 'Conteo'

except FileNotFoundError as e:
    print(f"❌ ERROR: CSV files not found. {e}")
    exit()

# --- 3. MAP GEOMETRY ---
url_mapa = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SLV_1.json"
gdf_mapa = gpd.read_file(url_mapa)

def normalizar(texto):
    if not isinstance(texto, str): return "SIN_DATO"
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').upper().replace(" ", "").strip()

df_ingles['match_key'] = df_ingles[col_depto].apply(normalizar)
gdf_mapa['match_key'] = gdf_mapa['NAME_1'].apply(normalizar)
mapa_final = gdf_mapa.merge(df_ingles, on='match_key', how='left')

# --- 4. VISUALIZATION ---
fig = plt.figure(figsize=(24, 14), facecolor='white')

# === A) MAP (English Proficiency) ===
ax1 = fig.add_axes([0.02, 0.05, 0.65, 0.88]) 
mapa_final.plot(column='Pct_Ingles', cmap='Blues', linewidth=0.8, ax=ax1, edgecolor='black')

for idx, row in mapa_final.iterrows():
    centroid = row['geometry'].representative_point()
    pct = row['Pct_Ingles']
    if pd.notna(pct):
        label_text = f"{row[col_depto]}\n{pct:.1f}%"
        ax1.annotate(text=label_text, xy=(centroid.x, centroid.y), ha='center', 
                     fontsize=10, fontweight='bold', color='black',
                     path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])

ax1.set_title("ENGLISH PROFICIENCY BY DEPARTMENT (Ages 4+)", fontsize=18, fontweight='bold', pad=10)
ax1.axis('off')

# === B) STACKED BAR CHART (Education Levels) ===
# Traducción interna para que la leyenda salga en inglés sin importar el CSV
educ_map = {
    'Ninguno': 'None', 'Inicial': 'Preschool', 'Básica': 'Elementary/Middle',
    'Media': 'High School', 'Superior': 'Higher Education', 'Especial': 'Special Ed',
    'Ignorado': 'Ignored'
}
df_educ_plot = df_educ.copy()
df_educ_plot[col_educ] = df_educ_plot[col_educ].replace(educ_map)

# Pivotar datos
df_pivot = df_educ_plot.pivot(index=col_depto, columns=col_educ, values=col_count).fillna(0)

# Orden lógico de las columnas (Colores)
order = ['None', 'Preschool', 'Elementary/Middle', 'High School', 'Higher Education', 'Special Ed', 'Ignored']
df_pivot = df_pivot[[c for c in order if c in df_pivot.columns]]

# Calcular Porcentajes
df_pivot_pct = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100

# --- LÓGICA DE ORDENAMIENTO (Ranking) ---
# Ordenamos por 'Higher Education' ascendente.
# Al graficar barh, el último valor queda ARRIBA visualmente.
if 'Higher Education' in df_pivot_pct.columns:
    df_pivot_pct = df_pivot_pct.sort_values(by='Higher Education', ascending=True)
# ----------------------------------------

ax2 = fig.add_axes([0.70, 0.45, 0.25, 0.40])
df_pivot_pct.plot(kind='barh', stacked=True, ax=ax2, colormap='viridis', edgecolor='white', linewidth=0.5)

ax2.set_title("EDUCATIONAL ATTAINMENT (%)\n(Sorted by Higher Ed)", fontsize=15, fontweight='bold')
ax2.set_xlabel("Percentage", fontsize=11)
ax2.set_ylabel("")
ax2.legend(title="Level", bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=3, fontsize=10)

# === C) SUMMARY BOX ===
ax3 = fig.add_axes([0.70, 0.10, 0.25, 0.25])
total_pob_4 = df_ingles['Poblacion_4plus'].sum()
total_eng = df_ingles['Hablantes_Ingles'].sum()
avg_eng = (total_eng / total_pob_4) * 100

# Ajuste fino de coordenadas de texto para evitar solapamiento
ax3.text(0.5, 0.55, f"{avg_eng:.1f}%", fontsize=50, fontweight='bold', ha='center', color='#2b6cb0')
ax3.text(0.5, 0.25, "National English\nProficiency Average", fontsize=14, ha='center', fontweight='bold')
ax3.text(0.5, 0.10, f"Total Speakers: {total_eng/1e3:.1f}K", fontsize=12, ha='center', color='gray')
ax3.axis('off')

plt.suptitle('HUMAN CAPITAL DASHBOARD: EDUCATION & LANGUAGES (2024)', fontsize=28, fontweight='bold', y=0.97)

# --- 5. SAVING ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)
save_path = os.path.join(IMG_DIR, "dashboard_education_en.png")
fig.savefig(save_path, dpi=400, bbox_inches='tight')

print(f"✅ Dashboard saved in: {save_path}")
plt.show()