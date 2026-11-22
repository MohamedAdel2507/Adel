"""Process Controller / Simulation Orchestrator.

Dependency graph (acyclic, derived from the real module inputs):
  M01 -> M02 (dry mass, moisture, composition)
  M01, M02 -> M03 (dry mass, moisture, recovered ethanol)
  M02, M03 -> M04 (residue solids, CO2, wastewater = washing water + pretreatment liquid)
  M01, M02, M03, M04 -> M05 (ethanol, feed, utilities, freshwater net of recycle, by-products)
"""
from __future__ import annotations

import copy
from typing import Callable

from core import configuration as cfg
from core.data_manager import DataManager
from core.validation import validate_inputs
from modules import module_01_feedstock as m01
from modules import module_02_process_yield as m02
from modules import module_03_energy_utilities as m03
from modules import module_04_zero_waste as m04
from modules import module_05_tea as m05


def _origin(manual: bool, value, default) -> str:
    return "user" if manual and value != default else "default"


def map_composition(m1: dict, mannan_share: float, dm: DataManager) -> dict:
    """Module 01 composition (5 pools) -> Module 02 composition (6 pools, sum 100%)."""
    c = m1["composition_pct_db"]
    hemi = c["Hemicellulose"]
    comp = {"Cellulose": c["Cellulose"], "Xylan": hemi * (1 - mannan_share), "Mannan": hemi * mannan_share,
            "Lignin": c["Lignin"], "Ash": c["Ash"],
            "Other / extractives": c["Other characterized components"] + m1["uncharacterized_pct"]}
    total = sum(comp.values())
    if abs(total - 100.0) > 0.15:
        dm.warn(f"Composition total {total:.2f}% was normalized to 100% before Module 02.")
        comp = {k: v * 100.0 / total for k, v in comp.items()}
    return comp


def run_simulation(inputs: dict, progress: Callable[[str, str], None] | None = None) -> DataManager:
    inp = copy.deepcopy(inputs)
    dm = DataManager(inputs=inp)
    manual = inp["mode"] == "manual"
    adv = inp["advanced"]
    days = inp["operating_days"]
    note = progress or (lambda m, s: None)

    errors, warnings = validate_inputs(inp)
    for w in warnings:
        dm.warn(w)
    if errors:
        for m in dm.status:
            dm.set_status(m, "skipped", "Input validation failed")
        dm.set_status("M01", "failed", " ".join(errors))
        dm.derived["validation_errors"] = errors
        return dm

    # ---------------- M01 ----------------
    note("M01", "running")
    try:
        r1 = m01.analyze(inp["wet_feed_kg_day"], inp["moisture_pct"], inp["composition"])
        dm.results["M01"] = r1
        dm.set_status("M01", "ok")
        dm.assume("M01", "Wet feed rate", inp["wet_feed_kg_day"], "kg/day", "user")
        dm.assume("M01", "Moisture (wet basis)", inp["moisture_pct"], "%", "user")
        for k, v in inp["composition"].items():
            dm.assume("M01", f"{k} (dry basis)", v, "%", "user" if inp["composition_data_type"] != "Illustrative assumption" else "default",
                      f"Data type: {inp['composition_data_type']}")
        for w in r1["warnings"]:
            dm.warn(w)
    except Exception as exc:  # noqa: BLE001 - reported to the user
        dm.set_status("M01", "failed", str(exc))
        for m in ("M02", "M03", "M04", "M05"):
            dm.set_status(m, "skipped", "Upstream module failed")
        return dm

    # ---------------- M02 ----------------
    note("M02", "running")
    try:
        mannan_share = adv["mannan_share"] if manual else cfg.DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE
        comp2 = map_composition(r1, mannan_share, dm)
        dm.assume("M02", "Mannan share of hemicellulose", round(mannan_share, 4), "fraction",
                  _origin(manual, mannan_share, cfg.DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE),
                  "Module 01 has one hemicellulose pool; split uses legacy Module 02 default (xylan 18 : mannan 3).")
        p = m02.default_params()
        if manual:
            p.update({k: copy.deepcopy(v) for k, v in adv["process"].items()})
        microbe = m02.MICROBES[inp["microbe"]]
        if not manual or adv["process"] == m02.default_params():
            p["fermentable"], p["fermentation_efficiency"] = dict(microbe["fermentable"]), dict(microbe["efficiency"])
        dm.transfer("M01", "M02", "Dry biomass", r1["dry_biomass_kg_day"], "kg/day")
        dm.transfer("M01", "M02", "Moisture (wet basis)", r1["moisture_pct_wb"], "%")
        dm.transfer("M01", "M02", "Composition (6 pools)", round(sum(comp2.values()), 3), "% dry basis (total)",
                    ", ".join(f"{k} {v:.2f}" for k, v in comp2.items()))
        p.update(dry_mass_kg=r1["dry_biomass_kg_day"], moisture_wet_basis=r1["moisture_pct_wb"] / 100.0,
                 composition=comp2)
        r2 = m02.calculate_scenario(p)
        mb = m02.build_mass_balance(r2)
        dm.results["M02"], dm.derived["mass_balance"], dm.derived["m02_params"] = r2, mb, p
        if mb["unaccounted_kg"] > 0.005 * r2["dry_mass_kg"]:
            dm.warn(f"Pretreatment fractions (retained + solubilized + degraded) total less than 100%: "
                    f"{mb['unaccounted_kg']:.2f} kg/day of dry mass is untracked by Module 02 (shown as 'unaccounted' in the mass balance).")
        dm.set_status("M02", "ok")
        dm.assume("M02", "Microorganism profile", inp["microbe"], "-", "user" if inp["microbe"] != cfg.DEFAULT_MICROBE else "default", microbe["note"])
        for k in ("solid_retention", "solubilized_fraction", "degraded_fraction", "cellulose_hydrolysis",
                  "xylan_hydrolysis", "mannan_hydrolysis", "ethanol_recovery"):
            dm.assume("M02", k, p[k], "fraction", _origin(manual, p[k], m02.default_params()[k]), "Illustrative legacy default")
        for s in m02.SUGARS:
            dm.assume("M02", f"{s} fermentation efficiency", p["fermentation_efficiency"][s], "fraction",
                      "default" if not manual else "user", f"Fermentable: {p['fermentable'][s]}")
        dm.assume("M02", "Ethanol theoretical yield", 0.511, "kg/kg sugar", "default", "Stoichiometric, legacy constant")
        dm.assume("M02", "CO2 from fermentation", round(m02.CO2_PER_KG_ETHANOL, 4), "kg CO2/kg ethanol", "calculated",
                  "Stoichiometry (44.01/46.07); excludes CO2 from cell growth. Integration-layer calculation.")
    except Exception as exc:  # noqa: BLE001
        dm.set_status("M02", "failed", str(exc))
        for m in ("M03", "M04", "M05"):
            dm.set_status(m, "skipped", "Upstream module failed")
        return dm

    # ---------------- M03 ----------------
    note("M03", "running")
    try:
        e = m03.default_params()
        if manual:
            e.update(copy.deepcopy(adv["energy"]))
        e["thermal_price_per_kwh"] = inp["utility_prices"]["thermal_price"]
        e["electricity_price_per_kwh"] = inp["utility_prices"]["electricity_price"]
        e["dry_biomass_kg_day"] = dm.transfer("M01", "M03", "Dry biomass", r1["dry_biomass_kg_day"], "kg/day")
        e["initial_moisture_pct"] = dm.transfer("M01", "M03", "Feed moisture before drying", r1["moisture_pct_wb"], "%")
        e["ethanol_kg_day"] = dm.transfer("M02", "M03", "Recovered ethanol", r2["recovered_ethanol_kg"], "kg/day")
        r3 = m03.calculate_energy(e)
        dm.results["M03"], dm.derived["m03_params"] = r3, e
        dm.set_status("M03", "ok")
        d0 = m03.default_params()
        for k, v in e.items():
            if k in d0:
                dm.assume("M03", k, v, "", _origin(manual, v, d0[k]), "Illustrative legacy default" if v == d0[k] else "")
        dm.assume("M03", "Drying/heating constants", "Cp water 4.186 kJ/kg.K, latent 2.257 MJ/kg", "", "default", "Legacy constants")
    except Exception as exc:  # noqa: BLE001
        dm.set_status("M03", "failed", str(exc))
        for m in ("M04", "M05"):
            dm.set_status(m, "skipped", "Upstream module failed")
        return dm
    if r3["energy_kwh_per_l"] and r3["energy_kwh_per_l"] > 30:
        dm.warn(f"Energy intensity is {r3['energy_kwh_per_l']:.0f} kWh per litre of ethanol; drying a "
                f"{inp['moisture_pct']:.0f}%-moisture feed dominates. Review drying assumptions before drawing conclusions.")

    # ---------------- M04 ----------------
    note("M04", "running")
    try:
        wash_kg = e["washing_water_m3_day"] * 1000.0
        wastewater = wash_kg + r3["slurry_liquid_kg_day"]
        streams = {
            "lignin_residue": dm.transfer("M02", "M04", "Residual lignin", mb["lignin_residue_kg"], "kg/day"),
            "other_residue": dm.transfer("M02", "M04", "Other residual solids (incl. unhydrolyzed carbohydrate)", mb["other_residue_kg"], "kg/day"),
            "ash_residue": dm.transfer("M02", "M04", "Residual ash", mb["ash_residue_kg"], "kg/day"),
            "wastewater": dm.transfer("M03", "M04", "Wastewater (washing water + pretreatment liquid)", wastewater, "kg/day",
                                      "Water mass assumed to leave as liquid effluent; dryer vapour excluded."),
            "co2_generated": dm.transfer("M02", "M04", "Fermentation CO2", mb["co2_kg"], "kg/day"),
            "other_discard": dm.transfer("M02", "M04", "Dissolved + degraded + unfermented sugar + ethanol loss",
                                         mb["dissolved_kg"] + r2["degraded_kg"] + mb["unfermented_sugars_kg"] + mb["ethanol_lost_kg"], "kg/day"),
        }
        alloc = dict(cfg.SCENARIOS[inp["scenario"]]["allocations"])
        if manual and adv["allocations"]:
            alloc = dict(adv["allocations"])
        r4 = m04.calculate(streams, alloc)
        dm.results["M04"], dm.derived["allocations"] = r4, alloc
        dm.set_status("M04", "ok")
        dm.assume("M04", "Scenario", inp["scenario"], "-", "user" if inp["scenario"] != cfg.DEFAULT_SCENARIO else "default",
                  cfg.SCENARIOS[inp["scenario"]]["description"])
        for k, v in alloc.items():
            dm.assume("M04", k, v, "%", "user" if (manual and adv["allocations"]) else "assumption",
                      "Allocation decision, not a conversion yield")
        dm.warn("Wastewater volume (washing + pretreatment liquid) and the fermentation broth volume used for "
                "distillation energy in Module 03 are derived independently in the legacy models and are not reconciled.")
    except Exception as exc:  # noqa: BLE001
        dm.set_status("M04", "failed", str(exc))
        dm.set_status("M05", "skipped", "Upstream module failed")
        return dm

    # ---------------- M05 ----------------
    note("M05", "running")
    try:
        eco = inp["economics"]
        char_yield = adv["char_yield"] if manual else cfg.DEFAULT_CHAR_YIELD
        lhv = adv["residue_heating_value_mj_kg"] if manual else cfg.DEFAULT_RESIDUE_HEATING_VALUE_MJ_KG
        boiler = adv["boiler_efficiency_pct"] if manual else cfg.DEFAULT_BOILER_EFFICIENCY_PCT
        fresh_m3_day = max(0.0, (wastewater - r4["water_recycled"]) / 1000.0)
        biochar_day = r4["lignin_to_char_kg"] * char_yield
        energy_residue_kg = r4["lignin_to_energy_kg"] + r4["other_to_energy_kg"]
        credit_kwh_day = energy_residue_kg * lhv / 3.6 * boiler / 100.0
        credit_egp = credit_kwh_day * days * inp["utility_prices"]["thermal_price"]
        q = {
            "ethanol_l_year": dm.transfer("M03", "M05", "Ethanol (L/day x operating days)", r3["ethanol_l_day"] * days, "L/year"),
            "feedstock_kg_year": dm.transfer("M01", "M05", "Wet feedstock (kg/day x days)", r1["wet_feed_kg_day"] * days, "kg/year", "Purchased as wet biomass"),
            "electricity_kwh_year": dm.transfer("M03", "M05", "Electricity", r3["electric_kwh_day"] * days, "kWh/year"),
            "thermal_kwh_year": dm.transfer("M03", "M05", "Net thermal energy", r3["net_thermal_kwh_day"] * days, "kWh/year"),
            "freshwater_m3_year": dm.transfer("M04", "M05", "Freshwater net of recycled water", fresh_m3_day * days, "m3/year"),
            "biochar_kg_year": dm.transfer("M04", "M05", "Biochar (char-routed lignin x yield)", biochar_day * days, "kg/year"),
            "enzymes_kg_year": eco["enzymes_kg_year"], "chemicals_kg_year": eco["chemicals_kg_year"],
            "yeast_kg_year": eco["yeast_kg_year"],
        }
        price = {"feedstock": eco["feedstock_price"], "enzyme": eco["enzyme_price"], "chemical": eco["chemical_price"],
                 "yeast": eco["yeast_price"], "electricity": inp["utility_prices"]["electricity_price"],
                 "thermal": inp["utility_prices"]["thermal_price"], "water": eco["water_price"],
                 "ethanol": eco["ethanol_price"], "biochar": eco["biochar_price"]}
        opex = {k: eco[k] for k in ("fuel", "labor", "maintenance", "transport", "waste_treatment", "other", "other_revenue")}
        opex["energy_credit"] = dm.transfer("M04", "M05", "Energy recovery credit", credit_egp, "EGP/year",
                                            "Only if a residue heating value is entered") if credit_egp else 0.0
        fin = {k: eco[k] for k in ("capex", "lifetime_years", "discount_pct", "tax_pct")}
        r5 = m05.calculate(q, price, opex, fin)
        r5["quantities"], r5["prices"] = q, price
        r5["waste_for_treatment_kg_year"] = r4["solids_unassigned"] * days
        r5["energy_credit_kwh_year"] = credit_kwh_day * days
        r5["missing_inputs"] = [lbl for k, lbl in (("ethanol_price", "Ethanol selling price"), ("feedstock_price", "Feedstock price"),
                                                   ("capex", "CAPEX"), ("labor", "Labor"), ("maintenance", "Maintenance")) if eco[k] <= 0]
        r5["biochar_unavailable"] = r4["lignin_to_char_kg"] > 0 and char_yield <= 0
        r5["credit_unavailable"] = energy_residue_kg > 0 and lhv <= 0
        dm.results["M05"] = r5
        dm.set_status("M05", "ok")
        dm.assume("M05", "Operating days", days, "days/year", "user" if days != cfg.DEFAULT_OPERATING_DAYS else "default")
        dm.assume("M05", "Utility prices", f"elec {price['electricity']}, thermal {price['thermal']}", "EGP/kWh", "default" if inp["utility_prices"] == cfg.DEFAULT_UTILITY_PRICES else "user", "Defaults are illustrative legacy Module 03 values")
        dm.assume("M05", "Biochar yield", char_yield, "kg/kg lignin", "default" if char_yield == cfg.DEFAULT_CHAR_YIELD else "user", "No source data: 0 = biochar not credited")
        dm.assume("M05", "Residue heating value", lhv, "MJ/kg", "default" if lhv == cfg.DEFAULT_RESIDUE_HEATING_VALUE_MJ_KG else "user", "No source data: 0 = energy credit not computed")
        for k, v in fin.items():
            dm.assume("M05", k, v, "", "default" if v == cfg.DEFAULT_ECONOMICS[k] else "user")
        for k, v in eco.items():
            if k not in fin:
                dm.assume("M05", k, v, "", "default" if v == cfg.DEFAULT_ECONOMICS[k] else "user", "0 = not provided" if v == 0 else "")
        if r5["missing_inputs"]:
            dm.warn("Economics incomplete - zero-valued inputs: " + ", ".join(r5["missing_inputs"]) + ".")
        if r5["biochar_unavailable"]:
            dm.warn("Lignin is routed to biochar but no biochar yield is set; biochar revenue is not calculated.")
        if r5["credit_unavailable"]:
            dm.warn("Residues are routed to energy recovery but no heating value is set; energy credit is not calculated.")
    except Exception as exc:  # noqa: BLE001
        dm.set_status("M05", "failed", str(exc))
        return dm

    _run_checks(dm)
    return dm


def _run_checks(dm: DataManager) -> None:
    r1, r2, r3, r4 = (dm.results[k] for k in ("M01", "M02", "M03", "M04"))
    mb = dm.derived["mass_balance"]
    wet_chk = abs(r1["dry_biomass_kg_day"] + r1["water_in_feed_kg_day"] - r1["wet_feed_kg_day"])
    dm.check("M01 wet = dry + water", wet_chk < 1e-9, f"difference {wet_chk:.2e} kg/day")
    dm.check("M01 -> M02 dry mass identical", abs(r2["dry_mass_kg"] - r1["dry_biomass_kg_day"]) < 1e-9, "")
    dm.check("M02 wet-equivalent = M01 wet feed", abs(r2["wet_equivalent_kg"] - r1["wet_feed_kg_day"]) < 1e-6, "")
    dm.check("M02 organic mass balance closes (<0.1%)", abs(mb["closure_error_pct"]) < 0.1,
             f"in {mb['total_in_kg']:.3f} / out {mb['total_out_kg']:.3f} kg/day ({mb['closure_error_pct']:+.4f}%)")
    dm.check("M02 -> M03 ethanol identical", abs(r3["ethanol_l_day"] * m03.ETHANOL_DENSITY - r2["recovered_ethanol_kg"]) < 1e-9, "")
    solids_in = sum(v[0] for v in r4["solids_table"].values())
    dm.check("M04 solids = M02 residual solids", abs(solids_in - mb["residual_solids_kg"]) < 1e-9, f"{solids_in:.3f} kg/day")
    w = r4["water_recycled"] + r4["water_treated"] + r4["water_discharge"]
    dm.check("M04 water balance closes", abs(w - r4["water_input"]) < 1e-9, f"{w:.3f} vs {r4['water_input']:.3f}")
    r5 = dm.results["M05"]
    days = dm.inputs["operating_days"]
    dm.check("M05 annual ethanol = daily x days", abs(r5["quantities"]["ethanol_l_year"] - r3["ethanol_l_day"] * days) < 1e-6, "")
    dm.check("M05 revenue - OPEX = operating profit", abs(r5["revenue"] - r5["net_opex"] - r5["operating_profit"]) < 1e-6, "")
