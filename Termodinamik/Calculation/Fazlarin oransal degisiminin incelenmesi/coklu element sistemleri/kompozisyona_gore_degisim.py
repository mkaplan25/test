from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings
from matplotlib import cm

# 🆕 Otomatik faz yöneticisi import
from Termodinamik.Phase_Configurator import get_phases_for_calculation


# 📌 Molar kütleler
M = {
    'FE': 55.845, 'C': 12.01, 'CR': 51.996, 'MN': 54.938, 'SI': 28.085,
    'MO': 95.95, 'V': 50.942, 'AL': 26.98, 'CU': 63.55, 'TI': 47.867,
    'NB': 92.91, 'W': 183.84
}

# 📌 Kullanıcıdan element bilgilerini al
num_elements = int(input("🔢 Kaç element eklemek istiyorsunuz? (FE otomatik eklenecek): "))
user_elements = []
for i in range(num_elements):
    el = input(f"🧪 {i+1}. Element adı (örn: C, MN): ").strip().upper()
    if el not in M:
        raise ValueError(f"❌ {el} için molar kütle tanımlı değil.")
    user_elements.append(el)

el_x = input("🧭 X ekseninde taranacak element (örn: C): ").strip().upper()
el_y = input("🧭 Y ekseninde taranacak element (örn: MN): ").strip().upper()
if el_x not in user_elements or el_y not in user_elements:
    raise ValueError("❌ X veya Y ekseninde verilen element, tanımlı elementlerden değil!")

fixed_elements = {}
for el in user_elements:
    if el == el_x or el == el_y:
        continue
    wt = float(input(f"🔒 Sabit {el} miktarı (wt%): ")) / 100
    fixed_elements[el] = wt

wt_min_x = float(input(f"🔽 {el_x} için min ağırlık%: ")) / 100
wt_max_x = float(input(f"🔼 {el_x} için max ağırlık%: ")) / 100
wt_min_y = float(input(f"🔽 {el_y} için min ağırlık%: ")) / 100
wt_max_y = float(input(f"🔼 {el_y} için max ağırlık%: ")) / 100
#step_count = int(input("🔢 Tarama adım sayısı (ör. 50): "))
step_count = 5
T_C = float(input("🌡️ Sabit sıcaklık (°C): "))
pressure=float(input("🌡️ Basınç (Pa): "))


# 📌 TDB ve fazlar
tdb_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"
dbf = Database(tdb_path)
components = ['FE'] + user_elements + ['VA']
#phases = [ph for ph in dbf.phases.keys() if ph not in ['GRAPHITE', 'DIAMOND_A4']]
phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)

# 📌 Tarama grid'i
wt_range_x = np.linspace(wt_min_x, wt_max_x, step_count)
wt_range_y = np.linspace(wt_min_y, wt_max_y, step_count)
X, Y = np.meshgrid(wt_range_x, wt_range_y)
Z_fractions = {ph: np.zeros_like(X) for ph in phases}

# 📌 Hesaplama döngüsü
for i in range(step_count):
    for j in range(step_count):
        wt_x = X[i, j]
        wt_y = Y[i, j]
        wt_dict = fixed_elements.copy()
        wt_dict[el_x] = wt_x
        wt_dict[el_y] = wt_y
        wt_fe = 1 - sum(wt_dict.values())
        if wt_fe <= 0:
            continue
        wt_dict['FE'] = wt_fe

        mols = {el: wt_dict[el] / M[el] for el in wt_dict}
        total_mol = sum(mols.values())
        x_dict = {el: mols[el] / total_mol for el in mols if el != 'FE'}

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                eq = equilibrium(dbf, components, phases, {
                    v.T: T_C + 273.15,
                    v.P: 101325,
                    v.N: 1,
                    **{v.X(el): x_dict[el] for el in x_dict}
                })

            names = eq.Phase.values.ravel()
            fracs = eq.NP.values.ravel()
            present = {name: float(frac) for name, frac in zip(names, fracs) if not np.isnan(frac)}

            for ph in Z_fractions:
                Z_fractions[ph][i, j] = present.get(ph, 0.0)

        except Exception as e:
            print(f"⚠️ Hata ({wt_x*100:.2f}%, {wt_y*100:.2f}%): {e}")
            continue

# 📊 Görselleştirme
for ph in Z_fractions:
    if np.max(Z_fractions[ph]) > 1e-5:  # 🎯 Daha düşük eşik ile CEMENTITE görünür olacak
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')
        surf = ax.plot_surface(X*100, Y*100, Z_fractions[ph], cmap=cm.viridis)
        ax.set_xlabel(f"{el_x} (wt%)")
        ax.set_ylabel(f"{el_y} (wt%)")
        ax.set_zlabel(f"{ph} Faz Oranı")
        ax.set_title(f"{T_C:.1f}°C - {ph} Fazı")
        fig.colorbar(surf, shrink=0.5, aspect=10)
        plt.tight_layout()
        plt.show()
