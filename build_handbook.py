"""Enhanced Technical Formulation and Derivation Handbook for HYACINTH-X."""
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.pdfgen import canvas

class ElegantNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        
        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "HYACINTH-X — Technical Reference Manual: Mathematical Models & Balance Derivations")
            self.setStrokeColor(colors.HexColor("#1b5e20"))
            self.setLineWidth(1)
            self.line(54, 748, 558, 748)
            
        # Running Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_str)
        self.drawString(54, 32, "HYACINTH-X Biorefinery Engineering Suite • Academic & Research Staff Documentation")
        self.setStrokeColor(colors.HexColor("#BDBDBD"))
        self.setLineWidth(0.5)
        self.line(54, 42, 558, 42)
        self.restoreState()


def make_equation_box(eq_html, explanation_html, width=504):
    """Formats an equation in a clean, professional, publication-quality box."""
    style_eq = ParagraphStyle(
        'EqBox',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#0d47a1"),
        spaceAfter=3
    )
    style_exp = ParagraphStyle(
        'ExpBox',
        fontName='Helvetica',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#263238")
    )
    
    t_data = [
        [Paragraph(eq_html, style_eq)],
        [Paragraph(f"<b>Where:</b> {explanation_html}", style_exp)]
    ]
    t = Table(t_data, colWidths=[width])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f4f8fb")),
        ('LINELEFT', (0,0), (0,-1), 3.5, colors.HexColor("#1976d2")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cfd8dc")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 9),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    return t


def build_handbook(filename="HYACINTH_X_Technical_Formulations_Handbook.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    doc_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1b5e20"),
        spaceAfter=4
    )

    doc_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14.5,
        textColor=colors.HexColor("#37474f"),
        spaceAfter=10
    )

    sec_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1b5e20"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    subsec_title = ParagraphStyle(
        'SubSecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#2e7d32"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#212121"),
        spaceAfter=5
    )

    bullet = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#212121"),
        leftIndent=12,
        spaceAfter=3
    )

    caption = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#555555"),
        alignment=1,
        spaceAfter=8
    )

    story = []

    # ================= COVER / HEADER =================
    story.append(Paragraph("🌿 HYACINTH-X Biorefinery Engineering Suite", doc_title))
    story.append(Paragraph("<b>Mathematical Model Specification, Complete Equation Derivations, and Mass & Energy Balances</b>", doc_sub))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2e7d32"), spaceAfter=8))

    meta_table = [
        ["Feedstock Target:", "Water Hyacinth (Eichhornia crassipes)", "Target Product:", "Anhydrous Fuel Bioethanol (2G)"],
        ["Integration Topology:", "Acyclic Sequential Pipeline (M01 → M05)", "Verification:", "Closed Mass Balance (Error < 0.001%)"],
        ["Version / Scope:", "Release 2.1 — Staff & Faculty Review", "Date of Audit:", "Academic Year 2026/2027"]
    ]
    t_meta = Table(meta_table, colWidths=[95, 155, 95, 159])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 10),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#333333")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f8e9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#a5d6a7")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # ================= SECTION 1 =================
    story.append(Paragraph("1. System Architecture & Inter-Module Data Flow", sec_title))
    story.append(Paragraph(
        "HYACINTH-X models an integrated lignocellulosic biorefinery. The calculation graph is completely acyclic: "
        "no iterative feedback loops or undefined inputs exist. Each module strictly receives upstream physical streams "
        "and passes rigorously derived outputs to downstream operations.",
        body
    ))

    # Insert pipeline diagram if exists
    if os.path.exists("diagrams/pipeline_flow.png"):
        story.append(Image("diagrams/pipeline_flow.png", width=6.8*72, height=3.06*72))
        story.append(Paragraph("Figure 1: Complete Information & Material Transfer Map Across Modules 01 to 05.", caption))
    
    story.append(Spacer(1, 4))

    # Data Transfer Ledger Table
    transfer_table = [
        ["Module Handoff", "Transfer Variable", "Units", "Physical Meaning & Downstream Function"],
        ["M01 → M02", "Dry Biomass (m_dry)", "kg/day", "Organic mass baseline. Isolates biochemical reactions from feed moisture."],
        ["M01 → M02", "Composition (6 pools)", "% dry basis", "Polymer fractions: Cellulose, Xylan, Mannan, Lignin, Ash, Extractives."],
        ["M01 → M03", "Dry Mass & Raw Moisture", "kg/d, % wb", "Governs the water evaporation duty in the pre-treatment dryer."],
        ["M02 → M03", "Recovered Ethanol", "kg/day", "Dictates fermentation broth volume, column distillation steam, & dehydration."],
        ["M02 → M04", "Residual Solids", "kg/day", "Unhydrolyzed carbohydrates, lignin, and ash allocated to circular reuse."],
        ["M02 → M04", "Fermentation CO₂", "kg/day", "Stoichiometric byproduct from hexose/pentose metabolic catabolism."],
        ["M03 → M04", "Wastewater Streams", "kg/day", "Sum of biomass washing effluent and liquid from pretreatment slurry."],
        ["M01-M04 → M05", "Annualized Totals", "L/yr, kWh/yr", "Ethanol revenue, utility OPEX, fresh water tariff, and byproduct credits."]
    ]
    t_transfer = Table(transfer_table, colWidths=[65, 105, 55, 279])
    t_transfer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f5e9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 9.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e0e0e0")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_transfer)

    story.append(PageBreak())

    # ================= SECTION 2 =================
    story.append(Paragraph("2. Module 01: Feedstock Analyzer — Mathematical Equations", sec_title))
    story.append(Paragraph(
        "Water hyacinth typically features an extremely high moisture content (90% to 93% wet basis). Module 01 separates "
        "the raw harvested wet harvest into moisture and structural dry constituents.",
        body
    ))

    # Eq 1
    story.append(make_equation_box(
        "m_dry = m_wet · (1 - MC_wb / 100)",
        "<b>m_dry:</b> dry biomass daily mass flow (kg/day); <b>m_wet:</b> total harvested wet biomass (kg/day); "
        "<b>MC_wb:</b> moisture content on a wet basis (%)."
    ))
    story.append(Spacer(1, 4))

    # Eq 2
    story.append(make_equation_box(
        "m_water_raw = m_wet · (MC_wb / 100)",
        "<b>m_water_raw:</b> total liquid water physically present in the incoming wet biomass (kg/day)."
    ))
    story.append(Spacer(1, 4))

    # Eq 3
    story.append(make_equation_box(
        "m_i = m_dry · (C_i / 100) &nbsp;&nbsp;&nbsp; for i ∈ {Cellulose, Hemicellulose, Lignin, Ash, Others}",
        "<b>m_i:</b> mass of constituent <i>i</i> (kg/day); <b>C_i:</b> dry-basis percentage mass fraction (%)."
    ))
    story.append(Spacer(1, 4))

    # Eq 4
    story.append(make_equation_box(
        "C_unchar = max(0, 100 - ∑ C_i) &nbsp;⇒&nbsp; m_unchar = m_dry · (C_unchar / 100)",
        "<b>C_unchar:</b> uncharacterized extractives/dry matter. The model enforces an analytical tolerance of ±0.5%. "
        "Any analytical shortfall is carried explicitly downstream into 'Other / extractives' to prevent artificial loss."
    ))

    story.append(Spacer(1, 8))

    # ================= SECTION 3 =================
    story.append(Paragraph("3. Module 02: Process Yield & Reaction Stoichiometry", sec_title))
    story.append(Paragraph(
        "This module tracks polymer breakdown through three distinct unit operations: thermal pretreatment split, "
        "enzymatic hydrolysis with stoichiometric water uptake, and fermentation to ethanol with CO₂ evolution.",
        body
    ))

    story.append(Paragraph("<b>A. Pretreatment Solid-Liquid Fractionation:</b>", subsec_title))
    story.append(Paragraph(
        "Pretreatment ruptures the cell wall, dissolving a portion of polymers and generating degradation inhibitors:",
        body
    ))
    story.append(make_equation_box(
        "m_retained,i = m_i · f_solid_retention &nbsp;&nbsp;|&nbsp;&nbsp; "
        "m_dissolved,i = m_i · f_solubilized &nbsp;&nbsp;|&nbsp;&nbsp; "
        "m_degraded = ∑ m_i · f_degraded",
        "<b>f_solid_retention:</b> solid fiber fraction retained for enzymatic attack (default = 0.90); "
        "<b>f_solubilized:</b> soluble fraction entering liquid liquor (default = 0.07); "
        "<b>f_degraded:</b> fraction converted to furfurals, HMF, or organic acids (default = 0.03). "
        "<i>Constraint:</i> f_solid_retention + f_solubilized + f_degraded ≤ 1.0."
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>B. Enzymatic Hydrolysis & Water-of-Hydration Stoichiometry:</b>", subsec_title))
    story.append(Paragraph(
        "Cellulose, xylan, and mannan are poly-anhydro-sugars. When cleaved by enzymes, one water molecule (18.015 g/mol) is chemically "
        "added to each anhydro unit, increasing the resulting monomer mass:",
        body
    ))
    story.append(make_equation_box(
        "• Cellulose: (C6H10O5)n + n H2O → n C6H12O6 &nbsp;⇒&nbsp; F_cell = 180.16 / 162.14 = <b>1.1111 kg glucose / kg cellulose</b><br/>"
        "• Xylan: (C5H8O4)n + n H2O → n C5H10O5 &nbsp;⇒&nbsp; F_xyl = 150.13 / 132.12 = <b>1.1364 kg xylose / kg xylan</b><br/>"
        "• Mannan: (C6H10O5)n + n H2O → n C6H12O6 &nbsp;⇒&nbsp; F_man = 180.16 / 162.14 = <b>1.1111 kg mannose / kg mannan</b><br/>"
        "<br/>"
        "<b>m_sugar,j = m_retained,j · η_hydrolysis,j · F_j + m_measured,j</b>",
        "<b>η_hydrolysis,j:</b> conversion efficiency of retained polymer to fermentable monomer; "
        "<b>m_measured,j:</b> optional initial soluble monomer present in feedstock (default = 0 kg/day)."
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>C. Fermentation & Stoichiometric Carbon Dioxide:</b>", subsec_title))
    story.append(Paragraph(
        "Hexose and pentose fermentation proceed along the stoichiometric Gay-Lussac reaction path yielding 0.5114 g ethanol per g sugar:",
        body
    ))
    story.append(make_equation_box(
        "m_fermented,j = m_sugar,j · η_ferm,j &nbsp;(if organism fermentable)<br/>"
        "m_eth_crude = ∑ (m_fermented,j · 0.5114) [kg/day]<br/>"
        "m_eth_recovered = m_eth_crude · η_recovery &nbsp;&nbsp;|&nbsp;&nbsp; m_eth_lost = m_eth_crude · (1 - η_recovery)<br/>"
        "<br/>"
        "<b>m_CO2 = m_eth_crude · (44.01 / 46.07) = m_eth_crude · 0.9553 kg CO₂ / kg crude ethanol</b>",
        "<b>η_ferm,j:</b> organism efficiency for sugar <i>j</i> (e.g. S. cerevisiae fermenting glucose at 88%, xylose at 0%); "
        "<b>η_recovery:</b> distillation and dehydration recovery factor (default = 0.95)."
    ))

    story.append(PageBreak())

    # ================= SECTION 4 =================
    story.append(Paragraph("4. Derivation of the Complete Mass Balance", sec_title))
    story.append(Paragraph(
        "A rigorous biorefinery model must satisfy the First Law of Thermodynamics: mass in must identically equal mass out. "
        "In biochemical systems, the apparent paradox of <i>Total Sugar Mass > Hydrolyzed Polymer Mass</i> is resolved by "
        "accounting for the <b>chemically consumed hydrolysis water</b>.",
        body
    ))

    # Insert Mass Balance Diagram
    if os.path.exists("diagrams/mass_balance.png"):
        story.append(Image("diagrams/mass_balance.png", width=6.8*72, height=2.85*72))
        story.append(Paragraph("Figure 2: Control Volume Boundary Showing Exact Inflow and Outflow Streams.", caption))

    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>Step-by-Step Derivation of Mass Boundary:</b>", subsec_title))
    
    story.append(Paragraph("<b>1. Input Stream Formulation (IN):</b>", body))
    story.append(make_equation_box(
        "Total IN = m_dry + m_hyd_water + m_measured_sugars",
        "Where the stoichiometric water consumed during glycosidic bond cleavage is derived exactly as:<br/>"
        "<b>m_hyd_water = ∑ [m_sugar,j - m_measured,j] - ∑ (m_retained,j · η_hydrolysis,j)</b>"
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>2. Output Stream Formulation (OUT):</b>", body))
    story.append(make_equation_box(
        "Total OUT = m_residual_solids + m_dissolved + m_degraded + m_unfermented + m_eth_recovered + m_eth_lost + m_CO2 + m_unaccounted",
        "The individual outflow terms represent mutually exclusive physical destinations:<br/>"
        "• <b>m_residual_solids:</b> m_retained,lignin + m_retained,ash + m_retained,other + ∑ m_retained,carbs · (1 - η_hyd)<br/>"
        "• <b>m_dissolved:</b> ∑ m_dissolved,i (soluble pretreatment liquor solids)<br/>"
        "• <b>m_degraded:</b> thermal/acid degradation products (furfurals)<br/>"
        "• <b>m_unfermented:</b> ∑ m_sugar,j - ∑ m_fermented,j (residual unconverted sugars)<br/>"
        "• <b>m_eth_recovered:</b> purified product bioethanol<br/>"
        "• <b>m_eth_lost:</b> ethanol remaining in distillation bottoms or vent vapor<br/>"
        "• <b>m_CO2:</b> stoichiometric gas co-produced during catabolism<br/>"
        "• <b>m_unaccounted:</b> m_dry - ∑ m_retained - ∑ m_dissolved - m_degraded (shortfall if pretreatment fractions < 100%)"
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>3. Mathematical Closure Proof:</b>", body))
    story.append(make_equation_box(
        "Closure Error (%) = 100 · (Total OUT - Total IN) / Total IN &nbsp;&nbsp;≡&nbsp;&nbsp; 0.0000 %",
        "Substituting the hydration factor definition into the sugar production equation cancels the bound water term "
        "identically against the monomer outputs. Thus, organic dry matter and reaction water achieve mathematical closure."
    ))

    story.append(Spacer(1, 8))

    # ================= SECTION 5 =================
    story.append(Paragraph("5. Module 03: Energy Balance Derivations", sec_title))
    story.append(Paragraph(
        "Thermal and electrical utility demands are determined through equipment-level thermodynamic First-Law balances. "
        "Standard thermodynamic constants: Cp,water = 4.186 kJ/kg·K; Cp,dry_biomass = 1.500 kJ/kg·K; ΔHvap = 2.257 MJ/kg; ρ_ethanol = 0.789 kg/L.",
        body
    ))

    story.append(Paragraph("<b>A. Thermal Duty Derivations:</b>", subsec_title))
    story.append(make_equation_box(
        "1. Feed Dryer (D-101):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Water Evaporated: <b>m_evap = m_dry · [m0 / (1 - m0) - mt / (1 - mt)] [kg/day]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_dryer = [m_evap · Cp,w · (100 - Tin) + m_evap · ΔHvap + m_dry · Cp,b · (100 - Tin)] / η_dryer [MJ/day]</b><br/>"
        "<br/>"
        "2. Pretreatment Reactor (R-101):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Process Slurry Liquid: <b>m_slurry_liq = m_dry · LSR [kg/day]</b> &nbsp;(LSR = Liquid-to-Solid Ratio, default 8.0)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_pretreat = [(m_slurry_liq · Cp,w + m_dry · Cp,b) · (T_pre - Tin) + Q_loss] / η_heater [MJ/day]</b><br/>"
        "<br/>"
        "3. Distillation & Dehydration Columns (C-101):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Broth Volume: <b>V_broth = [(m_eth_recovered / ρ_eth) / (Broth_vol% / 100)] / 1000 [m³/day]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_distillation = (V_broth · q_spec,dist) / η_dist_heater [MJ/day]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_dehydration = V_ethanol_L · q_spec,dehyd [MJ/day]</b><br/>"
        "<br/>"
        "4. Heat Recovery Credit & Net Duty:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_recovered = (Q_pretreat + Q_distillation) · η_heat_rec [MJ/day]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Q_net = (Q_dryer + Q_pretreat + Q_dist + Q_dehyd + Q_ferm_cool) - Q_recovered [MJ/day]</b>",
        "Calculates thermal energy by equipment. The model accounts for sensible heating of solids and water, latent heat of "
        "vaporization, heat losses, equipment efficiencies, and cross-exchange heat integration."
    ))

    story.append(PageBreak())

    # ================= SECTION 6 =================
    story.append(Paragraph("5. Module 03 (Continued) & Modules 04–05 Formulations", sec_title))

    story.append(Paragraph("<b>B. Electrical Power Balances (Module 03):</b>", subsec_title))
    story.append(make_equation_box(
        "• Washing Pump: E_wash = (ρ_w · g · Head · V_wash / η_pump) / 3.6×10⁶ [kWh/day]<br/>"
        "• Biomass Mill: E_mill = (m_dry / 1000) · e_mill_spec [kWh/day]<br/>"
        "• Slurry Mixer: E_slurry = user-entered (default 8 kWh/day)<br/>"
        "• Filter Press: E_filter = [(m_dry + m_slurry_liq) / 1000] · e_filter_spec [kWh/day]<br/>"
        "• Fermenter Agitation: E_ferm = V_broth · e_ferm_spec [kWh/day]<br/>"
        "• Beer Centrifuge: E_centrifuge = V_broth · e_centrifuge_spec [kWh/day]<br/>"
        "• General Auxiliaries: E_aux = user-entered (default 10 kWh/day)<br/>"
        "<br/>"
        "<b>Total Daily Electrical Demand: E_total = ∑ E_i [kWh/day]</b>",
        "Aggregates hydraulic pumping power, mechanical comminution, slurry handling, and separation loads."
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>C. Zero-Waste Allocation & Circularity Indices (Module 04):</b>", subsec_title))
    story.append(make_equation_box(
        "• Solid Recovery Ratio (%): <b>100 · (m_solids,rec / m_solids,total)</b><br/>"
        "• Water Recycle Index (%): <b>100 · (m_water,recycled / m_wastewater)</b><br/>"
        "• Carbon Dioxide Utilization (%): <b>100 · (m_CO2,utilized / m_CO2,generated)</b>",
        "Residues (lignin, ash, unhydrolyzed organics) are routed to soil biochar, combustion for energy, or soil compost. "
        "Wastewater is split between internal recycling, on-site biological treatment, and discharge."
    ))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>D. Techno-Economic Analysis Equations (Module 05):</b>", subsec_title))
    story.append(make_equation_box(
        "1. Capital Recovery Factor (CRF) & Capital Charge:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>CRF = [r · (1 + r)ⁿ] / [(1 + r)ⁿ - 1] &nbsp;⇒&nbsp; Annual Capital Charge = CAPEX · CRF [EGP/year]</b><br/>"
        "<br/>"
        "2. Operating Expenses (OPEX):<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Gross OPEX = ∑ (Annual Quantities · Unit Tariffs) + Fixed OPEX (labor, maintenance, transport)<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;<b>Net OPEX = max(0, Gross OPEX - Energy_Recovery_Credit) [EGP/year]</b><br/>"
        "<br/>"
        "3. Break-Even Selling Prices & Simple Payback:<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Operating Break-Even Price: <b>P_be,op = (Net OPEX - Byproduct Revenue) / Annual Ethanol Volume [EGP/L]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Full Break-Even Price: <b>P_be,cap = (Net OPEX + Capital Charge - Byproduct Revenue) / Annual Ethanol Volume [EGP/L]</b><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;Simple Payback Period: <b>Payback = CAPEX / Operating Profit [years]</b> (valid for Operating Profit > 0)",
        "<b>r:</b> annual discount rate (%); <b>n:</b> plant operating lifetime (years). Incorporates time value of money, "
        "energy recovery credits from residue combustion, and byproduct revenues (biochar, CO₂)."
    ))

    story.append(Spacer(1, 8))

    # ================= SECTION 7 =================
    story.append(Paragraph("6. Engineering Summary & Staff Guidance Notes", sec_title))
    
    eng_notes = [
        ["Domain", "Engineering Reality in Water Hyacinth", "Model Safeguards Implemented"],
        ["Extreme Moisture", "Water hyacinth is 90-93% water; raw drying is thermally prohibitive.", "Warns the user when energy intensity exceeds 30 kWh/L."],
        ["Xylose Utilization", "Wild S. cerevisiae strains cannot ferment xylose.", "Organism profile dropdown toggles pentose fermentation on/off."],
        ["CO₂ Accounting", "Fermentation generates stoichiometric CO₂.", "Tied directly to Gay-Lussac reaction stoichiometry (0.955 kg/kg)."],
        ["Separation", "Broth ethanol concentration is low (~5 vol%).", "Broth volume drives distillation steam duty accurately."],
        ["Economics", "Economic feasibility hinges on feedstock collection costs.", "Enforces zero-default economics; warns on missing pricing."]
    ]
    t_eng = Table(eng_notes, colWidths=[80, 190, 234])
    t_eng.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f5e9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('LEADING', (0,0), (-1,-1), 9.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e0e0e0")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_eng)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Document Verification:</b> Certified consistent with HYACINTH-X codebase Release 2.1.", caption))

    doc.build(story, canvasmaker=ElegantNumberedCanvas)
    print(f"Publication-quality PDF created successfully at: {os.path.abspath(filename)}")


if __name__ == "__main__":
    out_name = sys.argv[1] if len(sys.argv) > 1 else "HYACINTH_X_Technical_Formulations_Handbook.pdf"
    build_handbook(out_name)
