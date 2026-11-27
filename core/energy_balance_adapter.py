"""Isolated Read-Only Energy Balance Visualization Adapter for HYACINTH-X 3D Digital Twin.

Bridges existing M03 energy outputs and thermodynamic continuity to 3D equipment
and process streams without altering core simulation calculations.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd

from core.material_balance import compute_all_streams, compute_equipment_material_balance, ProcessStream


@dataclass
class StreamEnergyData:
    """Thermodynamic energy properties for a process stream."""
    stream_id: str
    mass_flow_kg_h: float
    temp_c: float
    pressure_bar: float
    phase: str
    specific_heat_kj_kg_k: float
    specific_enthalpy_kj_kg: float
    energy_flow_kw: float
    energy_flow_mj_h: float
    status: str = "Calculated"  # "Simulated", "Calculated", "Unavailable"


@dataclass
class EquipmentEnergyBalance:
    """First-law energy balance for an individual process unit."""
    eq_id: str
    name: str
    category: str
    thermal_duty_mj_day: float
    thermal_duty_mj_h: float
    thermal_duty_kw: float
    electric_duty_kwh_day: float
    electric_duty_kw: float
    steam_consumption_kg_h: float
    steam_consumption_kg_day: float
    inlet_temp_c: float
    outlet_temp_c: float
    inflow_enthalpy_kw: float
    outflow_enthalpy_kw: float
    heat_loss_kw: float
    energy_residual_kw: float
    energy_type: str  # Thermal Consumer, Thermal Generator, Electrical Mechanical, Ambient
    color_indicator: str  # Hex code for 3D overlay
    governing_equation: str
    assumptions: List[str]
    energy_table: pd.DataFrame = field(default_factory=pd.DataFrame)


# Specific heat capacities at 25-100 °C (kJ/kg·K)
CP_WATER = 4.184
CP_ETHANOL = 2.44
CP_DRY_BIOMASS = 1.54
CP_STEAM = 2.01
CP_CO2 = 0.85
LATENT_HEAT_WATER_VAP_KJ_KG = 2260.0
LATENT_HEAT_ETHANOL_VAP_KJ_KG = 841.0
T_REF_C = 0.0  # Reference temperature for enthalpy


def compute_stream_energy(stream: ProcessStream) -> StreamEnergyData:
    """Computes enthalpy and energy flow for a given process stream."""
    m_dot_kg_h = stream.mass_flow_kg_h
    t_c = stream.temp_c
    delta_t = t_c - T_REF_C

    # Compute mixture specific heat capacity Cp (kJ/kg·K)
    w_frac = stream.moisture_pct / 100.0
    dm_frac = stream.solids_pct / 100.0
    eth_frac = 0.0

    if stream.component_fractions:
        for comp, frac in stream.component_fractions.items():
            if "ethanol" in comp.lower():
                eth_frac = frac / 100.0

    rem_frac = max(0.0, 1.0 - w_frac - eth_frac)
    cp_mix = (w_frac * CP_WATER) + (eth_frac * CP_ETHANOL) + (rem_frac * CP_DRY_BIOMASS)

    if stream.category == "gas" or "co2" in stream.id.lower():
        cp_mix = CP_CO2
    elif stream.category == "steam" or stream.phase.lower() == "steam":
        cp_mix = CP_STEAM

    # Enthalpy h (kJ/kg)
    sensible_h = cp_mix * delta_t
    latent_h = 0.0

    if stream.phase.lower() in ("gas", "vapour", "steam") or stream.category in ("gas", "steam"):
        if "ethanol" in stream.name.lower():
            latent_h = LATENT_HEAT_ETHANOL_VAP_KJ_KG
        else:
            latent_h = LATENT_HEAT_WATER_VAP_KJ_KG

    total_h = sensible_h + latent_h

    # Energy flow rate: kW = (kg/h * kJ/kg) / 3600
    energy_kw = (m_dot_kg_h * total_h) / 3600.0
    energy_mj_h = (m_dot_kg_h * total_h) / 1000.0

    return StreamEnergyData(
        stream_id=stream.id,
        mass_flow_kg_h=m_dot_kg_h,
        temp_c=t_c,
        pressure_bar=stream.pressure_bar,
        phase=stream.phase,
        specific_heat_kj_kg_k=round(cp_mix, 3),
        specific_enthalpy_kj_kg=round(total_h, 2),
        energy_flow_kw=round(energy_kw, 2),
        energy_flow_mj_h=round(energy_mj_h, 2),
        status="Calculated" if m_dot_kg_h > 0 else "Unavailable",
    )


def compute_all_stream_energies(dm: Any = None) -> Dict[str, StreamEnergyData]:
    """Computes energy flow data for all 22 plant streams."""
    streams = compute_all_streams(dm)
    return {sid: compute_stream_energy(s) for sid, s in streams.items()}


def compute_equipment_energy_balance(eq_id: str, dm: Any = None) -> EquipmentEnergyBalance:
    """Computes first-law energy balance for an individual equipment unit using M03 outputs."""
    from core.plant_3d import EQUIPMENT_METADATA

    # Extract M03 results safely
    m03 = dm.results.get("M03", {}) if (dm and hasattr(dm, "results")) else {}
    thermal_rows = dict([(r[0], r[1]) for r in m03.get("thermal_rows", [])]) if m03 else {}
    electric_rows = dict([(r[0], r[1]) for r in m03.get("electric_rows", [])]) if m03 else {}

    meta = EQUIPMENT_METADATA.get(eq_id, {"name": eq_id, "stage": "Process"})
    name = meta["name"]

    # Match thermal and electrical duties to equipment
    thermal_mj_d = 0.0
    electric_kwh_d = 0.0
    steam_kg_h = 0.0
    in_temp = 25.0
    out_temp = 25.0
    energy_type = "Ambient / Minimal"
    color = "#9e9e9e"
    eq_formula = r"\sum \dot{H}_{\text{in}} + \dot{Q} + \dot{W}_e = \sum \dot{H}_{\text{out}} + \dot{Q}_{\text{loss}}"
    assumptions = [
        "First Law of Thermodynamics steady-state formulation.",
        "Kinetic and potential energy terms are negligible.",
        "Reference state: liquid water at 0.0 °C and 1.013 bar.",
    ]

    if eq_id == "T-101":
        # Washing tank: hydraulic pump duty
        electric_kwh_d = electric_rows.get("Washing pump (T-101 service)", 0.19)
        in_temp, out_temp = 20.0, 22.0
        energy_type = "Hydraulic Pumping"
        color = "#0288d1"
        assumptions.append("Hydraulic pump efficiency assumed at 75%.")

    elif eq_id == "D-101":
        # Biomass dryer: high thermal evaporation duty
        thermal_mj_d = thermal_rows.get("Dryer (D-101)", 3926.06)
        in_temp, out_temp = 23.0, 65.0
        energy_type = "Thermal Evaporative Consumer"
        color = "#ff5722"  # Bright Orange/Red
        assumptions.append("Thermal convective air drying reducing moisture from 85.2% to 12.0%.")
        assumptions.append("Latent heat of vaporization: 2,260 kJ/kg H2O.")

    elif eq_id == "M-101":
        # Hammer mill: mechanical grinding power
        electric_kwh_d = electric_rows.get("Mill (M-101)", 3.75)
        in_temp, out_temp = 65.0, 40.0
        energy_type = "Mechanical Size Reduction"
        color = "#ffb300"  # Amber/Yellow
        assumptions.append("Specific milling electricity: 25.0 kWh/tonne dry matter.")

    elif eq_id == "T-102":
        # Slurry mixing tank: mechanical agitator power
        electric_kwh_d = electric_rows.get("Slurry tank mixer (T-102)", 8.00)
        in_temp, out_temp = 25.0, 32.0
        energy_type = "Mechanical Agitation"
        color = "#ffb300"
        assumptions.append("Continuous turbine agitation power dissipation.")

    elif eq_id == "R-101":
        # Jacketed hydrothermal reactor: high thermal steam heating
        thermal_mj_d = thermal_rows.get("Pretreatment reactor (R-101)", 1248.22)
        # 1,248.22 MJ/day / (2.1 MJ/kg latent steam) ~ 594 kg steam/day = 24.8 kg steam/h
        steam_kg_h = (thermal_mj_d / 24.0) / 2.100  # ~24.77 kg/h
        in_temp, out_temp = 32.0, 140.0
        energy_type = "Thermal Reaction & Steam Heating"
        color = "#d50000"  # Vivid Red
        assumptions.append("Saturated heating steam at 6.0 bar, 160.0 °C.")
        assumptions.append("Heat duty accounts for slurry sensible heat + 15% thermal hold/jacket dissipation allowance.")

    elif eq_id == "F-101":
        # Rotary vacuum filter: vacuum pump & drum drive
        electric_kwh_d = electric_rows.get("Filter press", 6.75)
        in_temp, out_temp = 140.0, 50.0  # Quenched / cooled
        energy_type = "Mechanical Filtration & Vacuum"
        color = "#ffb300"
        assumptions.append("Vacuum pump electricity: 5.0 kWh/tonne slurry.")

    elif eq_id == "E-101":
        # Bioreactor / Fermenter: exothermic fermentation heat + agitation
        electric_kwh_d = electric_rows.get("Fermenter agitation (F-101)", 0.99)
        thermal_mj_d = thermal_rows.get("Fermenter cooling (F-101)", 0.0)
        in_temp, out_temp = 50.0, 32.0
        energy_type = "Exothermic Biological / Agitation"
        color = "#00bcd4"  # Cyan Cooling
        assumptions.append("Exothermic ethanolic fermentation heat generation: -58.8 kJ/mol glucose.")
        assumptions.append("Chilled cooling water jacket removes metabolic heat to maintain broth at 32.0 °C.")

    elif eq_id == "S-101":
        # Decanter centrifuge: centrifugal drive
        electric_kwh_d = electric_rows.get("Centrifuge (S-101)", 0.49)
        in_temp, out_temp = 32.0, 32.0
        energy_type = "Centrifugal Separation Drive"
        color = "#ffb300"
        assumptions.append("Centrifuge drive power: 1.5 kWh/m³ broth.")

    elif eq_id == "C-101":
        # Distillation column: reboiler steam thermal duty
        thermal_mj_d = thermal_rows.get("Distillation column (C-101)", 698.56)
        steam_kg_h = (thermal_mj_d / 24.0) / 2.150  # ~13.5 kg steam/h
        in_temp, out_temp = 32.0, 102.0
        energy_type = "Thermal Reboiler Consumer"
        color = "#ff5722"  # Thermal Orange/Red
        assumptions.append("Reboiler steam heating dilute beer to boiling points of ethanol-water mixtures.")
        assumptions.append("Reboiler thermal duty derived from specific enthalpy of vaporization.")

    elif eq_id == "V-101":
        # Molecular sieve dehydrator: regeneration thermal duty
        thermal_mj_d = thermal_rows.get("Dehydration", 24.74)
        in_temp, out_temp = 78.2, 80.0
        energy_type = "Adsorption Bed Regeneration"
        color = "#ff7043"
        assumptions.append("Thermal desorption and regeneration of 3A zeolite adsorbent bed.")

    thermal_mj_h = thermal_mj_d / 24.0
    thermal_kw = (thermal_mj_d * 1000.0) / 86400.0  # MJ/d -> kW
    electric_kw = electric_kwh_d / 24.0

    # Stream enthalpies
    mb = compute_equipment_material_balance(eq_id, dm)
    in_energies = [compute_stream_energy(s) for s in mb.inflow_streams]
    out_energies = [compute_stream_energy(s) for s in mb.outflow_streams]

    h_in_kw = sum(e.energy_flow_kw for e in in_energies)
    h_out_kw = sum(e.energy_flow_kw for e in out_energies)

    # First-law balance residual: H_in + Q_th + W_elec - H_out - Q_loss = 0
    heat_loss_kw = round(thermal_kw * 0.05, 2)  # 5% insulation / radiation allowance
    energy_residual_kw = round(h_in_kw + thermal_kw + electric_kw - h_out_kw - heat_loss_kw, 2)

    # Energy table
    energy_rows = [
        {"Parameter": "Thermal Duty", "Daily (MJ/d)": f"{thermal_mj_d:,.2f}", "Rate (kW)": f"{thermal_kw:.2f}", "Provenance": "M03 Simulation"},
        {"Parameter": "Electrical Power", "Daily (kWh/d)": f"{electric_kwh_d:,.2f}", "Rate (kW)": f"{electric_kw:.2f}", "Provenance": "M03 Simulation"},
        {"Parameter": "Process Steam", "Daily (kg/d)": f"{steam_kg_h * 24.0:,.1f}", "Rate (kg/h)": f"{steam_kg_h:.2f}", "Provenance": "Thermodynamic Derived"},
        {"Parameter": "Inlet Stream Enthalpy", "Daily (MJ/d)": f"{h_in_kw * 86.4:,.1f}", "Rate (kW)": f"{h_in_kw:.2f}", "Provenance": "Sensible Heat Balance"},
        {"Parameter": "Outlet Stream Enthalpy", "Daily (MJ/d)": f"{h_out_kw * 86.4:,.1f}", "Rate (kW)": f"{h_out_kw:.2f}", "Provenance": "Sensible Heat Balance"},
        {"Parameter": "Ambient Heat Loss (Est.)", "Daily (MJ/d)": f"{heat_loss_kw * 86.4:,.1f}", "Rate (kW)": f"{heat_loss_kw:.2f}", "Provenance": "5% Shell Radiation"},
    ]

    return EquipmentEnergyBalance(
        eq_id=eq_id,
        name=name,
        category=meta["stage"],
        thermal_duty_mj_day=round(thermal_mj_d, 2),
        thermal_duty_mj_h=round(thermal_mj_h, 2),
        thermal_duty_kw=round(thermal_kw, 2),
        electric_duty_kwh_day=round(electric_kwh_d, 2),
        electric_duty_kw=round(electric_kw, 2),
        steam_consumption_kg_h=round(steam_kg_h, 2),
        steam_consumption_kg_day=round(steam_kg_h * 24.0, 2),
        inlet_temp_c=in_temp,
        outlet_temp_c=out_temp,
        inflow_enthalpy_kw=round(h_in_kw, 2),
        outflow_enthalpy_kw=round(h_out_kw, 2),
        heat_loss_kw=heat_loss_kw,
        energy_residual_kw=energy_residual_kw,
        energy_type=energy_type,
        color_indicator=color,
        governing_equation=eq_formula,
        assumptions=assumptions,
        energy_table=pd.DataFrame(energy_rows),
    )


def compute_plant_energy_balance(dm: Any = None) -> Dict[str, Any]:
    """Computes overall facility-wide thermal, electrical and heat recovery energy balance."""
    m03 = dm.results.get("M03", {}) if (dm and hasattr(dm, "results")) else {}

    gross_thermal_mj_d = m03.get("gross_thermal_mj_day", 5897.58)
    net_thermal_mj_d = m03.get("net_thermal_mj_day", 5702.90)
    recovered_heat_mj_d = m03.get("recovered_heat_mj_day", 194.68)
    electric_kwh_d = m03.get("electric_kwh_day", 30.17)
    specific_energy_kwh_l = m03.get("energy_kwh_per_l", 97.87)

    return {
        "gross_thermal_mj_day": gross_thermal_mj_d,
        "gross_thermal_kw": (gross_thermal_mj_d * 1000.0) / 86400.0,
        "net_thermal_mj_day": net_thermal_mj_d,
        "net_thermal_kw": (net_thermal_mj_d * 1000.0) / 86400.0,
        "recovered_heat_mj_day": recovered_heat_mj_d,
        "recovered_heat_kw": (recovered_heat_mj_d * 1000.0) / 86400.0,
        "electric_kwh_day": electric_kwh_d,
        "electric_kw": electric_kwh_d / 24.0,
        "specific_energy_kwh_l": specific_energy_kwh_l,
        "heat_recovery_ratio_pct": (recovered_heat_mj_d / gross_thermal_mj_d * 100.0) if gross_thermal_mj_d else 0.0,
    }
