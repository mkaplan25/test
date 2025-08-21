from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

# 🆕 Otomatik faz yöneticisi import
from Termodinamik.Phase_Configurator import get_phases_for_calculation
from diger.faz_diyagrami_cizimleri_diger.Ternary_Isothermal_Section_Original import pressure

# 📌 Veritabanını yükle
tdb_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"
dbf = Database(tdb_path)
all_elements = dbf.elements

# 📌 FE hariç elementleri listele
available_alloying = [el for el in all_elements if el != 'FE' and el != 'VA']

# 📌 Kullanıcıya seçim sun
print("\n✅ Mevcut Alaşım Elementleri (FE dışında):")
for el in available_alloying:
    print("-", el)

selected_element = input("\nİkincil elementi girin (örneğin: CR): ").upper()
if selected_element not in available_alloying:
    raise ValueError(f"{selected_element} elementi TDB dosyasında tanımlı değil.")

# 📌 Kullanıcı girişleri
T_input = float(input("Sıcaklığı girin (°C): "))
wt_min = float(input(f"Min %{selected_element} (ağırlıkça): "))
wt_max = float(input(f"Max %{selected_element} (ağırlıkça): "))
pressure= float(input("Basınç değerini girin (Pa): "))
# 📌 Molar kütleler (g/mol)
molar_masses = {
    'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
}

M_FE = molar_masses['FE']
M_X = molar_masses.get(selected_element, None)
if M_X is None:
    raise ValueError(f"{selected_element} için molar kütle tanımlanmadı. Lütfen ekleyin.")

# 📌 Yardımcı dönüşüm fonksiyonu
def wt_to_molfrac(wt_x):
    wt_x = wt_x / 100
    mol_x = wt_x / M_X
    mol_fe = (1 - wt_x) / M_FE
    return mol_x / (mol_x + mol_fe)

# 📌 Hesaplama noktaları
temps = T_input + 273.15
n_points = int(input("Kaç noktada hesaplama yapılsın (ör. 100): "))
wt_range = np.linspace(wt_min, wt_max, n_points)
mol_fracs = [wt_to_molfrac(w) for w in wt_range]

components = ['FE', selected_element, 'VA']
# phases = list(dbf.phases.keys())
phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)

# 📌 Faz ismi eşlemesi (GRAPHITE → CEMENTITE)
phase_map = {'GRAPHITE': 'CEMENTITE'}

# 📌 Faz fraksiyonlarını phase_map ile oluştur
phase_fractions = {}

for wt_x, x in zip(wt_range, mol_fracs):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            eq = equilibrium(dbf, components, phases, {
                v.T: temps,
                v.P: 101325,
                v.X(selected_element): x,
                v.N: 1
            })

            names = eq.Phase.values[0, 0, 0, 0]
            fracs = eq.NP.values[0, 0, 0, 0]

            for name, frac in zip(names, fracs):
                if isinstance(name, str):
                    display_name = phase_map.get(name, name)
                    if display_name not in phase_fractions:
                        phase_fractions[display_name] = []
                    phase_fractions[display_name].append((wt_x, frac))
    except:
        continue

# ✅ Geçiş analizi
def detect_transitions(data_dict, epsilon=1e-6):
    transitions = {}
    for phase, data in data_dict.items():
        values = sorted(data, key=lambda x: x[0])
        frac_vals = [v[1] for v in values]
        if max(frac_vals) < epsilon:
            continue
        prev = values[0][1]
        for i in range(1, len(values)):
            current = values[i][1]
            wt = values[i][0]
            if prev < epsilon and current >= epsilon:
                transitions.setdefault(phase, []).append((wt, f"{wt:.2f}% {selected_element} → {phase} ortaya çıktı"))
            elif prev >= epsilon and current < epsilon:
                transitions.setdefault(phase, []).append((wt, f"{wt:.2f}% {selected_element} → {phase} kayboldu"))
            prev = current
    return transitions

# 🔍 Geçişleri hesapla
transitions = detect_transitions(phase_fractions)

print("\n🔍 Faz Geçiş Noktaları:")
if transitions:
    for phase, events in transitions.items():
        for _, msg in events:
            print("-", msg)
else:
    print("Geçiş bulunamadı.")

# 📈 Grafik çizimi
plt.figure(figsize=(12, 6))
colors = {}
for phase, values in phase_fractions.items():
    wt_vals, frac_vals = zip(*values)
    frac_vals = np.array(frac_vals)
    if max(frac_vals) > 1e-4:
        line, = plt.plot(wt_vals, frac_vals, label=phase)
        colors[phase] = line.get_color()

for phase, events in transitions.items():
    for wt, msg in events:
        plt.axvline(x=wt, color=colors.get(phase, 'gray'), linestyle='--', alpha=0.6)
        plt.text(wt + 0.3, 0.05, msg, rotation=90, fontsize=8, va='bottom', ha='left')

plt.title(f"Fe–{selected_element} Alaşımı ({T_input:.1f}°C) İçin Faz Dönüşümleri")
plt.xlabel(f"{selected_element} İçeriği (wt%)")
plt.ylabel("Faz Oranı")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
