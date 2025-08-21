import matplotlib.pyplot as plt
from pycalphad import Database, binplot, variables as v
from matplotlib.ticker import FuncFormatter
import warnings
import io
import base64

# 🆕 Otomatik faz yöneticisi import
from Phase_Configurator import get_phases_for_calculation

# TDB yükle
tdb_path = r"/Users/kaplan/Desktop/AlloyCraft-yeni/Termodinamik/FeC.tdb"
db = Database(tdb_path)

# Molar kütleler
molar_masses = {
    'FE': 55.845, 'C': 12.01, 'CR': 51.996, 'MN': 54.938, 'SI': 28.085,
    'MO': 95.95, 'V': 50.942, 'AL': 26.98, 'CU': 63.55, 'TI': 47.867,
    'NB': 92.91, 'W': 183.84
}

def mol_to_wt_percent(x_mol, element_x):
    M_FE = molar_masses['FE']
    M_X = molar_masses[element_x]
    mol_fe = 1 - x_mol
    g_fe = mol_fe * M_FE
    g_x = x_mol * M_X
    return (g_x / (g_fe + g_x)) * 100

def generate_binary_diagram(element_x, x_axis_type="mol", y_axis_type="celsius", 
                          x_range=(0, 0.25, 0.002), temp_range=(300, 1873, 10)):
    """
    Binary faz diyagramı oluşturur ve base64 string olarak döndürür
    """
    
    # Element validasyonu
    elements = sorted(set(str(el) for el in db.elements if str(el) != 'VA'))
    if element_x not in elements:
        raise ValueError(f"Element {element_x} TDB dosyasında bulunamadı")
    
    # Kompozisyon aralığı ayarlama
    if element_x == 'C' and x_range[1] > 0.25:
        x_range = (0, 0.25, 0.002)
    
    components = ['FE', element_x, 'VA']
    conds = {
        v.N: 1, 
        v.P: 101325, 
        v.T: temp_range, 
        v.X(element_x): x_range
    }
    
    # Faz konfigürasyonu
    allowed_phases, color_list, phase_labels = get_phases_for_calculation(tdb_path)
    
    # Çizim
    plt.figure(figsize=(10, 6))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        binplot(
            db,
            components,
            allowed_phases,
            conds,
            colorlist=color_list,
            labels=phase_labels
        )
    
    ax = plt.gca()
    
    # X ekseni ayarları
    if x_axis_type == "wt":
        xticks = ax.get_xticks()
        xticks_percent = [mol_to_wt_percent(x, element_x) for x in xticks]
        ax.set_xticks(xticks)
        ax.set_xticklabels([f"{wt:.1f}" for wt in xticks_percent])
        x_label = f"{element_x} İçeriği (wt%)"
    else:
        x_label = f"Mol Fraksiyonu {element_x}"
    
    ax.set_xlabel(x_label)
    
    # Y ekseni ayarları
    if y_axis_type == "celsius":
        ax.yaxis.set_major_formatter(FuncFormatter(lambda t, _: f"{t - 273.15:.0f}"))
        y_label = "Sıcaklık (°C)"
    else:
        y_label = "Sıcaklık (K)"
    
    ax.set_ylabel(y_label)
    
    title = f"Fe–{element_x} Faz Diyagramı"
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()
    
    # Base64'e çevir
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return {
        "image_base64": image_base64,
        "x_label": x_label,
        "y_label": y_label,
        "title": title
    }