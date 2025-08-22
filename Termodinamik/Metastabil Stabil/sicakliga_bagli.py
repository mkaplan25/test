from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

print("🔥 Çoklu Element Fe Alaşımı Metastabil Analiz Sistemi")
print("=" * 60)

# 🧪 Çoklu element girişi
elements = []
weights = []

while True:
    element_count = len(elements) + 1
    element = input(f"🧪 {element_count}. Element (örnek: C, MN, CR) [Enter=bitir]: ").strip().upper()

    if not element:  # Enter basılırsa çık
        if len(elements) == 0:
            print("❌ En az bir element girmelisiniz!")
            continue
        break

    try:
        wt = float(input(f"💠 {element} ağırlıkça yüzde (%): "))
        if wt <= 0 or wt >= 100:
            print("⚠️ Ağırlık yüzdesi 0-100 arasında olmalı!")
            continue

        elements.append(element)
        weights.append(wt / 100)

        total_wt = sum(weights) * 100
        remaining_fe = 100 - total_wt

        print(f"✅ {element}: %{wt:.2f} eklendi")
        print(f"📊 Toplam alaşım elementi: %{total_wt:.2f}")
        print(f"🔗 Kalan Fe: %{remaining_fe:.2f}")

        if total_wt >= 95:
            print("⚠️ Toplam alaşım elementi %95'i geçti, otomatik olarak sonlandırılıyor...")
            break

        if len(elements) >= 8:  # Çok fazla element girişini engelle
            print("⚠️ Maksimum 8 element desteklenmektedir.")
            break

    except ValueError:
        print("❌ Geçersiz sayı girdiniz, tekrar deneyin!")

T_start = float(input("🌡️ Başlangıç sıcaklığı (°C): "))
T_end = float(input("🌡️ Bitiş sıcaklığı (°C): "))
pressure=float(input("Basınç (Pa): "))
step_count = int(input("🔢 Tarama adım sayısı (min 50 önerilen): ") or "50")

# ✅ Genişletilmiş molar kütle listesi
MOLAR_MASSES = {
    'FE': 55.845, 'C': 12.01, 'AL': 26.9815, 'B': 10.81, 'CO': 58.933, 'CR': 51.996,
    'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
    'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
    'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84,
    'Y': 88.9059, 'ZN': 65.38, 'ZR': 91.224, 'AG': 107.8682, 'AU': 196.966569,
    'SN': 118.71, 'PB': 207.2, 'MG': 24.305, 'CA': 40.078, 'BE': 9.0122, 'LI': 6.94
}

# Element kontrolü
missing_elements = [elem for elem in elements if elem not in MOLAR_MASSES]
if missing_elements:
    print(f"❌ Bilinmeyen elementler: {', '.join(missing_elements)}")
    print(f"📋 Desteklenen elementler: {', '.join(sorted(MOLAR_MASSES.keys()))}")
    exit()

# ✅ Çoklu element mol hesaplamaları
total_alloy_wt = sum(weights)
wt_fe = 1 - total_alloy_wt

print(f"\n📊 Kompozisyon Özeti:")
print(f"🔗 Fe: %{wt_fe * 100:.3f}")
for elem, wt in zip(elements, weights):
    print(f"🧪 {elem}: %{wt * 100:.3f}")

# Mol hesaplamaları
mol_fe = wt_fe / MOLAR_MASSES['FE']
mol_elements = [wt / MOLAR_MASSES[elem] for wt, elem in zip(weights, elements)]
total_mol = mol_fe + sum(mol_elements)

# Mol fraksiyonları
x_elements = [mol_elem / total_mol for mol_elem in mol_elements]

print(f"\n🧮 Mol Fraksiyonları:")
print(f"🔗 Fe: {(mol_fe / total_mol):.6f}")
for elem, x in zip(elements, x_elements):
    print(f"🧪 {elem}: {x:.6f}")

# Veritabanı yükle
warnings.filterwarnings("ignore", category=UserWarning)
import os
import sys

if getattr(sys, 'frozen', False):
    # PyInstaller bundle içinde çalışıyor
    base_path = sys._MEIPASS
    tdb_path = os.path.join(base_path, "FeC.tdb")
else:
    # Normal Python çalışıyor - bir üst klasöre git
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tdb_path = os.path.join(current_dir, "..", "FeC.tdb")

dbf = Database(tdb_path)

# ✅ Dinamik component listesi
components = ['FE'] + elements + ['VA']
print(f"\n🔧 Sistem bileşenleri: {', '.join(components)}")

all_phases = list(dbf.phases.keys())

# ✅ Gelişmiş faz isimlendirmesi
PHASE_DISPLAY_NAMES = {
    'BCC_A2': 'Ferrit (α-Fe)',
    'FCC_A1': 'Austenit (γ-Fe)',
    'CEMENTITE': 'Sementit (Fe₃C)',
    'GRAPHITE': 'Grafit (C)',
    'LIQUID': 'Sıvı Faz',
    'BCC_B2': 'Düzenli BCC',
    'FCC_L12': 'Düzenli FCC',
    'SIGMA': 'Sigma Fazı',
    'M23C6': 'M₂₃C₆ Karbür',
    'M7C3': 'M₇C₃ Karbür',
    'M6C': 'M₆C Karbür',
    'MC_ETA': 'MC Karbür',
    'MX': 'MX Fazı',
    'LAVES_C14': 'Laves C14',
    'LAVES_C15': 'Laves C15',
    'LAVES_C36': 'Laves C36'
}

# ✅ Çoklu element için faz filtreleme
valid_elements = set(['FE'] + elements)
suppress_by_default = {'DIAMOND_A4', 'FC_MONO', 'CORUND', 'SPINEL', 'SIO2', 'O1_GAS'}
filtered_phases = []
user_suppressible_phases = []

for ph in all_phases:
    phase_obj = dbf.phases[ph]
    used_elems = set()
    for const in phase_obj.constituents:
        for site in const:
            if hasattr(site, 'name'):
                used_elems.add(site.name)

    # Sistemdeki elementlerle kesişim var mı?
    if len(used_elems.intersection(valid_elements)) > 0:
        if ph in suppress_by_default:
            user_suppressible_phases.append(ph)
        else:
            filtered_phases.append(ph)

# Sıcaklık aralığı
temps = np.linspace(T_start, T_end, step_count)


# ✅ Çoklu element koşul fonksiyonu
def build_conditions(T):
    conds = {v.T: T + 273.15, v.P: 101325, v.N: 1}

    # Tüm elementler için mol fraksiyonlarını ekle
    for elem, x in zip(elements, x_elements):
        conds[v.X(elem)] = x

    return conds


# Stabil durumda olası fazları tespit et
print("\n🔍 Stabil faz analizi yapılıyor...")
try:
    eq_stabil = equilibrium(dbf, components, filtered_phases + user_suppressible_phases, build_conditions(temps))
    all_stabil_phases = list(set(
        phase for phase, frac in zip(eq_stabil.Phase.values.flatten(), eq_stabil.NP.values.flatten())
        if isinstance(phase, str) and not np.isnan(frac) and frac > 1e-4
    ))
    print(f"✅ {len(all_stabil_phases)} adet stabil faz tespit edildi")
except Exception as e:
    print(f"❌ Stabil faz analizi hatası: {e}")
    exit()

# Kullanıcıya fazları göster
print("\n📌 Bu alaşımda, verilen sıcaklık aralığında oluşabilecek fazlar:")
for idx, ph in enumerate(all_stabil_phases):
    display_name = PHASE_DISPLAY_NAMES.get(ph, ph)
    print(f"{idx + 1:2d} → {ph:15s} ({display_name})")

# Bastırılacak fazları al
bastirilacak = input("\n⛔ Bastırmak (suppress) istediğiniz faz numaralarını girin (virgülle, 0=yok): ").strip()
suppress_fazlar = []
if bastirilacak and bastirilacak != '0':
    try:
        suppress_indices = [int(i.strip()) - 1 for i in bastirilacak.split(',')]
        suppress_fazlar = [all_stabil_phases[i] for i in suppress_indices if 0 <= i < len(all_stabil_phases)]
        print(f"✅ Bastırılan fazlar: {', '.join(suppress_fazlar)}")
    except:
        print("❌ Bastırılacak fazların girişi hatalı. Devam ediliyor...")

# Metastabil faz listesi
metastabil_phases = [ph for ph in all_stabil_phases if ph not in suppress_fazlar]
print(f"🔄 Metastabil hesaplamada kullanılacak fazlar: {', '.join(metastabil_phases)}")

# Hesaplama döngüsü
meta_fractions = {ph: [] for ph in all_stabil_phases}
stabil_data = {ph: [] for ph in all_stabil_phases}

print(f"\n🔄 {len(temps)} sıcaklık noktasında hesaplama başlatılıyor...")
successful_calcs = 0
failed_calcs = 0

for i, T in enumerate(temps):
    if i % max(1, len(temps) // 10) == 0:
        print(f"  📊 İlerleme: {i / len(temps) * 100:.1f}% - {T:.1f}°C")

    try:
        # Metastabil hesaplama
        eq_meta = equilibrium(dbf, components, metastabil_phases, build_conditions(T))
        meta_names = eq_meta.Phase.values.flatten()
        meta_fracs = eq_meta.NP.values.flatten()

        # Stabil hesaplama
        eq_stab = equilibrium(dbf, components, all_stabil_phases, build_conditions(T))
        stab_names = eq_stab.Phase.values.flatten()
        stab_fracs = eq_stab.NP.values.flatten()

        # Sonuçları kaydet
        for ph in all_stabil_phases:
            # Stabil durum
            indices_stab = np.where(stab_names == ph)[0]
            frac_stab = np.sum(stab_fracs[indices_stab]) if len(indices_stab) > 0 else 0.0
            stabil_data[ph].append((T, frac_stab))

            # Metastabil durum
            if ph in metastabil_phases:
                indices_meta = np.where(meta_names == ph)[0]
                frac_meta = np.sum(meta_fracs[indices_meta]) if len(indices_meta) > 0 else 0.0
                meta_fractions[ph].append((T, frac_meta))
            else:
                meta_fractions[ph].append((T, 0.0))

        successful_calcs += 1

    except Exception as e:
        print(f"⚠️ {T:.1f}°C'de hata: {e}")
        failed_calcs += 1
        for ph in all_stabil_phases:
            meta_fractions[ph].append((T, 0.0))
            stabil_data[ph].append((T, 0.0))

print(f"📈 Hesaplama istatistikleri: {successful_calcs} başarılı, {failed_calcs} başarısız")

# ✅ Gelişmiş grafik
plt.figure(figsize=(16, 10))
colors = plt.cm.tab20(np.linspace(0, 1, len(all_stabil_phases)))

plotted_phases = 0
for i, ph in enumerate(all_stabil_phases):
    if ph in suppress_fazlar:
        continue

    display_name = PHASE_DISPLAY_NAMES.get(ph, ph)
    T_vals, F_vals_meta = zip(*meta_fractions[ph])
    _, F_vals_stab = zip(*stabil_data[ph])

    # Sıfır olmayan değerler var mı kontrol et
    if max(F_vals_stab) < 1e-6 and max(F_vals_meta) < 1e-6:
        continue

    color = colors[i]

    # Stabil ve metastabil arasında fark var mı kontrol et
    if ph in metastabil_phases and not np.allclose(F_vals_meta, F_vals_stab, atol=1e-4):
        plt.plot(T_vals, F_vals_meta, label=f"{display_name} (metastabil)",
                 linestyle='--', linewidth=2.5, alpha=0.8, color=color)
        plt.plot(T_vals, F_vals_stab, label=f"{display_name} (stabil)",
                 linestyle='-', linewidth=2, alpha=1.0, color=color)
    else:
        plt.plot(T_vals, F_vals_stab, label=f"{display_name}",
                 linestyle='-', linewidth=2.5, alpha=1.0, color=color)

    plotted_phases += 1

plt.xlabel("Sıcaklık (°C)", fontsize=12)
plt.ylabel("Faz Oranı", fontsize=12)

# ✅ Dinamik başlık oluşturma
composition_str = " + ".join([f"%{wt * 100:.2f} {elem}" for elem, wt in zip(elements, weights)])
plt.title(f"Fe + {composition_str}\n🔄 Stabil ve Metastabil Faz Karşılaştırması", fontsize=14)

plt.grid(True, alpha=0.3)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
plt.tight_layout()

# Bastırılan fazları göster
if suppress_fazlar:
    plt.figtext(0.02, 0.02, f"⛔ Bastırılan fazlar: {', '.join(suppress_fazlar)}",
                fontsize=10, style='italic', alpha=0.7)

# Element bilgisini göster
element_info = f"🧪 Elementler: Fe + {', '.join(elements)}"
plt.figtext(0.02, 0.96, element_info, fontsize=10, weight='bold', alpha=0.8)

plt.show()

print(f"\n✅ Hesaplama tamamlandı!")
print(f"📊 Toplam {plotted_phases} faz grafiklendi")
print(f"🔬 Sistem: Fe + {' + '.join(elements)}")
print(f"🌡️ Sıcaklık aralığı: {T_start}°C - {T_end}°C")