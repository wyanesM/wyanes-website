# %% 
import pandas as pd
import os

# --- CONFIGURACIÓN ---
# Ruta al archivo GIGANTE
file_path = r"Z:\CENSO_2024\Bases-Finales-CPV2024SV-CSV\BasedeDatosdePoblacionCPV2024SV.csv"
output_folder = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed"

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
# --- NUEVO MÓDULO: EDUCACIÓN E IDIOMA ---
# ==========================================
print("⚙️ Procesando Módulo de Educación...")

# 1. Definir el Mapeo de Códigos (Basado en tu imagen)
MAPA_EDUCACION_MACRO = {
    1: "Ninguno",
    2: "Inicial", 3: "Inicial",
    4: "Especial",
    5: "Básica", 6: "Básica",
    7: "Media",
    8: "Superior", 9: "Superior", 10: "Superior", 
    11: "Superior", 12: "Superior"
}

# 2. Filtrar población apta
# Excluimos a menores de 4 años para no sesgar la data de "Ninguno"
# (Asumimos que un niño de 2 años es normal que no tenga grado aprobado)
df_educ = df_censo[df_censo['P02_3_EDAD'] >= 4].copy()

# 3. Crear columna de Nivel Simplificado
df_educ['Nivel_Educativo'] = df_educ['P10_1_GRADO_APROBADO'].map(MAPA_EDUCACION_MACRO).fillna("Ignorado")

# 4. Calcular Idioma Inglés
# Asumimos 1 = Sí (Estándar en censos). Si el código fuera distinto, avísame.
df_educ['Habla_Ingles'] = df_educ['P12_3_A_ENG'].apply(lambda x: 1 if x == 1 else 0)

# 5. Generar Tabla Resumen 1: Nivel Educativo por Departamento
# Resultado: Ahuachapán | Básica | 5000 personas
resumen_educacion = df_educ.groupby(['DEPTO', 'Nivel_Educativo']).size().reset_index(name='Conteo')
resumen_educacion['Nombre_Depto'] = resumen_educacion['DEPTO'].map(codigos_deptos)

# 6. Generar Tabla Resumen 2: Inglés por Departamento
resumen_ingles = df_educ.groupby('DEPTO').agg(
    Poblacion_4plus=('COD_PER', 'count'),
    Hablantes_Ingles=('Habla_Ingles', 'sum')
).reset_index()

resumen_ingles['Pct_Ingles'] = (resumen_ingles['Hablantes_Ingles'] / resumen_ingles['Poblacion_4plus']) * 100
resumen_ingles['Nombre_Depto'] = resumen_ingles['DEPTO'].map(codigos_deptos)

# --- GUARDAR LOS NUEVOS ARCHIVOS ---
print("💾 Guardando archivos de Educación...")
resumen_educacion.to_csv(f"{output_folder}/resumen_educacion.csv", index=False)
resumen_ingles.to_csv(f"{output_folder}/resumen_ingles.csv", index=False)