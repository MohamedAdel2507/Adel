"""Module 05 - Techno-Economic Analysis (calculation logic).

Ported from legacy/hyacinth_x_module_05.py; cost/revenue/profit/break-even/payback equations are unchanged.
The legacy alias-based JSON import is replaced by direct data transfer. Currency: EGP.
Known legacy quirk kept for traceability: the 'capital_in_break_even' checkbox was never used
(break-even including capital always includes the capital charge); it is not exposed here.
"""
from __future__ import annotations


def calculate(q: dict, price: dict, opex: dict, fin: dict) -> dict:
    """q: annual quantities; price: unit prices; opex: lump-sum annual items; fin: capex/lifetime/discount/tax."""
    annual = q["ethanol_l_year"]
    costs = {
        "Feedstock": q["feedstock_kg_year"] * price["feedstock"],
        "Enzymes": q["enzymes_kg_year"] * price["enzyme"],
        "Chemicals": q["chemicals_kg_year"] * price["chemical"],
        "Yeast / microorganisms": q["yeast_kg_year"] * price["yeast"],
        "Electricity": q["electricity_kwh_year"] * price["electricity"],
        "Thermal energy": q["thermal_kwh_year"] * price["thermal"],
        "Freshwater": q["freshwater_m3_year"] * price["water"],
        "Fuel": opex["fuel"], "Labor": opex["labor"], "Maintenance": opex["maintenance"],
        "Transportation": opex["transport"], "Waste treatment": opex["waste_treatment"],
        "Other OPEX": opex["other"],
    }
    gross_opex = sum(costs.values())
    net_opex = max(0.0, gross_opex - opex["energy_credit"])

    capex, life = fin["capex"], fin["lifetime_years"]
    r = fin["discount_pct"] / 100.0
    if capex == 0:
        cap_charge = 0.0
    elif r == 0:
        cap_charge = capex / life
    else:
        cap_charge = capex * (r * (1 + r) ** life) / (((1 + r) ** life) - 1)

    biochar_rev = q["biochar_kg_year"] * price["biochar"]
    byproduct_rev = biochar_rev + opex["other_revenue"]
    revenue = annual * price["ethanol"] + byproduct_rev
    op_profit = revenue - net_opex
    after_cap = op_profit - cap_charge
    tax = max(0.0, after_cap) * fin["tax_pct"] / 100.0
    net_profit = after_cap - tax
    return {
        "costs": costs, "gross_opex": gross_opex, "net_opex": net_opex, "energy_credit": opex["energy_credit"],
        "capital_charge": cap_charge, "biochar_revenue": biochar_rev, "byproduct_revenue": byproduct_rev,
        "revenue": revenue, "operating_profit": op_profit, "net_profit": net_profit, "tax": tax,
        "cost_per_l": net_opex / annual if annual > 0 else None,
        "break_even_operating": max(0.0, (net_opex - byproduct_rev) / annual) if annual > 0 else None,
        "break_even_with_capital": max(0.0, (net_opex + cap_charge - byproduct_rev) / annual) if annual > 0 else None,
        "margin_pct": op_profit / revenue * 100.0 if revenue > 0 else None,
        "payback_years": capex / op_profit if (capex > 0 and op_profit > 0) else None,
    }


def sensitivity(res: dict, change_pct: float) -> list[dict]:
    """One-at-a-time price sensitivity on operating profit (legacy method)."""
    rows = []
    for label, key in (("Feedstock price", "Feedstock"), ("Enzyme price", "Enzymes"),
                       ("Chemical prices", "Chemicals"), ("Electricity price", "Electricity"),
                       ("Thermal energy price", "Thermal energy")):
        d = res["costs"][key] * change_pct / 100.0
        rows.append({"Variable": label, "Profit at +price (EGP/yr)": res["operating_profit"] - d,
                     "Profit at -price (EGP/yr)": res["operating_profit"] + d})
    return rows
