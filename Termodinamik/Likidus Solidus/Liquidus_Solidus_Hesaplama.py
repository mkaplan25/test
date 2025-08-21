from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

# 🔹 Veritabanını yükle
db = Database(r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb")
phases = list(db.phases.keys())

# 🔹 Molar kütleler (g/mol)
M = {
        'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

# 🔹 Kullanıcıdan element sayısı ve isimlerini al
num_elements = int(input("Kaç element (Fe hariç) gireceksiniz? "))
elements = []
weights = {}
total_wt = 0

for i in range(num_elements):
    el = input(f"{i+1}. elementin adını girin (örn: C, MN, CR): ").strip().upper()
    if el not in M:
        print(f"{el} için molar kütle tanımı eksik!")
        continue
    wt = float(input(f"{el} için ağırlıkça yüzde değeri girin: "))
    elements.append(el)
    weights[el] = wt / 100
    total_wt += wt / 100

weights['FE'] = 1.0 - total_wt
if weights['FE'] < 0:
    raise ValueError("Toplam ağırlık oranı %100'ü aşamaz.")

# 🔹 Mol fraksiyonları hesapla
n = {el: weights[el] / M[el] for el in weights}
total_mol = sum(n.values())
X = {el: n[el] / total_mol for el in n}

# 🔹 PyCalphad kompozisyonu
components = list(set(elements + ['FE']))
composition = {v.X(el): X[el] for el in elements if el != 'FE'}

# 🔹 Solidus / Likidus fonksiyonu
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

# 🔹 Solidus / Likidus hesapla
solidus, liquidus = get_liquidus_solidus(db, components, phases, composition)


solidus_c = solidus - 273.15 if solidus else None
liquidus_c = liquidus - 273.15 if liquidus else None

print(f"\n✅ Belirlenen bileşim için:\n• Solidus: {solidus_c:.2f} °C\n• Liquidus: {liquidus_c:.2f} °C")




# 🔹 Kullanıcıya eksen tercihi sor
x_mode = input("X ekseni için 'mol' mu yoksa 'agirlik' mı? ").strip().lower()
y_mode = input("Y ekseni için 'kelvin' mi yoksa 'celsius' mu? ").strip().lower()

if y_mode == 'celsius':
    solidus -= 273.15
    liquidus -= 273.15

# 🔹 Grafik çizimi
fig, ax = plt.subplots(figsize=(10, 5))
colors = ['black', 'purple', 'blue', 'orange', 'green', 'red']

for idx, el in enumerate(elements):
    if x_mode == 'mol':
        x_val = X[el]
    else:
        x_val = weights[el] * 100

    ax.axvline(x_val, color=colors[idx % len(colors)], linestyle='--', label=f'{el} {x_mode} oranı')
    ax.plot(x_val, solidus, 'ro')
    ax.plot(x_val, liquidus, 'go')

ax.set_title("Mol/Ağırlık Oranına Göre Solidus ve Liquidus Noktaları")
ax.set_xlabel("Mol Fraksiyonu" if x_mode == 'mol' else "Ağırlıkça %")
ax.set_ylabel("Sıcaklık (K)" if y_mode == 'kelvin' else "Sıcaklık (°C)")
ax.grid(True)
ax.legend()
plt.tight_layout()
plt.show()
