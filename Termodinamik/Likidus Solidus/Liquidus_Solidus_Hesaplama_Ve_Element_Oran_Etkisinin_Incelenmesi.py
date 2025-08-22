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

# 🔹 Kullanıcıdan bileşim al
num_elements = int(input("Kaç element (Fe hariç) gireceksiniz? "))
elements = []
weights = {}
total_wt = 0

for i in range(num_elements):
    el = input(f"{i+1}. elementin adını girin (örn: C, MN, CR): ").strip().upper()
    if el not in M or el == 'FE':
        print(f"{el} geçerli değil.")
        continue
    wt = float(input(f"{el} için ağırlıkça yüzde değeri girin: "))
    elements.append(el)
    weights[el] = wt / 100
    total_wt += wt / 100

weights['FE'] = 1.0 - total_wt
if weights['FE'] < 0:
    raise ValueError("Toplam ağırlık oranı %100'ü aşamaz.")

# 🔹 Mol fraksiyonları
n = {el: weights[el] / M[el] for el in weights}
total_mol = sum(n.values())
X = {el: n[el] / total_mol for el in n}

components = list(set(elements + ['FE']))
composition = {v.X(el): X[el] for el in elements if el != 'FE'}

# 🔹 Solidus / Liquidus hesap fonksiyonu
def get_liquidus_solidus(db, comps, phases, composition):
    temps = np.linspace(1000, 2500, 100)
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

# 🔹 Mevcut bileşim için hesapla
solidus, liquidus = get_liquidus_solidus(db, components, phases, composition)
solidus_c = solidus - 273.15 if solidus else None
liquidus_c = liquidus - 273.15 if liquidus else None

print(f"\n✅ Belirlenen bileşim için:\n• Solidus: {solidus_c:.2f} °C\n• Liquidus: {liquidus_c:.2f} °C")




# 🔹 Etki analizi başlasın
target_el = input(f"\nEtki analizini görmek istediğiniz elementi girin ({', '.join(elements)}): ").strip().upper()
if target_el not in elements:
    raise ValueError("Girilen element mevcut alaşımda yok.")

wt_current = weights[target_el] * 100
wt_range = np.linspace(max(0, wt_current - 1), wt_current + 1, 10)

solidus_list = []
liquidus_list = []

for wt in wt_range:
    wt_frac = wt / 100
    wt_fe = 1 - wt_frac - sum([weights[e] for e in weights if e not in ['FE', target_el]])
    if wt_fe < 0:
        solidus_list.append(None)
        liquidus_list.append(None)
        continue

    n_target = wt_frac / M[target_el]
    n_other = sum([(weights[e] / M[e]) for e in weights if e not in ['FE', target_el]])
    n_fe = wt_fe / M['FE']
    total_m = n_target + n_other + n_fe

    x_target = n_target / total_m
    composition_test = {v.X(e): X[e] for e in X if e not in ['FE', target_el]}
    composition_test[v.X(target_el)] = x_target

    solidus, liquidus = get_liquidus_solidus(db, components, phases, composition_test)
    solidus_list.append(solidus - 273.15 if solidus else None)
    liquidus_list.append(liquidus - 273.15 if liquidus else None)

# 🔹 Grafik
plt.figure(figsize=(10, 6))
plt.plot(wt_range, solidus_list, 'r-o', label='Solidus (°C)')
plt.plot(wt_range, liquidus_list, 'g-o', label='Liquidus (°C)')
plt.axvline(wt_current, color='gray', linestyle='--', label='Mevcut %')
plt.title(f"{target_el} oranının etkisi")
plt.xlabel(f"{target_el} Ağırlıkça %")
plt.ylabel("Sıcaklık (°C)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
