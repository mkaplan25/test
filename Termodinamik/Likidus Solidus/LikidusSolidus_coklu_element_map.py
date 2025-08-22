from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings
from mpl_toolkits.mplot3d import Axes3D

warnings.filterwarnings('ignore')

# Veritabanı
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

# Molar kütleler
M = {
    'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

# Kullanıcıdan elementleri al
elements = []
while True:
    el = input("Alaşım elementini girin (örn: C, bitirmek için ENTER): ").strip().upper()
    if el == '':
        break
    if el in M and el != 'FE':
        elements.append(el)
    else:
        print("Geçersiz element veya Fe girilemez. Tekrar deneyin.")

if len(elements) < 2:
    raise ValueError("En az 2 alaşım elementi girilmelidir.")

# Kullanıcıdan eksen seçimleri al
print("\nSeçtiğiniz elementler:", elements)
el1 = input("X ekseninde hangi element olacak?: ").strip().upper()
el2 = input("Y ekseninde hangi element olacak?: ").strip().upper()

if el1 not in elements or el2 not in elements or el1 == el2:
    raise ValueError("Geçerli ve farklı iki element seçin.")

# Sabit elementlerin değerlerini al
fixed_elements = [el for el in elements if el != el1 and el != el2]
fixed_composition = {}
for el in fixed_elements:
    val = float(input(f"{el} sabit %: "))
    fixed_composition[el] = val / 100

# Aralıkları al
el1_min = float(input(f"{el1} min %: "))
el1_max = float(input(f"{el1} max %: "))
el2_min = float(input(f"{el2} min %: "))
el2_max = float(input(f"{el2} max %: "))
step = float(input("Adım aralığı (örn: 0.5): "))

# Grid oluştur
el1_vals = np.arange(el1_min, el1_max + step, step)
el2_vals = np.arange(el2_min, el2_max + step, step)
X_grid, Y_grid = np.meshgrid(el1_vals, el2_vals)

solidus_map = np.full_like(X_grid, np.nan, dtype=float)
liquidus_map = np.full_like(X_grid, np.nan, dtype=float)

# Hesap fonksiyonu
def get_liquidus_solidus(db, comps, phases, composition):
    temps = np.linspace(1000, 2000, 50)
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

# Grid üzerinde hesaplama
for i in range(X_grid.shape[0]):
    for j in range(X_grid.shape[1]):
        wt1 = X_grid[i, j] / 100
        wt2 = Y_grid[i, j] / 100
        wt_fixed = sum([fixed_composition[el] for el in fixed_composition])
        wt_fe = 1 - (wt1 + wt2 + wt_fixed)
        if wt_fe <= 0:
            continue

        n_el1 = wt1 / M[el1]
        n_el2 = wt2 / M[el2]
        n_fixed = sum([fixed_composition[el] / M[el] for el in fixed_composition])
        n_fe = wt_fe / M['FE']
        total_mol = n_el1 + n_el2 + n_fixed + n_fe

        composition = {v.X(el1): n_el1 / total_mol, v.X(el2): n_el2 / total_mol}
        for el in fixed_composition:
            composition[v.X(el)] = (fixed_composition[el] / M[el]) / total_mol

        comps = ['FE'] + elements

        solidus, liquidus = get_liquidus_solidus(db, comps, phases, composition)
        if solidus:
            solidus_map[i, j] = solidus - 273.15
        if liquidus:
            liquidus_map[i, j] = liquidus - 273.15

# 🔹 3D Grafik – Solidus
fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(121, projection='3d')
ax.plot_surface(X_grid, Y_grid, solidus_map, cmap='coolwarm')
ax.set_title('Solidus Sıcaklığı (°C)')
ax.set_xlabel(f'{el1} (%)')
ax.set_ylabel(f'{el2} (%)')
ax.set_zlabel('Sıcaklık (°C)')

# 🔹 3D Grafik – Liquidus
ax2 = fig.add_subplot(122, projection='3d')
ax2.plot_surface(X_grid, Y_grid, liquidus_map, cmap='viridis')
ax2.set_title('Liquidus Sıcaklığı (°C)')
ax2.set_xlabel(f'{el1} (%)')
ax2.set_ylabel(f'{el2} (%)')
ax2.set_zlabel('Sıcaklık (°C)')

plt.tight_layout()
plt.show()
