# %%
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import FuncFormatter
import seaborn as sns
import unicodedata

# --- 1. CARGA ULTRARÁPIDA ---
try:
    df_mapa_data = pd.read_csv("data_processed/resumen_deptos.csv")
    df_edad_data = pd.read_csv("data_processed/resumen_edades.csv")
    print("✅ Datos cargados del caché local.")
except FileNotFoundError:
    print("❌ ALERTA: No encuentro los archivos en 'data_processed/'. Corre primero el script 01.")
    exit()

# Cálculos al vuelo
df_mapa_data['Pct_Mujeres'] = (df_mapa_data['Mujeres'] / df_mapa_data['Poblacion']) * 100
df_mapa_data['Pct_Hombres'] = (df_mapa_data['Hombres'] / df_mapa_data['Poblacion']) * 100
total_pais = df_mapa_data['Poblacion'].sum()

# --- 2. GEOMETRÍA DEL MAPA ---
print("🗺️ Descargando mapa...")
url_mapa = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SLV_1.json"
gdf_mapa = gpd.read_file(url_mapa)

def normalizar(texto):
    if not isinstance(texto, str): return "SIN_DATO"
    return unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8').upper().replace(" ", "").strip()

df_mapa_data['match_key'] = df_mapa_data['Nombre_Depto'].apply(normalizar)
gdf_mapa['match_key'] = gdf_mapa['NAME_1'].apply(normalizar)
mapa_final = gdf_mapa.merge(df_mapa_data, on='match_key', how='left')

# --- 3. VISUALIZACIÓN ---
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
        ax1.annotate(text=label_text, xy=(centroid.x, centroid.y), xytext=(0, 0), textcoords="offset points", 
                     fontsize=6.5, fontweight='bold', ha='center', color='black',
                     path_effects=[pe.withStroke(linewidth=1.5, foreground="white")])

ax1.text(x=0.05, y=0.05, transform=ax1.transAxes, s=f"POBLACIÓN TOTAL\n{total_pais/1e6:.2f} Millones",
         fontsize=16, fontweight='bold', color='white', ha='left',
         bbox=dict(facecolor='#d62728', alpha=0.9, boxstyle='round,pad=0.8'))
ax1.set_title("DISTRIBUCIÓN GEOGRÁFICA", fontsize=14, fontweight='bold', color='#333')
ax1.axis('off')

# === B) DONA (SEPARANDO ETIQUETAS) ===
ax2 = fig.add_axes([0.72, 0.58, 0.22, 0.22]) 

wedges, texts, autotexts = ax2.pie(
    [df_mapa_data['Hombres'].sum(), df_mapa_data['Mujeres'].sum()], 
    labels=['Hombres', 'Mujeres'], 
    autopct='%1.1f%%', 
    startangle=90, 
    colors=['#4A90E2', '#E94E77'], 
    pctdistance=0.80, 
    explode=(0.03, 0.03),
    labeldistance=1.15  # <--- ESTO SEPARA LAS ETIQUETAS DE LA DONA
)
ax2.add_artist(plt.Circle((0,0),0.65,fc='white'))
ax2.set_title("DISTRIBUCIÓN POR SEXO", fontsize=12, fontweight='bold', pad=20) # Aumenté el pad para dar espacio
plt.setp(autotexts, size=9, weight="bold", color="black")
plt.setp(texts, size=13, weight="bold")

# === C) HISTOGRAMA (CON LÍNEA PROMEDIO) ===
ax3 = fig.add_axes([0.72, 0.10, 0.22, 0.25])

sns.barplot(data=df_edad_data, x='Edad', y='Frecuencia', color='#2ecc71', edgecolor='white', ax=ax3)

# CÁLCULO DEL PROMEDIO PONDERADO
# (Edad * Cantidad de personas) / Total de personas
promedio_edad = (df_edad_data['Edad'] * df_edad_data['Frecuencia']).sum() / df_edad_data['Frecuencia'].sum()

# DIBUJAR LA LÍNEA VERTICAL
ax3.axvline(x=promedio_edad, color='red', linestyle='--', linewidth=2, label=f'Promedio: {promedio_edad:.1f} años')
ax3.legend(loc='upper right', fontsize=10) # Mostrar la leyenda del promedio

# Ajustes de Ejes
ax3.set_xticks(range(0, 100, 10)) 
ax3.set_xticklabels(range(0, 100, 10))
def thousands_formatter(x, pos): return f'{x*1e-3:.0f}K'
ax3.yaxis.set_major_formatter(FuncFormatter(thousands_formatter))

ax3.set_title("DISTRIBUCIÓN POR EDAD", fontsize=12, fontweight='bold')
ax3.set_xlabel("Edad (Años)")
ax3.set_ylabel("Habitantes")
ax3.grid(axis='y', linestyle=':', alpha=0.4)

plt.suptitle('DASHBOARD DEMOGRÁFICO: CENSO EL SALVADOR 2024', fontsize=20, fontweight='bold', y=0.95)
plt.show()