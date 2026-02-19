# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 1. CONFIGURACIÓN DE RUTAS ---
WEB_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
IMG_DIR = os.path.join(WEB_DIR, "images", "CENSO2024")

# --- 2. CARGA Y LIMPIEZA ---
try:
    path_tic = os.path.join(DATA_DIR, "resumen_tic_completo.csv")
    df_tic = pd.read_csv(path_tic)
    
    # Detección de columna de población
    posibles_nombres = ['Poblacion_10plus', 'Total_Pob', 'Poblacion']
    col_pob = next((c for c in posibles_nombres if c in df_tic.columns), 'Total_Pob')
    
    if col_pob in df_tic.columns:
        print(f"✅ Data loaded. Population: {df_tic[col_pob].sum()/1e6:.2f}M")
        
except FileNotFoundError:
    print(f"❌ ERROR: CSV not found in {DATA_DIR}")
    exit()

df_tic = df_tic.dropna(subset=['Nombre_Depto'])
df_tic = df_tic.sort_values('Pct_Internet', ascending=True)

# --- 3. PREPARACIÓN PARA SEABORN (Melt) ---
cols_mostrar = ['Pct_Internet', 'Pct_Smartphone', 'Pct_Laptop'] # Agregamos las que necesites
df_plot = df_tic.melt(id_vars='Nombre_Depto', value_vars=cols_mostrar, 
                      var_name='Device', value_name='Percentage')

# Traducción de nombres en la leyenda
traduccion_dispositivos = {
    'Pct_Internet': 'Internet',
    'Pct_Smartphone': 'Smartphone',
    'Pct_Laptop': 'Laptop'
}
df_plot['Device'] = df_plot['Device'].map(traduccion_dispositivos)

# --- 4. VISUALIZACIÓN ---
fig, ax = plt.subplots(figsize=(14, 9), facecolor='white')
sns.set_style("whitegrid")

palette = {"Internet": "#3498db", "Smartphone": "#2ecc71", "Laptop": "#e74c3c"}

# Líneas guía
ax.hlines(y=df_tic['Nombre_Depto'], xmin=0, xmax=100, color='gray', alpha=0.1, linestyles='--')

# Puntos
sns.scatterplot(data=df_plot, x='Percentage', y='Nombre_Depto', hue='Device', 
                palette=palette, s=140, zorder=3, edgecolor='black', alpha=0.8, ax=ax)

# Etiquetas de datos (Smartphone y Laptop)
for i, (idx, row) in enumerate(df_tic.iterrows()):
    ax.text(row['Pct_Smartphone'] + 1.8, i, f"{row['Pct_Smartphone']:.0f}%", 
            va='center', fontsize=9, color='#27ae60', fontweight='bold')
    ax.text(row['Pct_Laptop'] - 1.8, i, f"{row['Pct_Laptop']:.0f}%", 
            va='center', ha='right', fontsize=9, color='#c0392b', fontweight='bold')

# Títulos en Inglés
plt.title("DIGITAL ADOPTION INDEX: EL SALVADOR 2024", fontsize=18, fontweight='bold', pad=20)
plt.xlabel("Percentage of Population (Ages 10+)", fontsize=12)
plt.ylabel("") 
plt.xlim(-5, 105)

plt.legend(title="Device / Service", loc='upper center', bbox_to_anchor=(0.5, -0.08), ncol=3)
plt.figtext(0.5, 0.94, "Comparison of digital device usage and connectivity by department", 
            ha="center", fontsize=12, color="#7f8c8d", style='italic')

plt.tight_layout()

# --- 5. GUARDADO ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)
save_path = os.path.join(IMG_DIR, "dashboard_digital_en.png")
fig.savefig(save_path, dpi=400, bbox_inches='tight')

print(f"✅ Digital Dashboard saved in: {save_path}")
plt.show()