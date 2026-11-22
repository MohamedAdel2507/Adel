# HYACINTH-X integration notes (audit of the five source modules)

## What each module actually does (from the source code)
| Module | Legacy file | Real capability |
|---|---|---|
| 01 | `legacy/hyacinth_x_module_01.py` | Wet/dry/water mass and component flows from wet feed, moisture (wet basis) and 5-pool composition. Local JSON profile save/load. |
| 02 | `legacy/hyacinth_x_module_02.py` | Screening chain: pretreatment split → enzymatic hydrolysis → fermentation → ethanol recovery. 6-pool composition (cellulose, xylan, mannan, lignin, ash, other). |
| 03 | `legacy/hyacinth_x_module_03.py` | **Energy & utilities only** (washing pump, dryer, milling, slurry mixing, pretreatment heating, filter press, fermenter, centrifuge, distillation, dehydration, heat recovery, utility cost). No ethanol purity / separation-efficiency model. |
| 04 | `legacy/hyacinth_x_module_04.py` | Allocation accounting of residues, wastewater and CO2 (percent splits). No water-quality or LCA model. |
| 05 | `legacy/hyacinth_x_module_05.py` | OPEX, revenue, annualized CAPEX, break-even, simple payback, price sensitivity. No ROI/NPV/IRR. All prices default to 0. |

## Dependency graph (acyclic)
M01→M02, M01→M03, M02→M03, M02→M04, M03→M04, M01/M02/M03/M04→M05. Every hand-off is logged in the Data Manager (`Assumptions & Checks` tab).

## Interface mismatches resolved (and how)
1. **Hemicellulose pool (M01) vs xylan + mannan (M02).** Split with the legacy M02 default ratio 18:3 (mannan share 3/21). Adjustable in Manual mode; logged as an assumption.
2. **Composition tolerance.** M01 allows ±0.5 points, M02 requires ±0.15. Uncharacterized dry matter goes to "Other / extractives"; totals outside ±0.15 are normalized with a warning.
3. **CO2.** No upstream module computes it; M04 needs it. Derived from fermentation stoichiometry (44.01/46.07 kg CO2 per kg ethanol), labelled as an integration-layer calculation; excludes CO2 from cell growth.
4. **Residue streams (M04 inputs).** Taken from M02: retained lignin, retained ash, other retained solids + unhydrolyzed carbohydrate. Dissolved + degraded + unfermented sugar + ethanol loss go to "other discard".
5. **Wastewater (M04 input).** = washing water + pretreatment liquid (L/S × dry mass) from M03. Dryer vapour is excluded. Documented as an estimate; user can change the underlying parameters in Manual mode.
6. **TEA quantities (M05).** Ethanol L/yr, electricity, net thermal energy from M03 × operating days; wet feedstock kg/yr from M01; freshwater = (wastewater − recycled water)/1000 × days from M04.
7. **Utility prices** exist in both M03 and M05: now one shared input.
8. **Biochar and energy credit.** No module provides a biochar yield or a residue heating value. Both default to 0 and the results are marked *not calculated* rather than invented.

## Model issues found (documented, not silently fixed)
- M02 allows retained + solubilized + degraded < 100%, silently losing mass. The integration shows the shortfall as an "unaccounted" line and warns.
- M03 broth volume (ethanol vol%) and M03 pretreatment liquid (L/S ratio) are independent and inconsistent (e.g. 8 m³ vs ~0.3 m³ per day at default settings). Flagged in the app.
- M03 defaults dry an 85%-moisture feed to 10%: ~98 kWh per litre of ethanol, far above the ethanol's energy content. Flagged in the app.
- M05 `capital_in_break_even` checkbox was never used; not carried over.
- M04 `tracked_recovery` and `entered_streams` were computed but never displayed; not carried over.

## Removed legacy behaviour (justification)
Local JSON profile files and the JSON-import/alias search: replaced by direct typed data transfer; local files are not persistent on Streamlit Community Cloud. Hourly basis in M04: the platform uses a single daily basis.
