"""Unit tests for HYACINTH-X Interactive Mass & Material Balance Engine."""
import unittest
import subprocess
import re
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.configuration import default_inputs
from core.process_controller import run_simulation
from core.material_balance import (
    compute_all_streams,
    compute_equipment_material_balance,
    compute_plant_material_balance,
    generate_sankey_data,
)
from core.plant_3d import build_threejs_html, EQUIPMENT_METADATA


class TestMaterialBalance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dm = run_simulation(default_inputs())
        cls.streams = compute_all_streams(cls.dm)

    def test_streams_generated(self):
        self.assertGreaterEqual(len(self.streams), 20)
        for sid in ["S-01", "S-02", "S-03", "S-04", "S-05", "S-06", "S-07", "S-08", "S-09", "S-10", "S-12", "S-14"]:
            self.assertIn(sid, self.streams)
            strm = self.streams[sid]
            self.assertGreater(strm.mass_flow_kg_h, 0.0)
            self.assertGreater(strm.mass_flow_kg_day, 0.0)
            self.assertTrue(len(strm.components) > 0)

    def test_all_10_units_mass_balance_closure(self):
        units = list(EQUIPMENT_METADATA.keys())
        self.assertEqual(len(units), 10)
        for u in units:
            b = compute_equipment_material_balance(u, self.dm)
            self.assertGreater(b.total_in_kg_h, 0.0, f"{u} total in must be > 0")
            self.assertGreater(b.total_out_kg_h, 0.0, f"{u} total out must be > 0")
            self.assertAlmostEqual(b.closure_pct, 100.0, delta=0.5, msg=f"{u} mass balance closure failed: {b.closure_pct}%")

    def test_overall_plant_boundary_closure(self):
        pb = compute_plant_material_balance(self.dm)
        self.assertGreater(pb["total_mass_in_kg_day"], 0.0)
        self.assertGreater(pb["total_mass_out_kg_day"], 0.0)
        self.assertAlmostEqual(pb["closure_pct"], 100.0, delta=0.5)
        self.assertAlmostEqual(pb["closure_error_pct"], 0.0, delta=0.5)
        self.assertGreater(pb["product_ethanol_kg_day"], 0.0)
        self.assertGreater(pb["wastewater_total_kg_day"], 0.0)

    def test_sankey_network(self):
        sankey = generate_sankey_data(self.dm)
        self.assertGreater(len(sankey["nodes"]), 10)
        self.assertGreater(len(sankey["sources"]), 10)
        self.assertEqual(len(sankey["sources"]), len(sankey["targets"]))
        self.assertEqual(len(sankey["sources"]), len(sankey["values"]))
        for v in sankey["values"]:
            self.assertGreater(v, 0.0)

    def test_build_threejs_html_js_syntax(self):
        html = build_threejs_html("R-101", "full_plant", True, "S-05", self.dm)
        m = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
        self.assertTrue(len(m) > 0)
        js_code = m[-1]
        tmp_js = os.path.join(os.path.dirname(__file__), "tmp_syntax_test.js")
        with open(tmp_js, "w", encoding="utf-8") as f:
            f.write(js_code)
        try:
            res = subprocess.run(["node", "-c", tmp_js], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, f"Three.js syntax error: {res.stderr}")
        finally:
            if os.path.exists(tmp_js):
                os.remove(tmp_js)


if __name__ == "__main__":
    unittest.main()
