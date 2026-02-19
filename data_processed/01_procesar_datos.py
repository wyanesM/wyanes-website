# %% 
import pandas as pd
import os

# --- CONFIGURATION ---
# Path to the MASTER file
file_path = r"Z:\CENSO_2024\Bases-Finales-CPV2024SV-CSV\BasedeDatosdePoblacionCPV2024SV.csv"
output_folder = r"C:\Users\wyane\OneDrive\Escritorio\WebPage\data_processed\CENSO"

# Create folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# --- 1. DATA LOADING ---
print("⏳ Loading master dataset (This may take a while)...")
try:
    df_censo = pd.read_csv(file_path)
    print(f"✅ Data loaded: {len(df_censo):,} records.")
except FileNotFoundError:
    print(f"❌ ERROR: File not found at {file_path}")
    print("Ensure you are connected to the server or have the file locally.")
    exit()

# --- 2. PROCESSING: DEMOGRAPHICS (Map & Pie Chart) ---
print("⚙️ Processing Demographics...")

def calc_stats(x):
    total = x['COD_PER'].count()
    # 1=Male, 2=Female
    females = x[x['P02_2_SEXO'] == 2]['COD_PER'].count()
    males = x[x['P02_2_SEXO'] == 1]['COD_PER'].count()
    return pd.Series({'Population': total, 'Females': females, 'Males': males})

# Group by Department
df_deptos = df_censo.groupby('DEPTO').apply(calc_stats).reset_index()

# Department Mapping
dept_codes = {
    1: "Ahuachapán", 2: "Santa Ana", 3: "Sonsonate", 4: "Chalatenango", 
    5: "La Libertad", 6: "San Salvador", 7: "Cuscatlán", 8: "La Paz", 
    9: "Cabañas", 10: "San Vicente", 11: "Usulután", 12: "San Miguel", 
    13: "Morazán", 14: "La Unión"
}
df_deptos['Dept_Name'] = df_deptos['DEPTO'].map(dept_codes)

# --- 3. PROCESSING: AGES (Histogram) ---
print("⚙️ Processing Ages...")
df_edades = df_censo['P02_3_EDAD'].value_counts().reset_index()
df_edades.columns = ['Age', 'Frequency']
df_edades['Age'] = pd.to_numeric(df_edades['Age'], errors='coerce')
df_edades = df_edades.dropna().sort_values('Age')

# --- 4. EXPORT LIGHTWEIGHT DATA ---
print("💾 Saving optimized files...")
df_deptos.to_csv(f"{output_folder}/resumen_deptos.csv", index=False)
df_edades.to_csv(f"{output_folder}/resumen_edades.csv", index=False)

# ==========================================
# --- MODULE: EDUCATION & LANGUAGE ---
# ==========================================
print("⚙️ Processing Education Module...")

def classify_level(value):
    try:
        c = int(value)
    except:
        return "Unknown"

    if c == 0:
        return "None"
    elif 1 <= c <= 3:
        return "Preschool"
    elif 4 <= c <= 9:
        return "Special Ed"
    elif 11 <= c <= 19:
        return "Elementary/Middle"
    elif 21 <= c <= 29:
        return "High School"
    elif c >= 30:
        return "Higher Education" # Technical, Univ, Masters, PhD
    else:
        return "Unknown"

# Filtering (Ages 4+)
df_censo['P02_3_EDAD'] = pd.to_numeric(df_censo['P02_3_EDAD'], errors='coerce')
df_educ = df_censo[df_censo['P02_3_EDAD'] >= 4].copy()

# Apply classification
col_grado = pd.to_numeric(df_educ['P10_1_GRADO_APROBADO'], errors='coerce').fillna(-1)
df_educ['Education_Level'] = col_grado.apply(classify_level)

# English Language Proficiency
col_ingles = pd.to_numeric(df_educ['P12_3_A_ENG'], errors='coerce')
df_educ['Speaks_English'] = (col_ingles == 1).astype(int)

# Summary 1: Education
resumen_educacion = df_educ.groupby(['DEPTO', 'Education_Level']).size().reset_index(name='Count')
resumen_educacion['Dept_Name'] = resumen_educacion['DEPTO'].map(dept_codes)

# Summary 2: English
resumen_ingles = df_educ.groupby('DEPTO').agg(
    Population_4plus=('COD_PER', 'count'),
    English_Speakers=('Speaks_English', 'sum')
).reset_index()

resumen_ingles['Pct_English'] = (resumen_ingles['English_Speakers'] / resumen_ingles['Population_4plus']) * 100
resumen_ingles['Dept_Name'] = resumen_ingles['DEPTO'].map(dept_codes)

print("💾 Saving Education files...")
resumen_educacion.to_csv(f"{output_folder}/resumen_educacion.csv", index=False, encoding='utf-8-sig')
resumen_ingles.to_csv(f"{output_folder}/resumen_ingles.csv", index=False, encoding='utf-8-sig')

# ==========================================
# --- MODULE: DIGITAL DIVIDE (ICT) ---
# ==========================================
print("⚙️ Processing ICT variables...")

# Filtering (Ages 10+)
df_tic = df_censo[pd.to_numeric(df_censo['P02_3_EDAD'], errors='coerce') >= 10].copy()

def clean_tic(col):
    return (pd.to_numeric(col, errors='coerce') == 1).astype(int)

df_tic['Uses_PC']          = clean_tic(df_tic['P14_1_USO_TIC_PC'])
df_tic['Uses_Laptop']      = clean_tic(df_tic['P14_2_USO_TIC_LAPTOP'])
df_tic['Uses_Tablet']      = clean_tic(df_tic['P14_3_USO_TIC_TABLET'])
df_tic['Uses_Smartphone']  = clean_tic(df_tic['P14_4_USO_TIC_SMARTPHONE'])
df_tic['Uses_Basic_Cell']  = clean_tic(df_tic['P14_5_USO_TIC_CEL'])
df_tic['Uses_Internet']    = clean_tic(df_tic['P14_6_USO_TIC_INTERNET'])

# Summary Table
resumen_tic = df_tic.groupby('DEPTO').agg(
    Total_Pop=('COD_PER', 'count'),
    Internet=('Uses_Internet', 'sum'),
    Smartphone=('Uses_Smartphone', 'sum'),
    Laptop=('Uses_Laptop', 'sum'),
    Desktop_PC=('Uses_PC', 'sum'),
    Tablet=('Uses_Tablet', 'sum'),
    Basic_Cell=('Uses_Basic_Cell', 'sum')
).reset_index()

# Calculate Percentages
cols_tic = ['Internet', 'Smartphone', 'Laptop', 'Desktop_PC', 'Tablet', 'Basic_Cell']
for col in cols_tic:
    resumen_tic[f'Pct_{col}'] = (resumen_tic[col] / resumen_tic['Total_Pop']) * 100

resumen_tic['Dept_Name'] = resumen_tic['DEPTO'].map(dept_codes)

# Final Save
resumen_tic.to_csv(f"{output_folder}/resumen_tic_completo.csv", index=False, encoding='utf-8-sig')
print("🚀 DONE! All English-formatted CSVs generated in 'data_processed'.")