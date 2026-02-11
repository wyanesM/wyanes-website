# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter
import os

# --- 1. CONFIGURACIÓN DE RUTAS ABSOLUTAS ---
BASE_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
# Ruta donde el Script 01 guarda los CSV
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
# Ruta organizada para imágenes del proyecto
IMG_DIR = os.path.join(BASE_DIR, "images", "CENSO2024")

# --- 2. CARGA DE DATOS ---
try:
    path_edu = os.path.join(DATA_DIR, "resumen_educacion.csv")
    path_eng = os.path.join(DATA_DIR, "resumen_ingles.csv")
    
    df_edu = pd.read_csv(path_edu)
    df_eng = pd.read_csv(path_eng)
    
    # Capturamos totales nacionales ANTES de limpiar para no perder precisión
    pob_total_ingles = df_eng['Poblacion_4plus'].sum()
    hablantes_total = df_eng['Hablantes_Ingles'].sum()
    
    print(f"✅ Datos cargados. Población analizada (>4 años): {pob_total_ingles/1e6:.2f}M")
except FileNotFoundError as e:
    print(f"❌ ERROR: No se encuentran los archivos en {DATA_DIR}. {e}")
    exit()

# --- 3. LIMPIEZA ---
# Eliminamos registros sin departamento asignado ('Ignorado' o nulos)
basura = ['DESCONOCIDO', 'Ignorado', 'nan']
df_edu = df_edu.dropna(subset=['Nombre_Depto'])
df_eng = df_eng.dropna(subset=['Nombre_Depto'])

df_edu = df_edu[~df_edu['Nombre_Depto'].astype(str).isin(basura)]
df_eng = df_eng[~df_eng['Nombre_Depto'].astype(str).isin(basura)]

df_edu['Nombre_Depto'] = df_edu['Nombre_Depto'].astype(str)
df_eng['Nombre_Depto'] = df_eng['Nombre_Depto'].astype(str)

# --- 4. PREPARACIÓN DE DATOS ---
df_pivot = df_edu.pivot(index='Nombre_Depto', columns='Nivel_Educativo', values='Conteo').fillna(0)

orden_niveles = ['Ninguno', 'Inicial', 'Especial', 'Básica', 'Media', 'Superior', 'Ignorado']
cols_existentes = [c for c in orden_niveles if c in df_pivot.columns]
df_pivot = df_pivot[cols_existentes]
df_pct = df_pivot.div(df_pivot.sum(axis=1), axis=0) * 100

# Ordenamiento por prioridad (Superior primero)
prioridad_orden = ['Superior', 'Media', 'Básica', 'Inicial', 'Ninguno']
cols_sort = [c for c in prioridad_orden if c in df_pct.columns]
df_pct = df_pct.sort_values(by=cols_sort, ascending=True)

# Sincronizar Inglés al mismo orden
df_eng = df_eng.set_index('Nombre_Depto').reindex(df_pct.index).fillna(0)

# --- 5. VISUALIZACIÓN ---
fig = plt.figure(figsize=(20, 11))

colores_edu = {
    'Ninguno': '#e74c3c', 'Inicial': '#f1c40f', 'Especial': '#95a5a6',
    'Básica': '#3498db', 'Media': '#2980b9', 'Superior': '#2ecc71',
    'Ignorado': '#bdc3c7'
}
lista_colores = [colores_edu.get(c, '#333') for c in df_pct.columns]

ax1 = fig.add_axes([0.08, 0.15, 0.52, 0.72]) 
ax2 = fig.add_axes([0.65, 0.15, 0.28, 0.72])

# === A) GRÁFICO EDUCACIÓN ===
df_pct.plot(kind='barh', stacked=True, ax=ax1, color=lista_colores, edgecolor='white', width=0.8)
ax1.set_title("NIVEL EDUCATIVO ALCANZADO POR DEPARTAMENTO", fontsize=14, fontweight='bold', pad=15)
ax1.set_xlabel("Distribución de la Población (%)", fontsize=11)
ax1.set_ylabel("")
ax1.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f'{x:.0f}%'))

for c in ax1.containers:
    labels = [f'{v.get_width():.1f}%' if v.get_width() > 4 else '' for v in c]
    ax1.bar_label(c, labels=labels, label_type='center', fontsize=9, color='white', fontweight='bold')

ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=4, frameon=False, fontsize=10)

# === B) GRÁFICO INGLÉS ===
barras = ax2.barh(df_eng.index, df_eng['Pct_Ingles'], color='#8e44ad', edgecolor='white', height=0.6)
ax2.set_title("POBLACIÓN BILINGÜE (INGLÉS)", fontsize=14, fontweight='bold', pad=15)
ax2.set_xlabel("% Habla Inglés", fontsize=11)
ax2.set_yticks([]) 
ax2.set_xlim(0, df_eng['Pct_Ingles'].max() * 1.25)
ax2.bar_label(barras, fmt='%.1f%%', padding=5, fontsize=10, fontweight='bold', color='#8e44ad')

# Línea de promedio nacional basada en la cifra oficial real
if pob_total_ingles > 0:
    promedio_real = (hablantes_total / pob_total_ingles) * 100
    ax2.axvline(promedio_real, color='gray', linestyle='--', alpha=0.7)
    ax2.text(promedio_real, 1.02, f'Promedio Nacional: {promedio_real:.1f}%', color='gray', 
             fontsize=10, ha='center', transform=ax2.get_xaxis_transform())

plt.suptitle('RADIOGRAFÍA DE CAPITAL HUMANO: EL SALVADOR 2024', fontsize=22, fontweight='bold', y=0.97)

# --- 6. GUARDADO ORGANIZADO ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

save_path = os.path.join(IMG_DIR, "dashboard_educacion.png")
fig.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"✅ Dashboard de Educación guardado en:\n{save_path}")

plt.show()