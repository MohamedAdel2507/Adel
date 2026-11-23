from __future__ import annotations

"""HYACINTH-X - unified Streamlit application (UI only; all calculations live in modules/ and core/)."""

import copy
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="HYACINTH-X | Integrated Biorefinery Simulator", page_icon="🌿", layout="wide")

# ── authentication ──────────────────────────────────────────────────────
def _check_credentials(email: str, password: str) -> bool:
    target_email = "ma2572006m@gmail.com".strip().lower()
    target_password = "25072006".strip()
    return (email or "").strip().lower() == target_email and (password or "").strip() == target_password

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="ma2572006m@gmail.com")
        pwd   = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")
        if submitted:
            if _check_credentials(email, pwd):
                st.session_state.authenticated = True
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.error("Invalid email or password. Please verify and try again.")
    st.stop()   # stop rendering the rest of the app until logged in
# ── end of authentication ───────────────────────────────────────────────

from core import configuration as cfg
from core.data_manager import MODULE_NAMES, MODULES
from core.process_controller import run_simulation
from core.validation import validate_inputs
from modules import module_01_feedstock as m01
from modules import module_02_process_yield as m02
from modules import module_03_energy_utilities as m03
from reports import report_generator as rg

st.markdown("""<style>
.block-container {padding-top: 1.2rem; padding-left: 1rem; padding-right: 1rem; max-width: 1400px;}
[data-testid="stMetricValue"] {font-size: 1.3rem;}
@media (max-width: 640px) {[data-testid="stMetricValue"] {font-size: 1.05rem;}}
</style>""", unsafe_allow_html=True)


# ------------------------------- helpers -------------------------------
def show_df(df: pd.DataFrame) -> None:
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except TypeError:  # older Streamlit
        st.dataframe(df, hide_index=True, use_container_width=True)


def button(label: str, **kw) -> bool:
    try:
        return st.button(label, width="stretch", **kw)
    except TypeError:
        return st.button(label, use_container_width=True, **kw)


def fmt(v, d=2, unit="") -> str:
    return "n/a" if v is None else f"{v:,.{d}f}{(' ' + unit) if unit else ''}"


def pretty(df: pd.DataFrame, d: int = 2) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object:
            out[c] = out[c].map(lambda v: f"{v:,.{d}f}" if isinstance(v, float) else v)
        elif pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].map(lambda v: "n/a" if pd.isna(v) else f"{v:,.{d}f}")
    return out


# ------------------------------- header -------------------------------
st.title("🌿 HYACINTH-X")
st.caption("Integrated second-generation bioethanol biorefinery simulator · Water hyacinth (*Eichhornia crassipes*) · "
           "one input → one integrated simulation → complete results")

tab_home, tab_setup, tab_run, tab_dash, tab_reports, tab_assump = st.tabs(
    ["🏠 Home", "⚙️ Setup", "▶️ Run", "📊 Dashboard", "📄 Reports", "🔍 Assumptions & Checks"])

# ------------------------------- Home -------------------------------
with tab_home:
    st.subheader("What this platform does")
    st.write("HYACINTH-X chains five calculation modules so that every result is passed downstream automatically. "
             "You enter only the feed, the scenario and (optionally) economic prices; everything else is calculated or "
             "shown as a visible default assumption.")
    st.markdown("""
| # | Module | What it actually calculates |
|---|---|---|
| 01 | Feedstock Analyzer | Dry mass, water and component mass flows from wet feed, moisture and composition |
| 02 | Process Yield Estimator | Pretreatment split → hydrolysis → fermentation → ethanol recovery (screening yields) |
| 03 | Energy & Utilities | Thermal and electrical demand by equipment, heat-recovery credit, utility cost |
| 04 | Zero-Waste Manager | Residue allocation, water recycle, CO₂ accounting, circularity indicators |
| 05 | Techno-Economic Analysis | OPEX, revenue, break-even, annualized CAPEX, payback, sensitivity |
""")
    st.info("**Start:** open the **⚙️ Setup** tab, then **▶️ Run**, then explore **📊 Dashboard** and download from **📄 Reports**.")
    st.warning("Screening-level tool. All default process parameters are illustrative legacy values - not validated "
               "experimental or vendor data. Economic inputs are never assumed: enter your own prices and costs.")

# ------------------------------- Setup -------------------------------
with tab_setup:
    D = cfg.default_inputs()
    st.subheader("1 · Operating mode and scenario")
    mode_label = st.radio("Operating mode", ["Automatic", "Manual / Advanced"], horizontal=True, key="w_mode",
                          help="Automatic uses the documented default parameters. Manual unlocks every supported process parameter.")
    manual = mode_label.startswith("Manual")
    scenario = st.selectbox("Zero-waste operating scenario", list(cfg.SCENARIOS), key="w_scenario")
    st.caption(cfg.SCENARIOS[scenario]["description"])
    microbe = st.selectbox("Fermentation organism profile", list(m02.MICROBES), key="w_microbe",
                           help="Determines which sugars are fermented and at what efficiency (illustrative profiles).")
    st.caption(m02.MICROBES[microbe]["note"])

    st.subheader("2 · Feedstock (essential inputs)")
    c1, c2, c3 = st.columns(3)
    wet = c1.number_input("Wet biomass feed (kg/day)", min_value=0.0, value=D["wet_feed_kg_day"], step=100.0, key="w_wet")
    moist = c2.number_input("Moisture content (% wet basis)", min_value=0.0, max_value=99.9, value=D["moisture_pct"], step=1.0, key="w_moist")
    days = c3.number_input("Operating days per year", min_value=1, max_value=365, value=D["operating_days"], step=1, key="w_days")
    with st.expander("Feedstock composition (% dry basis) - illustrative defaults, replace with lab/literature data", expanded=False):
        dtype = st.selectbox("Composition data type", ["Illustrative assumption", "Literature-based", "Laboratory measurement"], key="w_dtype")
        comp = {}
        cc = st.columns(5)
        for col, name in zip(cc, m01.COMPONENTS):
            comp[name] = col.number_input(name, min_value=0.0, max_value=100.0, value=D["composition"][name], step=1.0, key=f"w_comp_{name}")
        tot = sum(comp.values())
        st.write(f"Composition total: **{tot:.2f}%**" + ("" if abs(tot - 100) <= 0.5 else "  - adjust toward 100%."))

    st.subheader("3 · Economics (optional - nothing is assumed)")
    st.caption("Module 05 has no default prices. Leave zeros if unknown; affected results are then flagged incomplete. Currency: EGP.")
    eco = dict(D["economics"])
    with st.expander("Prices, costs and financial assumptions", expanded=False):
        a, b, c = st.columns(3)
        eco["ethanol_price"] = a.number_input("Bioethanol selling price (EGP/L)", min_value=0.0, value=0.0, step=1.0, key="w_e1")
        eco["feedstock_price"] = b.number_input("Feedstock price (EGP/kg wet)", min_value=0.0, value=0.0, step=0.1, key="w_e2")
        eco["capex"] = c.number_input("CAPEX (EGP)", min_value=0.0, value=0.0, step=100000.0, key="w_e3")
        a, b, c, d = st.columns(4)
        eco["labor"] = a.number_input("Labor (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e4")
        eco["maintenance"] = b.number_input("Maintenance (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e5")
        eco["transport"] = c.number_input("Transportation (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e6")
        eco["waste_treatment"] = d.number_input("Waste treatment (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e7")
        a, b, c, d = st.columns(4)
        eco["other"] = a.number_input("Other OPEX (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e8")
        eco["fuel"] = b.number_input("Other fuel (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e9")
        eco["other_revenue"] = c.number_input("Other by-product revenue (EGP/year)", min_value=0.0, value=0.0, step=1000.0, key="w_e10")
        eco["water_price"] = d.number_input("Water price (EGP/m³)", min_value=0.0, value=0.0, step=0.1, key="w_e11")
        a, b, c, d = st.columns(4)
        eco["enzymes_kg_year"] = a.number_input("Enzymes (kg/year) - not modeled", min_value=0.0, value=0.0, step=10.0, key="w_e12")
        eco["enzyme_price"] = b.number_input("Enzyme price (EGP/kg)", min_value=0.0, value=0.0, step=1.0, key="w_e13")
        eco["chemicals_kg_year"] = c.number_input("Chemicals (kg/year) - not modeled", min_value=0.0, value=0.0, step=10.0, key="w_e14")
        eco["chemical_price"] = d.number_input("Chemicals price (EGP/kg)", min_value=0.0, value=0.0, step=1.0, key="w_e15")
        a, b, c, d = st.columns(4)
        eco["yeast_kg_year"] = a.number_input("Yeast (kg/year) - not modeled", min_value=0.0, value=0.0, step=10.0, key="w_e16")
        eco["yeast_price"] = b.number_input("Yeast price (EGP/kg)", min_value=0.0, value=0.0, step=1.0, key="w_e17")
        eco["biochar_price"] = c.number_input("Biochar price (EGP/kg)", min_value=0.0, value=0.0, step=0.1, key="w_e18")
        eco["lifetime_years"] = d.number_input("Plant lifetime (years)", min_value=1, max_value=50, value=10, step=1, key="w_e19")
        a, b = st.columns(2)
        eco["discount_pct"] = a.number_input("Discount rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key="w_e20")
        eco["tax_pct"] = b.number_input("Tax rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="w_e21")
        a, b = st.columns(2)
        util = {"electricity_price": a.number_input("Electricity (EGP/kWh) - shared by Modules 03 & 05", min_value=0.0,
                                                    value=cfg.DEFAULT_UTILITY_PRICES["electricity_price"], step=0.1, key="w_u1"),
                "thermal_price": b.number_input("Thermal energy (EGP/kWh) - shared by Modules 03 & 05", min_value=0.0,
                                                value=cfg.DEFAULT_UTILITY_PRICES["thermal_price"], step=0.1, key="w_u2")}
        st.caption("Utility price defaults are illustrative legacy Module 03 values.")

    adv = copy.deepcopy(D["advanced"])
    if manual:
        st.subheader("4 · Advanced settings (Manual mode)")
        st.caption("Only the parameters below are user-defined; everything not listed is calculated or a documented default.")
        with st.expander("Module 02 - pretreatment, hydrolysis, fermentation, recovery", expanded=False):
            dp = m02.default_params()
            p = {}
            a, b = st.columns(2)
            p["solid_retention"] = a.slider("Solid retention (%)", 0, 100, int(dp["solid_retention"] * 100), key="w_p1") / 100
            p["solubilized_fraction"] = a.slider("Solubilized fraction (%)", 0, 100, int(dp["solubilized_fraction"] * 100), key="w_p2") / 100
            p["degraded_fraction"] = a.slider("Degraded fraction (%)", 0, 100, int(dp["degraded_fraction"] * 100), key="w_p3") / 100
            p["cellulose_hydrolysis"] = b.slider("Cellulose → glucose (%)", 0, 100, int(dp["cellulose_hydrolysis"] * 100), key="w_p4") / 100
            p["xylan_hydrolysis"] = b.slider("Xylan → xylose (%)", 0, 100, int(dp["xylan_hydrolysis"] * 100), key="w_p5") / 100
            p["mannan_hydrolysis"] = b.slider("Mannan → mannose (%)", 0, 100, int(dp["mannan_hydrolysis"] * 100), key="w_p6") / 100
            p["ethanol_recovery"] = st.slider("Ethanol recovery (%)", 0, 100, int(dp["ethanol_recovery"] * 100), key="w_p7") / 100
            prof = m02.MICROBES[microbe]
            p["fermentable"], p["fermentation_efficiency"] = {}, {}
            for col, s in zip(st.columns(3), m02.SUGARS):
                p["fermentable"][s] = col.checkbox(f"{s} fermentable", value=prof["fermentable"][s], key=f"w_f_{microbe}_{s}")
                p["fermentation_efficiency"][s] = col.slider(f"{s} efficiency (%)", 0, 100, int(prof["efficiency"][s] * 100), key=f"w_fe_{microbe}_{s}") / 100
            p["measured_sugars_kg"] = {s: 0.0 for s in m02.SUGARS}
            adv["process"] = p
            adv["mannan_share"] = st.slider("Mannan share of hemicellulose (%)", 0, 100, int(round(cfg.DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE * 100)), key="w_ms",
                                            help="Module 01 has one hemicellulose pool; Module 02 needs xylan and mannan.") / 100
        with st.expander("Module 03 - energy & utilities parameters", expanded=False):
            e = {}
            skip = {"thermal_price_per_kwh", "electricity_price_per_kwh"}
            items = [(k, v) for k, v in m03.default_params().items() if k not in skip]
            cols = st.columns(3)
            for i, (k, v) in enumerate(items):
                e[k] = cols[i % 3].number_input(k.replace("_", " "), value=float(v), min_value=0.0, key=f"w_en_{k}")
            adv["energy"] = e
        with st.expander("Module 04 - residue, water and CO₂ allocations (%)", expanded=False):
            base = cfg.SCENARIOS[scenario]["allocations"]
            alloc = {}
            cols = st.columns(3)
            for i, k in enumerate(base):
                alloc[k] = cols[i % 3].slider(k.replace("_", " "), 0, 100, int(base[k]), key=f"w_al_{scenario}_{k}")
            adv["allocations"] = alloc
        with st.expander("Integration assumptions (zero by default = not credited)", expanded=False):
            a, b, c = st.columns(3)
            adv["char_yield"] = a.number_input("Biochar yield (kg/kg lignin routed to char)", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="w_cy")
            adv["residue_heating_value_mj_kg"] = b.number_input("Residue heating value (MJ/kg)", min_value=0.0, value=0.0, step=1.0, key="w_lhv")
            adv["boiler_efficiency_pct"] = c.number_input("Boiler efficiency (%)", min_value=1.0, max_value=100.0, value=cfg.DEFAULT_BOILER_EFFICIENCY_PCT, step=1.0, key="w_boil")

    inputs = {"mode": "manual" if manual else "automatic", "scenario": scenario, "microbe": microbe,
              "wet_feed_kg_day": wet, "moisture_pct": moist, "composition": comp, "composition_data_type": dtype,
              "operating_days": int(days), "economics": eco, "utility_prices": util, "advanced": adv}
    errs, warns = validate_inputs(inputs)
    for m in errs:
        st.error(m)
    for m in warns:
        st.warning(m)
    if not errs:
        st.success("Inputs valid. Go to the ▶️ Run tab.")

# ------------------------------- Run -------------------------------
with tab_run:
    st.subheader("Run the integrated simulation")
    st.write(f"Mode: **{inputs['mode']}** · Scenario: **{inputs['scenario']}** · Feed: **{wet:,.0f} kg/day** at **{moist:.0f}%** moisture")
    if button("▶️ Run Full Simulation", type="primary", disabled=bool(errs)):
        with st.status("Running modules in dependency order…", expanded=True) as stat:
            def note(mod, state):
                st.write(f"{mod} - {MODULE_NAMES[mod]}: {state}")
            try:
                dm = run_simulation(inputs, progress=note)
                st.session_state["dm"] = dm
                st.session_state["dm_inputs"] = json.dumps(inputs, sort_keys=True, default=str)
                st.session_state.pop("reports", None)
                stat.update(label="Simulation complete" if dm.completed else "Simulation finished with failures",
                            state="complete" if dm.completed else "error")
            except Exception as exc:  # noqa: BLE001
                stat.update(label="Simulation failed", state="error")
                st.error(f"Unexpected error: {exc}")
    dm = st.session_state.get("dm")
    if dm:
        rows = [{"Module": f"{m} · {MODULE_NAMES[m]}", "Status": dm.status[m]["state"].upper(), "Message": dm.status[m]["message"]} for m in MODULES]
        show_df(pd.DataFrame(rows))
        if st.session_state.get("dm_inputs") != json.dumps(inputs, sort_keys=True, default=str):
            st.warning("Inputs changed since the last run. Press Run to refresh the results.")
        if not dm.completed:
            st.error("The simulation did not complete. Fix the issue above and run again.")
    else:
        st.info("No simulation has been run yet.")

dm = st.session_state.get("dm")
ready = bool(dm and dm.completed)

# ------------------------------- Dashboard -------------------------------
with tab_dash:
    if not ready:
        st.info("Run a successful simulation to see the dashboard.")
    else:
        r1, r2, r3, r4, r5 = (dm.results[k] for k in ("M01", "M02", "M03", "M04", "M05"))
        mb = dm.derived["mass_balance"]
        T = rg.build_tables(dm)
        for w in dm.warnings:
            st.warning(w)
        k = st.columns(4)
        k[0].metric("Dry biomass", fmt(r1["dry_biomass_kg_day"], 1, "kg/d"))
        k[1].metric("Recovered ethanol", fmt(r2["recovered_ethanol_kg"], 2, "kg/d"), fmt(r3["ethanol_l_day"], 1, "L/d"), delta_color="off")
        k[2].metric("Ethanol yield (dry)", fmt(100 * r2["recovered_ethanol_kg"] / r1["dry_biomass_kg_day"], 2, "%"))
        k[3].metric("Energy intensity", fmt(r3["energy_kwh_per_l"], 1, "kWh/L"))
        k = st.columns(4)
        k[0].metric("Net thermal", fmt(r3["net_thermal_mj_day"], 0, "MJ/d"))
        k[1].metric("Electricity", fmt(r3["electric_kwh_day"], 1, "kWh/d"))
        k[2].metric("Solid recovery alloc.", fmt(r4["indicators"]["solid_residue_recovery_pct"], 1, "%"))
        k[3].metric("Water recycled", fmt(r4["indicators"]["water_recycle_pct"], 1, "%"))
        k = st.columns(4)
        k[0].metric("Net OPEX", fmt(r5["net_opex"], 0, "EGP/yr"))
        k[1].metric("Revenue", fmt(r5["revenue"], 0, "EGP/yr"))
        k[2].metric("Operating cost / L", fmt(r5["cost_per_l"], 2, "EGP/L"))
        k[3].metric("Simple payback", fmt(r5["payback_years"], 1, "yr") if r5["payback_years"] else "n/a")

        sub = st.tabs(["Process flow", "Feedstock", "Process", "Mass balance", "Energy", "Zero-waste", "Economics"])
        with sub[0]:
            dot = f'''digraph G {{ rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#e8f5e9", fontsize=11];
M01 [label="M01 Feedstock\\n{r1["wet_feed_kg_day"]:,.0f} kg/d wet\\n{r1["dry_biomass_kg_day"]:,.0f} kg/d dry"];
M02 [label="M02 Pretreat → Hydrolysis\\n→ Fermentation → Recovery\\nEthanol {r2["recovered_ethanol_kg"]:,.1f} kg/d"];
M03 [label="M03 Energy & Utilities\\n{r3["net_thermal_mj_day"]:,.0f} MJ/d thermal\\n{r3["electric_kwh_day"]:,.0f} kWh/d elec"];
M04 [label="M04 Zero-Waste\\nSolids {r4["solids_total"]:,.0f} kg/d\\nWater {r4["water_input"]:,.0f} kg/d\\nCO2 {r4["co2_generated"]:,.1f} kg/d"];
M05 [label="M05 TEA\\nOPEX {r5["net_opex"]:,.0f} EGP/yr"];
M01 -> M02 [label="dry mass,\\ncomposition"]; M01 -> M03 [label="dry mass,\\nmoisture"]; M02 -> M03 [label="ethanol"];
M02 -> M04 [label="residues, CO2"]; M03 -> M04 [label="wastewater"];
M03 -> M05 [label="utilities, ethanol"]; M04 -> M05 [label="net water,\\nby-products"]; M01 -> M05 [label="feed"]; }}'''
            st.graphviz_chart(dot)
            show_df(pd.DataFrame(dm.transfers).assign(Value=lambda d: d["Value"].map(lambda v: f"{v:,.3f}" if isinstance(v, (int, float)) else v)))
        with sub[1]:
            show_df(pretty(T["feedstock"]["Feed quantities"]))
            comp_df = T["feedstock"]["Composition"]
            st.bar_chart(comp_df.set_index("Component")["kg/day"])
            show_df(pretty(comp_df))
        with sub[2]:
            show_df(pretty(T["process"]["Conversion"]))
            sd = T["process"]["Sugars and ethanol by pathway"]
            st.bar_chart(sd.set_index("Sugar"))
            show_df(pretty(sd))
            show_df(pretty(T["process"]["Pretreatment split"]))
            st.caption("Downstream processing note: Module 02 reports ethanol recovery as one fraction; purity and separation performance are not modeled in the source code.")
        with sub[3]:
            c1, c2 = st.columns(2)
            with c1:
                show_df(pretty(T["massbalance"]["Inputs (kg/day)"], 3))
            with c2:
                show_df(pretty(T["massbalance"]["Outputs (kg/day)"], 3))
            st.caption("Organic/solids balance on a dry basis from Module 02's own numbers (CO₂ by stoichiometry). Water streams below are reported separately.")
            show_df(pretty(T["massbalance"]["Water streams (kg/day)"]))
        with sub[4]:
            th = T["energy"]["Thermal utilities"]
            st.bar_chart(th.set_index("Equipment")["Thermal duty (MJ/day)"])
            show_df(pretty(th))
            show_df(pretty(T["energy"]["Electrical utilities"]))
            show_df(pretty(T["energy"]["Totals"]))
            if r4["indicators"] and dm.results["M05"].get("credit_unavailable"):
                st.info("Energy recovered from residue combustion is unavailable: no residue heating value was provided.")
        with sub[5]:
            for t in ("Solid-stream allocation (kg/day)", "Water (kg/day)", "CO2 (kg/day)", "Indicators"):
                st.markdown(f"**{t}**")
                show_df(pretty(T["zerowaste"][t]))
            st.caption("Allocation percentages are scenario decisions, not conversion yields. Water-quality, COD/BOD and LCA are not modeled.")
        with sub[6]:
            if r5["missing_inputs"]:
                st.warning("Incomplete economics - not provided: " + ", ".join(r5["missing_inputs"]))
            cb = T["economics"]["Cost breakdown"]
            cb = cb[cb["EGP/year"] != 0]
            if len(cb):
                st.bar_chart(cb.set_index("Cost item")["EGP/year"])
            show_df(pretty(T["economics"]["Economic results"]))
            show_df(pretty(T["economics"]["Annual quantities (from upstream modules)"]))
            pct = st.slider("Price sensitivity (± %)", 5, 100, 20, 5)
            show_df(pretty(pd.DataFrame(__import__("modules.module_05_tea", fromlist=["x"]).sensitivity(r5, pct))))
            st.caption("ROI is not calculated by the source Module 05 and is therefore not reported.")

# ------------------------------- Reports -------------------------------
with tab_reports:
    if not ready:
        st.info("Run a successful simulation to enable reports.")
    else:
        if "reports" not in st.session_state:
            with st.spinner("Building reports…"):
                st.session_state["reports"] = {
                    "pdf": rg.to_pdf(dm), "xlsx": rg.to_excel(dm), "json": rg.to_json(dm),
                    "process": rg.to_pdf(dm, ("summary", "feedstock", "process")),
                    "mass": rg.to_pdf(dm, ("massbalance",)), "energy": rg.to_pdf(dm, ("energy",)),
                    "econ": rg.to_pdf(dm, ("economics",)), "zw": rg.to_pdf(dm, ("zerowaste",))}
        R = st.session_state["reports"]
        st.subheader("Comprehensive reports")
        c = st.columns(3)
        c[0].download_button("⬇️ Full technical report (PDF)", R["pdf"], "HYACINTH_X_technical_report.pdf", "application/pdf")
        c[1].download_button("⬇️ All results (Excel)", R["xlsx"], "HYACINTH_X_results.xlsx",
                             "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        c[2].download_button("⬇️ Complete data (JSON)", R["json"], "HYACINTH_X_results.json", "application/json")
        st.subheader("Section reports (PDF)")
        c = st.columns(5)
        for col, (lbl, key, fn) in zip(c, [("Process summary", "process", "process_summary"), ("Mass balance", "mass", "mass_balance"),
                                           ("Energy", "energy", "energy"), ("Economics", "econ", "economics"), ("Zero-waste", "zw", "zero_waste")]):
            col.download_button(lbl, R[key], f"HYACINTH_X_{fn}.pdf", "application/pdf", key=f"dl_{key}")

# ------------------------------- Assumptions -------------------------------
with tab_assump:
    if not ready:
        st.info("Run a successful simulation to see assumptions, data transfers and checks.")
    else:
        T = rg.build_tables(dm)["assumptions"]
        st.subheader("Consistency checks")
        show_df(T["Consistency checks"])
        st.subheader("Inter-module data transfers")
        show_df(pretty(T["Inter-module data transfers"], 3))
        st.subheader("Assumptions ledger")
        st.caption("Origin: user = changed by you · default = documented default · assumption = scenario decision · calculated = derived.")
        led = T["Assumptions ledger"].copy()
        led["Value"] = led["Value"].astype(str)
        show_df(led)
    with st.expander("Known limitations of the source models"):
        st.markdown("""
- Module 02/03/04/05 defaults are illustrative; not validated against experiments.
- Module 03 computes energy/utilities only - **no ethanol purity or separation model** exists in the source code.
- Module 03 broth volume (from ethanol vol%) and the pretreatment liquid (L/S ratio) are independent and not reconciled.
- Module 04 treats treatment/recycle as flow fractions only (no water quality, COD/BOD, LCA).
- Module 05 has no ROI/NPV; payback is simple and ignores time value and tax. Enzymes, chemicals and yeast are not modeled upstream.
- CO₂ is stoichiometric from fermented ethanol only.
""")
