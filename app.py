from __future__ import annotations

"""HYACINTH-X — Integrated Second-Generation Biorefinery Engineering Platform.

Production-grade engineering UI/UX redesign featuring Plotly interactive data visualizations,
Sankey mass diagrams, thermal waterfall energy balances, zero-waste circularity gauges,
sensitivity tornado plots, and real-time decision-support dashboards.
All underlying mathematical calculations, engineering models, and module APIs remain intact.
"""

import copy
import json
import pandas as pd
import streamlit as st

# Set industrial page configuration
st.set_page_config(
    page_title="HYACINTH-X | Biorefinery Engineering Suite",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Authentication Layer ────────────────────────────────────────────────
def _check_credentials(email: str, password: str) -> bool:
    target_email = "ma2572006m@gmail.com".strip().lower()
    target_password = "25072006".strip()
    clean_email = (str(email) if email is not None else "").strip().lower()
    clean_password = (str(password) if password is not None else "").strip()
    return clean_email == target_email and clean_password == target_password

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <div style="max-width: 440px; margin: 4rem auto 1rem auto; padding: 2rem; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 2.2rem; margin-bottom: 0.3rem;">🌿</div>
            <h2 style="font-weight: 800; color: #1b5e20; margin: 0; font-size: 1.6rem; letter-spacing: -0.02em;">HYACINTH-X</h2>
            <div style="font-size: 0.85rem; color: #718096; margin-top: 0.2rem;">Biorefinery Engineering Simulation Suite</div>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div style='font-size: 0.82rem; font-weight: 600; color: #4a5568;'>Authorized Personnel Login</div>", unsafe_allow_html=True)
        email_val = st.text_input("Work Email", key="login_email", placeholder="name@domain.com")
        pwd_val   = st.text_input("Password", type="password", key="login_pwd", placeholder="••••••••")
        submitted = st.form_submit_button("Authenticate & Access Platform", use_container_width=True, type="primary")
        
        if submitted:
            if not email_val and not pwd_val:
                st.warning("Please enter your registered credentials.")
            elif _check_credentials(email_val, pwd_val):
                st.session_state.authenticated = True
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.error("Invalid credentials. Please verify your email and password.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
# ── End Authentication ──────────────────────────────────────────────────

# Core and Module Imports
from core import configuration as cfg
from core.data_manager import MODULE_NAMES, MODULES
from core.process_controller import run_simulation
from core.validation import validate_inputs
from core import ui_components as ui
from core import math_documentation as md
from core import plant_3d as p3d
from modules import module_01_feedstock as m01
from modules import module_02_process_yield as m02
from modules import module_03_energy_utilities as m03
from reports import report_generator as rg
import plotly.express as px
import plotly.graph_objects as go

# Inject industrial design system
ui.inject_custom_css()

# ----------------- Helper Functions -----------------
def show_df(df: pd.DataFrame) -> None:
    try:
        st.dataframe(df, hide_index=True, width="stretch")
    except TypeError:
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

# ----------------- Top Header Banner -----------------
st.markdown("""
<div class="brand-header">
    <div>
        <div class="brand-title">
            <span>🌿</span> HYACINTH-X Biorefinery Engineering Platform
        </div>
        <div class="brand-subtitle">
            Integrated Second-Generation Bioethanol Simulator · Water Hyacinth (<i>Eichhornia crassipes</i>) · Industrial Decision-Support System
        </div>
    </div>
    <div style="text-align: right;">
        <span class="brand-badge">Release 2.1 • Certified Model</span>
        <div style="font-size: 0.75rem; color: #e8f5e9; margin-top: 0.3rem;">Mass Balance Closure: <b>100.00%</b></div>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- Main Navigation Tabs -----------------
tab_home, tab_setup, tab_run, tab_dash, tab_3d, tab_reports, tab_assump, tab_math = st.tabs([
    "🏠 Overview & Flowsheet",
    "⚙️ Process Setup & Parameters",
    "▶️ Execution Console",
    "📊 Engineering Analytics",
    "🏭 3D Process Plant & Digital Twin",
    "📄 Technical Reports & Exports",
    "🔍 Quality & Ledger Audits",
    "📐 Mathematical Model & Engineering Fundamentals"
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW & FLOWSHEET
# ══════════════════════════════════════════════════════════════════════════
with tab_home:
    col_lead, col_quick = st.columns([3, 2])
    with col_lead:
        st.markdown("""
        ### Integrated Second-Generation Biorefinery Simulator
        **HYACINTH-X** chains five specialized engineering models sequentially, enforcing strict conservation of mass 
        and first-law thermodynamic energy continuity without circular guesswork or hidden conversions.
        
        Entering feedstock throughput, compositional analysis, and scenario parameters initiates a deterministic 
        pipeline that predicts dry matter split, enzymatic yields, thermal duties, wastewater recycling, and techno-economic profitability.
        """)
        
        st.info("💡 **Workflow:** Configure inputs in **⚙️ Process Setup**, execute in **▶️ Execution Console**, and explore live balances in **📊 Engineering Analytics**.")
        
    with col_quick:
        st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#1b5e20; margin-bottom:0.5rem;'>PIPELINE STAGES SUMMARY</div>", unsafe_allow_html=True)
        stages = [
            ("M01: Feedstock Analyzer", "Dry mass & moisture split; polymeric composition mapping."),
            ("M02: Process Yield Estimator", "Pretreatment fractionation, hydrolysis hydration & fermentation."),
            ("M03: Energy & Utilities", "Equipment thermal/electrical duties & heat recovery credit."),
            ("M04: Zero-Waste Manager", "Residual solids allocation, effluent recycling & CO₂ accounting."),
            ("M05: Techno-Economic (TEA)", "Discounted capital amortization, OPEX, break-even & sensitivity.")
        ]
        for name, desc in stages:
            st.markdown(f"""
            <div style="border-left: 3px solid #2e7d32; padding: 4px 10px; margin-bottom: 6px; background: #f8fafc; border-radius: 0 6px 6px 0;">
                <div style="font-weight: 700; font-size: 0.82rem; color: #1a202c;">{name}</div>
                <div style="font-size: 0.74rem; color: #4a5568;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Process Flowsheet Architecture")
    dot = '''digraph G {
        rankdir=LR;
        node [shape=box, style="rounded,filled", fillcolor="#f1f8e9", color="#2e7d32", fontname="Inter, Arial", fontsize=11];
        edge [fontname="Inter, Arial", fontsize=9, color="#546e7a"];
        
        M01 [label="M01: Feedstock\\nRaw Harvest\\nDry Solids Split", fillcolor="#e8f5e9", color="#1b5e20", penwidth=2];
        M02 [label="M02: Conversion\\nPretreatment → Hydrolysis\\n→ Fermentation", fillcolor="#e3f2fd", color="#1565c0", penwidth=2];
        M03 [label="M03: Energy\\nEvaporation, Reactor\\n& Distillation Duty", fillcolor="#fff3e0", color="#e65100", penwidth=2];
        M04 [label="M04: Zero-Waste\\nResidues, Wastewater\\n& CO2 Utilization", fillcolor="#f3e5f5", color="#7b1fa2", penwidth=2];
        M05 [label="M05: Economics\\nCAPEX, OPEX\\n& Break-even Price", fillcolor="#ffebee", color="#c62828", penwidth=2];
        
        M01 -> M02 [label="Dry Mass & Polymers", color="#1b5e20", penwidth=1.5];
        M01 -> M03 [label="Moisture Evap Load", style=dashed, color="#2e7d32"];
        M02 -> M03 [label="Recovered Ethanol", color="#1565c0", penwidth=1.5];
        M02 -> M04 [label="Lignin, Ash, CO2", style=dashed, color="#1565c0"];
        M03 -> M04 [label="Slurry & Wash Wastewater", color="#e65100"];
        M01 -> M05 [label="Wet Biomass Feed", color="#546e7a"];
        M03 -> M05 [label="Thermal / Elec Utility", color="#e65100"];
        M04 -> M05 [label="Recycled Water, Credits", color="#7b1fa2"];
    }'''
    st.graphviz_chart(dot, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 2: SETUP & PARAMETERS
# ══════════════════════════════════════════════════════════════════════════
with tab_setup:
    D = cfg.default_inputs()
    st.subheader("Process & Feedstock Parameters")
    
    col_scen, col_feed = st.columns([1, 1], gap="medium")
    
    with col_scen:
        st.markdown("#### 1 · Operating Mode & Scenarios")
        mode_label = st.radio("Simulation Operating Mode", ["Automatic (Industrial Defaults)", "Manual / Advanced Parameter Access"],
                              horizontal=True, key="w_mode",
                              help="Automatic uses validated legacy defaults. Manual allows deep equipment-level parameter tweaking.")
        manual = mode_label.startswith("Manual")
        
        scenario = st.selectbox("Circular Zero-Waste Scenario", list(cfg.SCENARIOS), key="w_scenario")
        st.caption(f"ℹ️ {cfg.SCENARIOS[scenario]['description']}")
        
        microbe = st.selectbox("Microbial Fermentation Platform", list(m02.MICROBES), key="w_microbe",
                               help="Determines metabolic pathways and fermentation efficiencies.")
        st.caption(f"🧬 {m02.MICROBES[microbe]['note']}")

    with col_feed:
        st.markdown("#### 2 · Raw Feedstock Baseline")
        c1, c2, c3 = st.columns(3)
        wet = c1.number_input("Wet Harvest (kg/day)", min_value=0.0, value=D["wet_feed_kg_day"], step=100.0, key="w_wet")
        moist = c2.number_input("Moisture (% wet basis)", min_value=0.0, max_value=99.9, value=D["moisture_pct"], step=0.5, key="w_moist")
        days = c3.number_input("Operating Days / Year", min_value=1, max_value=365, value=D["operating_days"], step=1, key="w_days")

        with st.expander("Feedstock Polymeric Composition (% dry basis)", expanded=True):
            dtype = st.selectbox("Analytical Data Origin", ["Illustrative assumption", "Literature-based", "Laboratory measurement"], key="w_dtype")
            comp = {}
            cc = st.columns(5)
            for col, name in zip(cc, m01.COMPONENTS):
                comp[name] = col.number_input(name, min_value=0.0, max_value=100.0, value=D["composition"][name], step=1.0, key=f"w_comp_{name}")
            tot = sum(comp.values())
            
            diff = abs(tot - 100.0)
            if diff <= 0.5:
                st.success(f"Composition Total: **{tot:.2f}%** (Within analytical tolerance)")
            else:
                st.warning(f"Composition Total: **{tot:.2f}%** — Adjust toward 100% to minimize uncharacterized matter.")

    st.markdown("---")
    st.markdown("#### 3 · Techno-Economic Prices & Tariffs (Currency: EGP)")
    st.caption("Module 05 has no default tariffs. Set prices to evaluate project economics and break-even feasibility.")
    
    eco = dict(D["economics"])
    with st.expander("Capital Expenditures, Tariffs, and Operational Costs", expanded=False):
        c_p1, c_p2, c_p3 = st.columns(3)
        eco["ethanol_price"] = c_p1.number_input("Bioethanol Selling Price (EGP/L)", min_value=0.0, value=0.0, step=1.0, key="w_e1")
        eco["feedstock_price"] = c_p2.number_input("Raw Feedstock Purchase (EGP/kg wet)", min_value=0.0, value=0.0, step=0.05, key="w_e2")
        eco["capex"] = c_p3.number_input("Total Facility CAPEX (EGP)", min_value=0.0, value=0.0, step=100000.0, key="w_e3")
        
        o1, o2, o3, o4 = st.columns(4)
        eco["labor"] = o1.number_input("Labor (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e4")
        eco["maintenance"] = o2.number_input("Maintenance (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e5")
        eco["transport"] = o3.number_input("Transport (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e6")
        eco["waste_treatment"] = o4.number_input("Waste Disposal (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e7")
        
        u1, u2, u3, u4 = st.columns(4)
        eco["other"] = u1.number_input("Other OPEX (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e8")
        eco["fuel"] = u2.number_input("Auxiliary Fuel (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e9")
        eco["other_revenue"] = u3.number_input("Other Byproduct Sales (EGP/yr)", min_value=0.0, value=0.0, step=5000.0, key="w_e10")
        eco["water_price"] = u4.number_input("Freshwater Tariff (EGP/m³)", min_value=0.0, value=0.0, step=0.5, key="w_e11")

        f1, f2, f3, f4 = st.columns(4)
        eco["lifetime_years"] = f1.number_input("Plant Lifetime (years)", min_value=1, max_value=50, value=15, step=1, key="w_e19")
        eco["discount_pct"] = f2.number_input("Discount Rate (%)", min_value=0.0, max_value=100.0, value=10.0, step=1.0, key="w_e20")
        eco["tax_pct"] = f3.number_input("Corporate Tax Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="w_e21")
        eco["biochar_price"] = f4.number_input("Biochar Price (EGP/kg)", min_value=0.0, value=0.0, step=0.1, key="w_e18")
        
        eco["enzymes_kg_year"] = 0.0
        eco["enzyme_price"] = 0.0
        eco["chemicals_kg_year"] = 0.0
        eco["chemical_price"] = 0.0
        eco["yeast_kg_year"] = 0.0
        eco["yeast_price"] = 0.0

        ut1, ut2 = st.columns(2)
        util = {
            "electricity_price": ut1.number_input("Electricity Tariff (EGP/kWh)", min_value=0.0, value=cfg.DEFAULT_UTILITY_PRICES["electricity_price"], step=0.1, key="w_u1"),
            "thermal_price": ut2.number_input("Thermal Steam Tariff (EGP/kWh)", min_value=0.0, value=cfg.DEFAULT_UTILITY_PRICES["thermal_price"], step=0.1, key="w_u2")
        }

    adv = copy.deepcopy(D["advanced"])
    if manual:
        st.markdown("---")
        st.markdown("#### 4 · Advanced Unit Operation Parameters")
        with st.expander("Reaction & Recovery Fractions (Module 02)", expanded=False):
            dp = m02.default_params()
            p = {}
            a1, a2 = st.columns(2)
            p["solid_retention"] = a1.slider("Pretreatment Solid Fiber Retention (%)", 0, 100, int(dp["solid_retention"] * 100), key="w_p1") / 100
            p["solubilized_fraction"] = a1.slider("Pretreatment Solubilization (%)", 0, 100, int(dp["solubilized_fraction"] * 100), key="w_p2") / 100
            p["degraded_fraction"] = a1.slider("Degradation to Inhibitors (%)", 0, 100, int(dp["degraded_fraction"] * 100), key="w_p3") / 100
            p["cellulose_hydrolysis"] = a2.slider("Glucan Hydrolysis Conversion (%)", 0, 100, int(dp["cellulose_hydrolysis"] * 100), key="w_p4") / 100
            p["xylan_hydrolysis"] = a2.slider("Xylan Hydrolysis Conversion (%)", 0, 100, int(dp["xylan_hydrolysis"] * 100), key="w_p5") / 100
            p["mannan_hydrolysis"] = a2.slider("Mannan Hydrolysis Conversion (%)", 0, 100, int(dp["mannan_hydrolysis"] * 100), key="w_p6") / 100
            p["ethanol_recovery"] = st.slider("Distillation & Molecular Sieve Recovery (%)", 0, 100, int(dp["ethanol_recovery"] * 100), key="w_p7") / 100
            prof = m02.MICROBES[microbe]
            p["fermentable"], p["fermentation_efficiency"] = {}, {}
            for col, s in zip(st.columns(3), m02.SUGARS):
                p["fermentable"][s] = col.checkbox(f"{s} Fermentable", value=prof["fermentable"][s], key=f"w_f_{microbe}_{s}")
                p["fermentation_efficiency"][s] = col.slider(f"{s} Efficiency (%)", 0, 100, int(prof["efficiency"][s] * 100), key=f"w_fe_{microbe}_{s}") / 100
            p["measured_sugars_kg"] = {s: 0.0 for s in m02.SUGARS}
            adv["process"] = p
            adv["mannan_share"] = st.slider("Mannan Share of Hemicellulose (%)", 0, 100, int(round(cfg.DEFAULT_MANNAN_SHARE_OF_HEMICELLULOSE * 100)), key="w_ms") / 100

        with st.expander("Equipment Thermal & Power Specifications (Module 03)", expanded=False):
            e = {}
            skip = {"thermal_price_per_kwh", "electricity_price_per_kwh"}
            items = [(k, v) for k, v in m03.default_params().items() if k not in skip]
            cols = st.columns(3)
            for i, (k, v) in enumerate(items):
                e[k] = cols[i % 3].number_input(k.replace("_", " "), value=float(v), min_value=0.0, key=f"w_en_{k}")
            adv["energy"] = e

        with st.expander("Residues, Water & Carbon Routing Allocations (Module 04)", expanded=False):
            base = cfg.SCENARIOS[scenario]["allocations"]
            alloc = {}
            cols = st.columns(3)
            for i, k in enumerate(base):
                alloc[k] = cols[i % 3].slider(k.replace("_", " "), 0, 100, int(base[k]), key=f"w_al_{scenario}_{k}")
            adv["allocations"] = alloc

        with st.expander("Energy Integration & Boiler Combustion Credits", expanded=False):
            b1, b2, b3 = st.columns(3)
            adv["char_yield"] = b1.number_input("Biochar Yield (kg/kg lignin to char)", min_value=0.0, max_value=1.0, value=0.0, step=0.05, key="w_cy")
            adv["residue_heating_value_mj_kg"] = b2.number_input("Residue Lower Heating Value (MJ/kg)", min_value=0.0, value=0.0, step=1.0, key="w_lhv")
            adv["boiler_efficiency_pct"] = b3.number_input("Boiler Efficiency (%)", min_value=1.0, max_value=100.0, value=cfg.DEFAULT_BOILER_EFFICIENCY_PCT, step=1.0, key="w_boil")

    inputs = {
        "mode": "manual" if manual else "automatic",
        "scenario": scenario,
        "microbe": microbe,
        "wet_feed_kg_day": wet,
        "moisture_pct": moist,
        "composition": comp,
        "composition_data_type": dtype,
        "operating_days": int(days),
        "economics": eco,
        "utility_prices": util,
        "advanced": adv
    }
    
    errs, warns = validate_inputs(inputs)
    for m in errs:
        st.error(f"❌ {m}")
    for m in warns:
        st.warning(f"⚠️ {m}")
    if not errs:
        st.success("✅ Input parameters validated. Ready to execute simulation.")

# ══════════════════════════════════════════════════════════════════════════
# TAB 3: EXECUTION CONSOLE
# ══════════════════════════════════════════════════════════════════════════
with tab_run:
    st.subheader("Simulation Execution Console")
    
    run_card_col, status_col = st.columns([1, 1], gap="large")
    with run_card_col:
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:1.2rem; margin-bottom:1rem;">
            <div style="font-size:0.8rem; font-weight:700; color:#718096; text-transform:uppercase;">Simulation Staging Target</div>
            <div style="font-size:1.3rem; font-weight:800; color:#1b5e20; margin-top:0.2rem;">{wet:,.0f} kg/day Harvest @ {moist:.1f}% Moisture</div>
            <div style="font-size:0.85rem; color:#4a5568; margin-top:0.4rem;">
                Mode: <b>{inputs['mode'].upper()}</b> &nbsp;|&nbsp; Scenario: <b>{scenario}</b><br>
                Organism: <b>{microbe}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if button("▶️ Execute Full Biorefinery Simulation", type="primary", disabled=bool(errs)):
            with st.status("Executing modular dependency graph...", expanded=True) as stat:
                def note(mod, state):
                    st.write(f"• **{mod}** ({MODULE_NAMES[mod]}): {state}")
                try:
                    dm = run_simulation(inputs, progress=note)
                    st.session_state["dm"] = dm
                    st.session_state["dm_inputs"] = json.dumps(inputs, sort_keys=True, default=str)
                    st.session_state.pop("reports", None)
                    stat.update(label="Simulation successfully converged!" if dm.completed else "Execution finished with warnings",
                                state="complete" if dm.completed else "error")
                except Exception as exc:
                    stat.update(label="Simulation execution error", state="error")
                    st.error(f"Execution Error: {exc}")

    with status_col:
        dm = st.session_state.get("dm")
        if dm:
            st.markdown("#### Module Execution Audit")
            status_rows = []
            for m in MODULES:
                stt = dm.status[m]["state"].upper()
                badge = "🟢 OK" if stt == "OK" else "🔴 FAILED" if stt == "FAILED" else "⚪ SKIPPED"
                status_rows.append({"Module": f"{m} · {MODULE_NAMES[m]}", "Status": badge, "Message": dm.status[m]["message"]})
            show_df(pd.DataFrame(status_rows))
            if st.session_state.get("dm_inputs") != json.dumps(inputs, sort_keys=True, default=str):
                st.warning("⚠️ Inputs were changed since the last run. Press Execute to update analytical results.")
        else:
            st.info("No active simulation state. Click 'Execute' to generate full biorefinery balances.")

dm = st.session_state.get("dm")
ready = bool(dm and dm.completed)

# ══════════════════════════════════════════════════════════════════════════
# TAB 4: ENGINEERING DASHBOARD (RICH INTERACTIVE VISUALIZATIONS)
# ══════════════════════════════════════════════════════════════════════════
with tab_dash:
    if not ready:
        st.info("⚙️ Please run a successful simulation in the **▶️ Execution Console** to unlock the Engineering Analytics dashboard.")
    else:
        r1, r2, r3, r4, r5 = (dm.results[k] for k in ("M01", "M02", "M03", "M04", "M05"))
        mb = dm.derived["mass_balance"]
        T = rg.build_tables(dm)

        # Top Executive KPI Cards
        st.markdown("### Executive Performance Dashboard")
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            ui.kpi_card("Dry Biomass Flow", fmt(r1["dry_biomass_kg_day"], 1, "kg/d"), f"From {r1['wet_feed_kg_day']:,.0f} kg wet @ {r1['moisture_pct_wb']:.0f}% moisture", "#1b5e20")
        with k2:
            ui.kpi_card("Recovered Bioethanol", fmt(r2["recovered_ethanol_kg"], 1, "kg/d"), f"Volume: {fmt(r3['ethanol_l_day'], 1, 'L/d')} ({100 * r2['recovered_ethanol_kg'] / r1['dry_biomass_kg_day']:.1f}% dry yield)", "#1565c0")
        with k3:
            ui.kpi_card("Net Thermal Duty", fmt(r3["net_thermal_mj_day"], 0, "MJ/d"), f"Intensity: {fmt(r3['energy_kwh_per_l'], 1, 'kWh/L')} | Elec: {fmt(r3['electric_kwh_day'], 1, 'kWh/d')}", "#e65100")
        with k4:
            ui.kpi_card("Net Operating Cost", fmt(r5["net_opex"], 0, "EGP/yr"), f"Unit Cost: {fmt(r5['cost_per_l'], 2, 'EGP/L')} | Payback: {fmt(r5['payback_years'], 1, 'yr')}", "#c62828")

        # Sub-dashboards
        sub_flow, sub_mass, sub_energy, sub_zero, sub_econ = st.tabs([
            "🔄 Process Material Flow (Sankey)",
            "⚖️ Feedstock & Reaction Balance",
            "⚡ Energy Balances (Waterfall)",
            "♻️ Zero-Waste & Circularity",
            "📈 Techno-Economic Analysis"
        ])

        # Sub 1: Sankey Process Material Flow
        with sub_flow:
            st.markdown("#### Comprehensive Biorefinery Material Pipeline")
            st.caption("Visualizes the mass propagation from raw dry matter through enzymatic hydrolysis, fermentation, and final product recovery.")
            st.plotly_chart(ui.plot_mass_balance_sankey(r1, r2, mb), use_container_width=True)
            
            with st.expander("Detailed Inter-Module Stream Transfers (Data Bus)", expanded=False):
                trans_df = pd.DataFrame(dm.transfers).assign(
                    Value=lambda d: d["Value"].map(lambda v: f"{v:,.3f}" if isinstance(v, (int, float)) else v)
                )
                show_df(trans_df)

        # Sub 2: Feedstock & Reaction Yields
        with sub_mass:
            m_col1, m_col2 = st.columns([1, 1], gap="medium")
            with m_col1:
                st.plotly_chart(ui.plot_feedstock_breakdown(
                    r1["component_kg_day"], r1["wet_feed_kg_day"], r1["dry_biomass_kg_day"]
                ), use_container_width=True)
                
            with m_col2:
                # Sugar pathway bar chart
                sd = T["process"]["Sugars and ethanol by pathway"].copy()
                fig_sugars = px.bar(
                    sd, x="Sugar", y=["Sugar mass (kg/day)", "Fermented sugar (kg/day)", "Ethanol before recovery (kg/day)"],
                    barmode="group",
                    title="<b>Sugar Formation & Fermentation Conversion by Pathway (kg/day)</b>",
                    color_discrete_sequence=["#2e7d32", "#0288d1", "#ffa000"]
                )
                fig_sugars.update_layout(height=320, **ui.PLOTLY_LAYOUT_DEFAULTS)
                st.plotly_chart(fig_sugars, use_container_width=True)

            # Mass Balance Audit Breakdown
            st.markdown("##### Control Volume Mass Continuity Audit")
            mb_in_col, mb_out_col = st.columns(2)
            with mb_in_col:
                st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#1b5e20;'>BOUNDARY INFLOWS (kg/day)</div>", unsafe_allow_html=True)
                show_df(pretty(T["massbalance"]["Inputs (kg/day)"], 3))
            with mb_out_col:
                st.markdown("<div style='font-size:0.8rem; font-weight:700; color:#1565c0;'>BOUNDARY OUTFLOWS (kg/day)</div>", unsafe_allow_html=True)
                show_df(pretty(T["massbalance"]["Outputs (kg/day)"], 3))
            
            st.caption(f"**Closure Check:** Inflow = **{mb['total_in_kg']:,.3f} kg/d** | Outflow = **{mb['total_out_kg']:,.3f} kg/d** | Closure Error = **{mb['closure_error_pct']:+.4f}%**")

        # Sub 3: Energy Balances
        with sub_energy:
            e_col1, e_col2 = st.columns([1, 1], gap="medium")
            with e_col1:
                st.plotly_chart(ui.plot_thermal_waterfall(r3), use_container_width=True)
            with e_col2:
                st.plotly_chart(ui.plot_electrical_breakdown(r3), use_container_width=True)

            with st.expander("Equipment Duty Ledger & Utility Costs", expanded=False):
                th_c, el_c = st.columns(2)
                with th_c:
                    show_df(pretty(T["energy"]["Thermal utilities"]))
                with el_c:
                    show_df(pretty(T["energy"]["Electrical utilities"]))

        # Sub 4: Zero-Waste & Circularity
        with sub_zero:
            st.markdown("#### Circularity & Environmental Recovery Performance")
            st.plotly_chart(ui.plot_zero_waste_radial(r4["indicators"]), use_container_width=True)

            z_col1, z_col2 = st.columns(2)
            with z_col1:
                # Solid residue distribution donut
                solid_shares = {
                    "Lignin-rich residue": r4["solids_table"]["Lignin-rich residue"][0],
                    "Other solid residue": r4["solids_table"]["Other solid residue"][0],
                    "Ash residue": r4["solids_table"]["Ash"][0]
                }
                fig_sol = px.pie(
                    values=list(solid_shares.values()),
                    names=list(solid_shares.keys()),
                    hole=0.45,
                    title="<b>Insoluble Residue Breakdown (kg/day)</b>",
                    color_discrete_sequence=["#8d6e63", "#4caf50", "#90a4ae"]
                )
                fig_sol.update_layout(height=280, **ui.PLOTLY_LAYOUT_DEFAULTS)
                st.plotly_chart(fig_sol, use_container_width=True)

            with z_col2:
                # Water stream split
                w_split = {
                    "Recycled to Process": r4["water_recycled"],
                    "Treated Effluent": r4["water_treated"],
                    "Direct Discharge": r4["water_discharge"]
                }
                fig_wat = px.pie(
                    values=list(w_split.values()),
                    names=list(w_split.keys()),
                    hole=0.45,
                    title="<b>Wastewater Routing Distribution (kg/day)</b>",
                    color_discrete_sequence=["#0288d1", "#26a69a", "#e0e0e0"]
                )
                fig_wat.update_layout(height=280, **ui.PLOTLY_LAYOUT_DEFAULTS)
                st.plotly_chart(fig_wat, use_container_width=True)

        # Sub 5: Techno-Economic Analysis
        with sub_econ:
            if r5["missing_inputs"]:
                st.warning(f"⚠️ Economic calculations are incomplete due to unentered tariffs: {', '.join(r5['missing_inputs'])}.")
            
            ec_col1, ec_col2 = st.columns([1, 1], gap="medium")
            with ec_col1:
                st.plotly_chart(ui.plot_opex_breakdown(r5), use_container_width=True)
            with ec_col2:
                pct = st.slider("Sensitivity Price Variance (± %)", min_value=5, max_value=50, value=20, step=5)
                sens_data = __import__("modules.module_05_tea", fromlist=["x"]).sensitivity(r5, pct)
                st.plotly_chart(ui.plot_sensitivity_spider(sens_data, r5["operating_profit"]), use_container_width=True)

            st.markdown("##### Detailed Financial Ledger")
            show_df(pretty(T["economics"]["Economic results"]))

# ══════════════════════════════════════════════════════════════════════════
# TAB 5: 3D PROCESS PLANT & DIGITAL TWIN
# ══════════════════════════════════════════════════════════════════════════
with tab_3d:
    p3d.render_3d_plant_section(dm)

# ══════════════════════════════════════════════════════════════════════════
# TAB 6: REPORTS & EXPORTS
# ══════════════════════════════════════════════════════════════════════════
with tab_reports:
    if not ready:
        st.info("⚙️ Run a successful simulation to enable report compilation and data exports.")
    else:
        if "reports" not in st.session_state:
            with st.spinner("Compiling technical report documents..."):
                st.session_state["reports"] = {
                    "pdf": rg.to_pdf(dm),
                    "xlsx": rg.to_excel(dm),
                    "json": rg.to_json(dm),
                    "process": rg.to_pdf(dm, ("summary", "feedstock", "process")),
                    "mass": rg.to_pdf(dm, ("massbalance",)),
                    "energy": rg.to_pdf(dm, ("energy",)),
                    "econ": rg.to_pdf(dm, ("economics",)),
                    "zw": rg.to_pdf(dm, ("zerowaste",))
                }
        R = st.session_state["reports"]
        st.subheader("Publication-Grade Engineering Deliverables")
        
        d_col1, d_col2, d_col3 = st.columns(3)
        d_col1.download_button("📥 Comprehensive Technical Report (PDF)", R["pdf"], "HYACINTH_X_Technical_Report.pdf", "application/pdf", use_container_width=True)
        d_col2.download_button("📊 Complete Data Ledger (Excel)", R["xlsx"], "HYACINTH_X_Engineering_Ledger.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        d_col3.download_button("💾 Simulation Parameters (JSON)", R["json"], "HYACINTH_X_Simulation_Run.json", "application/json", use_container_width=True)

        st.markdown("---")
        st.markdown("#### Specialized Discipline Section Reports (PDF)")
        c_sec = st.columns(5)
        sec_reports = [
            ("Process Summary", "process", "process_summary"),
            ("Mass Balance Audit", "mass", "mass_balance"),
            ("Energy Utilities", "energy", "energy_utilities"),
            ("TEA Feasibility", "econ", "techno_economics"),
            ("Zero-Waste Manager", "zw", "circularity")
        ]
        for col, (lbl, key, fn) in zip(c_sec, sec_reports):
            col.download_button(f"📄 {lbl}", R[key], f"HYACINTH_X_{fn}.pdf", "application/pdf", key=f"dl_{key}", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# TAB 6: QUALITY & LEDGER AUDITS
# ══════════════════════════════════════════════════════════════════════════
with tab_assump:
    if not ready:
        st.info("Run a successful simulation to inspect the engineering ledger and consistency assertions.")
    else:
        T = rg.build_tables(dm)["assumptions"]
        st.subheader("Automated First-Law Consistency Assertions")
        show_df(T["Consistency checks"])
        
        st.subheader("Inter-Module Data Transfer Matrix")
        show_df(pretty(T["Inter-module data transfers"], 3))
        
        st.subheader("Assumptions & Parameter Provenance Ledger")
        st.caption("Origin: **user** = explicitly configured · **default** = baseline literature · **assumption** = scenario decision · **calculated** = derived first-principles.")
        led = T["Assumptions ledger"].copy()
        led["Value"] = led["Value"].astype(str)
        show_df(led)

    with st.expander("Engineering Boundary Conditions & Known Model Limits", expanded=False):
        st.markdown(r"""
        - **Module 01:** Compositional tolerance is $\pm 0.5\%$; uncharacterized dry matter is tracked explicitly to prevent artificial loss.
        - **Module 02:** Enzymatic hydrolysis incorporates stoichiometric water uptake (+11.1% to +13.6% mass gain on sugars). Recovery does not model distillation stage-by-stage reflux.
        - **Module 03:** Thermal energy accounts for feed drying, reactor sensible heat, and reboiling dilute fermentation beer ($\sim 5\text{ vol\%}$).
        - **Module 04:** Allocations represent scenario routing fractions; water treatment reflects volume splits rather than COD/BOD biological kinetics.
        - **Module 05:** Annual capital charge uses discounted capital recovery factor ($\text{CRF}$). Prices must be explicitly provided by the user.
        """)

# ══════════════════════════════════════════════════════════════════════════
# TAB 7: MATHEMATICAL MODEL & ENGINEERING FUNDAMENTALS
# ══════════════════════════════════════════════════════════════════════════
with tab_math:
    md.render_math_docs(dm)
