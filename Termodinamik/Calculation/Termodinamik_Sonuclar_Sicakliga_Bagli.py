from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np

# 🔧 Molar kütleler (g/mol)
molar_weights = {
    'FE': 55.845, 'AL': 26.982, 'B': 10.81, 'C': 12.01, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.974, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.948, 'TI': 47.867, 'V': 50.942, 'W': 183.84, 'Y': 88.906
}

# 🔧 Kullanıcıdan kaç element seçeceği ve elementleri öğren
elements = ['FE', 'AL', 'B', 'C', 'CO', 'CR', 'CU', 'H', 'HF', 'LA', 'MN', 'MO', 'N', 'NB',
            'NI', 'O', 'P', 'PD', 'S', 'SI', 'TA', 'TI', 'V', 'W', 'Y']

print("Mevcut elementler:", ', '.join(elements[1:]))
num_elements = int(input("FE haricinde kaç element eklemek istiyorsunuz? (1-{}) ".format(len(elements) - 1)))

if num_elements < 1 or num_elements > len(elements) - 1:
    print("❌ Geçersiz sayı.")
    exit()

selected_elements = []
for i in range(num_elements):
    el = input(f"{i+1}. elementi seçin: ").strip().upper()
    if el not in elements[1:] or el in selected_elements:
        print("❌ Geçersiz veya tekrar eden element.")
        exit()
    selected_elements.append(el)

# 🔧 Kullanıcıdan ağırlıkça yüzdeleri al
wt = {}
wt_total = 0
for el in selected_elements:
    wt_val = float(input(f"{el} için ağırlıkça yüzde girin (%): "))
    wt[el] = wt_val
    wt_total += wt_val

# 🔧 Fe oranı kalan % ile hesaplanır
wt['FE'] = 100 - wt_total
if wt['FE'] < 0:
    print("❌ Toplam ağırlık %100'ü geçemez.")
    exit()

# 🔧 Seçilen element listesi (FE + seçilen elementler)
system_elements = ['FE'] + selected_elements

# 🔧 Mol oranları
mol = {}
total_mol = 0
for el in system_elements:
    mol[el] = wt[el] / molar_weights[el]
    total_mol += mol[el]

# 🔧 Normalize mol oranları
composition = {}
for el in selected_elements:
    composition[v.X(el)] = mol[el] / total_mol

# 🔧 Veritabanı yükleme
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

# 🔧 Tüm fazlar
phases = list(db.phases.keys())
temps = np.linspace(300, 1600, 100)

# 🔧 Hesaplamalar
gibbs_values = []
enthalpy_values = []
entropy_values = []
cp_values = []

for i, temp in enumerate(temps):
    eq = equilibrium(db, system_elements, phases, {**composition, v.T: temp, v.P: 101325})
    gibbs = eq.GM.values.squeeze()
    gibbs_values.append(gibbs)

    if i > 0:
        dG_dT = (gibbs_values[i] - gibbs_values[i - 1]) / (temps[i] - temps[i - 1])
        entropy = -dG_dT
    else:
        entropy = 0
    entropy_values.append(entropy)

    enthalpy = gibbs + temp * entropy
    enthalpy_values.append(enthalpy)

    if i > 0:
        dH_dT = (enthalpy_values[i] - enthalpy_values[i - 1]) / (temps[i] - temps[i - 1])
        cp = dH_dT
    else:
        cp = 0
    cp_values.append(cp)

# 🔧 Grafikler
plt.figure(figsize=(10, 5))
plt.plot(temps, gibbs_values, label='Gibbs Enerjisi (G)', color='blue')
plt.xlabel('Sıcaklık (K)')
plt.ylabel('G (J/mol)')
plt.title('Gibbs Enerjisi')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(temps, enthalpy_values, label='Entalpi (H)', color='red')
plt.xlabel('Sıcaklık (K)')
plt.ylabel('H (J/mol)')
plt.title('Entalpi')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(temps[1:], entropy_values[1:], label='Entropi (S)', color='green')
plt.xlabel('Sıcaklık (K)')
plt.ylabel('S (J/mol·K)')
plt.title('Entropi')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(10, 5))
plt.plot(temps[1:], cp_values[1:], label='Isıl Kapasite (Cp)', color='purple')
plt.xlabel('Sıcaklık (K)')
plt.ylabel('Cp (J/mol·K)')
plt.title('Isıl Kapasite')
plt.legend()
plt.grid()
plt.show()
