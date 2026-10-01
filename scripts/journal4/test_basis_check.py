"""Unit tests for scripts/journal4/basis_check.py (stdlib unittest; also runs under pytest).

    python -m unittest scripts/journal4/test_basis_check.py      (from the repo root)
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import basis_check as B  # noqa: E402

RD = HERE.parents[1] / "results" / "journal2" / "real_dose" / "instances.jsonl"


def flag(claim, evidence, variant="full"):
    r = B.check_pair(claim, evidence)
    return r["flag_" + variant], r["flag_type_" + variant], r["status_" + variant]


class TestFourPatterns(unittest.TestCase):
    """The four motivating error patterns (synthetic snippets modelled on the real RD rows)."""

    def test_losartan_dropped_per_kg(self):
        self.assertEqual(flag("the dose is 0.7 mg once daily (up to 50 mg) for pediatric patients.",
                              "Usual adult dose: 50 mg once daily. Usual pediatric starting dose: 0.7 mg per kg once daily "
                              "(up to 50 mg)."), (True, "basis_dropped", "flag"))

    def test_tacrolimus_dropped_per_kg_day(self):
        self.assertEqual(flag("The initial oral dosage is 0.2 mg capsules, divided in two doses every 12 hours.",
                              "With azathioprine 0.2 mg/kg/day capsules, divided in two doses, every 12 hours."),
                         (True, "basis_dropped", "flag"))

    def test_ethambutol_kg_to_lb(self):
        self.assertEqual(flag("the dose is 15 mg/lb of body weight.",
                              "decrease the dose to 15 mg/kg (7 mg/lb) of body weight"), (True, "basis_changed", "flag"))

    def test_clonidine_day_to_week(self):
        self.assertEqual(flag("starting with clonidine transdermal system 0.1 mg/week.",
                              "starting with clonidine transdermal system 0.1 mg/day."), (True, "time_basis", "flag"))

    def test_patterns_are_r1_strict(self):
        self.assertTrue(flag("the dose is 0.7 mg once daily.", "0.7 mg per kg once daily", "strict")[0])
        self.assertTrue(flag("0.1 mg/week", "0.1 mg/day", "strict")[0])


class TestNegatives(unittest.TestCase):
    def test_correct_mg_per_kg(self):
        self.assertEqual(flag("The pediatric starting dose is 0.7 mg/kg once daily, up to 50 mg.",
                              "Usual pediatric starting dose: 0.7 mg per kg once daily (up to 50 mg)."), (False, "", "pass"))

    def test_mg_per_kg_plus_absolute_for_stated_weight(self):
        ev = "the recommended total daily dose is 50 to 75 mg/kg given once a day. The total daily dose should not exceed 2 grams."
        self.assertEqual(flag("The dose is 50 mg/kg once daily; for a 20 kg child that is 1,000 mg.", ev), (False, "", "pass"))
        self.assertEqual(flag("The dose is 50-75 mg/kg/day, i.e. 1000-1500 mg per day for a 20 kg child.", ev)[0], False)
        self.assertEqual(flag("15 mg/kg, which is 1050 mg for a 154 lb (70 kg) patient.", "15 mg/kg (7 mg/lb)")[0], False)

    def test_absolute_dose_inconsistent_with_stated_weight_is_flagged(self):
        # 15 mg/kg x 70 kg = 1050 mg; the answer's absolute 15 mg (same numeral, basis dropped) is not explained
        self.assertTrue(flag("For a 70 kg patient give 15 mg.", "decrease the dose to 15 mg/kg of body weight")[0])

    def test_equivalent_conversions(self):
        self.assertFalse(flag("The dose is 7 mg/lb.", "15 mg/kg (7 mg/lb)")[0])
        self.assertFalse(flag("The dose is 33 mg/kg.", "The dose is 15 mg/lb.")[0])
        self.assertFalse(flag("0.7 mg/week", "0.1 mg/day")[0])
        self.assertFalse(flag("The dose is 0.5 g twice daily.", "Give 500 mg twice daily.")[0])
        self.assertFalse(flag("1,000 mcg IM", "Give 1 mg IM.")[0])

    def test_lost_superscript_m2_is_not_flagged(self):
        self.assertFalse(flag("The dose is 500 mg/m².", "doses of 500 mg/m 2 or greater")[0])

    def test_split_unit_phrase(self):
        self.assertFalse(flag("200 micrograms per kg of body weight",
                              "a single oral dose designed to provide approximately 200 mcg of ivermectin per kg of body weight")[0])

    def test_value_error_same_basis_not_flagged(self):
        self.assertFalse(flag("300 mg/m² every 8 hours", "100 mg/m 2 orally every 8 hours (maximum 800 mg/day)")[0])

    def test_per_dose_vs_per_day_not_judged(self):
        self.assertFalse(flag("150-300 mg per dose", "begin at 300 mg/day in 2 divided doses")[0])

    def test_no_dose(self):
        self.assertEqual(flag("Follow your doctor's instructions.", "Give 500 mg twice daily."), (False, "", "no_dose"))

    def test_abstain_when_nothing_comparable(self):
        self.assertEqual(flag("The dose is 20 mEq.", "Give 500 mg twice daily."), (False, "", "abstain"))


class TestOtherFlags(unittest.TestCase):
    def test_unit_kind(self):
        self.assertEqual(flag("The dose is 20 mg.", "If the insulin dose is less than 20 units daily, use 2.5 to 5 mg.")[1],
                         "unit_kind")

    def test_unit_scale_same_numeral(self):
        self.assertEqual(flag("500 mcg twice daily", "Give 500 mg twice daily.")[1], "unit_scale")

    def test_unit_scale_misconversion(self):
        self.assertEqual(flag("0.5 g daily", "500 mcg daily")[1], "unit_scale")

    def test_r2_unpaired_only_in_full(self):
        c, e = "The dose is 300 mcg daily.", "The recommended starting dosage is 5 mcg/kg/day. Escalate in increments of 5 mcg/kg."
        self.assertEqual(flag(c, e)[:2], (True, "basis_dropped_unpaired"))
        self.assertFalse(flag(c, e, "strict")[0])

    def test_r2_not_when_evidence_has_absolute_dose(self):
        self.assertFalse(flag("The dose is 300 mg.", "Adults: 400 mg daily. Children: 8 mg/kg daily.")[0])

    def test_bounds_and_strengths_excluded_from_r2(self):
        self.assertTrue(flag("The dose is 500 mg once a day.",
                             "the recommended total daily dose is 50 to 75 mg/kg. The total daily dose should not exceed 2 grams.")[0])
        self.assertTrue(flag("The dose is 15 mg.", "Number of 3-mg Tablets 15 to 25 1 tablet ... >=85 150 mcg/kg")[0])


@unittest.skipUnless(RD.is_file(), "RD instances not present")
class TestDevRows(unittest.TestCase):
    """Regression on the four real RD rows behind the motivating patterns (dev set; seen while designing the rule)."""
    IDS = {"losartan": "basis_dropped", "tacrolimus": "basis_dropped", "ethambutol": "basis_changed", "clonidine": "time_basis"}

    def test_real_rows(self):
        import csv
        pre = HERE.parents[1] / "qc" / "ai_precheck_real_dose_unit_errors.csv"
        with pre.open(encoding="utf-8") as fh:
            true_ids = {r["instance_id"]: r["drug"] for r in csv.DictReader(l for l in fh if not l.startswith("#"))
                        if r["ai_label"] == "true_unit_error"}
        with RD.open(encoding="utf-8") as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        seen = 0
        for r in rows:
            if r["instance_id"] in true_ids and r["drug"] in self.IDS:
                res = B.check_pair(r["claim"], r["evidence"])
                self.assertEqual(res["flag_type_strict"], self.IDS[r["drug"]], r["instance_id"])
                seen += 1
        self.assertEqual(seen, 4)


class TestSelftest(unittest.TestCase):
    def test_module_selftest_cases(self):
        for name, c, e, want, wtype in B.SELFTEST:
            r = B.check_pair(c, e)
            self.assertEqual((r["flag_full"], r["flag_type_full"]), (want, wtype), name)


if __name__ == "__main__":
    unittest.main()
