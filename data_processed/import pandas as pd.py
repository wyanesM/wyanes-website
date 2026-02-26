import pandas as pd

# Ruta al archivo GIGANTE
file_path = r"Z:\CENSO_2024\Bases-Finales-CPV2024SV-CSV\BasedeDatosdePoblacionCPV2024SV.csv"

print("🕵️‍♂️ Buscando variables de Vivienda y Tecnología...")

# Leemos solo los encabezados (0 filas) para ser instantáneo
df_head = pd.read_csv(file_path, nrows=0)
todas_las_cols = df_head.columns.tolist()

# Palabras clave a buscar
keywords = ['INTERNET', 'WIFI', 'CONEXION', # Tecnología
            'COMPU', 'ORDENADOR', 'LAPTOP', 'TABLET', # Dispositivos
            'CELULAR', 'TELEFONO', # Comunicación
            'AGUA', 'CAÑERIA', 'GRIFO', # Servicios
            'LUZ', 'ELECTRICIDAD', 'ALUMBRADO', # Energía
            'PISO', 'PARED', 'TECHO'] # Materiales

print(f"\n--- COLUMNAS ENCONTRADAS ({len(todas_las_cols)} total) ---")

encontradas = []
for col in todas_las_cols:
    for key in keywords:
        if key in col.upper():
            encontradas.append(col)
            break # Si ya encontró una keyword, pasa a la siguiente columna

# Imprimimos bonito
for col in encontradas:
    print(f" -> {col}")

if not encontradas:
    print("❌ No encontré nada obvio. Quizás usan códigos como V01, H05, etc.")
    print("Aquí te van las primeras 50 columnas para que veas el patrón:")
    print(todas_las_cols[:50])