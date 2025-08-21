# Phase_Configurator.py - Sadece ayar yapma dosyası
import json
import os
from pycalphad import Database


class PhaseConfigurator:
    def __init__(self, tdb_path, config_file="phase_config.json"):
        self.tdb_path = tdb_path
        self.config_file = config_file
        self.db = Database(tdb_path)
        self.load_config()

    def load_config(self):
        """Konfigürasyon dosyasını yükle"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            # Varsayılan konfigürasyon
            self.config = {
                "excluded_phases": ["GRAPHITE", "DIAMOND_A4", "SIGMA", "BCC_B2"],
                "phase_colors": {
                    "LIQUID": "gold",
                    "BCC_A2": "blue",
                    "FCC_A1": "black",
                    "CEMENTITE": "brown",
                    "M23C6": "red",
                    "M7C3": "orange",
                    "FCC_A1#2": "darkgreen"
                },
                "phase_labels": {
                    "CEMENTITE": "Cementite",
                    "BCC_A2": "Ferrit",
                    "FCC_A1": "Östenit",
                    "M23C6": "M₂₃C₆",
                    "M7C3": "M₇C₃"
                }
            }
            self.save_config()

    def save_config(self):
        """Konfigürasyonu kaydet"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
        print(f"💾 Ayarlar kaydedildi: {self.config_file}")

    def show_current_status(self):
        """Mevcut durumu göster"""
        all_phases = list(self.db.phases.keys())
        excluded = self.config.get("excluded_phases", [])
        active = [ph for ph in all_phases if ph not in excluded]

        print(f"📊 MEVCUT DURUM:")
        print(f"✅ Aktif fazlar ({len(active)}): {', '.join(active)}")
        print(f"❌ Çıkarılan fazlar ({len(excluded)}): {', '.join(excluded) if excluded else 'Hiçbiri'}")

    def interactive_setup(self):
        """Etkileşimli kurulum"""
        print("═" * 80)
        print("🔧 FAZ KONFIGÜRATÖRÜ")
        print("═" * 80)

        all_phases = list(self.db.phases.keys())
        excluded = self.config.get("excluded_phases", [])

        print(f"\n📋 TDB dosyasındaki tüm fazlar ({len(all_phases)}):")
        for i, phase in enumerate(all_phases, 1):
            status = "❌" if phase in excluded else "✅"
            print(f"  {i:2d}. {status} {phase}")

        self.show_current_status()

        while True:
            print(f"\n⚙️ Ne yapmak istiyorsunuz?")
            print("1. Hızlı seçenekler")
            print("2. Manuel faz çıkar/ekle")
            print("3. Tüm fazları aktif et")
            print("4. Varsayılan ayarlara dön")
            print("5. Ayarları kaydet ve çık")

            choice = input("Seçiminiz (1-5): ").strip()

            if choice == "1":
                self._quick_options()
            elif choice == "2":
                self._manual_phase_management()
            elif choice == "3":
                self.config["excluded_phases"] = []
                print("✅ Tüm fazlar aktif edildi!")
                self.show_current_status()
            elif choice == "4":
                self.config["excluded_phases"] = ["GRAPHITE", "DIAMOND_A4", "SIGMA", "BCC_B2"]
                print("✅ Varsayılan ayarlara döndürüldü!")
                self.show_current_status()
            elif choice == "5":
                self.save_config()
                break
            else:
                print("❌ Geçersiz seçim!")

    def _quick_options(self):
        """Hızlı seçenekler"""
        print(f"\n🚀 Hızlı seçenekler:")
        print("1. Karbon fazlarını çıkar (GRAPHITE, DIAMOND_A4)")
        print("2. İntermetalik fazları çıkar (SIGMA, BCC_B2, CHI_A12)")
        print("3. Varsayılan çıkarmalar (Karbon + İntermetalik)")
        print("4. Sadece temel fazlar (LIQUID, BCC_A2, FCC_A1, CEMENTITE)")
        print("5. Geri dön")

        choice = input("Seçiminiz (1-5): ").strip()

        if choice == "1":
            to_exclude = ["GRAPHITE", "DIAMOND_A4"]
        elif choice == "2":
            to_exclude = ["SIGMA", "BCC_B2", "CHI_A12"]
        elif choice == "3":
            to_exclude = ["GRAPHITE", "DIAMOND_A4", "SIGMA", "BCC_B2"]
        elif choice == "4":
            all_phases = list(self.db.phases.keys())
            keep_phases = ["LIQUID", "BCC_A2", "FCC_A1", "CEMENTITE"]
            to_exclude = [ph for ph in all_phases if ph not in keep_phases]
        elif choice == "5":
            return
        else:
            print("❌ Geçersiz seçim!")
            return

        self.config["excluded_phases"] = to_exclude
        print(f"✅ Ayarlandı! Çıkarılan fazlar: {to_exclude}")
        self.show_current_status()

    def _manual_phase_management(self):
        """Manuel faz yönetimi"""
        all_phases = list(self.db.phases.keys())
        excluded = self.config["excluded_phases"]

        print(f"\n📝 Manuel faz yönetimi:")
        print("1. Faz çıkar")
        print("2. Faz geri ekle")
        print("3. Geri dön")

        choice = input("Seçiminiz (1-3): ").strip()

        if choice == "1":
            active_phases = [ph for ph in all_phases if ph not in excluded]
            if not active_phases:
                print("❌ Çıkarılacak aktif faz yok!")
                return

            print(f"\n✅ Aktif fazlar:")
            for i, phase in enumerate(active_phases, 1):
                print(f"  {i}. {phase}")

            try:
                selection = int(input(f"Çıkarmak istediğiniz fazın numarası (1-{len(active_phases)}): "))
                if 1 <= selection <= len(active_phases):
                    phase = active_phases[selection - 1]
                    excluded.append(phase)
                    print(f"✅ {phase} çıkarıldı!")
                    self.show_current_status()
                else:
                    print("❌ Geçersiz numara!")
            except ValueError:
                print("❌ Lütfen geçerli bir numara girin!")

        elif choice == "2":
            if not excluded:
                print("❌ Geri eklenecek faz yok!")
                return

            print(f"\n❌ Çıkarılan fazlar:")
            for i, phase in enumerate(excluded, 1):
                print(f"  {i}. {phase}")

            try:
                selection = int(input(f"Geri eklemek istediğiniz fazın numarası (1-{len(excluded)}): "))
                if 1 <= selection <= len(excluded):
                    phase = excluded.pop(selection - 1)
                    print(f"✅ {phase} geri eklendi!")
                    self.show_current_status()
                else:
                    print("❌ Geçersiz numara!")
            except ValueError:
                print("❌ Lütfen geçerli bir numara girin!")


def get_phases_for_calculation(tdb_path, config_file="phase_config.json"):
    """
    Binary diagram için faz listesi al (otomatik)

    Returns:
        tuple: (active_phases, color_list, phase_labels)
    """
    # Konfigürasyon dosyası varsa oku
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        # Yoksa varsayılan ayarları kullan
        config = {
            "excluded_phases": ["GRAPHITE", "DIAMOND_A4", "SIGMA", "BCC_B2"],
            "phase_colors": {
                "LIQUID": "gold",
                "BCC_A2": "blue",
                "FCC_A1": "black",
                "CEMENTITE": "brown",
                "M23C6": "red",
                "M7C3": "orange"
            },
            "phase_labels": {
                "CEMENTITE": "Cementite",
                "BCC_A2": "Ferrit",
                "FCC_A1": "Östenit"
            }
        }

    # Aktif fazları hesapla
    db = Database(tdb_path)
    all_phases = list(db.phases.keys())
    excluded = config.get("excluded_phases", [])
    active_phases = [ph for ph in all_phases if ph not in excluded]

    # Renk listesi oluştur
    colors = config.get("phase_colors", {})
    color_list = [colors.get(ph, 'gray') for ph in active_phases]

    # Etiket sözlüğü
    phase_labels = config.get("phase_labels", {})

    return active_phases, color_list, phase_labels


# Ana program - Sadece konfigürasyon için
def main():
    print("🎯 FAZ KONFIGÜRATÖRÜ")
    print("Bu program faz ayarlarını yapmak içindir.")
    print("=" * 80)

    tdb_path = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"

    try:
        configurator = PhaseConfigurator(tdb_path)
        configurator.interactive_setup()

        print(f"\n🎉 FAS AYARLARI TAMAMLANDI!")
        print(f"📁 Ayarlar şu dosyada saklandı: {configurator.config_file}")
        print(f"💡 Artık Binary_Phase_Diagram.py dosyasını çalıştırabilirsiniz.")
        print(f"💡 O dosya bu ayarları otomatik olarak kullanacak.")

    except Exception as e:
        print(f"❌ Hata: {e}")
        input("Devam etmek için ENTER'a basın...")


if __name__ == "__main__":
    main()