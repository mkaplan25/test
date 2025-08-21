from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

# 🆕 Otomatik faz yöneticisi import
from Termodinamik.Phase_Configurator import get_phases_for_calculation

# 📌 Kullanıcıdan alınacak:
element_x = input("Demir ile alaşım yapmak istediğiniz elementi girin (örnek: C, CR, MN): ").strip().upper()
wt_x = float(input(f"Ağırlıkça %{element_x} miktarını girin: ")) / 100
T_start = float(input("Başlangıç sıcaklığı (°C): "))
T_end = float(input("Bitiş sıcaklığı (°C): "))
pressure= float(input("Basınç değerini girin (Pa): "))

# 🔍 Molar kütleler
MOLAR_MASSES = {
    'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

if element_x not in MOLAR_MASSES:
    print(f"{element_x} için molar kütle tanımlı değil. Lütfen kodda `MOLAR_MASSES` sözlüğüne ekleyin.")
    exit()

M_FE = MOLAR_MASSES['FE']
M_X = MOLAR_MASSES[element_x]

# 🎯 Mol kesirine dönüştür
mol_x = wt_x / M_X
mol_fe = (1 - wt_x) / M_FE
x_x = mol_x / (mol_x + mol_fe)

n_points = int(input("Kaç noktada hesaplama yapılsın (ör. 100): "))  # Daha hassas çözüm için artırıldı
temps = np.linspace(T_start, T_end, n_points)

# 📚 Veritabanı
tdb_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"
dbf = Database(tdb_path)

components = ['FE', element_x, 'VA']
#phases = list(dbf.phases.keys())

phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)

# 🔍 CEMENTITE veya GRAPHITE var mı kontrolü
if 'CEMENTITE' in phases:
    selected_phase = 'CEMENTITE'
elif 'GRAPHITE' in phases:
    selected_phase = 'GRAPHITE'
else:
    selected_phase = None

# 🔧 Faz oranlarını tut
phase_fractions = {}

for T in temps:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            eq = equilibrium(dbf, components, phases, {
                v.T: T + 273.15,
                v.P: 101325,
                v.X(element_x): x_x,
                v.N: 1
            })

            names = eq.Phase.values[0, 0, 0, 0]
            fracs = eq.NP.values[0, 0, 0, 0]

            for name, frac in zip(names, fracs):
                if isinstance(name, str):
                    if name not in phase_fractions:
                        phase_fractions[name] = []
                    phase_fractions[name].append((T, frac))
    except:
        continue

# 📌 Geçiş noktalarını tespit et (fark analizi ile)
def detect_phase_transitions(fractions, epsilon=1e-3):
    transitions = {}
    for phase, data in fractions.items():
        data_sorted = sorted(data, key=lambda x: x[0])
        T_vals, F_vals = zip(*data_sorted)
        F_vals = np.array(F_vals)
        dF = np.gradient(F_vals)
        for i in range(1, len(dF)):
            if (F_vals[i-1] < epsilon and F_vals[i] >= epsilon):
                transitions.setdefault(phase, []).append((T_vals[i], 'ortaya çıktı', F_vals[i]))
            elif (F_vals[i-1] >= epsilon and F_vals[i] < epsilon):
                transitions.setdefault(phase, []).append((T_vals[i], 'kayboldu', F_vals[i]))
    return transitions

transitions = detect_phase_transitions(phase_fractions)

print("\n🔍 Faz Geçiş Noktaları:")
if transitions:
    for phase, events in transitions.items():
        for T, desc, frac in events:
            print(f"- {T:.2f} °C - {phase} {desc}")
else:
    print("Geçiş noktası bulunamadı.")

# 📈 Grafik çizimi
plt.figure(figsize=(12, 6))
colors = {}

for phase, values in phase_fractions.items():
    if not values or all(f[1] == 0.0 for f in values):
        continue
    T_vals, F_vals = zip(*values)
    F_vals = np.array(F_vals)
    if max(F_vals) > 1e-5:
        label = phase
        if phase == 'GRAPHITE' and selected_phase == 'CEMENTITE':
            label = 'CEMENTITE'
        line, = plt.plot(T_vals, F_vals, label=label)
        colors[label] = line.get_color()

# 📍 Geçiş noktalarını faz çizgisine metin olarak yerleştir
for phase, events in transitions.items():
    label = phase
    if phase == 'GRAPHITE' and selected_phase == 'CEMENTITE':
        label = 'CEMENTITE'
    data_dict = dict(phase_fractions.get(phase, []))
    for T, desc, frac in events:
        y_val = data_dict.get(T, frac)
        plt.axvline(x=T, color=colors.get(label, 'gray'), linestyle='--', alpha=0.6)
        plt.text(T + 5, y_val, f"{T:.1f}°C - {label} {desc}", rotation=90, fontsize=8, va='bottom', ha='left')

plt.xlabel("Sıcaklık (°C)")
plt.ylabel("Faz Oranı")
plt.title(f"Fe–{element_x} Alaşımı (%{wt_x*100:.1f} {element_x}) İçin Faz Dönüşümleri")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
