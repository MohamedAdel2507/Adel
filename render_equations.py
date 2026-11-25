"""Generate crisp LaTeX mathematical equations and flow diagrams for the handbook."""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

os.makedirs("math_eqs", exist_ok=True)
os.makedirs("diagrams", exist_ok=True)

plt.rcParams.update({
    "font.size": 12,
    "mathtext.fontset": "cm",
})

def render_math(filename, latex_str, fontsize=13, color="#0d47a1", dpi=300):
    fig = plt.figure(figsize=(8, 0.8), dpi=dpi)
    fig.patch.set_alpha(0.0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    ax.text(0.02, 0.5, f"${latex_str}$", fontsize=fontsize, color=color, va='center', ha='left')
    plt.savefig(f"math_eqs/{filename}.png", bbox_inches='tight', transparent=True, pad_inches=0.04, dpi=dpi)
    plt.close()

equations = {
    # Module 01
    "eq_m01_dry": r"\dot{m}_{\mathrm{dry}} = \dot{m}_{\mathrm{wet}} \times \left(1 - \frac{MC_{\mathrm{wb}}}{100}\right)",
    "eq_m01_water": r"\dot{m}_{\mathrm{water, raw}} = \dot{m}_{\mathrm{wet}} \times \left(\frac{MC_{\mathrm{wb}}}{100}\right)",
    "eq_m01_components": r"\dot{m}_i = \dot{m}_{\mathrm{dry}} \times \left(\frac{C_i}{100}\right) \quad \forall \; i \in \{\mathrm{Cell., \; Hemi., \; Lig., \; Ash., \; Others}\}",
    "eq_m01_unchar": r"C_{\mathrm{unchar}} = \max\left(0, \; 100 - \sum C_i\right) \longrightarrow \dot{m}_{\mathrm{unchar}} = \dot{m}_{\mathrm{dry}} \times \frac{C_{\mathrm{unchar}}}{100}",

    # Module 02
    "eq_m02_pretreat": r"\dot{m}_{\mathrm{ret}, i} = \dot{m}_i \cdot f_{\mathrm{ret}}, \quad \dot{m}_{\mathrm{diss}, i} = \dot{m}_i \cdot f_{\mathrm{sol}}, \quad \dot{m}_{\mathrm{deg}} = \sum \dot{m}_i \cdot f_{\mathrm{deg}}",
    "eq_m02_hydrolysis_stoich": r"F_{\mathrm{hydration}} = \frac{M_{\mathrm{monomer}}}{M_{\mathrm{polymer}}} = 1.1111 \; (\mathrm{Hexoses}), \quad 1.1364 \; (\mathrm{Pentoses})",
    "eq_m02_sugars": r"\dot{m}_{\mathrm{sugar}, j} = \left(\dot{m}_{\mathrm{ret}, j} \cdot \eta_{\mathrm{hyd}, j} \cdot F_{\mathrm{hydration}, j}\right) + \dot{m}_{\mathrm{measured}, j}",
    "eq_m02_fermentation": r"\dot{m}_{\mathrm{eth, crude}} = \sum_{j} \left(\dot{m}_{\mathrm{sugar}, j} \cdot \eta_{\mathrm{ferm}, j} \cdot 0.5114\right) \quad \left[\frac{\mathrm{g \; ethanol}}{\mathrm{g \; sugar}}\right]",
    "eq_m02_recovery": r"\dot{m}_{\mathrm{eth, recovered}} = \dot{m}_{\mathrm{eth, crude}} \cdot \eta_{\mathrm{recovery}}, \quad \dot{m}_{\mathrm{eth, lost}} = \dot{m}_{\mathrm{eth, crude}} \cdot (1 - \eta_{\mathrm{recovery}})",
    "eq_m02_co2": r"\dot{m}_{\mathrm{CO}_2} = \dot{m}_{\mathrm{eth, crude}} \times \left(\frac{2 \times 44.01}{2 \times 46.07}\right) = \dot{m}_{\mathrm{eth, crude}} \times 0.9553",

    # Mass Balance Derivations
    "eq_mb_in": r"\text{Total IN} = \dot{m}_{\mathrm{dry}} + \dot{m}_{\mathrm{hyd\_water}} + \dot{m}_{\mathrm{measured\_sugars}}",
    "eq_mb_hyd_water": r"\dot{m}_{\mathrm{hyd\_water}} = \sum_{j} \dot{m}_{\mathrm{sugar}, j} - \sum_{j} \left(\dot{m}_{\mathrm{ret}, j} \cdot \eta_{\mathrm{hyd}, j}\right)",
    "eq_mb_out": r"\text{Total OUT} = \dot{m}_{\mathrm{resid\_solids}} + \dot{m}_{\mathrm{diss}} + \dot{m}_{\mathrm{deg}} + \dot{m}_{\mathrm{unferm}} + \dot{m}_{\mathrm{eth, rec}} + \dot{m}_{\mathrm{eth, lost}} + \dot{m}_{\mathrm{CO}_2} + \dot{m}_{\mathrm{unacc}}",
    "eq_mb_solids": r"\dot{m}_{\mathrm{resid\_solids}} = \dot{m}_{\mathrm{ret, lig}} + \dot{m}_{\mathrm{ret, ash}} + \dot{m}_{\mathrm{ret, other}} + \sum_{k} \dot{m}_{\mathrm{ret}, k}(1 - \eta_{\mathrm{hyd}, k})",
    "eq_mb_closure": r"\text{Closure Error } \varepsilon = 100 \times \left(\frac{\text{Total OUT} - \text{Total IN}}{\text{Total IN}}\right) \equiv 0.0000\%",

    # Module 03: Energy
    "eq_m03_dryer": r"Q_{\mathrm{dryer}} = \frac{\dot{m}_{\mathrm{evap}} C_{p, w}(100 - T_{\mathrm{in}}) + \dot{m}_{\mathrm{evap}} \Delta H_{\mathrm{vap}} + \dot{m}_{\mathrm{dry}} C_{p, b}(100 - T_{\mathrm{in}})}{\eta_{\mathrm{dryer}}}",
    "eq_m03_pretreat": r"Q_{\mathrm{pretreat}} = \frac{\left(\dot{m}_{\mathrm{slurry\_liq}} C_{p, w} + \dot{m}_{\mathrm{dry}} C_{p, b}\right)(T_{\mathrm{pre}} - T_{\mathrm{in}}) + Q_{\mathrm{hold\_loss}}}{\eta_{\mathrm{heater}}}",
    "eq_m03_dist": r"V_{\mathrm{broth}} = \frac{\dot{m}_{\mathrm{eth, rec}} / \rho_{\mathrm{eth}}}{C_{\mathrm{broth, vol\%}} / 100} \cdot \frac{1}{1000} \longrightarrow Q_{\mathrm{dist}} = \frac{V_{\mathrm{broth}} \cdot q_{\mathrm{spec, dist}}}{\eta_{\mathrm{dist\_heater}}}",
    "eq_m03_net": r"Q_{\mathrm{net}} = \left(Q_{\mathrm{dryer}} + Q_{\mathrm{pretreat}} + Q_{\mathrm{dist}} + Q_{\mathrm{dehyd}} + Q_{\mathrm{ferm\_cool}}\right) - \left(Q_{\mathrm{pretreat}} + Q_{\mathrm{dist}}\right)\eta_{\mathrm{heat\_rec}}",
    "eq_m03_elec": r"E_{\mathrm{total}} = E_{\mathrm{wash}} + E_{\mathrm{mill}} + E_{\mathrm{slurry}} + E_{\mathrm{filter}} + E_{\mathrm{ferm}} + E_{\mathrm{centrifuge}} + E_{\mathrm{aux}} \quad [\mathrm{kWh/day}]",

    # Module 04 & 05
    "eq_m04_circ": r"\mathrm{SRR} = \frac{\dot{m}_{\mathrm{solids, rec}}}{\dot{m}_{\mathrm{solids, tot}}} \times 100\%, \quad \mathrm{WRR} = \frac{\dot{m}_{\mathrm{water, rec}}}{\dot{m}_{\mathrm{wastewater}}} \times 100\%, \quad \mathrm{CUR} = \frac{\dot{m}_{\mathrm{CO}_2, \mathrm{util}}}{\dot{m}_{\mathrm{CO}_2, \mathrm{gen}}} \times 100\%",
    "eq_m05_crf": r"\mathrm{CRF} = \frac{r(1 + r)^n}{(1 + r)^n - 1} \longrightarrow \text{Annual Capital Charge} = \mathrm{CAPEX} \times \mathrm{CRF} \quad [\mathrm{EGP/yr}]",
    "eq_m05_opex": r"\mathrm{OPEX}_{\mathrm{net}} = \max\left(0, \; \sum (\text{Annual Quantities} \times \text{Tariffs}) + \text{Fixed OPEX} - \text{Energy Credit}\right)",
    "eq_m05_breakeven": r"P_{\mathrm{be, operating}} = \frac{\mathrm{OPEX}_{\mathrm{net}} - \mathrm{Revenue}_{\mathrm{byproducts}}}{V_{\mathrm{ethanol, annual}}}, \quad P_{\mathrm{be, capital}} = \frac{\mathrm{OPEX}_{\mathrm{net}} + \text{Capital Charge} - \mathrm{Revenue}_{\mathrm{byproducts}}}{V_{\mathrm{ethanol, annual}}}",
    "eq_m05_payback": r"\text{Simple Payback Period} = \frac{\mathrm{CAPEX}}{\text{Operating Profit}} = \frac{\mathrm{CAPEX}}{\mathrm{Revenue} - \mathrm{OPEX}_{\mathrm{net}}} \quad [\mathrm{years}]"
}

for name, latex in equations.items():
    render_math(name, latex)

print(f"Rendered {len(equations)} mathematical equations to math_eqs/")
