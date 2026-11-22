"""Module 04 - Zero-Waste Manager (calculation logic).

Ported from legacy/hyacinth_x_module_04.py (equations unchanged). The legacy JSON-import
(find_nested_val alias search) is replaced by direct, typed data transfer from the DataManager.
Basis: kg/day (water kg/day ~ L/day). Hourly basis of the legacy UI is not used (platform is daily).
"""
from __future__ import annotations

ALLOCATION_KEYS = ("lignin_energy", "lignin_material", "lignin_char", "other_compost", "other_energy",
                   "other_material", "ash_reuse", "ash_disposal", "water_recycle", "water_treatment",
                   "co2_capture", "co2_use")


def default_allocations() -> dict[str, float]:
    """Legacy defaults: nothing allocated to recovery; all non-recycled water treated."""
    d = {k: 0 for k in ALLOCATION_KEYS}
    d["water_treatment"] = 100
    return d


def validate_allocations(a: dict[str, float]) -> list[str]:
    errs = []
    for name, keys in (("Lignin", ("lignin_energy", "lignin_material", "lignin_char")),
                       ("Other-residue", ("other_compost", "other_energy", "other_material")),
                       ("Ash", ("ash_reuse", "ash_disposal"))):
        tot = sum(a[k] for k in keys)
        if tot > 100:
            errs.append(f"{name} allocation ({tot:.0f}%) exceeds 100%.")
    for k in ALLOCATION_KEYS:
        if not 0 <= a[k] <= 100:
            errs.append(f"{k} must be between 0 and 100%.")
    return errs


def calculate(streams: dict[str, float], alloc: dict[str, float]) -> dict:
    errs = validate_allocations(alloc)
    if errs:
        raise ValueError(" ".join(errs))
    lignin, other = streams["lignin_residue"], streams["other_residue"]
    ash, ww = streams["ash_residue"], streams["wastewater"]
    co2, extra = streams["co2_generated"], streams.get("other_discard", 0.0)

    l_alloc = alloc["lignin_energy"] + alloc["lignin_material"] + alloc["lignin_char"]
    o_alloc = alloc["other_compost"] + alloc["other_energy"] + alloc["other_material"]
    a_alloc = alloc["ash_reuse"] + alloc["ash_disposal"]
    l_rec = lignin * l_alloc / 100.0
    o_rec = other * o_alloc / 100.0
    a_rec = ash * alloc["ash_reuse"] / 100.0          # legacy: only 'reuse' counts as recovery
    solids_rec = l_rec + o_rec + a_rec
    solids_total = lignin + other + ash

    w_rec = ww * alloc["water_recycle"] / 100.0
    w_treated = max(0.0, ww - w_rec) * alloc["water_treatment"] / 100.0
    w_disch = max(0.0, ww - w_rec - w_treated)

    c_cap = co2 * alloc["co2_capture"] / 100.0
    c_use = c_cap * alloc["co2_use"] / 100.0
    c_rel = max(0.0, co2 - c_use)

    return {
        "streams": dict(streams),
        "unallocated_pct": {"lignin": max(0, 100 - l_alloc), "other": max(0, 100 - o_alloc), "ash": max(0, 100 - a_alloc)},
        "solids_table": {
            "Lignin-rich residue": (lignin, l_rec, max(0.0, lignin - l_rec)),
            "Other solid residue": (other, o_rec, max(0.0, other - o_rec)),
            "Ash": (ash, a_rec, max(0.0, ash - a_rec)),
        },
        "lignin_to_energy_kg": lignin * alloc["lignin_energy"] / 100.0,
        "lignin_to_char_kg": lignin * alloc["lignin_char"] / 100.0,
        "lignin_to_material_kg": lignin * alloc["lignin_material"] / 100.0,
        "other_to_energy_kg": other * alloc["other_energy"] / 100.0,
        "solids_total": solids_total, "solids_recovered": solids_rec,
        "solids_unassigned": max(0.0, solids_total - solids_rec),
        "water_input": ww, "water_recycled": w_rec, "water_treated": w_treated, "water_discharge": w_disch,
        "co2_generated": co2, "co2_captured": c_cap, "co2_utilized": c_use, "co2_released": c_rel,
        "other_discard": extra,
        "indicators": {
            "solid_residue_recovery_pct": 100.0 * solids_rec / solids_total if solids_total > 0 else 0.0,
            "water_recycle_pct": 100.0 * w_rec / ww if ww > 0 else 0.0,
            "co2_utilization_pct": 100.0 * c_use / co2 if co2 > 0 else 0.0,
        },
    }
