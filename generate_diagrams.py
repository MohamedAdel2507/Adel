"""Generate clear visual diagrams for the HYACINTH-X technical handbook."""
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("diagrams", exist_ok=True)

def create_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=300)
    ax.axis('off')
    
    # Title
    ax.text(5.0, 4.2, "HYACINTH-X Information & Material Flow Architecture", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#1b5e20')
    
    # Modules boxes
    modules = [
        ("M01: Feedstock\nAnalyzer", (0.5, 2.2), "#e8f5e9", "#2e7d32"),
        ("M02: Process\nYield Estimator", (2.8, 2.2), "#e3f2fd", "#1565c0"),
        ("M03: Energy &\nUtilities", (5.1, 2.2), "#fff3e0", "#e65100"),
        ("M04: Zero-Waste\nManager", (7.4, 2.2), "#f3e5f5", "#7b1fa2"),
        ("M05: Techno-Economic\nAnalysis (TEA)", (5.1, 0.4), "#fbe9e7", "#c62828")
    ]
    
    for name, (x, y), face, edge in modules:
        rect = patches.FancyBboxPatch((x, y), 1.8, 1.1, boxstyle="round,pad=0.1,rounding_size=0.15",
                                      facecolor=face, edgecolor=edge, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 0.9, y + 0.55, name, ha='center', va='center', fontsize=9, fontweight='bold', color=edge)

    # Arrows and labels
    # M01 -> M02
    ax.annotate('', xy=(2.8, 2.75), xytext=(2.3, 2.75),
                arrowprops=dict(facecolor='#2e7d32', edgecolor='#2e7d32', arrowstyle='->', lw=2))
    ax.text(2.55, 3.0, "Dry Mass\nComposition", ha='center', va='bottom', fontsize=7, color='#2e7d32', fontweight='bold')
    
    # M02 -> M03
    ax.annotate('', xy=(5.1, 2.75), xytext=(4.6, 2.75),
                arrowprops=dict(facecolor='#1565c0', edgecolor='#1565c0', arrowstyle='->', lw=2))
    ax.text(4.85, 3.0, "Recovered\nEthanol", ha='center', va='bottom', fontsize=7, color='#1565c0', fontweight='bold')

    # M01 -> M03 (curved up)
    ax.annotate('', xy=(5.8, 3.3), xytext=(1.4, 3.3),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.25", color='#2e7d32', lw=1.5, ls='--'))
    ax.text(3.6, 3.9, "Dry Mass & Raw Moisture (Drying Load)", ha='center', va='center', fontsize=7.5, color='#2e7d32', style='italic')

    # M02 -> M04 (curved up)
    ax.annotate('', xy=(8.1, 3.3), xytext=(3.7, 3.3),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.2", color='#1565c0', lw=1.5, ls='--'))
    ax.text(5.9, 3.75, "Residual Lignin, Ash, Unhydrolyzed Solids, Fermentation CO₂", ha='center', va='center', fontsize=7.5, color='#1565c0', style='italic')

    # M03 -> M04
    ax.annotate('', xy=(7.4, 2.75), xytext=(6.9, 2.75),
                arrowprops=dict(facecolor='#e65100', edgecolor='#e65100', arrowstyle='->', lw=2))
    ax.text(7.15, 3.0, "Wastewater\nStreams", ha='center', va='bottom', fontsize=7, color='#e65100', fontweight='bold')

    # To M05
    # M03 -> M05
    ax.annotate('', xy=(6.0, 1.5), xytext=(6.0, 2.2),
                arrowprops=dict(facecolor='#e65100', edgecolor='#e65100', arrowstyle='->', lw=2))
    ax.text(6.1, 1.85, "Utilities (Thermal/Elec) & Ethanol L/yr", ha='left', va='center', fontsize=7, color='#e65100')

    # M04 -> M05
    ax.annotate('', xy=(6.9, 0.95), xytext=(7.4, 2.2),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2", color='#7b1fa2', lw=1.5))
    ax.text(7.5, 1.3, "Freshwater Deficit, Biochar,\nResidues for Combustion", ha='left', va='center', fontsize=7, color='#7b1fa2')

    # M01 -> M05
    ax.annotate('', xy=(5.1, 0.95), xytext=(1.4, 2.2),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2", color='#2e7d32', lw=1.5))
    ax.text(2.6, 1.3, "Wet Feed Purchased (kg/yr)", ha='center', va='center', fontsize=7, color='#2e7d32')

    plt.tight_layout()
    plt.savefig("diagrams/pipeline_flow.png", bbox_inches='tight')
    plt.close()

def create_mass_balance_diagram():
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=300)
    ax.axis('off')
    
    ax.text(5.0, 3.9, "Module 02 Organic Mass Boundary & Water Incorporation", 
            ha='center', va='center', fontsize=13, fontweight='bold', color='#1565c0')
    
    # Boundary box
    rect = patches.FancyBboxPatch((3.0, 0.5), 4.0, 2.8, boxstyle="round,pad=0.15,rounding_size=0.2",
                                  facecolor='#f5f5f5', edgecolor='#1565c0', linewidth=2.5, linestyle='--')
    ax.add_patch(rect)
    ax.text(5.0, 3.0, "SYSTEM BOUNDARY: REACTION & SEPARATION", ha='center', va='center', fontsize=9, fontweight='bold', color='#1565c0')
    
    # Inner processes
    ax.text(5.0, 2.3, "Pretreatment Fractionation\n(Solids retained: 90% | Solubilized: 7% | Degraded: 3%)", ha='center', va='center', fontsize=8, color='#333333')
    ax.text(5.0, 1.6, "Enzymatic Hydrolysis\n(Glucan → Glucose, Xylan → Xylose, Mannan → Mannose)", ha='center', va='center', fontsize=8, color='#333333')
    ax.text(5.0, 0.9, "Fermentation & Product Recovery\n(Hexose/Pentose → Ethanol + CO₂)", ha='center', va='center', fontsize=8, color='#333333')

    # IN ARROWS
    inputs = [
        ("Dry Biomass Input\n(m_dry)", 2.7),
        ("Hydrolysis Water Consumed\n(Stoichiometric +11.1% to +13.6%)", 1.8),
        ("Measured Soluble Sugars\n(Optional feed sugars)", 0.9)
    ]
    for lbl, y in inputs:
        ax.annotate('', xy=(3.0, y), xytext=(0.8, y),
                    arrowprops=dict(facecolor='#2e7d32', edgecolor='#2e7d32', arrowstyle='->', lw=2))
        ax.text(0.7, y, lbl, ha='right', va='center', fontsize=8, fontweight='bold', color='#2e7d32')

    # OUT ARROWS
    outputs = [
        ("Recovered Bioethanol (95% recovery)", 3.0, '#1565c0'),
        ("Fermentation CO₂ (Stoichiometric 0.955 kg/kg)", 2.4, '#37474f'),
        ("Residual Solids (Lignin, Ash, Unhydrolyzed Fiber)", 1.8, '#6d4c41'),
        ("Soluble Pretreatment Stream (Dissolved & Extractives)", 1.2, '#7b1fa2'),
        ("Byproducts (Degraded mass, Ethanol loss, Unfermented sugars)", 0.6, '#c62828')
    ]
    for lbl, y, col in outputs:
        ax.annotate('', xy=(9.2, y), xytext=(7.0, y),
                    arrowprops=dict(facecolor=col, edgecolor=col, arrowstyle='->', lw=2))
        ax.text(9.3, y, lbl, ha='left', va='center', fontsize=8, fontweight='bold', color=col)

    plt.tight_layout()
    plt.savefig("diagrams/mass_balance.png", bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_pipeline_diagram()
    create_mass_balance_diagram()
    print("Diagrams successfully generated in diagrams/ directory.")
