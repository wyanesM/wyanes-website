# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 1. CONFIGURACIÓN DE RUTAS ABSOLUTAS ---
WEB_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage"
# Ruta donde el Script 01 guarda los CSV
DATA_DIR = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"
# Carpeta organizada para las imágenes del proyecto
IMG_DIR = os.path.join(WEB_DIR, "images", "CENSO2024")

# --- 2. CARGA Y LIMPIEZA ---
try:
    path_tic = os.path.join(DATA_DIR, "resumen_tic_completo.csv")
    df_tic = pd.read_csv(path_tic)
    
    # === DETECCIÓN AUTOMÁTICA DE COLUMNA DE POBLACIÓN ===
    # Buscamos nombres comunes para evitar el KeyError
    posibles_nombres = ['Poblacion_10plus', 'Poblacion', 'Total', 'Pob_10_mas']
    col_pob = next((c for c in posibles_nombres if c in df_tic.columns), None)
    
    if col_pob:
        pob_total_tic = df_tic[col_pob].sum()
        print(f"✅ Datos cargados. Población analizada: {pob_total_tic/1e6:.2f}M")
    else:
        print("⚠️ Advertencia: No se encontró columna de población, pero continuando con el dashboard...")
        
except FileNotFoundError:
    print(f"❌ ERROR: No se encuentra el CSV en {DATA_DIR}")
    exit()

# Limpieza de seguridad
df_tic = df_tic.dropna(subset=['Nombre_Depto'])
df_tic['Nombre_Depto'] = df_tic['Nombre_Depto'].astype(str)
df_tic = df_tic[~df_tic['Nombre_Depto'].isin(['DESCONOCIDO', 'Ignorado', 'nan'])]
df_tic = df_tic.sort_values('Pct_Internet', ascending=True)

# --- 3. PREPARACIÓN PARA SEABORN ---
cols_mostrar = ['Pct_Internet', 'Pct_Smartphone', 'Pct_Laptop', 'Pct_PC_Escritorio', 'Pct_Tablet']
df_plot = df_tic.melt(id_vars='Nombre_Depto', value_vars=cols_mostrar, 
                      var_name='Dispositivo', value_name='Porcentaje')

# Limpiar nombres de leyenda
df_plot['Dispositivo'] = df_plot['Dispositivo'].str.replace('Pct_', '').str.replace('_', ' ')

# --- 4. VISUALIZACIÓN ---
fig, ax = plt.subplots(figsize=(12, 8))
sns.set_style("whitegrid")

# Paleta de colores consistente
palette = {"Internet": "#3498db", "Smartphone": "#2ecc71", "Laptop": "#e74c3c", 
           "PC Escritorio": "#f39c12", "Tablet": "#9b59b6"}

# Dibujar líneas guía horizontales
ax.hlines(y=df_tic['Nombre_Depto'], xmin=0, xmax=100, color='gray', alpha=0.1, linestyles='--')

# Dibujar los puntos
sns.scatterplot(data=df_plot, x='Porcentaje', y='Nombre_Depto', hue='Dispositivo', 
                palette=palette, s=120, zorder=3, edgecolor='black', alpha=0.8, ax=ax)

# Etiquetas de datos simplificadas (Smartphone y Laptop)
for i, (idx, row) in enumerate(df_tic.iterrows()):
    ax.text(row['Pct_Smartphone'] + 1.5, i, f"{row['Pct_Smartphone']:.0f}%", 
            va='center', fontsize=8, color='#27ae60', fontweight='bold')
    ax.text(row['Pct_Laptop'] - 1.5, i, f"{row['Pct_Laptop']:.0f}%", 
            va='center', ha='right', fontsize=8, color='#c0392b', fontweight='bold')

# Formato final
plt.title("ADOPCIÓN TECNOLÓGICA: EL SALVADOR 2024", fontsize=15, fontweight='bold', pad=15)
plt.xlabel("Porcentaje de la Población (> 10 años)", fontsize=10)
plt.ylabel("") 
plt.xlim(-5, 105)

# Leyenda compacta
plt.legend(title="Dispositivo", loc='upper center', bbox_to_anchor=(0.5, -0.1), 
            ncol=5, fontsize=9, title_fontsize=9, frameon=True)

plt.figtext(0.5, 0.92, "Comparación del uso de dispositivos digitales por departamento", 
            ha="center", fontsize=10, color="#7f8c8d")

plt.tight_layout()

# --- 5. GUARDADO ORGANIZADO ---
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

save_path = os.path.join(IMG_DIR, "dashboard_digital.png")
fig.savefig(save_path, dpi=300, bbox_inches='tight')
print(f"✅ Dashboard Digital guardado en:\n{save_path}")

plt.show()