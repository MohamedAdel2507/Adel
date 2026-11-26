"""Generate clear, bold, publication-quality diagrams for the PDF."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("diagrams", exist_ok=True)

def generate_flowsheet():
    # Width 10 inches, height 4.2 inches, 150 DPI = 1500 x 630 px
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.5)
    ax.axis('off')

    # Main pipeline boxes
    modules = [
        ("M01: Feedstock\nAnalyzer", (0.3, 2.3), "#E8F5E9", "#2E7D32"),
        ("M02: Process\nYield Estimator", (2.7, 2.3), "#E3F2FD", "#1565C0"),
        ("M03: Energy &\nUtilities", (5.1, 2.3), "#FFF3E0", "#E65100"),
        ("M04: Zero-Waste\nManager", (7.5, 2.3), "#F3E5F5", "#7B1FA2"),
        ("M05: Techno-Economic\nAnalysis (TEA)", (4.8, 0.4), "#FFEBEE", "#C62828")
    ]

    for name, (x, y), face, edge in modules:
        rect = patches.FancyBboxPatch((x, y), 2.0, 1.2, boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=face, edgecolor=edge, linewidth=2.5)
        ax.add_patch(rect)
        ax.text(x + 1.0, y + 0.6, name, ha='center', va='center', fontsize=11, fontweight='bold', color=edge)

    # Arrows between linear modules
    # M01 -> M02
    ax.annotate('', xy=(2.7, 2.9), xytext=(2.3, 2.9),
                arrowprops=dict(facecolor='#2E7D32', edgecolor='#2E7D32', width=2.5, headwidth=8))
    ax.text(2.5, 3.1, "Dry Mass\nComposition", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#2E7D32')

    # M02 -> M03
    ax.annotate('', xy=(5.1, 2.9), xytext=(4.7, 2.9),
                arrowprops=dict(facecolor='#1565C0', edgecolor='#1565C0', width=2.5, headwidth=8))
    ax.text(4.9, 3.1, "Recovered\nEthanol", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1565C0')

    # M03 -> M04
    ax.annotate('', xy=(7.5, 2.9), xytext=(7.1, 2.9),
                arrowprops=dict(facecolor='#E65100', edgecolor='#E65100', width=2.5, headwidth=8))
    ax.text(7.3, 3.1, "Wastewater\nStreams", ha='center', va='bottom', fontsize=9, fontweight='bold', color='#E65100')

    # M01 -> M03 curved overhead arrow
    ax.annotate('', xy=(6.1, 3.5), xytext=(1.3, 3.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.22", color='#2E7D32', lw=2.2, ls='--'))
    ax.text(3.7, 4.25, "Dry Mass & Raw Moisture (Drying Load)", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#2E7D32')

    # M02 -> M04 curved overhead arrow
    ax.annotate('', xy=(8.5, 3.5), xytext=(3.7, 3.5),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.18", color='#1565C0', lw=2.2, ls='--'))
    ax.text(6.1, 4.0, "Residual Lignin, Ash, Unhydrolyzed Fiber, CO₂", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1565C0')

    # Connections to M05
    # M01 -> M05
    ax.annotate('', xy=(4.8, 1.0), xytext=(1.3, 2.3),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.18", color='#2E7D32', lw=2))
    ax.text(2.6, 1.3, "Wet Biomass (kg/yr)", ha='center', va='center', fontsize=9, fontweight='bold', color='#2E7D32')

    # M03 -> M05
    ax.annotate('', xy=(5.8, 1.6), xytext=(5.8, 2.3),
                arrowprops=dict(facecolor='#E65100', edgecolor='#E65100', width=2.5, headwidth=8))
    ax.text(5.95, 1.95, "Utilities (Thermal/Elec) & Ethanol L/yr", ha='left', va='center', fontsize=9, fontweight='bold', color='#E65100')

    # M04 -> M05
    ax.annotate('', xy=(6.8, 1.0), xytext=(8.5, 2.3),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.18", color='#7B1FA2', lw=2))
    ax.text(8.0, 1.3, "Fresh Water Deficit,\nBiochar & Energy Credit", ha='center', va='center', fontsize=9, fontweight='bold', color='#7B1FA2')

    plt.savefig("diagrams/pipeline_flow.png", dpi=150, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print("pipeline_flow.png regenerated.")


def generate_mass_balance():
    fig, ax = plt.subplots(figsize=(10, 4.0), dpi=150)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.0)
    ax.axis('off')

    # System boundary
    rect = patches.FancyBboxPatch((3.0, 0.4), 4.0, 3.2, boxstyle="round,pad=0.1,rounding_size=0.2",
                                  facecolor='#F8F9FA', edgecolor='#1565C0', linewidth=3, linestyle='--')
    ax.add_patch(rect)
    ax.text(5.0, 3.3, "SYSTEM BOUNDARY: REACTION & RECOVERY", ha='center', va='center', fontsize=11, fontweight='bold', color='#1565C0')

    # Inner process labels
    ax.text(5.0, 2.5, "1. Pretreatment Fractionation\n(Solids retained: 90% | Dissolved: 7% | Degraded: 3%)", ha='center', va='center', fontsize=9, color='#333333')
    ax.text(5.0, 1.7, "2. Enzymatic Hydrolysis with Hydration\n(Glucan → Glucose, Xylan → Xylose, Mannan → Mannose)", ha='center', va='center', fontsize=9, color='#333333')
    ax.text(5.0, 0.9, "3. Fermentation & Product Distillation\n(Hexose & Pentose → Bioethanol + CO₂)", ha='center', va='center', fontsize=9, color='#333333')

    # Inflow arrows
    inputs = [
        ("Dry Biomass (m_dry)", 2.8),
        ("Bound Hydrolysis Water (+11% to +13%)", 1.9),
        ("Measured Soluble Feed Sugars", 1.0)
    ]
    for lbl, y in inputs:
        ax.annotate('', xy=(3.0, y), xytext=(1.0, y),
                    arrowprops=dict(facecolor='#2E7D32', edgecolor='#2E7D32', width=2.5, headwidth=8))
        ax.text(0.9, y, lbl, ha='right', va='center', fontsize=9, fontweight='bold', color='#2E7D32')

    # Outflow arrows
    outputs = [
        ("Recovered Bioethanol (95% recovery)", 3.1, '#1565C0'),
        ("Fermentation CO₂ (Stoichiometric 0.955 kg/kg)", 2.5, '#37474F'),
        ("Residual Solids (Lignin, Ash, Fiber)", 1.9, '#6D4C41'),
        ("Dissolved Pretreatment Liquor Organics", 1.3, '#7B1FA2'),
        ("Byproducts (Degraded Inhibitors, Unfermented Sugars, Losses)", 0.7, '#C62828')
    ]
    for lbl, y, col in outputs:
        ax.annotate('', xy=(9.0, y), xytext=(7.0, y),
                    arrowprops=dict(facecolor=col, edgecolor=col, width=2.5, headwidth=8))
        ax.text(9.1, y, lbl, ha='left', va='center', fontsize=9, fontweight='bold', color=col)

    plt.savefig("diagrams/mass_balance.png", dpi=150, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print("mass_balance.png regenerated.")

if __name__ == "__main__":
    generate_flowsheet()
    generate_mass_balance()
