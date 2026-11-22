"""Pre-run input validation with plain-language messages."""
from __future__ import annotations

from core import configuration as cfg
from modules import module_01_feedstock as m01
from modules import module_04_zero_waste as m04


def validate_inputs(inp: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    e, w, _ = m01.validate(inp["wet_feed_kg_day"], inp["moisture_pct"], inp["composition"])
    errors += e
    warnings += w
    if not 1 <= inp["operating_days"] <= 365:
        errors.append("Operating days per year must be between 1 and 365.")
    manual = inp["mode"] == "manual"
    adv = inp["advanced"]
    if manual:
        tgt = adv["energy"]["target_moisture_pct"]
        if tgt > inp["moisture_pct"]:
            errors.append(f"Dryer target moisture ({tgt}%) is higher than the feed moisture "
                          f"({inp['moisture_pct']}%). Lower the target or raise the feed moisture.")
        p = adv["process"]
        if p["solid_retention"] + p["solubilized_fraction"] + p["degraded_fraction"] > 1.0001:
            errors.append("Pretreatment solid retention + solubilized + degraded fractions exceed 100%.")
        if not 0 <= adv["mannan_share"] <= 1:
            errors.append("Mannan share of hemicellulose must be between 0 and 1.")
        if adv["energy"]["pretreatment_temp_c"] < adv["energy"]["pretreatment_inlet_temp_c"]:
            errors.append("Pretreatment temperature must be at least the inlet temperature.")
    else:
        if inp["moisture_pct"] < 10:
            errors.append("Feed moisture is below the default 10% dryer target. Use Manual mode to change the "
                          "drying target, or enter a higher feed moisture.")
    if inp["scenario"] not in cfg.SCENARIOS:
        errors.append(f"Unknown scenario '{inp['scenario']}'.")
    alloc = (adv["allocations"] if manual and adv["allocations"] else cfg.SCENARIOS.get(inp["scenario"], {}).get("allocations"))
    if alloc:
        errors += m04.validate_allocations(alloc)
    if inp["composition_data_type"] == "Illustrative assumption":
        warnings.append("Feedstock composition is marked illustrative: results are screening estimates, not predictions.")
    econ = inp["economics"]
    missing = [lbl for k, lbl in (("ethanol_price", "ethanol selling price"), ("capex", "CAPEX")) if econ.get(k, 0) <= 0]
    if missing:
        warnings.append("Economic inputs not provided: " + ", ".join(missing) +
                        ". Revenue/profit/payback will be incomplete (no values are assumed).")
    return errors, warnings
