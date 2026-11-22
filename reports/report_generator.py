"""Report generation from the actual simulation results held in a DataManager (PDF, Excel, JSON)."""
from __future__ import annotations

import io
import json
from datetime import datetime

import pandas as pd

from core import configuration as cfg
from core.data_manager import MODULE_NAMES, DataManager
from modules import module_02_process_yield as m02

SECTIONS = ("summary", "feedstock", "process", "massbalance", "energy", "zerowaste", "economics", "assumptions")
SECTION_TITLES = {"summary": "Process Summary", "feedstock": "Feedstock Analysis (Module 01)",
                  "process": "Process Performance (Module 02)", "massbalance": "Mass Balance",
                  "energy": "Energy & Utilities (Module 03)", "zerowaste": "Zero-Waste Analysis (Module 04)",
                  "economics": "Techno-Economic Analysis (Module 05)",
                  "assumptions": "Assumptions, Data Transfers & Checks"}


def _num(v, d=2):
    return f"{v:,.{d}f}" if isinstance(v, (int, float)) else ("n/a" if v is None else str(v))


def build_tables(dm: DataManager) -> dict[str, dict[str, pd.DataFrame]]:
    """{section: {table title: DataFrame}} - single source for dashboard, PDF and Excel."""
    r1, r2, r3, r4, r5 = (dm.results[k] for k in ("M01", "M02", "M03", "M04", "M05"))
    mb = dm.derived["mass_balance"]
    days = dm.inputs["operating_days"]
    T: dict[str, dict[str, pd.DataFrame]] = {}

    T["summary"] = {"Key results": pd.DataFrame([
        ("Wet feed", r1["wet_feed_kg_day"], "kg/day"), ("Dry biomass", r1["dry_biomass_kg_day"], "kg/day"),
        ("Total modeled sugars", r2["total_sugars_kg"], "kg/day"),
        ("Ethanol before recovery", r2["ethanol_before_recovery_kg"], "kg/day"),
        ("Recovered ethanol", r2["recovered_ethanol_kg"], "kg/day"),
        ("Recovered ethanol (volume)", r3["ethanol_l_day"], "L/day"),
        ("Ethanol yield on dry biomass", 100 * r2["recovered_ethanol_kg"] / r1["dry_biomass_kg_day"], "% (kg/kg)"),
        ("Net thermal demand", r3["net_thermal_mj_day"], "MJ/day"), ("Electricity demand", r3["electric_kwh_day"], "kWh/day"),
        ("Energy intensity", r3["energy_kwh_per_l"], "kWh/L ethanol"),
        ("Solid residue recovery allocation", r4["indicators"]["solid_residue_recovery_pct"], "%"),
        ("Water recycle ratio", r4["indicators"]["water_recycle_pct"], "%"),
        ("Annual ethanol", r5["quantities"]["ethanol_l_year"], "L/year"),
        ("Annual OPEX (net)", r5["net_opex"], "EGP/year"), ("Annual revenue", r5["revenue"], "EGP/year"),
        ("Operating cost per litre", r5["cost_per_l"], "EGP/L"),
    ], columns=["Metric", "Value", "Unit"])}

    comp = pd.DataFrame([{"Component": k, "% dry basis": r1["composition_pct_db"][k], "kg/day": r1["component_kg_day"][k]}
                         for k in r1["composition_pct_db"]])
    comp.loc[len(comp)] = ["Uncharacterized", r1["uncharacterized_pct"], r1["uncharacterized_kg_day"]]
    T["feedstock"] = {
        "Feed quantities": pd.DataFrame([("Wet feed", r1["wet_feed_kg_day"], "kg/day"), ("Moisture (wet basis)", r1["moisture_pct_wb"], "%"),
                                         ("Dry biomass", r1["dry_biomass_kg_day"], "kg/day"), ("Water in feed", r1["water_in_feed_kg_day"], "kg/day")],
                                        columns=["Quantity", "Value", "Unit"]),
        "Composition": comp}

    T["process"] = {
        "Sugars and ethanol by pathway": pd.DataFrame([{"Sugar": s, "Sugar available (kg/day)": r2["sugar_mass_kg"][s],
                                                        "Sugar fermented (kg/day)": r2["fermented_sugar_kg"][s],
                                                        "Ethanol before recovery (kg/day)": r2["theoretical_ethanol_by_sugar_kg"][s]} for s in m02.SUGARS]),
        "Pretreatment split": pd.DataFrame([{"Component": k, "Initial (kg/day)": r2["component_kg"][k],
                                             "Retained solids (kg/day)": r2["retained_component_kg"][k],
                                             "Dissolved (kg/day)": r2["dissolved_component_kg"][k]} for k in m02.COMPONENTS]),
        "Conversion": pd.DataFrame([("Sugar conversion from retained carbohydrate", 100 * (r2["total_sugars_kg"] - sum(r2["measured_sugars_kg"].values())) /
                                     max(1e-12, sum(r2["retained_component_kg"][c] for c in m02.CARBOHYDRATES)), "% (mass, incl. hydration gain)"),
                                    ("Fermented fraction of sugars", 100 * r2["total_fermented_sugar_kg"] / max(1e-12, r2["total_sugars_kg"]), "%"),
                                    ("Ethanol recovery", 100 * r2["ethanol_recovery"], "%"),
                                    ("Degraded mass", r2["degraded_kg"], "kg/day")], columns=["Metric", "Value", "Unit"])}

    T["massbalance"] = {
        "Inputs (kg/day)": pd.DataFrame(list(mb["inputs"].items()) + [("TOTAL IN", mb["total_in_kg"])], columns=["Stream", "kg/day"]),
        "Outputs (kg/day)": pd.DataFrame(list(mb["outputs"].items()) + [("TOTAL OUT", mb["total_out_kg"]),
                                         ("Closure error (%)", mb["closure_error_pct"])], columns=["Stream", "kg/day"]),
        "Water streams (kg/day)": pd.DataFrame([("Water in incoming feed (leaves as dryer vapour)", r1["water_in_feed_kg_day"]),
                                                ("Water evaporated in dryer (Module 03)", r3["water_removed_kg_day"]),
                                                ("Washing water", dm.derived["m03_params"]["washing_water_m3_day"] * 1000),
                                                ("Pretreatment liquid (L/S x dry mass)", r3["slurry_liquid_kg_day"]),
                                                ("Wastewater passed to Module 04", r4["water_input"])], columns=["Stream", "kg/day"])}

    T["energy"] = {
        "Thermal utilities": pd.DataFrame(r3["thermal_rows"], columns=["Equipment", "Thermal duty (MJ/day)", "Basis"]),
        "Electrical utilities": pd.DataFrame(r3["electric_rows"], columns=["Equipment", "Electricity (kWh/day)", "Basis"]),
        "Totals": pd.DataFrame([("Gross thermal", r3["gross_thermal_mj_day"], "MJ/day"), ("Heat recovered (screening credit)", r3["recovered_heat_mj_day"], "MJ/day"),
                                ("Net thermal", r3["net_thermal_mj_day"], "MJ/day"), ("Electricity", r3["electric_kwh_day"], "kWh/day"),
                                ("Energy (kWh-equivalent)", r3["energy_kwh_equiv_day"], "kWh/day"), ("Energy intensity", r3["energy_kwh_per_l"], "kWh/L"),
                                ("Utility cost", r3["utility_cost_day"], "EGP/day"), ("Utility cost per litre", r3["utility_cost_per_l"], "EGP/L"),
                                ("Broth volume (from ethanol vol%)", r3["broth_volume_m3_day"], "m3/day")], columns=["Metric", "Value", "Unit"])}

    T["zerowaste"] = {
        "Solid-stream allocation (kg/day)": pd.DataFrame([{"Stream": k, "Input": v[0], "Allocated to recovery": v[1], "Unassigned / disposal": v[2]}
                                                          for k, v in r4["solids_table"].items()]),
        "Water (kg/day)": pd.DataFrame([("Wastewater input", r4["water_input"]), ("Recycled", r4["water_recycled"]),
                                        ("Treated after recycle", r4["water_treated"]), ("Discharged untreated", r4["water_discharge"])], columns=["Item", "kg/day"]),
        "CO2 (kg/day)": pd.DataFrame([("Generated", r4["co2_generated"]), ("Captured", r4["co2_captured"]),
                                      ("Utilized / stored", r4["co2_utilized"]), ("Not utilized", r4["co2_released"])], columns=["Item", "kg/day"]),
        "Indicators": pd.DataFrame([("Solid-residue recovery allocation", r4["indicators"]["solid_residue_recovery_pct"]),
                                    ("Water recycle ratio", r4["indicators"]["water_recycle_pct"]),
                                    ("CO2 utilization ratio", r4["indicators"]["co2_utilization_pct"])], columns=["Indicator", "%"])}

    cost_rows = [{"Cost item": k, "EGP/year": v} for k, v in r5["costs"].items()]
    if r5["energy_credit"]:
        cost_rows.append({"Cost item": "Energy recovery credit", "EGP/year": -r5["energy_credit"]})
    T["economics"] = {
        "Cost breakdown": pd.DataFrame(cost_rows),
        "Economic results": pd.DataFrame([("Gross OPEX", r5["gross_opex"], "EGP/year"), ("Net OPEX", r5["net_opex"], "EGP/year"),
                                          ("Annualized CAPEX", r5["capital_charge"], "EGP/year"), ("Revenue", r5["revenue"], "EGP/year"),
                                          ("By-product revenue", r5["byproduct_revenue"], "EGP/year"), ("Operating profit", r5["operating_profit"], "EGP/year"),
                                          ("Net profit after capital & tax (indicative)", r5["net_profit"], "EGP/year"),
                                          ("Operating cost per litre", r5["cost_per_l"], "EGP/L"), ("Break-even (operating)", r5["break_even_operating"], "EGP/L"),
                                          ("Break-even incl. capital", r5["break_even_with_capital"], "EGP/L"),
                                          ("Operating margin", r5["margin_pct"], "%"), ("Simple payback", r5["payback_years"], "years")],
                                         columns=["Metric", "Value", "Unit"]),
        "Annual quantities (from upstream modules)": pd.DataFrame([(k, v) for k, v in r5["quantities"].items()], columns=["Quantity", "Value (annual)"])}

    T["assumptions"] = {"Assumptions ledger": pd.DataFrame(dm.assumptions), "Inter-module data transfers": pd.DataFrame(dm.transfers),
                        "Consistency checks": pd.DataFrame(dm.checks),
                        "Warnings": pd.DataFrame({"Warning": dm.warnings or ["None"]})}
    return T


def to_excel(dm: DataManager) -> bytes:
    T = build_tables(dm)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for sec in SECTIONS:
            row = 0
            name = SECTION_TITLES[sec].split(" (")[0].replace("&", "and").replace(",", "")[:31]
            for title, df in T[sec].items():
                pd.DataFrame({title: []}).to_excel(xw, sheet_name=name, startrow=row, index=False)
                df.to_excel(xw, sheet_name=name, startrow=row + 1, index=False)
                row += len(df) + 4
            ws = xw.sheets[name]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = min(60, max(12, max(len(str(c.value or "")) for c in col) + 2))
    return buf.getvalue()


def to_json(dm: DataManager) -> str:
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        return o
    return json.dumps({"platform": f"{cfg.APP_NAME} {cfg.VERSION}", "generated": datetime.now().isoformat(timespec="seconds"),
                       "inputs": clean(dm.inputs), "status": dm.status, "results": clean(dm.results),
                       "mass_balance": clean(dm.derived["mass_balance"]), "data_transfers": dm.transfers,
                       "assumptions": clean(dm.assumptions), "checks": dm.checks, "warnings": dm.warnings},
                      indent=2, default=str)


def to_pdf(dm: DataManager, sections: tuple[str, ...] = SECTIONS) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    T = build_tables(dm)
    ss = getSampleStyleSheet()
    small = ss["BodyText"].clone("small", fontSize=7.5, leading=9)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm, bottomMargin=14 * mm,
                            title="HYACINTH-X Technical Report")
    width = A4[0] - 28 * mm
    story = [Paragraph(f"{cfg.APP_NAME} - Integrated Biorefinery Simulation Report", ss["Title"]),
             Paragraph(f"Generated {datetime.now():%Y-%m-%d %H:%M} | Mode: {dm.inputs['mode']} | Scenario: {dm.inputs['scenario']} | "
                       f"Basis: kg/day, {dm.inputs['operating_days']} operating days/year | Currency: {cfg.CURRENCY}", small),
             Paragraph("Screening-level estimates. Default parameters are illustrative legacy values, not validated experimental or vendor data.", small),
             Spacer(1, 6)]

    def cell(v):
        if isinstance(v, float):
            return f"{v:,.3f}" if abs(v) < 100 else f"{v:,.1f}"
        return Paragraph(str(v), small) if isinstance(v, str) and len(v) > 28 else ("n/a" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v))

    for sec in sections:
        story.append(Paragraph(SECTION_TITLES[sec], ss["Heading2"]))
        for title, df in T[sec].items():
            story.append(Paragraph(title, ss["Heading4"]))
            data = [list(map(str, df.columns))] + [[cell(v) for v in row] for row in df.itertuples(index=False)]
            if sec == "assumptions" and len(data) > 60:
                data = data[:60] + [["... (truncated in PDF; full ledger in Excel/JSON)"] + [""] * (len(df.columns) - 1)]
            t = Table(data, colWidths=[width / len(df.columns)] * len(df.columns), repeatRows=1)
            t.setStyle(TableStyle([("FONTSIZE", (0, 0), (-1, -1), 7.5), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e7d32")),
                                   ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP")]))
            story += [t, Spacer(1, 6)]
    if "summary" in sections and dm.warnings:
        story.append(Paragraph("Warnings and limitations", ss["Heading2"]))
        story += [Paragraph("- " + w, small) for w in dm.warnings]
    doc.build(story)
    return buf.getvalue()
