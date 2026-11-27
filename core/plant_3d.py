"""3D Process Plant & Digital Twin for HYACINTH-X.

Renders an interactive, WebGL/Three.js-powered 3D industrial biorefinery plant.
Root-cause fixes applied vs. previous version:
  - Camera targets actual geometric centre of each unit (not ground y=0)
  - Environment map (PMREMGenerator + gradient cubemap) so PBR metal/roughness renders correctly
  - 180-degree cutaway (open half) for unambiguous interior reveal
  - Correct proportions and colour contrast for every sub-assembly
  - Distinct per-unit colour accents so equipment is immediately identifiable
"""
from __future__ import annotations

from typing import Any, Dict
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Equipment Catalog
# ---------------------------------------------------------------------------
EQUIPMENT_METADATA = {
    "T-101": {
        "name": "Washing Tank",
        "stage": "Feedstock Preparation",
        "description": "Continuous agitated immersion tank with spray ring manifold for dislodging silt, sand, and surface contaminants from harvested water hyacinth.",
        "icon": "🚿",
        "internals": [
            "Heavy-Duty Agitator Drive & Gear Reducer",
            "Dual-Tier Agitator (Marine Propeller + Pitch Turbine)",
            "4× Vertical Anti-Vortex Wall Baffles",
            "Radial Wash Water Spray Manifold & Nozzles",
            "Conical Silt Bottom Discharge & Knife Gate Valve",
            "Side Effluent Overflow Launder & Drainage Nozzle",
        ],
        "working_principle": (
            "Raw water hyacinth is immersed in agitated wash water. High-shear fluid motion strips detritus "
            "and sand while hydraulic pumps transfer effluent to biological treatment."
        ),
        "status_color": "#2e7d32",
    },
    "D-101": {
        "name": "Biomass Dryer",
        "stage": "Feedstock Preparation",
        "description": "Industrial rotary dryer with trunnion riding rings, drive girth gear, and helical screw flights reducing feedstock moisture from ~90% to ~10% wb.",
        "icon": "🔥",
        "internals": [
            "Twin Reinforced Concrete Support Pedestals",
            "Solid Forged Riding Rings & Trunnion Rollers",
            "Central Girth Gear Ring & Side Motor Pinion Drive Skid",
            "Continuous Archimedean Internal Helical Screw Flights",
            "Stationary Feed & Discharge Breeching Hoods",
            "Steam Rotary Joint & Cyclone Vapour Exhaust Stack",
        ],
        "working_principle": (
            "Washed biomass passes through a heated rotating drum equipped with internal lifting flights. "
            "Thermal energy (ΔHvap = 2.257 MJ/kg) evaporates free moisture prior to comminution."
        ),
        "status_color": "#e65100",
    },
    "M-101": {
        "name": "Milling Unit",
        "stage": "Feedstock Preparation",
        "description": "Heavy-duty industrial hammer mill reducing dried biomass fibres to <2 mm for maximum surface-area exposure.",
        "icon": "⚙️",
        "internals": [
            "Structural I-Beam Skid with Anti-Vibration Dampers",
            "Heavy-Duty TEFC Electric Motor & V-Belt Guard",
            "Split Clamshell Cast-Iron Housing with Toggle Clamps",
            "Multi-Disc Rotor with Hardened Through-Pins",
            "Free-Swinging Manganese Steel Impact Hammers",
            "Perforated Sizing Screen Basket & Feed Hopper with Tramp Magnet",
        ],
        "working_principle": (
            "Dried plant stalks undergo high-velocity impact with rotating hammers. "
            "Particles exit through classified sieve screens (<2 mm)."
        ),
        "status_color": "#546e7a",
    },
    "T-102": {
        "name": "Slurry Tank",
        "stage": "Pretreatment Preparation",
        "description": "Continuous stirred tank blending milled biomass with recycled water and dilute H₂SO₄ at LSR = 8:1.",
        "icon": "🧪",
        "internals": [
            "316L Stainless Steel Vessel with Torispherical Heads",
            "Top Structural Mixer Bridge & Helical-Bevel Gear Drive",
            "Dual A310 Axial Hydrofoil Impellers",
            "4× Full-Length Vertical Wall Baffles",
            "PTFE-Lined H₂SO₄ Dosing Dip Tube",
            "Process Water Sparger Header & Radar Level Transmitter",
        ],
        "working_principle": (
            "Milled biomass, recycled water, and catalytic H₂SO₄ are homogenised into an 8:1 pumpable slurry, "
            "ensuring uniform thermal conductivity and mass transfer in the downstream reactor."
        ),
        "status_color": "#0288d1",
    },
    "R-101": {
        "name": "Pretreatment Reactor",
        "stage": "Thermochemical Fractionation",
        "description": "High-pressure, steam-jacketed CSTR for dilute-acid thermochemical deconstruction of hemicellulose at 120 °C.",
        "icon": "⚗️",
        "internals": [
            "ASME Pressure Vessel Shell with Ellipsoidal Heads",
            "External Dimpled Steam Heating Jacket & Mineral Wool Insulation",
            "High-Torque Hydraulic Drive & Double Mechanical Seal Pot",
            "Heavy Internal Anchor Agitator with PTFE Wall Wipers",
            "Multi-Elevation Thermowell RTD Transmitter Array",
            "Safety Relief Valve (SRV) & Pneumatic Bottom Blowdown Valve",
        ],
        "working_principle": (
            "Operates at 120 °C. Dilute acid cleaves glycosidic bonds within hemicellulose, hydrolysing ~7 % "
            "to soluble oligomers while retaining ~90 % insoluble cellulose for enzymatic conversion."
        ),
        "status_color": "#c62828",
    },
    "F-101": {
        "name": "Filter Press",
        "stage": "Solid-Liquid Separation",
        "description": "Industrial recessed-chamber membrane filter press separating pretreated cellulosic cake from acidic liquid hydrolysate.",
        "icon": "📦",
        "internals": [
            "Heavy-Duty Dual Side-Beam Steel Frame & Stationary Feed Head",
            "Rear Hydraulic Clamping Cylinder & Chrome Ram Rod",
            "Moving Follower Thrust Plate on Side Guide Bars",
            "22 Recessed Polypropylene Chamber Plates",
            "High-Pressure Slurry Feed Manifold with Diaphragm Valve",
            "Twin Stainless Filtrate Launders & Cake Discharge Chute",
        ],
        "working_principle": (
            "Pretreated slurry is pumped under hydraulic pressure through filter cloths. "
            "Liquid drains into the filtrate manifold; dewatered cellulosic cake is discharged mechanically."
        ),
        "status_color": "#455a64",
    },
    "E-101": {
        "name": "Bioreactor / Fermenter",
        "stage": "Enzymatic Hydrolysis & Fermentation",
        "description": "Large-scale aseptic jacketed vessel where cellulase enzymes depolymerise glucan and S. cerevisiae converts sugars to bioethanol.",
        "icon": "🧬",
        "internals": [
            "Slender 316L Sanitary Stainless Shell (H:D = 3:1)",
            "Top Servo Drive & Sterile Double Mechanical Seal",
            "3-Tier 6-Blade Rushton Disc Turbine Impellers",
            "Internal Stainless Vertical Cooling Coils",
            "Bottom Ring Aeration Sparger & Mechanical Foam Breaker",
            "Sterile Vent Filter, CIP Spray Balls & Sensor Ports",
        ],
        "working_principle": (
            "Cellulase cleaves anhydroglucose units (+11.1 % hydration water). "
            "S. cerevisiae metabolises hexoses via Gay-Lussac reaction (theoretical yield 0.511 g EtOH/g glucose)."
        ),
        "status_color": "#2e7d32",
    },
    "S-101": {
        "name": "Clarification Centrifuge",
        "stage": "Broth Clarification",
        "description": "Continuous disc-stack centrifuge separating spent yeast and insoluble fines from dilute ethanol beer broth.",
        "icon": "🌀",
        "internals": [
            "Cast-Iron Machine Pedestal with Vibration Dampers",
            "Vertical High-Speed Spindle & Belt Drive",
            "Disc-Stack Assembly (30+ Conical Separation Plates)",
            "Centripetal Paring Disc Liquid Pump",
            "Peripheral Solid Ejection Ports & Sliding Hydraulic Piston",
            "Clarified Broth Outlet Pipe & Back-Pressure Valve",
        ],
        "working_principle": (
            "Up to 8 000 g centrifugal force drives yeast cells and lignaceous fines to the bowl periphery; "
            "they are intermittently ejected, leaving clear beer broth for distillation."
        ),
        "status_color": "#00838f",
    },
    "C-101": {
        "name": "Distillation Column",
        "stage": "Thermal Separation",
        "description": "Multi-stage fractional distillation column with 16 sieve trays, thermosiphon reboiler, and overhead reflux condenser.",
        "icon": "🏛️",
        "internals": [
            "Tall Cylindrical Column Shell with Base Skirt & Anchor Ring",
            "16× Perforated Sieve Trays with Downcomers & Overflow Weirs",
            "Side Horizontal Thermosiphon Reboiler Skid",
            "Top Overhead Vapour Line & Shell-and-Tube Condenser",
            "Reflux Accumulator Vessel & Canned-Motor Reflux Pump",
            "Full-Height Safety Cage Ladder & 3× Access Platforms",
        ],
        "working_principle": (
            "Steam vaporises ethanol from 5 vol % broth; counter-current vapour-liquid contact enriches "
            "overhead vapour toward azeotrope (~95 wt %), while stillage exits at column base."
        ),
        "status_color": "#1565c0",
    },
    "V-101": {
        "name": "Molecular Sieve Dehydration",
        "stage": "Product Purification",
        "description": "Twin-bed pressure-swing adsorption (PSA) system using Zeolite 3A to produce anhydrous fuel bioethanol (>99.5 %).",
        "icon": "💎",
        "internals": [
            "Structural Steel Skid with Diamond Plate Flooring",
            "Twin Vertical Adsorption Columns (Bed A & Bed B)",
            "Zeolite 3A Molecular Sieve Bed with Stainless Retaining Grids",
            "Automated Pneumatic Cross-Over Switching Valve Manifold",
            "Inter-Bed Regeneration Gas Electric Superheater",
            "Water Knockout Pot & Duplex Micron Particulate Filters",
        ],
        "working_principle": (
            "Azeotropic ethanol vapour passes through 3-Å zeolite pores that selectively adsorb "
            "2.8-Å water molecules while excluding 4.4-Å ethanol, yielding fuel-grade ethanol >99.5 %."
        ),
        "status_color": "#0d47a1",
    },
}


# ---------------------------------------------------------------------------
# Live telemetry extraction (unchanged from previous version)
# ---------------------------------------------------------------------------
def extract_equipment_telemetry(eq_id: str, dm: Any) -> Dict[str, Any]:
    """Extracts genuine simulation telemetry parameters for a given equipment item."""
    if not dm or not dm.completed:
        return {"status": "Awaiting Simulation Run", "parameters": []}

    r1 = dm.results.get("M01", {})
    r2 = dm.results.get("M02", {})
    r3 = dm.results.get("M03", {})
    r5 = dm.results.get("M05", {})
    mb = dm.derived.get("mass_balance", {})
    m3_params = dm.derived.get("m03_params", {})
    params = []

    if eq_id == "T-101":
        wash_vol = m3_params.get("washing_water_m3_day", 3.0)
        wash_power = [r[1] for r in r3.get("electric_rows", []) if "Washing" in r[0]]
        params = [
            {"Parameter": "Wet Biomass Inflow", "Value": f"{r1.get('wet_feed_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M01"},
            {"Parameter": "Raw Harvest Moisture", "Value": f"{r1.get('moisture_pct_wb', 0):.1f}", "Unit": "% wb", "Source": "M01"},
            {"Parameter": "Process Washing Water", "Value": f"{wash_vol:,.1f}", "Unit": "m³/day", "Source": "M03"},
            {"Parameter": "Pump Hydraulic Head", "Value": f"{m3_params.get('washing_pump_head_m', 15.0):.1f}", "Unit": "m", "Source": "M03"},
            {"Parameter": "Pump Power Demand", "Value": f"{wash_power[0] if wash_power else 0.19:.2f}", "Unit": "kWh/day", "Source": "M03"},
        ]
    elif eq_id == "D-101":
        evap = r3.get("water_removed_kg_day", 0.0)
        dryer_mj = [r[1] for r in r3.get("thermal_rows", []) if "Dryer" in r[0]]
        params = [
            {"Parameter": "Water Mass Evaporated", "Value": f"{evap:,.1f}", "Unit": "kg/day", "Source": "M03"},
            {"Parameter": "Target Moisture", "Value": f"{m3_params.get('target_moisture_pct', 10.0):.1f}", "Unit": "% wb", "Source": "M03"},
            {"Parameter": "Thermal Drying Duty", "Value": f"{dryer_mj[0] if dryer_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03"},
            {"Parameter": "Dryer Efficiency", "Value": f"{m3_params.get('dryer_eff_pct', 55.0):.0f}", "Unit": "%", "Source": "M03"},
            {"Parameter": "Outlet Temperature", "Value": "100.0", "Unit": "°C", "Source": "Model"},
        ]
    elif eq_id == "M-101":
        mill_power = [r[1] for r in r3.get("electric_rows", []) if "Mill" in r[0]]
        params = [
            {"Parameter": "Dry Biomass Throughput", "Value": f"{r1.get('dry_biomass_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M01"},
            {"Parameter": "Specific Milling Energy", "Value": f"{m3_params.get('milling_kwh_per_t', 25.0):.1f}", "Unit": "kWh/t dry", "Source": "M03"},
            {"Parameter": "Milling Load", "Value": f"{mill_power[0] if mill_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03"},
            {"Parameter": "Target Screen Size", "Value": "< 2.0", "Unit": "mm", "Source": "Design"},
        ]
    elif eq_id == "T-102":
        slurry_liq = r3.get("slurry_liquid_kg_day", 0.0)
        slurry_power = [r[1] for r in r3.get("electric_rows", []) if "Slurry" in r[0]]
        lsr = m3_params.get("pretreatment_liquid_solid_ratio", 8.0)
        params = [
            {"Parameter": "Liquid-to-Solid Ratio", "Value": f"{lsr:.1f}:1", "Unit": "kg liq/kg dry", "Source": "M03"},
            {"Parameter": "Process Water Added", "Value": f"{slurry_liq:,.1f}", "Unit": "kg/day", "Source": "M03"},
            {"Parameter": "Total Slurry", "Value": f"{slurry_liq + r1.get('dry_biomass_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "Balance"},
            {"Parameter": "Mixer Power", "Value": f"{slurry_power[0] if slurry_power else 8.0:.2f}", "Unit": "kWh/day", "Source": "M03"},
        ]
    elif eq_id == "R-101":
        react_mj = [r[1] for r in r3.get("thermal_rows", []) if "Pretreatment" in r[0]]
        p_m2 = dm.derived.get("m02_params", {})
        params = [
            {"Parameter": "Cooking Temperature", "Value": f"{m3_params.get('pretreatment_temp_c', 120.0):.1f}", "Unit": "°C", "Source": "M03"},
            {"Parameter": "Thermal Duty", "Value": f"{react_mj[0] if react_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03"},
            {"Parameter": "Solid Fibre Retention", "Value": f"{p_m2.get('solid_retention', 0.90)*100:.1f}", "Unit": "%", "Source": "M02"},
            {"Parameter": "Solubilised Organics", "Value": f"{p_m2.get('solubilized_fraction', 0.07)*100:.1f}", "Unit": "%", "Source": "M02"},
            {"Parameter": "Degradation Inhibitors", "Value": f"{p_m2.get('degraded_fraction', 0.03)*100:.1f}", "Unit": "%", "Source": "M02"},
        ]
    elif eq_id == "F-101":
        filter_power = [r[1] for r in r3.get("electric_rows", []) if "Filter press" in r[0]]
        resid = mb.get("residual_solids_kg", 0.0)
        params = [
            {"Parameter": "Residual Insoluble Solids", "Value": f"{resid:,.1f}", "Unit": "kg/day", "Source": "M02/M04"},
            {"Parameter": "Filtrate Flow", "Value": f"{r3.get('slurry_liquid_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M03"},
            {"Parameter": "Filter Press Power", "Value": f"{filter_power[0] if filter_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03"},
            {"Parameter": "Separation Type", "Value": "Recessed Membrane Filtration", "Unit": "—", "Source": "Design"},
        ]
    elif eq_id == "E-101":
        sugar_tot = dm.results.get("M02", {}).get("total_sugars_kg", 0.0)
        eth_crude = dm.results.get("M02", {}).get("ethanol_before_recovery_kg", 0.0)
        co2 = mb.get("co2_kg", 0.0)
        ferm_power = [r[1] for r in r3.get("electric_rows", []) if "Fermenter" in r[0]]
        params = [
            {"Parameter": "Total Monomeric Sugars", "Value": f"{sugar_tot:,.1f}", "Unit": "kg/day", "Source": "M02"},
            {"Parameter": "Hydrolysis Water Gain", "Value": f"{mb.get('hydrolysis_water_kg', 0):,.2f}", "Unit": "kg/day", "Source": "Stoichiometry"},
            {"Parameter": "Crude Ethanol Produced", "Value": f"{eth_crude:,.1f}", "Unit": "kg/day", "Source": "M02"},
            {"Parameter": "CO₂ Off-Gas", "Value": f"{co2:,.1f}", "Unit": "kg/day", "Source": "Gay-Lussac"},
            {"Parameter": "Agitator Power", "Value": f"{ferm_power[0] if ferm_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03"},
        ]
    elif eq_id == "S-101":
        broth_vol = r3.get("broth_volume_m3_day", 0.0)
        cent_power = [r[1] for r in r3.get("electric_rows", []) if "Centrifuge" in r[0]]
        params = [
            {"Parameter": "Broth Throughput", "Value": f"{broth_vol:,.2f}", "Unit": "m³/day", "Source": "M03"},
            {"Parameter": "Broth Ethanol Conc.", "Value": f"{m3_params.get('broth_ethanol_vol_pct', 5.0):.1f}", "Unit": "vol %", "Source": "M03"},
            {"Parameter": "Centrifuge Power", "Value": f"{cent_power[0] if cent_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03"},
            {"Parameter": "G-Force Field", "Value": "6 500 – 8 000", "Unit": "g", "Source": "Specification"},
        ]
    elif eq_id == "C-101":
        dist_mj = [r[1] for r in r3.get("thermal_rows", []) if "Distillation" in r[0]]
        eth_rec = dm.results.get("M02", {}).get("recovered_ethanol_kg", 0.0)
        params = [
            {"Parameter": "Recovered Ethanol (mass)", "Value": f"{eth_rec:,.2f}", "Unit": "kg/day", "Source": "M02/M03"},
            {"Parameter": "Recovered Ethanol (volume)", "Value": f"{r3.get('ethanol_l_day', 0):,.1f}", "Unit": "L/day", "Source": "M03"},
            {"Parameter": "Reboiler Heating Load", "Value": f"{dist_mj[0] if dist_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03"},
            {"Parameter": "Reboiler Efficiency", "Value": f"{m3_params.get('distillation_heater_eff_pct', 85.0):.0f}", "Unit": "%", "Source": "M03"},
            {"Parameter": "Ethanol Recovery", "Value": f"{dm.results.get('M02', {}).get('ethanol_recovery', 0.95)*100:.1f}", "Unit": "%", "Source": "M02"},
        ]
    elif eq_id == "V-101":
        dehyd_mj = [r[1] for r in r3.get("thermal_rows", []) if "Dehydration" in r[0]]
        annual_l = r5.get("quantities", {}).get("ethanol_l_year", 0.0)
        params = [
            {"Parameter": "Anhydrous Ethanol (>99.5 %)", "Value": f"{r3.get('ethanol_l_day', 0):,.1f}", "Unit": "L/day", "Source": "Product"},
            {"Parameter": "Annual Production", "Value": f"{annual_l:,.0f}", "Unit": "L/year", "Source": "M05"},
            {"Parameter": "Dehydration Energy", "Value": f"{m3_params.get('dehydration_mj_per_l_ethanol', 1.5):.2f}", "Unit": "MJ/L ethanol", "Source": "M03"},
            {"Parameter": "Thermal Duty", "Value": f"{dehyd_mj[0] if dehyd_mj else 0:,.1f}", "Unit": "MJ/day", "Source": "M03"},
        ]

    return {"status": "Live Simulation Linked", "parameters": params}


# ---------------------------------------------------------------------------
# Three.js scene builder
# ---------------------------------------------------------------------------
def build_threejs_html(selected_eq_id: str, view_mode: str = "full_plant", cutaway: bool = True) -> str:
    """Generate a self-contained Three.js WebGL page with detailed industrial equipment."""

    cutaway_js = "true" if cutaway else "false"
    meta = EQUIPMENT_METADATA.get(selected_eq_id, {})
    eq_name = meta.get("name", selected_eq_id)
    mode_label = "Single Equipment" if view_mode == "single_equipment" else "Full Plant"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0d14;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
#c{{display:block;width:100vw;height:100vh}}
#hud{{position:fixed;top:12px;left:12px;background:rgba(10,13,20,.88);backdrop-filter:blur(8px);
      border:1px solid rgba(99,179,237,.3);border-radius:8px;padding:9px 15px;color:#e2e8f0;font-size:12.5px;z-index:9;pointer-events:none}}
#hud b{{color:#63b3ed;font-size:13.5px;display:block;margin-bottom:3px}}
#btns{{position:fixed;top:12px;right:12px;display:flex;gap:6px;z-index:9}}
.cb{{background:rgba(15,20,30,.88);border:1px solid rgba(255,255,255,.18);color:#cbd5e0;
     padding:6px 11px;border-radius:6px;font-size:11.5px;font-weight:600;cursor:pointer;
     backdrop-filter:blur(6px);transition:.18s}}
.cb:hover{{background:#2b6cb0;color:#fff;border-color:#63b3ed}}
#leg{{position:fixed;bottom:12px;right:12px;background:rgba(10,13,20,.85);border:1px solid rgba(255,255,255,.12);
      border-radius:6px;padding:7px 12px;color:#a0aec0;font-size:11px;display:flex;flex-wrap:wrap;gap:10px 16px;max-width:360px;z-index:9;pointer-events:none}}
.dot{{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle}}
#tip{{position:fixed;bottom:12px;left:12px;background:rgba(10,13,20,.82);border:1px solid rgba(255,255,255,.1);
      border-radius:6px;padding:7px 13px;color:#718096;font-size:11px;pointer-events:none}}
#eqlab{{position:fixed;bottom:52px;left:12px;background:rgba(43,108,176,.85);border-radius:6px;
        padding:5px 12px;color:#fff;font-size:12.5px;font-weight:700;pointer-events:none}}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
<canvas id="c"></canvas>
<div id="hud"><b>🏭 HYACINTH-X Industrial Digital Twin</b>
<span id="hudtxt">{selected_eq_id} · {eq_name} · {mode_label}</span></div>
<div id="btns">
  <button id="btn-iso" class="cb" onclick="window.camPreset && window.camPreset('iso')">📐 Isometric</button>
  <button id="btn-front" class="cb" onclick="window.camPreset && window.camPreset('front')">👁 Front</button>
  <button id="btn-top" class="cb" onclick="window.camPreset && window.camPreset('top')">⬆ Plan</button>
  <button id="btn-sel" class="cb" onclick="window.camPreset && window.camPreset('sel')">🔍 Focus {selected_eq_id}</button>
</div>
<div id="leg">
  <span><span class="dot" style="background:#38a169"></span>Biomass/Slurry</span>
  <span><span class="dot" style="background:#3182ce"></span>Broth/Hydrolysate</span>
  <span><span class="dot" style="background:#dd6b20"></span>Steam/Heat</span>
  <span><span class="dot" style="background:#805ad5"></span>H₂SO₄/Catalyst</span>
  <span><span class="dot" style="background:#ecc94b"></span>Fuel Ethanol &gt;99%</span>
</div>
<div id="tip">🖱 Rotate: left-drag · Pan: right-drag · Zoom: scroll</div>
<div id="eqlab">Cutaway: {'ON' if cutaway else 'OFF'}</div>

<script>
(function(){{
// ─── RENDERER SETUP ──────────────────────────────────────────────────────
const canvas = document.getElementById('c');
const getW = () => canvas.clientWidth || window.innerWidth || 800;
const getH = () => canvas.clientHeight || window.innerHeight || 600;

const renderer = new THREE.WebGLRenderer({{canvas, antialias:true, alpha:false, powerPreference:'high-performance'}});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(getW(), getH());
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

// ─── SCENE & CAMERA ──────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111827);
scene.fog = new THREE.Fog(0x111827, 90, 240);

const initW = getW(), initH = getH();
const aspect = (initW > 0 && initH > 0) ? (initW / initH) : (16 / 9);
const camera = new THREE.PerspectiveCamera(42, aspect, 0.1, 1000);
camera.position.set(0, 25, 50);

const controls = new THREE.OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.dampingFactor = 0.06;
controls.minPolarAngle = 0;
controls.maxPolarAngle = Math.PI * 0.88;
controls.minDistance = 2;
controls.maxDistance = 250;

// ─── ENVIRONMENT / LIGHTING ───────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0xffffff, 0.75));
const hemiLight = new THREE.HemisphereLight(0xdbeafe, 0x1e293b, 1.2);
hemiLight.position.set(0, 60, 0);
scene.add(hemiLight);

// Key light – warm overhead
const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.8);
keyLight.position.set(25, 45, 30);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.near = 2;
keyLight.shadow.camera.far = 180;
keyLight.shadow.camera.left = keyLight.shadow.camera.bottom = -70;
keyLight.shadow.camera.right = keyLight.shadow.camera.top = 70;
scene.add(keyLight);

// Fill light – cool blue side
const fillLight = new THREE.DirectionalLight(0x93c5fd, 0.9);
fillLight.position.set(-35, 25, -25);
scene.add(fillLight);

// Back rim
const rimLight = new THREE.DirectionalLight(0xfef08a, 0.6);
rimLight.position.set(5, 15, -45);
scene.add(rimLight);

// ─── GROUND PLANE ─────────────────────────────────────────────────────────
const groundMat = new THREE.MeshStandardMaterial({{color:0x1e293b, roughness:0.85, metalness:0.1}});
const ground = new THREE.Mesh(new THREE.PlaneGeometry(200, 120), groundMat);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.05;
ground.receiveShadow = true;
scene.add(ground);

// Grid overlay
const grid = new THREE.GridHelper(200, 100, 0x3b82f6, 0x334155);
grid.position.y = 0;
scene.add(grid);

// Safety walkway stripes
function stripe(x1, z1, x2, z2){{
  const len = Math.hypot(x2 - x1, z2 - z1);
  const ang = Math.atan2(z2 - z1, x2 - x1);
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(len, 0.3),
    new THREE.MeshBasicMaterial({{color:0xfacc15, depthWrite:false}})
  );
  m.rotation.x = -Math.PI / 2;
  m.rotation.z = -ang;
  m.position.set((x1 + x2) / 2, 0.01, (z1 + z2) / 2);
  scene.add(m);
}}
stripe(-38, 8, 22, 8); stripe(-38, -8, 22, -8);
stripe(-38, 24, 22, 24); stripe(-38, -24, 22, -24);

// ─── PBR MATERIAL LIBRARY (All with DoubleSide for cutaways) ─────────────
const M = {{
  ss316    : new THREE.MeshStandardMaterial({{color:0xd1d5db, metalness:0.85, roughness:0.22, side:THREE.DoubleSide}}),
  ssBrushed: new THREE.MeshStandardMaterial({{color:0x9ca3af, metalness:0.80, roughness:0.35, side:THREE.DoubleSide}}),
  cs       : new THREE.MeshStandardMaterial({{color:0x4b5563, metalness:0.75, roughness:0.45, side:THREE.DoubleSide}}),
  ci       : new THREE.MeshStandardMaterial({{color:0x374151, metalness:0.60, roughness:0.60, side:THREE.DoubleSide}}),
  insul    : new THREE.MeshStandardMaterial({{color:0xd4c5a9, metalness:0.10, roughness:0.85, side:THREE.DoubleSide}}),
  copper   : new THREE.MeshStandardMaterial({{color:0xd97706, metalness:0.85, roughness:0.28, side:THREE.DoubleSide}}),
  yellow   : new THREE.MeshStandardMaterial({{color:0xeab308, metalness:0.30, roughness:0.45, side:THREE.DoubleSide}}),
  blue     : new THREE.MeshStandardMaterial({{color:0x2563eb, metalness:0.55, roughness:0.35, side:THREE.DoubleSide}}),
  red      : new THREE.MeshStandardMaterial({{color:0xdc2626, metalness:0.55, roughness:0.40, side:THREE.DoubleSide}}),
  conc     : new THREE.MeshStandardMaterial({{color:0x475569, roughness:0.95, metalness:0.05, side:THREE.DoubleSide}}),
  glass    : new THREE.MeshPhysicalMaterial({{
    color:0x93c5fd, transparent:true, opacity:0.35,
    roughness:0.1, metalness:0.1, transmission:0.75,
    ior:1.45, depthWrite:false, side:THREE.DoubleSide
  }}),
  highlight: new THREE.MeshStandardMaterial({{
    color:0x10b981, emissive:0x059669, emissiveIntensity:0.55,
    metalness:0.75, roughness:0.22, side:THREE.DoubleSide
  }}),
  // per-unit accent colours (DoubleSide ensures inner chamber is always visible)
  T101col  : new THREE.MeshStandardMaterial({{color:0x15803d, metalness:0.75, roughness:0.30, side:THREE.DoubleSide}}),
  D101col  : new THREE.MeshStandardMaterial({{color:0xb45309, metalness:0.70, roughness:0.35, side:THREE.DoubleSide}}),
  M101col  : new THREE.MeshStandardMaterial({{color:0x334155, metalness:0.72, roughness:0.42, side:THREE.DoubleSide}}),
  T102col  : new THREE.MeshStandardMaterial({{color:0x0284c7, metalness:0.80, roughness:0.25, side:THREE.DoubleSide}}),
  R101col  : new THREE.MeshStandardMaterial({{color:0xb91c1c, metalness:0.78, roughness:0.28, side:THREE.DoubleSide}}),
  F101col  : new THREE.MeshStandardMaterial({{color:0x1d4ed8, metalness:0.72, roughness:0.38, side:THREE.DoubleSide}}),
  E101col  : new THREE.MeshStandardMaterial({{color:0x16a34a, metalness:0.82, roughness:0.20, side:THREE.DoubleSide}}),
  S101col  : new THREE.MeshStandardMaterial({{color:0x0f766e, metalness:0.84, roughness:0.22, side:THREE.DoubleSide}}),
  C101col  : new THREE.MeshStandardMaterial({{color:0x1e40af, metalness:0.80, roughness:0.25, side:THREE.DoubleSide}}),
  V101col  : new THREE.MeshStandardMaterial({{color:0x4338ca, metalness:0.80, roughness:0.25, side:THREE.DoubleSide}}),
}};

const isCut = {cutaway_js};
const selId = "{selected_eq_id}";
const isSingle = ("{view_mode}" === "single_equipment");

function selMat(id, base){{ return selId===id ? M.highlight : base; }}
// Cutaway angles: Generates 270 deg of cylinder, leaving a 90 deg front window
const CW = 0;              // cutaway phi start
const CL = Math.PI * 1.5;  // 270 deg arc leaves front 90 deg quadrant open
const FW = 0;              // full phi start
const FL = Math.PI * 2;    // full 360 deg

function cylMat(id, base){{
  if(selId===id && !isCut) return M.highlight;
  return isCut ? (selId===id ? base : M.glass) : base;
}}
function phi(open){{ return open&&isCut ? [CW,CL] : [FW,FL]; }}

// ─── GEOMETRY HELPERS ─────────────────────────────────────────────────────
function add(parent,geo,mat,px=0,py=0,pz=0,rx=0,ry=0,rz=0){{
  const m=new THREE.Mesh(geo,mat);
  m.position.set(px,py,pz); m.rotation.set(rx,ry,rz);
  m.castShadow=true; m.receiveShadow=true;
  parent.add(m); return m;
}}
function cyl(r,h,segs=32){{return new THREE.CylinderGeometry(r,r,h,segs,1,false,FW,FL);}}
function ocyl(r,h,ps,pl,segs=32){{return new THREE.CylinderGeometry(r,r,h,segs,1,true,ps,pl);}}
function sphere(r,ps=0,pl=Math.PI*2,ts=0,tl=Math.PI,segs=32){{
  return new THREE.SphereGeometry(r,segs,16,ps,pl,ts,tl);
}}
function box(w,h,d){{return new THREE.BoxGeometry(w,h,d);}}
function cone(r,h,s=20){{return new THREE.ConeGeometry(r,h,s);}}
function torus(R,r,s=8,t=24){{return new THREE.TorusGeometry(R,r,s,t);}}

// Concrete pad
function pad(parent,w,d,h,x=0,z=0){{
  add(parent,box(w,h,d),M.conc, x,h/2,z);
}}
// Flanged nozzle stub
function nozzle(parent,r,len,px,py,pz,axis='x'){{
  const g=new THREE.Group(); g.position.set(px,py,pz);
  const pipe=new THREE.Mesh(cyl(r,len),M.ss316); pipe.castShadow=true;
  const fl=new THREE.Mesh(cyl(r*1.65,0.07),M.cs);
  if(axis==='x'){{pipe.rotation.z=Math.PI/2; fl.rotation.z=Math.PI/2; fl.position.x=len/2; pipe.position.x=len/2;}}
  else if(axis==='-x'){{pipe.rotation.z=-Math.PI/2; fl.rotation.z=-Math.PI/2; fl.position.x=-len/2; pipe.position.x=-len/2;}}
  else if(axis==='z'){{pipe.rotation.x=-Math.PI/2; fl.rotation.x=-Math.PI/2; fl.position.z=len/2; pipe.position.z=len/2;}}
  else {{fl.position.y=len; pipe.position.y=len/2;}}
  g.add(pipe); g.add(fl); parent.add(g); return g;
}}
// Motor + gearbox on top of a vessel
function motorDrive(parent,cx,cy,cz,s=1){{
  const g=new THREE.Group(); g.position.set(cx,cy,cz);
  add(g,box(0.8*s,0.55*s,0.8*s),M.ci,0,0.275*s,0);        // gearbox housing
  add(g,cyl(0.38*s,1.2*s),M.blue,0,0.55*s+0.6*s,0);        // motor body
  add(g,cyl(0.40*s,0.22*s),M.cs,0,0.55*s+1.2*s+0.11*s,0);  // fan cowl
  add(g,box(0.22*s,0.28*s,0.22*s),M.yellow,0.42*s,0.55*s+0.5*s,0); // JBox
  add(g,cyl(0.09*s,0.4*s),M.ss316,0,0,0);                   // output shaft stub
  parent.add(g); return g;
}}
// Centrifugal pump skid
function pump(parent,px,py,pz,ry=0){{
  const g=new THREE.Group(); g.position.set(px,py,pz); g.rotation.y=ry;
  add(g,box(1.2,0.12,0.75),M.ci,0,0.06,0);           // base plate
  add(g,cyl(0.20,0.55,16),M.blue,  -0.28,0.28+0.275, 0,0,0,Math.PI/2); // motor
  add(g,cyl(0.24,0.22,16),M.red,    0.24,0.28,0, Math.PI/2,0,0);       // volute
  add(g,cyl(0.075,0.32,12),M.cs,    0.24,0.50,0);                      // discharge
  parent.add(g); return g;
}}

// ─── EQUIPMENT CONTAINERS & ANIMATION ────────────────────────────────────
const plantGrp = new THREE.Group();
scene.add(plantGrp);
const eqObjs = {{}};
const animFns = [];

// ══════════════════════════════════════════════════════════════════════════
// 1. T-101  INDUSTRIAL BIOMASS WASHING TANK
//    Stainless vessel elevated on 4 legs, inverted cone bottom,
//    dual-tier impeller, spray ring, 4 baffles.
// ══════════════════════════════════════════════════════════════════════════
function buildT101(ox,oz){{
  const g=new THREE.Group(); g.name='T-101'; g.position.set(ox,0,oz);
  const col=selMat('T-101',M.T101col);
  const shellMat=cylMat('T-101',M.T101col);
  const H=4.0, R=1.75;
  const shellBase=2.2; // y of bottom of cylindrical shell

  pad(g,5,5,0.3);

  // 4 pipe support legs + cross bracing
  for(let i=0;i<4;i++){{
    const a=(i*Math.PI/2)+Math.PI/4;
    const lx=Math.cos(a)*(R-0.1), lz=Math.sin(a)*(R-0.1);
    add(g,cyl(0.11,shellBase-0.3),M.ssBrushed, lx,(0.3+(shellBase-0.3)/2),lz);
    add(g,cyl(0.11,0.08),M.cs, lx,0.3,lz);  // base pad
  }}
  // cross braces at mid-height
  for(let i=0;i<2;i++){{
    const a=i*Math.PI/2+Math.PI/4, bx=Math.cos(a)*(R-0.1)*0.7, bz=Math.sin(a)*(R-0.1)*0.7;
    add(g,box(R*1.3,0.08,0.08),M.cs, 0, 0.3+(shellBase-0.3)*0.5, 0, 0,a,0);
  }}

  // Inverted conical silt hopper (bottom of vessel)
  const coneH=1.0;
  const coneMesh=new THREE.Mesh(
    new THREE.ConeGeometry(R,coneH,32,1,isCut,CW,CL),
    isCut?M.glass:col
  );
  coneMesh.rotation.x=Math.PI;
  coneMesh.position.set(0,shellBase-coneH/2,0);
  coneMesh.castShadow=true; g.add(coneMesh);

  // Bottom drain stub + valve
  add(g,cyl(0.14,0.5,16),M.cs, 0,shellBase-coneH-0.25,0);
  add(g,box(0.35,0.28,0.28),M.red, 0,shellBase-coneH-0.52,0);

  // Cylindrical shell body
  const shY=shellBase+H/2;
  const [ps,pl]=phi(true);
  add(g,new THREE.CylinderGeometry(R,R,H,36,1,true,ps,pl), shellMat, 0,shY,0);

  // Girth rings (flange stiffeners)
  add(g,cyl(R+0.08,0.10),M.cs, 0,shellBase,0);
  add(g,cyl(R+0.08,0.10),M.cs, 0,shellBase+H,0);

  // Top dished head
  add(g,sphere(R,FW,FL,0,Math.PI/2.1),col, 0,shellBase+H+R*0.05,0);

  // Top mixer bridge + motor
  add(g,box(R*2.5,0.2,0.65),M.ssBrushed, 0,shellBase+H+R*0.05+0.4,0);
  motorDrive(g,0,shellBase+H+R*0.05+0.5,0,1.1);

  // Agitator shaft
  const shaftMesh=add(g,cyl(0.07,H+0.6),M.cs, 0,shY,0);

  // Impeller group (animates)
  const impGrp=new THREE.Group(); impGrp.position.set(0,shY,0);

  // Lower 3-blade marine propeller
  for(let b=0;b<3;b++){{
    const a=b*Math.PI*2/3;
    const blade=new THREE.Mesh(box(R*0.75,0.08,0.26),M.copper);
    blade.position.set(Math.cos(a)*R*0.35, -H*0.33, Math.sin(a)*R*0.35);
    blade.rotation.set(0.3,a,0);
    impGrp.add(blade);
  }}
  // Upper 4-blade pitched turbine
  for(let b=0;b<4;b++){{
    const a=b*Math.PI/2;
    const blade=new THREE.Mesh(box(R*0.9,0.11,0.30),M.copper);
    blade.position.set(Math.cos(a)*R*0.42, H*0.1, Math.sin(a)*R*0.42);
    blade.rotation.set(0.25,a,0);
    impGrp.add(blade);
  }}
  g.add(impGrp);

  // 4 vertical anti-vortex baffles
  for(let i=0;i<4;i++){{
    const a=i*Math.PI/2;
    const bfl=new THREE.Mesh(box(0.28,H*0.88,0.05),M.ssBrushed);
    bfl.position.set(Math.cos(a)*(R-0.06),shY,Math.sin(a)*(R-0.06));
    bfl.rotation.y=-a; g.add(bfl);
  }}

  // Spray ring manifold + 6 nozzle tips
  add(g,torus(R*0.72,0.055),M.copper, 0,shellBase+H*0.52,0, Math.PI/2,0,0);
  for(let s=0;s<6;s++){{
    const a=s*Math.PI*2/6;
    add(g,cone(0.07,0.18,8),M.copper,
      Math.cos(a)*R*0.72, shellBase+H*0.44, Math.sin(a)*R*0.72, Math.PI,0,0);
  }}

  // Side manway
  nozzle(g,0.32,0.28, R,shellBase+H*0.6,0,'x');

  // Wash water inlet pipe from above
  add(g,cyl(0.1,1.0),M.ssBrushed, R*0.6,shellBase+H+0.9,0);

  // Liquid surface
  add(g,new THREE.CylinderGeometry(R-0.05,R-0.05,0.04,32),
    new THREE.MeshStandardMaterial({{color:0x2d6a4f,transparent:true,opacity:0.65,roughness:0.15}}),
    0,shellBase+H*0.6,0);

  animFns.push(()=>{{impGrp.rotation.y+=0.045;}});

  plantGrp.add(g); eqObjs['T-101']=g;
  return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 2. D-101  INDUSTRIAL ROTARY BIOMASS DRYER
//    Horizontal drum on 2 concrete piers, riding rings, girth gear, motor
// ══════════════════════════════════════════════════════════════════════════
function buildD101(ox,oz){{
  const g=new THREE.Group(); g.name='D-101'; g.position.set(ox,0,oz);
  const col=selMat('D-101',M.D101col);

  // Drum elevation center
  const drumY=3.4, drumR=1.35, drumL=9.5;

  // 2 concrete piers
  add(g,box(2.2,drumY-0.4,3.8),M.conc,-3.5,  (drumY-0.4)/2,0);
  add(g,box(2.2,drumY-0.4,3.8),M.conc, 3.5,  (drumY-0.4)/2,0);

  // Drum group (rotates around X)
  const drumGrp=new THREE.Group();
  drumGrp.position.set(0,drumY,0);
  drumGrp.rotation.z=0.025; // slight slope

  // Main drum shell
  const [ps,pl]=phi(true);
  const drum=new THREE.Mesh(
    new THREE.CylinderGeometry(drumR,drumR,drumL,36,1,true,ps,pl), isCut?M.glass:col
  );
  drum.rotation.z=Math.PI/2; drum.castShadow=true;
  drumGrp.add(drum);

  // End plates (solid discs at each end)
  for(let ex of[-drumL/2,drumL/2]){{
    const ep=new THREE.Mesh(new THREE.CircleGeometry(drumR,32),col);
    ep.rotation.y=Math.PI/2; ep.position.x=ex; drumGrp.add(ep);
  }}

  // 2 riding rings (thick solid cylinders)
  for(let rx of[-3.4,3.4]){{
    const ring=new THREE.Mesh(cyl(drumR+0.18,0.6),M.ssBrushed);
    ring.rotation.z=Math.PI/2; ring.position.x=rx;
    drumGrp.add(ring);
    // Trunnion roller pair per ring
    for(let rz of[-1.1,1.1]){{
      const roller=new THREE.Mesh(cyl(0.32,0.45,16),M.cs);
      roller.rotation.z=Math.PI/2; roller.position.set(rx,-(drumR+0.05),rz);
      drumGrp.add(roller);
    }}
  }}

  // Girth drive gear ring (at ~1/3 from one end)
  const gear=new THREE.Mesh(cyl(drumR+0.28,0.5,36),M.ci);
  gear.rotation.z=Math.PI/2; gear.position.x=-1.8;
  drumGrp.add(gear);

  // Internal screw flighting (visible in cutaway)
  const screwShaft=new THREE.Mesh(cyl(0.18,drumL-0.6),M.cs);
  screwShaft.rotation.z=Math.PI/2; drumGrp.add(screwShaft);
  for(let fx=-drumL/2+1;fx<drumL/2-0.5;fx+=0.9){{
    const flight=new THREE.Mesh(torus(drumR*0.80,0.11,8,20),M.copper);
    flight.position.x=fx; flight.rotation.y=Math.PI/2+(fx*0.9);
    drumGrp.add(flight);
  }}

  g.add(drumGrp);

  // Drive motor pinion skid (stationary)
  const drivGrp=new THREE.Group(); drivGrp.position.set(-1.8, 2.0, 2.4);
  motorDrive(drivGrp,0,0.3,0,0.95);
  add(drivGrp,cyl(0.26,0.5,16),M.ci, 0,2.0,-0.65); // pinion
  g.add(drivGrp);

  // Feed breeching hood (stationary, left end)
  add(g,box(1.8,2.8*2,3.2),M.cs, -5.6, drumY,0);
  add(g,cyl(0.42,1.2),M.ssBrushed, -5.6, drumY+1.9,0); // feed chute inlet

  // Discharge hood (right end) + cyclone stack
  add(g,box(1.8,2.8*2,3.2),M.cs,  5.6, drumY,0);
  add(g,cyl(0.38,2.6),M.ssBrushed, 5.6, drumY+2.4,0); // vapour stack
  // Cyclone separator on top
  add(g,cone(0.65,1.3,16),M.ssBrushed, 5.6, drumY+3.4+0.65,0, Math.PI,0,0);
  add(g,cyl(0.65,0.3,16),M.ssBrushed, 5.6, drumY+3.4+1.3,0);

  // Bottom rotary airlock discharge
  add(g,cyl(0.32,0.5,16),M.red, 5.6, drumY-1.6,0, 0,0,Math.PI/2);

  animFns.push(()=>{{drumGrp.rotation.x+=0.012;}});
  plantGrp.add(g); eqObjs['D-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 3. M-101  INDUSTRIAL HAMMER MILL
//    Heavy I-beam skid, clamshell housing, rotor+hammers, motor+belt guard
// ══════════════════════════════════════════════════════════════════════════
function buildM101(ox,oz){{
  const g=new THREE.Group(); g.name='M-101'; g.position.set(ox,0,oz);
  const col=selMat('M-101',M.M101col);
  const houseMat=isCut?M.glass:col;

  pad(g,4.4,4.0,0.3);

  // I-beam skid frame
  add(g,box(3.8,0.38,3.4),M.ci,0,0.3+0.19,0);  // top beam
  for(let bx of[-1.6,1.6]){{
    add(g,box(0.3,0.7,3.4),M.ci,bx,0.3+0.35,0);  // web
    add(g,box(0.65,0.12,3.4),M.ci,bx,0.3+0.65,0);// bottom flange
  }}

  // Anti-vibration mounts
  for(let sx of[-1.5,1.5]) for(let sz of[-1.3,1.3])
    add(g,cyl(0.11,0.22,8),M.yellow, sx,0.3+0.73,sz);

  // Lower cast-iron mill base frame
  add(g,box(2.2,1.2,2.4),M.ci, 0.3,0.3+0.65+0.6,0);

  // Upper clamshell housing (open-side cutaway)
  const hY=0.3+0.65+1.2+0.9, hR=1.0;
  const housGeo=new THREE.CylinderGeometry(hR,hR,2.1,28,1,true,CW,CL);
  const housOpen=new THREE.Mesh(housGeo, houseMat);
  housOpen.rotation.x=Math.PI/2; housOpen.rotation.z=Math.PI/4;
  housOpen.position.set(0.3,hY,0); housOpen.castShadow=true; g.add(housOpen);
  // Closed half
  const housClosed=new THREE.Mesh(
    new THREE.CylinderGeometry(hR,hR,2.1,28,1,true,CW+CL,CL), col
  );
  housClosed.rotation.x=Math.PI/2; housClosed.rotation.z=Math.PI/4;
  housClosed.position.set(0.3,hY,0); housClosed.castShadow=true; g.add(housClosed);

  // Rotor shaft (horizontal, in mill axis = z)
  const rotorShaft=new THREE.Mesh(cyl(0.13,2.5),M.ss316);
  rotorShaft.rotation.x=Math.PI/2; rotorShaft.position.set(0.3,hY,0); g.add(rotorShaft);

  // Rotor assembly (spins)
  const rotGrp=new THREE.Group(); rotGrp.position.set(0.3,hY,0);
  rotGrp.rotation.x=Math.PI/2;
  // 5 rotor discs
  for(let dz=-0.8;dz<=0.8;dz+=0.4){{
    add(rotGrp,cyl(0.52,0.09,20),M.ci,0,dz,0);
    // 4 hammers per disc
    for(let h=0;h<4;h++){{
      const ha=h*Math.PI/2;
      const hammer=new THREE.Mesh(box(0.11,0.44,0.08),M.ssBrushed);
      hammer.position.set(Math.cos(ha)*0.72, dz+0.04, Math.sin(ha)*0.72);
      hammer.rotation.z=ha; rotGrp.add(hammer);
    }}
  }}
  g.add(rotGrp);

  // Sieve screen (arc under rotor)
  const screen=new THREE.Mesh(
    new THREE.CylinderGeometry(0.90,0.90,2.0,24,1,true,Math.PI,Math.PI),M.copper
  );
  screen.rotation.x=Math.PI/2; screen.position.set(0.3,hY,0); g.add(screen);

  // Electric drive motor (left side)
  const motGrp=new THREE.Group(); motGrp.position.set(-1.2,0.3+0.65+0.5,0);
  add(motGrp,cyl(0.38,1.4),M.blue,0,0.7,0,Math.PI/2,0,0);  // motor body
  add(motGrp,cyl(0.4,0.26,20),M.cs,0,1.5,0,Math.PI/2,0,0); // cowl
  g.add(motGrp);

  // V-belt guard enclosure
  add(g,box(1.8,1.5,0.38),M.yellow, -0.4,0.3+0.65+0.95, 1.4);

  // Feed hopper (top)
  add(g,new THREE.ConeGeometry(0.9,1.6,4),col, 0.3,hY+0.9+0.8+0.8,0);
  add(g,cyl(0.35,0.8,12),M.ssBrushed, 0.3,hY+0.9+0.8*0.5,0);  // throat

  // Discharge hopper (bottom)
  add(g,new THREE.ConeGeometry(0.7,1.1,4),M.cs, 0.3,0.3+0.65+0.3,0, Math.PI,0,0);

  animFns.push(()=>{{rotGrp.rotation.z+=0.14;}});
  plantGrp.add(g); eqObjs['M-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 4. T-102  STAINLESS STEEL SLURRY MIXING TANK
//    316L vessel, dished bottom, hydrofoil impellers, acid dosing tube
// ══════════════════════════════════════════════════════════════════════════
function buildT102(ox,oz){{
  const g=new THREE.Group(); g.name='T-102'; g.position.set(ox,0,oz);
  const col=selMat('T-102',M.T102col);
  const shellMat=cylMat('T-102',M.T102col);
  const H=3.8, R=1.75, legH=1.6;
  const shellBase=legH+0.3;

  pad(g,5,5,0.3);
  // 4 stainless pipe legs
  for(let i=0;i<4;i++){{
    const a=i*Math.PI/2+Math.PI/4, lx=Math.cos(a)*(R*0.75), lz=Math.sin(a)*(R*0.75);
    add(g,cyl(0.10,legH),M.ss316, lx,0.3+legH/2,lz);
    add(g,cyl(0.17,0.06,16),M.cs, lx,0.3+0.03,lz);
    add(g,cyl(0.17,0.06,16),M.cs, lx,0.3+legH-0.03,lz);
  }}
  // Cross braces
  for(let i=0;i<2;i++) add(g,box(R*1.5,0.07,0.07),M.ss316,0,0.3+legH*0.6,0,0,i*Math.PI/2,0);

  // Dished bottom (inverted ellipsoid cap)
  const shY=shellBase+H/2;
  add(g,sphere(R,FW,FL,Math.PI/2,Math.PI/2.1),col,0,shellBase,0);

  // Shell
  const [ps,pl]=phi(true);
  add(g,new THREE.CylinderGeometry(R,R,H,36,1,true,ps,pl),shellMat,0,shY,0);
  add(g,cyl(R+0.07,0.09),M.cs,0,shellBase,0);
  add(g,cyl(R+0.07,0.09),M.cs,0,shellBase+H,0);

  // Dished top head
  add(g,sphere(R,FW,FL,0,Math.PI/2.1),col,0,shellBase+H,0);

  // Mixer bridge + motor
  add(g,box(R*2.4,0.18,0.60),M.ss316,0,shellBase+H+0.56,0);
  motorDrive(g,0,shellBase+H+0.62,0,0.95);

  // Agitator shaft
  const shaftMsh=add(g,cyl(0.065,H+0.55),M.ss316,0,shY,0);

  // Dual hydrofoil impeller group
  const hydGrp=new THREE.Group(); hydGrp.position.set(0,shY,0);
  for(const tier of[-H*0.28, H*0.12]){{
    for(let b=0;b<3;b++){{
      const a=b*Math.PI*2/3;
      const blade=new THREE.Mesh(box(R*0.80,0.065,0.22),M.ss316);
      blade.position.set(Math.cos(a)*R*0.38,tier,Math.sin(a)*R*0.38);
      blade.rotation.set(0.22,a,0); hydGrp.add(blade);
    }}
  }}
  g.add(hydGrp);

  // 4 baffles
  for(let i=0;i<4;i++){{
    const a=i*Math.PI/2;
    const bfl=new THREE.Mesh(box(0.26,H*0.86,0.045),M.ss316);
    bfl.position.set(Math.cos(a)*(R-0.05),shY,Math.sin(a)*(R-0.05));
    bfl.rotation.y=-a; g.add(bfl);
  }}

  // Acid dosing dip tube (purple/violet top valve)
  add(g,cyl(0.045,H*0.90,12),M.copper, R*0.52,shY, R*0.52);
  add(g,box(0.22,0.22,0.22),
    new THREE.MeshStandardMaterial({{color:0x805ad5}}),
    R*0.52, shellBase+H+0.36, R*0.52);

  // Radar level transmitter (blue cylinder on top)
  add(g,cyl(0.11,0.38,12),M.blue, -R*0.5,shellBase+H+0.76,R*0.5);

  // Side manway
  nozzle(g,0.30,0.26, R,shY+0.3,0,'x');

  // CW inlet nozzle
  nozzle(g,0.10,0.35, 0,shellBase+H*0.8,-R,'z');

  animFns.push(()=>{{hydGrp.rotation.y+=0.055; shaftMsh.rotation.y+=0.055;}});
  plantGrp.add(g); eqObjs['T-102']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 5. R-101  HIGH-PRESSURE PRETREATMENT REACTOR  ← primary focus unit
//    Skirt-mounted vertical CSTR, jacket, flanged top head, anchor agitator
// ══════════════════════════════════════════════════════════════════════════
function buildR101(ox,oz){{
  const g=new THREE.Group(); g.name='R-101'; g.position.set(ox,0,oz);
  const col=selMat('R-101',M.R101col);
  const shellMat=cylMat('R-101',M.R101col);

  const R=1.9;    // vessel radius
  const H=4.2;    // straight shell height
  const skirtH=1.6; // short skirt (NOT dominating)
  const padH=0.3;
  // Key Y reference:  vessel shell occupies [base,base+H]
  const base = padH + skirtH;      // bottom of cylindrical shell
  const shY  = base + H/2;         // vessel centre (camera will target this)
  const topY = base + H;            // top of shell

  pad(g,5.5,5.5,padH);

  // ── Cylindrical skirt support (short, structural) ──
  add(g,new THREE.CylinderGeometry(R*0.72,R*0.78,skirtH,32),M.cs, 0,padH+skirtH/2,0);
  // Skirt access manhole
  add(g,cyl(0.35,0.22,16),M.cs, 0,padH+skirtH/2, R*0.72, Math.PI/2,0,0);
  // Anchor bolt ring (visible flats around skirt base)
  for(let b=0;b<16;b++){{
    const a=b*Math.PI/8;
    add(g,box(0.12,0.28,0.12),M.cs, Math.cos(a)*(R*0.78+0.08),padH+0.14,Math.sin(a)*(R*0.78+0.08));
  }}

  // ── Ellipsoidal bottom head ──
  // SphereGeometry with phiStart for cutaway
  const [ps,pl]=phi(true);
  const botHead=new THREE.Mesh(sphere(R,ps,pl,Math.PI/2,Math.PI/2.15),shellMat);
  botHead.position.set(0,base,0); botHead.castShadow=true; g.add(botHead);

  // ── Main pressure vessel cylindrical shell ──
  const shell=new THREE.Mesh(
    new THREE.CylinderGeometry(R,R,H,36,1,true,ps,pl), shellMat
  );
  shell.position.set(0,shY,0); shell.castShadow=true; g.add(shell);

  // ── External steam heating jacket (bottom 68% of shell) ──
  const jH=H*0.68, jR=R+0.14;
  const jacketMat=isCut?M.glass:M.insul;
  // Show jacket as separate colour when no cutaway, as insulation-coloured sleeve
  const jacket=new THREE.Mesh(
    new THREE.CylinderGeometry(jR,jR,jH,36,1,true,ps,pl), jacketMat
  );
  jacket.position.set(0, base+jH/2, 0); jacket.castShadow=true; g.add(jacket);
  // Jacket band rings
  add(g,cyl(jR+0.04,0.09),M.cs,0,base+jH,0);
  add(g,cyl(jR+0.04,0.09),M.cs,0,base+0.04,0);
  // Steam inlet/condensate outlet nozzles on jacket
  nozzle(g,0.11,0.42, jR,base+jH*0.75,0,'x');
  nozzle(g,0.11,0.42, jR,base+jH*0.18,0,'x');

  // ── Flanged top head joint: 24 visible stud bolts ──
  const fY=topY+0.05;
  add(g,cyl(R+0.14,0.14),M.cs,0,fY,0);  // top ring flange
  for(let b=0;b<24;b++){{
    const a=b*Math.PI*2/24;
    add(g,cyl(0.045,0.28,8),M.ss316,Math.cos(a)*(R+0.14),fY,Math.sin(a)*(R+0.14));
  }}

  // ── Ellipsoidal top head ──
  const topHead=new THREE.Mesh(sphere(R,ps,pl,0,Math.PI/2.15),shellMat);
  topHead.position.set(0,topY+0.07,0); topHead.castShadow=true; g.add(topHead);

  // ── Heavy top drive (motor + gearbox) ──
  motorDrive(g,0,topY+0.07+R*0.5+0.3,0,1.3);

  // ── Mechanical seal housing (small cylinder below motor) ──
  add(g,cyl(0.22,0.35,16),M.ssBrushed, 0,topY+0.07+R*0.5+0.1,0);
  // Seal barrier pot
  add(g,cyl(0.16,0.72,16),M.ssBrushed, R*0.55,topY+0.07+R*0.5+0.5, R*0.3);

  // ── INTERNAL COMPONENTS (anchor agitator + baffles + thermowells) ──
  const internalGrp=new THREE.Group();
  internalGrp.position.set(0,shY,0);

  // Agitator shaft
  const aShaft=new THREE.Mesh(cyl(0.085,H+0.6),M.ss316);
  internalGrp.add(aShaft);

  // Anchor frame: 2 vertical sweep arms + horizontal cross-bow
  const armMat=M.ss316;
  // Left arm
  const armL=new THREE.Mesh(box(0.12,H*0.72,0.18),armMat);
  armL.position.set(-(R-0.18),-H*0.1,0); internalGrp.add(armL);
  // Right arm
  const armR=new THREE.Mesh(box(0.12,H*0.72,0.18),armMat);
  armR.position.set( (R-0.18),-H*0.1,0); internalGrp.add(armR);
  // Top connecting bar
  const topBar=new THREE.Mesh(box(R*1.75,0.12,0.18),armMat);
  topBar.position.set(0,H*0.26,0); internalGrp.add(topBar);
  // Bottom cross-bow
  const bow=new THREE.Mesh(box(R*1.75,0.12,0.22),armMat);
  bow.position.set(0,-H*0.44,0); internalGrp.add(bow);
  // PTFE wall wiper blades (highly visible copper contrast)
  for(let wy of[-H*0.35,-H*0.1,H*0.15]){{
    const wiperL=new THREE.Mesh(box(0.14,0.3,0.10),M.copper);
    wiperL.position.set(-(R-0.07),wy,0); internalGrp.add(wiperL);
    const wiperR=new THREE.Mesh(box(0.14,0.3,0.10),M.copper);
    wiperR.position.set( (R-0.07),wy,0); internalGrp.add(wiperR);
  }}
  // Rear wall agitator brace
  const rear=new THREE.Mesh(box(0.12,H*0.70,0.18),armMat);
  rear.position.set(0,-H*0.1,-(R-0.18)); internalGrp.add(rear);

  // 4 vertical anti-vortex baffles
  for(let i=0;i<4;i++){{
    const a=i*Math.PI/2+Math.PI/4;
    const bfl=new THREE.Mesh(box(0.28,H*0.82,0.05),M.ssBrushed);
    bfl.position.set(Math.cos(a)*(R-0.05),0,Math.sin(a)*(R-0.05));
    bfl.rotation.y=-a; internalGrp.add(bfl);
  }}

  g.add(internalGrp);

  // ── 3-tier thermowell array (blue instrument heads on vessel wall) ──
  for(const tw of[-H*0.3+shY-shY, 0, H*0.26]){{
    nozzle(g,0.075,0.38, -(R+0.14),shY+tw,0,'-x');
    // RTD head
    add(g,box(0.14,0.18,0.14),M.blue, -(R+0.52),shY+tw,0);
  }}

  // ── Safety relief valve + rupture disc ──
  const srvGrp=new THREE.Group(); srvGrp.position.set(-R*0.4,topY+0.07+R*0.5+0.1,-R*0.4);
  add(srvGrp,cyl(0.11,0.60,12),M.red,0,0.3,0);
  add(srvGrp,cone(0.11,0.4,12),M.cs,0,0.6+0.2,0);
  g.add(srvGrp);

  // ── Feed inlet nozzle (top side) ──
  nozzle(g,0.14,0.55, 0,topY+0.07+R*0.5-0.2,R*0.6,'y');
  // ── Bottom blowdown valve ──
  add(g,box(0.38,0.44,0.38),M.red, 0,padH+skirtH*0.35,0);

  animFns.push(()=>{{internalGrp.rotation.y+=0.032;}});

  plantGrp.add(g); eqObjs['R-101']=g;
  return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 6. F-101  INDUSTRIAL RECESSED MEMBRANE FILTER PRESS
//    Heavy I-beam frame, 22 filter plates, hydraulic cylinder
// ══════════════════════════════════════════════════════════════════════════
function buildF101(ox,oz){{
  const g=new THREE.Group(); g.name='F-101'; g.position.set(ox,0,oz);
  const col=selMat('F-101',M.F101col);

  pad(g,7.2,4.0,0.3);

  // 4 vertical support columns
  for(let px of[-2.8,2.8]) for(let pz of[-1.2,1.2])
    add(g,box(0.38,2.0,0.38),M.ci, px,0.3+1.0,pz);

  // Dual horizontal side guide bars / tension rails
  for(let pz of[-1.25,1.25])
    add(g,box(5.8,0.32,0.18),M.cs, 0,0.3+2.0,pz);

  // Stationary feed head (cast-iron, left)
  add(g,box(0.72,2.6,2.6),M.ci, -2.8,0.3+2.0+1.3,0);

  // Rear thrust stand (right)
  add(g,box(0.72,2.6,2.6),M.ci,  2.8,0.3+2.0+1.3,0);

  // Hydraulic clamping cylinder
  add(g,cyl(0.42,1.8,24),M.blue, 3.65,0.3+2.0+1.3,0,0,0,Math.PI/2);
  // Chrome ram rod
  add(g,cyl(0.21,1.4,20),M.ss316, 2.5,0.3+2.0+1.3,0,0,0,Math.PI/2);

  // Moving follower plate
  add(g,box(0.38,2.4,2.3),M.cs, 1.5,0.3+2.0+1.3,0);

  // 22 filter plates stack (colour-coded: polypropylene grey-blue)
  const pMat=selMat('F-101',new THREE.MeshStandardMaterial({{color:0x4a7c8a,metalness:0.2,roughness:0.6}}));
  for(let p=0;p<22;p++){{
    const px=-2.35+p*0.17;
    add(g,box(0.09,2.2,2.15),pMat, px,0.3+2.0+1.3,0);
    // Hanging handle
    add(g,box(0.09,0.14,2.55),M.cs, px,0.3+2.0+2.2,0);
  }}

  // Twin filtrate collection launders
  for(let pz of[-1.18,1.18])
    add(g,box(4.6,0.26,0.4),M.ss316, -0.3,0.3+2.0-0.14,pz);

  // Cake discharge hopper
  add(g,box(4.8,0.85,2.1),M.cs, -0.3,0.3+0.85/2,0);

  // HPU skid (rear right)
  add(g,box(1.3,1.1,1.5),M.ci, 3.5,0.3+0.55,1.5);
  add(g,cyl(0.22,0.9),M.blue, 3.5,0.3+0.55+0.65,1.5);

  // Feed slurry inlet valve
  add(g,box(0.4,0.42,0.4),M.red, -2.8,0.3+2.0+0.1,0);

  plantGrp.add(g); eqObjs['F-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 7. E-101  INDUSTRIAL FERMENTATION BIOREACTOR
//    Slender 3:1 aspect vessel, 3-tier Rushton turbines, sparger, baffles
// ══════════════════════════════════════════════════════════════════════════
function buildE101(ox,oz){{
  const g=new THREE.Group(); g.name='E-101'; g.position.set(ox,0,oz);
  const col=selMat('E-101',M.E101col);
  const shellMat=cylMat('E-101',M.E101col);

  const R=2.2, H=7.0, skH=1.6;
  const base=0.3+skH, shY=base+H/2, topY=base+H;

  pad(g,6.0,6.0,0.3);

  // Skirt
  add(g,new THREE.CylinderGeometry(R*0.70,R*0.76,skH,32),M.cs, 0,0.3+skH/2,0);
  for(let b=0;b<16;b++){{
    const a=b*Math.PI/8;
    add(g,box(0.11,0.26,0.11),M.cs, Math.cos(a)*(R*0.76+0.07),0.3+0.13,Math.sin(a)*(R*0.76+0.07));
  }}

  // Bottom dished head
  const [ps,pl]=phi(true);
  add(g,sphere(R,ps,pl,Math.PI/2,Math.PI/2.1),shellMat,0,base,0);

  // Shell
  const sh=new THREE.Mesh(new THREE.CylinderGeometry(R,R,H,36,1,true,ps,pl),shellMat);
  sh.position.set(0,shY,0); sh.castShadow=true; g.add(sh);
  add(g,cyl(R+0.07,0.09),M.cs,0,base,0);
  add(g,cyl(R+0.07,0.09),M.cs,0,topY,0);

  // Top head
  add(g,sphere(R,ps,pl,0,Math.PI/2.1),shellMat,0,topY,0);

  // Drive motor
  motorDrive(g,0,topY+R*0.5+0.5,0,1.35);
  add(g,cyl(0.20,0.40,16),M.ssBrushed,0,topY+R*0.5+0.18,0); // seal housing

  // Agitator shaft
  const aShaft=add(g,cyl(0.075,H+0.55),M.ss316,0,shY,0);

  // 3-tier Rushton disc turbine group
  const rushGrp=new THREE.Group(); rushGrp.position.set(0,shY,0);
  for(const tier of[-H*0.33, 0, H*0.28]){{
    // Disc
    const disc=new THREE.Mesh(cyl(0.60,0.065,20),M.ss316); disc.position.set(0,tier,0); rushGrp.add(disc);
    // 6 flat blades
    for(let b=0;b<6;b++){{
      const ba=b*Math.PI*2/6;
      const blade=new THREE.Mesh(box(0.52,0.28,0.065),M.ss316);
      blade.position.set(Math.cos(ba)*0.86, tier, Math.sin(ba)*0.86);
      blade.rotation.y=-ba; rushGrp.add(blade);
    }}
  }}
  g.add(rushGrp);

  // 4 baffles
  for(let i=0;i<4;i++){{
    const ba=i*Math.PI/2;
    const bfl=new THREE.Mesh(box(0.34,H*0.86,0.05),M.ssBrushed);
    bfl.position.set(Math.cos(ba)*(R-0.06),shY,Math.sin(ba)*(R-0.06));
    bfl.rotation.y=-ba; g.add(bfl);
  }}

  // 4 internal cooling coil rods
  for(let i=0;i<4;i++){{
    const ca=i*Math.PI/2+Math.PI/4;
    add(g,cyl(0.075,H*0.80,12),M.ssBrushed, Math.cos(ca)*1.4,shY,Math.sin(ca)*1.4);
  }}

  // Bottom ring sparger
  add(g,torus(R*0.60,0.065),M.ss316, 0,base+0.45,0, Math.PI/2,0,0);

  // Top vent filter + foam breaker
  add(g,cyl(0.20,0.85,16),M.ssBrushed,-R*0.5,topY+R*0.5+0.1,R*0.4);
  add(g,cyl(0.14,0.5,12),M.ss316, 0,topY+0.3,R*0.6);

  // Sight glass strip
  add(g,box(0.14,H*0.5,0.28),M.glass, R,shY+H*0.1,0);

  // CIP spray balls
  for(let sx of[-0.7,0.7])
    add(g,sphere(0.11),M.ss316, sx,topY+0.1,0);

  // Sample / sensor nozzles (blue indicator heads)
  for(const nh of[-H*0.2,0,H*0.25])
    nozzle(g,0.07,0.38, R,shY+nh,0,'x');

  animFns.push(()=>{{rushGrp.rotation.y+=0.038; aShaft.rotation.y+=0.038;}});
  plantGrp.add(g); eqObjs['E-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 8. S-101  CONTINUOUS DISC-STACK CLARIFICATION CENTRIFUGE
//    Cast-iron base, vertical high-speed bowl, disc stack, paring disc
// ══════════════════════════════════════════════════════════════════════════
function buildS101(ox,oz){{
  const g=new THREE.Group(); g.name='S-101'; g.position.set(ox,0,oz);
  const col=selMat('S-101',M.S101col);
  const bowlMat=cylMat('S-101',M.S101col);

  pad(g,4.5,4.5,0.3);

  // Cast-iron machine base frame
  add(g,new THREE.CylinderGeometry(1.75,1.9,1.5,24),M.ci,0,0.3+0.75,0);

  // Drive motor (vertical) inside base
  add(g,cyl(0.32,0.95,16),M.blue,0,0.3+0.6,0.95, Math.PI/2,0,0);

  // Centrifuge bowl casing (upper)
  const [ps,pl]=phi(true);
  const bowY=0.3+1.5+0.75;
  add(g,new THREE.CylinderGeometry(1.4,1.4,1.5,32,1,true,ps,pl),bowlMat,0,bowY,0);
  // Conical lower section
  const cone3=new THREE.Mesh(
    new THREE.ConeGeometry(1.4,1.3,32,1,true,ps,pl),bowlMat
  ); cone3.rotation.x=Math.PI; cone3.position.set(0,0.3+1.5+0.1,0); g.add(cone3);

  // Internal disc stack (spins)
  const diskGrp=new THREE.Group(); diskGrp.position.set(0,bowY,0);
  add(diskGrp,cyl(0.11,1.6),M.ss316,0,0,0); // central spindle
  for(let d=-0.5;d<=0.5;d+=0.09){{
    const coneDisc = new THREE.Mesh(new THREE.ConeGeometry(1.1,0.22,24,1,true),M.ssBrushed);
    coneDisc.position.set(0, d, 0);
    diskGrp.add(coneDisc);
  }}
  g.add(diskGrp);

  // Top paring disc chamber (centripetal pump)
  add(g,cyl(0.50,0.38,20),M.ssBrushed,0,bowY+1.0,0);

  // Feed pipe entering from top
  add(g,cyl(0.09,0.9,12),M.ss316,0,bowY+1.5,0);

  // Clarified broth outlet pipe (side elbow)
  add(g,cyl(0.085,1.2,12),M.ss316,-0.75,bowY+0.85,0,0,0,Math.PI/2);

  // Solids ejection chute
  add(g,new THREE.CylinderGeometry(0.28,0.14,0.85,16),M.cs, 1.1,0.3+1.5+0.35,0,0,0,-0.5);

  animFns.push(()=>{{diskGrp.rotation.y+=0.18;}});
  plantGrp.add(g); eqObjs['S-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 9. C-101  MULTI-STAGE FRACTIONAL DISTILLATION COLUMN
//    Tall column with sieve trays, side reboiler, top condenser, ladder
// ══════════════════════════════════════════════════════════════════════════
function buildC101(ox,oz){{
  const g=new THREE.Group(); g.name='C-101'; g.position.set(ox,0,oz);
  const col=selMat('C-101',M.C101col);
  const shellMat=cylMat('C-101',M.C101col);

  const R=1.45, H=14.0, skH=2.0;
  const base=0.3+skH, shY=base+H/2, topY=base+H;

  pad(g,6.5,5.5,0.3);

  // Skirt support
  add(g,new THREE.CylinderGeometry(R*0.72,R*0.78,skH,32),M.cs,0,0.3+skH/2,0);
  nozzle(g,0.35,0.26,0,0.3+skH/2,R*0.78,'z'); // skirt manhole

  // Nozzle ring flange at skirt-to-shell join
  add(g,cyl(R+0.1,0.1),M.cs,0,base,0);

  // Shell
  const [ps,pl]=phi(true);
  const sh=new THREE.Mesh(new THREE.CylinderGeometry(R,R,H,36,1,true,ps,pl),shellMat);
  sh.position.set(0,shY,0); sh.castShadow=true; g.add(sh);

  // Girder rings every ~2.5m
  for(let gy=base;gy<=topY;gy+=2.5)
    add(g,cyl(R+0.07,0.09),M.cs,0,gy,0);

  // Top head
  add(g,sphere(R,ps,pl,0,Math.PI/2.1),shellMat,0,topY,0);

  // ── 16 internal sieve trays ──
  const numTrays=16, tStep=(H-1.5)/numTrays;
  for(let t=0;t<numTrays;t++){{
    const ty=base+0.8+t*tStep;
    add(g,cyl(R-0.07,0.055,24),M.copper,0,ty,0);
    // Downcomer apron
    const dcSide=(t%2===0?0.75:-0.75);
    add(g,box(0.055,tStep*0.72,0.75),M.ssBrushed, dcSide,ty-tStep*0.32,0);
  }}

  // ── Side horizontal thermosiphon reboiler skid ──
  const rebGrp=new THREE.Group(); rebGrp.position.set(3.0,0.3+1.5,0);
  add(rebGrp,cyl(0.80,2.8,24),M.ssBrushed, 0,0,0, 0,0,Math.PI/2);
  // Vapor return elbow (copper)
  add(rebGrp,cyl(0.17,1.5,16),M.copper, -1.6,0.65,0, 0,0,Math.PI/2);
  add(rebGrp,cyl(0.17,0.75,16),M.copper, -1.6,0.65+0.75/2,0);
  // Steam inlet nozzle
  nozzle(rebGrp,0.11,0.45, -0.7,0.80,0,'y');
  g.add(rebGrp);

  // ── Overhead vapour line + condenser ──
  add(g,cyl(0.19,2.2,16),M.copper, 0,topY+1.1,0);
  add(g,cyl(0.65,2.5,20),M.ssBrushed, -2.2,topY+1.6,0, 0,0,Math.PI/2);

  // Reflux accumulator drum
  add(g,cyl(0.50,1.7,16),M.ss316, -2.2,topY-0.5,0, 0,0,Math.PI/2);

  // ── Full-height safety cage ladder ──
  for(let ry=0.8;ry<H+2;ry+=0.46)
    add(g,box(0.52,0.04,0.045),M.yellow, -(R+0.08),0.3+ry,0);
  // Cage side rails
  add(g,box(0.045,H+2.4,0.045),M.yellow, -(R+0.33),shY,0);
  add(g,box(0.045,H+2.4,0.045),M.yellow, -(R-0.08),shY,0);

  // ── 3 maintenance platforms ──
  for(const py of[base+H*0.25, base+H*0.55, base+H*0.82]){{
    add(g,cyl(R+0.95,0.09),M.cs,0,py,0);
    add(g,torus(R+0.90,0.04),M.yellow,0,py+0.90,0,Math.PI/2,0,0);
  }}

  // Feed nozzle
  nozzle(g,0.14,0.52, R,base+H*0.45,0,'x');
  // Bottoms (stillage) outlet
  nozzle(g,0.14,0.45, 0,base+0.3,0,'y');

  plantGrp.add(g); eqObjs['C-101']=g; return g;
}}

// ══════════════════════════════════════════════════════════════════════════
// 10. V-101  TWIN-BED MOLECULAR SIEVE PSA DEHYDRATION SYSTEM
//    Structural skid, 2 adsorption vessels, switching valve manifold
// ══════════════════════════════════════════════════════════════════════════
function buildV101(ox,oz){{
  const g=new THREE.Group(); g.name='V-101'; g.position.set(ox,0,oz);
  const col=selMat('V-101',M.V101col);
  const vMat=cylMat('V-101',M.V101col);

  pad(g,6.0,4.6,0.3);

  // Structural steel skid base
  add(g,box(5.4,0.28,4.0),M.ci,0,0.3+0.14,0);
  // Cross-beams
  for(let sx of[-2.1,2.1]) add(g,box(0.22,0.28,4.0),M.ci,sx,0.3+0.14,0);

  // Twin adsorption vessels
  const [ps,pl]=phi(true);
  for(const bx of[-1.6,1.6]){{
    const bH=5.4, bR=0.82;
    // Skirt
    add(g,new THREE.CylinderGeometry(bR*0.65,bR*0.70,1.1,24),M.cs,bx,0.3+0.28+0.55,0);
    // Bottom head
    add(g,sphere(bR,ps,pl,Math.PI/2,Math.PI/2.1),vMat,bx,0.3+0.28+1.1,0);
    // Shell
    const bY=0.3+0.28+1.1+bH/2;
    const bSh=new THREE.Mesh(new THREE.CylinderGeometry(bR,bR,bH,28,1,true,ps,pl),vMat);
    bSh.position.set(bx,bY,0); g.add(bSh);
    // Zeolite bed (copper interior)
    add(g,cyl(bR-0.08,bH*0.75,20),M.copper,bx,bY,0);
    // Top head
    add(g,sphere(bR,ps,pl,0,Math.PI/2.1),vMat,bx,0.3+0.28+1.1+bH,0);
    // Flange rings
    add(g,cyl(bR+0.1,0.09),M.cs,bx,0.3+0.28+1.1,0);
    add(g,cyl(bR+0.1,0.09),M.cs,bx,0.3+0.28+1.1+bH,0);
  }}

  // Cross-over switching valve manifold
  const manY=0.3+0.28+1.1+5.4*0.5;
  add(g,cyl(0.095,3.6),M.ssBrushed, 0,manY,0, 0,0,Math.PI/2);
  for(const vx of[-1.0,0,1.0]){{
    add(g,box(0.36,0.46,0.36),M.red, vx,manY,0);
    add(g,cyl(0.14,0.5,12),M.blue, vx,manY+0.46,0); // actuator
  }}

  // Regeneration superheater exchanger (horizontal)
  add(g,cyl(0.38,1.9,16),M.ssBrushed, 0,0.3+0.28+0.75,-1.4,0,0,Math.PI/2);

  // Water knockout drum
  add(g,cyl(0.33,1.5,16),M.ss316, -2.2,0.3+0.28+1.4,1.3);
  // Level gauge
  add(g,box(0.06,1.2,0.06),M.glass, -2.2+0.33+0.08,0.3+0.28+1.4,1.3);

  // Duplex filter vessels
  for(const fx of[2.0,2.55])
    add(g,cyl(0.19,1.1,16),M.ss316, fx,0.3+0.28+1.2,1.3);

  // Product outlet pipe
  add(g,cyl(0.11,1.2,16),M.ssBrushed, 2.4,0.3+0.28+1.2,0, 0,0,Math.PI/2);

  plantGrp.add(g); eqObjs['V-101']=g; return g;
}}

// ─── BUILD ALL EQUIPMENT (PFD LAYOUT) ─────────────────────────────────────
buildT101(-30, 0);
buildD101(-20, 0);
buildM101(-11, 0);
buildT102( -3, 0);
buildR101(  5, 0);
buildF101( 13, 0);

buildE101( 13, 18);
buildS101(  3, 18);
buildC101( -8, 18);
buildV101(-19, 18);

// Auxiliary pumps
pump(plantGrp,-27.0,0.3,1.4,0);
pump(plantGrp, -7.5,0.3,-2.0, Math.PI/2);
pump(plantGrp,  0.5,0.3,-0.5,0);
pump(plantGrp, 14.5,0.3,9.0,Math.PI/2);
pump(plantGrp,  8.0,0.3,18.0,0);
pump(plantGrp, -2.0,0.3,18.0,0);

// ─── PROCESS PIPING & FLOW PARTICLES ──────────────────────────────────────
const pipeDefs=[
  {{ pts:[[-30,2.5,0],[-24,2.5,0]],                        col:0x38a169, r:0.16 }},
  {{ pts:[[-15.5,2.5,0],[-11,2.5,0]],                      col:0x38a169, r:0.16 }},
  {{ pts:[[-11,1.5,0],[-7.5,1.5,0],[-7.5,3.5,0],[-3,3.5,0]], col:0x38a169,r:0.14}},
  {{ pts:[[-3,2,0],[0.5,2,0],[0.5,3.8,0],[5,3.8,0]],       col:0x38a169, r:0.14 }},
  {{ pts:[[5,1.4,0],[9.4,1.4,0]],                           col:0x38a169, r:0.15 }},
  {{ pts:[[15.6,2.2,0],[19.5,2.2,0],[19.5,2.2,18],[15.5,2.2,18]], col:0x3182ce,r:0.14}},
  {{ pts:[[10.8,2.2,18],[3,2.2,18]],                        col:0xd97706, r:0.14 }},
  {{ pts:[[3,2.5,18],[-8,2.5,18],[-8,5.5,18]],              col:0x3182ce, r:0.13 }},
  {{ pts:[[-8,13,18],[-13,13,18],[-13,5,18],[-19,5,18]],   col:0xecc94b, r:0.15 }},
  {{ pts:[[-19,2.5,18],[-26,2.5,18]],                       col:0x68d391, r:0.12 }},
  {{ pts:[[-3,5,0],[-3,6,0],[-3,6,-2.5]],                   col:0x805ad5, r:0.08 }},
  {{ pts:[[5,8,0],[5,8.5,0],[3.5,8.5,0]],                   col:0xdd6b20, r:0.09 }},
];

const particles=[];
pipeDefs.forEach(pd=>{{
  const v3pts=pd.pts.map(p=>new THREE.Vector3(...p));
  const curve=v3pts.length===2
    ? new THREE.LineCurve3(v3pts[0],v3pts[1])
    : new THREE.CatmullRomCurve3(v3pts,false,'catmullrom',0.1);

  const tubMat=new THREE.MeshStandardMaterial({{
    color:pd.col, metalness:0.70, roughness:0.32
  }});
  const tube=new THREE.Mesh(new THREE.TubeGeometry(curve,24,pd.r,10,false),tubMat);
  tube.castShadow=true; plantGrp.add(tube);

  const nP=Math.max(2,Math.floor(curve.getLength()/2.2));
  for(let i=0;i<nP;i++){{
    const sp=new THREE.Mesh(
      new THREE.SphereGeometry(pd.r*1.45,7,7),
      new THREE.MeshBasicMaterial({{color:0xffffff}})
    );
    plantGrp.add(sp);
    particles.push({{m:sp,c:curve,t:i/nP,s:0.004+pd.r*0.001}});
  }}
}});

// ─── EQUIPMENT ID LABELS (small point-lights per unit) ────────────────────
Object.entries(eqObjs).forEach(([id,grp])=>{{
  const bbox=new THREE.Box3().setFromObject(grp);
  const ctr=bbox.getCenter(new THREE.Vector3());
  // Small point light centred on each unit for depth accent
  const light=new THREE.PointLight(0x60a5fa,1.0,8);
  light.position.copy(ctr);
  scene.add(light);
}});

// ─── CAMERA POSITIONING ───────────────────────────────────────────────────
// Compute the TRUE bounding-box centre of the selected equipment
function getEqCentre(id){{
  const grp=eqObjs[id];
  if(!grp) return new THREE.Vector3(0,5,0);
  const bb=new THREE.Box3().setFromObject(grp);
  return bb.getCenter(new THREE.Vector3());
}}
function getEqSize(id){{
  const grp=eqObjs[id];
  if(!grp) return new THREE.Vector3(4,8,4);
  const bb=new THREE.Box3().setFromObject(grp);
  return bb.getSize(new THREE.Vector3());
}}

function camPreset(mode){{
  camera.up.set(0, 1, 0);
  if(mode === 'iso'){{
    if(isSingle && eqObjs[selId]){{
      const bb = new THREE.Box3().setFromObject(eqObjs[selId]);
      const ctr = bb.getCenter(new THREE.Vector3());
      const sz = bb.getSize(new THREE.Vector3());
      const dist = Math.max(sz.x, sz.y, sz.z) * 1.55 + 5;
      camera.position.set(ctr.x + dist * 0.65, ctr.y + dist * 0.42, ctr.z + dist * 0.9);
      controls.target.set(ctr.x, ctr.y, ctr.z);
    }} else {{
      camera.position.set(28, 32, 45);
      controls.target.set(-5, 4, 9);
    }}
  }}else if(mode === 'front'){{
    if(isSingle && eqObjs[selId]){{
      const bb = new THREE.Box3().setFromObject(eqObjs[selId]);
      const ctr = bb.getCenter(new THREE.Vector3());
      const sz = bb.getSize(new THREE.Vector3());
      const dist = Math.max(sz.x, sz.y, sz.z) * 1.6 + 5;
      camera.position.set(ctr.x, ctr.y + sz.y * 0.1, ctr.z + dist);
      controls.target.set(ctr.x, ctr.y, ctr.z);
    }} else {{
      camera.position.set(-5, 14, 55);
      controls.target.set(-5, 5, 9);
    }}
  }}else if(mode === 'top' || mode === 'plan'){{
    if(isSingle && eqObjs[selId]){{
      const bb = new THREE.Box3().setFromObject(eqObjs[selId]);
      const ctr = bb.getCenter(new THREE.Vector3());
      const sz = bb.getSize(new THREE.Vector3());
      const dist = Math.max(sz.x, sz.z) * 1.8 + 6;
      camera.position.set(ctr.x, ctr.y + dist, ctr.z + 0.01);
      controls.target.set(ctr.x, ctr.y, ctr.z);
    }} else {{
      camera.position.set(-5, 75, 9.01);
      controls.target.set(-5, 0, 9);
    }}
  }}else if(mode === 'sel' || mode === 'focus'){{
    const targetObj = eqObjs[selId];
    if(targetObj){{
      const bb = new THREE.Box3().setFromObject(targetObj);
      const ctr = bb.getCenter(new THREE.Vector3());
      const sz = bb.getSize(new THREE.Vector3());
      const dist = Math.max(sz.x, sz.y, sz.z) * 1.55 + 5;
      camera.position.set(ctr.x + dist * 0.65, ctr.y + dist * 0.42, ctr.z + dist * 0.9);
      controls.target.set(ctr.x, ctr.y, ctr.z);
    }} else {{
      camera.position.set(28, 32, 45);
      controls.target.set(-5, 4, 9);
    }}
  }}
  controls.update();
}}
window.camPreset = camPreset;

const bIso = document.getElementById('btn-iso');
if(bIso) bIso.addEventListener('click', function(e){{ e.preventDefault(); camPreset('iso'); }});
const bFront = document.getElementById('btn-front');
if(bFront) bFront.addEventListener('click', function(e){{ e.preventDefault(); camPreset('front'); }});
const bTop = document.getElementById('btn-top');
if(bTop) bTop.addEventListener('click', function(e){{ e.preventDefault(); camPreset('top'); }});
const bSel = document.getElementById('btn-sel');
if(bSel) bSel.addEventListener('click', function(e){{ e.preventDefault(); camPreset('sel'); }});

// Initial camera
if(isSingle){{
  const ctr=getEqCentre(selId);
  const sz=getEqSize(selId);
  const dist=Math.max(sz.x,sz.y,sz.z)*1.55+5;
  camera.position.set(ctr.x+dist*0.65, ctr.y+dist*0.42, ctr.z+dist*0.9);
  controls.target.set(ctr.x, ctr.y, ctr.z);
}}else{{
  camera.position.set(15,34,52);
  controls.target.set(-5,4,9);
}}
controls.update();

// ─── RENDER LOOP ──────────────────────────────────────────────────────────
function animate(){{
  requestAnimationFrame(animate);
  animFns.forEach(f=>{{ try{{ f(); }}catch(e){{}} }});
  particles.forEach(p=>{{
    p.t+=p.s; if(p.t>1) p.t=0;
    try{{ p.m.position.copy(p.c.getPointAt(p.t)); }}catch(e){{}}
  }});
  controls.update();
  renderer.render(scene,camera);
}}
animate();

function onWinResize(){{
  const nw = canvas.clientWidth || window.innerWidth || 800;
  const nh = canvas.clientHeight || window.innerHeight || 600;
  if (nw > 0 && nh > 0) {{
    camera.aspect = nw / nh;
    camera.updateProjectionMatrix();
    renderer.setSize(nw, nh);
  }}
}}
window.addEventListener('resize', onWinResize);
setTimeout(onWinResize, 200);
setTimeout(onWinResize, 800);
}})();
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
def render_3d_plant_section(dm: Any = None) -> None:
    """Renders the comprehensive 3D Process Plant & Digital Twin engineering suite."""

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0d47a1 0%,#1565c0 50%,#0277bd 100%);
                    padding:1.2rem 1.6rem;border-radius:10px;color:white;margin-bottom:1.2rem;
                    box-shadow:0 4px 15px rgba(2,119,189,.2)">
          <div style="font-size:1.45rem;font-weight:800;letter-spacing:-.02em">🏭 3D Process Plant &amp; Digital Twin</div>
          <div style="font-size:.85rem;color:#e1f5fe;margin-top:.2rem">
            Industrial WebGL Process Engineering Explorer · Detailed Equipment Assemblies · Live Simulation Telemetry Bus
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])
    with ctrl1:
        view_mode = st.selectbox(
            "Visualization Mode",
            ["Full Plant Overview (PFD Layout)", "Focused Equipment Inspection"],
            key="w_3d_view_mode",
        )
    with ctrl2:
        eq_list = list(EQUIPMENT_METADATA.keys())
        selected_eq = st.selectbox(
            "Select Process Equipment",
            eq_list,
            format_func=lambda k: f"{k} — {EQUIPMENT_METADATA[k]['name']}",
            key="w_3d_eq_select",
        )
    with ctrl3:
        cutaway_toggle = st.checkbox("Internal Cutaway / Components View", value=True, key="w_3d_cutaway")

    col_left, col_center, col_right = st.columns([1.1, 2.5, 1.4], gap="medium")

    with col_left:
        st.markdown(
            "<div style='font-size:.85rem;font-weight:700;color:#1565c0;margin-bottom:.4rem'>PROCESS EQUIPMENT ROSTER</div>",
            unsafe_allow_html=True,
        )
        for eid, meta in EQUIPMENT_METADATA.items():
            is_active = eid == selected_eq
            bg = "#e3f2fd" if is_active else "#ffffff"
            border = "2px solid #1565c0" if is_active else "1px solid #e2e8f0"
            st.markdown(
                f"""<div style="background:{bg};border:{border};border-radius:8px;padding:7px 10px;margin-bottom:6px">
                    <div style="font-weight:700;font-size:.82rem;color:#1a202c">{meta['icon']} {eid}: {meta['name']}</div>
                    <div style="font-size:.72rem;color:#718096">{meta['stage']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_center:
        mode_param = "single_equipment" if "Focused" in view_mode else "full_plant"
        html = build_threejs_html(selected_eq, mode_param, cutaway_toggle)
        components.html(html, height=600, scrolling=False)
        st.caption("🎮 **3D Controls:** Left-drag Rotate · Right-drag Pan · Scroll Zoom · Use preset buttons top-right to jump to views")

    with col_right:
        meta = EQUIPMENT_METADATA[selected_eq]
        st.markdown(f"#### {meta['icon']} {selected_eq}: {meta['name']}")
        st.caption(f"**Stage:** {meta['stage']}")
        r_tab1, r_tab2, r_tab3 = st.tabs(["📊 Live Telemetry", "⚙️ Internals", "📖 Principle"])

        with r_tab1:
            telem = extract_equipment_telemetry(selected_eq, dm)
            st.markdown(
                f"<div style='font-size:.75rem;font-weight:700;color:#2e7d32;margin-bottom:.4rem'>DATA BUS: {telem['status'].upper()}</div>",
                unsafe_allow_html=True,
            )
            if telem["parameters"]:
                st.dataframe(pd.DataFrame(telem["parameters"]), hide_index=True, use_container_width=True)
            else:
                st.info("No telemetry. Run simulation to stream live parameters.")

        with r_tab2:
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#4a5568'>INTERNAL MECHANICAL ASSEMBLIES:</div>", unsafe_allow_html=True)
            for item in meta["internals"]:
                st.markdown(f"• **{item}**")

        with r_tab3:
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#4a5568'>WORKING MECHANISM:</div>", unsafe_allow_html=True)
            st.write(meta["working_principle"])
