"""Smoke test of app.py logic with a *stub* streamlit (NOT the real Streamlit).

It verifies that app.py runs end to end (setup -> run -> dashboard -> reports) without Python errors,
using widget default values. It cannot verify real rendering, layout or browser behaviour.
Run:  python tests/ui_smoke_stub.py [--manual]
"""
import contextlib
import runpy
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
MANUAL = "--manual" in sys.argv
CALLS = {"metric": 0, "download": 0, "df": 0, "error": [], "chart": 0}


class Ctx(contextlib.AbstractContextManager):
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def update(self, **k): pass
    def __getattr__(self, name): return getattr(st, name)
    def metric(self, *a, **k): CALLS["metric"] += 1
    def number_input(self, label, **k): return k.get("value", 0)
    def slider(self, label, *a, **k): return k.get("value", a[2] if len(a) > 2 else 0)
    def checkbox(self, label, value=False, **k): return value
    def download_button(self, *a, **k): CALLS["download"] += 1


class State(dict):
    __getattr__ = dict.get
    def __setattr__(self, k, v): self[k] = v


st = types.ModuleType("streamlit")
st.session_state = State()
for n in ("title", "caption", "write", "markdown", "info", "warning", "success", "subheader", "graphviz_chart", "set_page_config", "spinner_noop"):
    setattr(st, n, lambda *a, **k: None)
st.error = lambda m, *a, **k: CALLS["error"].append(m)
st.bar_chart = lambda *a, **k: CALLS.__setitem__("chart", CALLS["chart"] + 1)
st.dataframe = lambda *a, **k: CALLS.__setitem__("df", CALLS["df"] + 1)
st.tabs = lambda labels: [Ctx() for _ in labels]
st.columns = lambda spec, **k: [Ctx() for _ in range(spec if isinstance(spec, int) else len(spec))]
st.expander = lambda *a, **k: Ctx()
st.spinner = lambda *a, **k: Ctx()
st.status = lambda *a, **k: Ctx()
st.radio = lambda label, options, **k: options[1 if MANUAL else 0]
st.selectbox = lambda label, options, **k: list(options)[0]
st.number_input = lambda label, **k: k.get("value", 0)
st.slider = lambda label, *a, **k: k.get("value", a[2] if len(a) > 2 else 0)
st.checkbox = lambda label, value=False, **k: value
st.button = lambda label, **k: not k.get("disabled", False)   # "press" Run
st.download_button = lambda *a, **k: CALLS.__setitem__("download", CALLS["download"] + 1)
sys.modules["streamlit"] = st

# economic test fixture values injected through number_input labels (TEST ONLY, not defaults)
_orig = st.number_input
FIX = {"Bioethanol selling price (EGP/L)": 30.0, "CAPEX (EGP)": 1e6, "Feedstock price (EGP/kg wet)": 0.5,
       "Labor (EGP/year)": 50000.0, "Maintenance (EGP/year)": 20000.0}
st.number_input = lambda label, **k: FIX.get(label, _orig(label, **k))
Ctx.number_input = lambda self, label, **k: FIX.get(label, k.get("value", 0))

runpy.run_path(str(ROOT / "app.py"), run_name="__main__")
dm = st.session_state.get("dm")
assert dm is not None and dm.completed, f"simulation did not complete: {dm and dm.status}"
assert "reports" in st.session_state and len(st.session_state["reports"]["pdf"]) > 1000
assert not CALLS["error"], CALLS["error"]
print("UI STUB SMOKE OK", "mode=manual" if MANUAL else "mode=automatic", CALLS)
