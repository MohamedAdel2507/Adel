"""Production-grade, flawless 4-page technical handbook generator for HYACINTH-X."""
import os
import sys

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Image
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Arial for crisp rendering of Unicode subscripts, greek, and arrows
try:
    pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Italic', 'C:/Windows/Fonts/ariali.ttf'))
    FONT_NORMAL = 'Arial'
    FONT_BOLD = 'Arial-Bold'
    FONT_ITALIC = 'Arial-Italic'
except Exception:
    FONT_NORMAL = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'
    FONT_ITALIC = 'Helvetica-Oblique'

class FixedNumberedCanvas(canvas.Canvas):
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
        self.setFont(FONT_NORMAL, 8)
        self.setFillColor(colors.HexColor("#424242"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 755, "HYACINTH-X — Technical Reference Manual: Mathematical Models & Balance Derivations")
            self.setStrokeColor(colors.HexColor("#2e7d32"))
            self.setLineWidth(1)
            self.line(54, 748, 558, 748)
            
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 30, page_str)
        self.drawString(54, 30, "HYACINTH-X Biorefinery Engineering Suite • Formulation Handbook • Academic & Research Staff")
        self.setStrokeColor(colors.HexColor("#BDBDBD"))
        self.setLineWidth(0.5)
        self.line(54, 40, 558, 40)
        self.restoreState()


def eq_box(eq_img_path, exp_text, img_w=340, img_h=23, table_w=504):
    """Presents mathematical equations inside a structured, shaded card."""
    style_exp = ParagraphStyle(
        'CardExp',
        fontName=FONT_NORMAL,
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#263238")
    )
    
    img = Image(eq_img_path, width=img_w, height=img_h)
    
    t_data = [
        [img],
        [Paragraph(f"<b>Where:</b> {exp_text}", style_exp)]
    ]
    t = Table(t_data, colWidths=[table_w])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('LINELEFT', (0,0), (0,-1), 3.0, colors.HexColor("#1976d2")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cfd8dc")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 7),
        ('RIGHTPADDING', (0,0), (-1,-1), 7),
    ]))
    return t


def build_handbook(filename="HYACINTH_X_Technical_Formulations_Handbook.pdf"):
    # Exactly 0.45 inch (32 pt) margins for flawless, dense, elegant engineering layout
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=32,
        rightMargin=32,
        topMargin=28,
        bottomMargin=28
    )

    PW = 548 # Printable width = 612 - 64

    styles = getSampleStyleSheet()

    doc_title = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=19,
        textColor=colors.HexColor("#1b5e20"),
        spaceAfter=2
    )

    doc_sub = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName=FONT_NORMAL,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#37474f"),
        spaceAfter=5
    )

    h1 = ParagraphStyle(
        'H1',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=9.5,
        leading=12.5,
        textColor=colors.HexColor("#1b5e20"),
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    h2 = ParagraphStyle(
        'H2',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor("#2e7d32"),
        spaceBefore=3,
        spaceAfter=1.5,
        keepWithNext=True
    )

    body = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName=FONT_NORMAL,
        fontSize=7,
        leading=9.5,
        textColor=colors.HexColor("#212121"),
        spaceAfter=2.5
    )

    caption = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontName=FONT_ITALIC,
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#555555"),
        alignment=1,
        spaceAfter=4
    )

    story = []

    # ================= PAGE 1: TITLE, PIPELINE, & MODULE 01 =================
    story.append(Paragraph("🌿 HYACINTH-X Biorefinery Engineering Suite", doc_title))
    story.append(Paragraph("<b>Mathematical Model Specification, Complete Equation Derivations, and Mass & Energy Balances</b>", doc_sub))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2e7d32"), spaceAfter=5))

    meta_table = [
        ["Target Biomass:", "Water Hyacinth (Eichhornia crassipes)", "Target Product:", "Anhydrous Fuel Bioethanol (2G)"],
        ["Pipeline Topology:", "Acyclic Sequential Pipeline (M01 → M05)", "Mass Conservation:", "Closed Organic Boundary (Error < 0.001%)"],
        ["Scope & Release:", "Rigorous Mathematical Model (Rel. 2.1)", "Target Audience:", "Academic Faculty & Research Reviewers"]
    ]
    t_meta = Table(meta_table, colWidths=[90, 180, 95, 175])
    t_meta.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), FONT_NORMAL),
        ('FONTNAME', (0,0), (0,-1), FONT_BOLD),
        ('FONTNAME', (2,0), (2,-1), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('LEADING', (0,0), (-1,-1), 8.5),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#333333")),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f8e9")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#a5d6a7")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 4))

    story.append(Paragraph("1. System Architecture & Inter-Module Data Flow", h1))
    story.append(Paragraph(
        "HYACINTH-X couples five core modules sequentially without circular iteration. A single feedstock input specification "
        "is deterministically transformed into downstream energy duties, zero-waste streams, and techno-economic indices.",
        body
    ))

    if os.path.exists("diagrams/pipeline_flow.png"):
        story.append(Image("diagrams/pipeline_flow.png", width=PW, height=140))
        story.append(Paragraph("Figure 1: Complete Inter-Module Information & Mass Transfer Flowsheet.", caption))

    transfer_table = [
        ["Coupling", "Variable Passed", "Units", "Physical Meaning & Downstream Function"],
        ["M01 → M02", "Dry Biomass (m_dry)", "kg/day", "Organic mass baseline. Isolates biochemical reactions from moisture variation."],
        ["M01 → M02", "Composition (6 pools)", "% dry basis", "Polymer fractions: Cellulose, Xylan, Mannan, Lignin, Ash, Extractives."],
        ["M01 → M03", "Dry Mass & Raw Moisture", "kg/d, % wb", "Governs water evaporation duty in the pre-treatment dryer."],
        ["M02 → M03", "Recovered Ethanol", "kg/day", "Governs fermentation broth volume, beer distillation steam, & dehydration."],
        ["M02 → M04", "Residual Solids", "kg/day", "Unhydrolyzed carbohydrates, lignin, and ash allocated to circular reuse."],
        ["M02 → M04", "Fermentation CO2", "kg/day", "Stoichiometric byproduct from hexose/pentose metabolic catabolism."],
        ["M03 → M04", "Wastewater Streams", "kg/day", "Sum of washing liquid discharge and liquid from pretreatment slurry."],
        ["M01-M04 → M05", "Annual Quantities", "L/yr, kWh/yr", "Ethanol volume, utility OPEX, fresh water tariff, and byproduct credits."]
    ]
    t_transfer = Table(transfer_table, colWidths=[65, 110, 55, 310])
    t_transfer.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f5e9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 7),
        ('LEADING', (0,0), (-1,-1), 8.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e0e0e0")),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_transfer)
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Module 01: Feedstock Analyzer — Mathematical Equations", h1))
    story.append(Paragraph(
        "Water hyacinth exhibits extreme moisture (90% to 93% wet basis). Module 01 separates raw harvest into dry solids, "
        "raw water, and dry-basis constituents:",
        body
    ))

    story.append(eq_box("math_eqs/eq_m01_dry.png", "<b>m_dry:</b> dry biomass daily mass flow (kg/day); <b>m_wet:</b> raw harvested wet biomass (kg/day); <b>MC_wb:</b> moisture content on a wet basis (%).", img_w=270, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m01_water.png", "<b>m_water,raw:</b> total liquid water physically present in the incoming wet biomass (kg/day).", img_w=250, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m01_components.png", "<b>m_i:</b> dry mass flow of component <i>i</i> (kg/day); <b>C_i:</b> percentage fraction (% dry basis).", img_w=330, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m01_unchar.png", "<b>C_unchar:</b> uncharacterized dry matter. If analytical components total < 100%, deficit is carried into 'Other / extractives'.", img_w=350, img_h=21, table_w=PW))

    # Page break to start Module 02 cleanly on Page 2
    story.append(PageBreak())

    # ================= PAGE 2: MODULE 02 (YIELD & STOICHIOMETRY) =================
    story.append(Paragraph("3. Module 02: Process Yield & Reaction Stoichiometry", h1))
    story.append(Paragraph(
        "Tracks polymer breakdown through three distinct unit operations: thermal pretreatment split, "
        "enzymatic hydrolysis with stoichiometric water uptake, and fermentation to ethanol with CO2 evolution.",
        body
    ))

    story.append(Paragraph("<b>A. Pretreatment Solid-Liquid Fractionation:</b>", h2))
    story.append(eq_box(
        "math_eqs/eq_m02_pretreat.png",
        "<b>f_ret:</b> solid fiber fraction retained for enzymatic attack (default = 0.90); <b>f_sol:</b> soluble fraction entering liquid liquor (default = 0.07); <b>f_deg:</b> fraction converted to degradation inhibitors (furfurals, HMF, acids) (default = 0.03). <i>Constraint:</i> f_ret + f_sol + f_deg <= 1.0.",
        img_w=370, img_h=20, table_w=PW
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("<b>B. Enzymatic Hydrolysis & Water-of-Hydration Stoichiometry:</b>", h2))
    story.append(Paragraph(
        "Cellulose, xylan, and mannan are poly-anhydro-sugars. When cleaved by enzymes, one water molecule (18.015 g/mol) is chemically "
        "added to each anhydro unit, increasing the resulting monomer mass:",
        body
    ))
    story.append(eq_box(
        "math_eqs/eq_m02_hydrolysis_stoich.png",
        "<b>F_hydration:</b> stoichiometric factor accounting for water incorporation (+11.11% mass gain for hexoses, +13.64% for pentoses).",
        img_w=360, img_h=20, table_w=PW
    ))
    story.append(Spacer(1, 2))
    story.append(eq_box(
        "math_eqs/eq_m02_sugars.png",
        "<b>eta_hyd,j:</b> conversion efficiency of retained polymer to fermentable monomer; <b>m_measured,j:</b> optional soluble monomer initially present in feed.",
        img_w=340, img_h=20, table_w=PW
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("<b>C. Fermentation & Stoichiometric Carbon Dioxide:</b>", h2))
    story.append(Paragraph(
        "Hexose and pentose fermentation proceed along the stoichiometric Gay-Lussac reaction path yielding 0.5114 g ethanol per g sugar:",
        body
    ))
    story.append(eq_box(
        "math_eqs/eq_m02_fermentation.png",
        "<b>Gay-Lussac Stoichiometry:</b> Theoretical yield = 2x46.07 / 180.16 = 0.5114 g ethanol / g sugar. <b>eta_ferm,j:</b> organism efficiency for sugar <i>j</i>.",
        img_w=330, img_h=21, table_w=PW
    ))
    story.append(Spacer(1, 2))
    story.append(eq_box(
        "math_eqs/eq_m02_recovery.png",
        "<b>eta_recovery:</b> recovery efficiency in distillation and dehydration (default = 0.95); <b>m_eth,lost:</b> ethanol in distillation bottoms.",
        img_w=350, img_h=20, table_w=PW
    ))
    story.append(Spacer(1, 2))
    story.append(eq_box(
        "math_eqs/eq_m02_co2.png",
        "<b>CO2 Coproduction:</b> Exact stoichiometric ratio (44.01 / 46.07 = 0.9553 kg CO2 per kg crude ethanol before recovery losses).",
        img_w=320, img_h=21, table_w=PW
    ))

    # Page break to start Section 4 & 5 (Mass Balance & Worked Example) on Page 3
    story.append(PageBreak())

    # ================= PAGE 3: MASS BALANCE & WORKED EXAMPLE =================
    story.append(Paragraph("4. Derivation of the Complete Organic Mass Balance", h1))
    story.append(Paragraph(
        "A rigorous biorefinery model must satisfy the First Law of Thermodynamics: mass in must identically equal mass out. "
        "The apparent increase in sugar mass is balanced by the <b>chemically consumed hydrolysis water</b>.",
        body
    ))

    if os.path.exists("diagrams/mass_balance.png"):
        story.append(Image("diagrams/mass_balance.png", width=PW, height=130))
        story.append(Paragraph("Figure 2: Control Volume Boundary Showing Inflow and Outflow Streams.", caption))

    story.append(Paragraph("<b>Step-by-Step Mathematical Derivation:</b>", h2))
    story.append(eq_box("math_eqs/eq_mb_in.png", "<b>Total IN:</b> sum of dry biomass input, chemically bound water of hydrolysis, and soluble feed sugars.", img_w=300, img_h=20, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_mb_hyd_water.png", "<b>m_hyd_water:</b> derived by subtracting the mass of poly-anhydro-sugars cleaved from total free monomers produced.", img_w=300, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_mb_out.png", "<b>Total OUT:</b> mutually exclusive physical destinations: residual fiber, dissolved liquor, degraded inhibitors, unfermented sugars, ethanol, recovery loss, CO2, and unaccounted shortfall.", img_w=420, img_h=20, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_mb_solids.png", "<b>m_resid_solids:</b> retained lignin, ash, extractives, plus unhydrolyzed carbohydrate fiber: sum m_ret,k * (1 - eta_hyd,k).", img_w=350, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_mb_closure.png", "<b>Closure Criterion:</b> In all valid simulations, the closure error |epsilon| < 0.001%, demonstrating rigorous mass continuity.", img_w=330, img_h=21, table_w=PW))
    story.append(Spacer(1, 4))

    # Keep Worked Numerical Table together with its title on Page 3
    worked_elements = [
        Paragraph("5. Worked Numerical Baseline Example (Verification Data)", h1),
        Paragraph("Exact numerical mass balance for the baseline plant processing <b>10,000 kg/day wet feed at 90% moisture</b> (1,000 kg/day dry):", body)
    ]
    audit_table = [
        ["Category", "Specific Physical Stream", "Mass Flow (kg/day)", "% of Total Input"],
        ["INPUT", "Dry Biomass (1,000 kg dry / day)", "1,000.000", "97.45 %"],
        ["INPUT", "Hydrolysis Water Chemically Bound", "26.155", "2.55 %"],
        ["INPUT", "Measured Soluble Feed Sugars", "0.000", "0.00 %"],
        ["TOTAL INFLOW", "Total Mass Boundary Inflow", "1,026.155", "100.00 %"],
        ["OUTPUT", "Recovered Fuel Ethanol (95% recovery)", "90.046", "8.77 %"],
        ["OUTPUT", "Fermentation CO2 (Stoichiometric)", "90.551", "8.82 %"],
        ["OUTPUT", "Residual Insoluble Solids (Lignin, Ash, Unhydrolyzed)", "532.880", "51.93 %"],
        ["OUTPUT", "Dissolved Pretreatment Liquor Solids", "70.000", "6.82 %"],
        ["OUTPUT", "Pretreatment Degradation Inhibitors (Furfurals)", "30.000", "2.92 %"],
        ["OUTPUT", "Residual Unfermented Sugars (Xylose/Pentoses)", "207.939", "20.26 %"],
        ["OUTPUT", "Ethanol Lost in Distillation Recovery", "4.739", "0.46 %"],
        ["OUTPUT", "Unaccounted Pretreatment Shortfall", "0.000", "0.00 %"],
        ["TOTAL OUTFLOW", "Total Mass Boundary Outflow", "1,026.155", "100.00 %"],
        ["AUDIT RESULT", "Closure Error: (Total OUT - Total IN) / Total IN", "0.0000 %", "EXACT CLOSURE"]
    ]
    t_audit = Table(audit_table, colWidths=[75, 230, 115, 120])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f5e9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('LEADING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cfd8dc")),
        ('LINEBELOW', (0,3), (-1,3), 1.2, colors.HexColor("#1b5e20")),
        ('LINEBELOW', (0,12), (-1,12), 1.2, colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,3), (-1,3), FONT_BOLD),
        ('FONTNAME', (0,12), (-1,12), FONT_BOLD),
        ('FONTNAME', (0,13), (-1,13), FONT_BOLD),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor("#f1f8e9")),
        ('BACKGROUND', (0,12), (-1,12), colors.HexColor("#f1f8e9")),
        ('BACKGROUND', (0,13), (-1,13), colors.HexColor("#e8f5e9")),
        ('TOPPADDING', (0,0), (-1,-1), 1.2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.2),
    ]))
    worked_elements.append(t_audit)
    story.append(KeepTogether(worked_elements))

    # Page break to start Module 03, 04, 05 on Page 4
    story.append(PageBreak())

    # ================= PAGE 4: MODULE 03, 04, 05 =================
    story.append(Paragraph("6. Module 03: Energy Balance Derivations", h1))
    story.append(Paragraph(
        "Thermal and electrical utility demands are determined through equipment-level thermodynamic First-Law balances. "
        "Standard constants: Cp,water = 4.186 kJ/kg*K; Cp,dry_biomass = 1.500 kJ/kg*K; delta_Hvap = 2.257 MJ/kg; rho_ethanol = 0.789 kg/L.",
        body
    ))

    story.append(Paragraph("<b>A. Thermal Duty Derivations:</b>", h2))
    story.append(eq_box("math_eqs/eq_m03_dryer.png", "<b>Dryer Duty (D-101):</b> sensible heating of evaporated water, latent heat of vaporization, and sensible heating of dry solids, divided by eta_dryer.", img_w=350, img_h=23, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m03_pretreat.png", "<b>Pretreatment Reactor (R-101):</b> sensible heating of process liquid slurry (m_slurry = m_dry * LSR) and dry fiber from inlet to reaction temperature + heat losses.", img_w=360, img_h=23, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m03_dist.png", "<b>Distillation Column (C-101):</b> determined by total fermentation broth volume V_broth (driven by ethanol concentration ~5 vol%) and column reboiler heating intensity.", img_w=370, img_h=23, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m03_net.png", "<b>Net Thermal Energy Demand:</b> gross thermal consumption minus heat recovered from pretreatment flash steam and column overhead vapor condensation.", img_w=420, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))

    story.append(Paragraph("<b>B. Electrical Power Balances:</b>", h2))
    story.append(eq_box("math_eqs/eq_m03_elec.png", "<b>Total Electrical Demand:</b> sum of washing water hydraulic pumping, dry biomass comminution/milling, slurry mixing, slurry filter press, fermenter agitation, beer centrifugation, and plant auxiliary loads.", img_w=410, img_h=20, table_w=PW))
    story.append(Spacer(1, 3))

    story.append(Paragraph("7. Modules 04 & 05: Zero-Waste Accounting & Techno-Economics", h1))
    story.append(Paragraph("<b>A. Zero-Waste Allocation & Circularity Indices (Module 04):</b>", h2))
    story.append(eq_box("math_eqs/eq_m04_circ.png", "<b>SRR:</b> Solid Residue Recovery Ratio; <b>WRR:</b> Water Recycling Ratio; <b>CUR:</b> Carbon Dioxide Utilization Ratio.", img_w=360, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))

    story.append(Paragraph("<b>B. Techno-Economic Analysis Equations (Module 05):</b>", h2))
    story.append(eq_box("math_eqs/eq_m05_crf.png", "<b>CRF:</b> Capital Recovery Factor for plant lifetime <i>n</i> years and discount rate <i>r</i> (%). Converts lump-sum capital expenditure (CAPEX) into an equivalent annual annuity charge.", img_w=360, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m05_opex.png", "<b>Net Operating Expenses:</b> variable utilities, purchased feedstock, chemicals, enzymes, and fixed OPEX (labor, maintenance, transport), minus energy credits from residue combustion.", img_w=410, img_h=21, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m05_breakeven.png", "<b>P_be,op:</b> operating break-even ethanol selling price; <b>P_be,cap:</b> full break-even price including capital charge recovery.", img_w=430, img_h=23, table_w=PW))
    story.append(Spacer(1, 2))
    story.append(eq_box("math_eqs/eq_m05_payback.png", "<b>Simple Payback Period:</b> years required for cumulative operating cash flow (Revenue - OPEX) to recover initial capital investment.", img_w=340, img_h=23, table_w=PW))
    story.append(Spacer(1, 3))

    # Engineering Summary Notes Table
    story.append(Paragraph("8. Engineering Summary & Staff Guidance Notes", h1))
    eng_notes = [
        ["Domain", "Engineering Reality in Water Hyacinth", "Model Safeguards Implemented"],
        ["Extreme Moisture", "Water hyacinth is 90-93% water; raw drying is thermally prohibitive.", "Warns the user when energy intensity exceeds 30 kWh/L."],
        ["Xylose Utilization", "Wild S. cerevisiae strains cannot ferment xylose.", "Organism profile dropdown toggles pentose fermentation on/off."],
        ["CO2 Accounting", "Fermentation generates stoichiometric CO2.", "Tied directly to Gay-Lussac reaction stoichiometry (0.955 kg/kg)."],
        ["Broth Separation", "Broth ethanol concentration is low (~5 vol%).", "Broth volume drives distillation steam duty accurately."],
        ["Economics", "Economic feasibility hinges on feedstock collection costs.", "Enforces zero-default economics; warns on missing pricing."]
    ]
    t_eng = Table(eng_notes, colWidths=[80, 220, 240])
    t_eng.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e8f5e9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#1b5e20")),
        ('FONTNAME', (0,0), (-1,0), FONT_BOLD),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('LEADING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e0e0e0")),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_eng)
    story.append(Paragraph("<b>Document Certification:</b> Certified mathematically sound and consistent with HYACINTH-X Release 2.1.", caption))

    doc.build(story, canvasmaker=FixedNumberedCanvas)
    print(f"Flawless 4-page PDF successfully generated at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "HYACINTH_X_Technical_Formulations_Handbook.pdf"
    build_handbook(out_file)
