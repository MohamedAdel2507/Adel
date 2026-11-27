"""Mathematical Model & Engineering Fundamentals for HYACINTH-X.

Provides an interactive textbook and formal engineering reference section embedded
directly into the web application. Covers engineering objectives, LaTeX governing equations,
variable definitions, derivations, computational methodology, assumptions, worked numerical
examples, and peer-reviewed scientific citations across Modules 01 to 05.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st


def render_math_docs(dm=None):
    """Renders the comprehensive 'Mathematical Model & Engineering Fundamentals' section."""
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%); padding: 1.2rem 1.6rem; border-radius: 10px; color: white; margin-bottom: 1.2rem;">
        <div style="font-size: 1.45rem; font-weight: 800; letter-spacing: -0.02em;">📐 Mathematical Model & Engineering Fundamentals</div>
        <div style="font-size: 0.85rem; color: #c8e6c9; margin-top: 0.2rem;">
            Formal Engineering Formulations, First-Principles Balance Derivations, Stoichiometric Models, and Computational Methodology
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    This section serves as a scientific and academic reference for **HYACINTH-X**. 
    Every governing equation, reaction mechanism, thermodynamic duty, and financial metric documented below is 
    derived directly from the implemented Python codebase. Reviewers, researchers, and engineering students can inspect 
    the mathematical formulations, variable definitions, and assumptions underlying the simulation.
    """)

    # Interactive Navigation between Chapters
    chapter = st.radio(
        "Select Technical Chapter",
        [
            "Computational Topology & Module Coupling",
            "Module 01: Feedstock Characterization & Phase Split",
            "Module 02: Deconstruction, Hydrolysis Hydration & Fermentation",
            "Module 03: First-Law Energy Duties & Utility Balances",
            "Module 04: Zero-Waste Mass Accounting & Circularity Indices",
            "Module 05: Techno-Economic Analysis & Discounted Cash Flows",
            "Scientific Foundations & Peer-Reviewed References"
        ],
        horizontal=True,
        key="math_chapter_sel"
    )

    st.markdown("---")

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 0: COMPUTATIONAL TOPOLOGY
    # ═════════════════════════════════════════════════════════════════════════
    if chapter == "Computational Topology & Module Coupling":
        st.subheader("1. Computational Dependency Chain & Information Pipeline")
        st.markdown("""
        HYACINTH-X executes as an **acyclic sequential dependency graph** ($M01 \\to M02 \\to M03 \\to M04 \\to M05$).
        There are no circular iterations or hidden parameters; every downstream calculation receives verified physical streams 
        from upstream unit operations managed by the `ProcessController`.
        """)

        # Dependency Flowchart
        dot = '''digraph DependencyChain {
            rankdir=LR;
            node [shape=box, style="rounded,filled", fontname="Inter, Arial", fontsize=10];
            edge [fontname="Inter, Arial", fontsize=8];

            M01 [label="Module 01\\nFeedstock Analyzer", fillcolor="#e8f5e9", color="#1b5e20", penwidth=2];
            M02 [label="Module 02\\nProcess Yield Estimator", fillcolor="#e3f2fd", color="#1565c0", penwidth=2];
            M03 [label="Module 03\\nEnergy & Utilities", fillcolor="#fff3e0", color="#e65100", penwidth=2];
            M04 [label="Module 04\\nZero-Waste Manager", fillcolor="#f3e5f5", color="#7b1fa2", penwidth=2];
            M05 [label="Module 05\\nTechno-Economics", fillcolor="#ffebee", color="#c62828", penwidth=2];

            M01 -> M02 [label="m_dry, comp[6]", color="#1b5e20", penwidth=1.5];
            M01 -> M03 [label="m_dry, MC_wb", color="#2e7d32", style=dashed];
            M02 -> M03 [label="m_eth_rec", color="#1565c0", penwidth=1.5];
            M02 -> M04 [label="Lignin, Ash, CO2", color="#1565c0", style=dashed];
            M03 -> M04 [label="Wastewater (wash+slurry)", color="#e65100"];
            M01 -> M05 [label="m_wet (annual)", color="#546e7a"];
            M03 -> M05 [label="Electricity, Thermal", color="#e65100"];
            M04 -> M05 [label="Net Freshwater, Biochar", color="#7b1fa2"];
        }'''
        st.graphviz_chart(dot, use_container_width=True)

        st.markdown("#### Inter-Module Coupling Matrix")
        coupling_data = [
            {"Source": "M01", "Target": "M02", "Transfer Parameter": "Dry Biomass Flow (m_dry)", "Mathematical Variable": r"\dot{m}_{\mathrm{dry}}", "Units": "kg/day", "Function": "Baseline dry matter; decouples biological conversion from moisture variations."},
            {"Source": "M01", "Target": "M02", "Transfer Parameter": "Mapped Polymeric Pools", "Mathematical Variable": "C_i", "Units": "% dry basis", "Function": "Maps hemicellulose into xylan (85.7%) and mannan (14.3%) pools."},
            {"Source": "M01", "Target": "M03", "Transfer Parameter": "Feed Moisture & Dry Flow", "Mathematical Variable": "MC_{\mathrm{wb}}, \; \dot{m}_{\mathrm{dry}}", "Units": "%, kg/day", "Function": "Determines daily water mass evaporated in dryer D-101."},
            {"Source": "M02", "Target": "M03", "Transfer Parameter": "Recovered Fuel Bioethanol", "Mathematical Variable": r"\dot{m}_{\mathrm{eth, recovered}}", "Units": "kg/day", "Function": "Establishes fermentation broth volume, beer distillation steam, and dehydration loads."},
            {"Source": "M02", "Target": "M04", "Transfer Parameter": "Residual Solids & Off-Gas", "Mathematical Variable": r"\dot{m}_{\mathrm{resid\_solids}}, \; \dot{m}_{\mathrm{CO}_2}", "Units": "kg/day", "Function": "Routes unhydrolyzed fibers, lignin, and ash for biochar, energy, and soil amendment."},
            {"Source": "M03", "Target": "M04", "Transfer Parameter": "Process Liquid Effluent", "Mathematical Variable": r"\dot{m}_{\mathrm{wastewater}}", "Units": "kg/day", "Function": "Combines biomass washing water and pretreatment slurry liquid for circular recycle."},
            {"Source": "M01-M04", "Target": "M05", "Transfer Parameter": "Annual Operational Totals", "Mathematical Variable": "q_k", "Units": "yr⁻¹, kWh, L", "Function": "Feeds product sales, utility tariffs, chemical tariffs, and energy credits into cash flow equations."}
        ]
        st.dataframe(pd.DataFrame(coupling_data), use_container_width=True, hide_index=True)

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 1: MODULE 01
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Module 01: Feedstock Characterization & Phase Split":
        st.subheader("Module 01: Feedstock Characterization & Phase Split")
        st.markdown("**Core Source:** `modules/module_01_feedstock.py`")

        with st.expander("A. Engineering Objective & Process Rationale", expanded=True):
            st.markdown("""
            Fresh water hyacinth (*Eichhornia crassipes*) is an invasive aquatic macrophyte characterized by extreme water content 
            ($90\%\\text{ to }93\%$ wet basis). In process design, formulating reactions on a wet basis introduces significant distortion.
            **Module 01** eliminates this by separating the raw feed into a pure liquid water stream and an invariant dry structural mass baseline,
            subdividing the dry fraction into structural biopolymers (cellulose, hemicellulose, lignin), mineral ash, and extractives.
            """)

        with st.expander("B. Governing Equations & Formulations", expanded=True):
            st.markdown("##### 1. Total Dry Matter Mass Flow Rate")
            st.latex(r"\dot{m}_{\mathrm{dry}} = \dot{m}_{\mathrm{wet}} \times \left(1 - \frac{MC_{\mathrm{wb}}}{100}\right)")

            st.markdown("##### 2. Raw Water Inflow Rate")
            st.latex(r"\dot{m}_{\mathrm{water, raw}} = \dot{m}_{\mathrm{wet}} \times \left(\frac{MC_{\mathrm{wb}}}{100}\right)")

            st.markdown("##### 3. Component Mass Flows (Dry Basis)")
            st.latex(r"\dot{m}_i = \dot{m}_{\mathrm{dry}} \times \left(\frac{C_i}{100}\right) \quad \forall \; i \in \{\text{Cellulose, Hemicellulose, Lignin, Ash, Others}\}")

            st.markdown("##### 4. Uncharacterized Mass Closure")
            st.latex(r"C_{\mathrm{unchar}} = \max\left(0, \; 100 - \sum_{i=1}^5 C_i\right) \implies \dot{m}_{\mathrm{unchar}} = \dot{m}_{\mathrm{dry}} \times \left(\frac{C_{\mathrm{unchar}}}{100}\right)")

        with st.expander("C. Variable Definitions & Engineering Dimensions", expanded=True):
            vars_m01 = [
                {"Variable": r"\dot{m}_{\mathrm{wet}}", "Physical Meaning": "Raw harvested wet biomass feed rate", "Units": "kg/day", "Nature": "User Input"},
                {"Variable": r"MC_{\mathrm{wb}}", "Physical Meaning": "Feedstock moisture content on a wet basis", "Units": "%", "Nature": "User Input"},
                {"Variable": r"\dot{m}_{\mathrm{dry}}", "Physical Meaning": "Invariant dry matter mass flow rate", "Units": "kg/day", "Nature": "Calculated Output (Transferred to M02 & M03)"},
                {"Variable": r"\dot{m}_{\mathrm{water, raw}}", "Physical Meaning": "Moisture physically present in raw feed", "Units": "kg/day", "Nature": "Calculated Output"},
                {"Variable": r"C_i", "Physical Meaning": "Dry-basis component mass fraction", "Units": "% dry basis", "Nature": "User Input / Lab Assay"},
                {"Variable": r"\dot{m}_i", "Physical Meaning": "Mass flow rate of dry constituent i", "Units": "kg/day", "Nature": "Calculated Output"},
                {"Variable": r"C_{\mathrm{unchar}}", "Physical Meaning": "Uncharacterized dry fraction deficit", "Units": "% dry basis", "Nature": "Conservation Buffer"}
            ]
            st.dataframe(pd.DataFrame(vars_m01), use_container_width=True, hide_index=True)

        with st.expander("D. Assumptions, Tolerances & Computational Limits", expanded=False):
            st.markdown("""
            - **Analytical Tolerance:** $\\pm 0.5\\%$ on dry-basis composition sum $\\sum C_i$.
            - **Constituent Treatment:** If $\\sum C_i < 99.5\\%$, the uncharacterized deficit is mapped downstream to "Other / extractives" rather than discarded, guaranteeing zero mass loss.
            - **Invariance Assumption:** Harvest composition is treated as homogeneous across continuous operating days.
            """)

        with st.expander("E. Worked Numerical Example (Baseline Plant)", expanded=False):
            st.markdown(r"""
            **Input Data:**
            - $\dot{m}_{\mathrm{wet}} = 10,000.0\text{ kg/day}$, $MC_{\mathrm{wb}} = 90.0\%$
            - Composition: Cellulose $= 20.0\%$, Hemicellulose $= 21.0\%$, Lignin $= 10.0\%$, Ash $= 15.0\%$, Other $= 34.0\%$

            **Calculations:**
            $$\dot{m}_{\mathrm{dry}} = 10,000.0 \times (1 - 0.90) = \mathbf{1,000.0\text{ kg/day}}$$
            $$\dot{m}_{\mathrm{water, raw}} = 10,000.0 \times 0.90 = \mathbf{9,000.0\text{ kg/day}}$$
            $$\dot{m}_{\mathrm{cellulose}} = 1,000.0 \times 0.20 = \mathbf{200.0\text{ kg/day}}$$
            $$\dot{m}_{\mathrm{hemicellulose}} = 1,000.0 \times 0.21 = \mathbf{210.0\text{ kg/day}}$$
            """)

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 2: MODULE 02
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Module 02: Deconstruction, Hydrolysis Hydration & Fermentation":
        st.subheader("Module 02: Process Yield, Hydrolysis Hydration & Fermentation")
        st.markdown("**Core Source:** `modules/module_02_process_yield.py`")

        with st.expander("A. Engineering Objective & Stoichiometric Foundation", expanded=True):
            st.markdown("""
            Module 02 models the chemical transformation of structural biomass into purified bioethanol.
            It encompasses:
            1. **Thermochemical Pretreatment:** Destructures the lignocellulose matrix into retained fiber, solubilized organics, and degradation byproducts.
            2. **Enzymatic Hydrolysis:** Cleaves glycosidic bonds with stoichiometric water consumption.
            3. **Anaerobic Fermentation:** Converts hexose and pentose sugars into ethanol and carbon dioxide following Gay-Lussac stoichiometry.
            4. **Distillation Recovery:** Accounts for volatile product recovery and bottoms losses.
            """)

        with st.expander("B. Governing Equations & Reaction Stoichiometry", expanded=True):
            st.markdown("##### 1. Pretreatment Fractionation Split")
            st.latex(r"\dot{m}_{\mathrm{ret}, i} = \dot{m}_i \cdot f_{\mathrm{ret}}, \quad \dot{m}_{\mathrm{diss}, i} = \dot{m}_i \cdot f_{\mathrm{sol}}, \quad \dot{m}_{\mathrm{deg}} = \sum_{i} \dot{m}_i \cdot f_{\mathrm{deg}}")
            st.caption("Constraint: $f_{\mathrm{ret}} + f_{\mathrm{sol}} + f_{\mathrm{deg}} \le 1.0001$. Default values: $90\%$ retention, $7\%$ solubilization, $3\%$ degradation.")

            st.markdown("##### 2. Enzymatic Hydrolysis & Water-of-Hydration Stoichiometry")
            st.markdown("""
            Cellulose and hemicellulose are condensation polymers of anhydro-sugars. When enzymes cleave a glycosidic bond, 
            one water molecule ($18.015\\text{ g/mol}$) is chemically added across each unit:
            """)
            st.latex(r"\text{Glucan: } (\text{C}_6\text{H}_{10}\text{O}_5)_n + n\text{H}_2\text{O} \longrightarrow n\text{C}_6\text{H}_{12}\text{O}_6 \implies F_{\mathrm{cell}} = \frac{180.16}{162.14} = \mathbf{1.1111}")
            st.latex(r"\text{Xylan: } (\text{C}_5\text{H}_8\text{O}_4)_n + n\text{H}_2\text{O} \longrightarrow n\text{C}_5\text{H}_{10}\text{O}_5 \implies F_{\mathrm{xyl}} = \frac{150.13}{132.12} = \mathbf{1.1364}")
            st.latex(r"\text{Mannan: } (\text{C}_6\text{H}_{10}\text{O}_5)_n + n\text{H}_2\text{O} \longrightarrow n\text{C}_6\text{H}_{12}\text{O}_6 \implies F_{\mathrm{man}} = \frac{180.16}{162.14} = \mathbf{1.1111}")

            st.markdown("Sugar monomer mass flow generated:")
            st.latex(r"\dot{m}_{\mathrm{sugar}, j} = \left(\dot{m}_{\mathrm{ret}, j} \cdot \eta_{\mathrm{hyd}, j} \cdot F_{\mathrm{hydration}, j}\right) + \dot{m}_{\mathrm{measured}, j}")

            st.markdown("##### 3. Fermentation & Product Recovery")
            st.markdown("Gay-Lussac anaerobic metabolic pathway for hexoses and pentoses:")
            st.latex(r"\text{C}_6\text{H}_{12}\text{O}_6 \longrightarrow 2\text{C}_2\text{H}_5\text{OH} + 2\text{CO}_2 \implies Y_{\mathrm{eth/sugar}}^{\mathrm{theor}} = \frac{2 \times 46.07}{180.16} = \mathbf{0.5114\text{ g/g}}")
            st.latex(r"\dot{m}_{\mathrm{eth, crude}} = \sum_{j} \left(\dot{m}_{\mathrm{sugar}, j} \cdot \eta_{\mathrm{ferm}, j} \cdot 0.5114\right)")
            st.latex(r"\dot{m}_{\mathrm{eth, recovered}} = \dot{m}_{\mathrm{eth, crude}} \cdot \eta_{\mathrm{recovery}} \quad (\eta_{\mathrm{recovery}} = 0.95)")
            st.latex(r"\dot{m}_{\mathrm{CO}_2} = \dot{m}_{\mathrm{eth, crude}} \times \left(\frac{2 \times 44.01}{2 \times 46.07}\right) = \dot{m}_{\mathrm{eth, crude}} \times \mathbf{0.9553\text{ kg CO}_2\text{ / kg crude ethanol}}")

        with st.expander("C. Organic Mass Balance Closure Derivation", expanded=True):
            st.markdown("""
            A common error in bioethanol modeling is ignoring the water bound during hydrolysis, causing an apparent mass imbalance. 
            HYACINTH-X formulates exact boundary closure:
            """)
            st.latex(r"\text{Total IN} = \dot{m}_{\mathrm{dry}} + \dot{m}_{\mathrm{hyd\_water}} + \dot{m}_{\mathrm{measured\_sugars}}")
            st.latex(r"\text{where: } \dot{m}_{\mathrm{hyd\_water}} = \sum_j \left(\dot{m}_{\mathrm{sugar}, j} - \dot{m}_{\mathrm{measured}, j}\right) - \sum_j \left(\dot{m}_{\mathrm{ret}, j} \cdot \eta_{\mathrm{hyd}, j}\right)")
            st.latex(r"\text{Total OUT} = \dot{m}_{\mathrm{resid\_solids}} + \dot{m}_{\mathrm{diss}} + \dot{m}_{\mathrm{deg}} + \dot{m}_{\mathrm{unferm}} + \dot{m}_{\mathrm{eth, rec}} + \dot{m}_{\mathrm{eth, lost}} + \dot{m}_{\mathrm{CO}_2} + \dot{m}_{\mathrm{unacc}}")
            st.latex(r"\varepsilon = \frac{\text{Total OUT} - \text{Total IN}}{\text{Total IN}} \times 100\% \equiv \mathbf{0.0000\%}")

        with st.expander("D. Worked Numerical Example (Baseline Plant)", expanded=False):
            st.markdown(r"""
            **Baseline Data:** $\dot{m}_{\mathrm{dry}} = 1,000\text{ kg/d}$, Cellulose $= 200\text{ kg/d}$, Xylan $= 180\text{ kg/d}$, Mannan $= 30\text{ kg/d}$.
            - Retained ($90\%$): Cellulose $= 180\text{ kg/d}$, Xylan $= 162\text{ kg/d}$, Mannan $= 27\text{ kg/d}$.
            - Hydrolysis ($\eta_{\mathrm{gluc}} = 75\%$, $\eta_{\mathrm{xyl}} = 65\%$, $\eta_{\mathrm{man}} = 60\%$):
              - Glucose $= 180 \times 0.75 \times 1.1111 = \mathbf{150.00\text{ kg/d}}$
              - Xylose $= 162 \times 0.65 \times 1.1364 = \mathbf{119.66\text{ kg/d}}$
              - Mannose $= 27 \times 0.60 \times 1.1111 = \mathbf{18.00\text{ kg/d}}$
            - Water chemically incorporated: $(150.0 + 119.66 + 18.0) - (135.0 + 105.3 + 16.2) = \mathbf{26.16\text{ kg/d}}$
            - Fermentation (*S. cerevisiae* converts Glucose at $88\%$, Mannose at $80\%$, Xylose at $0\%$):
              - Crude Ethanol $= (150 \times 0.88 + 18 \times 0.80) \times 0.5114 = \mathbf{74.87\text{ kg/d}}$
              - Recovered Ethanol ($95\%$) $= 74.87 \times 0.95 = \mathbf{71.13\text{ kg/d}}$
            """)

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 3: MODULE 03
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Module 03: First-Law Energy Duties & Utility Balances":
        st.subheader("Module 03: PFD-Based Energy & Utilities Formulations")
        st.markdown("**Core Source:** `modules/module_03_energy_utilities.py`")

        with st.expander("A. Engineering Objective & Thermodynamic Constants", expanded=True):
            st.markdown("""
            Module 03 performs equipment-by-equipment First-Law thermal and electrical energy accounting across the process flowsheet.
            
            **Thermodynamic Baseline Constants:**
            - Specific heat capacity of water: $C_{p, w} = 0.004186\text{ MJ/(kg}\cdot\text{K)}$ ($4.186\text{ kJ/kg}\cdot\text{K}$)
            - Specific heat capacity of dry biomass: $C_{p, b} = 0.0015\text{ MJ/(kg}\cdot\text{K)}$ ($1.50\text{ kJ/kg}\cdot\text{K}$)
            - Latent heat of water vaporization: $\Delta H_{\mathrm{vap}} = 2.257\text{ MJ/kg}$ (at $100^\circ\text{C}$, $1\text{ atm}$)
            - Pure ethanol density: $\rho_{\mathrm{ethanol}} = 0.789\text{ kg/L}$
            - Gravitational acceleration: $g = 9.81\text{ m/s}^2$
            - Unit energy conversion: $1\text{ kWh} = 3.6\text{ MJ}$
            """)

        with st.expander("B. Thermal Duty Governing Equations", expanded=True):
            st.markdown("##### 1. Biomass Feed Dryer (D-101)")
            st.latex(r"\dot{m}_{\mathrm{evap}} = \dot{m}_{\mathrm{dry}} \times \left[\frac{m_0}{1 - m_0} - \frac{m_t}{1 - m_t}\right] \quad [\text{kg/day}]")
            st.latex(r"Q_{\mathrm{dryer}} = \frac{\dot{m}_{\mathrm{evap}} C_{p, w} (100 - T_{\mathrm{in}}) + \dot{m}_{\mathrm{evap}} \Delta H_{\mathrm{vap}} + \dot{m}_{\mathrm{dry}} C_{p, b} (100 - T_{\mathrm{in}})}{\eta_{\mathrm{dryer}}} \quad [\text{MJ/day}]")
            st.caption("m₀ = initial moisture fraction; mt = target dried moisture fraction (default 10%); η_dryer = 0.55.")

            st.markdown("##### 2. Pretreatment Slurry Cooking Reactor (R-101)")
            st.latex(r"\dot{m}_{\mathrm{slurry\_liq}} = \dot{m}_{\mathrm{dry}} \times \text{LSR} \quad (\text{LSR} = \text{Liquid-to-Solid Ratio}, \text{default } 8.0)")
            st.latex(r"Q_{\mathrm{pretreat}} = \frac{\left(\dot{m}_{\mathrm{slurry\_liq}} C_{p, w} + \dot{m}_{\mathrm{dry}} C_{p, b}\right) (T_{\mathrm{pre}} - T_{\mathrm{in}}) + Q_{\mathrm{hold\_loss}}}{\eta_{\mathrm{heater}}} \quad [\text{MJ/day}]")
            st.caption("T_pre = 120°C; Q_hold_loss = 500 MJ/day; η_heater = 0.80.")

            st.markdown("##### 3. Beer Distillation Column (C-101) & Molecular Sieve Dehydration")
            st.latex(r"V_{\mathrm{ethanol, L}} = \frac{\dot{m}_{\mathrm{eth, rec}}}{\rho_{\mathrm{ethanol}}} \quad [\text{L/day}]")
            st.latex(r"V_{\mathrm{broth}} = \frac{V_{\mathrm{ethanol, L}}}{C_{\mathrm{broth, vol\%}} / 100} \times \frac{1}{1000} \quad [\text{m}^3\text{/day}] \quad (C_{\mathrm{broth}} = 5.0\text{ vol\%})")
            st.latex(r"Q_{\mathrm{dist}} = \frac{V_{\mathrm{broth}} \times q_{\mathrm{spec, dist}}}{\eta_{\mathrm{dist\_heater}}} \quad [\text{MJ/day}] \quad (q_{\mathrm{spec, dist}} = 1,800.0\text{ MJ/m}^3, \; \eta = 0.85)")
            st.latex(r"Q_{\mathrm{dehyd}} = V_{\mathrm{ethanol, L}} \times q_{\mathrm{spec, dehyd}} \quad [\text{MJ/day}] \quad (q_{\mathrm{spec, dehyd}} = 1.5\text{ MJ/L})")

            st.markdown("##### 4. Cross-Exchange Heat Integration & Net Duty")
            st.latex(r"Q_{\mathrm{eligible}} = Q_{\mathrm{pretreat}} + Q_{\mathrm{dist}} \implies Q_{\mathrm{recovered}} = Q_{\mathrm{eligible}} \times \eta_{\mathrm{heat\_rec}} \quad (\eta_{\mathrm{heat\_rec}} = 0.10)")
            st.latex(r"Q_{\mathrm{net}} = \left(Q_{\mathrm{dryer}} + Q_{\mathrm{pretreat}} + Q_{\mathrm{dist}} + Q_{\mathrm{dehyd}} + Q_{\mathrm{ferm\_cool}}\right) - Q_{\mathrm{recovered}} \quad [\text{MJ/day}]")
            st.latex(r"\text{Net Thermal Demand (kWh)} = \frac{Q_{\mathrm{net}}}{3.6} \quad [\text{kWh/day}]")

        with st.expander("C. Electrical Power Balances", expanded=True):
            st.markdown("""
            Facility power consumption aggregates continuous hydraulic pumping, mechanical solids comminution, and slurry handling:
            """)
            st.latex(r"E_{\mathrm{wash}} = \frac{\rho_w \cdot g \cdot H \cdot V_{\mathrm{wash}}}{\eta_{\mathrm{pump}} \times 3.6 \times 10^6} \quad [\text{kWh/day}] \quad (H = 15.0\text{ m}, \; \eta = 0.65)")
            st.latex(r"E_{\mathrm{mill}} = \left(\frac{\dot{m}_{\mathrm{dry}}}{1000}\right) \times e_{\mathrm{mill\_spec}} \quad [\text{kWh/day}] \quad (e_{\mathrm{mill\_spec}} = 25.0\text{ kWh/t dry})")
            st.latex(r"E_{\mathrm{filter}} = \left(\frac{\dot{m}_{\mathrm{dry}} + \dot{m}_{\mathrm{slurry\_liq}}}{1000}\right) \times e_{\mathrm{filter\_spec}} \quad [\text{kWh/day}] \quad (e = 5.0\text{ kWh/t slurry})")
            st.latex(r"E_{\mathrm{ferm}} = V_{\mathrm{broth}} \times e_{\mathrm{ferm\_spec}} \quad [\text{kWh/day}] \quad (e = 3.0\text{ kWh/m}^3\text{ broth})")
            st.latex(r"E_{\mathrm{centrifuge}} = V_{\mathrm{broth}} \times e_{\mathrm{cent\_spec}} \quad [\text{kWh/day}] \quad (e = 1.5\text{ kWh/m}^3\text{ broth})")
            st.latex(r"E_{\mathrm{total}} = E_{\mathrm{wash}} + E_{\mathrm{mill}} + E_{\mathrm{slurry}} + E_{\mathrm{filter}} + E_{\mathrm{ferm}} + E_{\mathrm{centrifuge}} + E_{\mathrm{aux}} \quad [\text{kWh/day}]")

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 4: MODULE 04
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Module 04: Zero-Waste Mass Accounting & Circularity Indices":
        st.subheader("Module 04: Zero-Waste Mass Accounting & Circularity Formulations")
        st.markdown("**Core Source:** `modules/module_04_zero_waste.py`")

        with st.expander("A. Engineering Objective & Scenario Decision Logic", expanded=True):
            st.markdown("""
            A second-generation biorefinery cannot operate economically on ethanol revenue alone. 
            **Module 04** quantifies circular mass valorization, routing insoluble residues (lignin, ash, unhydrolyzed holocellulose) 
            and liquid wastewater streams into circular valorization pathways according to defined operating scenarios:
            - **Scenario A (Max Circularity):** Maximizes energy recovery via lignin combustion, compost, and closed-loop water recycle.
            - **Scenario B (Biochar Focus):** Pyrolyzes lignin into soil-amending biochar.
            - **Scenario C (Minimum Capital Baseline):** Direct treatment and discharge.
            """)

        with st.expander("B. Governing Formulations & Indicator Definitions", expanded=True):
            st.markdown("##### 1. Circularity Performance Indices")
            st.latex(r"\text{Solid Residue Recovery Index (SRR)} = \frac{\dot{m}_{\mathrm{solids, recovered}}}{\dot{m}_{\mathrm{solids, total}}} \times 100\%")
            st.latex(r"\text{Water Recycling Ratio (WRR)} = \frac{\dot{m}_{\mathrm{water, recycled}}}{\dot{m}_{\mathrm{wastewater}}} \times 100\%")
            st.latex(r"\text{Carbon Dioxide Utilization Index (CUR)} = \frac{\dot{m}_{\mathrm{CO}_2, \mathrm{utilized}}}{\dot{m}_{\mathrm{CO}_2, \mathrm{generated}}} \times 100\%")

            st.markdown("##### 2. Process Wastewater Partitioning")
            st.latex(r"\dot{m}_{\mathrm{wastewater}} = (\dot{V}_{\mathrm{wash}} \times 1000) + \dot{m}_{\mathrm{slurry\_liq}} \quad [\text{kg/day}]")
            st.latex(r"\dot{m}_{\mathrm{recycled}} = \dot{m}_{\mathrm{wastewater}} \times \left(\frac{\alpha_{\mathrm{recycle}}}{100}\right)")
            st.latex(r"\dot{m}_{\mathrm{treated}} = \max\left(0, \; \dot{m}_{\mathrm{wastewater}} - \dot{m}_{\mathrm{recycled}}\right) \times \left(\frac{\alpha_{\mathrm{treatment}}}{100}\right)")
            st.latex(r"\dot{m}_{\mathrm{discharge}} = \max\left(0, \; \dot{m}_{\mathrm{wastewater}} - \dot{m}_{\mathrm{recycled}} - \dot{m}_{\mathrm{treated}}\right)")
            st.caption("α represents scenario allocation percentage decisions.")

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 5: MODULE 05
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Module 05: Techno-Economic Analysis & Discounted Cash Flows":
        st.subheader("Module 05: Techno-Economic Analysis (TEA) Formulations")
        st.markdown("**Core Source:** `modules/module_05_tea.py`")

        with st.expander("A. Engineering Objective & Financial Scope", expanded=True):
            st.markdown("""
            Module 05 integrates technical yields, utility duties, and byproduct streams into discounted techno-economic cash flows.
            It calculates annual OPEX, capital charge annuities via the **Capital Recovery Factor (CRF)**, break-even ethanol production costs,
            and simple payback periods. Currency is in Egyptian Pounds ($\text{EGP}$).
            """)

        with st.expander("B. Governing Financial Equations", expanded=True):
            st.markdown("##### 1. Discounted Capital Charge Annuity")
            st.latex(r"\mathrm{CRF} = \frac{r(1 + r)^n}{(1 + r)^n - 1} \implies \text{Annual Capital Charge} = \mathrm{CAPEX} \times \mathrm{CRF} \quad [\text{EGP/yr}]")
            st.caption("r = annual discount rate (%); n = economic operating life (years). If r = 0, CRF = 1/n.")

            st.markdown("##### 2. Operating Expenses (OPEX) & Energy Recovery Credit")
            st.latex(r"\text{Gross OPEX} = \sum (\text{Annual Consumables} \times \text{Unit Prices}) + \text{Fixed Costs} \quad [\text{EGP/yr}]")
            st.latex(r"\text{Energy Credit} = \left(\dot{m}_{\mathrm{solids, energy}} \times \text{LHV}_{\mathrm{residue}} \times \frac{1}{3.6} \times \frac{\eta_{\mathrm{boiler}}}{100} \times \text{days}\right) \times P_{\mathrm{thermal}} \quad [\text{EGP/yr}]")
            st.latex(r"\mathrm{OPEX}_{\mathrm{net}} = \max\left(0, \; \text{Gross OPEX} - \text{Energy Credit}\right) \quad [\text{EGP/yr}]")

            st.markdown("##### 3. Break-Even Selling Prices & Simple Payback")
            st.latex(r"P_{\mathrm{be, op}} = \frac{\mathrm{OPEX}_{\mathrm{net}} - \mathrm{Revenue}_{\mathrm{byproducts}}}{V_{\mathrm{ethanol, annual}}} \quad [\text{EGP/L}]")
            st.latex(r"P_{\mathrm{be, cap}} = \frac{\mathrm{OPEX}_{\mathrm{net}} + \text{Annual Capital Charge} - \mathrm{Revenue}_{\mathrm{byproducts}}}{V_{\mathrm{ethanol, annual}}} \quad [\text{EGP/L}]")
            st.latex(r"\text{Simple Payback Period} = \frac{\mathrm{CAPEX}}{\text{Operating Profit}} = \frac{\mathrm{CAPEX}}{\text{Revenue} - \mathrm{OPEX}_{\mathrm{net}}} \quad [\text{years}]")

    # ═════════════════════════════════════════════════════════════════════════
    # CHAPTER 6: REFERENCES
    # ═════════════════════════════════════════════════════════════════════════
    elif chapter == "Scientific Foundations & Peer-Reviewed References":
        st.subheader("Scientific Foundations & Peer-Reviewed Literature Citations")
        st.markdown("""
        The governing equations, thermodynamic constants, and stoichiometric conversion factors in HYACINTH-X 
        are based on established chemical engineering principles and biomass conversion literature:
        """)

        refs = [
            {"Discipline": "Biochemical Engineering", "Model Application": "Gay-Lussac Stoichiometry (0.5114 g/g) & CO₂ Evolution", "Author & Year": "Bailey, J.E. & Ollis, D.F. (1986)", "Reference Title": "Biochemical Engineering Fundamentals (2nd ed.), McGraw-Hill.", "DOI/Link": "ISBN: 978-0070032125"},
            {"Discipline": "Biomass Pretreatment", "Model Application": "Hydrolysis Hydration Factors (1.1111 Hexose, 1.1364 Pentose)", "Author & Year": "Wyman, C.E. et al. (2005)", "Reference Title": "Coordinated development of leading cell wall deconstruction technologies for bioenergy.", "DOI/Link": "10.1385/ABAB:124:1-3:893"},
            {"Discipline": "Feedstock Assay", "Model Application": "Water Hyacinth Composition & Extreme Moisture (90-93% wb)", "Author & Year": "Gunnarsson, C.C. & Petersen, C.M. (2007)", "Reference Title": "Water hyacinths as a resource in agriculture and energy production: a review.", "DOI/Link": "10.1111/j.1751-8369.2007.00004.x"},
            {"Discipline": "Process Economics", "Model Application": "Discounted Annuity Capital Recovery Factor (CRF) & Net OPEX", "Author & Year": "Peters, M.S., Timmerhaus, K.D. & West, R.E. (2003)", "Reference Title": "Plant Design and Economics for Chemical Engineers (5th ed.), McGraw-Hill.", "DOI/Link": "ISBN: 978-0072392661"},
            {"Discipline": "Chemical Thermodynamics", "Model Application": "Latent Heat of Vaporization & Biomass Cp Formulations", "Author & Year": "Smith, J.M., Van Ness, H.C. & Abbott, M.M. (2005)", "Reference Title": "Introduction to Chemical Engineering Thermodynamics (7th ed.).", "DOI/Link": "ISBN: 978-0073104454"}
        ]
        st.dataframe(pd.DataFrame(refs), use_container_width=True, hide_index=True)
