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

from typing import Any, Dict, List, Optional
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go

from core.material_balance import (
    compute_all_streams,
    compute_equipment_material_balance,
    compute_plant_material_balance,
    generate_sankey_data,
    STREAM_COLORS,
)

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
def build_threejs_html(
    selected_eq_id: str,
    view_mode: str = "full_plant",
    cutaway: bool = True,
    selected_stream_id: str = "",
    dm: Any = None,
) -> str:
    """Generate a self-contained Three.js WebGL page with detailed industrial equipment and mass balance streams."""

    cutaway_js = "true" if cutaway else "false"
    meta = EQUIPMENT_METADATA.get(selected_eq_id, {})
    eq_name = meta.get("name", selected_eq_id)
    mode_label = "Single Equipment" if view_mode == "single_equipment" else "Full Plant"

    # Compute authoritative simulation streams
    all_streams = compute_all_streams(dm)
    stream_payload = {}
    for sid, strm in all_streams.items():
        comp_summary = ", ".join(f"{k}: {v:.1f}%" for k, v in list(strm.component_fractions.items())[:3])
        stream_payload[sid] = {
            "name": strm.name,
            "flow_h": f"{strm.mass_flow_kg_h:.1f} kg/h",
            "flow_d": f"{strm.mass_flow_kg_day:,.1f} kg/d",
            "temp": f"{strm.temp_c:.1f} °C",
            "press": f"{strm.pressure_bar:.2f} bar",
            "phase": strm.phase,
            "moist": f"{strm.moisture_pct:.1f} %",
            "solids": f"{strm.solids_pct:.1f} %",
            "cat": strm.category,
            "src": strm.source_id,
            "tgt": strm.target_id,
            "comp": comp_summary,
            "desc": strm.description,
        }
    stream_data_json = json.dumps(stream_payload)
    active_stream_js = f'"{selected_stream_id}"' if selected_stream_id and selected_stream_id in stream_payload else '""'

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
      border-radius:6px;padding:7px 12px;color:#a0aec0;font-size:11px;display:flex;flex-wrap:wrap;gap:10px 16px;max-width:380px;z-index:9;pointer-events:none}}
.dot{{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:4px;vertical-align:middle}}
#tip{{position:fixed;bottom:12px;left:12px;background:rgba(10,13,20,.82);border:1px solid rgba(255,255,255,.1);
      border-radius:6px;padding:7px 13px;color:#718096;font-size:11px;pointer-events:none}}
#eqlab{{position:fixed;bottom:52px;left:12px;background:rgba(43,108,176,.85);border-radius:6px;
        padding:5px 12px;color:#fff;font-size:12.5px;font-weight:700;pointer-events:none}}
#sc_card{{display:none;position:fixed;bottom:85px;left:12px;background:rgba(10,15,25,.94);
          border:1px solid #38a169;border-radius:8px;padding:10px 14px;color:#e2e8f0;font-size:12px;
          z-index:10;max-width:340px;box-shadow:0 8px 24px rgba(0,0,0,.7);backdrop-filter:blur(8px)}}
#sc_title{{font-weight:700;color:#4ade80;font-size:13px;margin-bottom:3px}}
#sc_flow{{font-weight:700;color:#fff;font-size:13.5px;margin-bottom:4px}}
#sc_details{{font-size:11.5px;color:#cbd5e1;line-height:1.45}}
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
  <span><span class="dot" style="background:#2e7d32"></span>Biomass/Slurry</span>
  <span><span class="dot" style="background:#0288d1"></span>Process Water</span>
  <span><span class="dot" style="background:#00acc1"></span>Hydrolysate</span>
  <span><span class="dot" style="background:#3949ab"></span>Broth/Beer</span>
  <span><span class="dot" style="background:#ea580c"></span>Steam/Heat</span>
  <span><span class="dot" style="background:#8b5cf6"></span>H₂SO₄ Acid</span>
  <span><span class="dot" style="background:#eab308"></span>Fuel Ethanol &gt;99%</span>
  <span><span class="dot" style="background:#78350f"></span>Residue Cake</span>
</div>
<div id="tip">🖱 Rotate: left-drag · Pan: right-drag · Zoom: scroll · Click pipe for stream info</div>
<div id="eqlab">Cutaway: {'ON' if cutaway else 'OFF'}</div>
<div id="sc_card">
  <div id="sc_title">STREAM DATA</div>
  <div id="sc_flow"></div>
  <div id="sc_details"></div>
</div>

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
// Cutaway angles: Generates 270 deg of cylinder, leaving a 90 deg front-right window
const CW = Math.PI * 0.5;  // cutaway phi start (opens directly toward isometric/front view)
const CL = Math.PI * 1.5;  // 270 deg arc leaves front viewing quadrant open
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
// 5. R-101  HIGH-PRESSURE INDUSTRIAL PRETREATMENT REACTOR (REFERENCE MODEL)
//    ASME VIII CSTR, steam jacket, dished heads, 28-stud girth flange,
//    skirt with gussets & anchor bolts, lantern stool, API 682 seal & pot,
//    motor with cooling fins, stationary wall baffles, rotating PBT & anchor
// ══════════════════════════════════════════════════════════════════════════
function buildR101(ox,oz){{
  const g = new THREE.Group(); g.name = 'R-101'; g.position.set(ox, 0, oz);
  const col = selMat('R-101', M.R101col);
  const shellMat = cylMat('R-101', M.R101col);

  const R = 1.9;        // vessel radius (m)
  const H = 4.2;        // straight shell height (m)
  const skirtH = 1.5;   // structural support skirt height (m)
  const padH = 0.3;     // reinforced concrete foundation height (m)

  const base = padH + skirtH;   // lower head tangent line (y = 1.8m)
  const shY  = base + H/2;      // vessel centerline (y = 3.9m)
  const topY = base + H;        // upper body flange baseline (y = 6.0m)

  const [ps, pl] = phi(true);   // cutaway phi start & length

  // ── 1. REINFORCED CONCRETE FOUNDATION PAD ──
  pad(g, 5.8, 5.8, padH);
  // Grout chamfer bevel ring
  add(g, cyl(2.2, 0.06, 32), M.cs, 0, padH + 0.03, 0);

  // ── 2. CYLINDRICAL SUPPORT SKIRT WITH BASE RING & GUSSETS ──
  const rSkirt = R * 0.84; // 1.60m
  // Base flange ring (annular plate)
  add(g, cyl(rSkirt + 0.22, 0.08, 36), M.cs, 0, padH + 0.04, 0);

  // Support skirt rolled shell (open front in cutaway to view bottom discharge assembly)
  const skirtGeo = new THREE.CylinderGeometry(rSkirt, rSkirt, skirtH, 36, 1, true, ps, pl);
  const skirtMesh = new THREE.Mesh(skirtGeo, M.cs);
  skirtMesh.position.set(0, padH + skirtH/2, 0);
  skirtMesh.castShadow = true;
  g.add(skirtMesh);

  // 12 Skirt Base Radial Gusset Plates & Anchor Stud Assemblies
  for(let i = 0; i < 12; i++){{
    const a = i * Math.PI * 2 / 12;
    const gx = Math.cos(a) * (rSkirt + 0.08);
    const gz = Math.sin(a) * (rSkirt + 0.08);
    // Triangular gusset plate
    add(g, box(0.04, 0.40, 0.18), M.cs, gx, padH + 0.20, gz, 0, -a, 0);
    // Anchor bolt stud + double hex nut
    const ba = a + Math.PI / 12;
    const bx = Math.cos(ba) * (rSkirt + 0.14);
    const bz = Math.sin(ba) * (rSkirt + 0.14);
    add(g, cyl(0.026, 0.28, 8), M.ss316, bx, padH + 0.14, bz);
    add(g, cyl(0.048, 0.07, 6), M.cs, bx, padH + 0.24, bz); // hex nut
  }}

  // Skirt Access Manhole & Collar Ring (at angle 35 deg)
  const mAng = Math.PI * 0.20;
  const smX = Math.cos(mAng) * rSkirt;
  const smZ = Math.sin(mAng) * rSkirt;
  add(g, cyl(0.32, 0.22, 20), M.cs, smX, padH + skirtH * 0.52, smZ, Math.PI/2, 0, -mAng);
  add(g, torus(0.33, 0.035, 8, 20), M.cs, smX, padH + skirtH * 0.52, smZ, 0, mAng, 0);
  // Grounding earth boss lug
  add(g, box(0.08, 0.08, 0.06), M.copper, -(rSkirt + 0.04), padH + 0.12, 0);
  add(g, cyl(0.015, 0.35, 8), M.copper, -(rSkirt + 0.06), padH + 0.08, 0);

  // ── 3. ASME 2:1 ELLIPSOIDAL BOTTOM HEAD ──
  const botHeadGeo = sphere(R, ps, pl, Math.PI/2, Math.PI/2, 36);
  const botHead = new THREE.Mesh(botHeadGeo, shellMat);
  botHead.scale.set(1, 0.50, 1);
  botHead.position.set(0, base, 0);
  botHead.castShadow = true;
  g.add(botHead);
  // Tangent weld seam circumferential band
  add(g, cyl(R + 0.02, 0.06, 36), M.cs, 0, base, 0);

  // ── 4. MAIN CYLINDRICAL PRESSURE VESSEL SHELL ──
  const shellGeo = new THREE.CylinderGeometry(R, R, H, 36, 1, true, ps, pl);
  const shell = new THREE.Mesh(shellGeo, shellMat);
  shell.position.set(0, shY, 0);
  shell.castShadow = true;
  g.add(shell);

  // Realistic inner shell wall lining & machined cutaway seam lips
  if(isCut){{
    const inShell = new THREE.Mesh(
      new THREE.CylinderGeometry(R - 0.04, R - 0.04, H, 36, 1, true, ps, pl),
      M.ssBrushed
    );
    inShell.position.set(0, shY, 0);
    g.add(inShell);
    // Machined wall thickness seam edges along cutaway angles CW and CL
    for(const cAng of [CW, CL]){{
      const ex = Math.cos(cAng) * (R - 0.02);
      const ez = -Math.sin(cAng) * (R - 0.02);
      add(g, box(0.04, H, 0.04), M.ss316, ex, shY, ez, 0, cAng, 0);
    }}
  }}

  // ── 5. EXTERNAL STEAM HEATING JACKET & SPIRAL BAFFLING ──
  const jH = H * 0.70;        // 2.94m jacket height
  const jR = R + 0.15;        // 2.05m jacket outer radius
  const jacketMat = isCut ? M.glass : M.insul;
  const jacket = new THREE.Mesh(
    new THREE.CylinderGeometry(jR, jR, jH, 36, 1, true, ps, pl),
    jacketMat
  );
  jacket.position.set(0, base + jH/2, 0);
  jacket.castShadow = true;
  g.add(jacket);

  // Jacket top closure ring & bottom weld band
  add(g, cyl(jR + 0.03, 0.08, 36), M.cs, 0, base + jH, 0);
  add(g, cyl(jR + 0.02, 0.08, 36), M.cs, 0, base + 0.04, 0);

  // External vacuum / stiffener channel rings on jacket body
  add(g, cyl(jR + 0.04, 0.09, 36), M.cs, 0, base + jH * 0.36, 0);
  add(g, cyl(jR + 0.04, 0.09, 36), M.cs, 0, base + jH * 0.72, 0);

  // Internal spiral steam circulation guide baffles (revealed in cutaway)
  if(isCut){{
    for(let k = 1; k <= 5; k++){{
      const ringY = base + jH * (k / 6);
      const sBfl = new THREE.Mesh(
        new THREE.CylinderGeometry(R + 0.07, R + 0.07, 0.05, 32, 1, true, ps, pl),
        M.copper
      );
      sBfl.position.set(0, ringY, 0);
      g.add(sBfl);
    }}
  }}

  // Jacket Steam Supply Nozzle & Cast Iron Isolation Valve (Upper Section)
  const stmY = base + jH * 0.82;
  nozzle(g, 0.11, 0.44, jR, stmY, 0, 'x');
  // Steam valve body, bonnet, and red handwheel
  add(g, box(0.24, 0.24, 0.20), M.red, jR + 0.32, stmY, 0);
  add(g, cyl(0.06, 0.18, 10), M.cs, jR + 0.32, stmY + 0.18, 0);
  add(g, torus(0.14, 0.022, 8, 16), M.red, jR + 0.32, stmY + 0.28, 0, Math.PI/2, 0, 0);

  // Jacket Condensate Return Nozzle & Steam Trap Manifold (Lower Section)
  const cndY = base + jH * 0.18;
  nozzle(g, 0.09, 0.44, jR, cndY, 0, 'x');
  add(g, box(0.20, 0.20, 0.18), M.blue, jR + 0.32, cndY, 0);
  add(g, cyl(0.05, 0.15, 10), M.cs, jR + 0.32, cndY - 0.14, 0);

  // ── 6. ASME BODY GIRTH FLANGE WITH 28 STUD BOLTS & GASKET ──
  const fY = topY + 0.07;
  // Vessel shell flange ring
  add(g, cyl(R + 0.16, 0.12, 36), M.cs, 0, fY, 0);
  // Mating top head flange ring
  add(g, cyl(R + 0.16, 0.12, 36), M.cs, 0, fY + 0.14, 0);
  // Intermediate spiral-wound metallic gasket
  add(g, cyl(R + 0.06, 0.02, 36), M.copper, 0, fY + 0.07, 0);

  // 28 High-tensile stud bolts with double hex nuts
  const bR = R + 0.09;
  for(let b = 0; b < 28; b++){{
    const a = b * Math.PI * 2 / 28;
    const bx = Math.cos(a) * bR;
    const bz = Math.sin(a) * bR;
    add(g, cyl(0.030, 0.34, 8), M.ss316, bx, fY + 0.07, bz);
    add(g, cyl(0.052, 0.065, 6), M.cs, bx, fY + 0.22, bz); // top nut
    add(g, cyl(0.052, 0.065, 6), M.cs, bx, fY - 0.08, bz); // bottom nut
  }}

  // ── 7. ASME 2:1 ELLIPSOIDAL TOP DISHED HEAD ──
  const topHeadGeo = sphere(R, ps, pl, 0, Math.PI/2, 36);
  const topHead = new THREE.Mesh(topHeadGeo, shellMat);
  topHead.scale.set(1, 0.50, 1);
  topHead.position.set(0, fY + 0.18, 0);
  topHead.castShadow = true;
  g.add(topHead);

  const headApexY = fY + 0.18 + R * 0.50; // top head apex (y ~ 7.15m)

  // Heavy Rigging / Crane Lifting Lugs (at 90 deg and 270 deg on top head)
  for(const sign of [-1, 1]){{
    const lugZ = sign * (R * 0.72);
    add(g, box(0.08, 0.44, 0.32), M.cs, 0, headApexY - 0.15, lugZ);
    add(g, torus(0.08, 0.025, 8, 16), M.ss316, 0, headApexY + 0.05, lugZ, 0, Math.PI/2, 0);
  }}

  // ── 8. PROCESS NOZZLES, MANWAY & INSTRUMENTATION ──

  // Feed Slurry Inlet Nozzle (receiving pipe from T-102 at y = 3.8m)
  const inY = 3.8;
  const inX = -(R + 0.15);
  // Wall reinforcing pad plate
  add(g, cyl(0.28, 0.04, 20), M.cs, inX + 0.02, inY, 0, 0, 0, Math.PI/2);
  nozzle(g, 0.14, 0.45, inX, inY, 0, '-x');
  // Actuated feed isolation valve
  add(g, box(0.28, 0.30, 0.26), M.red, inX - 0.32, inY, 0);
  add(g, cyl(0.18, 0.22, 16), M.yellow, inX - 0.32, inY + 0.24, 0); // actuator dome

  // Bottom Slurry Discharge & Emergency Blowdown (connecting to F-101 pipe at y = 1.4m)
  const botDishLowest = base - R * 0.50; // ~0.85m
  // Center drop nozzle through skirt
  add(g, cyl(0.15, 0.60, 16), M.ss316, 0, botDishLowest - 0.25, 0);
  // Bottom-ram flush discharge valve body at y = 1.4m
  add(g, box(0.38, 0.42, 0.38), M.red, 0, 1.4, 0);
  add(g, cyl(0.12, 0.55, 16), M.cs, 0.35, 1.4, 0, 0, 0, Math.PI/2); // spool leading to outlet pipe
  add(g, torus(0.16, 0.025, 8, 16), M.cs, -0.28, 1.4, 0, 0, Math.PI/2, 0); // manual handwheel

  // Top Manway DN500 (20") with Swivel Davit Arm (mounted on top head at 32 deg)
  const manAng = Math.PI * 0.18;
  const manR = R * 0.55;
  const mwX = Math.cos(manAng) * manR;
  const mwZ = Math.sin(manAng) * manR;
  const mwY = headApexY - 0.22;
  // Manway flanged neck
  add(g, cyl(0.32, 0.38, 24), M.ss316, mwX, mwY + 0.19, mwZ);
  add(g, cyl(0.44, 0.10, 24), M.cs, mwX, mwY + 0.38, mwZ);    // neck flange
  add(g, cyl(0.44, 0.08, 24), M.ss316, mwX, mwY + 0.46, mwZ); // blind cover
  // 16 Manway cover bolts
  for(let mb = 0; mb < 16; mb++){{
    const mba = mb * Math.PI * 2 / 16;
    add(g, cyl(0.024, 0.12, 6), M.cs, mwX + Math.cos(mba) * 0.38, mwY + 0.47, mwZ + Math.sin(mba) * 0.38);
  }}
  // Swivel Davit hinge post and arm
  add(g, cyl(0.045, 0.65, 12), M.cs, mwX + 0.38, mwY + 0.32, mwZ + 0.15);
  add(g, box(0.36, 0.06, 0.06), M.cs, mwX + 0.22, mwY + 0.62, mwZ + 0.08);
  // Sight glass illumination port
  add(g, cyl(0.12, 0.10, 16), M.glass, mwX, mwY + 0.52, mwZ);

  // Safety Relief Valve (SRV) Assembly with Rupture Disc
  const srvX = -R * 0.42;
  const srvZ = -R * 0.40;
  const srvBaseY = headApexY - 0.18;
  nozzle(g, 0.09, 0.35, srvX, srvBaseY, srvZ, 'y');
  // Rupture disc companion flanges
  add(g, cyl(0.18, 0.07, 16), M.copper, srvX, srvBaseY + 0.38, srvZ);
  // Angle safety valve body & bonnet
  add(g, box(0.24, 0.26, 0.22), M.red, srvX, srvBaseY + 0.54, srvZ);
  add(g, cyl(0.11, 0.52, 16), M.cs, srvX, srvBaseY + 0.90, srvZ); // spring bonnet
  add(g, box(0.03, 0.24, 0.08), M.cs, srvX + 0.08, srvBaseY + 1.05, srvZ); // test lever
  add(g, cyl(0.08, 0.45, 12), M.ss316, srvX + 0.24, srvBaseY + 0.54, srvZ, 0, 0, Math.PI/2); // vent discharge

  // 3-Tier Side Instrument Thermowell Array with Weatherproof Transmitters
  for(const twY of [base + 0.85, base + 2.10, base + 3.35]){{
    nozzle(g, 0.07, 0.38, -(R + 0.15), twY, 0, '-x');
    // Transmitter enclosure (blue NEMA 4X / EEx d body)
    add(g, box(0.16, 0.20, 0.16), M.blue, -(R + 0.52), twY, 0);
    // Local LCD face
    add(g, cyl(0.065, 0.02, 16), M.cs, -(R + 0.61), twY, 0, 0, 0, Math.PI/2);
    // Stainless conduit line
    add(g, cyl(0.018, 0.28, 8), M.ss316, -(R + 0.52), twY - 0.20, 0);
  }}

  // ── 9. TOP DRIVE MOUNTING STOOL, MECHANICAL SEAL & GEARMOTOR ──

  // Cast Steel Lantern Stool / Mounting Pedestal (open inspection windows)
  const stoolBaseY = headApexY;
  const stoolH = 0.85;
  add(g, cyl(0.68, 0.09, 24), M.cs, 0, stoolBaseY + 0.045, 0); // bottom flange
  add(g, cyl(0.68, 0.09, 24), M.cs, 0, stoolBaseY + stoolH - 0.045, 0); // top deck flange
  // 4 Structural Pedestal Legs
  for(let li = 0; li < 4; li++){{
    const la = li * Math.PI / 2 + Math.PI / 4;
    const lx = Math.cos(la) * 0.52;
    const lz = Math.sin(la) * 0.52;
    add(g, box(0.12, stoolH - 0.09, 0.16), M.cs, lx, stoolBaseY + stoolH/2, lz, 0, -la, 0);
  }}

  // Double Cartridge Mechanical Seal Housing (visible inside stool windows)
  add(g, cyl(0.28, 0.44, 20), M.ssBrushed, 0, stoolBaseY + 0.26, 0);
  // Rigid split muff coupling
  add(g, cyl(0.19, 0.22, 16), M.ss316, 0, stoolBaseY + 0.60, 0);

  // API Plan 53A Thermosyphon Barrier Fluid Reservoir Pot & Tubing
  const potX = R * 0.52;
  const potZ = -R * 0.32;
  const potY = stoolBaseY + 0.55;
  add(g, cyl(0.18, 0.78, 16), M.ssBrushed, potX, potY, potZ);
  add(g, cyl(0.045, 0.42, 8), M.glass, potX + 0.16, potY, potZ); // sight level gauge
  add(g, cyl(0.07, 0.04, 16), M.cs, potX, potY + 0.41, potZ);    // pressure gauge
  // Stainless circulation tubing connecting pot to seal
  add(g, cyl(0.016, 0.65, 8), M.ss316, potX * 0.5, potY - 0.20, potZ * 0.5, 0, 0, Math.PI/4);

  // Industrial Heavy Ribbed Gearbox Reducer
  const gbY = stoolBaseY + stoolH;
  const gbH = 0.65;
  add(g, box(0.96, gbH, 0.96), M.ci, 0, gbY + gbH/2, 0);
  // Gearbox structural cooling ribs
  for(let ri of [-0.38, 0, 0.38]){{
    add(g, box(0.04, gbH * 0.9, 1.02), M.cs, ri, gbY + gbH/2, 0);
    add(g, box(1.02, gbH * 0.9, 0.04), M.cs, 0, gbY + gbH/2, ri);
  }}
  // Oil level sight glass & air breather plug
  add(g, cyl(0.06, 0.04, 12), M.copper, 0.49, gbY + 0.20, 0, 0, 0, Math.PI/2);
  add(g, cyl(0.05, 0.12, 10), M.yellow, 0, gbY + gbH + 0.06, 0.35);

  // TEFC High-Efficiency Induction Drive Motor
  const motY = gbY + gbH;
  const motH = 1.35;
  const motR = 0.42;
  // Stator body
  add(g, cyl(motR, motH, 24), M.blue, 0, motY + motH/2, 0);
  // 12 Longitudinal cooling fins around motor perimeter
  for(let fi = 0; fi < 12; fi++){{
    const fa = fi * Math.PI * 2 / 12;
    const fx = Math.cos(fa) * (motR + 0.035);
    const fz = Math.sin(fa) * (motR + 0.035);
    add(g, box(0.025, motH * 0.88, 0.07), M.blue, fx, motY + motH/2, fz, 0, -fa, 0);
  }}
  // Top fan cowl / shroud
  add(g, cyl(motR + 0.02, 0.26, 24), M.cs, 0, motY + motH + 0.13, 0);
  // Terminal conduit junction box
  add(g, box(0.24, 0.30, 0.22), M.yellow, motR + 0.11, motY + motH * 0.52, 0);
  add(g, cyl(0.04, 0.12, 8), M.cs, motR + 0.24, motY + motH * 0.52, 0, 0, 0, Math.PI/2);

  // ── 10. STATIONARY VESSEL INTERNALS (NEVER ROTATING) ──
  // 4 Vertical Anti-Vortex Wall Baffles with Standoff Brackets
  const bflW = 0.28;
  const bflH = H * 0.82;
  for(let bi = 0; bi < 4; bi++){{
    const ba = bi * Math.PI / 2 + Math.PI / 4;
    const bx = Math.cos(ba) * (R - 0.05);
    const bz = Math.sin(ba) * (R - 0.05);
    // Baffle plate
    add(g, box(bflW, bflH, 0.035), M.ssBrushed, bx, shY, bz, 0, -ba, 0);
    // Standoff support lugs
    for(const ly of [shY - H * 0.32, shY, shY + H * 0.32]){{
      const sx = Math.cos(ba) * (R - 0.025);
      const sz = Math.sin(ba) * (R - 0.025);
      add(g, box(0.05, 0.05, 0.05), M.ss316, sx, ly, sz, 0, -ba, 0);
    }}
  }}

  // Internal Circular Toroidal Steam Sparger Ring (in bottom dished head)
  const spargerY = base - R * 0.22;
  add(g, torus(R * 0.65, 0.045, 12, 32), M.ss316, 0, spargerY, 0, Math.PI/2, 0, 0);
  // Vertical steam feed downpipe to sparger
  add(g, cyl(0.045, 1.2, 12), M.ss316, R * 0.65, spargerY + 0.60, 0);

  // Internal Thermowell Deep Protection Sheath
  add(g, cyl(0.035, H * 0.72, 12), M.ss316, -R * 0.35, shY, 0);

  // ── 11. ROTATING AGITATOR ASSEMBLY (ANIMATION GROUP) ──
  const internalGrp = new THREE.Group();
  internalGrp.position.set(0, shY, 0);

  // Solid Central Stainless Drive Shaft
  const shaftTotalH = H + 1.2;
  add(internalGrp, cyl(0.078, shaftTotalH, 20), M.ss316, 0, 0.2, 0);

  // Upper Impeller: 4-Blade 45-deg Pitched-Blade Turbine (PBT)
  const pbtHubY = H * 0.22;
  add(internalGrp, cyl(0.20, 0.18, 16), M.ss316, 0, pbtHubY, 0); // clamp hub
  for(let pi = 0; pi < 4; pi++){{
    const pa = pi * Math.PI / 2;
    add(internalGrp, box(0.68, 0.18, 0.025), M.ss316,
      Math.cos(pa) * 0.44, pbtHubY, Math.sin(pa) * 0.44,
      Math.PI / 4, -pa, 0); // 45 deg pitched hydrofoil blade
  }}

  // Lower Impeller: High-Viscosity Contoured Anchor Sweep with PTFE Wall Scrapers
  const ancHubY = -H * 0.42;
  add(internalGrp, cyl(0.24, 0.22, 16), M.ss316, 0, ancHubY, 0); // lower hub
  // Heavy horizontal structural cross-beam
  add(internalGrp, box(R * 1.76, 0.14, 0.15), M.ss316, 0, ancHubY, 0);
  // Intermediate stabilizing cross-brace
  add(internalGrp, box(R * 1.76, 0.09, 0.12), M.ss316, 0, -H * 0.08, 0);

  // Two Vertical Wall Sweep Arms (clearance R - 0.13m)
  const armR = R - 0.13;
  const armH = H * 0.68;
  add(internalGrp, box(0.12, armH, 0.15), M.ss316, -armR, -H * 0.08, 0);
  add(internalGrp, box(0.12, armH, 0.15), M.ss316,  armR, -H * 0.08, 0);

  // Bottom Contoured Anchor Sweep (following ellipsoidal bottom head curve)
  add(internalGrp, box(0.45, 0.12, 0.15), M.ss316, -armR * 0.72, ancHubY - 0.16, 0, 0, 0, Math.PI / 6);
  add(internalGrp, box(0.45, 0.12, 0.15), M.ss316,  armR * 0.72, ancHubY - 0.16, 0, 0, 0, -Math.PI / 6);

  // 6 Replaceable PTFE Wall Wiper Blocks (simulating scrapers on arm edges)
  for(const wy of [-H * 0.35, -H * 0.08, H * 0.16]){{
    // Left scrapers
    add(internalGrp, box(0.12, 0.24, 0.10), M.copper, -(armR + 0.05), wy, 0);
    // Right scrapers
    add(internalGrp, box(0.12, 0.24, 0.10), M.copper,  (armR + 0.05), wy, 0);
  }}

  g.add(internalGrp);

  // Smooth rotation animation for agitator assembly
  animFns.push(()=>{{ internalGrp.rotation.y += 0.032; }});

  plantGrp.add(g);
  eqObjs['R-101'] = g;
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

// ─── PROCESS PIPING & MASS BALANCE STREAMS ───────────────────────────────
const streamMeta = {stream_data_json};
const activeStreamId = {active_stream_js};

const pipeDefs=[
  {{ id:'S-01', name:'Raw Feedstock', src:'Feed', tgt:'T-101', col:0x2e7d32, r:0.16, pts:[[-36,2.5,0],[-30,2.5,0]] }},
  {{ id:'S-W1', name:'Washing Water Inflow', src:'Water', tgt:'T-101', col:0x0288d1, r:0.11, pts:[[-30,6.2,0],[-30,4.2,0]] }},
  {{ id:'S-W2', name:'Wash Effluent Wastewater', src:'T-101', tgt:'Waste', col:0x64748b, r:0.12, pts:[[-30,0.4,0],[-30,0.4,-6]] }},
  {{ id:'S-02', name:'Washed Biomass to Dryer', src:'T-101', tgt:'D-101', col:0x2e7d32, r:0.16, pts:[[-30,2.5,0],[-24,2.5,0]] }},
  {{ id:'S-V1', name:'Dryer Evaporated Vapour', src:'D-101', tgt:'Exhaust', col:0x94a3b8, r:0.12, pts:[[-18,5.5,0],[-18,8.0,0],[-18,8.0,-4]] }},
  {{ id:'S-03', name:'Dried Biomass (10% Moisture)', src:'D-101', tgt:'M-101', col:0xb45309, r:0.16, pts:[[-15.5,2.5,0],[-11,2.5,0]] }},
  {{ id:'S-04', name:'Milled Biomass Powder', src:'M-101', tgt:'T-102', col:0x334155, r:0.14, pts:[[-11,1.5,0],[-7.5,1.5,0],[-7.5,3.5,0],[-3,3.5,0]] }},
  {{ id:'S-W3', name:'Slurry Dilution Water', src:'Water', tgt:'T-102', col:0x0288d1, r:0.10, pts:[[-3,5,0],[-3,6,0],[-3,6,-2.5]] }},
  {{ id:'S-A1', name:'Dilute H2SO4 Catalyst', src:'Acid', tgt:'T-102', col:0x8b5cf6, r:0.08, pts:[[-1.5,5,-2.5],[-3,5,0]] }},
  {{ id:'S-05', name:'Acidic Feedstock Slurry', src:'T-102', tgt:'R-101', col:0x0284c7, r:0.14, pts:[[-3,2,0],[0.5,2,0],[0.5,3.8,0],[5,3.8,0]] }},
  {{ id:'S-H2', name:'High-Pressure Reactor Steam', src:'Boiler', tgt:'R-101', col:0xea580c, r:0.09, pts:[[5,8,0],[5,8.5,0],[3.5,8.5,0]] }},
  {{ id:'S-H2C', name:'Jacket Steam Condensate', src:'R-101', tgt:'Condensate', col:0x0288d1, r:0.09, pts:[[5,2.2,0],[5,2.2,-4],[2,2.2,-4]] }},
  {{ id:'S-06', name:'Pretreated Reaction Slurry', src:'R-101', tgt:'F-101', col:0xb91c1c, r:0.15, pts:[[5,1.4,0],[9.4,1.4,0]] }},
  {{ id:'S-07', name:'Solid Filter Press Cake', src:'F-101', tgt:'Residue', col:0x78350f, r:0.15, pts:[[13,0.5,0],[13,0.5,-6]] }},
  {{ id:'S-08', name:'Clarified Hydrolysate', src:'F-101', tgt:'E-101', col:0x00acc1, r:0.14, pts:[[15.6,2.2,0],[19.5,2.2,0],[19.5,2.2,18],[15.5,2.2,18]] }},
  {{ id:'S-G1', name:'Fermentation CO2 Off-Gas', src:'E-101', tgt:'Vent', col:0x64748b, r:0.10, pts:[[13,7.5,18],[13,10.0,18],[10,10.0,18]] }},
  {{ id:'S-09', name:'Fermentation Broth (Beer)', src:'E-101', tgt:'S-101', col:0x16a34a, r:0.14, pts:[[10.8,2.2,18],[3,2.2,18]] }},
  {{ id:'S-11', name:'Yeast & Cell Biomass', src:'S-101', tgt:'Feedstock', col:0x78350f, r:0.12, pts:[[3,0.4,18],[3,0.4,23]] }},
  {{ id:'S-10', name:'Clarified Beer Broth', src:'S-101', tgt:'C-101', col:0x0f766e, r:0.13, pts:[[3,2.5,18],[-8,2.5,18],[-8,5.5,18]] }},
  {{ id:'S-13', name:'Stillage Bottoms Effluent', src:'C-101', tgt:'Waste', col:0x64748b, r:0.14, pts:[[-8,0.5,18],[-8,0.5,23]] }},
  {{ id:'S-12', name:'Azeotropic Ethanol Vapour', src:'C-101', tgt:'V-101', col:0xf59e0b, r:0.15, pts:[[-8,13,18],[-13,13,18],[-13,5,18],[-19,5,18]] }},
  {{ id:'S-14', name:'Fuel Ethanol Product (>99%)', src:'V-101', tgt:'Storage', col:0xeab308, r:0.13, pts:[[-19,2.5,18],[-26,2.5,18]] }},
];

const particles=[];
const pipeMeshes=[];

pipeDefs.forEach(pd=>{{
  const v3pts=pd.pts.map(p=>new THREE.Vector3(...p));
  const curve=v3pts.length===2
    ? new THREE.LineCurve3(v3pts[0],v3pts[1])
    : new THREE.CatmullRomCurve3(v3pts,false,'catmullrom',0.1);

  const isSelInlet = (pd.tgt === selId);
  const isSelOutlet = (pd.src === selId);
  const isStreamActive = (pd.id === activeStreamId);

  let emCol = 0x000000;
  let emInt = 0.0;
  if(isStreamActive){{
    emCol = 0x22c55e; emInt = 0.95;
  }}else if(isSelInlet){{
    emCol = 0x00e5ff; emInt = 0.80; // Glowing Cyan for Inlets
  }}else if(isSelOutlet){{
    emCol = 0xffaa00; emInt = 0.80; // Glowing Amber for Outlets
  }}

  const radMult = isStreamActive ? 1.35 : ((isSelInlet || isSelOutlet) ? 1.20 : 1.0);
  const tubMat = new THREE.MeshStandardMaterial({{
    color: pd.col,
    emissive: emCol,
    emissiveIntensity: emInt,
    metalness: 0.72,
    roughness: 0.30,
    side: THREE.DoubleSide
  }});

  const tube = new THREE.Mesh(new THREE.TubeGeometry(curve, 28, pd.r * radMult, 12, false), tubMat);
  tube.castShadow = true;
  tube.userData = {{ streamId: pd.id }};
  plantGrp.add(tube);
  pipeMeshes.push(tube);

  // Flow direction arrows (small cones oriented tangentially along the pipe curve)
  for(const tPos of [0.40, 0.75]){{
    const pt = curve.getPointAt(tPos);
    const tangent = curve.getTangentAt(tPos).normalize();
    const coneGeo = new THREE.ConeGeometry(pd.r * 1.7 * radMult, pd.r * 2.8 * radMult, 12);
    const coneMat = new THREE.MeshStandardMaterial({{
      color: (isSelInlet ? 0x00e5ff : (isSelOutlet ? 0xffaa00 : pd.col)),
      emissive: emCol,
      emissiveIntensity: emInt
    }});
    const arrow = new THREE.Mesh(coneGeo, coneMat);
    arrow.position.copy(pt);
    arrow.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), tangent);
    arrow.userData = {{ streamId: pd.id }};
    plantGrp.add(arrow);
    pipeMeshes.push(arrow);
  }}

  // Animated material flow particles
  const nP = Math.max(2, Math.floor(curve.getLength() / 2.0));
  const partSpeed = (isSelInlet || isSelOutlet || isStreamActive) ? 0.0075 : 0.004;
  for(let i=0;i<nP;i++){{
    const partCol = isStreamActive ? 0x4ade80 : (isSelInlet ? 0x67e8f9 : (isSelOutlet ? 0xfde047 : 0xffffff));
    const sp = new THREE.Mesh(
      new THREE.SphereGeometry(pd.r * 1.35 * radMult, 8, 8),
      new THREE.MeshBasicMaterial({{color: partCol}})
    );
    plantGrp.add(sp);
    particles.push({{m: sp, c: curve, t: i / nP, s: partSpeed + pd.r * 0.001}});
  }}
}});

// ─── INTERACTIVE STREAM CLICK & HUD INSPECTOR ────────────────────────────
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

function showStreamCard(sid){{
  const s = streamMeta[sid];
  if(!s) return;
  const card = document.getElementById('sc_card');
  const title = document.getElementById('sc_title');
  const flow = document.getElementById('sc_flow');
  const details = document.getElementById('sc_details');
  if(!card || !title || !flow || !details) return;

  title.innerText = 'STREAM ' + sid + ' · ' + s.name.toUpperCase();
  flow.innerText = '⚡ Mass Rate: ' + s.flow_h + ' (' + s.flow_d + ')';
  details.innerHTML = '<b>Origin:</b> ' + s.src + ' → <b>Target:</b> ' + s.tgt + '<br/>' +
    '<b>Temp:</b> ' + s.temp + ' · <b>Pressure:</b> ' + s.press + ' · <b>Phase:</b> ' + s.phase + '<br/>' +
    '<b>Moisture:</b> ' + s.moist + ' · <b>Solids:</b> ' + s.solids + '<br/>' +
    '<b>Components:</b> ' + s.comp;
  card.style.display = 'block';
}}

function onCanvasClick(e){{
  const rect = canvas.getBoundingClientRect();
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(mouse, camera);
  const hits = raycaster.intersectObjects(pipeMeshes, false);
  if(hits.length > 0 && hits[0].object.userData.streamId){{
    showStreamCard(hits[0].object.userData.streamId);
  }}
}}
canvas.addEventListener('click', onCanvasClick);
if(activeStreamId && streamMeta[activeStreamId]){{
  showStreamCard(activeStreamId);
}}

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

    # Precompute balances and streams
    all_streams = compute_all_streams(dm)
    plant_balance = compute_plant_material_balance(dm)

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#0d47a1 0%,#1565c0 50%,#0277bd 100%);
                    padding:1.2rem 1.6rem;border-radius:10px;color:white;margin-bottom:1.2rem;
                    box-shadow:0 4px 15px rgba(2,119,189,.2)">
          <div style="font-size:1.45rem;font-weight:800;letter-spacing:-.02em">🏭 3D Process Plant &amp; Digital Twin</div>
          <div style="font-size:.85rem;color:#e1f5fe;margin-top:.2rem">
            Industrial WebGL Digital Twin · Interactive Mass &amp; Material Balance · Sankey Flow Network · Educational Engineering Mode
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns([1.5, 1.8, 1.8, 1.1, 1.4])
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
        stream_choices = ["(All Streams Overview)"] + [f"{sid}: {s.name}" for sid, s in all_streams.items()]
        selected_stream_label = st.selectbox(
            "Inspect Process Stream",
            stream_choices,
            key="w_3d_stream_select",
        )
        selected_stream_id = selected_stream_label.split(":")[0] if selected_stream_label != "(All Streams Overview)" else ""
    with ctrl4:
        cutaway_toggle = st.checkbox("Internal Cutaway", value=True, key="w_3d_cutaway")
    with ctrl5:
        edu_mode = st.checkbox("🎓 Educational Mode", value=False, key="w_3d_edu_mode")

    eq_balance = compute_equipment_material_balance(selected_eq, dm)

    col_left, col_center, col_right = st.columns([1.1, 2.5, 1.4], gap="medium")

    with col_left:
        st.markdown(
            "<div style='font-size:.85rem;font-weight:700;color:#1565c0;margin-bottom:.4rem'>PROCESS EQUIPMENT ROSTER</div>",
            unsafe_allow_html=True,
        )
        for eid, meta in EQUIPMENT_METADATA.items():
            b_item = compute_equipment_material_balance(eid, dm)
            is_active = eid == selected_eq
            bg = "#e3f2fd" if is_active else "#ffffff"
            border = "2px solid #1565c0" if is_active else "1px solid #e2e8f0"
            st.markdown(
                f"""<div style="background:{bg};border:{border};border-radius:8px;padding:7px 10px;margin-bottom:6px">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                      <div style="font-weight:700;font-size:.82rem;color:#1a202c">{meta['icon']} {eid}: {meta['name']}</div>
                      <span style="background:#e8f5e9;color:#2e7d32;font-size:.68rem;font-weight:700;padding:2px 6px;border-radius:10px">✓ 100%</span>
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:2px">
                      <span style="font-size:.70rem;color:#718096">{meta['stage']}</span>
                      <span style="font-size:.70rem;font-weight:600;color:#2d3748">{b_item.total_in_kg_h:.1f} kg/h</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    with col_center:
        mode_param = "single_equipment" if "Focused" in view_mode else "full_plant"
        html = build_threejs_html(selected_eq, mode_param, cutaway_toggle, selected_stream_id, dm)
        components.html(html, height=620, scrolling=False)
        st.caption("🎮 **3D Controls:** Left-drag Rotate · Right-drag Pan · Scroll Zoom · Click any pipe for stream info · Presets top-right")

        # Interactive Stream Flow Badges for Active Equipment
        in_badges = " ".join([f"<span style='background:#e0f7fa;border:1px solid #00bcd4;color:#006064;padding:3px 7px;border-radius:4px;font-size:11px;font-weight:700;margin-right:4px'>IN: {s.id} ({s.mass_flow_kg_h:.1f} kg/h)</span>" for s in eq_balance.inflow_streams])
        out_badges = " ".join([f"<span style='background:#fff3e0;border:1px solid #ff9800;color:#e65100;padding:3px 7px;border-radius:4px;font-size:11px;font-weight:700;margin-right:4px'>OUT: {s.id} ({s.mass_flow_kg_h:.1f} kg/h)</span>" for s in eq_balance.outflow_streams])
        st.markdown(
            f"""<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;margin-top:4px">
              <div style="font-size:.78rem;font-weight:700;color:#334155;margin-bottom:4px">⚡ {selected_eq} ACTIVE STREAM CONNECTORS:</div>
              <div>{in_badges if in_badges else "<span style='font-size:11px;color:#94a3b8'>No inflows</span>"} {out_badges if out_badges else "<span style='font-size:11px;color:#94a3b8'>No outflows</span>"}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    with col_right:
        meta = EQUIPMENT_METADATA[selected_eq]
        st.markdown(f"#### {meta['icon']} {selected_eq}: {meta['name']}")
        st.caption(f"**Stage:** {meta['stage']}")

        r_tab1, r_tab2, r_tab3, r_tab4 = st.tabs(["⚖️ Mass Balance", "🌊 Stream Data", "📊 Telemetry", "⚙️ Internals"])

        with r_tab1:
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#1565c0;margin-bottom:.3rem'>EQUIPMENT MASS BALANCE:</div>", unsafe_allow_html=True)
            m_c1, m_c2 = st.columns(2)
            with m_c1:
                st.metric("Total Inflow", f"{eq_balance.total_in_kg_h:.2f} kg/h", f"{eq_balance.total_in_kg_day:,.1f} kg/d")
            with m_c2:
                st.metric("Total Outflow", f"{eq_balance.total_out_kg_h:.2f} kg/h", f"Closure: {eq_balance.closure_pct:.1f}%")

            if eq_balance.is_reactive:
                st.info(f"🔄 **Reaction Active:** Generation = {eq_balance.generation_kg_h:.2f} kg/h | Consumption = {eq_balance.consumption_kg_h:.2f} kg/h")

            st.markdown("<div style='font-size:.75rem;font-weight:700;color:#475569;margin-top:.4rem;margin-bottom:.2rem'>COMPONENT-WISE MASS DISTRIBUTION:</div>", unsafe_allow_html=True)
            if not eq_balance.components_table.empty:
                st.dataframe(eq_balance.components_table, hide_index=True, use_container_width=True)
            else:
                st.caption("No component-level breakdown available.")

        with r_tab2:
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#0288d1;margin-bottom:.3rem'>STREAM THERMODYNAMICS &amp; COMPOSITION:</div>", unsafe_allow_html=True)
            strm = all_streams.get(selected_stream_id) or (eq_balance.inflow_streams[0] if eq_balance.inflow_streams else (eq_balance.outflow_streams[0] if eq_balance.outflow_streams else None))
            if strm:
                st.markdown(f"**Stream {strm.id}: {strm.name}**")
                st.caption(f"*{strm.description}*")
                s_c1, s_c2 = st.columns(2)
                s_c1.metric("Mass Flow Rate", f"{strm.mass_flow_kg_h:.2f} kg/h", f"{strm.mass_flow_kg_day:,.1f} kg/day")
                s_c2.metric("Temperature / Press", f"{strm.temp_c:.1f} °C", f"{strm.pressure_bar:.2f} bar")

                st.markdown(f"**Phase:** `{strm.phase}` · **Moisture:** `{strm.moisture_pct:.1f}%` · **Dry Solids:** `{strm.solids_pct:.1f}%`")
                if strm.component_fractions:
                    st.markdown("<div style='font-size:.75rem;font-weight:700;color:#475569;margin-top:.4rem'>COMPONENT FRACTIONS (wt%):</div>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame([{"Component": k, "Mass Fraction (%)": f"{v:.2f}%", "Flow (kg/h)": f"{strm.components.get(k, 0):.3f}"} for k, v in strm.component_fractions.items()]), hide_index=True, use_container_width=True)
            else:
                st.info("Select a stream from the top controls or click any pipe in 3D to inspect.")

        with r_tab3:
            telem = extract_equipment_telemetry(selected_eq, dm)
            st.markdown(
                f"<div style='font-size:.75rem;font-weight:700;color:#2e7d32;margin-bottom:.4rem'>DATA BUS: {telem['status'].upper()}</div>",
                unsafe_allow_html=True,
            )
            if telem["parameters"]:
                st.dataframe(pd.DataFrame(telem["parameters"]), hide_index=True, use_container_width=True)
            else:
                st.info("No telemetry. Run simulation to stream live parameters.")

        with r_tab4:
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#4a5568'>INTERNAL MECHANICAL ASSEMBLIES:</div>", unsafe_allow_html=True)
            for item in meta["internals"]:
                st.markdown(f"• **{item}**")
            st.markdown("<div style='font-size:.78rem;font-weight:700;color:#4a5568;margin-top:.6rem'>WORKING MECHANISM:</div>", unsafe_allow_html=True)
            st.write(meta["working_principle"])

    # ══════════════════════════════════════════════════════════════════════════
    # EXPANSIVE SECTION 1: OVERALL BIOREFINERY MASS BALANCE & SANKEY DIAGRAM
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🌐 Overall Biorefinery Mass Balance & Flow Distribution")
    st.caption("Complete facility boundary balance reconciling feedstock, water consumption, chemical inputs, fuel ethanol product, and environmental effluents.")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Wet Feedstock", f"{plant_balance['total_mass_in_kg_day']:,.1f} kg/day", f"{plant_balance['total_mass_in_kg_h']:.1f} kg/h")
    with kpi2:
        st.metric("Total Water Consumption", f"{plant_balance['wastewater_total_kg_day']:,.1f} kg/day", f"{plant_balance['wastewater_total_kg_day']/1000.0:.2f} m³/day")
    with kpi3:
        st.metric("Fuel Ethanol Output", f"{plant_balance['product_ethanol_kg_day']:.2f} kg/day", f"{plant_balance['product_ethanol_l_day']:.1f} L/day (>99.5%)")
    with kpi4:
        st.metric("Facility Balance Closure", f"{plant_balance['closure_pct']:.2f}%", f"Error: {plant_balance['closure_error_pct']:+.2f}%")

    # Plotly Interactive Sankey Diagram
    sankey_data = generate_sankey_data(dm)
    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(
                    pad=18,
                    thickness=18,
                    line=dict(color="#1e293b", width=0.5),
                    label=sankey_data["nodes"],
                    color="#1e3a8a",
                ),
                link=dict(
                    source=sankey_data["sources"],
                    target=sankey_data["targets"],
                    value=sankey_data["values"],
                    customdata=sankey_data["labels"],
                    hovertemplate="%{customdata}<br>Mass Flow: %{value:.2f} kg/h<extra></extra>",
                    color="rgba(56, 161, 105, 0.45)",
                ),
            )
        ]
    )
    fig.update_layout(
        title_text="<b>Biorefinery Mass Flow Network (PFD Process Streams in kg/h)</b>",
        font=dict(size=12, family="sans-serif"),
        height=480,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Master Process Stream Summary Table
    with st.expander("📋 Master Process Stream Data Table (All 22 Streams)"):
        stream_rows = [
            {
                "Stream ID": s.id,
                "Stream Name": s.name,
                "Origin": s.source_id,
                "Destination": s.target_id,
                "Category": s.category.capitalize(),
                "Mass Flow (kg/h)": s.mass_flow_kg_h,
                "Mass Flow (kg/day)": s.mass_flow_kg_day,
                "Temp (°C)": s.temp_c,
                "Pressure (bar)": s.pressure_bar,
                "Phase": s.phase,
                "Moisture (%)": f"{s.moisture_pct:.1f}%",
                "Solids (%)": f"{s.solids_pct:.1f}%",
            }
            for s in all_streams.values()
        ]
        st.dataframe(pd.DataFrame(stream_rows), hide_index=True, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # EXPANSIVE SECTION 2: EDUCATIONAL ENGINEERING MODE
    # ══════════════════════════════════════════════════════════════════════════
    if edu_mode:
        st.markdown("---")
        st.markdown(f"### 🎓 Educational Engineering Mode — {selected_eq}: {eq_balance.name}")
        st.caption("Rigorous engineering equations, variable audit, step-by-step mathematical derivation, and assumptions ledger.")

        edu_col1, edu_col2 = st.columns([1.4, 1.6], gap="large")

        with edu_col1:
            st.markdown("#### 1. Governing Material Balance Formulation")
            st.latex(eq_balance.governing_equation)

            st.markdown(
                """
                > [!NOTE]
                > **General Material Balance Conservation Law:**
                > $$\\text{Accumulation} = \\text{Input} - \\text{Output} + \\text{Generation} - \\text{Consumption}$$
                > For continuous steady-state operations without chemical reaction, $\\text{Accumulation} = 0$, $\\text{Generation} = 0$, and $\\text{Consumption} = 0$, yielding:
                > $$\\sum \\dot{m}_{\\text{in}} = \\sum \\dot{m}_{\\text{out}}$$
                """
            )

            st.markdown("#### 2. Process Variables Audit")
            v_t1, v_t2 = st.tabs(["Known Inputs", "Calculated Outputs"])
            with v_t1:
                st.dataframe(pd.DataFrame(eq_balance.known_variables), hide_index=True, use_container_width=True)
            with v_t2:
                st.dataframe(pd.DataFrame(eq_balance.calculated_variables), hide_index=True, use_container_width=True)

        with edu_col2:
            st.markdown("#### 3. Step-by-Step Computational Derivation")
            for i, step in enumerate(eq_balance.step_by_step, 1):
                st.markdown(f"**Step {i}:** {step}")

            st.markdown("#### 4. Engineering Assumptions Ledger")
            for asm in eq_balance.assumptions:
                st.markdown(f"• *{asm}*")
