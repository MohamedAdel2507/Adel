# 🌿 HYACINTH-X

Integrated second-generation bioethanol biorefinery simulator (water hyacinth, *Eichhornia crassipes*).
Five calculation modules are chained through a central Data Manager and exposed in one Streamlit app.

```
USER INPUT → M01 Feedstock → M02 Process yield → M03 Energy & utilities → M04 Zero-waste → M05 TEA → results & reports
```

## Quick start
```bash
pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests -v      # automated tests
```

## Structure
```
app.py                      Streamlit UI (no calculations)
modules/                    module_01 … module_05 (calculation logic ported from legacy/)
core/                       configuration, data_manager, validation, process_controller
reports/report_generator.py PDF, Excel, JSON
legacy/                     the five original source files, untouched
tests/                      unit, integration, scientific and report tests (+ UI stub smoke test)
docs/INTEGRATION_NOTES.md   module audit, mappings, known model issues
```

## Inputs
Required: wet feed (kg/day), moisture (% wet basis), composition (illustrative defaults shown), operating days/year, scenario, organism profile.
Optional: economic prices and costs (none are assumed), plus every supported parameter in **Manual / Advanced** mode.

## Automatic vs Manual
Automatic uses documented defaults (all listed in the *Assumptions & Checks* tab with their origin). Manual exposes Module 02/03/04 parameters and integration assumptions, validated before running.

## Deploy on Streamlit Community Cloud
1. Push this folder to your GitHub repository (branch `main`).
2. Go to https://share.streamlit.io → **Create app** → select the repository, branch `main`, main file `app.py`.
3. Deploy. No secrets are required.

## Scientific scope and limits
Screening-level; default parameters are illustrative legacy values. No ethanol purity/separation model, no ROI/NPV, no water quality or LCA. See `docs/INTEGRATION_NOTES.md`.
