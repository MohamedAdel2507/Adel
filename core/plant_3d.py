"""3D Process Plant & Digital Twin for HYACINTH-X.

Renders an interactive, WebGL/Three.js-powered 3D industrial biorefinery plant based on the
Process Flow Diagram (PFD) for Bioethanol Production from Water Hyacinth.
Includes:
- Full 3D Plant Overview with authentic industrial equipment geometry, structural skids, and animated stream particles
- 10 detailed unit operations (T-101 to V-101) with internal cutaways, rotating impellers, trays, and heating jackets
- Real-time telemetry linkage with simulation output data (M01 to M05)
- Material stream property inspector and mechanical component breakdown
"""
from __future__ import annotations

import json
from typing import Any, Dict, Optional
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Equipment Catalog mapped to Process Flow Diagram (PFD)
EQUIPMENT_METADATA = {
    "T-101": {
        "name": "Washing Tank",
        "stage": "Feedstock Preparation",
        "description": "Continuous agitated immersion tank with spray ring manifold for dislodging silt, sand, and surface contaminants from harvested water hyacinth using process wash water.",
        "icon": "🚿",
        "internals": [
            "Heavy-Duty Agitator Drive & Gear Reducer",
            "Dual-Tier Agitator (Axial Marine Propeller + Pitch Turbine)",
            "4x Vertical Anti-Vortex Wall Baffles",
            "Radial Wash Water Spray Manifold & Nozzles",
            "Conical Silt Bottom Discharge & Knife Gate Valve",
            "Side Effluent Overflow Launder & Drainage Nozzle"
        ],
        "working_principle": "Raw harvested water hyacinth is immersed in wash water agitated by a variable-speed dual impeller. High-shear fluid motion strips extraneous detritus and sand while hydraulic pumps transfer washing effluent to biological treatment.",
        "status_color": "#2e7d32"
    },
    "D-101": {
        "name": "Biomass Dryer",
        "stage": "Feedstock Preparation",
        "description": "Industrial rotary conduction/convection dryer with thermal jacket, trunnion riding rings, drive girth gear, and internal flighting screw for dewatering biomass to ~10% moisture.",
        "icon": "🔥",
        "internals": [
            "Dual Reinforced Concrete Support Pedestals",
            "Twin Solid Forged Riding Rings (Tires) & Trunnion Rollers",
            "Central Girth Gear Ring & Side Motor Pinion Drive Skid",
            "Continuous Archimedean Internal Helical Screw Flights",
            "Stationary Feed & Discharge Breeching Hoods with Labyrinth Seals",
            "Steam Rotary Joint & Top Cyclone Vapor Exhaust Stack"
        ],
        "working_principle": "Washed water hyacinth passes through a heated rotating drum equipped with internal lifting flights. Thermal energy provides sensible heating of liquid and latent heat of vaporization (2.257 MJ/kg), evaporating free moisture prior to mechanical comminution.",
        "status_color": "#e65100"
    },
    "M-101": {
        "name": "Milling Unit",
        "stage": "Feedstock Preparation",
        "description": "Heavy-duty industrial hammer mill on structural steel skid for mechanical particle size reduction of dried biomass fibers (<2 mm) to maximize specific surface area.",
        "icon": "⚙️",
        "internals": [
            "Structural I-Beam Skid Base with Anti-Vibration Dampers",
            "Heavy-Duty TEFC Electric Motor with V-Belt Guard Enclosure",
            "Split Clamshell Upper/Lower Cast-Iron Housing with Toggle Clamps",
            "Multi-Disc Rotor Assembly with Hardened Through-Pins",
            "Free-Swinging Stepped Manganese Impact Hammers",
            "Perforated Sizing Screen Basket (180° Arc) & Hopper with Tramp Magnet"
        ],
        "working_principle": "Dried plant stalks undergo high-velocity impact with rotating hardened steel hammers. Particles exit through classified sieve screens at specified mesh sizes (<2 mm), maximizing accessibility for liquid pretreatment.",
        "status_color": "#546e7a"
    },
    "T-102": {
        "name": "Slurry Tank",
        "stage": "Pretreatment Preparation",
        "description": "Continuous stirred tank where milled biomass is blended with recycled process water and dilute sulfuric acid (H2SO4) to establish the targeted Liquid-to-Solid Ratio (LSR).",
        "icon": "🧪",
        "internals": [
            "316L Brushed Stainless Steel Vessel with Torispherical Heads",
            "Top Structural Mixer Bridge & Helical-Bevel Gear Drive",
            "Dual High-Efficiency A310-Style Axial Hydrofoil Impellers",
            "4x Full-Length Vertical Wall Baffles",
            "PTFE-Lined Sulfuric Acid (H2SO4) Dosing Dip Tube",
            "Process Water Sparger Header & Flanged Radar Level Transmitter"
        ],
        "working_principle": "Milled biomass, fresh/recycled water, and catalytic sulfuric acid are vigorously homogenized into an 8:1 liquid-to-solid pumpable slurry, ensuring uniform thermal conductivity and mass transfer in the downstream reactor.",
        "status_color": "#0288d1"
    },
    "R-101": {
        "name": "Pretreatment Reactor",
        "stage": "Thermochemical Fractionation",
        "description": "High-pressure, steam-jacketed continuous stirred reactor for dilute-acid thermochemical deconstruction of hemicellulose and lignin disruption.",
        "icon": "⚗️",
        "internals": [
            "Heavy-Wall ASME Pressure Vessel Shell with Ellipsoidal Heads",
            "External Dimpled/Half-Pipe Steam Heating Jacket & Cladding",
            "High-Torque Hydraulic Drive & Double Mechanical Seal Pot",
            "Heavy Internal Anchor Agitator with PTFE Wall Wipers",
            "Multi-Elevation Thermowell RTD Transmitter Array",
            "Safety Relief Valve (SRV), Rupture Disc, and Pneumatic Blowdown Valve"
        ],
        "working_principle": "Operates at 120°C. Dilute acid cleaves ester and glycosidic bonds within hemicellulose, hydrolyzing ~7% into soluble oligomers while retaining ~90% of insoluble cellulose-rich fibers for enzymatic conversion.",
        "status_color": "#c62828"
    },
    "F-101": {
        "name": "Filter Press",
        "stage": "Solid-Liquid Separation",
        "description": "Industrial recessed-chamber membrane filter press for separating insoluble pretreated cellulose-rich cake from the acidic liquid hydrolysate liquor.",
        "icon": "📦",
        "internals": [
            "Heavy-Duty Dual Side-Beam Steel Frame & Stationary Feed Head",
            "Massive Rear Hydraulic Clamping Cylinder & Chrome Ram",
            "Moving Follower Thrust Plate Guided on Side Bars",
            "Stack of 22 Recessed Polypropylene Chamber Plates with Handles",
            "High-Pressure Slurry Feed Manifold with Diaphragm Valve",
            "Twin Stainless Filtrate Launders & Cake Discharge Chute"
        ],
        "working_principle": "Pretreated slurry is pumped under hydraulic pressure through woven filter cloths. Liquid liquor drains into the filtrate manifold, while dewatered cellulosic cake is mechanically discharged from opening plates.",
        "status_color": "#455a64"
    },
    "E-101": {
        "name": "Bioreactor / Fermenter",
        "stage": "Enzymatic Hydrolysis & Fermentation",
        "description": "Large-scale aseptic jacketed bioconversion vessel where cellulase enzymes depolymerize glucan and yeast converts free sugars to bioethanol.",
        "icon": "🧬",
        "internals": [
            "Slender Aspect Ratio (3:1) 316L Sanitary Stainless Shell",
            "Top Sanitary Servo Drive & Sterile Double Mechanical Seal",
            "3-Tier 6-Blade Rushton Disc Turbine Impellers",
            "Internal Stainless Vertical Cooling Coil Loops",
            "Bottom Ring Aeration/Purge Sparger & Mechanical Foam Breaker",
            "Heated Sterile Vent Filter Capsule, CIP Spray Balls & Sensor Ports"
        ],
        "working_principle": "Cellulase enzymes cleave anhydroglucose rings (adding +11.1% hydration water), releasing glucose. S. cerevisiae metabolizes hexoses into ethanol and CO2 following Gay-Lussac reaction stoichiometry (0.5114 g/g yield).",
        "status_color": "#2e7d32"
    },
    "S-101": {
        "name": "Clarification Centrifuge",
        "stage": "Broth Clarification",
        "description": "Continuous disc-stack centrifuge for separating spent yeast cells and insoluble particulate solids from the dilute ethanol-bearing beer broth.",
        "icon": "🌀",
        "internals": [
            "Cast-Iron Machine Pedestal Base with Vibration Dampers",
            "Vertical High-Speed Spindle Drive Motor & Belt Transmission",
            "Precision Disc-Stack Assembly (30+ Conical Separation Plates)",
            "Centripetal Paring Disc Liquid Pump for Non-Foaming Discharge",
            "Peripheral Solid Ejection Ports & Sliding Hydraulic Piston",
            "Clarified Broth Outlet Pipe with Back-Pressure Valve & Gauge"
        ],
        "working_principle": "Generating up to 8,000 g centrifugal force, high-density yeast cell mass and insoluble lignaceous fines migrate to the bowl periphery and are intermittently ejected, yielding a clear beer broth feed for distillation.",
        "status_color": "#00838f"
    },
    "C-101": {
        "name": "Distillation Column",
        "stage": "Thermal Separation",
        "description": "Multi-stage fractional distillation column equipped with sieve trays, thermosiphon reboiler, and overhead reflux condenser to concentrate ethanol.",
        "icon": "🏛️",
        "internals": [
            "Tall Cylindrical Column Shell with Cylindrical Skirt & Anchor Ring",
            "16x Internal Perforated Sieve Trays with Downcomers and Weirs",
            "Side Horizontal Shell-and-Tube Thermosiphon Reboiler Skid",
            "Top Overhead Vapor Line & Shell-and-Tube Condenser Drum",
            "Reflux Accumulator Vessel & Canned-Motor Reflux Pump",
            "Full-Height Vertical Safety Cage Ladder & 3x Access Platforms"
        ],
        "working_principle": "Steam vaporizes volatile ethanol from the 5 vol% broth. Counter-current vapor-liquid contact enriches ethanol overhead toward the azeotrope (~92-95 wt%), while alcohol-free stillage discharges at the base.",
        "status_color": "#1565c0"
    },
    "V-101": {
        "name": "Molecular Sieve Dehydration",
        "stage": "Product Purification",
        "description": "Twin-bed pressure swing adsorption (PSA) zeolite molecular sieve system producing anhydrous fuel bioethanol (>99.5% purity).",
        "icon": "💎",
        "internals": [
            "Structural Steel Skid Base with Diamond Flooring Plate",
            "Twin Parallel Vertical Adsorption Vessels (Bed A & Bed B)",
            "Zeolite 3A Molecular Sieve Bed with Stainless Retaining Grids",
            "Automated Pneumatic Cross-Over Switching Valve Manifold (4 Valves)",
            "Inter-Bed Regeneration Gas Superheater Electric Exchanger",
            "Water Knockout Pot & Inline Duplex Micron Particulate Filters"
        ],
        "working_principle": "Azeotropic ethanol vapor passes through 3-Angstrom zeolite pores which selectively adsorb 2.8 Å water molecules while excluding 4.4 Å ethanol molecules, yielding anhydrous fuel-grade ethanol (>99.5%).",
        "status_color": "#0d47a1"
    }
}


def extract_equipment_telemetry(eq_id: str, dm: Any) -> Dict[str, Any]:
    """Extracts genuine simulation telemetry parameters for a given equipment item."""
    if not dm or not dm.completed:
        return {"status": "Awaiting Simulation Run", "parameters": []}

    r1 = dm.results.get("M01", {})
    r2 = dm.results.get("M02", {})
    r3 = dm.results.get("M03", {})
    r4 = dm.results.get("M04", {})
    r5 = dm.results.get("M05", {})
    mb = dm.derived.get("mass_balance", {})
    m3_params = dm.derived.get("m03_params", {})

    params = []

    if eq_id == "T-101":
        wash_vol = m3_params.get("washing_water_m3_day", 3.0)
        wash_power = [r[1] for r in r3.get("electric_rows", []) if "Washing" in r[0]]
        params = [
            {"Parameter": "Wet Biomass Inflow", "Value": f"{r1.get('wet_feed_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M01 Feedstock"},
            {"Parameter": "Raw Harvest Moisture", "Value": f"{r1.get('moisture_pct_wb', 0):.1f}", "Unit": "% wet basis", "Source": "M01 Feedstock"},
            {"Parameter": "Process Washing Water", "Value": f"{wash_vol:,.1f}", "Unit": "m³/day", "Source": "M03 Utilities"},
            {"Parameter": "Pump Hydraulic Head", "Value": f"{m3_params.get('washing_pump_head_m', 15.0):.1f}", "Unit": "m", "Source": "M03 Specs"},
            {"Parameter": "Washing Pump Power Demand", "Value": f"{wash_power[0] if wash_power else 0.19:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"}
        ]

    elif eq_id == "D-101":
        evap_water = r3.get("water_removed_kg_day", 0.0)
        dryer_mj = [r[1] for r in r3.get("thermal_rows", []) if "Dryer" in r[0]]
        params = [
            {"Parameter": "Water Mass Evaporated", "Value": f"{evap_water:,.1f}", "Unit": "kg/day", "Source": "M03 Mass Balance"},
            {"Parameter": "Target Biomass Moisture", "Value": f"{m3_params.get('target_moisture_pct', 10.0):.1f}", "Unit": "% wet basis", "Source": "M03 Design Spec"},
            {"Parameter": "Thermal Drying Duty", "Value": f"{dryer_mj[0] if dryer_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03 Enthalpy Balance"},
            {"Parameter": "Dryer Thermal Efficiency", "Value": f"{m3_params.get('dryer_eff_pct', 55.0):.0f}", "Unit": "%", "Source": "M03 Specification"},
            {"Parameter": "Biomass Outlet Temperature", "Value": "100.0", "Unit": "°C", "Source": "M03 Model Constant"}
        ]

    elif eq_id == "M-101":
        mill_power = [r[1] for r in r3.get("electric_rows", []) if "Mill" in r[0]]
        params = [
            {"Parameter": "Dry Biomass Throughput", "Value": f"{r1.get('dry_biomass_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M01 Output"},
            {"Parameter": "Milling Specific Energy", "Value": f"{m3_params.get('milling_kwh_per_t', 25.0):.1f}", "Unit": "kWh / tonne dry", "Source": "M03 Design Spec"},
            {"Parameter": "Milling Electrical Load", "Value": f"{mill_power[0] if mill_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "Target Screen Particle Size", "Value": "< 2.0", "Unit": "mm", "Source": "Process Design"}
        ]

    elif eq_id == "T-102":
        slurry_liq = r3.get("slurry_liquid_kg_day", 0.0)
        slurry_power = [r[1] for r in r3.get("electric_rows", []) if "Slurry" in r[0]]
        lsr = m3_params.get("pretreatment_liquid_solid_ratio", 8.0)
        params = [
            {"Parameter": "Liquid-to-Solid Ratio (LSR)", "Value": f"{lsr:.1f}:1", "Unit": "kg liq / kg dry", "Source": "M03 Configuration"},
            {"Parameter": "Process Slurry Water Added", "Value": f"{slurry_liq:,.1f}", "Unit": "kg/day", "Source": "M03 Calculation"},
            {"Parameter": "Total Homogenized Slurry", "Value": f"{slurry_liq + r1.get('dry_biomass_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "Material Balance"},
            {"Parameter": "Mixer Power Consumption", "Value": f"{slurry_power[0] if slurry_power else 8.0:.2f}", "Unit": "kWh/day", "Source": "M03 Auxiliary Input"}
        ]

    elif eq_id == "R-101":
        react_mj = [r[1] for r in r3.get("thermal_rows", []) if "Pretreatment" in r[0]]
        p_m2 = dm.derived.get("m02_params", {})
        params = [
            {"Parameter": "Cooking Temperature", "Value": f"{m3_params.get('pretreatment_temp_c', 120.0):.1f}", "Unit": "°C", "Source": "M03 Design Spec"},
            {"Parameter": "Pretreatment Thermal Duty", "Value": f"{react_mj[0] if react_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03 Sensible Heat"},
            {"Parameter": "Solid Fiber Retention", "Value": f"{p_m2.get('solid_retention', 0.90)*100:.1f}", "Unit": "%", "Source": "M02 Yield Model"},
            {"Parameter": "Solubilized Organics", "Value": f"{p_m2.get('solubilized_fraction', 0.07)*100:.1f}", "Unit": "%", "Source": "M02 Yield Model"},
            {"Parameter": "Degradation Inhibitors", "Value": f"{p_m2.get('degraded_fraction', 0.03)*100:.1f}", "Unit": "%", "Source": "M02 Furfurals"}
        ]

    elif eq_id == "F-101":
        filter_power = [r[1] for r in r3.get("electric_rows", []) if "Filter press" in r[0]]
        resid_solids = mb.get("residual_solids_kg", 0.0)
        params = [
            {"Parameter": "Insoluble Residual Solids", "Value": f"{resid_solids:,.1f}", "Unit": "kg/day", "Source": "M02/M04 Balance"},
            {"Parameter": "Wastewater Slurry Filtrate", "Value": f"{r3.get('slurry_liquid_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M03/M04 Flow"},
            {"Parameter": "Filter Press Power Demand", "Value": f"{filter_power[0] if filter_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "Separation Principle", "Value": "Recessed Membrane Pressure Filtration", "Unit": "-", "Source": "Industrial Design"}
        ]

    elif eq_id == "E-101":
        sugar_tot = r2.get("total_sugars_kg", 0.0)
        eth_crude = r2.get("ethanol_before_recovery_kg", 0.0)
        co2_gen = mb.get("co2_kg", 0.0)
        ferm_power = [r[1] for r in r3.get("electric_rows", []) if "Fermenter" in r[0]]
        params = [
            {"Parameter": "Total Monomeric Sugars Fed", "Value": f"{sugar_tot:,.1f}", "Unit": "kg/day", "Source": "M02 Hydrolysis"},
            {"Parameter": "Chemically Bound Hydrolysis Water", "Value": f"{mb.get('hydrolysis_water_kg', 0):,.2f}", "Unit": "kg/day", "Source": "Stoichiometric Gain"},
            {"Parameter": "Synthesized Crude Ethanol", "Value": f"{eth_crude:,.1f}", "Unit": "kg/day", "Source": "M02 Fermentation"},
            {"Parameter": "Fermentation Off-Gas CO₂", "Value": f"{co2_gen:,.1f}", "Unit": "kg/day", "Source": "Gay-Lussac Stoichiometry"},
            {"Parameter": "Agitator Power Load", "Value": f"{ferm_power[0] if ferm_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Power Demand"}
        ]

    elif eq_id == "S-101":
        broth_vol = r3.get("broth_volume_m3_day", 0.0)
        cent_power = [r[1] for r in r3.get("electric_rows", []) if "Centrifuge" in r[0]]
        params = [
            {"Parameter": "Fermentation Broth Throughput", "Value": f"{broth_vol:,.2f}", "Unit": "m³/day", "Source": "M03 Hydraulic Basis"},
            {"Parameter": "Broth Ethanol Concentration", "Value": f"{m3_params.get('broth_ethanol_vol_pct', 5.0):.1f}", "Unit": "vol %", "Source": "M03 Design Spec"},
            {"Parameter": "Centrifuge Electrical Load", "Value": f"{cent_power[0] if cent_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "G-Force Separation Field", "Value": "6,500 - 8,000", "Unit": "g", "Source": "Disc-Stack Specification"}
        ]

    elif eq_id == "C-101":
        dist_mj = [r[1] for r in r3.get("thermal_rows", []) if "Distillation" in r[0]]
        eth_rec = r2.get("recovered_ethanol_kg", 0.0)
        params = [
            {"Parameter": "Recovered Bioethanol (Mass)", "Value": f"{eth_rec:,.2f}", "Unit": "kg/day", "Source": "M02/M03 Output"},
            {"Parameter": "Recovered Bioethanol (Volume)", "Value": f"{r3.get('ethanol_l_day', 0):,.1f}", "Unit": "L/day", "Source": "M03 (Density 0.789)"},
            {"Parameter": "Reboiler Thermal Heating Load", "Value": f"{dist_mj[0] if dist_mj else 0:,.0f}", "Unit": "MJ/day", "Source": "M03 Steam Reboiler"},
            {"Parameter": "Column Reboiler Efficiency", "Value": f"{m3_params.get('distillation_heater_eff_pct', 85.0):.0f}", "Unit": "%", "Source": "M03 Design Spec"},
            {"Parameter": "Ethanol Recovery Efficiency", "Value": f"{r2.get('ethanol_recovery', 0.95)*100:.1f}", "Unit": "%", "Source": "M02 Separation Factor"}
        ]

    elif eq_id == "V-101":
        dehyd_mj = [r[1] for r in r3.get("thermal_rows", []) if "Dehydration" in r[0]]
        annual_l = r5.get("quantities", {}).get("ethanol_l_year", 0.0)
        params = [
            {"Parameter": "Anhydrous Fuel Ethanol (>99.5%)", "Value": f"{r3.get('ethanol_l_day', 0):,.1f}", "Unit": "L/day", "Source": "Final Product Stream"},
            {"Parameter": "Annual Plant Production", "Value": f"{annual_l:,.0f}", "Unit": "L/year", "Source": "M05 Economic Basis"},
            {"Parameter": "Dehydration Energy Intensity", "Value": f"{m3_params.get('dehydration_mj_per_l_ethanol', 1.5):.2f}", "Unit": "MJ / L ethanol", "Source": "M03 Molecular Sieve"},
            {"Parameter": "Thermal Duty", "Value": f"{dehyd_mj[0] if dehyd_mj else 0:,.1f}", "Unit": "MJ/day", "Source": "M03 Thermal Balance"}
        ]

    return {"status": "Live Simulation Linked", "parameters": params}


def build_threejs_html(selected_eq_id: str, view_mode: str = "full_plant", cutaway: bool = True) -> str:
    """Generates standalone Three.js WebGL HTML visualization with detailed industrial engineering models."""
    
    cutaway_js_bool = "true" if cutaway else "false"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>HYACINTH-X Industrial Digital Twin</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #0b0f17;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            user-select: none;
        }}
        #canvas-container {{
            width: 100vw;
            height: 100vh;
            position: absolute;
            top: 0;
            left: 0;
        }}
        #hud {{
            position: absolute;
            top: 14px;
            left: 14px;
            background: rgba(11, 15, 23, 0.88);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(88, 166, 255, 0.25);
            border-radius: 8px;
            padding: 10px 16px;
            color: #e6edf3;
            font-size: 13px;
            z-index: 100;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            pointer-events: none;
        }}
        #hud h4 {{
            margin: 0 0 4px 0;
            font-size: 14px;
            color: #58a6ff;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        #hud .badge {{
            display: inline-block;
            background: #1f6feb;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 6px;
        }}
        #camera-bar {{
            position: absolute;
            top: 14px;
            right: 14px;
            z-index: 100;
            display: flex;
            gap: 6px;
        }}
        .cam-btn {{
            background: rgba(22, 27, 34, 0.88);
            border: 1px solid rgba(255, 255, 255, 0.18);
            color: #c9d1d9;
            padding: 6px 11px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            backdrop-filter: blur(8px);
            transition: all 0.2s ease;
        }}
        .cam-btn:hover {{
            background: #1f6feb;
            color: #fff;
            border-color: #58a6ff;
        }}
        #instructions {{
            position: absolute;
            bottom: 14px;
            left: 14px;
            background: rgba(11, 15, 23, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 8px 14px;
            color: #8b949e;
            font-size: 11px;
            pointer-events: none;
        }}
        #legend {{
            position: absolute;
            bottom: 14px;
            right: 14px;
            background: rgba(11, 15, 23, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 6px;
            padding: 8px 12px;
            color: #c9d1d9;
            font-size: 11px;
            display: flex;
            gap: 12px;
            pointer-events: none;
        }}
        .dot {{
            width: 9px;
            height: 9px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
        }}
    </style>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="canvas-container"></div>
    <div id="hud">
        <h4>🏭 HYACINTH-X Biorefinery Digital Twin</h4>
        <div><span class="badge">{selected_eq_id}</span> {EQUIPMENT_METADATA.get(selected_eq_id, {}).get('name', 'Industrial Unit')} &nbsp;|&nbsp; Mode: <b>{view_mode.replace('_', ' ').title()}</b></div>
    </div>

    <div id="camera-bar">
        <button class="cam-btn" onclick="setPreset('pfd')">🗺️ PFD Layout</button>
        <button class="cam-btn" onclick="setPreset('iso')">📐 3D Isometric</button>
        <button class="cam-btn" onclick="setPreset('front')">👁️ Front Elevation</button>
        <button class="cam-btn" onclick="setPreset('top')">⬆️ Top Plan</button>
    </div>

    <div id="instructions">
        🖱️ <b>Rotate:</b> Left Drag &nbsp;|&nbsp; <b>Pan:</b> Right Drag &nbsp;|&nbsp; <b>Zoom:</b> Scroll &nbsp;|&nbsp; Cutaway: <b>{'Active' if cutaway else 'Disabled'}</b>
    </div>

    <div id="legend">
        <span><span class="dot" style="background:#2e7d32"></span>Slurry / Biomass</span>
        <span><span class="dot" style="background:#0288d1"></span>Hydrolysate / Broth</span>
        <span><span class="dot" style="background:#f57c00"></span>Steam / Heat</span>
        <span><span class="dot" style="background:#8e24aa"></span>H₂SO₄ / Catalyst</span>
        <span><span class="dot" style="background:#ffb300"></span>Fuel Ethanol (>99%)</span>
    </div>

    <script>
        const container = document.getElementById('canvas-container');
        const isCutawayGlobal = {cutaway_js_bool};
        const targetId = "{selected_eq_id}";
        const isSingleMode = ("{view_mode}" === "single_equipment");

        // Scene, Camera, Renderer
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x0a0e17);
        scene.fog = new THREE.FogExp2(0x0a0e17, 0.009);

        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: "high-performance" }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.1;
        container.appendChild(renderer.domElement);

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.maxPolarAngle = Math.PI / 2 + 0.02;

        // Lighting Architecture
        const ambientLight = new THREE.AmbientLight(0xdbeafe, 0.75);
        scene.add(ambientLight);

        const sunLight = new THREE.DirectionalLight(0xffffff, 1.15);
        sunLight.position.set(35, 55, 30);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        sunLight.shadow.camera.near = 5;
        sunLight.shadow.camera.far = 150;
        sunLight.shadow.camera.left = -50;
        sunLight.shadow.camera.right = 50;
        sunLight.shadow.camera.top = 50;
        sunLight.shadow.camera.bottom = -50;
        scene.add(sunLight);

        const rimLight = new THREE.DirectionalLight(0x60a5fa, 0.55);
        rimLight.position.set(-40, 25, -35);
        scene.add(rimLight);

        const floorBounce = new THREE.DirectionalLight(0x38bdf8, 0.25);
        floorBounce.position.set(0, -10, 0);
        scene.add(floorBounce);

        // Ground Floor System
        const floorGeo = new THREE.PlaneGeometry(120, 80);
        const floorMat = new THREE.MeshStandardMaterial({{
            color: 0x111827,
            roughness: 0.85,
            metalness: 0.15
        }});
        const floorMesh = new THREE.Mesh(floorGeo, floorMat);
        floorMesh.rotation.x = -Math.PI / 2;
        floorMesh.position.y = -0.05;
        floorMesh.receiveShadow = true;
        scene.add(floorMesh);

        // Factory Floor Grid
        const gridHelper = new THREE.GridHelper(100, 50, 0x3b82f6, 0x1f2937);
        gridHelper.position.y = -0.02;
        scene.add(gridHelper);

        // Safety Walkway Demarcation Lines
        function createWalkway(x1, z1, x2, z2) {{
            const dist = Math.hypot(x2 - x1, z2 - z1);
            const angle = Math.atan2(z2 - z1, x2 - x1);
            const lineGeo = new THREE.PlaneGeometry(dist, 0.25);
            const lineMat = new THREE.MeshBasicMaterial({{ color: 0xfacc15, depthWrite: false }});
            const lineMesh = new THREE.Mesh(lineGeo, lineMat);
            lineMesh.rotation.x = -Math.PI / 2;
            lineMesh.rotation.z = -angle;
            lineMesh.position.set((x1 + x2) / 2, 0.01, (z1 + z2) / 2);
            scene.add(lineMesh);
        }}
        createWalkway(-38, 8, 20, 8);
        createWalkway(-38, -6, 20, -6);
        createWalkway(-38, 24, 20, 24);

        // Master Materials Library (Industrial Standard PBR)
        const matSS316 = new THREE.MeshStandardMaterial({{ color: 0xd1d5db, metalness: 0.88, roughness: 0.22 }});
        const matSSBrushed = new THREE.MeshStandardMaterial({{ color: 0x9ca3af, metalness: 0.82, roughness: 0.35 }});
        const matCarbonSteel = new THREE.MeshStandardMaterial({{ color: 0x374151, metalness: 0.75, roughness: 0.45 }});
        const matCastIron = new THREE.MeshStandardMaterial({{ color: 0x1f2937, metalness: 0.6, roughness: 0.65 }});
        const matInsulation = new THREE.MeshStandardMaterial({{ color: 0xe5e7eb, metalness: 0.45, roughness: 0.4 }});
        const matCopper = new THREE.MeshStandardMaterial({{ color: 0xd97706, metalness: 0.85, roughness: 0.28 }});
        const matBronze = new THREE.MeshStandardMaterial({{ color: 0xb45309, metalness: 0.8, roughness: 0.3 }});
        const matSafetyYellow = new THREE.MeshStandardMaterial({{ color: 0xeab308, metalness: 0.2, roughness: 0.45 }});
        const matMotorBlue = new THREE.MeshStandardMaterial({{ color: 0x1d4ed8, metalness: 0.5, roughness: 0.35 }});
        const matPumpRed = new THREE.MeshStandardMaterial({{ color: 0xb91c1c, metalness: 0.55, roughness: 0.35 }});
        const matConcrete = new THREE.MeshStandardMaterial({{ color: 0x4b5563, roughness: 0.9, metalness: 0.1 }});
        const matGlass = new THREE.MeshPhysicalMaterial({{
            color: 0xe0f2fe,
            transparent: true,
            opacity: 0.35,
            roughness: 0.1,
            transmission: 0.8,
            ior: 1.5,
            depthWrite: false
        }});
        const matHighlight = new THREE.MeshStandardMaterial({{
            color: 0x10b981,
            emissive: 0x059669,
            emissiveIntensity: 0.55,
            metalness: 0.7,
            roughness: 0.2
        }});

        // Process Fluid Materials
        const matBiofluid = new THREE.MeshStandardMaterial({{ color: 0x4d7c0f, transparent: true, opacity: 0.65, roughness: 0.2 }});
        const matBrothFluid = new THREE.MeshStandardMaterial({{ color: 0xd97706, transparent: true, opacity: 0.6, roughness: 0.25 }});
        const matEthanolFluid = new THREE.MeshStandardMaterial({{ color: 0x0ea5e9, transparent: true, opacity: 0.5, roughness: 0.15 }});

        // Common Geometry Builders
        function addConcretePad(parent, w, d, h = 0.35, x = 0, z = 0) {{
            const pad = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), matConcrete);
            pad.position.set(x, h / 2, z);
            pad.receiveShadow = true;
            pad.castShadow = true;
            parent.add(pad);
            return pad;
        }}

        function addFlange(parent, r, y, thick = 0.08) {{
            const f = new THREE.Mesh(new THREE.CylinderGeometry(r * 1.15, r * 1.15, thick, 24), matCarbonSteel);
            f.position.y = y;
            f.castShadow = true;
            parent.add(f);
            return f;
        }}

        function addNozzle(parent, r, len, pos, rot) {{
            const nozzle = new THREE.Group();
            nozzle.position.copy(pos);
            if (rot) nozzle.rotation.copy(rot);
            const pipe = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 16), matSSBrushed);
            pipe.position.y = len / 2;
            pipe.castShadow = true;
            nozzle.add(pipe);
            const fl = new THREE.Mesh(new THREE.CylinderGeometry(r * 1.6, r * 1.6, 0.08, 16), matCarbonSteel);
            fl.position.y = len;
            fl.castShadow = true;
            nozzle.add(fl);
            parent.add(nozzle);
            return nozzle;
        }}

        function addMotorGearbox(parent, pos, scale = 1.0) {{
            const g = new THREE.Group();
            g.position.copy(pos);
            g.scale.set(scale, scale, scale);

            // Gearbox base
            const box = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.6, 0.7), matCastIron);
            box.position.y = 0.3;
            box.castShadow = true;
            g.add(box);

            // Motor housing
            const motor = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 1.1, 20), matMotorBlue);
            motor.position.y = 0.6 + 0.55;
            motor.castShadow = true;
            g.add(motor);

            // Fan cowl
            const cowl = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.25, 20), matCarbonSteel);
            cowl.position.y = 0.6 + 1.1 + 0.12;
            cowl.castShadow = true;
            g.add(cowl);

            // Conduit junction box
            const jbox = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.25, 0.2), matSafetyYellow);
            jbox.position.set(0.35, 0.6 + 0.55, 0);
            g.add(jbox);

            parent.add(g);
            return g;
        }}

        function addCentrifugalPump(parent, x, y, z, rotY = 0) {{
            const pGroup = new THREE.Group();
            pGroup.position.set(x, y, z);
            pGroup.rotation.y = rotY;

            // Skid
            const skid = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.15, 0.8), matCastIron);
            skid.position.y = 0.08;
            skid.castShadow = true;
            pGroup.add(skid);

            // Motor
            const mot = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.6, 16), matMotorBlue);
            mot.rotation.z = Math.PI / 2;
            mot.position.set(-0.3, 0.32, 0);
            mot.castShadow = true;
            pGroup.add(mot);

            // Pump volute casing
            const vol = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.25, 16), matPumpRed);
            vol.rotation.x = Math.PI / 2;
            vol.position.set(0.25, 0.32, 0);
            vol.castShadow = true;
            pGroup.add(vol);

            // Discharge nozzle
            const noz = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.35, 12), matCarbonSteel);
            noz.position.set(0.25, 0.55, 0);
            pGroup.add(noz);

            parent.add(pGroup);
            return pGroup;
        }}

        // Equipment Container & Animation Registry
        const plantGroup = new THREE.Group();
        scene.add(plantGroup);
        const eqObjects = {{}};
        const animators = [];

        // ══════════════════════════════════════════════════════════════════════
        // 1. T-101: INDUSTRIAL BIOMASS WASHING TANK
        // ══════════════════════════════════════════════════════════════════════
        function buildT101(x, z) {{
            const g = new THREE.Group();
            g.name = "T-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "T-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 5.0, 5.0, 0.35);

            // 4 Structural Pipe Support Legs
            for (let i = 0; i < 4; i++) {{
                const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1.6, 12), matCarbonSteel);
                const ang = (i * Math.PI) / 2 + Math.PI / 4;
                leg.position.set(Math.cos(ang) * 1.7, 0.35 + 0.8, Math.sin(ang) * 1.7);
                leg.castShadow = true;
                g.add(leg);

                // Diagonal gusset
                const gusset = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.6, 0.35), matCarbonSteel);
                gusset.position.set(Math.cos(ang) * 1.7, 0.35 + 1.2, Math.sin(ang) * 1.7);
                g.add(gusset);
            }}

            // Lower Conical Silt Hopper Bottom
            const coneMat = isSel ? matHighlight : matSS316;
            const coneGeo = new THREE.ConeGeometry(2.0, 1.4, 32, 1, true);
            const cone = new THREE.Mesh(coneGeo, coneMat);
            cone.rotation.x = Math.PI;
            cone.position.y = 0.35 + 1.6 + 0.7;
            cone.castShadow = true;
            g.add(cone);

            // Bottom Silt Drain Valve & Elbow
            const drainPipe = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 0.6, 16), matCarbonSteel);
            drainPipe.position.y = 0.35 + 1.6 - 0.2;
            g.add(drainPipe);
            const valve = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.3, 0.3), matPumpRed);
            valve.position.y = 0.35 + 1.6 - 0.35;
            g.add(valve);

            // Main Tank Cylindrical Shell (With Cutaway logic)
            const shellH = 3.6;
            const shellY = 0.35 + 1.6 + 1.4 + shellH / 2;
            const shellMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const shell = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, shellH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), shellMat);
            shell.position.y = shellY;
            shell.castShadow = true;
            g.add(shell);

            // Girth Rings
            addFlange(g, 2.0, shellY - shellH / 2);
            addFlange(g, 2.0, shellY + shellH / 2);

            // Top Structural Mixer Bridge
            const bridge = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.22, 0.6), matCarbonSteel);
            bridge.position.y = shellY + shellH / 2 + 0.11;
            bridge.castShadow = true;
            g.add(bridge);

            // Agitator Motor & Drive
            addMotorGearbox(g, new THREE.Vector3(0, shellY + shellH / 2 + 0.22, 0), 1.1);

            // Agitator Shaft & Dual-Tier Impellers
            const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.07, shellH + 1.0, 16), matCarbonSteel);
            shaft.position.y = shellY;
            g.add(shaft);

            const impellersGroup = new THREE.Group();
            impellersGroup.position.y = shellY;

            // Lower 3-Blade Marine Propeller
            for (let b = 0; b < 3; b++) {{
                const blade = new THREE.Mesh(new THREE.BoxGeometry(1.2, 0.08, 0.28), matCopper);
                blade.rotation.y = (b * Math.PI * 2) / 3;
                blade.rotation.x = 0.3;
                blade.position.y = -shellH * 0.35;
                impellersGroup.add(blade);
            }}

            // Upper 4-Blade Pitch Turbine
            for (let b = 0; b < 4; b++) {{
                const blade = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.12, 0.32), matBronze);
                blade.rotation.y = (b * Math.PI) / 2;
                blade.rotation.z = 0.25;
                blade.position.y = shellH * 0.15;
                impellersGroup.add(blade);
            }}
            g.add(impellersGroup);

            // 4 Internal Anti-Vortex Wall Baffles
            for (let i = 0; i < 4; i++) {{
                const bfl = new THREE.Mesh(new THREE.BoxGeometry(0.35, shellH * 0.85, 0.05), matCarbonSteel);
                const ang = (i * Math.PI) / 2;
                bfl.position.set(Math.cos(ang) * 1.8, shellY, Math.sin(ang) * 1.8);
                bfl.rotation.y = -ang;
                g.add(bfl);
            }}

            // Top Circular Wash Water Spray Manifold Ring & Spray Nozzles
            const sprayRing = new THREE.Mesh(new THREE.TorusGeometry(1.6, 0.06, 8, 24), matCopper);
            sprayRing.rotation.x = Math.PI / 2;
            sprayRing.position.y = shellY + shellH * 0.4;
            g.add(sprayRing);

            for (let s = 0; s < 6; s++) {{
                const noz = new THREE.Mesh(new THREE.ConeGeometry(0.08, 0.18, 8), matCopper);
                const ang = (s * Math.PI * 2) / 6;
                noz.position.set(Math.cos(ang) * 1.6, shellY + shellH * 0.35, Math.sin(ang) * 1.6);
                noz.rotation.x = Math.PI;
                g.add(noz);
            }}

            // Biomass Inflow Chute (Slanted Hopper)
            const chute = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 1.2), matSSBrushed);
            chute.position.set(-1.4, shellY + shellH * 0.45, 0);
            chute.rotation.z = -0.4;
            g.add(chute);

            // Water Level Surface
            const waterMesh = new THREE.Mesh(new THREE.CylinderGeometry(1.95, 1.95, 0.05, 32), matBiofluid);
            waterMesh.position.y = shellY + shellH * 0.25;
            g.add(waterMesh);

            animators.push(() => {{
                impellersGroup.rotation.y += 0.045;
                shaft.rotation.y += 0.045;
                waterMesh.scale.set(1 + Math.sin(Date.now() * 0.005) * 0.015, 1, 1 + Math.cos(Date.now() * 0.005) * 0.015);
            }});

            plantGroup.add(g);
            eqObjects["T-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 2. D-101: INDUSTRIAL ROTARY BIOMASS DRYER
        // ══════════════════════════════════════════════════════════════════════
        function buildD101(x, z) {{
            const g = new THREE.Group();
            g.name = "D-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "D-101");
            const isCut = isCutawayGlobal;

            // Dual Concrete Piers
            addConcretePad(g, 2.2, 4.0, 1.4, -3.2, 0);
            addConcretePad(g, 2.2, 4.0, 1.2, 3.2, 0);

            // Roller Trunnion Assemblies (2 per pier)
            for (let px of [-3.2, 3.2]) {{
                for (let pz of [-1.2, 1.2]) {{
                    const roller = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.4, 16), matCarbonSteel);
                    roller.rotation.z = Math.PI / 2;
                    roller.position.set(px, 1.5, pz);
                    roller.castShadow = true;
                    g.add(roller);

                    const block = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.3, 0.5), matCastIron);
                    block.position.set(px, 1.35, pz);
                    g.add(block);
                }}
            }}

            // Main Rotary Drum Group (inclined 2.5 degrees)
            const drumGroup = new THREE.Group();
            drumGroup.position.set(0, 2.6, 0);
            drumGroup.rotation.z = 0.04; // inclination slope

            const drumL = 9.2;
            const drumR = 1.45;
            const drumMat = isSel ? matHighlight : (isCut ? matGlass : matInsulation);
            const drum = new THREE.Mesh(new THREE.CylinderGeometry(drumR, drumR, drumL, 32, 1, isCut, 0, isCut ? Math.PI * 1.3 : Math.PI * 2), drumMat);
            drum.rotation.z = Math.PI / 2;
            drum.castShadow = true;
            drumGroup.add(drum);

            // 2 Solid Forged Riding Rings (Tires)
            for (let tx of [-3.2, 3.2]) {{
                const tire = new THREE.Mesh(new THREE.CylinderGeometry(drumR + 0.15, drumR + 0.15, 0.55, 32), matSSBrushed);
                tire.rotation.z = Math.PI / 2;
                tire.position.x = tx;
                drumGroup.add(tire);
            }}

            // Girth Gear Ring
            const girthGear = new THREE.Mesh(new THREE.CylinderGeometry(drumR + 0.22, drumR + 0.22, 0.45, 36), matCastIron);
            girthGear.rotation.z = Math.PI / 2;
            girthGear.position.x = 0;
            drumGroup.add(girthGear);

            // Internal Archimedean Helical Screw Flights & Lifters
            const screwGroup = new THREE.Group();
            const screwShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, drumL - 0.4, 16), matCarbonSteel);
            screwShaft.rotation.z = Math.PI / 2;
            screwGroup.add(screwShaft);

            for (let f = -drumL / 2 + 0.8; f <= drumL / 2 - 0.8; f += 0.8) {{
                const flight = new THREE.Mesh(new THREE.TorusGeometry(drumR * 0.85, 0.12, 8, 20), matCopper);
                flight.position.x = f;
                flight.rotation.y = Math.PI / 2 + (f * 0.8);
                screwGroup.add(flight);
            }}
            drumGroup.add(screwGroup);
            g.add(drumGroup);

            // Drive Motor & Gearbox Skid (Meshing with Girth Gear)
            const driveGroup = new THREE.Group();
            driveGroup.position.set(0, 0.35, 2.2);
            addMotorGearbox(driveGroup, new THREE.Vector3(0, 0.3, 0), 1.0);
            const pinion = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.3, 0.5, 16), matCastIron);
            pinion.position.set(0, 1.8, -0.6);
            driveGroup.add(pinion);
            g.add(driveGroup);

            // Stationary Feed Breeching Hood (Inlet End)
            const feedHood = new THREE.Mesh(new THREE.BoxGeometry(1.6, 3.4, 3.2), matCarbonSteel);
            feedHood.position.set(-4.9, 2.6, 0);
            g.add(feedHood);

            // Feed Inlet Chute
            const inChute = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.2, 16), matSSBrushed);
            inChute.position.set(-4.9, 4.4, 0);
            g.add(inChute);

            // Stationary Discharge Breeching Hood & Vapor Stack
            const dischHood = new THREE.Mesh(new THREE.BoxGeometry(1.6, 3.4, 3.2), matCarbonSteel);
            dischHood.position.set(4.9, 2.6, 0);
            g.add(dischHood);

            // Top Exhaust Vapor Stack with Cyclone Collector
            const stack = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 2.4, 16), matSSBrushed);
            stack.position.set(4.9, 4.8, 0);
            g.add(stack);
            const cyclone = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.2, 16), matSSBrushed);
            cyclone.position.set(4.9, 5.8, 0);
            g.add(cyclone);

            // Bottom Rotary Airlock Discharge Valve
            const airlock = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.5, 16), matPumpRed);
            airlock.rotation.z = Math.PI / 2;
            airlock.position.set(4.9, 1.0, 0);
            g.add(airlock);

            animators.push(() => {{
                drumGroup.rotation.x += 0.015;
            }});

            plantGroup.add(g);
            eqObjects["D-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 3. M-101: INDUSTRIAL COMMINUTION HAMMER MILL
        // ══════════════════════════════════════════════════════════════════════
        function buildM101(x, z) {{
            const g = new THREE.Group();
            g.name = "M-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "M-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 4.2, 3.8, 0.35);

            // Structural I-Beam Skid Base
            const skid = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.4, 3.2), matCarbonSteel);
            skid.position.y = 0.35 + 0.2;
            g.add(skid);

            // 4 Anti-Vibration Isolator Springs
            for (let px of [-1.5, 1.5]) {{
                for (let pz of [-1.3, 1.3]) {{
                    const spring = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.25, 8), matSafetyYellow);
                    spring.position.set(px, 0.35 + 0.45, pz);
                    g.add(spring);
                }}
            }}

            // Lower Cast-Iron Mill Frame
            const lowerHousing = new THREE.Mesh(new THREE.BoxGeometry(2.0, 1.4, 2.2), matCastIron);
            lowerHousing.position.set(0.4, 0.35 + 0.4 + 0.7, 0);
            lowerHousing.castShadow = true;
            g.add(lowerHousing);

            // Upper Clamshell Housing (With Cutaway logic)
            const upperMat = isSel ? matHighlight : (isCut ? matGlass : matCastIron);
            const upperHousing = new THREE.Mesh(new THREE.CylinderGeometry(1.0, 1.0, 2.0, 24, 1, false, 0, isCut ? Math.PI : Math.PI * 2), upperMat);
            upperHousing.rotation.z = Math.PI / 2;
            upperHousing.position.set(0.4, 0.35 + 0.4 + 1.4 + 0.8, 0);
            g.add(upperHousing);

            // Rotor Shaft & Pillow Block Bearings
            const rotorShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 2.8, 16), matSS316);
            rotorShaft.rotation.x = Math.PI / 2;
            rotorShaft.position.set(0.4, 0.35 + 0.4 + 1.4 + 0.8, 0);
            g.add(rotorShaft);

            // Internal Rotor Discs & Free-Swinging Hammer Blades
            const rotorGroup = new THREE.Group();
            rotorGroup.position.set(0.4, 0.35 + 0.4 + 1.4 + 0.8, 0);

            for (let d = -0.7; d <= 0.7; d += 0.35) {{
                const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.08, 16), matCarbonSteel);
                disc.rotation.x = Math.PI / 2;
                disc.position.z = d;
                rotorGroup.add(disc);

                // 4 Swinging hammers per disc
                for (let h = 0; h < 4; h++) {{
                    const hammer = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.45, 0.06), matBronze);
                    const ang = (h * Math.PI) / 2;
                    hammer.position.set(Math.cos(ang) * 0.65, Math.sin(ang) * 0.65, d);
                    hammer.rotation.z = ang;
                    rotorGroup.add(hammer);
                }}
            }}
            g.add(rotorGroup);

            // Semi-Circular Sieve Screen Basket (Bottom 180° arc)
            const screen = new THREE.Mesh(new THREE.CylinderGeometry(0.92, 0.92, 1.8, 24, 1, true, Math.PI, Math.PI), matCopper);
            screen.rotation.x = Math.PI / 2;
            screen.position.set(0.4, 0.35 + 0.4 + 1.4 + 0.8, 0);
            g.add(screen);

            // Large TEFC Electric Drive Motor on Slide Rails
            const motorGroup = new THREE.Group();
            motorGroup.position.set(-1.1, 0.35 + 0.4 + 0.5, 0);
            const millMotor = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.3, 20), matMotorBlue);
            millMotor.rotation.x = Math.PI / 2;
            motorGroup.add(millMotor);
            const mCowl = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 0.3, 20), matCarbonSteel);
            mCowl.rotation.x = Math.PI / 2;
            mCowl.position.z = -0.75;
            motorGroup.add(mCowl);
            g.add(motorGroup);

            // V-Belt Drive Guard Enclosure
            const beltGuard = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.4, 0.4), matSafetyYellow);
            beltGuard.position.set(-0.35, 0.35 + 0.4 + 1.1, 1.3);
            g.add(beltGuard);

            // Feed Hopper with Tramp Iron Separator
            const hopper = new THREE.Mesh(new THREE.ConeGeometry(0.9, 1.5, 4), isSel ? matHighlight : matSSBrushed);
            hopper.position.set(0.4, 0.35 + 0.4 + 1.4 + 1.6 + 0.75, 0);
            g.add(hopper);

            // Bottom Discharge Duct Hopper
            const disch = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.0, 4), matCarbonSteel);
            disch.rotation.x = Math.PI;
            disch.position.set(0.4, 0.35 + 0.4 - 0.2, 0);
            g.add(disch);

            animators.push(() => {{
                rotorGroup.rotation.z += 0.12;
            }});

            plantGroup.add(g);
            eqObjects["M-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 4. T-102: STAINLESS STEEL SLURRY MIXING TANK
        // ══════════════════════════════════════════════════════════════════════
        function buildT102(x, z) {{
            const g = new THREE.Group();
            g.name = "T-102";
            g.position.set(x, 0, z);
            const isSel = (targetId === "T-102");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 4.6, 4.6, 0.35);

            // 4 Stainless Pipe Legs with Floor Pads
            for (let i = 0; i < 4; i++) {{
                const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 1.8, 16), matSSBrushed);
                const ang = (i * Math.PI) / 2 + Math.PI / 4;
                leg.position.set(Math.cos(ang) * 1.6, 0.35 + 0.9, Math.sin(ang) * 1.6);
                leg.castShadow = true;
                g.add(leg);

                // Pad
                const pad = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.05, 12), matCarbonSteel);
                pad.position.set(Math.cos(ang) * 1.6, 0.35 + 0.03, Math.sin(ang) * 1.6);
                g.add(pad);
            }}

            // ASME Dished Bottom Head
            const botDish = new THREE.Mesh(new THREE.SphereGeometry(1.8, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), isSel ? matHighlight : matSS316);
            botDish.position.y = 0.35 + 1.8;
            g.add(botDish);

            // Cylindrical Shell (With Cutaway)
            const tH = 3.8;
            const tY = 0.35 + 1.8 + tH / 2;
            const shellMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const shell = new THREE.Mesh(new THREE.CylinderGeometry(1.8, 1.8, tH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), shellMat);
            shell.position.y = tY;
            shell.castShadow = true;
            g.add(shell);

            // Torispherical Top Head
            const topDish = new THREE.Mesh(new THREE.SphereGeometry(1.8, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), isSel ? matHighlight : matSS316);
            topDish.position.y = tY + tH / 2;
            g.add(topDish);

            // Mixer Structural Bridge & Drive
            const bridge = new THREE.Mesh(new THREE.BoxGeometry(4.0, 0.2, 0.6), matSSBrushed);
            bridge.position.y = tY + tH / 2 + 0.6;
            g.add(bridge);
            addMotorGearbox(g, new THREE.Vector3(0, tY + tH / 2 + 0.7, 0), 0.95);

            // Dual A310 High-Efficiency Hydrofoil Impellers
            const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, tH + 0.8, 16), matSS316);
            shaft.position.y = tY;
            g.add(shaft);

            const hydGroup = new THREE.Group();
            hydGroup.position.y = tY;

            for (let tier of [-tH * 0.3, tH * 0.15]) {{
                for (let b = 0; b < 3; b++) {{
                    const foil = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.06, 0.22), matSS316);
                    foil.rotation.y = (b * Math.PI * 2) / 3;
                    foil.rotation.x = 0.25;
                    foil.position.y = tier;
                    hydGroup.add(foil);
                }}
            }}
            g.add(hydGroup);

            // 4 Internal Wall Baffles
            for (let i = 0; i < 4; i++) {{
                const bfl = new THREE.Mesh(new THREE.BoxGeometry(0.3, tH * 0.85, 0.04), matSS316);
                const ang = (i * Math.PI) / 2;
                bfl.position.set(Math.cos(ang) * 1.62, tY, Math.sin(ang) * 1.62);
                bfl.rotation.y = -ang;
                g.add(bfl);
            }}

            // Sulfuric Acid (H2SO4) Dosing Dip Tube (Extending to bottom)
            const acidTube = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, tH * 0.9, 12), matCopper);
            acidTube.position.set(1.1, tY, 0.4);
            g.add(acidTube);

            // Acid Isolation Ball Valve (Violet/Magenta)
            const acidValve = new THREE.Mesh(new THREE.BoxGeometry(0.25, 0.25, 0.25), new THREE.MeshStandardMaterial({{ color: 0x8e24aa }}));
            acidValve.position.set(1.1, tY + tH / 2 + 0.65, 0.4);
            g.add(acidValve);

            // Radar Level Transmitter Housing
            const radar = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.4, 12), matMotorBlue);
            radar.position.set(-1.0, tY + tH / 2 + 0.75, 0.4);
            g.add(radar);

            // Side Manway & Sight Glass Port
            const manway = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 0.25, 16), matSSBrushed);
            manway.rotation.z = Math.PI / 2;
            manway.position.set(1.85, tY + 0.4, 0);
            g.add(manway);

            // Slurry Fluid Volume
            const slurryLiq = new THREE.Mesh(new THREE.CylinderGeometry(1.75, 1.75, 0.05, 32), matBiofluid);
            slurryLiq.position.y = tY + tH * 0.2;
            g.add(slurryLiq);

            animators.push(() => {{
                hydGroup.rotation.y += 0.05;
                shaft.rotation.y += 0.05;
            }});

            plantGroup.add(g);
            eqObjects["T-102"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 5. R-101: HIGH-PRESSURE PRETREATMENT REACTOR
        // ══════════════════════════════════════════════════════════════════════
        function buildR101(x, z) {{
            const g = new THREE.Group();
            g.name = "R-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "R-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 5.2, 5.2, 0.35);

            // Skirt Support with Anchor Bolting Ring
            const skirt = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.05, 1.8, 32), matCarbonSteel);
            skirt.position.y = 0.35 + 0.9;
            skirt.castShadow = true;
            g.add(skirt);

            // Skirt Access Manhole
            const manhole = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 0.3, 16), matCarbonSteel);
            manhole.rotation.x = Math.PI / 2;
            manhole.position.set(0, 0.35 + 0.9, 1.95);
            g.add(manhole);

            // Ellipsoidal Bottom Head
            const botHead = new THREE.Mesh(new THREE.SphereGeometry(2.0, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), isSel ? matHighlight : matSS316);
            botHead.position.y = 0.35 + 1.8;
            g.add(botHead);

            // Main Pressure Vessel Shell (ASME Rated)
            const rH = 4.4;
            const rY = 0.35 + 1.8 + rH / 2;
            const shellMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const shell = new THREE.Mesh(new THREE.CylinderGeometry(2.0, 2.0, rH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), shellMat);
            shell.position.y = rY;
            shell.castShadow = true;
            g.add(shell);

            // External Dimpled/Half-Pipe Steam Heating Jacket (Lower 70%)
            const jH = rH * 0.7;
            const jacketMat = isSel ? matHighlight : (isCut ? matGlass : matInsulation);
            const jacket = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, jH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), jacketMat);
            jacket.position.y = rY - rH / 2 + jH / 2;
            jacket.castShadow = true;
            g.add(jacket);

            // Jacket Steam Inlet & Condensate Outlet Flanges
            addNozzle(g, 0.12, 0.4, new THREE.Vector3(2.2, rY + 0.4, 0), new THREE.Euler(0, 0, -Math.PI / 2));
            addNozzle(g, 0.12, 0.4, new THREE.Vector3(2.2, rY - jH / 2, 0), new THREE.Euler(0, 0, -Math.PI / 2));

            // Bolted Flange Joint with 24 Perimeter Stud Bolts
            const mainFlange = addFlange(g, 2.0, rY + rH / 2, 0.15);
            for (let b = 0; b < 24; b++) {{
                const bolt = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.25, 8), matSS316);
                const ang = (b * Math.PI * 2) / 24;
                bolt.position.set(Math.cos(ang) * 2.15, rY + rH / 2, Math.sin(ang) * 2.15);
                g.add(bolt);
            }}

            // Ellipsoidal Top Head
            const topHead = new THREE.Mesh(new THREE.SphereGeometry(2.0, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), isSel ? matHighlight : matSS316);
            topHead.position.y = rY + rH / 2 + 0.08;
            g.add(topHead);

            // Heavy Drive Motor & Mechanical Seal Pot
            addMotorGearbox(g, new THREE.Vector3(0, rY + rH / 2 + 0.8, 0), 1.2);

            // Seal Barrier Fluid Reservoir Pot (Thermosiphon)
            const sealPot = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.8, 16), matSSBrushed);
            sealPot.position.set(1.2, rY + rH / 2 + 1.2, 0.6);
            g.add(sealPot);

            // Internal Heavy Anchor Agitator with PTFE Wall Scrapers
            const anchorGroup = new THREE.Group();
            anchorGroup.position.y = rY;

            const aShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, rH + 0.8, 16), matSS316);
            anchorGroup.add(aShaft);

            // Curved Anchor Sweep Arms
            const armL = new THREE.Mesh(new THREE.BoxGeometry(0.1, rH * 0.75, 0.15), matSS316);
            armL.position.set(-1.8, -rH * 0.1, 0);
            anchorGroup.add(armL);
            const armR = new THREE.Mesh(new THREE.BoxGeometry(0.1, rH * 0.75, 0.15), matSS316);
            armR.position.set(1.8, -rH * 0.1, 0);
            anchorGroup.add(armR);

            // Bottom Cross Bow
            const bow = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.12, 0.2), matSS316);
            bow.position.y = -rH * 0.45;
            anchorGroup.add(bow);

            // Wall Wipers
            for (let w = -rH * 0.35; w <= rH * 0.25; w += 0.6) {{
                const wiper1 = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.25, 0.08), matBronze);
                wiper1.position.set(-1.85, w, 0);
                anchorGroup.add(wiper1);
                const wiper2 = new THREE.Mesh(new THREE.BoxGeometry(0.12, 0.25, 0.08), matBronze);
                wiper2.position.set(1.85, w, 0);
                anchorGroup.add(wiper2);
            }}
            g.add(anchorGroup);

            // 3-Tier Side Thermowell Sensor Transmitter Heads
            for (let th of [-1.0, 0.2, 1.4]) {{
                const tw = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.35, 12), matMotorBlue);
                tw.rotation.z = Math.PI / 2;
                tw.position.set(-2.25, rY + th, 0);
                g.add(tw);
            }}

            // Safety Relief Valve (SRV) & Vent Horn on Top Head
            const srv = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.6, 12), matPumpRed);
            srv.position.set(-0.8, rY + rH / 2 + 1.2, -0.6);
            g.add(srv);
            const srvHorn = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.16, 0.6, 12), matCarbonSteel);
            srvHorn.rotation.x = 0.5;
            srvHorn.position.set(-0.8, rY + rH / 2 + 1.6, -0.75);
            g.add(srvHorn);

            // Bottom Flash Blowdown Ball Valve with Pneumatic Actuator
            const blowdown = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.5, 0.4), matPumpRed);
            blowdown.position.set(0, 0.35 + 0.6, 0);
            g.add(blowdown);

            animators.push(() => {{
                anchorGroup.rotation.y += 0.035;
            }});

            plantGroup.add(g);
            eqObjects["R-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 6. F-101: INDUSTRIAL RECESSED MEMBRANE FILTER PRESS
        // ══════════════════════════════════════════════════════════════════════
        function buildF101(x, z) {{
            const g = new THREE.Group();
            g.name = "F-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "F-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 6.8, 3.8, 0.35);

            // 4 Heavy Structural Support Columns
            for (let px of [-2.6, 2.6]) {{
                for (let pz of [-1.2, 1.2]) {{
                    const col = new THREE.Mesh(new THREE.BoxGeometry(0.35, 1.8, 0.35), matCarbonSteel);
                    col.position.set(px, 0.35 + 0.9, pz);
                    col.castShadow = true;
                    g.add(col);
                }}
            }}

            // Stationary Feed Head (Front Heavy Casting)
            const headMat = isSel ? matHighlight : matCastIron;
            const feedHead = new THREE.Mesh(new THREE.BoxGeometry(0.7, 2.6, 2.4), headMat);
            feedHead.position.set(-2.6, 0.35 + 1.8 + 1.3, 0);
            feedHead.castShadow = true;
            g.add(feedHead);

            // Rear Thrust Stand
            const rearStand = new THREE.Mesh(new THREE.BoxGeometry(0.7, 2.6, 2.4), headMat);
            rearStand.position.set(2.6, 0.35 + 1.8 + 1.3, 0);
            rearStand.castShadow = true;
            g.add(rearStand);

            // Massive Hydraulic Clamping Cylinder & Chrome Ram Rod
            const hydCyl = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.6, 24), matMotorBlue);
            hydCyl.rotation.z = Math.PI / 2;
            hydCyl.position.set(3.4, 0.35 + 1.8 + 1.3, 0);
            g.add(hydCyl);

            const ramRod = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 1.2, 20), matSS316);
            ramRod.rotation.z = Math.PI / 2;
            ramRod.position.set(2.1, 0.35 + 1.8 + 1.3, 0);
            g.add(ramRod);

            // Dual Heavy Side Guide Tension Rails
            for (let pz of [-1.2, 1.2]) {{
                const rail = new THREE.Mesh(new THREE.BoxGeometry(5.2, 0.35, 0.18), matCarbonSteel);
                rail.position.set(0, 0.35 + 1.8 + 1.3, pz);
                g.add(rail);
            }}

            // Moving Follower Thrust Plate
            const follower = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.4, 2.2), matCarbonSteel);
            follower.position.set(1.5, 0.35 + 1.8 + 1.3, 0);
            follower.castShadow = true;
            g.add(follower);

            // Stack of 22 Recessed Polypropylene Chamber Plates
            const plateGroup = new THREE.Group();
            const plateMat = isSel ? matHighlight : matSSBrushed;
            const numPlates = 22;
            const startX = -2.15;
            const spacing = 0.16;

            for (let p = 0; p < numPlates; p++) {{
                const px = startX + p * spacing;
                const plate = new THREE.Mesh(new THREE.BoxGeometry(0.09, 2.2, 2.0), plateMat);
                plate.position.set(px, 0.35 + 1.8 + 1.3, 0);

                // Top hanging handles resting on side rails
                const handle = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.15, 2.45), matCarbonSteel);
                handle.position.set(px, 0.35 + 1.8 + 2.2, 0);
                plateGroup.add(plate);
                plateGroup.add(handle);
            }}
            g.add(plateGroup);

            // Twin Stainless Filtrate Collection Launders (Troughs)
            for (let pz of [-1.15, 1.15]) {{
                const launder = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.25, 0.35), matSS316);
                launder.position.set(-0.3, 0.35 + 1.8 - 0.15, pz);
                g.add(launder);
            }}

            // Bottom Sloped Cake Discharge Drop Hopper
            const cakeHopper = new THREE.Mesh(new THREE.BoxGeometry(4.4, 0.8, 2.0), matCarbonSteel);
            cakeHopper.position.set(-0.3, 0.35 + 0.8, 0);
            g.add(cakeHopper);

            // Hydraulic Power Unit (HPU) Skid at Rear
            const hpu = new THREE.Mesh(new THREE.BoxGeometry(1.2, 1.0, 1.4), matCastIron);
            hpu.position.set(3.4, 0.35 + 0.5, 1.2);
            g.add(hpu);

            plantGroup.add(g);
            eqObjects["F-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 7. E-101: INDUSTRIAL FERMENTATION BIOREACTOR
        // ══════════════════════════════════════════════════════════════════════
        function buildE101(x, z) {{
            const g = new THREE.Group();
            g.name = "E-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "E-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 6.0, 6.0, 0.35);

            // Skirt Support Base with Manhole
            const skirt = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.45, 2.0, 32), matCarbonSteel);
            skirt.position.y = 0.35 + 1.0;
            skirt.castShadow = true;
            g.add(skirt);

            // Torispherical Bottom Head
            const botHead = new THREE.Mesh(new THREE.SphereGeometry(2.4, 32, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2), isSel ? matHighlight : matSS316);
            botHead.position.y = 0.35 + 2.0;
            g.add(botHead);

            // Tall Slender Aspect Ratio Vessel Shell (H:D = 3:1)
            const fH = 7.2;
            const fY = 0.35 + 2.0 + fH / 2;
            const shellMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const shell = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, fH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), shellMat);
            shell.position.y = fY;
            shell.castShadow = true;
            g.add(shell);

            // Flange Rings
            addFlange(g, 2.4, fY - fH / 2);
            addFlange(g, 2.4, fY + fH / 2);

            // Torispherical Top Head
            const topHead = new THREE.Mesh(new THREE.SphereGeometry(2.4, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), isSel ? matHighlight : matSS316);
            topHead.position.y = fY + fH / 2;
            g.add(topHead);

            // Top Sanitary Servo Drive & Sterile Double Mechanical Seal
            addMotorGearbox(g, new THREE.Vector3(0, fY + fH / 2 + 0.8, 0), 1.25);

            // Agitator Shaft & 3 Tiers of 6-Blade Rushton Turbines
            const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, fH + 1.2, 16), matSS316);
            shaft.position.y = fY;
            g.add(shaft);

            const rushtonGroup = new THREE.Group();
            rushtonGroup.position.y = fY;

            const tiers = [-fH * 0.35, 0, fH * 0.3];
            for (let t of tiers) {{
                const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 0.65, 0.06, 20), matSS316);
                disc.position.y = t;
                rushtonGroup.add(disc);

                for (let b = 0; b < 6; b++) {{
                    const bMesh = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.25, 0.06), matSS316);
                    const ang = (b * Math.PI * 2) / 6;
                    bMesh.position.set(Math.cos(ang) * 0.9, t, Math.sin(ang) * 0.9);
                    bMesh.rotation.y = -ang;
                    rushtonGroup.add(bMesh);
                }}
            }}
            g.add(rushtonGroup);

            // 4 Internal Vertical Sanitary Baffles
            for (let i = 0; i < 4; i++) {{
                const bfl = new THREE.Mesh(new THREE.BoxGeometry(0.38, fH * 0.88, 0.04), matSS316);
                const ang = (i * Math.PI) / 2;
                bfl.position.set(Math.cos(ang) * 2.2, fY, Math.sin(ang) * 2.2);
                bfl.rotation.y = -ang;
                g.add(bfl);
            }}

            // Internal Stainless Vertical Cooling Coil Loops
            for (let c = 0; c < 4; c++) {{
                const ang = (c * Math.PI) / 2 + Math.PI / 4;
                const coil = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, fH * 0.8, 12), matSSBrushed);
                coil.position.set(Math.cos(ang) * 1.5, fY, Math.sin(ang) * 1.5);
                g.add(coil);
            }}

            // Bottom Ring Aeration / Purge Sparger
            const sparger = new THREE.Mesh(new THREE.TorusGeometry(1.2, 0.06, 8, 24), matSS316);
            sparger.rotation.x = Math.PI / 2;
            sparger.position.y = fY - fH * 0.45;
            g.add(sparger);

            // Heated Sterile Vent Filter Capsule (CO2 Exhaust Line)
            const ventFilter = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 0.9, 16), matSSBrushed);
            ventFilter.position.set(-1.2, fY + fH / 2 + 1.4, 0.8);
            g.add(ventFilter);

            // Dual CIP Rotary Spray Balls
            for (let sx of [-0.8, 0.8]) {{
                const sball = new THREE.Mesh(new THREE.SphereGeometry(0.12, 12, 12), matSS316);
                sball.position.set(sx, fY + fH / 2 - 0.3, 0);
                g.add(sball);
            }}

            // Side Sanitary Ports (DO, pH, Sample Valve, Sight Glass)
            const sightWindow = new THREE.Mesh(new THREE.BoxGeometry(0.15, 3.2, 0.3), matGlass);
            sightWindow.position.set(2.4, fY, 0);
            g.add(sightWindow);

            // Fermentation Broth Fluid Mesh
            const fermFluid = new THREE.Mesh(new THREE.CylinderGeometry(2.32, 2.32, 0.05, 32), matBrothFluid);
            fermFluid.position.y = fY + fH * 0.35;
            g.add(fermFluid);

            animators.push(() => {{
                rushtonGroup.rotation.y += 0.04;
                shaft.rotation.y += 0.04;
            }});

            plantGroup.add(g);
            eqObjects["E-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 8. S-101: INDUSTRIAL CONTINUOUS DISC-STACK CLARIFICATION CENTRIFUGE
        // ══════════════════════════════════════════════════════════════════════
        function buildS101(x, z) {{
            const g = new THREE.Group();
            g.name = "S-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "S-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 4.2, 4.2, 0.35);

            // Vibration-Damped Cast-Iron Machine Frame Base
            const baseFrame = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.8, 1.4, 24), matCastIron);
            baseFrame.position.y = 0.35 + 0.7;
            baseFrame.castShadow = true;
            g.add(baseFrame);

            // Vertical High-Speed Spindle Drive Motor
            const mot = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 1.0, 16), matMotorBlue);
            mot.position.set(0, 0.35 + 0.6, -1.0);
            g.add(mot);

            // Upper Stainless Centrifuge Bowl Casing (With Cutaway)
            const bowlMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const bowlCasing = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 1.4, 32, 1, isCut, 0, isCut ? Math.PI * 1.3 : Math.PI * 2), bowlMat);
            bowlCasing.position.y = 0.35 + 1.4 + 0.7;
            bowlCasing.castShadow = true;
            g.add(bowlCasing);

            // Conical Sludge Bottom Section
            const cone = new THREE.Mesh(new THREE.ConeGeometry(1.4, 1.2, 32, 1, isCut, 0, isCut ? Math.PI * 1.3 : Math.PI * 2), bowlMat);
            cone.rotation.x = Math.PI;
            cone.position.y = 0.35 + 1.4 - 0.1;
            g.add(cone);

            // Internal Disc-Stack Assembly (30+ Conical Separation Plates)
            const stackGroup = new THREE.Group();
            stackGroup.position.y = 0.35 + 1.4 + 0.6;

            const spindle = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1.6, 16), matSS316);
            stackGroup.add(spindle);

            for (let d = -0.5; d <= 0.5; d += 0.08) {{
                const disc = new THREE.Mesh(new THREE.ConeGeometry(1.15, 0.22, 24, 1, true), matSSBrushed);
                disc.rotation.x = Math.PI;
                disc.position.y = d;
                stackGroup.add(disc);
            }}
            g.add(stackGroup);

            // Centripetal Liquid Pump (Paring Disc Chamber) at Neck
            const paringDisc = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 0.35, 20), matSSBrushed);
            paringDisc.position.y = 0.35 + 1.4 + 1.5;
            g.add(paringDisc);

            // External Top Feed Pipe & Clarified Broth Discharge Elbow
            const feedTube = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 0.9, 12), matSS316);
            feedTube.position.set(0, 0.35 + 1.4 + 2.0, 0);
            g.add(feedTube);

            const dischPipe = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.2, 12), matSS316);
            dischPipe.rotation.z = Math.PI / 2;
            dischPipe.position.set(-0.8, 0.35 + 1.4 + 1.6, 0);
            g.add(dischPipe);

            // Solids / Sludge Ejection Discharge Cyclone Chute
            const sludgeChute = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.15, 0.8, 16), matCarbonSteel);
            sludgeChute.rotation.z = -0.5;
            sludgeChute.position.set(1.2, 0.35 + 1.2, 0);
            g.add(sludgeChute);

            animators.push(() => {{
                stackGroup.rotation.y += 0.14;
            }});

            plantGroup.add(g);
            eqObjects["S-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 9. C-101: MULTI-STAGE INDUSTRIAL DISTILLATION COLUMN & REBOILER SKID
        // ══════════════════════════════════════════════════════════════════════
        function buildC101(x, z) {{
            const g = new THREE.Group();
            g.name = "C-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "C-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 6.5, 5.0, 0.35);

            // Base Skirt Support with Anchor Bolting Ring & Manhole
            const skirt = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.65, 2.2, 32), matCarbonSteel);
            skirt.position.y = 0.35 + 1.1;
            skirt.castShadow = true;
            g.add(skirt);

            // Tall Vertical Fractional Distillation Column Shell (14m scaled)
            const colH = 13.5;
            const colY = 0.35 + 2.2 + colH / 2;
            const shellMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
            const shell = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, colH, 32, 1, isCut, 0, isCut ? Math.PI * 1.25 : Math.PI * 2), shellMat);
            shell.position.y = colY;
            shell.castShadow = true;
            g.add(shell);

            // Ellipsoidal Top Head
            const topD = new THREE.Mesh(new THREE.SphereGeometry(1.5, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), isSel ? matHighlight : matSS316);
            topD.position.y = colY + colH / 2;
            g.add(topD);

            // 16 Internal Perforated Sieve Trays with Downcomers & Overflow Weirs
            const trayGroup = new THREE.Group();
            const numTrays = 16;
            const startY = colY - colH / 2 + 0.8;
            const trayStep = (colH - 1.6) / numTrays;

            for (let t = 0; t < numTrays; t++) {{
                const ty = startY + t * trayStep;
                // Perforated deck
                const tray = new THREE.Mesh(new THREE.CylinderGeometry(1.44, 1.44, 0.06, 24), matCopper);
                tray.position.y = ty;
                trayGroup.add(tray);

                // Downcomer apron plate
                const downcomer = new THREE.Mesh(new THREE.BoxGeometry(0.06, trayStep * 0.75, 0.7), matSS316);
                downcomer.position.set((t % 2 === 0 ? 0.9 : -0.9), ty - trayStep * 0.35, 0);
                trayGroup.add(downcomer);
            }}
            g.add(trayGroup);

            // Side Horizontal Thermosiphon Reboiler Skid next to Column Base
            const rebGroup = new THREE.Group();
            rebGroup.position.set(2.8, 0.35 + 1.5, 0);

            const rebShell = new THREE.Mesh(new THREE.CylinderGeometry(0.8, 0.8, 2.6, 24), matSSBrushed);
            rebShell.rotation.z = Math.PI / 2;
            rebShell.castShadow = true;
            rebGroup.add(rebShell);

            // Steam Inlet & Condensate Flanges
            addNozzle(rebGroup, 0.12, 0.5, new THREE.Vector3(-0.7, 0.8, 0), new THREE.Euler(0, 0, 0));
            addNozzle(rebGroup, 0.12, 0.5, new THREE.Vector3(0.7, -0.8, 0), new THREE.Euler(0, 0, Math.PI));

            // Vapor return loop to column
            const vapLoop = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 1.5, 16), matCopper);
            vapLoop.rotation.z = Math.PI / 2;
            vapLoop.position.set(-1.6, 0.6, 0);
            rebGroup.add(vapLoop);
            g.add(rebGroup);

            // Overhead Vapor Line with Long-Radius Sweep Elbow & Condenser
            const sweepPipe = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 2.2, 16), matCopper);
            sweepPipe.position.set(0, colY + colH / 2 + 1.1, 0);
            g.add(sweepPipe);

            const condenser = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 0.65, 2.4, 20), matSSBrushed);
            condenser.rotation.z = Math.PI / 2;
            condenser.position.set(-2.2, colY + colH / 2 + 1.6, 0);
            g.add(condenser);

            // Reflux Drum Accumulator Vessel & Reflux Return Pump
            const drum = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 1.6, 16), matSS316);
            drum.rotation.z = Math.PI / 2;
            drum.position.set(-2.2, colY + colH / 2 - 0.4, 0);
            g.add(drum);

            // Vertical Safety Cage Ladder running full height
            const ladderGroup = new THREE.Group();
            for (let ly = 1.0; ly <= colH + 2.0; ly += 0.45) {{
                const rung = new THREE.Mesh(new THREE.BoxGeometry(0.5, 0.04, 0.04), matSafetyYellow);
                rung.position.set(-1.65, ly, 0);
                ladderGroup.add(rung);
            }}
            g.add(ladderGroup);

            // 3 Circular Maintenance Platforms with Safety Handrails
            for (let py of [colY - colH * 0.25, colY + colH * 0.1, colY + colH * 0.4]) {{
                const plat = new THREE.Mesh(new THREE.CylinderGeometry(2.3, 2.3, 0.1, 24), matCarbonSteel);
                plat.position.y = py;
                g.add(plat);

                const rail = new THREE.Mesh(new THREE.TorusGeometry(2.25, 0.04, 6, 24), matSafetyYellow);
                rail.rotation.x = Math.PI / 2;
                rail.position.y = py + 0.9;
                g.add(rail);
            }}

            plantGroup.add(g);
            eqObjects["C-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // 10. V-101: TWIN-BED MOLECULAR SIEVE PSA DEHYDRATION SYSTEM
        // ══════════════════════════════════════════════════════════════════════
        function buildV101(x, z) {{
            const g = new THREE.Group();
            g.name = "V-101";
            g.position.set(x, 0, z);
            const isSel = (targetId === "V-101");
            const isCut = isCutawayGlobal;

            addConcretePad(g, 5.8, 4.4, 0.35);

            // Structural Skid Base with Diamond Flooring
            const skid = new THREE.Mesh(new THREE.BoxGeometry(5.2, 0.3, 3.8), matCastIron);
            skid.position.y = 0.35 + 0.15;
            g.add(skid);

            // Twin Adsorption Columns (Bed A and Bed B)
            const bedOffsets = [-1.4, 1.4];
            for (let bx of bedOffsets) {{
                const bGroup = new THREE.Group();
                bGroup.position.set(bx, 0.35 + 0.3, 0);

                // Column Skirt
                const bSkirt = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.9, 1.2, 24), matCarbonSteel);
                bSkirt.position.y = 0.6;
                bGroup.add(bSkirt);

                // Vessel Shell (ASME Rating)
                const vH = 5.2;
                const vMat = isSel ? matHighlight : (isCut ? matGlass : matSS316);
                const vShell = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.85, vH, 24, 1, isCut, 0, isCut ? Math.PI * 1.3 : Math.PI * 2), vMat);
                vShell.position.y = 1.2 + vH / 2;
                vShell.castShadow = true;
                bGroup.add(vShell);

                // Top & Bottom Heads
                const bHead = new THREE.Mesh(new THREE.SphereGeometry(0.85, 24, 12, 0, Math.PI * 2, 0, Math.PI / 2), isSel ? matHighlight : matSS316);
                bHead.position.y = 1.2 + vH;
                bGroup.add(bHead);

                // Internal Zeolite 3A Molecular Sieve Bed
                const sieveBed = new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.78, vH * 0.75, 20), matCopper);
                sieveBed.position.y = 1.2 + vH * 0.45;
                bGroup.add(sieveBed);

                g.add(bGroup);
            }}

            // Automated Cross-Over Switching Valve Manifold Skid (4 Actuated Valves)
            const manifoldY = 0.35 + 0.3 + 1.2 + 2.6;
            const crossPipe = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 3.2, 16), matSSBrushed);
            crossPipe.rotation.z = Math.PI / 2;
            crossPipe.position.set(0, manifoldY, 0);
            g.add(crossPipe);

            for (let vx of [-1.0, 1.0]) {{
                const valveAct = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.45, 0.35), matPumpRed);
                valveAct.position.set(vx, manifoldY, 0);
                g.add(valveAct);
            }}

            // Inter-Bed Regeneration Gas Superheater Exchanger
            const heater = new THREE.Mesh(new THREE.CylinderGeometry(0.4, 0.4, 1.8, 16), matSSBrushed);
            heater.rotation.z = Math.PI / 2;
            heater.position.set(0, 0.35 + 0.3 + 0.8, -1.2);
            g.add(heater);

            // Water Knockout Separator Drum with Level Gauge
            const koDrum = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.35, 1.4, 16), matSS316);
            koDrum.position.set(-2.1, 0.35 + 0.3 + 1.4, 1.2);
            g.add(koDrum);

            // Inline Duplex Micron Particulate Filter Housings (Final Anhydrous Ethanol Stream)
            for (let fx of [1.8, 2.3]) {{
                const filterVessel = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 1.1, 16), matSS316);
                filterVessel.position.set(fx, 0.35 + 0.3 + 1.2, 1.2);
                g.add(filterVessel);
            }}

            plantGroup.add(g);
            eqObjects["V-101"] = g;
            return g;
        }}

        // ══════════════════════════════════════════════════════════════════════
        // BUILD COMPLETE REFINERY LAYOUT (ACCORDING TO PFD PROCESS STAGES)
        // ══════════════════════════════════════════════════════════════════════
        // Row 1 (Pretreatment & Separation): X: -30 -> +12, Z: 0
        buildT101(-30, 0);     // Washing Tank
        buildD101(-21, 0);     // Dryer
        buildM101(-12, 0);     // Milling Unit
        buildT102(-4, 0);      // Slurry Tank
        buildR101(4, 0);       // Pretreatment Reactor
        buildF101(12, 0);      // Filter Press

        // Row 2 (Bioconversion & Product Recovery): X: +12 -> -20, Z: 16
        buildE101(12, 16);     // Fermentation Bioreactor
        buildS101(3, 16);      // Broth Centrifuge
        buildC101(-8, 16);     // Distillation Column
        buildV101(-20, 16);    // Molecular Sieve Dehydration

        // Auxiliary Process Pumps along the stream paths
        addCentrifugalPump(plantGroup, -26.5, 0.35, 1.2, 0);       // Wash Water Pump
        addCentrifugalPump(plantGroup, -8, 0.35, -1.8, Math.PI / 2); // Slurry Recirculation Pump
        addCentrifugalPump(plantGroup, 0, 0.35, 0, 0);             // High-Pressure Reactor Feed Pump
        addCentrifugalPump(plantGroup, 14.5, 0.35, 8, Math.PI / 2); // Hydrolysate Transfer Pump
        addCentrifugalPump(plantGroup, 7.5, 0.35, 16, 0);           // Fermenter Broth Feed Pump
        addCentrifugalPump(plantGroup, -3.0, 0.35, 16, 0);          // Clarified Broth Feed Pump

        // ══════════════════════════════════════════════════════════════════════
        // INDUSTRIAL COLOR-CODED PIPING SYSTEM WITH ANIMATED PARTICLES
        // ══════════════════════════════════════════════════════════════════════
        const pipeDefinitions = [
            // 1. T-101 -> D-101: Washed Biomass Conveying
            {{ pts: [new THREE.Vector3(-30, 2.2, 0), new THREE.Vector3(-25.5, 2.2, 0)], color: 0x2e7d32, radius: 0.16 }},
            // 2. D-101 -> M-101: Dried Biomass
            {{ pts: [new THREE.Vector3(-16.5, 2.2, 0), new THREE.Vector3(-12, 2.2, 0)], color: 0x2e7d32, radius: 0.16 }},
            // 3. M-101 -> T-102: Milled Biomass Slurry Feed
            {{ pts: [new THREE.Vector3(-12, 1.2, 0), new THREE.Vector3(-8, 1.2, 0), new THREE.Vector3(-8, 3.8, 0), new THREE.Vector3(-4, 3.8, 0)], color: 0x2e7d32, radius: 0.14 }},
            // 4. Acid Dosing Header into T-102
            {{ pts: [new THREE.Vector3(-4, 5.8, -2.5), new THREE.Vector3(-4, 5.8, 0)], color: 0x8e24aa, radius: 0.08 }},
            // 5. T-102 -> R-101: Acid Slurry Transfer
            {{ pts: [new THREE.Vector3(-4, 1.8, 0), new THREE.Vector3(0, 1.8, 0), new THREE.Vector3(0, 4.2, 0), new THREE.Vector3(4, 4.2, 0)], color: 0x2e7d32, radius: 0.14 }},
            // 6. R-101 -> F-101: Pretreated Slurry Blowdown
            {{ pts: [new THREE.Vector3(4, 1.8, 0), new THREE.Vector3(9.4, 1.8, 0)], color: 0x2e7d32, radius: 0.15 }},
            // 7. F-101 -> E-101: Liquid Hydrolysate Liquor (U-turn loop)
            {{ pts: [new THREE.Vector3(14.6, 2.0, 0), new THREE.Vector3(18.5, 2.0, 0), new THREE.Vector3(18.5, 2.0, 16), new THREE.Vector3(14.4, 2.0, 16)], color: 0x0288d1, radius: 0.14 }},
            // 8. E-101 -> S-101: Fermented Broth Stream
            {{ pts: [new THREE.Vector3(9.6, 2.0, 16), new THREE.Vector3(3, 2.0, 16)], color: 0xd97706, radius: 0.14 }},
            // 9. S-101 -> C-101: Clarified Beer Feed
            {{ pts: [new THREE.Vector3(3, 2.4, 16), new THREE.Vector3(-8, 2.4, 16), new THREE.Vector3(-8, 5.2, 16)], color: 0x0288d1, radius: 0.13 }},
            // 10. C-101 -> V-101: Azeotropic Ethanol Vapor Line
            {{ pts: [new THREE.Vector3(-8, 12.0, 16), new THREE.Vector3(-14, 12.0, 16), new THREE.Vector3(-14, 4.8, 16), new THREE.Vector3(-20, 4.8, 16)], color: 0xffb300, radius: 0.15 }},
            // 11. V-101 Outflow: Final Anhydrous Fuel Ethanol (>99.5%)
            {{ pts: [new THREE.Vector3(-20, 2.2, 16), new THREE.Vector3(-26, 2.2, 16)], color: 0x10b981, radius: 0.12 }}
        ];

        const particleFlows = [];

        pipeDefinitions.forEach((pdef) => {{
            let curve;
            if (pdef.pts.length === 2) {{
                curve = new THREE.LineCurve3(pdef.pts[0], pdef.pts[1]);
            }} else {{
                curve = new THREE.CatmullRomCurve3(pdef.pts, false, 'catmullrom', 0.1);
            }}
            const tubeGeo = new THREE.TubeGeometry(curve, 32, pdef.radius, 12, false);
            const tubeMat = new THREE.MeshStandardMaterial({{
                color: pdef.color,
                metalness: 0.7,
                roughness: 0.3
            }});
            const pipeMesh = new THREE.Mesh(tubeGeo, tubeMat);
            pipeMesh.castShadow = true;
            plantGroup.add(pipeMesh);

            // Flow Particles along curve
            const numP = Math.max(3, Math.floor(curve.getLength() / 1.8));
            for (let i = 0; i < numP; i++) {{
                const pSphere = new THREE.Mesh(new THREE.SphereGeometry(pdef.radius * 1.35, 8, 8), new THREE.MeshBasicMaterial({{ color: 0xffffff }}));
                plantGroup.add(pSphere);
                particleFlows.push({{
                    mesh: pSphere,
                    curve: curve,
                    progress: i / numP,
                    speed: 0.0035 + (0.002 * (1 / (curve.getLength() || 1)))
                }});
            }}
        }});

        // ══════════════════════════════════════════════════════════════════════
        // CAMERA NAVIGATION & PRESETS
        // ══════════════════════════════════════════════════════════════════════
        function setPreset(mode) {{
            if (mode === 'pfd') {{
                // True PFD Ortho-style view
                camera.position.set(-8, 38, 42);
                controls.target.set(-8, 3, 8);
            }} else if (mode === 'iso') {{
                // Isometric Biorefinery View
                camera.position.set(30, 32, 38);
                controls.target.set(-4, 3, 8);
            }} else if (mode === 'front') {{
                // Front Process Elevation
                camera.position.set(-8, 12, 50);
                controls.target.set(-8, 5, 8);
            }} else if (mode === 'top') {{
                // Top Down Plan
                camera.position.set(-8, 65, 8.1);
                controls.target.set(-8, 0, 8);
            }}
            controls.update();
        }}

        if (isSingleMode && eqObjects[targetId]) {{
            const obj = eqObjects[targetId];
            const p = obj.position;
            camera.position.set(p.x + 8, p.y + 6, p.z + 10);
            controls.target.set(p.x, p.y + 3, p.z);
        }} else {{
            camera.position.set(-8, 32, 45);
            controls.target.set(-8, 3, 8);
        }}
        controls.update();

        // ══════════════════════════════════════════════════════════════════════
        // RENDER LOOP & RESIZE
        // ══════════════════════════════════════════════════════════════════════
        function animate() {{
            requestAnimationFrame(animate);

            // Execute custom unit animations (rotors, impellers, drums)
            animators.forEach(fn => fn());

            // Animate piping flow particles
            particleFlows.forEach(pf => {{
                pf.progress += pf.speed;
                if (pf.progress > 1.0) pf.progress = 0.0;
                const pt = pf.curve.getPointAt(pf.progress);
                pf.mesh.position.copy(pt);
            }});

            controls.update();
            renderer.render(scene, camera);
        }}
        animate();

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}, false);
    </script>
</body>
</html>
"""
    return html


def render_3d_plant_section(dm: Any = None):
    """Renders the comprehensive 3D Process Plant & Digital Twin engineering suite."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #0d47a1 0%, #1565c0 50%, #0277bd 100%); padding: 1.2rem 1.6rem; border-radius: 10px; color: white; margin-bottom: 1.2rem; box-shadow: 0 4px 15px rgba(2, 119, 189, 0.2);">
        <div style="font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em;">🏭 3D Process Plant & Digital Twin</div>
        <div style="font-size: 0.85rem; color: #e1f5fe; margin-top: 0.2rem;">
            Industrial WebGL Process Engineering Explorer · Mechanical Equipment Assemblies · Live Simulation Telemetry Bus
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Control Bar
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 2])
    with ctrl_col1:
        view_mode = st.selectbox(
            "Visualization Mode",
            ["Full Plant Overview (PFD Layout)", "Focused Equipment Inspection"],
            key="w_3d_view_mode"
        )
    with ctrl_col2:
        eq_list = list(EQUIPMENT_METADATA.keys())
        selected_eq = st.selectbox(
            "Select Process Equipment",
            eq_list,
            format_func=lambda k: f"{k} — {EQUIPMENT_METADATA[k]['name']}",
            key="w_3d_eq_select"
        )
    with ctrl_col3:
        cutaway_toggle = st.checkbox("Internal Cutaway / Components View", value=True, key="w_3d_cutaway")

    # Main 3-Column Inspection Layout
    col_left, col_center, col_right = st.columns([1.1, 2.5, 1.4], gap="medium")

    # ──── LEFT: Equipment Directory & Process Stages ────
    with col_left:
        st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#1565c0; margin-bottom:0.4rem;'>PROCESS EQUIPMENT ROSTER</div>", unsafe_allow_html=True)
        for eid, meta in EQUIPMENT_METADATA.items():
            is_active = (eid == selected_eq)
            bg = "#e3f2fd" if is_active else "#ffffff"
            border = "2px solid #1565c0" if is_active else "1px solid #e2e8f0"
            st.markdown(f"""
            <div style="background:{bg}; border:{border}; border-radius:8px; padding:7px 10px; margin-bottom:6px; cursor:pointer;">
                <div style="font-weight:700; font-size:0.82rem; color:#1a202c;">{meta['icon']} {eid}: {meta['name']}</div>
                <div style="font-size:0.72rem; color:#718096;">{meta['stage']}</div>
            </div>
            """, unsafe_allow_html=True)

    # ──── CENTER: Interactive 3D WebGL Canvas ────
    with col_center:
        mode_param = "single_equipment" if "Focused" in view_mode else "full_plant"
        three_html = build_threejs_html(selected_eq, mode_param, cutaway_toggle)
        components.html(three_html, height=560, scrolling=False)
        st.caption("🎮 **3D Controls:** Left-click drag to rotate camera • Right-click drag to pan • Mouse-wheel to zoom. Preset buttons top right.")

    # ──── RIGHT: Live Telemetry & Mechanical Data ────
    with col_right:
        meta = EQUIPMENT_METADATA[selected_eq]
        st.markdown(f"#### {meta['icon']} {selected_eq}: {meta['name']}")
        st.caption(f"**Discipline:** {meta['stage']}")
        
        # Tabs for telemetry vs internals
        r_tab1, r_tab2, r_tab3 = st.tabs(["📊 Live Telemetry", "⚙️ Internals", "📖 Principle"])

        with r_tab1:
            telemetry = extract_equipment_telemetry(selected_eq, dm)
            st.markdown(f"<div style='font-size:0.75rem; font-weight:700; color:#2e7d32; margin-bottom:0.4rem;'>DATA BUS: {telemetry['status'].upper()}</div>", unsafe_allow_html=True)
            if telemetry["parameters"]:
                st.dataframe(pd.DataFrame(telemetry["parameters"]), hide_index=True, use_container_width=True)
            else:
                st.info("No active telemetry. Execute simulation to stream parameters.")

        with r_tab2:
            st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#4a5568;'>INTERNAL MECHANICAL ASSEMBLIES:</div>", unsafe_allow_html=True)
            for item in meta["internals"]:
                st.markdown(f"• **{item}**")

        with r_tab3:
            st.markdown("<div style='font-size:0.78rem; font-weight:700; color:#4a5568;'>WORKING MECHANISM:</div>", unsafe_allow_html=True)
            st.write(meta["working_principle"])
