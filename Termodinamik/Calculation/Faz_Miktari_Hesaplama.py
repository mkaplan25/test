# Revised version using fallback average molar masses for key phases like BCC_A2 and CEMENTITE
# if eq.X.sel(...) fails.


from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

print("\\n🧪 Fe Tabanlı Alaşımlar için Faz Denge Hesaplayıcı")

# === Kullanıcıdan giriş ===
n = int(input("🔢 Kaç element gireceksiniz? (En az 2, örn: FE-C): "))
elements = []
wt_percents = {}

for i in range(n):
    el = input(f"🧪 {i+1}. elementin sembolü (örn: FE, C, CR): ").strip().upper()
    wt = float(input(f"💠 {el} oranı (% ağırlıkça): ")) / 100
    elements.append(el)
    wt_percents[el] = wt

if 'FE' not in elements:
    print("⚠️ FE elementi zorunludur.")
    exit()

total_wt = sum(wt_percents.values())
if abs(total_wt - 1.0) > 1e-3:
    print("⚠️ Ağırlık oranlarının toplamı %100 olmalı.")
    exit()

T_C = float(input("🌡️ Sıcaklık (°C): "))
pressure=float(input("Basınç (Pa): "))

# === Molar kütleler ===
M = {
    'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938,
    'MO': 95.95, 'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999,
    'P': 30.9738, 'PD': 106.42, 'S': 32.065, 'SI': 28.0855, 'TA': 180.9479,
    'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

try:
    mols = {el: wt_percents[el] / M[el] for el in elements}
except KeyError as e:
    print(f"❌ Tanımsız molar kütle: {e}")
    exit()

total_mol = sum(mols.values())
mol_fracs = {el: mols[el] / total_mol for el in elements}

# Veritabanını yükle
import os
import sys

if getattr(sys, 'frozen', False):
    # PyInstaller bundle içinde çalışıyor
    base_path = sys._MEIPASS
    tdb_path = os.path.join(base_path, "FeC.tdb")
else:
    # Normal Python çalışıyor - bir üst klasörde ara
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    tdb_path = os.path.join(parent_dir, "FeC.tdb")
db = Database(tdb_path)

exclude = ['GRAPHITE', 'DIAMOND_A4', 'FC_MONO', 'H_BCC', 'SPINEL', 'CORUND', 'SIO2', 'O1_GAS']
phases = [ph for ph in db.phases.keys() if ph not in exclude]

phase_map = {
    'BCC_A2': 'Ferrit (α)', 'FCC_A1': 'Ostenit (γ)', 'CEMENTITE': 'Sementit (Fe₃C)',
    'LIQUID': 'Sıvı', 'SIGMA': 'Sigma Fazı', 'BCC_B2': 'Sementit (Fe₃C)',
    'M23C6': 'M23C6 Karbürü', 'M7C3': 'M7C3 Karbürü', 'M3C2': 'M3C2 Karbürü',
    'MU_PHASE': 'Mu Fazı', 'LAVES_PHASE': 'Laves Fazı', 'CHI_A12': 'Chi Fazı',
    'G_PHASE': 'G Fazı', 'ETA_CARB': 'Eta Karbür', 'K_CARB': 'K Karbür', 'KSI_CARBIDE': 'Ksi Karbür'
}

components = elements + ['VA']
conds = {v.T: T_C + 273.15, v.P: 101325, v.N: 1}
for el in elements:
    if el != 'FE':
        conds[v.X(el)] = mol_fracs[el]

eq = equilibrium(db, components, phases, conds)

phases_out = eq.Phase.values.ravel()
fractions_out = eq.NP.values.ravel()

components_in_eq = eq.X.coords['component'].values
phase_list = []
weight_list = []

for i, (pname, frac) in enumerate(zip(phases_out, fractions_out)):
    if isinstance(pname, str) and not np.isnan(frac):
        try:
            xvals = eq.X.sel(phase=pname).values[0, 0, 0, 0]
            avg_mw = sum(xval * M.get(comp, 0) for xval, comp in zip(xvals, components_in_eq))
        except:
            if pname == "CEMENTITE":
                avg_mw = 179.546
            elif pname in ["BCC_A2", "FCC_A1"]:
                avg_mw = 55.845
            else:
                avg_mw = 60.0
        phase_list.append(phase_map.get(pname, pname))
        weight_list.append(frac * avg_mw)

df = pd.DataFrame({'Phase': phase_list, 'Weight': weight_list})
df = df.groupby('Phase').sum().reset_index()
total_weight = df['Weight'].sum()
df['Weight Fraction (%)'] = (df['Weight'] / total_weight * 100).round(2)

print(f"\\n✅ {T_C:.1f}°C'de denge fazları (ağırlıkça):")
if not df.empty:
    print(df[['Phase', 'Weight Fraction (%)']].to_string(index=False))
else:
    print("⚠️ Geçerli faz bulunamadı.")

# Grafik
if not df.empty:
    plt.figure(figsize=(7, 7))
    plt.pie(df['Weight Fraction (%)'], labels=df['Phase'], autopct="%1.1f%%", startangle=140)
    plt.title(f"Fe Tabanlı Alaşım @ {T_C:.1f}°C (Ağırlıkça Faz Dağılımı)")
    plt.axis('equal')
    plt.tight_layout()
    plt.show()
