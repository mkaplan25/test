# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
from pycalphad import Database, equilibrium
from pycalphad.variables import T, P, N, X


class TrueScheilGulliverModel:
    def __init__(self, tdb_file, elements_composition_wt):
        """
        Geliştirilmiş Scheil-Gulliver modeli (mol-kesri tabanlı)
        - wt.% -> mol kesri dönüşümü
        - Solidus'a kadar ilerleme için sağlam geri-deneme
        - NP ağırlıklı C_L* ve C_S* tahmini
        - Uyarlamalı df_s
        """
        self.db = Database(tdb_file)

        # Kullanıcı girdisi (FE hariç, wt.%)
        self.elements_composition_wt = elements_composition_wt  # örn: {'C':1.0, 'MN':1.0}

        # Atomik ağırlıklar (g/mol) - kullanılan yaygın elementler
        self.atomic_wt = {
            'FE': 55.845, 'C': 12.011, 'MN': 54.938, 'CR': 51.996, 'NI': 58.693, 'CO': 58.933,
            'SI': 28.085, 'AL': 26.982, 'N': 14.007, 'B': 10.81, 'MO': 95.95, 'NB': 92.906,
            'TI': 47.867, 'V': 50.942, 'W': 183.84, 'CU': 63.546, 'O': 15.999, 'P': 30.974,
            'S': 32.06, 'LA': 138.905, 'HF': 178.49, 'PD': 106.42, 'TA': 180.948, 'Y': 88.906
        }

        # Çalışma bileşen listesi
        self.comps = ['FE'] + list(elements_composition_wt.keys()) + ['VA']

        # Scheil parametreleri
        self.df_solid_step = 0.005       # hedef adım: %0.5 katılaşma
        self.min_liquid_fraction = 0.001 # sıvı kalıntısı eşiği

        # Sonuç depolama (mol %)
        self.results = {
            'temperature': [],
            'liquid_fraction': [],
            'solid_fraction': [],
            'liquid_composition': {},               # C_L* (mol %)
            'solid_interface_composition': {},      # C_S* (mol %)
            'cumulative_solid_composition': {},     # ort. katı (mol %)
            'partition_coefficients': {},           # k = C_S*/C_L*
        }
        for el in ['FE'] + list(elements_composition_wt.keys()):
            self.results['liquid_composition'][el] = []
            self.results['solid_interface_composition'][el] = []
            self.results['cumulative_solid_composition'][el] = []
            self.results['partition_coefficients'][el] = []

        # Faz takibi
        self.phase_history = []   # yeni fazların ilk göründüğü anlar
        self.phase_evolution = [] # her adımda faz payları
        self.phase_map = {
            'BCC_A2': 'δ-Ferrit/α-Ferrit',
            'FCC_A1': 'γ-Austenit',
            'CEMENTITE': 'Fe3C (Sementit)',
            'LIQUID': 'Sıvı',
            'SIGMA': 'σ (Sigma)',
            'BCC_B2': 'Düzenli BCC',
            'M23C6': 'M23C6',
            'M7C3': 'M7C3',
            'M3C2': 'M3C2',
            'M6C': 'M6C',
            'MU_PHASE': 'μ',
            'LAVES_PHASE': 'Laves',
            'CHI_A12': 'χ',
            'GRAPHITE': 'Grafit'
        }

        # wt.% -> mol kesri başlangıç dönüşümü
        self.initial_molf = self.wt_to_molf(self.elements_composition_wt)   # FE dahil, toplam=1
        self.initial_molf_no_fe = {el: mf for el, mf in self.initial_molf.items() if el != 'FE'}

    # ---------- Yardımcı dönüşümler ----------
    def wt_to_molf(self, wt_dict_without_fe):
        """wt.% -> mol kesri (FE dahil, toplam=1)"""
        wt_fe = 100.0 - float(sum(wt_dict_without_fe.values()))
        masses = dict(wt_dict_without_fe)
        masses['FE'] = wt_fe
        # mol sayıları
        moles = {el: masses[el] / self.atomic_wt[el] for el in masses}
        tot = sum(moles.values())
        return {el: moles[el] / tot for el in moles}

    # ---------- PyCalphad denge adımları ----------
    def get_liquidus_temperature(self):
        """Liquidus sıcaklığını bul (mol kesri ile)"""
        print("Liquidus sıcaklığı aranıyor...")

        # Sadece L ve birincil katının devrede olduğu sade faz seti
        phases_probe = ['LIQUID', 'FCC_A1', 'BCC_A2']
        phases_probe = [p for p in phases_probe if p in self.db.phases.keys()]

        # Geniş arama
        for temp in np.linspace(1800, 1200, 120):
            try:
                cond = {T: temp, P: 101325, N: 1,
                        **{X(el): mf for el, mf in self.initial_molf_no_fe.items()}}
                eq = equilibrium(self.db, self.comps, phases_probe, cond)
                if 'LIQUID' in np.unique(eq.Phase.values):
                    fL = float(np.nan_to_num(eq.NP.where(eq.Phase == 'LIQUID', drop=True)).sum())
                    print(f"  T={temp:.1f}K ({temp-273.15:.1f}°C): f_L={fL:.4f}")
                    if fL < 0.999:  # ilk katı oluştu
                        print(f"Liquidus bulundu: {temp:.1f}K ({temp-273.15:.1f}°C)")
                        return temp
            except Exception:
                continue

        print("Liquidus bulunamadı; 1600K varsayılıyor.")
        return 1600.0

    def _weighted_interface(self, eq, phase_name, element):
        """Belirtilen faz ve element için NP ağırlıklı arayüz kompozisyonu (mol kesri)"""
        x = eq.X.sel(component=element).where(eq.Phase == phase_name, drop=True)
        w = eq.NP.where(eq.Phase == phase_name, drop=True)
        if getattr(x, 'size', 0) > 0 and getattr(w, 'size', 0) > 0 and float(np.nansum(w)) > 0:
            return float(np.nansum(x * w) / np.nansum(w))
        return np.nan

    def equilibrium_step(self, temp, liquid_comp_molf):
        """
        Verilen T'de L + S dengesi.
        Geriye: C_L* dict, C_S* dict, toplam katı fraksiyonu, faz bilgileri
        (Tüm kompozisyonlar mol kesri)
        """
        # Normalize et (güvenlik)
        tot = float(sum(liquid_comp_molf.values()))
        comp_all = {el: max(0.0, liquid_comp_molf[el] / tot) for el in liquid_comp_molf}

        # PyCalphad şartları (FE hariç X verilir)
        cond = {T: temp, P: 101325, N: 1,
                **{X(el): mf for el, mf in comp_all.items() if el != 'FE'}}

        # Zengin faz kümesi
        phases_all = ['LIQUID', 'FCC_A1', 'BCC_A2', 'CEMENTITE', 'GRAPHITE',
                      'M7C3', 'M23C6', 'M6C', 'M3C2', 'SIGMA', 'MU_PHASE',
                      'LAVES_PHASE', 'CHI_A12']
        phases_all = [p for p in phases_all if p in self.db.phases.keys()]

        try:
            eq = equilibrium(self.db, self.comps, phases_all, cond)
        except Exception as e:
            print(f"  Denge hatası @T={temp:.1f}K: {str(e)[:60]}...")
            return None, None, None, []

        uniq = np.unique(eq.Phase.values)
        if 'LIQUID' not in uniq:
            return None, None, None, []

        # Katı fazlar ve payları
        phase_info = []
        for ph in uniq:
            if ph in ['', 'LIQUID', 'VA']:
                continue
            frac = float(np.nan_to_num(eq.NP.where(eq.Phase == ph, drop=True)).sum())
            if frac > 1e-8:
                phase_info.append({
                    'name': ph,
                    'display_name': self.phase_map.get(ph, ph),
                    'fraction': frac,
                    'temperature': temp
                })

        if not phase_info:
            return None, None, None, []

        # Birincil katı = en büyük pay
        primary_solid = max(phase_info, key=lambda x: x['fraction'])['name']

        # Arayüz kompozisyonları (NP ağırlıklı)
        C_l_star = {}
        C_s_star = {}
        for el in comp_all.keys():
            # Sıvı
            valL = self._weighted_interface(eq, 'LIQUID', el)
            C_l_star[el] = float(valL) if not np.isnan(valL) else comp_all.get(el, 0.0)
            # Birincil katı
            valS = self._weighted_interface(eq, primary_solid, el)
            C_s_star[el] = float(valS) if not np.isnan(valS) else C_l_star[el]

        # Toplam katı fraksiyonu
        f_s_total = float(sum(p['fraction'] for p in phase_info))
        return C_l_star, C_s_star, f_s_total, phase_info

    # ---------- Faz takibi ----------
    def track_phase_evolution(self, temp, f_s, phase_info):
        step = {'temperature': temp, 'solid_fraction': f_s, 'phases': {}}
        for ph in phase_info:
            step['phases'][ph['name']] = {'fraction': ph['fraction'],
                                          'display_name': ph['display_name']}
            names = [p['name'] for p in self.phase_history]
            if ph['name'] not in names and ph['fraction'] > 1e-4:
                self.phase_history.append({
                    'name': ph['name'],
                    'display_name': ph['display_name'],
                    'first_appearance_temp': temp,
                    'first_appearance_temp_celsius': temp - 273.15,
                    'first_appearance_f_s': f_s,
                    'initial_fraction': ph['fraction']
                })
                print(f"  Yeni faz: {ph['display_name']} @ {temp-273.15:.1f}°C | oran={ph['fraction']:.4f}")
        self.phase_evolution.append(step)

    # ---------- Scheil kütle dengesi ----------
    def scheil_mass_balance(self, C_l_old, C_s_star, f_s_old, df_s):
        """
        C_l_new = (C_l_old*(1-f_s_old) - C_s_star*df_s) / ((1-f_s_old) - df_s)
        (mol kesri)
        """
        C_l_new = {}
        denom = (1.0 - f_s_old) - df_s
        for el in C_l_old.keys():
            num = C_l_old[el] * (1.0 - f_s_old) - C_s_star[el] * df_s
            C_l_new[el] = num / denom if denom > 1e-12 else C_l_old[el]
            C_l_new[el] = max(0.0, min(1.0, C_l_new[el]))
        # normalize
        tot = sum(C_l_new.values())
        return {el: (C_l_new[el] / tot if tot > 0 else C_l_new[el]) for el in C_l_new}

    def update_cumulative_solid(self, C_avg_old, C_s_star, f_s_old, df_s):
        """C_avg_new = (C_avg_old*f_s_old + C_s_star*df_s) / (f_s_old + df_s)"""
        f_s_new = f_s_old + df_s
        out = {}
        for el in C_avg_old.keys():
            out[el] = ((C_avg_old[el] * f_s_old + C_s_star[el] * df_s) / f_s_new) if f_s_new > 1e-12 else C_s_star[el]
        return out

    # ---------- Ana döngü ----------
    def run_scheil_calculation(self):
        print("Gerçek Scheil-Gulliver hesaplaması başlıyor...")
        liquidus = self.get_liquidus_temperature()

        # Başlangıç: sıvı kompozisyonu mol kesri (FE dahil toplam=1)
        C_l = dict(self.initial_molf)
        f_s = 0.0
        temp = liquidus

        # Bilgi
        print("\nBaşlangıç (mol %):")
        for el, mf in C_l.items():
            print(f"  {el}: {mf*100:.3f} mol %")
        print(f"\nAdım boyu hedefi: df_s={self.df_solid_step}")

        step_count = 0
        fail_count = 0
        max_steps = 5000

        while f_s < (1.0 - self.min_liquid_fraction) and step_count < max_steps and temp > 1000:
            result = self.equilibrium_step(temp, C_l)
            if result is None or result[0] is None:
                # denge başarısız: daha fazla soğut, biraz esne
                fail_count += 1
                if fail_count < 10:
                    temp -= 2.0
                    continue
                else:
                    print("  Art arda 10 denge başarısızlığı. Döngü sonlandırılıyor.")
                    break
            fail_count = 0
            C_l_star, C_s_star, f_s_eq, phase_info = result

            # Faz takibi
            if phase_info:
                self.track_phase_evolution(temp, f_s, phase_info)

            # Uyarlamalı df_s
            if f_s_eq > f_s:
                df_s = min(self.df_solid_step, max(1e-3, f_s_eq - f_s), 1.0 - f_s - self.min_liquid_fraction)
            else:
                temp -= 1.0
                continue

            if df_s <= 1e-6:
                temp -= 1.0
                continue

            # Scheil güncellemeleri
            C_l = self.scheil_mass_balance(C_l, C_s_star, f_s, df_s)
            # Kümülatif katı
            if step_count == 0:
                C_avg = {el: C_s_star[el] for el in C_l.keys()}
            else:
                C_avg = self.update_cumulative_solid(C_avg, C_s_star, f_s, df_s)

            # k katsayıları
            k_vals = {}
            for el in C_l.keys():
                k_vals[el] = (C_s_star[el] / C_l_star[el]) if C_l_star[el] > 1e-14 else 1.0

            # Sonuç kaydı
            self.results['temperature'].append(temp)
            self.results['liquid_fraction'].append(1.0 - f_s)
            self.results['solid_fraction'].append(f_s)
            for el in C_l.keys():
                self.results['liquid_composition'][el].append(C_l_star[el] * 100.0)          # mol %
                self.results['solid_interface_composition'][el].append(C_s_star[el] * 100.0)  # mol %
                self.results['cumulative_solid_composition'][el].append(C_avg[el] * 100.0)    # mol %
                self.results['partition_coefficients'][el].append(k_vals[el])

            # durum güncelle
            f_s += df_s
            temp -= 1.0
            step_count += 1

            if step_count % 100 == 0:
                cL = self.results['liquid_composition'].get('C', [])
                kmn = self.results['partition_coefficients'].get('MN', [])
                msg_c = f"C_L*(C)={cL[-1]:.3f} mol %" if cL else ""
                msg_kmn = f"k_MN={kmn[-1]:.3f}" if kmn else ""
                print(f"  Adım {step_count}: T={temp-273.15:.1f}°C, f_s={f_s:.3f}  {msg_c}  {msg_kmn}")

        print("\nScheil hesaplaması tamamlandı.")
        print(f"  Toplam adım: {step_count}")
        print(f"  Son sıcaklık: {temp:.1f} K ({temp-273.15:.1f} °C)")
        print(f"  Son katı fraksiyon: {f_s:.4f}")
        print(f"  Katılaşma aralığı: {liquidus - temp:.1f} K")

    # ---------- Raporlama ----------
    def print_phase_sequence(self):
        if not self.phase_history:
            print("Faz dizisi bilgisi yok.")
            return

        print("\n" + "=" * 80)
        print("KATILAŞMA SIRASI – FAZ DİZİSİ")
        print("=" * 80)
        comp_str = " + ".join([f"{el}({pct:.2f} wt%)" for el, pct in self.elements_composition_wt.items()])
        print(f"Fe + {comp_str}\n")

        for i, ph in enumerate(self.phase_history, 1):
            print(f"{i}. {ph['display_name']} ({ph['name']})")
            print(f"   İlk görünüm: {ph['first_appearance_temp_celsius']:.1f} °C")
            print(f"   Katı fraksiyon: {ph['first_appearance_f_s']:.3f}")
            print(f"   Başlangıç oranı: {ph['initial_fraction']:.4f}")

    def print_summary(self):
        if not self.results['temperature']:
            print("Özet için veri yok.")
            return

        print("\n" + "=" * 60)
        print("SCHEIL-GULLIVER ANALİZİ ÖZETİ")
        print("=" * 60)

        print("Başlangıç (wt.%):")
        for el, pct in self.elements_composition_wt.items():
            print(f"  {el}: {pct:.2f} wt%")
        print("Başlangıç (mol %):")
        for el, mf in self.initial_molf.items():
            print(f"  {el}: {mf*100:.3f} mol %")

        liq = max(self.results['temperature'])
        sol = min(self.results['temperature'])
        print("\nKatılaşma aralığı:")
        print(f"  Liquidus: {liq:.1f} K ({liq-273.15:.1f} °C)")
        print(f"  Solidus : {sol:.1f} K ({sol-273.15:.1f} °C)")
        print(f"  Aralık  : {liq-sol:.1f} K")

        print("\nMikro-segregasyon (son C_L*, mol %):")
        for el in self.elements_composition_wt.keys():
            arr = self.results['liquid_composition'].get(el, [])
            if arr:
                final_molpct = arr[-1]
                ini_molpct = self.initial_molf.get(el, 0.0) * 100.0
                enr = (final_molpct / ini_molpct) if ini_molpct > 0 else 1.0
                print(f"  {el}: {final_molpct:.3f} mol % (x{enr:.1f} zenginleşme)")

        print("\nOrtalama k katsayıları:")
        for el in self.elements_composition_wt.keys():
            ks = self.results['partition_coefficients'].get(el, [])
            if ks:
                print(f"  k_{el} = {np.mean(ks):.3f}")

    def print_phase_evolution_summary(self):
        if not self.phase_history:
            print("Faz evrimi özeti için veri yok.")
            return

        print("\n" + "=" * 60)
        print("FAZ EVRİMİ ÖZETİ")
        print("=" * 60)
        for i, ph in enumerate(self.phase_history, 1):
            print(f"{i}. {ph['display_name']}")
            print(f"   İlk oluşum: {ph['first_appearance_temp_celsius']:.1f} °C")
            print(f"   Katı fraksiyon: {ph['first_appearance_f_s']:.3f}")
            print(f"   İlk oran: {ph['initial_fraction']:.4f}")

    # ---------- Grafikler ----------
    def plot_phase_evolution(self):
        if not self.phase_evolution:
            print("Faz evrimi verisi yok.")
            return

        temps = [s['temperature'] - 273.15 for s in self.phase_evolution]
        solid_fracs = [s['solid_fraction'] for s in self.phase_evolution]

        # Faz oranları (ayrı grafik)
        plt.figure(figsize=(12, 8))
        ax = plt.gca()
        all_phases = set()
        for s in self.phase_evolution:
            all_phases.update(s['phases'].keys())

        color_map = {
            'BCC_A2': '#d35400', 'FCC_A1': '#2980b9', 'CEMENTITE': '#27ae60',
            'M7C3': '#f39c12', 'M23C6': '#8e44ad', 'SIGMA': '#c0392b',
            'GRAPHITE': '#2c3e50'
        }

        for ph in all_phases:
            series = []
            tt = []
            for s in self.phase_evolution:
                series.append(s['phases'].get(ph, {'fraction': 0.0})['fraction'])
                tt.append(s['temperature'] - 273.15)
            if max(series) > 1e-4:
                ax.plot(tt, series, lw=3, color=color_map.get(ph, '#7f8c8d'),
                        label=self.phase_map.get(ph, ph))
        ax.set_xlabel('Sıcaklık (°C)')
        ax.set_ylabel('Faz Oranı (katı içindeki pay)')
        ax.set_title('Faz Evrimi – Her Fazın Katı İçindeki Oranı')
        ax.grid(True, alpha=0.4, ls='--')
        ax.legend()
        plt.tight_layout()
        plt.show()

        # Katılaşma eğrisi
        plt.figure(figsize=(12, 8))
        ax2 = plt.gca()
        ax2.plot(temps, solid_fracs, lw=4, label='Toplam Katı Fraksiyon')
        ax2.plot(temps, [1.0 - s for s in solid_fracs], lw=4, label='Sıvı Fraksiyon')
        for i, ph in enumerate(self.phase_history):
            ax2.axvline(ph['first_appearance_temp_celsius'], color=color_map.get(ph['name'], f'C{i}'),
                        ls='--', lw=2, alpha=0.7)
            ax2.text(ph['first_appearance_temp_celsius'], 0.9 - 0.1*(i % 5),
                     f"{ph['display_name']}\n{ph['first_appearance_temp_celsius']:.0f}°C",
                     ha='center', va='center', fontsize=10,
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
        ax2.set_xlabel('Sıcaklık (°C)')
        ax2.set_ylabel('Fraksiyon')
        ax2.set_title('Katılaşma Eğrisi ve Faz Başlangıçları')
        ax2.grid(True, alpha=0.4, ls='--')
        ax2.legend()
        plt.tight_layout()
        plt.show()

    def plot_results(self):
        if not self.results['temperature']:
            print("Grafikler için sonuç yok.")
            return

        temps_c = [t - 273.15 for t in self.results['temperature']]

        # Faz evrimi grafikleri
        self.plot_phase_evolution()

        # 1) Katılaşma eğrisi (mol kesri)
        plt.figure(figsize=(10, 6))
        plt.plot(temps_c, self.results['liquid_fraction'], 'b-', lw=3, label='Sıvı Faz')
        plt.plot(temps_c, self.results['solid_fraction'], 'r-', lw=3, label='Katı Faz')
        plt.xlabel('Sıcaklık (°C)')
        plt.ylabel('Faz Oranı')
        title_comp = "-".join([f"{el}{pct}" for el, pct in self.elements_composition_wt.items()])
        plt.title(f'Scheil-Gulliver Katılaşma Eğrisi\nFe-{title_comp}')
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout(); plt.show()

        # 2) Sıvı arayüz kompozisyonu (mol %)
        plt.figure(figsize=(10, 6))
        colors = ['#2c3e50', '#16a085', '#8e44ad', '#e67e22', '#c0392b', '#1abc9c']
        i = 0
        for el in self.elements_composition_wt.keys():
            arr = self.results['liquid_composition'].get(el, [])
            if arr:
                plt.plot(temps_c, arr, lw=3, color=colors[i % len(colors)], label=f'{el} (Sıvı Arayüz)')
                i += 1
        plt.xlabel('Sıcaklık (°C)'); plt.ylabel('Konsantrasyon (mol %)')
        plt.title('Sıvı Arayüz Kompozisyonu – Mikro Segregasyon (C_L*)')
        plt.yscale('log'); plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout(); plt.show()

        # 3) Katı arayüz kompozisyonu (mol %)
        plt.figure(figsize=(10, 6))
        i = 0
        for el in self.elements_composition_wt.keys():
            arr = self.results['solid_interface_composition'].get(el, [])
            if arr:
                plt.plot(self.results['solid_fraction'], arr, lw=3, color=colors[i % len(colors)],
                         label=f'{el} (Katı Arayüz)')
                i += 1
        plt.xlabel('Katı Faz Oranı'); plt.ylabel('Konsantrasyon (mol %)')
        plt.title('Katı Arayüz Kompozisyonu – Dendrit Kenarı (C_S*)')
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout(); plt.show()

        # 4) Ortalama katı kompozisyonu (mol %)
        plt.figure(figsize=(10, 6))
        i = 0
        for el in self.elements_composition_wt.keys():
            arr = self.results['cumulative_solid_composition'].get(el, [])
            if arr:
                plt.plot(self.results['solid_fraction'], arr, lw=3, ls='--',
                         color=colors[i % len(colors)], label=f'{el} (Ortalama Katı)')
                # başlangıç mol %
                plt.axhline(self.initial_molf.get(el, 0.0) * 100.0, color=colors[i % len(colors)],
                            ls=':', lw=2, alpha=0.7, label=f'{el} (Başlangıç mol %)')
                i += 1
        plt.xlabel('Katı Faz Oranı'); plt.ylabel('Konsantrasyon (mol %)')
        plt.title('Ortalama Katı Kompozisyonu')
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout(); plt.show()

        # 5) Bölünme katsayıları
        plt.figure(figsize=(10, 6))
        i = 0
        for el in self.elements_composition_wt.keys():
            ks = self.results['partition_coefficients'].get(el, [])
            if ks:
                plt.plot(temps_c, ks, lw=3, color=colors[i % len(colors)], label=f'k_{el}=C_S*/C_L*')
                i += 1
        plt.axhline(1.0, color='k', ls='--', alpha=0.5, label='k=1 (segregasyon yok)')
        plt.xlabel('Sıcaklık (°C)'); plt.ylabel('Bölünme Katsayısı (k)')
        plt.title('Bölünme Katsayıları')
        plt.legend(); plt.grid(True, alpha=0.3); plt.tight_layout(); plt.show()

    def generate_comprehensive_report(self):
        self.print_summary()
        self.print_phase_sequence()
        self.print_phase_evolution_summary()


# ---------------------- Komut satırı kullanımı ----------------------
if __name__ == "__main__":
    # Kullanıcıdan FE harici elementler (wt.%) alınır
    available_elements = ['AL', 'B', 'C', 'CO', 'CR', 'CU', 'H', 'HF', 'LA', 'MN', 'MO',
                          'N', 'NB', 'NI', 'O', 'P', 'PD', 'S', 'SI', 'TA', 'TI', 'V', 'W', 'Y']

    print("Mevcut elementler:", ", ".join(available_elements))
    n = int(input(f"FE haricinde kaç element eklemek istiyorsunuz? (1-{len(available_elements)}) "))
    if n < 1 or n > len(available_elements):
        print("Geçersiz sayı."); raise SystemExit

    selected = {}
    for i in range(n):
        el = input(f"{i+1}. elementi seçin: ").strip().upper()
        if el not in available_elements or el in selected:
            print("Geçersiz/tekrar eden element."); raise SystemExit
        pct = float(input(f"{el} için ağırlıkça yüzde girin (%): "))
        selected[el] = pct

    if sum(selected.values()) >= 100.0:
        print("Toplam wt.% 100'ü geçemez."); raise SystemExit

    tdb_file = r"C:\Users\user\PycharmProjects\AlloyCraft\Termodinamik\FeC.tdb"
    print(f"\n{selected} (wt.%) kompozisyonlu Fe alaşımı için Scheil-Gulliver analizi başlıyor...")

    model = TrueScheilGulliverModel(tdb_file, selected)
    try:
        model.run_scheil_calculation()
        model.generate_comprehensive_report()
        print("\nGrafikler çiziliyor...")
        model.plot_results()
        print("\nTamamlandı.")
    except Exception as e:
        print(f"Hata: {e}")
    finally:
        print("Program sonlandırıldı.")
