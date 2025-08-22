import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, variables as v, ternplot
import numpy as np
import io
import base64

# Phase configurator import eklendi
from Phase_Configurator import get_phases_for_calculation

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

def generate_ternary_isothermal_api(element1, element2, weight_percent1, weight_percent2, temperature_c, pressure_pa, step_size=0.1):
    """API için ternary isothermal diagram oluştur"""
    
    # Mevcut koddan değişkenleri ayarla
    el1, el2 = element1, element2
    wt1 = weight_percent1 / 100
    wt2 = weight_percent2 / 100
    wt_fe = 1 - (wt1 + wt2)
    temp = temperature_c
    pressure = pressure_pa
    
    # Molar kütleler
    molar_masses = {
        'FE': 55.845, 'AL': 26.9815, 'B': 10.81, 'C': 12.01, 'CO': 58.933, 'CR': 51.996,
        'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
        'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
        'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
    }
    
    # Mol fraksiyonları hesapla
    mol_el1 = wt1 / molar_masses[el1]
    mol_el2 = wt2 / molar_masses[el2]
    mol_fe = wt_fe / molar_masses['FE']
    mol_total = mol_el1 + mol_el2 + mol_fe
    x_el1 = mol_el1 / mol_total
    x_el2 = mol_el2 / mol_total
    
    # Bileşenler ve fazlar
    comps = ['FE', el1, el2, 'VA']
    allowed_phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)
    
    # Denge hesapla (stabil fazlar için)
    conds = {
        v.T: temp + 273.15,
        v.P: pressure,
        v.X(el1): x_el1,
        v.X(el2): x_el2,
        v.N: 1
    }
    eq = equilibrium(db, comps, allowed_phases, conds)
    present_phases = np.unique(eq.Phase.values)
    kararli_fazlar = set([p for p in present_phases if p != ''])
    
    # Ternary plot oluştur
    plt.figure(figsize=(10, 8))
    fig = ternplot(
        dbf=db,
        comps=comps,
        phases=list(allowed_phases),
        conds={
            v.T: temp + 273.15,
            v.P: pressure,
            v.X(el1): (0.001, 0.85, step_size),
            v.X(el2): (0.001, 0.85, step_size)
        },
        x=v.X(el1),
        y=v.X(el2),
        label_nodes=False
    )
    
    # Seçilen alaşım bileşimi işaretle
    plt.scatter(x_el1, x_el2, color='red', s=100)
    plt.title(f"Fe-{el1}-{el2} Üçlü Faz Diyagramı @ {temp:.1f}°C")
    plt.subplots_adjust(right=0.75)
    
    # Base64'e çevir
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return {
        "image_base64": image_base64,
        "stable_phases": list(kararli_fazlar),
        "system_info": f"Fe-{el1}-{el2}"
    }

# CLI kodu - sadece doğrudan çalıştırıldığında aktif
if __name__ == "__main__":
    # VA ve FE hariç tüm elementleri listele
    all_elements = sorted([el for el in db.elements if el not in ['VA', 'FE']])
    print("Mevcut alaşım elementleri:", ', '.join(all_elements))

    elements = input("Hangi elementleri gireceksiniz? (Virgülle): ").strip().upper().split(',')

    if len(elements) < 2:
        print("❌ En az iki element girilmelidir.")
        exit()

    for el in elements:
        if el not in all_elements:
            print(f"❌ '{el}' elementi geçerli değil.")
            exit()

    if len(elements) == 2:
        # Sadece 2 element varsa direkt kullan
        el1, el2 = elements[0], elements[1]
        print(f"✅ Seçilen elementler: {el1} ve {el2}")
    else:
        # 2'den fazla element varsa kullanıcıdan seç
        el1 = input("Üçlü diyagram için birinci elementi seçin (listeden): ").strip().upper()
        el2 = input("Üçlü diyagram için ikinci elementi seçin (listeden): ").strip().upper()

        if el1 not in elements or el2 not in elements or el1 == el2:
            print("❌ Seçilen elementler geçersiz veya aynı.")
            exit()

    # Kompozisyon girişi - opsiyonel
    print(f"\n📊 Kompozisyon girişi (opsiyonel - boş bırakabilirsiniz):")
    wt1_input = input(f"{el1} için ağırlıkça yüzde (% - boş=0): ").strip()
    wt2_input = input(f"{el2} için ağırlıkça yüzde (% - boş=0): ").strip()

    # Boş girişleri 0 olarak ayarla
    wt1 = float(wt1_input) / 100 if wt1_input else 0.0
    wt2 = float(wt2_input) / 100 if wt2_input else 0.0
    wt_fe = 1 - (wt1 + wt2)

    if wt_fe < 0:
        print("❌ Toplam ağırlık %100'ü geçemez.")
        exit()

    temp = float(input("Analiz yapılacak sıcaklığı girin (°C): "))
    pressure = float(input("Basınç değerini giriniz (Pa): "))

    # Molar kütleler
    molar_masses = {
        'FE': 55.845, 'AL': 26.9815, 'B': 10.81, 'C': 12.01, 'CO': 58.933, 'CR': 51.996,
        'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
        'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
        'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
    }

    try:
        mol_el1 = wt1 / molar_masses[el1]
        mol_el2 = wt2 / molar_masses[el2]
        mol_fe = wt_fe / molar_masses['FE']
    except KeyError as e:
        print(f"❌ Molar kütle verisi eksik: {e}")
        exit()

    mol_total = mol_el1 + mol_el2 + mol_fe
    x_el1 = mol_el1 / mol_total
    x_el2 = mol_el2 / mol_total

    # Bileşenler ve fazlar
    comps = ['FE', el1, el2, 'VA']
    allowed_phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)
    step_size = 0.1

    # Fe-C sistemi tespiti ve faz eşleme
    if {'FE', 'C'} <= set(['FE', el1, el2]):
        graphite_to_cementite = True
    else:
        graphite_to_cementite = False

    phase_map = {'GRAPHITE': 'CEMENTITE'} if graphite_to_cementite else {}

    # Denge hesapla
    conds = {
        v.T: temp + 273.15,
        v.P: pressure,
        v.X(el1): x_el1,
        v.X(el2): x_el2,
        v.N: 1
    }
    eq = equilibrium(db, comps, allowed_phases, conds)

    present_phases = np.unique(eq.Phase.values)
    kararli_fazlar = set([phase_map.get(p, p) for p in present_phases if p != ''])
    tum_fazlar = set([phase_map.get(ph, ph) for ph in allowed_phases])
    kararsiz_fazlar = tum_fazlar - kararli_fazlar

    # Kullanıcıya kararsız fazları çizdirip çizdirmeyeceğini sor
    if kararsiz_fazlar:
        print(f"\n🤮 Hesaplanan sıcaklıkta kararsız (ama sistemde tanımlı) {len(kararsiz_fazlar)} faz bulundu:")
        for f in sorted(kararsiz_fazlar):
            print(f"- {f}")
        etiketlenebilir_fazlar = kararli_fazlar

    # Kararlı faz listesi yazdır
    if len(kararli_fazlar) == 0:
        print("⚠️ Hiçbir kararlı faz bulunamadı.")
    else:
        print(f"\n✅ {temp}°C sıcaklıkta (%{wt_fe*100:.2f} Fe, %{wt1*100:.2f} {el1}, %{wt2*100:.2f} {el2}) bulunan fazlar:")
        for p in sorted(kararli_fazlar):
            print(f"  - {p}")

    # Faz diyagramı çizimi
    fig = ternplot(
        dbf=db,
        comps=comps,
        phases=tum_fazlar,
        conds={
            v.T: temp + 273.15,
            v.P: pressure,
            v.X(el1): (0.001, 0.85, step_size),
            v.X(el2): (0.001, 0.85, step_size)
        },
        x=v.X(el1),
        y=v.X(el2),
        label_nodes=False
    )

    # Kararlı fazları etiketleme tetikleyicisi
    for phase in etiketlenebilir_fazlar:
        plt.text(0.05, 0.05, '', alpha=0)

    # Seçilen alaşım bileşimi işaretle
    plt.scatter(x_el1, x_el2, color='red', s=100)
    plt.title(f"Fe-{el1}-{el2} Üçlü Faz Diyagramı @ {temp:.1f}°C")
    plt.subplots_adjust(right=0.75)
    plt.show()