"""Module 01 - Feedstock Analyzer (calculation logic).

Ported from legacy/hyacinth_x_module_01.py. Equations unchanged:
  dry = wet * (1 - moisture_wb);  water = wet * moisture_wb;  component = dry * pct/100.
UI code, and local JSON profile persistence (not suitable for cloud hosting), were removed.
Basis: kg/day, moisture on a wet basis, composition on a dry basis.
"""
from __future__ import annotations

COMPONENTS = ("Cellulose", "Hemicellulose", "Lignin", "Ash", "Other characterized components")
COMPOSITION_TOLERANCE = 0.5  # percentage points (legacy value)


def validate(wet_feed: float, moisture_pct: float, composition: dict[str, float]):
    errors, warnings = [], []
    total = sum(composition.get(k, 0.0) for k in COMPONENTS)
    if wet_feed <= 0:
        errors.append("Wet biomass feed rate must be greater than zero.")
    if not (0 <= moisture_pct < 100):
        errors.append("Moisture content must be at least 0% and less than 100%.")
    if any(composition.get(k, 0.0) < 0 or composition.get(k, 0.0) > 100 for k in COMPONENTS):
        errors.append("Each component percentage must be between 0% and 100%.")
    if total > 100 + COMPOSITION_TOLERANCE:
        errors.append(f"Dry-basis composition totals {total:.2f}%, exceeding 100% by more than "
                      f"the {COMPOSITION_TOLERANCE:.1f}-point tolerance.")
    elif total < 100 - COMPOSITION_TOLERANCE:
        warnings.append(f"Composition totals {total:.2f}%; {100 - total:.2f}% of dry matter is "
                        "uncharacterized and is carried downstream as 'Other / extractives'.")
    return errors, warnings, total


def analyze(wet_feed_kg_day: float, moisture_pct: float, composition: dict[str, float]) -> dict:
    errors, warnings, total = validate(wet_feed_kg_day, moisture_pct, composition)
    if errors:
        raise ValueError(" ".join(errors))
    dry = wet_feed_kg_day * (1.0 - moisture_pct / 100.0)
    water = wet_feed_kg_day * moisture_pct / 100.0
    flows = {k: dry * composition.get(k, 0.0) / 100.0 for k in COMPONENTS}
    unchar_pct = max(0.0, 100.0 - total)
    return {
        "wet_feed_kg_day": wet_feed_kg_day,
        "moisture_pct_wb": moisture_pct,
        "dry_biomass_kg_day": dry,
        "water_in_feed_kg_day": water,
        "composition_pct_db": dict(composition),
        "composition_total_pct": total,
        "component_kg_day": flows,
        "uncharacterized_pct": unchar_pct,
        "uncharacterized_kg_day": dry * unchar_pct / 100.0,
        "warnings": warnings,
    }
