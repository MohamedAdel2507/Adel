"""Central configuration: defaults, scenario presets and the mapping assumptions between modules.

Every value here is either (a) taken from a legacy module default, or (b) an explicit scenario
decision. None are validated experimental data - the UI and reports label them accordingly.
"""
from __future__ import annotations

from modules import module_02_process_yield as m02
from modules import module_03_energy_utilities as m03
from modules import module_04_zero_waste as m04

APP_NAME = "HYACINTH-X"
VERSION = "1.0.0"
CURRENCY = "EGP"

# ---- Essential inputs (legacy Module 01 defaults; illustrative) ----
DEFAULT_WET_FEED_KG_DAY = 1000.0
DEFAULT_MOISTURE_PCT = 85.0
DEFAULT_COMPOSITION = {            # % dry basis (legacy Module 01 defaults - illustrative, NOT validated data)
    "Cellulose": 25.0, "Hemicellulose": 20.0, "Lignin": 10.0, "Ash": 15.0,
    "Other characterized components": 30.0,
}
DEFAULT_OPERATING_DAYS = 300       # legacy Module 05 default

# Module 01 reports one 'Hemicellulose' pool; Module 02 needs xylan and mannan separately.
# Split = legacy Module 02 default composition (xylan 18 : mannan 3). Assumption, adjustable.
DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE = 3.0 / 21.0

# Integration assumptions (shown in the ledger)
DEFAULT_CHAR_YIELD = 0.0           # kg biochar / kg lignin routed to char: no data in any module -> not credited
DEFAULT_RESIDUE_HEATING_VALUE_MJ_KG = 0.0   # no data in any module -> energy credit not computed
DEFAULT_BOILER_EFFICIENCY_PCT = 80.0        # used only if a heating value is entered

# ---- Scenario presets: Module 04 allocation decisions (screening choices, not conversion yields) ----
SCENARIOS = {
    "Baseline - no valorization": {
        "description": "Legacy Module 04 defaults: no residue valorization, no water recycle, all remaining wastewater treated.",
        "allocations": m04.default_allocations(),
    },
    "Energy recovery": {
        "description": "Lignin-rich and other solid residues routed to energy recovery; ash to managed disposal.",
        "allocations": {**m04.default_allocations(), "lignin_energy": 100, "other_energy": 100, "ash_disposal": 100},
    },
    "Circular biorefinery": {
        "description": "Residues split across energy, material, biochar and compost routes; ash 50% reuse; 50% water recycle.",
        "allocations": {**m04.default_allocations(), "lignin_energy": 60, "lignin_material": 20, "lignin_char": 20,
                        "other_compost": 50, "other_energy": 50, "ash_reuse": 50, "ash_disposal": 50,
                        "water_recycle": 50},
    },
}
DEFAULT_SCENARIO = "Baseline - no valorization"
DEFAULT_MICROBE = "Conventional S. cerevisiae (illustrative)"

# Economic inputs: NO defaults exist in the legacy Module 05 (all zero). Not fabricated here.
DEFAULT_ECONOMICS = {
    "ethanol_price": 0.0, "feedstock_price": 0.0, "enzyme_price": 0.0, "chemical_price": 0.0, "yeast_price": 0.0,
    "water_price": 0.0, "biochar_price": 0.0,
    "enzymes_kg_year": 0.0, "chemicals_kg_year": 0.0, "yeast_kg_year": 0.0,
    "fuel": 0.0, "labor": 0.0, "maintenance": 0.0, "transport": 0.0, "waste_treatment": 0.0,
    "other": 0.0, "other_revenue": 0.0,
    "capex": 0.0, "lifetime_years": 10, "discount_pct": 10.0, "tax_pct": 0.0,
}
# Utility prices come from legacy Module 03 defaults (illustrative) and feed BOTH Module 03 and 05.
DEFAULT_UTILITY_PRICES = {"electricity_price": 2.0, "thermal_price": 1.5}


def default_inputs() -> dict:
    return {
        "mode": "automatic", "scenario": DEFAULT_SCENARIO, "microbe": DEFAULT_MICROBE,
        "wet_feed_kg_day": DEFAULT_WET_FEED_KG_DAY, "moisture_pct": DEFAULT_MOISTURE_PCT,
        "composition": dict(DEFAULT_COMPOSITION), "composition_data_type": "Illustrative assumption",
        "operating_days": DEFAULT_OPERATING_DAYS,
        "economics": dict(DEFAULT_ECONOMICS), "utility_prices": dict(DEFAULT_UTILITY_PRICES),
        "advanced": {                       # honoured only when mode == 'manual'
            "mannan_share": DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE,
            "process": m02.default_params(),
            "energy": m03.default_params(),
            "allocations": None,            # None -> use scenario preset
            "char_yield": DEFAULT_CHAR_YIELD,
            "residue_heating_value_mj_kg": DEFAULT_RESIDUE_HEATING_VALUE_MJ_KG,
            "boiler_efficiency_pct": DEFAULT_BOILER_EFFICIENCY_PCT,
        },
    }
