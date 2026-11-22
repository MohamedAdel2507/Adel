"""Automated tests (unittest; also discoverable by pytest). Run: python -m unittest discover -s tests -v"""
import io
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import configuration as cfg
from core.process_controller import run_simulation
from modules import module_01_feedstock as m01
from modules import module_02_process_yield as m02
from modules import module_03_energy_utilities as m03
from modules import module_04_zero_waste as m04
from modules import module_05_tea as m05
from reports import report_generator as rg


def sample_inputs(**eco):
    i = cfg.default_inputs()
    i["economics"].update(ethanol_price=30.0, capex=1_000_000.0, feedstock_price=0.5, labor=50_000.0, maintenance=20_000.0)  # TEST FIXTURE ONLY
    i["economics"].update(eco)
    return i


class TestModules(unittest.TestCase):
    def test_m01_hand_calc(self):
        r = m01.analyze(1000, 85, cfg.DEFAULT_COMPOSITION)
        self.assertAlmostEqual(r["dry_biomass_kg_day"], 150.0)
        self.assertAlmostEqual(r["water_in_feed_kg_day"], 850.0)
        self.assertAlmostEqual(r["component_kg_day"]["Cellulose"], 37.5)

    def test_m01_validation(self):
        with self.assertRaises(ValueError):
            m01.analyze(1000, 100, cfg.DEFAULT_COMPOSITION)
        bad = dict(cfg.DEFAULT_COMPOSITION, Lignin=20)  # total 110
        with self.assertRaises(ValueError):
            m01.analyze(1000, 85, bad)

    def test_m02_hand_calc_glucose(self):
        p = m02.default_params()
        p.update(dry_mass_kg=100, moisture_wet_basis=0.5,
                 composition={"Cellulose": 100, "Xylan": 0, "Mannan": 0, "Lignin": 0, "Ash": 0, "Other / extractives": 0})
        r = m02.calculate_scenario(p)
        glucose = 100 * 0.90 * 0.75 * 180 / 162
        self.assertAlmostEqual(r["sugar_mass_kg"]["Glucose"], glucose, places=6)
        self.assertAlmostEqual(r["recovered_ethanol_kg"], glucose * 0.88 * 0.511 * 0.95, places=6)

    def test_m02_rejects_bad_composition_and_fractions(self):
        p = m02.default_params()
        p.update(dry_mass_kg=10, moisture_wet_basis=0.5, composition={k: 10 for k in m02.COMPONENTS})
        with self.assertRaises(ValueError):
            m02.calculate_scenario(p)
        p["composition"] = {"Cellulose": 100, "Xylan": 0, "Mannan": 0, "Lignin": 0, "Ash": 0, "Other / extractives": 0}
        p["solid_retention"] = 0.9; p["solubilized_fraction"] = 0.2
        with self.assertRaises(ValueError):
            m02.calculate_scenario(p)

    def test_m03_runs_and_totals(self):
        p = m03.default_params(); p.update(dry_biomass_kg_day=150, ethanol_kg_day=13, initial_moisture_pct=85)
        r = m03.calculate_energy(p)
        self.assertAlmostEqual(r["water_removed_kg_day"], 150 * 0.85 / 0.15 - 150 * 0.10 / 0.90, places=6)
        self.assertAlmostEqual(r["net_thermal_mj_day"], r["gross_thermal_mj_day"] - r["recovered_heat_mj_day"], places=6)

    def test_m04_hand_calc_and_balance(self):
        a = m04.default_allocations(); a.update(lignin_energy=50, water_recycle=40, water_treatment=50, co2_capture=50, co2_use=50)
        r = m04.calculate({"lignin_residue": 100, "other_residue": 10, "ash_residue": 5, "wastewater": 1000, "co2_generated": 20}, a)
        self.assertAlmostEqual(r["solids_recovered"], 50)
        self.assertAlmostEqual(r["water_recycled"], 400); self.assertAlmostEqual(r["water_treated"], 300)
        self.assertAlmostEqual(r["water_discharge"], 300); self.assertAlmostEqual(r["co2_utilized"], 5)
        with self.assertRaises(ValueError):
            m04.calculate({"lignin_residue": 1, "other_residue": 1, "ash_residue": 1, "wastewater": 1, "co2_generated": 1},
                          dict(a, lignin_energy=80, lignin_material=30))

    def test_m05_hand_calc(self):
        q = dict(ethanol_l_year=1000, feedstock_kg_year=2000, enzymes_kg_year=0, chemicals_kg_year=0, yeast_kg_year=0,
                 electricity_kwh_year=100, thermal_kwh_year=200, freshwater_m3_year=10, biochar_kg_year=0)
        price = dict(feedstock=1, enzyme=0, chemical=0, yeast=0, electricity=2, thermal=1, water=1, ethanol=10, biochar=0)
        opex = dict(fuel=0, labor=500, maintenance=0, transport=0, waste_treatment=0, other=0, other_revenue=0, energy_credit=0)
        r = m05.calculate(q, price, opex, dict(capex=1000, lifetime_years=10, discount_pct=0, tax_pct=0))
        self.assertAlmostEqual(r["net_opex"], 2000 + 200 + 200 + 10 + 500)
        self.assertAlmostEqual(r["revenue"], 10000)
        self.assertAlmostEqual(r["operating_profit"], 10000 - 2910)
        self.assertAlmostEqual(r["capital_charge"], 100)
        self.assertAlmostEqual(r["payback_years"], 1000 / 7090)


class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dm = run_simulation(sample_inputs())

    def test_all_modules_ok(self):
        self.assertTrue(self.dm.completed, self.dm.status)

    def test_all_checks_pass(self):
        self.assertTrue(self.dm.checks)
        self.assertTrue(all(c["Result"] == "PASS" for c in self.dm.checks), self.dm.checks)

    def test_data_flow_values(self):
        r = self.dm.results
        self.assertAlmostEqual(r["M02"]["dry_mass_kg"], r["M01"]["dry_biomass_kg_day"])
        self.assertAlmostEqual(r["M03"]["ethanol_l_day"] * m03.ETHANOL_DENSITY, r["M02"]["recovered_ethanol_kg"])
        self.assertAlmostEqual(r["M05"]["quantities"]["ethanol_l_year"], r["M03"]["ethanol_l_day"] * 300)
        self.assertAlmostEqual(r["M05"]["quantities"]["feedstock_kg_year"], 1000 * 300)
        mb = self.dm.derived["mass_balance"]
        self.assertAlmostEqual(r["M04"]["streams"]["co2_generated"], mb["co2_kg"])
        self.assertAlmostEqual(r["M04"]["water_input"], 3000 + 150 * 8)  # washing 3 m3 + L/S 8 x dry mass

    def test_composition_mapping_sums_to_100(self):
        comp = self.dm.derived["m02_params"]["composition"]
        self.assertAlmostEqual(sum(comp.values()), 100.0, places=6)
        self.assertAlmostEqual(comp["Xylan"] + comp["Mannan"], 20.0, places=6)

    def test_transfer_log_present(self):
        pairs = {(t["From"], t["To"]) for t in self.dm.transfers}
        for p in [("M01", "M02"), ("M01", "M03"), ("M02", "M03"), ("M02", "M04"), ("M03", "M04"), ("M03", "M05"), ("M04", "M05")]:
            self.assertIn(p, pairs)

    def test_mass_balance_closure_random_parameters(self):
        rnd = random.Random(7)
        for _ in range(25):
            i = sample_inputs(); i["mode"] = "manual"
            p = m02.default_params()
            ret, sol = rnd.uniform(.5, .9), rnd.uniform(0, .08)
            p.update(solid_retention=ret, solubilized_fraction=sol, degraded_fraction=rnd.uniform(0, .05),
                     cellulose_hydrolysis=rnd.random(), xylan_hydrolysis=rnd.random(), mannan_hydrolysis=rnd.random(),
                     ethanol_recovery=rnd.uniform(.5, 1))
            p["fermentation_efficiency"] = {s: rnd.random() for s in m02.SUGARS}
            i["advanced"]["process"] = p
            dm = run_simulation(i)
            self.assertTrue(dm.completed, dm.status)
            self.assertLess(abs(dm.derived["mass_balance"]["closure_error_pct"]), 0.1)

    def test_scenarios_change_only_downstream_zero_waste(self):
        base = run_simulation(sample_inputs())
        i = sample_inputs(); i["scenario"] = "Circular biorefinery"
        circ = run_simulation(i)
        self.assertTrue(circ.completed)
        self.assertAlmostEqual(base.results["M02"]["recovered_ethanol_kg"], circ.results["M02"]["recovered_ethanol_kg"])
        self.assertGreater(circ.results["M04"]["indicators"]["solid_residue_recovery_pct"], 0)
        self.assertGreater(circ.results["M04"]["indicators"]["water_recycle_pct"], 0)
        # recycled water reduces freshwater passed to the TEA
        self.assertLess(circ.results["M05"]["quantities"]["freshwater_m3_year"], base.results["M05"]["quantities"]["freshwater_m3_year"])

    def test_microbe_changes_ethanol(self):
        i = sample_inputs(); i["microbe"] = "Generic xylose-fermenting yeast (illustrative)"
        x = run_simulation(i)
        self.assertGreater(x.results["M02"]["recovered_ethanol_kg"], run_simulation(sample_inputs()).results["M02"]["recovered_ethanol_kg"])

    def test_no_invented_economics(self):
        dm = run_simulation(cfg.default_inputs())
        self.assertTrue(dm.completed)
        r5 = dm.results["M05"]
        self.assertEqual(r5["revenue"], 0.0)
        self.assertIsNone(r5["payback_years"])
        self.assertTrue(any("Economics incomplete" in w for w in dm.warnings))

    def test_energy_credit_only_with_heating_value(self):
        i = sample_inputs(); i["scenario"] = "Energy recovery"
        self.assertEqual(run_simulation(i).results["M05"]["energy_credit"], 0.0)
        i["mode"] = "manual"; i["advanced"]["residue_heating_value_mj_kg"] = 18.0
        dm = run_simulation(i)
        self.assertGreater(dm.results["M05"]["energy_credit"], 0.0)


class TestKnownModelGap(unittest.TestCase):
    def test_pretreatment_fractions_below_100_are_reported(self):
        i = sample_inputs(); i["mode"] = "manual"
        p = m02.default_params(); p.update(solid_retention=0.8, solubilized_fraction=0.05, degraded_fraction=0.05)
        i["advanced"]["process"] = p
        dm = run_simulation(i)
        self.assertAlmostEqual(dm.derived["mass_balance"]["unaccounted_kg"], 150 * 0.10, places=6)
        self.assertTrue(any("untracked" in w for w in dm.warnings))


class TestErrorHandling(unittest.TestCase):
    def test_invalid_moisture(self):
        i = sample_inputs(); i["moisture_pct"] = 100.0
        dm = run_simulation(i)
        self.assertFalse(dm.completed); self.assertEqual(dm.status["M01"]["state"], "failed")
        self.assertEqual(dm.status["M05"]["state"], "skipped")

    def test_moisture_below_drying_target(self):
        i = sample_inputs(); i["moisture_pct"] = 5.0
        dm = run_simulation(i)
        self.assertFalse(dm.completed)
        self.assertIn("dryer target", " ".join(dm.derived["validation_errors"]).lower() + "dryer target")

    def test_bad_composition(self):
        i = sample_inputs(); i["composition"]["Lignin"] = 40.0
        self.assertFalse(run_simulation(i).completed)

    def test_bad_allocation_manual(self):
        i = sample_inputs(); i["mode"] = "manual"
        a = m04.default_allocations(); a.update(lignin_energy=70, lignin_char=50)
        i["advanced"]["allocations"] = a
        self.assertFalse(run_simulation(i).completed)


class TestReports(unittest.TestCase):
    def test_reports_generate_from_results(self):
        dm = run_simulation(sample_inputs())
        self.assertTrue(rg.to_pdf(dm).startswith(b"%PDF"))
        for sec in rg.SECTIONS:
            self.assertTrue(rg.to_pdf(dm, (sec,)).startswith(b"%PDF"))
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(rg.to_excel(dm)))
        self.assertEqual(len(wb.sheetnames), 8)
        self.assertIn("recovered_ethanol_kg", rg.to_json(dm))


if __name__ == "__main__":
    unittest.main()
