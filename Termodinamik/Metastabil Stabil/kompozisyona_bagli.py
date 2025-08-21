from pycalphad import Database, equilibrium, variables as v
import matplotlib.pyplot as plt
import numpy as np
import warnings

print("🔥 Sabit Sıcaklık Kompozisyon Bazlı Metastabil Analiz Sistemi")
print("=" * 65)

# 🌡️ Sabit sıcaklık girişi
temperature = float(input("🌡️ Analiz sıcaklığı (°C): "))

pressure=float(input("Basınç (Pa): "))

# 🧪 Ana değişken element seçimi
print("\n📊 Kompozisyon değişimi için ana element seçimi:")
main_element = input("🎯 Ana değişken element (örnek: C, MN, CR): ").strip().upper()
min_wt = float(input(f"💠 {main_element} minimum ağırlık % (örnek: 0): "))
max_wt = float(input(f"💠 {main_element} maksimum ağırlık % (örnek: 2): "))
step_count = int(input("🔢 Kompozisyon adım sayısı (min 30 önerilen): ") or "30")

# 🧪 Sabit tutulacak diğer elementler
fixed_elements = []
fixed_weights = []

print(f"\n➕ {main_element} dışında sabit tutulacak elementler:")
while True:
    element = input(f"🧪 Sabit element {len(fixed_elements) + 1} (Enter=bitir): ").strip().upper()

    if not element:  # Enter basılırsa çık
        break

    if element == main_element:
        print(f"⚠️ {main_element} zaten ana değişken element!")
        continue

    try:
        wt = float(input(f"💠 {element} sabit ağırlık % (örnek: 1.0): "))
        if wt <= 0 or wt >= 100:
            print("⚠️ Ağırlık yüzdesi 0-100 arasında olmalı!")
            continue

        fixed_elements.append(element)
        fixed_weights.append(wt / 100)

        total_fixed = sum(fixed_weights) * 100
        remaining_for_main = 100 - total_fixed - max_wt

        print(f"✅ {element}: %{wt:.2f} eklendi")
        print(f"📊 Toplam sabit elementler: %{total_fixed:.2f}")
        print(f"🔗 Kalan Fe aralığı: %{remaining_for_main:.2f} - %{100 - total_fixed - min_wt:.2f}")

        if total_fixed + max_wt >= 95:
            print("⚠️ Toplam element %95'i geçecek, dikkatli olun!")

        if len(fixed_elements) >= 6:
            print("⚠️ Maksimum 6 sabit element desteklenmektedir.")
            break

    except ValueError:
        print("❌ Geçersiz sayı girdiniz, tekrar deneyin!")

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
all_elements = [main_element] + fixed_elements
missing_elements = [elem for elem in all_elements if elem not in MOLAR_MASSES]
if missing_elements:
    print(f"❌ Bilinmeyen elementler: {', '.join(missing_elements)}")
    print(f"📋 Desteklenen elementler: {', '.join(sorted(MOLAR_MASSES.keys()))}")
    exit()

# ✅ Kompozisyon aralığı hesaplama
total_fixed_wt = sum(fixed_weights)
main_wt_range = np.linspace(min_wt / 100, max_wt / 100, step_count)

print(f"\n📊 Kompozisyon Analiz Özeti:")
print(f"🎯 Ana element: {main_element} (%{min_wt:.2f} - %{max_wt:.2f})")
print(
    f"🔗 Sabit elementler: {', '.join([f'{elem}: %{wt * 100:.2f}' for elem, wt in zip(fixed_elements, fixed_weights)])}")
print(f"🌡️ Analiz sıcaklığı: {temperature}°C")

# Veritabanı yükle
warnings.filterwarnings("ignore", category=UserWarning)
dbf = Database(r"C:\\Users\\user\\PycharmProjects\\AlloyCraft\\Termodinamik\\FeC.tdb")

# ✅ Dinamik component listesi
components = ['FE', main_element] + fixed_elements + ['VA']
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

# ✅ Kompozisyon için faz filtreleme
valid_elements = set(['FE', main_element] + fixed_elements)
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


# ✅ Kompozisyon bazlı koşul fonksiyonu
def build_conditions(main_wt):
    # Mol hesaplamaları
    wt_fe = 1 - main_wt - total_fixed_wt

    mol_fe = wt_fe / MOLAR_MASSES['FE']
    mol_main = main_wt / MOLAR_MASSES[main_element]
    mol_fixed = [wt / MOLAR_MASSES[elem] for wt, elem in zip(fixed_weights, fixed_elements)]

    total_mol = mol_fe + mol_main + sum(mol_fixed)

    # Mol fraksiyonları
    x_main = mol_main / total_mol
    x_fixed = [mol / total_mol for mol in mol_fixed]

    conds = {v.T: temperature + 273.15, v.P: 101325, v.N: 1}
    conds[v.X(main_element)] = x_main

    # Sabit elementlerin mol fraksiyonları
    for elem, x in zip(fixed_elements, x_fixed):
        conds[v.X(elem)] = x

    return conds


# Stabil durumda olası fazları tespit et (orta kompozisyonda)
print("\n🔍 Stabil faz analizi yapılıyor...")
mid_composition = (min_wt + max_wt) / 200  # Orta nokta
try:
    eq_stabil = equilibrium(dbf, components, filtered_phases + user_suppressible_phases,
                            build_conditions(mid_composition))
    all_stabil_phases = list(set(
        phase for phase, frac in zip(eq_stabil.Phase.values.flatten(), eq_stabil.NP.values.flatten())
        if isinstance(phase, str) and not np.isnan(frac) and frac > 1e-4
    ))
    print(f"✅ {len(all_stabil_phases)} adet stabil faz tespit edildi")
except Exception as e:
    print(f"❌ Stabil faz analizi hatası: {e}")
    exit()

# Kullanıcıya fazları göster
print(f"\n📌 {main_element} kompozisyon değişiminde oluşabilecek fazlar:")
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
composition_points = []

print(f"\n🔄 {len(main_wt_range)} kompozisyon noktasında hesaplama başlatılıyor...")
successful_calcs = 0
failed_calcs = 0

for i, main_wt in enumerate(main_wt_range):
    if i % max(1, len(main_wt_range) // 10) == 0:
        print(f"  📊 İlerleme: {i / len(main_wt_range) * 100:.1f}% - {main_element}: %{main_wt * 100:.3f}")

    composition_points.append(main_wt * 100)

    try:
        # Metastabil hesaplama
        eq_meta = equilibrium(dbf, components, metastabil_phases, build_conditions(main_wt))
        meta_names = eq_meta.Phase.values.flatten()
        meta_fracs = eq_meta.NP.values.flatten()

        # Stabil hesaplama
        eq_stab = equilibrium(dbf, components, all_stabil_phases, build_conditions(main_wt))
        stab_names = eq_stab.Phase.values.flatten()
        stab_fracs = eq_stab.NP.values.flatten()

        # Sonuçları kaydet
        for ph in all_stabil_phases:
            # Stabil durum
            indices_stab = np.where(stab_names == ph)[0]
            frac_stab = np.sum(stab_fracs[indices_stab]) if len(indices_stab) > 0 else 0.0
            stabil_data[ph].append((main_wt * 100, frac_stab))

            # Metastabil durum
            if ph in metastabil_phases:
                indices_meta = np.where(meta_names == ph)[0]
                frac_meta = np.sum(meta_fracs[indices_meta]) if len(indices_meta) > 0 else 0.0
                meta_fractions[ph].append((main_wt * 100, frac_meta))
            else:
                meta_fractions[ph].append((main_wt * 100, 0.0))

        successful_calcs += 1

    except Exception as e:
        print(f"⚠️ {main_element}: %{main_wt * 100:.3f}'de hata: {e}")
        failed_calcs += 1
        for ph in all_stabil_phases:
            meta_fractions[ph].append((main_wt * 100, 0.0))
            stabil_data[ph].append((main_wt * 100, 0.0))

print(f"📈 Hesaplama istatistikleri: {successful_calcs} başarılı, {failed_calcs} başarısız")

# ✅ Gelişmiş grafik
plt.figure(figsize=(16, 10))
colors = plt.cm.tab20(np.linspace(0, 1, len(all_stabil_phases)))

plotted_phases = 0
for i, ph in enumerate(all_stabil_phases):
    if ph in suppress_fazlar:
        continue

    display_name = PHASE_DISPLAY_NAMES.get(ph, ph)
    comp_vals, F_vals_meta = zip(*meta_fractions[ph])
    _, F_vals_stab = zip(*stabil_data[ph])

    # Sıfır olmayan değerler var mı kontrol et
    if max(F_vals_stab) < 1e-6 and max(F_vals_meta) < 1e-6:
        continue

    color = colors[i]

    # Stabil ve metastabil arasında fark var mı kontrol et
    if ph in metastabil_phases and not np.allclose(F_vals_meta, F_vals_stab, atol=1e-4):
        plt.plot(comp_vals, F_vals_meta, label=f"{display_name} (metastabil)",
                 linestyle='--', linewidth=2.5, alpha=0.8, color=color)
        plt.plot(comp_vals, F_vals_stab, label=f"{display_name} (stabil)",
                 linestyle='-', linewidth=2, alpha=1.0, color=color)
    else:
        plt.plot(comp_vals, F_vals_stab, label=f"{display_name}",
                 linestyle='-', linewidth=2.5, alpha=1.0, color=color)

    plotted_phases += 1

plt.xlabel(f"{main_element} Ağırlık % (wt%)", fontsize=12)
plt.ylabel("Faz Oranı", fontsize=12)

# ✅ Dinamik başlık oluşturma
fixed_str = " + ".join([f"%{wt * 100:.2f} {elem}" for elem, wt in zip(fixed_elements, fixed_weights)])
base_composition = f"Fe + {fixed_str}" if fixed_elements else "Fe"
plt.title(
    f"{base_composition} + {main_element} (değişken)\n🔄 {temperature}°C'de Stabil vs Metastabil Faz Karşılaştırması",
    fontsize=14)

plt.grid(True, alpha=0.3)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
plt.tight_layout()

# Bastırılan fazları göster
if suppress_fazlar:
    plt.figtext(0.02, 0.02, f"⛔ Bastırılan fazlar: {', '.join(suppress_fazlar)}",
                fontsize=10, style='italic', alpha=0.7)

# Analiz bilgisini göster
analysis_info = f"🌡️ {temperature}°C | 🎯 {main_element}: %{min_wt:.2f}-%{max_wt:.2f}"
plt.figtext(0.02, 0.96, analysis_info, fontsize=10, weight='bold', alpha=0.8)

plt.show()

print(f"\n✅ Kompozisyon analizi tamamlandı!")
print(f"📊 Toplam {plotted_phases} faz grafiklendi")
print(f"🔬 Sistem: {base_composition} + {main_element} (değişken)")
print(f"🎯 Kompozisyon aralığı: %{min_wt:.2f} - %{max_wt:.2f} {main_element}")
print(f"🌡️ Analiz sıcaklığı: {temperature}°C")