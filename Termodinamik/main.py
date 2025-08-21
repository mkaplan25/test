from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import matplotlib
matplotlib.use('Agg')  # GUI olmayan backend
import matplotlib.pyplot as plt
import io
import base64
from Binary_Phase_Diagram.Binary_Phase_Diagram import generate_binary_diagram
from uuid import uuid4
from typing import Dict, Any
import io
import contextlib
from fastapi.responses import JSONResponse
import io
import base64
import numpy as np
from pycalphad import Database, equilibrium, variables as v, ternplot
from Ternary_Phase_Diagram.Ternary_Isothermal import generate_ternary_isothermal_api
from Ternary_Phase_Diagram.Ternary_Vertical import generate_ternary_vertical_api

SINGLE_POINT_SESSIONS: Dict[str, Dict[str, Any]] = {}

def _call_and_capture(fn, *args, **kwargs):
    """CLI'de print eden fonksiyonların çıktısını UTF-8 olarak yakala"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ret = fn(*args, **kwargs)
    text = buf.getvalue()
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='replace')  # Bozuk karakterleri '?' ile değiştir
    return ret if ret is not None else {"text": text.strip()}
  

app = FastAPI(title="AlloyCraft Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class BinaryDiagramRequest(BaseModel):
    element_x: str  # ikinci element (C, CR, MN vs.)
    x_axis_type: str = "mol"  # "mol" veya "wt"
    y_axis_type: str = "celsius"  # "kelvin" veya "celsius"
    x_range_start: float = 0.0
    x_range_end: float = 0.25
    x_range_step: float = 0.002
    temp_min: float = 300.0
    temp_max: float = 1873.0

class BinaryDiagramResponse(BaseModel):
    success: bool
    message: str
    diagram_base64: Optional[str] = None
    element_pair: str
    x_axis_label: str
    y_axis_label: str

@app.get("/")
async def root():
    return {"message": "AlloyCraft Backend API"}

@app.get("/available-elements")
async def get_available_elements():
    """Kullanılabilir elementleri döndür"""
    elements = ['C', 'CR', 'MN', 'SI', 'MO', 'V', 'AL', 'CU', 'TI', 'NB', 'W']
    return {"available_elements": elements}

@app.post("/binary-phase-diagram", response_model=BinaryDiagramResponse)
async def create_binary_diagram(request: BinaryDiagramRequest):
    """Binary faz diyagramı oluştur"""
    try:
        # Binary_Phase_Diagram.py'den fonksiyon çağır
        diagram_data = generate_binary_diagram(
            element_x=request.element_x,
            x_axis_type=request.x_axis_type,
            y_axis_type=request.y_axis_type,
            x_range=(request.x_range_start, request.x_range_end, request.x_range_step),
            temp_range=(request.temp_min, request.temp_max, 10)
        )
        
        return BinaryDiagramResponse(
            success=True,
            message="Diyagram başarıyla oluşturuldu",
            diagram_base64=diagram_data["image_base64"],
            element_pair=f"Fe-{request.element_x}",
            x_axis_label=diagram_data["x_label"],
            y_axis_label=diagram_data["y_label"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Diyagram oluşturma hatası: {str(e)}")
    
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from pydantic import BaseModel
from Main_Parameters.All_parameters import (
    main_calculation,
    analyze_results,
    calculate_additional_properties,
    db  # db'yi All_parameters'tan import et
)

class SinglePointRequest(BaseModel):
    elements: List[str]                # ['FE', 'C', 'CR']
    weight_percents: Dict[str, float]  # {'FE': 80.0, 'C': 15.0, 'CR': 5.0}
    temperature_c: float
    pressure_pa: float = 100000.0


class SinglePointResponse(BaseModel):
    success: bool
    message: str
    results: Optional[Dict[str, Any]] = None
    basic_properties: Optional[Dict[str, Any]] = None
    phase_data: Optional[List[Dict[str, Any]]] = None
    stable_phases: Optional[List[str]] = None
    additional_properties: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None   # <-- EKLE


from Main_Parameters.All_parameters import (
    main_calculation,
    analyze_results,
    calculate_additional_properties,
    db
)

@app.post("/single-point-calculation", response_model=SinglePointResponse)
async def calculate_single_point(request: SinglePointRequest):
    try:
        elements = [e.upper() for e in request.elements]
        wt_percents = {k.upper(): v for k, v in request.weight_percents.items()}
        
        T_K = request.temperature_c + 273.15
        P = request.pressure_pa

        eq, elements, wt_percents, X, T_K, P, phases, components = main_calculation(
            elements=elements,
            wt_percents=wt_percents,
            temperature_K=T_K,
            pressure_Pa=P
        )

        results = analyze_results(eq, elements, wt_percents, X, T_K, P, phases, components)
        additional_props = calculate_additional_properties(
            results, db, T_K, P, X, elements, components, phases
        )
        
        sid = str(uuid4())
        SINGLE_POINT_SESSIONS[sid] = {
            "eq": eq,
            "results": results,
            "additional_props": additional_props,
            "T_K": T_K,
            "P": P,
            "X": X,
            "elements": elements,
            "components": components,
            "phases": phases,
            "wt_percents": wt_percents,
            "session_id": sid
        }

        return SinglePointResponse(
            success=True,
            message="Hesaplama başarıyla tamamlandı",
            results={
                "temperature_k": T_K,
                "temperature_c": request.temperature_c,
                "pressure_pa": P,
                "composition": wt_percents,
            },
            basic_properties=results['basic_props'],
            phase_data=results['phase_data'],
            stable_phases=results['stable_phases'],
            additional_properties=additional_props,
            session_id=sid,
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Single Point hesaplama hatası: {str(e)}")
# === EKLE: Tek nokta analiz endpoint'i ===
class SinglePointAnalysisRequest(BaseModel):
    session_id: str
    menu_choice: int  # 1..33

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    payload: Any | None = None

@app.post("/single-point-analysis", response_model=AnalysisResponse)
async def single_point_analysis(req: SinglePointAnalysisRequest):
    from Main_Parameters.All_parameters import (
        density,
        show_density_phases,
        show_volume_data_system,
        show_volume_data_phase,
        show_component_amounts,
        show_phase_weight_fractions,
        show_driving_forces,
        show_u_fractions,
        show_site_fractions_thermocalc_style,
        show_chemical_potentials,
        show_clean_phase_referenced_analysis,
        show_activities,
        show_phase_ref_activities,
        show_phase_properties,
        curie_temperature,
        show_bohr_magneton_with_site_fractions,
        show_helmholtz,
        show_system_gibbs_energy,
        show_system_enthalpy,
        show_system_entropy,
        show_system_internal_energy,
        show_system_heat_capacity,
        show_electrical_resistance,
        show_electrical_conductivity,
        show_thermal_conductivity,
        show_thermal_diffusity,
        show_thermal_resistance,
        show_thermal_expansion,
        show_young_modulus,
        show_shear_modulus,
        show_bulk_modulus,
        show_poisson_ratio,
        show_surface_tension_properties,
        db,  # bazı fonksiyonlar için lazım
    )

    ctx = SINGLE_POINT_SESSIONS.get(req.session_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    results = ctx["results"]
    additional_props = ctx["additional_props"]
    T_K = ctx["T_K"]
    P = ctx["P"]
    X = ctx["X"]
    elements = ctx["elements"]
    components = ctx["components"]

    c = req.menu_choice
    try:
        if c == 1:  payload = _call_and_capture(density, results)
        elif c == 2: payload = _call_and_capture(show_density_phases, results)
        elif c == 3: payload = _call_and_capture(show_volume_data_system, results)
        elif c == 4: payload = _call_and_capture(show_volume_data_phase, results)
        elif c == 5: payload = _call_and_capture(show_component_amounts, results)
        elif c == 6: payload = _call_and_capture(show_phase_weight_fractions, results)
        elif c == 7: payload = _call_and_capture(show_driving_forces, results)
        elif c == 8: payload = _call_and_capture(show_u_fractions, results)
        elif c == 9: payload = _call_and_capture(show_site_fractions_thermocalc_style, results, db)
        elif c == 10: payload = _call_and_capture(show_chemical_potentials, results)
        elif c == 11: payload = _call_and_capture(show_clean_phase_referenced_analysis, results, T_K, P, X, elements, db, components)
        elif c == 12: payload = _call_and_capture(show_activities, results)
        elif c == 13: payload = _call_and_capture(show_phase_ref_activities, results)
        elif c == 14: payload = _call_and_capture(show_phase_properties, results, T_K, P, X, elements, db)
        elif c == 15: payload = _call_and_capture(curie_temperature)
        elif c == 16: payload = _call_and_capture(show_bohr_magneton_with_site_fractions, results, db)
        elif c == 17: payload = _call_and_capture(show_helmholtz, results)
        elif c == 18: payload = _call_and_capture(show_system_gibbs_energy, results)
        elif c == 19: payload = _call_and_capture(show_system_enthalpy, results)
        elif c == 20: payload = _call_and_capture(show_system_entropy, results)
        elif c == 21: payload = _call_and_capture(show_system_internal_energy, results)
        elif c == 22: payload = _call_and_capture(show_system_heat_capacity, results)
        elif c == 23: payload = _call_and_capture(show_electrical_resistance, results, additional_props, T_K)
        elif c == 24: payload = _call_and_capture(show_electrical_conductivity, results, additional_props, T_K)
        elif c == 25: payload = _call_and_capture(show_thermal_conductivity, results, additional_props, T_K)
        elif c == 26: payload = _call_and_capture(show_thermal_diffusity, results, additional_props, T_K)
        elif c == 27: payload = _call_and_capture(show_thermal_resistance, results, additional_props, T_K)
        elif c == 28: payload = _call_and_capture(show_thermal_expansion, results, additional_props, T_K)
        elif c == 29: payload = _call_and_capture(show_young_modulus, additional_props)
        elif c == 30: payload = _call_and_capture(show_shear_modulus, additional_props)
        elif c == 31: payload = _call_and_capture(show_bulk_modulus, additional_props)
        elif c == 32: payload = _call_and_capture(show_poisson_ratio, additional_props)
        elif c == 33: payload = _call_and_capture(show_surface_tension_properties, additional_props)
        else:
            raise HTTPException(status_code=400, detail="Geçersiz menu_choice (1..33)")

        return AnalysisResponse(success=True, message="OK", payload=payload)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Analiz hatası: {e}")

# Diğer BaseModel sınıflarının yanına ekle
class TernaryRequest(BaseModel):
    element1: str
    element2: str
    weight_percent1: float = 0.0
    weight_percent2: float = 0.0
    temperature_c: float = 1000.0
    pressure_pa: float = 101325.0
    step_size: float = 0.1
    # Vertical section için ek parametreler
    temp_min: Optional[float] = 300.0
    temp_max: Optional[float] = 1873.0
    diagram_type: str = "isothermal"  # "isothermal" veya "vertical"

class TernaryResponse(BaseModel):
    success: bool
    message: str
    diagram_base64: Optional[str] = None
    stable_phases: Optional[List[str]] = None
    system_info: Optional[str] = None
    diagram_type: str
@app.post("/ternary-diagram", response_model=TernaryResponse)
async def create_ternary_diagram(request: TernaryRequest):
    try:
        if request.diagram_type == "isothermal":
            # Ternary_Isothermal.py'den fonksiyon çağır
            diagram_data = generate_ternary_isothermal_api(
                element1=request.element1,
                element2=request.element2,
                weight_percent1=request.weight_percent1,
                weight_percent2=request.weight_percent2,
                temperature_c=request.temperature_c,
                pressure_pa=request.pressure_pa,
                step_size=request.step_size
            )
        else:  # vertical
            # Ternary_Vertical.py'den fonksiyon çağır
            diagram_data = generate_ternary_vertical_api(
                element1=request.element1,
                element2=request.element2,
                weight_percent1=request.weight_percent1,
                weight_percent2=request.weight_percent2,
                temp_min=request.temp_min,
                temp_max=request.temp_max
            )
        
        return TernaryResponse(
            success=True,
            message="Ternary diagram başarıyla oluşturuldu",
            diagram_base64=diagram_data["image_base64"],
            stable_phases=diagram_data.get("stable_phases", []),
            system_info=f"Fe-{request.element1}-{request.element2}",
            diagram_type=request.diagram_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ternary diagram oluşturma hatası: {str(e)}")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)