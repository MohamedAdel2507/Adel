"""HYACINTH-X UI Components & Visualization Engine.

Provides an industrial, modern engineering visual theme using Plotly and styled containers.
Replaces table-heavy displays with Sankey diagrams, waterfall balances, interactive donuts,
and custom engineering KPI metrics without altering any underlying calculations.
"""
from __future__ import annotations

from typing import Any, Dict, List
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ----------------- Industrial Design System Colors -----------------
PALETTE = {
    "primary": "#1b5e20",       # Deep Forest / Bio Green
    "secondary": "#2e7d32",     # Leaf Green
    "accent_blue": "#0277bd",   # Process Liquid / Water Blue
    "accent_amber": "#f57f17",  # Thermal / Energy Gold
    "accent_purple": "#6a1b9a", # Zero-Waste / Circular
    "accent_red": "#c62828",    # Economic / Cost
    "accent_teal": "#00695c",   # Cellulose / Glucan
    "bg_card": "#ffffff",
    "bg_subtle": "#f8f9fa",
    "text_dark": "#1a202c",
    "text_muted": "#718096",
    "border": "#e2e8f0",
}

PLOTLY_LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12, color="#2d3748"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=20, r=20, t=35, b=25),
    hoverlabel=dict(bgcolor="#1a202c", font_size=12, font_color="#ffffff"),
)


def inject_custom_css():
    """Injects high-grade industrial stylesheet for modern engineering aesthetics."""
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }

    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: 1480px;
    }

    /* Top Brand Navigation Bar */
    .brand-header {
        background: linear-gradient(135deg, #134e19 0%, #1b5e20 50%, #2e7d32 100%);
        border-radius: 12px;
        padding: 1.4rem 1.8rem;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(27, 94, 32, 0.15);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .brand-title {
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .brand-subtitle {
        font-size: 0.88rem;
        color: #c8e6c9;
        margin-top: 0.25rem;
        font-weight: 400;
    }
    .brand-badge {
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 20px;
        padding: 0.35rem 0.85rem;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    /* KPI Cards */
    .kpi-container {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        margin-bottom: 0.8rem;
        border-left: 4px solid #1b5e20;
    }
    .kpi-container:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.06);
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #718096;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 1.45rem;
        font-weight: 800;
        color: #1a202c;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 0.76rem;
        color: #4a5568;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* Section Cards */
    .section-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }

    /* Custom Streamlit Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8fafc;
        padding: 6px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        padding: 0 18px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #4a5568;
        border: none !important;
        background-color: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #1b5e20 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08) !important;
    }

    /* Button Styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 1.2rem;
        transition: all 0.2s;
    }
    </style>
    """, unsafe_allow_html=True)


def kpi_card(title: str, value: str, subtext: str = "", border_color: str = "#1b5e20"):
    """Renders a modern, industrial KPI summary card."""
    html = f"""
    <div class="kpi-container" style="border-left-color: {border_color};">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-sub">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ----------------- Plotly Visualizations Engine -----------------

def plot_feedstock_breakdown(component_dict: Dict[str, float], wet_feed: float, dry_biomass: float) -> go.Figure:
    """Renders interactive Donut Chart of Biomass Chemical Pools with Dry Mass Breakdown."""
    labels = list(component_dict.keys())
    values = list(component_dict.values())
    
    color_map = {
        "Cellulose": "#2e7d32",
        "Hemicellulose": "#66bb6a",
        "Lignin": "#8d6e63",
        "Ash": "#78909c",
        "Other characterized components": "#ffa726",
        "Other / extractives": "#ffb74d"
    }
    marker_colors = [color_map.get(k, "#9e9e9e") for k in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(colors=marker_colors, line=dict(color="#ffffff", width=2)),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Daily Flow: %{value:.2f} kg/day<br>Share: %{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        title=dict(text="<b>Dry Biomass Chemical Composition (Dry Basis)</b>", font=dict(size=14, color="#1b5e20")),
        annotations=[dict(text=f"<b>{dry_biomass:,.0f}</b><br><span style='font-size:10px;'>kg/d dry</span>", x=0.5, y=0.5, font_size=15, showarrow=False)],
        showlegend=False,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig


def plot_mass_balance_sankey(r1: dict, r2: dict, mb: dict) -> go.Figure:
    """Builds a comprehensive Sankey diagram of the Organic Matter & Hydration Water Pipeline."""
    labels = [
        "Raw Biomass (Dry Basis)",    # 0
        "Chemically Bound Water",     # 1
        "Pretreatment Reactor",       # 2
        "Retained Solid Fibers",      # 3
        "Dissolved Liquor Solubles",  # 4
        "Degradation Inhibitors",     # 5
        "Enzymatic Hydrolysis",       # 6
        "Fermentable Sugars",         # 7
        "Unhydrolyzed Insoluble Residue", # 8
        "Fermentation",               # 9
        "Recovered Bioethanol",       # 10
        "Fermentation CO₂",           # 11
        "Distillation Losses",        # 12
        "Unfermented Pentoses"        # 13
    ]
    
    colors_nodes = [
        "#1b5e20", "#0277bd", "#37474f", "#2e7d32", "#7b1fa2",
        "#d32f2f", "#43a047", "#00897b", "#8d6e63", "#00acc1",
        "#1565c0", "#78909c", "#e53935", "#fb8c00"
    ]
    
    m_dry = r1["dry_biomass_kg_day"]
    m_hyd = max(0.1, mb["hydrolysis_water_kg"])
    ret_tot = sum(r2["retained_component_kg"].values())
    diss_tot = sum(r2["dissolved_component_kg"].values())
    deg_tot = r2["degraded_kg"]
    sugar_tot = r2["total_sugars_kg"]
    unhyd_tot = mb["outputs"]["Residual solids - unhydrolyzed carbohydrates"] + mb["lignin_residue_kg"] + mb["ash_residue_kg"]
    ferm_sugar = r2["total_fermented_sugar_kg"]
    unferm_sugar = mb["unfermented_sugars_kg"]
    eth_rec = r2["recovered_ethanol_kg"]
    eth_lost = mb["ethanol_lost_kg"]
    co2 = mb["co2_kg"]

    sources = [0, 0, 0, 3, 1, 6, 6, 7, 7, 9, 9, 9]
    targets = [2, 4, 5, 6, 6, 7, 8, 9, 13, 10, 11, 12]
    values =  [ret_tot, diss_tot, deg_tot, ret_tot, m_hyd, sugar_tot, unhyd_tot, ferm_sugar, unferm_sugar, eth_rec, co2, eth_lost]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=16,
            thickness=18,
            line=dict(color="#ffffff", width=1),
            label=labels,
            color=colors_nodes
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(180, 205, 230, 0.45)",
            hovertemplate="From: %{source.label}<br>To: %{target.label}<br>Flow: <b>%{value:,.2f} kg/day</b><extra></extra>"
        )
    )])

    fig.update_layout(
        title=dict(text="<b>HYACINTH-X Biorefinery Material & Reaction Flow (kg/day)</b>", font=dict(size=14, color="#1b5e20")),
        height=380,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig


def plot_thermal_waterfall(r3: dict) -> go.Figure:
    """Renders a Waterfall balance of equipment thermal duties and heat recovery credit."""
    thermal_data = r3["thermal_rows"]
    recovered = r3["recovered_heat_mj_day"]
    net = r3["net_thermal_mj_day"]

    names = [row[0].split("(")[0].strip() for row in thermal_data] + ["Heat Recovery Credit", "Net Thermal Demand"]
    values = [row[1] for row in thermal_data] + [-recovered, net]
    measures = ["relative"] * len(thermal_data) + ["relative", "total"]

    fig = go.Figure(go.Waterfall(
        name="Thermal Balance",
        orientation="v",
        measure=measures,
        x=names,
        textposition="outside",
        text=[f"{v:,.0f} MJ" if m != "total" else f"<b>{v:,.0f} MJ</b>" for v, m in zip(values, measures)],
        y=values,
        connector={"line": {"color": "#b0bec5", "width": 1.5}},
        decreasing={"marker": {"color": "#43a047"}},
        increasing={"marker": {"color": "#e65100"}},
        totals={"marker": {"color": "#d84315"}}
    ))

    fig.update_layout(
        title=dict(text="<b>Thermal Utilities Waterfall Balance (MJ/day)</b>", font=dict(size=14, color="#e65100")),
        yaxis=dict(title="Thermal Energy (MJ/day)", gridcolor="#f1f5f9"),
        height=380,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig


def plot_electrical_breakdown(r3: dict) -> go.Figure:
    """Renders interactive Horizontal Bar Chart of Electrical Consumers."""
    rows = r3["electric_rows"]
    df = pd.DataFrame(rows, columns=["Equipment", "kWh_day", "Note"]).sort_values("kWh_day", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["kWh_day"],
        y=df["Equipment"],
        orientation='h',
        marker=dict(color="#0288d1", line=dict(color="#01579b", width=1)),
        text=[f" {v:.1f} kWh/d" for v in df["kWh_day"]],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Demand: %{x:.2f} kWh/day<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="<b>Electrical Demand by Unit Operation (kWh/day)</b>", font=dict(size=14, color="#0277bd")),
        xaxis=dict(title="Electricity (kWh/day)", gridcolor="#f1f5f9"),
        height=320,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig


def plot_zero_waste_radial(indicators: dict) -> go.Figure:
    """Renders Circularity Gauge Indicators for Zero-Waste Performance."""
    solid_rec = indicators.get("solid_residue_recovery_pct", 0.0)
    water_rec = indicators.get("water_recycle_pct", 0.0)
    co2_util = indicators.get("co2_utilization_pct", 0.0)

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=solid_rec,
        title={'text': "<b>Solids Recovery</b>", 'font': {'size': 12}},
        domain={'x': [0.0, 0.30], 'y': [0, 1]},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#2e7d32"},
               'steps': [{'range': [0, 50], 'color': "#e8f5e9"}, {'range': [50, 100], 'color': "#c8e6c9"}]}
    ))

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=water_rec,
        title={'text': "<b>Water Recycled</b>", 'font': {'size': 12}},
        domain={'x': [0.35, 0.65], 'y': [0, 1]},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#0288d1"},
               'steps': [{'range': [0, 50], 'color': "#e1f5fe"}, {'range': [50, 100], 'color': "#b3e5fc"}]}
    ))

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=co2_util,
        title={'text': "<b>CO₂ Utilized</b>", 'font': {'size': 12}},
        domain={'x': [0.70, 1.0], 'y': [0, 1]},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#7b1fa2"},
               'steps': [{'range': [0, 50], 'color': "#f3e5f5"}, {'range': [50, 100], 'color': "#e1bee7"}]}
    ))

    fig.update_layout(
        height=220,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    return fig


def plot_opex_breakdown(r5: dict) -> go.Figure:
    """Renders Treemap / Donut Breakdown of Operating Expenses."""
    costs = r5.get("costs", {})
    non_zero = {k: v for k, v in costs.items() if v > 0}
    
    if not non_zero:
        fig = go.Figure()
        fig.add_annotation(text="No OPEX entered yet.<br>Provide unit prices in Setup tab to visualize costs.",
                           showarrow=False, font=dict(size=13, color="#718096"))
        fig.update_layout(height=280, **PLOTLY_LAYOUT_DEFAULTS)
        return fig

    labels = list(non_zero.keys())
    values = list(non_zero.values())

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Cost: %{value:,.0f} EGP/yr<br>Share: %{percent}<extra></extra>",
        marker=dict(line=dict(color="#ffffff", width=2))
    )])

    fig.update_layout(
        title=dict(text="<b>Annual OPEX Distribution (EGP/year)</b>", font=dict(size=14, color="#c62828")),
        annotations=[dict(text=f"<b>{r5['net_opex']:,.0f}</b><br><span style='font-size:10px;'>EGP/yr Net</span>", x=0.5, y=0.5, font_size=13, showarrow=False)],
        height=320,
        showlegend=False,
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig


def plot_sensitivity_spider(sens_list: List[Dict[str, Any]], base_profit: float) -> go.Figure:
    """Renders Sensitivity Tornado Chart for price elasticity on Operating Profit."""
    if not sens_list:
        return go.Figure()

    df = pd.DataFrame(sens_list)
    df["Positive_Impact"] = df["Profit at +price (EGP/yr)"] - base_profit
    df["Negative_Impact"] = df["Profit at -price (EGP/yr)"] - base_profit

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df["Variable"],
        x=df["Negative_Impact"],
        name="Price Decrease (-)",
        orientation='h',
        marker=dict(color="#43a047")
    ))
    fig.add_trace(go.Bar(
        y=df["Variable"],
        x=df["Positive_Impact"],
        name="Price Increase (+)",
        orientation='h',
        marker=dict(color="#e53935")
    ))

    fig.update_layout(
        barmode='relative',
        title=dict(text="<b>Sensitivity Impact on Operating Profit (Delta EGP/yr)</b>", font=dict(size=14, color="#1b5e20")),
        xaxis=dict(title="Profit Variance vs Baseline (EGP/year)", gridcolor="#f1f5f9"),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **PLOTLY_LAYOUT_DEFAULTS
    )
    return fig
