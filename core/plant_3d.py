"""3D Process Plant & Digital Twin for HYACINTH-X.

Renders an interactive, WebGL/Three.js-powered 3D industrial biorefinery plant based on the
Process Flow Diagram (PFD) for Bioethanol Production from Water Hyacinth.
Includes:
- Full 3D Plant Overview with animated stream particles and equipment layout (T-101 to V-101)
- Individual 3D Equipment Inspection with cutaways, rotating impellers, trays, and heating jackets
- Real-time telemetry linkage with simulation output data (M01 to M05)
- Material stream property inspector
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
        "description": "Continuous agitated immersion tank for dislodging silt, sand, and surface contaminants from harvested water hyacinth using process wash water.",
        "icon": "🚿",
        "internals": ["Cylindrical Shell", "Vertical Agitator Shaft", "Radial Marine Impeller", "Silt Bottom Drain", "Wash Water Spray Ring"],
        "working_principle": "Raw harvested water hyacinth is immersed in wash water agitated by a variable-speed impeller. High-shear fluid motion strips extraneous detritus while hydraulic pumps transfer washing effluent to biological treatment.",
        "status_color": "#2e7d32"
    },
    "D-101": {
        "name": "Biomass Dryer",
        "stage": "Feedstock Preparation",
        "description": "Rotary/screw thermal conduction dryer utilizing low-pressure plant steam to reduce feedstock moisture from ~90% wet basis down to ~10%.",
        "icon": "🔥",
        "internals": ["Steam Jacket", "Conveying Flight Screw", "Vapor Exhaust Hood", "Condensate Trap", "Biomass Discharge Rotary Valve"],
        "working_principle": "Washed water hyacinth passes through a heated thermal screw conveyor. Thermal energy provides sensible heating of liquid and latent heat of vaporization (2.257 MJ/kg), evaporating free moisture prior to mechanical comminution.",
        "status_color": "#e65100"
    },
    "M-101": {
        "name": "Milling Unit",
        "stage": "Feedstock Preparation",
        "description": "Rotary hammer/knife mill for mechanical particle size reduction of dried water hyacinth fibers to enhance specific surface area for chemical attack.",
        "icon": "⚙️",
        "internals": ["Feed Hopper", "Heavy-Duty Rotor Assembly", "Replaceable Impact Hammers", "Perforated Sizing Screen", "Cyclone Air Classifier"],
        "working_principle": "Dried plant stalks undergo high-velocity impact with rotating hardened steel hammers. Particles exit through classified sieve screens at specified mesh sizes (<2 mm), maximizing accessibility for liquid pretreatment.",
        "status_color": "#546e7a"
    },
    "T-102": {
        "name": "Slurry Tank",
        "stage": "Pretreatment Preparation",
        "description": "Continuous stirred tank where milled biomass is blended with recycled process water and dilute sulfuric acid (H2SO4) to establish the targeted Liquid-to-Solid Ratio (LSR).",
        "icon": "🧪",
        "internals": ["Acid-Resistant Clad Tank", "Dual-Stage Axial Hydrofoil", "Acid Dosing Dip Tube", "Water Recirculation Header", "Vortex Breakers"],
        "working_principle": "Milled biomass, fresh/recycled water, and catalytic sulfuric acid are vigorously homogenized into an 8:1 liquid-to-solid pumpable slurry, ensuring uniform thermal conductivity and mass transfer in the downstream reactor.",
        "status_color": "#0288d1"
    },
    "R-101": {
        "name": "Pretreatment Reactor",
        "stage": "Thermochemical Fractionation",
        "description": "High-pressure, steam-jacketed continuous stirred reactor for dilute-acid thermochemical deconstruction of hemicellulose and lignin disruption.",
        "icon": "⚗️",
        "internals": ["Pressure Vessel Shell", "Thermal Steam Jacket", "Anchor Agitator with Scrapers", "Thermowell Sensor Array", "Bottom Flash Discharge Nozzle"],
        "working_principle": "Operates at 120°C. Dilute acid cleaves ester and glycosidic bonds within hemicellulose, hydrolyzing ~7% into soluble oligomers while retaining ~90% of insoluble cellulose-rich fibers for enzymatic conversion.",
        "status_color": "#c62828"
    },
    "F-101": {
        "name": "Filter Press",
        "stage": "Solid-Liquid Separation",
        "description": "Recessed-chamber membrane filter press for separating insoluble pretreated cellulose-rich cake from the acidic liquid hydrolysate liquor.",
        "icon": "📦",
        "internals": ["Filter Plate Stack", "Recessed Filter Chambers", "Polypropylene Filter Cloths", "Hydraulic Clamping Ram", "Filtrate Manifold Launders"],
        "working_principle": "Pretreated slurry is pumped under hydraulic pressure through woven filter cloths. Liquid liquor drains into the filtrate manifold, while dewatered cellulosic cake is mechanically discharged from opening plates.",
        "status_color": "#455a64"
    },
    "E-101": {
        "name": "Bioreactor / Fermenter",
        "stage": "Enzymatic Hydrolysis & Fermentation",
        "description": "Large-scale aseptic jacketed bioconversion vessel where cellulase enzymes depolymerize glucan and yeast converts free sugars to bioethanol.",
        "icon": "🧬",
        "internals": ["Aseptic 316L Stainless Shell", "Multi-Tier Rushton Impellers", "Internal Cooling Coils", "CO2 Vent & Foam Breaker", "Enzyme/Yeast Inoculation Ports"],
        "working_principle": "Cellulase enzymes cleave anhydroglucose rings (adding +11.1% hydration water), releasing glucose. S. cerevisiae metabolizes hexoses into ethanol and CO2 following Gay-Lussac reaction stoichiometry (0.5114 g/g yield).",
        "status_color": "#2e7d32"
    },
    "S-101": {
        "name": "Clarification Centrifuge",
        "stage": "Broth Clarification",
        "description": "Continuous disc-stack centrifuge for separating spent yeast cells and insoluble particulate solids from the dilute ethanol-bearing beer broth.",
        "icon": "🌀",
        "internals": ["Rotating Centrifuge Bowl", "Disc Stack Assembly", "Sludge Discharge Ports", "Centripetal Liquid Pump", "Vibration Isolating Bearings"],
        "working_principle": "Generating up to 8,000 g centrifugal force, high-density yeast cell mass and insoluble lignaceous fines migrate to the bowl periphery and are intermittently ejected, yielding a clear beer broth feed for distillation.",
        "status_color": "#00838f"
    },
    "C-101": {
        "name": "Distillation Column",
        "stage": "Thermal Separation",
        "description": "Multi-stage fractional distillation column equipped with sieve trays, thermosiphon reboiler, and overhead reflux condenser to concentrate ethanol.",
        "icon": "🏛️",
        "internals": ["Perforated Sieve Trays", "Downcomers and Weirs", "Thermosiphon Steam Reboiler", "Total Condenser & Reflux Drum", "Stillage Bottoms Sump"],
        "working_principle": "Steam vaporizes volatile ethanol from the 5 vol% broth. Counter-current vapor-liquid contact enriches ethanol overhead toward the azeotrope (~92-95 wt%), while alcohol-free stillage discharges at the base.",
        "status_color": "#1565c0"
    },
    "V-101": {
        "name": "Molecular Sieve Dehydration",
        "stage": "Product Purification",
        "description": "Twin-bed pressure swing adsorption (PSA) zeolite molecular sieve system producing anhydrous fuel bioethanol (>99.5% purity).",
        "icon": "💎",
        "internals": ["Twin Adsorption Columns", "Zeolite 3A Molecular Sieve Bed", "Switching Control Valves", "Superheater Exchanger", "Dry Product Surge Tank"],
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
        # Washing Tank
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
        # Dryer
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
        # Milling Unit
        mill_power = [r[1] for r in r3.get("electric_rows", []) if "Mill" in r[0]]
        params = [
            {"Parameter": "Dry Biomass Throughput", "Value": f"{r1.get('dry_biomass_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M01 Output"},
            {"Parameter": "Milling Specific Energy", "Value": f"{m3_params.get('milling_kwh_per_t', 25.0):.1f}", "Unit": "kWh / tonne dry", "Source": "M03 Design Spec"},
            {"Parameter": "Milling Electrical Load", "Value": f"{mill_power[0] if mill_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "Operating Mechanism", "Value": "Rotary Knife / Hammer Comminution", "Unit": "-", "Source": "Process Design"}
        ]

    elif eq_id == "T-102":
        # Slurry Tank
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
        # Pretreatment Reactor
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
        # Filter Press
        filter_power = [r[1] for r in r3.get("electric_rows", []) if "Filter press" in r[0]]
        resid_solids = mb.get("residual_solids_kg", 0.0)
        params = [
            {"Parameter": "Insoluble Residual Solids", "Value": f"{resid_solids:,.1f}", "Unit": "kg/day", "Source": "M02/M04 Balance"},
            {"Parameter": "Wastewater Slurry Filtrate", "Value": f"{r3.get('slurry_liquid_kg_day', 0):,.1f}", "Unit": "kg/day", "Source": "M03/M04 Flow"},
            {"Parameter": "Filter Press Power Demand", "Value": f"{filter_power[0] if filter_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "Separation Principle", "Value": "Recessed Membrane Pressure Filtration", "Unit": "-", "Source": "Industrial Design"}
        ]

    elif eq_id == "E-101":
        # Fermenter
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
        # Centrifuge
        broth_vol = r3.get("broth_volume_m3_day", 0.0)
        cent_power = [r[1] for r in r3.get("electric_rows", []) if "Centrifuge" in r[0]]
        params = [
            {"Parameter": "Fermentation Broth Throughput", "Value": f"{broth_vol:,.2f}", "Unit": "m³/day", "Source": "M03 Hydraulic Basis"},
            {"Parameter": "Broth Ethanol Concentration", "Value": f"{m3_params.get('broth_ethanol_vol_pct', 5.0):.1f}", "Unit": "vol %", "Source": "M03 Design Spec"},
            {"Parameter": "Centrifuge Electrical Load", "Value": f"{cent_power[0] if cent_power else 0:.2f}", "Unit": "kWh/day", "Source": "M03 Calculation"},
            {"Parameter": "Separation Mechanism", "Value": "Continuous Disc-Stack Centrifugation", "Unit": "-", "Source": "Process Design"}
        ]

    elif eq_id == "C-101":
        # Distillation Column
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
        # Molecular Sieve Dehydration
        dehyd_mj = [r[1] for r in r3.get("thermal_rows", []) if "Dehydration" in r[0]]
        annual_l = r5.get("quantities", {}).get("ethanol_l_year", 0.0)
        params = [
            {"Parameter": "Anhydrous Fuel Ethanol (>99.5%)", "Value": f"{r3.get('ethanol_l_day', 0):,.1f}", "Unit": "L/day", "Source": "Final Product Stream"},
            {"Parameter": "Annual Plant Production", "Value": f"{annual_l:,.0f}", "Unit": "L/year", "Source": "M05 Economic Basis"},
            {"Parameter": "Dehydration Energy Intensity", "Value": f"{m3_params.get('dehydration_mj_per_l_ethanol', 1.5):.2f}", "Unit": "MJ / L ethanol", "Source": "M03 Molecular Sieve"},
            {"Parameter": "Thermal Duty", "Value": f"{dehyd_mj[0] if dehyd_mj else 0:,.1f}", "Unit": "MJ/day", "Source": "M03 Thermal Balance"}
        ]

    return {"status": "Live Simulation Linked", "parameters": params}


def build_threejs_html(selected_eq_id: str, view_mode: str = "full_plant", cutaway: bool = False) -> str:
    """Generates standalone Three.js WebGL HTML visualization matching industrial engineering standards."""
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background-color: #0d1117; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            #canvas-container {{ width: 100vw; height: 100vh; position: absolute; top: 0; left: 0; }}
            #hud {{
                position: absolute; top: 15px; left: 15px;
                background: rgba(13, 17, 23, 0.85); backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 8px;
                padding: 10px 16px; color: #e6edf3; font-size: 13px; z-index: 100;
                pointer-events: none;
            }}
            #hud h4 {{ margin: 0 0 4px 0; font-size: 14px; color: #58a6ff; font-weight: 600; }}
            #instructions {{
                position: absolute; bottom: 15px; right: 15px;
                background: rgba(13, 17, 23, 0.8); border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px; padding: 8px 12px; color: #8b949e; font-size: 11px;
                pointer-events: none;
            }}
            .tag {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 600; font-size: 10px; }}
            .tag-solid {{ background: #2e7d32; color: #fff; }}
            .tag-liq {{ background: #0288d1; color: #fff; }}
            .tag-vap {{ background: #e65100; color: #fff; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="canvas-container"></div>
        <div id="hud">
            <h4>🌿 HYACINTH-X Digital Twin 3D View</h4>
            <div id="view-mode-label">Mode: {view_mode.replace('_', ' ').title()} &nbsp;|&nbsp; Target: <b>{selected_eq_id}</b></div>
        </div>
        <div id="instructions">
            🖱️ Left Drag: Rotate • Right Drag: Pan • Scroll: Zoom • Click Equipment to Inspect
        </div>

        <script>
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x0f141c);
            scene.fog = new THREE.FogExp2(0x0f141c, 0.012);

            const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2 + 0.05;

            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.65);
            scene.add(ambientLight);

            const dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
            dirLight.position.set(25, 45, 30);
            dirLight.castShadow = true;
            dirLight.shadow.mapSize.width = 2048;
            dirLight.shadow.mapSize.height = 2048;
            scene.add(dirLight);

            const fillLight = new THREE.DirectionalLight(0x64b5f6, 0.35);
            fillLight.position.set(-30, 20, -25);
            scene.add(fillLight);

            // Ground Floor Grid
            const gridHelper = new THREE.GridHelper(90, 45, 0x1f6feb, 0x21262d);
            gridHelper.position.y = -0.05;
            scene.add(gridHelper);

            // Materials
            const matSteel = new THREE.MeshStandardMaterial({{ color: 0x90a4ae, metalness: 0.85, roughness: 0.25 }});
            const matDarkSteel = new THREE.MeshStandardMaterial({{ color: 0x37474f, metalness: 0.9, roughness: 0.3 }});
            const matCopper = new THREE.MeshStandardMaterial({{ color: 0xd87d4a, metalness: 0.7, roughness: 0.3 }});
            const matGlass = new THREE.MeshPhysicalMaterial({{ color: 0xe0f7fa, transparent: true, opacity: 0.35, roughness: 0.1, transmission: 0.7 }});
            const matHighlight = new THREE.MeshStandardMaterial({{ color: 0x00e676, emissive: 0x00e676, emissiveIntensity: 0.3, metalness: 0.5, roughness: 0.2 }});
            
            // Equipment definitions with 3D models
            const equipmentGroup = new THREE.Group();
            scene.add(equipmentGroup);

            const eqObjects = {{}};
            const animators = [];

            // Factory builders for 3D equipment
            function makeTank(id, x, z, h=5, r=1.8, color=0x90a4ae) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, h/2, z);

                const geo = new THREE.CylinderGeometry(r, r, h, 32);
                const mat = (id === '{selected_eq_id}') ? matHighlight : new THREE.MeshStandardMaterial({{ color: color, metalness: 0.8, roughness: 0.3 }});
                const body = new THREE.Mesh(geo, mat);
                body.castShadow = true;
                group.add(body);

                // Top & Bottom Dish Heads
                const dishGeo = new THREE.SphereGeometry(r, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2);
                const topDish = new THREE.Mesh(dishGeo, mat);
                topDish.position.y = h/2;
                group.add(topDish);

                // Legs
                for(let i=0; i<4; i++) {{
                    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 1.2), matDarkSteel);
                    const ang = (i * Math.PI) / 2;
                    leg.position.set(Math.cos(ang)*(r-0.2), -h/2 - 0.5, Math.sin(ang)*(r-0.2));
                    group.add(leg);
                }}

                // Internal Impeller if inspecting
                const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, h*0.8), matDarkSteel);
                shaft.position.y = 0;
                group.add(shaft);

                const bladeGeo = new THREE.BoxGeometry(r*1.2, 0.1, 0.3);
                const blade = new THREE.Mesh(bladeGeo, matCopper);
                blade.position.y = -h*0.25;
                group.add(blade);

                animators.push(() => {{ blade.rotation.y += 0.04; shaft.rotation.y += 0.04; }});

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeDryer(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 2, z);

                const shell = new THREE.Mesh(new THREE.CylinderGeometry(1.4, 1.4, 8, 32), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                shell.rotation.z = Math.PI / 2;
                shell.castShadow = true;
                group.add(shell);

                // Internal Screw Conveyor
                const screw = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 7.8, 16), matCopper);
                screw.rotation.z = Math.PI / 2;
                group.add(screw);

                animators.push(() => {{ shell.rotation.x += 0.02; screw.rotation.x += 0.05; }});

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeMill(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 2, z);

                const base = new THREE.Mesh(new THREE.BoxGeometry(2.4, 1.8, 2.4), matDarkSteel);
                group.add(base);

                const hopper = new THREE.Mesh(new THREE.ConeGeometry(1.5, 2.0, 4), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                hopper.position.y = 1.9;
                group.add(hopper);

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeFilterPress(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 1.8, z);

                const frame = new THREE.Mesh(new THREE.BoxGeometry(5.5, 0.4, 2.0), matDarkSteel);
                frame.position.y = -1.0;
                group.add(frame);

                // Filter plates stack
                const platesGroup = new THREE.Group();
                for(let i=0; i<18; i++) {{
                    const pl = new THREE.Mesh(new THREE.BoxGeometry(0.12, 2.0, 1.8), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                    pl.position.x = -2.0 + (i * 0.23);
                    platesGroup.add(pl);
                }}
                group.add(platesGroup);

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeColumn(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 6.5, z);

                const mat = (id === '{selected_eq_id}') ? matHighlight : matSteel;
                const shell = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 12, 32), mat);
                shell.castShadow = true;
                group.add(shell);

                // Dished ends
                const topD = new THREE.Mesh(new THREE.SphereGeometry(1.2, 32, 16, 0, Math.PI * 2, 0, Math.PI / 2), mat);
                topD.position.y = 6.0;
                group.add(topD);

                // Internal Sieve Trays
                for(let t=0; t<14; t++) {{
                    const tray = new THREE.Mesh(new THREE.CylinderGeometry(1.15, 1.15, 0.08, 16), matCopper);
                    tray.position.y = -5.0 + (t * 0.75);
                    group.add(tray);
                }}

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeCentrifuge(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 2.2, z);

                const upper = new THREE.Mesh(new THREE.CylinderGeometry(1.3, 1.3, 1.8, 32), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                group.add(upper);

                const cone = new THREE.Mesh(new THREE.ConeGeometry(1.3, 1.8, 32), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                cone.rotation.x = Math.PI;
                cone.position.y = -1.4;
                group.add(cone);

                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            function makeDehydrator(id, x, z) {{
                const group = new THREE.Group();
                group.name = id;
                group.position.set(x, 3.5, z);

                // Twin Bed Columns
                for(let c of [-0.9, 0.9]) {{
                    const bed = new THREE.Mesh(new THREE.CylinderGeometry(0.7, 0.7, 6, 24), (id === '{selected_eq_id}') ? matHighlight : matSteel);
                    bed.position.x = c;
                    group.add(bed);
                }}
                equipmentGroup.add(group);
                eqObjects[id] = group;
                return group;
            }}

            // Reconstruct Plant Layout according to PFD coordinates
            makeTank("T-101", -26, 0, 4.5, 1.8, 0x81c784);       // Washing Tank
            makeDryer("D-101", -19, 0);                           // Dryer
            makeMill("M-101", -12, 0);                            // Milling
            makeTank("T-102", -5, 0, 5.0, 1.8, 0x64b5f6);         // Slurry Tank
            makeTank("R-101", 3, 0, 6.0, 2.0, 0xe57373);          // Pretreatment Reactor
            makeFilterPress("F-101", 11, 0);                      // Filter Press
            makeTank("E-101", 11, 14, 7.5, 2.6, 0x81c784);       // Bioreactor/Fermenter
            makeCentrifuge("S-101", 2, 14);                       // Centrifuge
            makeColumn("C-101", -9, 14);                          // Distillation Column
            makeDehydrator("V-101", -18, 14);                     // Molecular Sieve Dehydration

            // Animated Piping Material Streams
            const pipePoints = [
                // T-101 -> D-101
                [new THREE.Vector3(-26, 2, 0), new THREE.Vector3(-23, 2, 0)],
                // D-101 -> M-101
                [new THREE.Vector3(-15, 2, 0), new THREE.Vector3(-12, 2, 0)],
                // M-101 -> T-102
                [new THREE.Vector3(-12, 1, 0), new THREE.Vector3(-5, 1, 0)],
                // T-102 -> R-101
                [new THREE.Vector3(-5, 2, 0), new THREE.Vector3(3, 2, 0)],
                // R-101 -> F-101
                [new THREE.Vector3(3, 2, 0), new THREE.Vector3(8.5, 2, 0)],
                // F-101 -> E-101 (Liquid Hydrolysate)
                [new THREE.Vector3(13.5, 2, 0), new THREE.Vector3(18, 2, 0), new THREE.Vector3(18, 2, 14), new THREE.Vector3(13.6, 2, 14)],
                // E-101 -> S-101 (Beer Broth)
                [new THREE.Vector3(8.4, 2, 14), new THREE.Vector3(2, 2, 14)],
                // S-101 -> C-101 (Clarified Broth)
                [new THREE.Vector3(2, 2, 14), new THREE.Vector3(-9, 4, 14)],
                // C-101 -> V-101 (Ethanol Vapor)
                [new THREE.Vector3(-9, 10, 14), new THREE.Vector3(-14, 10, 14), new THREE.Vector3(-14, 4, 14), new THREE.Vector3(-18, 4, 14)]
            ];

            const pipeMat = new THREE.MeshStandardMaterial({{ color: 0x4fc3f7, metalness: 0.6, roughness: 0.2 }});
            pipePoints.forEach(pts => {{
                if(pts.length === 2) {{
                    const curve = new THREE.LineCurve3(pts[0], pts[1]);
                    const geom = new THREE.TubeGeometry(curve, 10, 0.14, 8, false);
                    scene.add(new THREE.Mesh(geom, pipeMat));
                }} else {{
                    const curve = new THREE.CatmullRomCurve3(pts);
                    const geom = new THREE.TubeGeometry(curve, 30, 0.14, 8, false);
                    scene.add(new THREE.Mesh(geom, pipeMat));
                }}
            }});

            // Camera Setup
            if ('{view_mode}' === 'single_equipment' && eqObjects['{selected_eq_id}']) {{
                const targetObj = eqObjects['{selected_eq_id}'];
                const p = targetObj.position;
                camera.position.set(p.x + 6, p.y + 4, p.z + 8);
                controls.target.set(p.x, p.y, p.z);
            }} else {{
                camera.position.set(-8, 26, 38);
                controls.target.set(-5, 3, 7);
            }}

            // Render loop
            function animate() {{
                requestAnimationFrame(animate);
                animators.forEach(fn => fn());
                controls.update();
                renderer.render(scene, camera);
            }}
            animate();

            // Window resize
            window.addEventListener('resize', onWindowResize, false);
            function onWindowResize() {{
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            }}
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
            Interactive WebGL Process Engineering Explorer · Internal Equipment Cutaways · Live Simulation Telemetry Bus
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
        components.html(three_html, height=520, scrolling=False)
        st.caption("🎮 **3D Controls:** Left-click drag to rotate camera • Right-click drag to pan • Mouse-wheel to zoom.")

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
