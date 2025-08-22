from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# 🔹 Veritabanı ve molar kütleler
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

phases = list(db.phases.keys())
M = {
        'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

# 🔹 Kullanıcıdan element seçimi
el = input("İncelenecek alaşım elementini girin (örn: C, MN, CR): ").strip().upper()
if el not in M or el == 'FE':
    raise ValueError("Geçerli bir alaşım elementi giriniz (Fe hariç).")

# 🔹 Ayarlar
min_wt = float(input(f"Min % {el} değeri (örn: 0): "))
max_wt = float(input(f"Max % {el} değeri (örn: 3): "))
step = float(input("Adım aralığı (örn: 0.2): "))

wt_values = np.arange(min_wt, max_wt + step, step)
solidus_list = []
liquidus_list = []

# 🔹 Hesap fonksiyonu
def get_liquidus_solidus(db, comps, phases, composition):
    temps = np.linspace(1000, 2000, 200)
    solidus_temp = None
    liquidus_temp = None
    for temp in temps:
        try:
            eq = equilibrium(db, comps, phases, {**composition, v.T: temp, v.P: 101325})
        except:
            continue
        eq_phases = eq.Phase.values.squeeze()
        eq_np = eq.NP.values.squeeze()
        if 'LIQUID' in eq_phases:
            liq_idx = np.where(eq_phases == 'LIQUID')[0][0]
            liq_frac = eq_np[liq_idx]
            if solidus_temp is None and liq_frac > 0:
                solidus_temp = temp
            if liq_frac >= 0.99:
                liquidus_temp = temp
                break
    return solidus_temp, liquidus_temp

# 🔹 Her % oran için hesapla
for wt in wt_values:
    wt_frac = wt / 100
    wt_fe = 1.0 - wt_frac
    if wt_fe < 0:
        solidus_list.append(None)
        liquidus_list.append(None)
        continue

    # Mol fraksiyonuna çevir
    n_el = wt_frac / M[el]
    n_fe = wt_fe / M['FE']
    total_mol = n_el + n_fe
    x_el = n_el / total_mol

    # PyCalphad kompozisyonu
    comps = ['FE', el]
    composition = {v.X(el): x_el}

    solidus, liquidus = get_liquidus_solidus(db, comps, phases, composition)
    solidus_list.append(solidus - 273.15 if solidus else None)
    liquidus_list.append(liquidus - 273.15 if liquidus else None)

# 🔹 Grafik çizimi
plt.figure(figsize=(10, 6))
plt.plot(wt_values, solidus_list, 'r-o', label='Solidus (°C)')
plt.plot(wt_values, liquidus_list, 'g-o', label='Liquidus (°C)')
plt.title(f"{el} oranının Solidus / Liquidus sıcaklığına etkisi")
plt.xlabel(f"{el} Ağırlıkça %")
plt.ylabel("Sıcaklık (°C)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
