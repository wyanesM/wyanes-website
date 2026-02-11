# %% 
import pandas as pd
import os

# --- CONFIGURACIÓN ---
# Ruta al archivo GIGANTE
file_path = r"Z:\CENSO_2024\Bases-Finales-CPV2024SV-CSV\BasedeDatosdePoblacionCPV2024SV.csv"
output_folder = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"

# Crear carpeta si no existe
os.makedirs(output_folder, exist_ok=True)

# --- 1. CARGA DE DATOS ---
print("⏳ Cargando el dataset maestro (Esto puede tardar)...")
try:
    df_censo = pd.read_csv(file_path)
    print(f"✅ Datos cargados: {len(df_censo):,} registros.")
except FileNotFoundError:
    print(f"❌ ERROR: No encuentro el archivo en {file_path}")
    print("Asegurate de estar conectado al servidor o tener el archivo local.")
    exit()

# --- 2. PROCESAMIENTO: DEMOGRAFÍA (Mapa y Dona) ---
print("⚙️ Procesando Demografía...")

def calc_stats(x):
    total = x['COD_PER'].count()
    # Asumiendo 1=Hombre, 2=Mujer (Verifica tu diccionario)
    mujeres = x[x['P02_2_SEXO'] == 2]['COD_PER'].count()
    hombres = x[x['P02_2_SEXO'] == 1]['COD_PER'].count()
    return pd.Series({'Poblacion': total, 'Mujeres': mujeres, 'Hombres': hombres})

# Agrupar por Departamento
df_deptos = df_censo.groupby('DEPTO').apply(calc_stats).reset_index()

# Agregar Nombres de Departamentos (Para que ya vaya limpio)
codigos_deptos = {
    1: "Ahuachapán", 2: "SantaAna", 3: "Sonsonate", 4: "Chalatenango", 
    5: "LaLibertad", 6: "San Salvador", 7: "Cuscatlán", 8: "LaPaz", 
    9: "Cabañas", 10: "SanVicente", 11: "Usulután", 12: "SanMiguel", 
    13: "Morazán", 14: "LaUnión"
}
df_deptos['Nombre_Depto'] = df_deptos['DEPTO'].map(codigos_deptos)

# --- 3. PROCESAMIENTO: EDADES (Histograma) ---
print("⚙️ Procesando Edades...")
# Solo contamos cuánta gente tiene cada edad (0 años: 50k, 1 año: 48k...)
df_edades = df_censo['P02_3_EDAD'].value_counts().reset_index()
df_edades.columns = ['Edad', 'Frecuencia']
# Limpieza básica de errores (solo números)
df_edades['Edad'] = pd.to_numeric(df_edades['Edad'], errors='coerce')
df_edades = df_edades.dropna().sort_values('Edad')

# --- 4. EXPORTAR DATOS LIGEROS ---
print("💾 Guardando archivos optimizados...")

df_deptos.to_csv(f"{output_folder}/resumen_deptos.csv", index=False)
df_edades.to_csv(f"{output_folder}/resumen_edades.csv", index=False)

print("🚀 ¡LISTO! Archivos generados en folder 'data_processed'.")
print("Ahora puedes correr el script de visualización instantáneamente.")

# ==========================================
# --- NUEVO MÓDULO: EDUCACIÓN E IDIOMA (LÓGICA FINAL) ---
# ==========================================
print("⚙️ Procesando Módulo de Educación...")

# 1. Definir la Función basada en la IMAGEN P10_1_GRADO_APROBADO
def clasificar_nivel(valor):
    try:
        c = int(valor)
    except:
        return "Ignorado"

    # --- LÓGICA EXACTA SEGÚN TU DICCIONARIO ---
    if c == 0:
        return "Ninguno"        # Código 0
    elif 1 <= c <= 3:
        return "Inicial"        # Códigos 1, 2, 3 (Parvularia)
    elif 4 <= c <= 9:
        return "Especial"       # Códigos 4 al 9 (Educación Especial)
    elif 11 <= c <= 19:
        return "Básica"         # Códigos 11 al 19 (1° a 9° Grado)
    elif 21 <= c <= 29:
        return "Media"          # Códigos 21 al 24 (Bachillerato)
    elif c >= 30:
        return "Superior"       # Series 30 (Técnico), 40 (Univ), 50 (Maestría), 60 (Doctorado)
    else:
        return "Ignorado"

# 2. Filtrar y Limpiar
# Forzamos numérico en EDAD
df_censo['P02_3_EDAD'] = pd.to_numeric(df_censo['P02_3_EDAD'], errors='coerce')
# IMPORTANTE: Filtrar niños muy pequeños para no inflar "Ninguno"
df_educ = df_censo[df_censo['P02_3_EDAD'] >= 4].copy()

# 3. Aplicar la clasificación
col_grado = pd.to_numeric(df_educ['P10_1_GRADO_APROBADO'], errors='coerce').fillna(-1)
df_educ['Nivel_Educativo'] = col_grado.apply(clasificar_nivel)

# 4. Calcular Idioma Inglés
col_ingles = pd.to_numeric(df_educ['P12_3_A_ENG'], errors='coerce')
df_educ['Habla_Ingles'] = (col_ingles == 1).astype(int)

# 5. Generar Tabla Resumen 1: Educación
resumen_educacion = df_educ.groupby(['DEPTO', 'Nivel_Educativo']).size().reset_index(name='Conteo')
resumen_educacion['Nombre_Depto'] = resumen_educacion['DEPTO'].map(codigos_deptos)

# 6. Generar Tabla Resumen 2: Inglés
resumen_ingles = df_educ.groupby('DEPTO').agg(
    Poblacion_4plus=('COD_PER', 'count'),
    Hablantes_Ingles=('Habla_Ingles', 'sum')
).reset_index()

resumen_ingles['Pct_Ingles'] = (resumen_ingles['Hablantes_Ingles'] / resumen_ingles['Poblacion_4plus']) * 100
resumen_ingles['Nombre_Depto'] = resumen_ingles['DEPTO'].map(codigos_deptos)

# --- GUARDAR (Con utf-8-sig para las tildes) ---
print("💾 Guardando archivos de Educación Corregidos...")
resumen_educacion.to_csv(f"{output_folder}/resumen_educacion.csv", index=False, encoding='utf-8-sig')
resumen_ingles.to_csv(f"{output_folder}/resumen_ingles.csv", index=False, encoding='utf-8-sig')

# ==========================================
# --- MÓDULO: BRECHA DIGITAL COMPLETO ---
# ==========================================
print("⚙️ Procesando todas las variables TIC...")

# 1. Filtramos población > 10 años
df_tic = df_censo[pd.to_numeric(df_censo['P02_3_EDAD'], errors='coerce') >= 10].copy()

# 2. Función de limpieza (1=Sí, resto=0)
def limpiar_tic(columna):
    return (pd.to_numeric(columna, errors='coerce') == 1).astype(int)

# Procesamos todas las variables de tus imágenes
df_tic['Usa_PC']         = limpiar_tic(df_tic['P14_1_USO_TIC_PC'])
df_tic['Usa_Laptop']     = limpiar_tic(df_tic['P14_2_USO_TIC_LAPTOP'])
df_tic['Usa_Tablet']     = limpiar_tic(df_tic['P14_3_USO_TIC_TABLET'])
df_tic['Usa_Smartphone'] = limpiar_tic(df_tic['P14_4_USO_TIC_SMARTPHONE'])
df_tic['Usa_Cel_Basico'] = limpiar_tic(df_tic['P14_5_USO_TIC_CEL'])
df_tic['Usa_Internet']   = limpiar_tic(df_tic['P14_6_USO_TIC_INTERNET'])

# 3. Generar Tabla Resumen por Departamento
resumen_tic = df_tic.groupby('DEPTO').agg(
    Total_Pob=('COD_PER', 'count'),
    Internet=('Usa_Internet', 'sum'),
    Smartphone=('Usa_Smartphone', 'sum'),
    Laptop=('Usa_Laptop', 'sum'),
    PC_Escritorio=('Usa_PC', 'sum'),
    Tablet=('Usa_Tablet', 'sum'),
    Cel_Basico=('Usa_Cel_Basico', 'sum')
).reset_index()

# 4. Calcular Porcentajes
cols_tic = ['Internet', 'Smartphone', 'Laptop', 'PC_Escritorio', 'Tablet', 'Cel_Basico']
for col in cols_tic:
    resumen_tic[f'Pct_{col}'] = (resumen_tic[col] / resumen_tic['Total_Pob']) * 100

resumen_tic['Nombre_Depto'] = resumen_tic['DEPTO'].map(codigos_deptos)

# Guardar
resumen_tic.to_csv(f"{output_folder}/resumen_tic_completo.csv", index=False, encoding='utf-8-sig')