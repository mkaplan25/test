import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium, variables as v
import numpy as np
import warnings

import io
import base64
# 🆕 Phase configurator import eklendi
from Phase_Configurator import get_phases_for_calculation

# 🔧 Veritabanını yükle
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

class VerticalSectionAnalyzer:
    def __init__(self, db_path):
        """Vertical section analizi sınıfı"""
        self.db = Database(db_path)
        self.molar_masses = {
            'FE': 55.845, 'AL': 26.9815, 'B': 10.81, 'C': 12.01, 'CO': 58.933, 'CR': 51.996,
            'CU': 63.546, 'H': 1.008, 'HF': 178.49, 'LA': 138.9055, 'MN': 54.938, 'MO': 95.95,
            'N': 14.007, 'NB': 92.9064, 'NI': 58.693, 'O': 15.999, 'P': 30.9738, 'PD': 106.42,
            'S': 32.065, 'SI': 28.0855, 'TA': 180.9479, 'TI': 47.867, 'V': 50.9415, 'W': 183.84, 'Y': 88.9059
        }
        self.available_elements = sorted([el for el in self.db.elements if el not in ['VA', 'FE']])

    def get_available_elements(self):
        """Mevcut elementleri listele"""
        return self.available_elements

    def weight_to_mole_fraction(self, compositions):
        """Ağırlık yüzdesini mol fraksiyonuna çevir"""
        total_moles = sum(wt / self.molar_masses[el] for el, wt in compositions.items())
        return {el: (wt / self.molar_masses[el]) / total_moles for el, wt in compositions.items()}

    def validate_composition(self, compositions):
        """Kompozisyon geçerliliğini kontrol et"""
        total_weight = sum(compositions.values())
        if not (0.99 <= total_weight <= 1.01):  # %1 tolerans
            raise ValueError(f"Toplam ağırlık %100 olmalı, şu anda: %{total_weight * 100:.2f}")

        for element in compositions:
            if element not in self.molar_masses:
                raise ValueError(f"'{element}' elementi için molar kütle verisi yok")

    def calculate_equilibrium(self, elements, compositions, temperature):
        """Termodinamik dengeyi hesapla"""
        # Kompozisyonu doğrula
        self.validate_composition(compositions)

        # Mol fraksiyonlarını hesapla
        mole_fractions = self.weight_to_mole_fraction(compositions)

        # Bileşenler ve fazlar
        comps = ['FE'] + elements + ['VA']
        allowed_phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)

        # Denge koşulları
        conds = {
            v.T: temperature + 273.15,
            v.P: 101325,
            v.N: 1
        }

        # Element mol fraksiyonlarını ekle
        for el in elements:
            conds[v.X(el)] = mole_fractions[el]

        # Denge hesapla
        eq = equilibrium(self.db, comps, allowed_phases, conds)

        return eq, mole_fractions

    def plot_vertical_section(self, elements, composition_ratios, temp_range, save_path=None):
        """Vertical section çiz (sabit kompozisyon oranında sıcaklık değişimi)"""
        if len(elements) != 2:
            raise ValueError("İkili sistem için tam olarak 2 element gerekli")

        el1, el2 = elements
        comps = ['FE', el1, el2, 'VA']
        all_phases = list(self.db.phases.keys())

        temperatures = np.linspace(temp_range[0], temp_range[1], 50)
        phase_fractions = {}

        print(f"🔄 {len(temperatures)} sıcaklık noktası için hesaplama yapılıyor...")

        for i, temp in enumerate(temperatures):
            if i % 10 == 0:  # Her 10 noktada progress
                print(f"   İlerleme: {i}/{len(temperatures)} ({temp:.0f}°C)")

            # Sabit kompozisyon oranını kullan
            compositions = {
                'FE': composition_ratios['FE'],
                el1: composition_ratios[el1],
                el2: composition_ratios[el2]
            }

            try:
                eq, mole_fractions = self.calculate_equilibrium(elements, compositions, temp)

                # Faz fraksiyonlarını hesapla
                present_phases = np.unique(eq.Phase.values)

                temp_phase_fractions = {}
                for phase_idx, phase in enumerate(present_phases):
                    if phase != '':
                        # Faz fraksiyonunu hesapla
                        phase_mask = eq.Phase.values == phase
                        if np.any(phase_mask):
                            phase_fraction = np.mean(eq.NP.values[phase_mask])
                            if phase_fraction > 1e-6:  # Çok küçük fraksiyonları filtrele
                                temp_phase_fractions[phase] = phase_fraction

                # Her faz için sıcaklık-fraksiyon çiftini kaydet
                for phase in temp_phase_fractions:
                    if phase not in phase_fractions:
                        phase_fractions[phase] = {'temps': [], 'fractions': []}
                    phase_fractions[phase]['temps'].append(temp)
                    phase_fractions[phase]['fractions'].append(temp_phase_fractions[phase])

            except Exception as e:
                continue  # Hataları sessizce atla

        # Grafik çiz
        fig, ax = plt.subplots(figsize=(12, 8))

        # Her faz için çizgi çiz
        colors = plt.cm.Set1(np.linspace(0, 1, len(phase_fractions)))
        color_map = dict(zip(phase_fractions.keys(), colors))

        for phase, data in phase_fractions.items():
            if len(data['temps']) > 0:
                ax.plot(data['temps'], data['fractions'],
                        color=color_map[phase], label=phase,
                        linewidth=3, marker='o', markersize=3)

        ax.set_xlabel('Sıcaklık (°C)', fontsize=14)
        ax.set_ylabel('Faz Fraksiyonu', fontsize=14)
        ax.set_title(f'Vertical Section: Fe-{el1}-{el2}\n' +
                     f'Kompozisyon: %{composition_ratios["FE"] * 100:.1f} Fe, ' +
                     f'%{composition_ratios[el1] * 100:.1f} {el1}, ' +
                     f'%{composition_ratios[el2] * 100:.1f} {el2}', fontsize=16)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.05)

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        plt.tight_layout()
        plt.show()

        return fig

    def generate_phase_report(self, elements, compositions, temperature):
        """Sadece faz raporu oluştur"""
        eq, mole_fractions = self.calculate_equilibrium(elements, compositions, temperature)
        present_phases = np.unique(eq.Phase.values)
        stable_phases = set([p for p in present_phases if p != ''])

        report = f"""
═══════════════════════════════════════════════════════════════
                        FAZ ANALİZ RAPORU
═══════════════════════════════════════════════════════════════

🔧 SİSTEM: Fe-{'-'.join(elements)}
📊 KOMPOZİSYON: %{compositions['FE']*100:.1f} Fe, %{compositions[elements[0]]*100:.1f} {elements[0]}, %{compositions[elements[1]]*100:.1f} {elements[1]}
🌡️ SICAKLIK: {temperature:.1f}°C

✅ KARALI FAZLAR ({len(stable_phases)} adet):
"""
        for phase in sorted(stable_phases):
            report += f"   • {phase}\n"

        # Faz açıklamaları
        phase_descriptions = {
            'BCC_A2': 'Ferrit (α-demir) - Hacim merkezli kübik yapı',
            'FCC_A1': 'Östenit (γ-demir) - Yüzey merkezli kübik yapı',
            'M23C6': 'Krom-demir karbürü (M23C6 tipi)',
            'M7C3': 'Krom karbürü (M7C3 tipi)',
            'LIQUID': 'Sıvı faz',
            'CEMENTITE': 'Sementit (Fe3C)',
            'GRAPHITE': 'Grafit (saf karbon)'
        }

        report += f"\n📖 FAZ AÇIKLAMALARI:\n"
        for phase in sorted(stable_phases):
            if phase in phase_descriptions:
                report += f"   • {phase}: {phase_descriptions[phase]}\n"

        report += "\n═══════════════════════════════════════════════════════════════\n"
        return report


def main():
    # Veritabanı yolu
    db_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"

    # Sınıfı başlat
    vsa = VerticalSectionAnalyzer(db_path)

    # Kullanıcı arayüzü
    print("🔄 VERTICAL SECTION ANALİZİ")
    print("═" * 50)
    print("🔧 Mevcut elementler:", ', '.join(vsa.get_available_elements()))

    # Element seçimi
    element1 = input("\nBirinci element: ").strip().upper()
    element2 = input("İkinci element: ").strip().upper()
    elements = [element1, element2]

    # Kompozisyon girişi
    print(f"\n📊 Kompozisyon girişi:")
    wt1 = float(input(f"{element1} ağırlık %: ")) / 100
    wt2 = float(input(f"{element2} ağırlık %: ")) / 100
    wt_fe = 1 - (wt1 + wt2)

    if wt_fe < 0:
        print("❌ Toplam ağırlık %100'ü geçemez!")
        return

    compositions = {'FE': wt_fe, element1: wt1, element2: wt2}

    # Sıcaklık aralığı
    print(f"\n🌡️ Sıcaklık aralığı:")
    temp_min = float(input("Minimum sıcaklık (°C): "))
    temp_max = float(input("Maximum sıcaklık (°C): "))
    pressure= float(input("Basınç değerini giriniz (Pa): "))

    if temp_min >= temp_max:
        print("❌ Minimum sıcaklık maksimumdan küçük olmalı!")
        return

    # Vertical section çiz
    print(f"\n🔄 Vertical section çiziliyor ({temp_min}°C - {temp_max}°C)...")
    vsa.plot_vertical_section(elements, compositions, (temp_min, temp_max))

    # Rapor oluştur (orta sıcaklık için)
    mid_temp = (temp_min + temp_max) / 2
    print(f"\n📋 {mid_temp:.0f}°C için faz raporu:")
    report = vsa.generate_phase_report(elements, compositions, mid_temp)
    print(report)

    # Raporu kaydet
    save_report = input("Raporu dosyaya kaydet? (e/h): ").strip().lower()
    if save_report == 'e':
        filename = f"vertical_section_Fe-{element1}-{element2}_{temp_min}-{temp_max}C.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Rapor kaydedildi: {filename}")
        
def generate_ternary_vertical_api(element1, element2, weight_percent1, weight_percent2, temp_min, temp_max):
    """API için ternary vertical section oluştur"""
    
    # VerticalSectionAnalyzer kullan
    vsa = VerticalSectionAnalyzer(tdb_path)
    
    elements = [element1, element2]
    wt_fe = (100.0 - (weight_percent1 + weight_percent2)) / 100
    compositions = {
        'FE': wt_fe, 
        element1: weight_percent1 / 100, 
        element2: weight_percent2 / 100
    }
    
    # Plot oluştur
    fig = vsa.plot_vertical_section(elements, compositions, (temp_min, temp_max))
    
    # Base64'e çevir
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close(fig)
    
    return {
        "image_base64": image_base64,
        "stable_phases": [],  # Vertical section'dan extract edilebilir
        "system_info": f"Fe-{element1}-{element2}"
    }

if __name__ == "__main__":
    main()