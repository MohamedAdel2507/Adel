"""Module 03 - PFD-Based Energy & Utilities Calculator (calculation logic).

Ported verbatim from legacy/hyacinth_x_module_03.py (constants + calculate_energy).
NOTE: despite the 'Downstream Processing' label in the project brief, this module calculates
per-equipment thermal/electrical demand and utility cost. It does NOT model ethanol purity,
separation efficiency or product losses; those are not reported anywhere in the platform.
"""
from __future__ import annotations

CP_WATER = 0.004186              # MJ/(kg.K)
CP_BIOMASS = 0.0015              # MJ/(kg.K), approximate dry biomass
LATENT_WATER = 2.257             # MJ/kg at ~100 C
RHO_WATER = 1000.0               # kg/m3
G = 9.81
ETHANOL_DENSITY = 0.789          # kg/L
MJ_PER_KWH = 3.6

def _nonnegative(x, name):
    x = float(x)
    if x < 0:
        raise ValueError(f"{name} cannot be negative.")
    return x

def calculate_energy(p: dict) -> dict:
    """Return per-equipment energy on a daily basis. Inputs use kg/day, m3/day, kWh/day."""
    dry = _nonnegative(p["dry_biomass_kg_day"], "Dry biomass")
    ethanol = _nonnegative(p["ethanol_kg_day"], "Ethanol production")
    m0 = float(p["initial_moisture_pct"]) / 100
    mt = float(p["target_moisture_pct"]) / 100
    if not (0 <= m0 < 1 and 0 <= mt < 1):
        raise ValueError("Moisture values must be from 0% to less than 100%.")
    if mt > m0:
        raise ValueError("Target moisture must not exceed initial moisture for a drying calculation.")

    # 1) Washing: pump hydraulic energy from flow and head.
    wash_water = _nonnegative(p["washing_water_m3_day"], "Washing water")
    head = _nonnegative(p["washing_pump_head_m"], "Pump head")
    pump_eff = float(p["washing_pump_eff_pct"]) / 100
    if not 0 < pump_eff <= 1: raise ValueError("Pump efficiency must be >0 and <=100%.")
    wash_kwh = (RHO_WATER * G * head * wash_water / pump_eff) / 3.6e6

    # 2) Drying: water removed from wet biomass, plus heating of solids and evaporated water.
    water_initial = dry * m0 / (1-m0) if m0 else 0.0
    water_target = dry * mt / (1-mt) if mt else 0.0
    water_removed = max(0.0, water_initial-water_target)
    t_in = float(p["dryer_inlet_temp_c"])
    t_evap = 100.0
    dryer_eff = float(p["dryer_eff_pct"])/100
    if not 0 < dryer_eff <= 1: raise ValueError("Dryer efficiency must be >0 and <=100%.")
    water_heat = water_removed * CP_WATER * max(0, t_evap-t_in)
    evaporation = water_removed * LATENT_WATER
    solids_heat = dry * CP_BIOMASS * max(0, t_evap-t_in)
    dryer_mj = (water_heat + evaporation + solids_heat) / dryer_eff

    # 3) Milling: specific electrical consumption per tonne dry feed.
    milling_kwh = dry/1000 * _nonnegative(p["milling_kwh_per_t"], "Milling intensity")

    # 4) Slurry tank: user-entered mixer electricity.
    slurry_kwh = _nonnegative(p["slurry_mixing_kwh_day"], "Slurry mixing energy")

    # 5) Pretreatment: sensible heating of biomass + process liquid from inlet to setpoint.
    lsr = _nonnegative(p["pretreatment_liquid_solid_ratio"], "Liquid-to-solid ratio")
    slurry_liquid = dry * lsr
    t_pre_in = float(p["pretreatment_inlet_temp_c"])
    t_pre = float(p["pretreatment_temp_c"])
    if t_pre < t_pre_in: raise ValueError("Pretreatment temperature must be >= inlet temperature.")
    pre_eff = float(p["pretreatment_heater_eff_pct"])/100
    if not 0 < pre_eff <= 1: raise ValueError("Pretreatment heater efficiency must be >0 and <=100%.")
    pre_sensible = (slurry_liquid*CP_WATER + dry*CP_BIOMASS) * (t_pre-t_pre_in)
    pre_allowance = _nonnegative(p["pretreatment_hold_loss_mj_day"], "Pretreatment hold/loss allowance")
    pretreatment_mj = (pre_sensible + pre_allowance)/pre_eff

    # 6) Filter press: specific electrical energy per tonne of incoming slurry.
    slurry_mass = dry + slurry_liquid
    filter_kwh = slurry_mass/1000 * _nonnegative(p["filter_press_kwh_per_t"], "Filter press intensity")

    # 7) Fermenter: agitation plus optional cooling duty.
    broth_volume = 0.0
    ethanol_l = ethanol / ETHANOL_DENSITY
    broth_pct = float(p["broth_ethanol_vol_pct"])
    if not 0 < broth_pct <= 100:
        raise ValueError("Broth ethanol concentration must be >0 and <=100 vol%.")
    broth_ethanol_fraction = broth_pct / 100.0
    if ethanol_l > 0:
        # Convert broth volume from Liters to m3 (1 m3 = 1000 L)
        broth_volume = (ethanol_l / broth_ethanol_fraction) / 1000.0
    fermenter_mix = broth_volume * _nonnegative(p["fermenter_mixing_kwh_m3"], "Fermenter mixing intensity")
    fermenter_cooling = _nonnegative(p["fermenter_cooling_mj_day"], "Fermenter cooling duty")

    # 8) Centrifuge: specific electrical energy per m3 broth.
    centrifuge_kwh = broth_volume * _nonnegative(p["centrifuge_kwh_per_m3"], "Centrifuge intensity")

    # 9) Distillation and 10) dehydration. Distillation basis is broth volume.
    dist_eff = float(p["distillation_heater_eff_pct"])/100
    if not 0 < dist_eff <= 1: raise ValueError("Distillation heater efficiency must be >0 and <=100%.")
    dist_mj = broth_volume * _nonnegative(p["distillation_mj_per_m3_broth"], "Distillation intensity") / dist_eff
    dehydration_mj = ethanol_l * _nonnegative(p["dehydration_mj_per_l_ethanol"], "Dehydration intensity")

    # Optional heat recovery applied only to the stated eligible thermal loads.
    recovery_pct = float(p["heat_recovery_pct"])/100
    if not 0 <= recovery_pct <= 1: raise ValueError("Heat recovery must be between 0% and 100%.")
    eligible = pretreatment_mj + dist_mj
    recovered = eligible * recovery_pct

    thermal_rows = [
        ("Dryer (D-101)", dryer_mj, "Evaporation + sensible heating"),
        ("Pretreatment reactor (R-101)", pretreatment_mj, "Slurry sensible heating + hold/loss allowance"),
        ("Fermenter cooling (F-101)", fermenter_cooling, "User-entered cooling duty; reported separately"),
        ("Distillation column (C-101)", dist_mj, "Specific energy × broth volume / heater efficiency"),
        ("Dehydration", dehydration_mj, "Specific energy × ethanol product volume"),
    ]
    gross_thermal = sum(x[1] for x in thermal_rows)
    net_thermal = gross_thermal - recovered
    electric_rows = [
        ("Washing pump (T-101 service)", wash_kwh, "Hydraulic pump estimate"),
        ("Mill (M-101)", milling_kwh, "Specific electricity × dry biomass"),
        ("Slurry tank mixer (T-102)", slurry_kwh, "User-entered daily mixer electricity"),
        ("Filter press", filter_kwh, "Specific electricity × slurry mass"),
        ("Fermenter agitation (F-101)", fermenter_mix, "Specific electricity × broth volume"),
        ("Centrifuge (S-101)", centrifuge_kwh, "Specific electricity × broth volume"),
        ("Other auxiliaries", _nonnegative(p["auxiliary_kwh_day"], "Auxiliary electricity"), "User-entered daily electricity"),
    ]
    total_electric = sum(x[1] for x in electric_rows)
    thermal_cost = net_thermal/MJ_PER_KWH * _nonnegative(p["thermal_price_per_kwh"], "Thermal price")
    electric_cost = total_electric * _nonnegative(p["electricity_price_per_kwh"], "Electricity price")
    total_cost = thermal_cost + electric_cost
    energy_kwh_equiv = net_thermal/MJ_PER_KWH + total_electric
    return {
        "ethanol_l_day": ethanol_l, "broth_volume_m3_day": broth_volume,
        "water_removed_kg_day": water_removed, "slurry_liquid_kg_day": slurry_liquid,
        "thermal_rows": thermal_rows, "electric_rows": electric_rows,
        "gross_thermal_mj_day": gross_thermal, "recovered_heat_mj_day": recovered,
        "net_thermal_mj_day": net_thermal, "net_thermal_kwh_day": net_thermal/MJ_PER_KWH,
        "electric_kwh_day": total_electric, "energy_kwh_equiv_day": energy_kwh_equiv,
        "energy_kwh_per_l": energy_kwh_equiv/ethanol_l if ethanol_l else None,
        "utility_cost_day": total_cost, "utility_cost_per_l": total_cost/ethanol_l if ethanol_l else None,
        "thermal_cost_day": thermal_cost, "electric_cost_day": electric_cost,
        "eligible_heat_mj_day": eligible
    }


def default_params() -> dict:
    """Legacy sidebar defaults (all illustrative). Production basis and moisture are supplied upstream."""
    return {
        "washing_water_m3_day": 3.0, "washing_pump_head_m": 15.0, "washing_pump_eff_pct": 65,
        "target_moisture_pct": 10, "dryer_inlet_temp_c": 25.0, "dryer_eff_pct": 55,
        "milling_kwh_per_t": 25.0, "slurry_mixing_kwh_day": 8.0, "pretreatment_liquid_solid_ratio": 8.0,
        "pretreatment_inlet_temp_c": 25.0, "pretreatment_temp_c": 120.0, "pretreatment_heater_eff_pct": 80,
        "pretreatment_hold_loss_mj_day": 500.0, "filter_press_kwh_per_t": 5.0, "broth_ethanol_vol_pct": 5.0,
        "fermenter_mixing_kwh_m3": 3.0, "fermenter_cooling_mj_day": 0.0, "centrifuge_kwh_per_m3": 1.5,
        "distillation_mj_per_m3_broth": 1800.0, "distillation_heater_eff_pct": 85,
        "dehydration_mj_per_l_ethanol": 1.5, "heat_recovery_pct": 10, "auxiliary_kwh_day": 10.0,
        "thermal_price_per_kwh": 1.5, "electricity_price_per_kwh": 2.0,
    }
