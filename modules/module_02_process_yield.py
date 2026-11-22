"""Module 02 - Process Yield Estimator (calculation logic).

Ported from legacy/hyacinth_x_module_02.py. calculate_scenario() equations are unchanged.
Added (integration layer, clearly separate): build_mass_balance() - an audit of the same
numbers that closes the organic dry-matter balance, and co2_from_fermentation().
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

SUGARS = ("Glucose", "Xylose", "Mannose")
COMPONENTS = ("Cellulose", "Xylan", "Mannan", "Lignin", "Ash", "Other / extractives")
CARBOHYDRATES = ("Cellulose", "Xylan", "Mannan")
SUGAR_FACTORS = {"Cellulose": 180.0 / 162.0, "Xylan": 150.0 / 132.0, "Mannan": 180.0 / 162.0}
ETHANOL_YIELD_G_PER_G = {"Glucose": 0.511, "Xylose": 0.511, "Mannose": 0.511}
# Stoichiometric CO2 per kg ethanol: C6H12O6 -> 2 C2H5OH + 2 CO2 (44.01 / 46.07)
CO2_PER_KG_ETHANOL = 44.01 / 46.07

MICROBES = {
    "Conventional S. cerevisiae (illustrative)": {
        "fermentable": {"Glucose": True, "Xylose": False, "Mannose": True},
        "efficiency": {"Glucose": 0.88, "Xylose": 0.00, "Mannose": 0.80},
        "note": "Glucose and mannose fermentable; xylose not assumed fermentable."},
    "Generic xylose-fermenting yeast (illustrative)": {
        "fermentable": {"Glucose": True, "Xylose": True, "Mannose": True},
        "efficiency": {"Glucose": 0.85, "Xylose": 0.65, "Mannose": 0.75},
        "note": "Simplified engineered/xylose-fermenting profile."},
    "Custom profile": {
        "fermentable": {"Glucose": True, "Xylose": True, "Mannose": True},
        "efficiency": {"Glucose": 0.80, "Xylose": 0.50, "Mannose": 0.65},
        "note": "User-defined fermentability and efficiencies."},
}


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(x)))


def validate_composition(composition: Dict[str, float]) -> Tuple[bool, float]:
    total = sum(float(composition.get(k, 0.0)) for k in COMPONENTS)
    return abs(total - 100.0) <= 0.15, total


def default_params() -> Dict[str, Any]:
    m = MICROBES["Conventional S. cerevisiae (illustrative)"]
    return {
        "solid_retention": 0.90, "solubilized_fraction": 0.07, "degraded_fraction": 0.03,
        "cellulose_hydrolysis": 0.75, "xylan_hydrolysis": 0.65, "mannan_hydrolysis": 0.60,
        "fermentable": dict(m["fermentable"]), "fermentation_efficiency": dict(m["efficiency"]),
        "ethanol_recovery": 0.95, "measured_sugars_kg": {s: 0.0 for s in SUGARS},
    }


def calculate_scenario(params: Dict[str, Any]) -> Dict[str, Any]:
    """Screening estimate from dry biomass to recovered ethanol (legacy equations)."""
    dry_mass = max(0.0, float(params["dry_mass_kg"]))
    moisture = clamp(params["moisture_wet_basis"])
    wet_equivalent = dry_mass / max(1e-9, (1.0 - moisture))

    comp = params["composition"]
    ok, comp_total = validate_composition(comp)
    if not ok:
        raise ValueError(f"Dry-basis composition must sum to 100%; current total = {comp_total:.2f}%.")
    component_kg = {k: dry_mass * float(comp.get(k, 0.0)) / 100.0 for k in COMPONENTS}

    retention = clamp(params["solid_retention"])
    solubilized = clamp(params["solubilized_fraction"])
    degraded = clamp(params["degraded_fraction"])
    if retention + solubilized + degraded > 1.0001:
        raise ValueError("Pretreatment solid retention + solubilized + degraded fraction cannot exceed 100%.")
    retained = {k: component_kg[k] * retention for k in COMPONENTS}
    dissolved = {k: component_kg[k] * solubilized for k in COMPONENTS}
    degraded_kg = sum(component_kg[k] * degraded for k in COMPONENTS)

    hydrolysis = {"Cellulose": clamp(params["cellulose_hydrolysis"]),
                  "Xylan": clamp(params["xylan_hydrolysis"]),
                  "Mannan": clamp(params["mannan_hydrolysis"])}
    sugar_mass = {
        "Glucose": retained["Cellulose"] * hydrolysis["Cellulose"] * SUGAR_FACTORS["Cellulose"],
        "Xylose": retained["Xylan"] * hydrolysis["Xylan"] * SUGAR_FACTORS["Xylan"],
        "Mannose": retained["Mannan"] * hydrolysis["Mannan"] * SUGAR_FACTORS["Mannan"],
    }
    measured = params.get("measured_sugars_kg", {})
    for s in SUGARS:
        sugar_mass[s] += max(0.0, float(measured.get(s, 0.0)))

    fermentable = params["fermentable"]
    efficiency = {s: clamp(params["fermentation_efficiency"][s]) for s in SUGARS}
    fermented, eth_by_sugar = {}, {}
    for s in SUGARS:
        fermented[s] = sugar_mass[s] * (efficiency[s] if fermentable.get(s, False) else 0.0)
        eth_by_sugar[s] = fermented[s] * ETHANOL_YIELD_G_PER_G[s]
    eth_before = sum(eth_by_sugar.values())
    recovery = clamp(params["ethanol_recovery"])
    return {
        "dry_mass_kg": dry_mass, "moisture_wet_basis": moisture, "wet_equivalent_kg": wet_equivalent,
        "component_kg": component_kg, "retained_component_kg": retained,
        "dissolved_component_kg": dissolved, "degraded_kg": degraded_kg,
        "hydrolysis_fraction": hydrolysis,
        "sugar_mass_kg": sugar_mass, "fermented_sugar_kg": fermented,
        "theoretical_ethanol_by_sugar_kg": eth_by_sugar,
        "total_sugars_kg": sum(sugar_mass.values()), "total_fermented_sugar_kg": sum(fermented.values()),
        "ethanol_before_recovery_kg": eth_before, "ethanol_recovery": recovery,
        "recovered_ethanol_kg": eth_before * recovery, "composition_total_pct": comp_total,
        "measured_sugars_kg": {s: max(0.0, float(measured.get(s, 0.0))) for s in SUGARS},
    }


# ----------------------- integration-layer additions -----------------------
def co2_from_fermentation(result: Dict[str, Any]) -> float:
    """CO2 (kg) co-produced with the modeled ethanol (stoichiometry). Excludes CO2 from cell growth."""
    return result["ethanol_before_recovery_kg"] * CO2_PER_KG_ETHANOL


def build_mass_balance(result: Dict[str, Any]) -> Dict[str, Any]:
    """Organic dry-matter + hydrolysis-water balance using only Module 02's own numbers.

    IN : dry biomass + water consumed by hydrolysis + measured soluble sugars (if any)
    OUT: residual retained solids, dissolved solids, degraded mass, unfermented sugars,
         ethanol (recovered + lost in recovery), CO2.
    Residual solids = retained non-carbohydrates + unhydrolyzed retained carbohydrates.
    """
    ret, h = result["retained_component_kg"], result["hydrolysis_fraction"]
    hydrolyzed_poly = sum(ret[c] * h[c] for c in CARBOHYDRATES)
    sugars_from_poly = sum(result["sugar_mass_kg"][s] - result["measured_sugars_kg"][s] for s in SUGARS)
    hydrolysis_water = sugars_from_poly - hydrolyzed_poly
    unhydrolyzed = sum(ret[c] * (1 - h[c]) for c in CARBOHYDRATES)
    res_lignin, res_ash, res_other = ret["Lignin"], ret["Ash"], ret["Other / extractives"]
    residual_solids = res_lignin + res_ash + res_other + unhydrolyzed
    dissolved = sum(result["dissolved_component_kg"].values())
    unfermented = result["total_sugars_kg"] - result["total_fermented_sugar_kg"]
    eth_lost = result["ethanol_before_recovery_kg"] - result["recovered_ethanol_kg"]
    co2 = co2_from_fermentation(result)
    # Legacy Module 02 only requires retention + solubilized + degraded <= 100%; any shortfall is mass
    # that the legacy model does not track. It is reported explicitly so the balance stays honest.
    unaccounted = (result["dry_mass_kg"] - sum(ret.values()) - dissolved - result["degraded_kg"])
    unaccounted = 0.0 if abs(unaccounted) < 1e-9 else unaccounted
    measured_total = sum(result["measured_sugars_kg"].values())
    inputs = result["dry_mass_kg"] + hydrolysis_water + measured_total
    outputs = (residual_solids + dissolved + result["degraded_kg"] + unfermented
               + result["recovered_ethanol_kg"] + eth_lost + co2 + unaccounted)
    return {
        "inputs": {"Dry biomass": result["dry_mass_kg"], "Hydrolysis water consumed": hydrolysis_water,
                   "Measured soluble sugars": measured_total},
        "outputs": {"Residual solids - lignin": res_lignin, "Residual solids - ash": res_ash,
                    "Residual solids - other/extractives": res_other,
                    "Residual solids - unhydrolyzed carbohydrates": unhydrolyzed,
                    "Dissolved pretreatment solids": dissolved, "Degraded mass": result["degraded_kg"],
                    "Unfermented sugars": unfermented, "Ethanol lost in recovery": eth_lost,
                    "Recovered ethanol": result["recovered_ethanol_kg"], "CO2 (stoichiometric)": co2,
                    "Unaccounted pretreatment mass (fractions < 100%)": unaccounted},
        "residual_solids_kg": residual_solids, "hydrolysis_water_kg": hydrolysis_water,
        "total_in_kg": inputs, "total_out_kg": outputs,
        "closure_error_pct": 100.0 * (outputs - inputs) / inputs if inputs else 0.0,
        "lignin_residue_kg": res_lignin, "ash_residue_kg": res_ash,
        "other_residue_kg": res_other + unhydrolyzed, "dissolved_kg": dissolved,
        "unfermented_sugars_kg": unfermented, "ethanol_lost_kg": eth_lost, "co2_kg": co2, "unaccounted_kg": unaccounted,
    }
