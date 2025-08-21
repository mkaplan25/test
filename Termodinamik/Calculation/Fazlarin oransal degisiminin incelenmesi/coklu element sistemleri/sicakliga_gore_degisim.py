from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

# 🆕 Otomatik faz yöneticisi import
from Termodinamik.Phase_Configurator import get_phases_for_calculation


# 📌 Molar kütleler
M = {
    'FE': 55.845, 'C': 12.01, 'CR': 51.996, 'MN': 54.938, 'SI': 28.085,
    'MO': 95.95, 'V': 50.942, 'AL': 26.98, 'CU': 63.55, 'TI': 47.867,
    'NB': 92.91, 'W': 183.84
}

# 📌 Kullanıcıdan element girdileri
num_elements = int(input("🔢 Kaç element eklemek istiyorsunuz? (FE otomatik eklenecek): "))
wt_dict = {}
for i in range(num_elements):
    el = input(f"🧪 {i+1}. Element adı (örn: C, MN): ").strip().upper()
    if el not in M:
        raise ValueError(f"❌ {el} için molar kütle tanımlı değil.")
    wt = float(input(f"🔒 {el} miktarı (wt%): ")) / 100
    wt_dict[el] = wt

# 📌 FE'yi tamamlayıcı olarak ekle
wt_fe = 1 - sum(wt_dict.values())
if wt_fe <= 0:
    raise ValueError("⚠️ FE oranı sıfır veya negatif! Girdi değerleri çok yüksek.")
wt_dict['FE'] = wt_fe

# 📌 Sıcaklık aralığı
T_min = float(input("🌡️ Başlangıç sıcaklığı (°C): "))
T_max = float(input("🌡️ Bitiş sıcaklığı (°C): "))

#step_count = int(input("🔢 Tarama adım sayısı (ör. 50): "))
step_count = 5

T_range = np.linspace(T_min, T_max, step_count)
pressure=float(input("🌡️ Basınç (Pa): "))

# 📌 TDB ve fazlar
tdb_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"
dbf = Database(tdb_path)
components = list(wt_dict.keys()) + ['VA']
#phases = [ph for ph in dbf.phases.keys() if ph not in ['GRAPHITE', 'DIAMOND_A4']]

phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)

# 📌 Mol oranlarına dönüştür
mols = {el: wt_dict[el] / M[el] for el in wt_dict}
total_mol = sum(mols.values())
x_dict = {el: mols[el] / total_mol for el in mols if el != 'FE'}

# 📌 Faz verileri
phase_fractions = {ph: [] for ph in phases}
T_used = []

# 📌 Hesaplama döngüsü
for T_C in T_range:
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

        for ph in phase_fractions:
            phase_fractions[ph].append(present.get(ph, 0.0))
        T_used.append(T_C)

    except Exception as e:
        print(f"⚠️ Hata @ {T_C:.1f}°C: {e}")
        for ph in phase_fractions:
            phase_fractions[ph].append(0.0)
        T_used.append(T_C)

# 📌 Kullanıcıya faz seçtir
available_phases = [ph for ph in phase_fractions if max(phase_fractions[ph]) > 1e-4]
print("\n📢 Oluşan fazlar:")
for i, ph in enumerate(available_phases):
    print(f"{i+1}. {ph}")
selections = input("👁️ Görmek istediğiniz fazları seçin (virgülle veya '*' hepsi): ").strip()

if selections == '*' or selections == '':
    selected_phases = available_phases
else:
    try:
        indices = [int(x.strip()) - 1 for x in selections.split(',')]
        selected_phases = [available_phases[i] for i in indices if 0 <= i < len(available_phases)]
    except:
        print("⚠️ Geçersiz seçim. Tüm fazlar çiziliyor.")
        selected_phases = available_phases

# 📊 Görselleştirme
plt.figure(figsize=(10, 6))
for ph in selected_phases:
    plt.plot(T_used, phase_fractions[ph], label=ph)

plt.xlabel("Sıcaklık (°C)")
plt.ylabel("Faz Oranı")
plt.title("Sıcaklığa Bağlı Faz Dönüşümleri")
plt.ylim(0, 1.05)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
