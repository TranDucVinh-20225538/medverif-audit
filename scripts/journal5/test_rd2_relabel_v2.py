#!/usr/bin/env python3
"""Tests for scripts/journal5/rd2_relabel_v2.py (RD2 amendment 1).

Run:  python scripts/journal5/test_rd2_relabel_v2.py -v
(`python -m unittest` from the repo root picks up a site-packages package named `scripts` in the vllm env.)
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rd2_common as C  # noqa: E402
import rd2_relabel_v2 as V  # noqa: E402
from rd_extract import classify  # noqa: E402
from unit_norm_fix import find_spans  # noqa: E402

UNIT_TYPE = ("unit_error", "basis_error")

# the 33 BSA-superscript artefacts: v1 unit/basis error (per_m2) caused by a flattened "m 2" (relabel_diff.md)
M2_ARTEFACTS = [
    "RD2_ifosfamide_0__baichuan_m2_32b__closed", "RD2_ifosfamide_0__baichuan_m2_32b__grounded",
    "RD2_ifosfamide_0__gemma3_27b__closed", "RD2_ifosfamide_0__gemma3_27b__grounded", "RD2_ifosfamide_0__gpt4o_mini__closed",
    "RD2_ifosfamide_0__gpt4o_mini__grounded", "RD2_ifosfamide_0__llama31_8b__closed", "RD2_ifosfamide_0__llama31_8b__grounded",
    "RD2_ifosfamide_0__medgemma_27b__closed", "RD2_ifosfamide_0__qwen25_14b__closed", "RD2_ifosfamide_0__qwen25_14b__grounded",
    "RD2_pegaspargase_0__baichuan_m2_32b__closed", "RD2_pegaspargase_0__baichuan_m2_32b__grounded",
    "RD2_pegaspargase_0__gemma3_27b__closed", "RD2_pegaspargase_0__gemma3_27b__grounded", "RD2_pegaspargase_0__gpt4o_mini__closed",
    "RD2_pegaspargase_0__gpt4o_mini__grounded", "RD2_pegaspargase_0__llama31_8b__closed",
    "RD2_pegaspargase_0__llama31_8b__grounded", "RD2_pegaspargase_0__medgemma_27b__closed",
    "RD2_pegaspargase_0__qwen25_14b__closed", "RD2_ritonavir_1__baichuan_m2_32b__closed", "RD2_ritonavir_1__gemma3_27b__closed",
    "RD2_ritonavir_1__gpt4o_mini__closed", "RD2_ritonavir_1__gpt4o_mini__grounded", "RD2_ritonavir_1__llama31_8b__closed",
    "RD2_ritonavir_1__medgemma_27b__closed", "RD2_ritonavir_1__qwen25_14b__closed", "RD2_temozolomide_1__gemma3_27b__closed",
    "RD2_temozolomide_1__gpt4o_mini__closed", "RD2_temozolomide_1__llama31_8b__closed",
    "RD2_temozolomide_1__llama31_8b__grounded", "RD2_temozolomide_1__medgemma_27b__closed",
]


def spans(text):
    return [s.text for s in find_spans(text)]


class TestPatchSurface(unittest.TestCase):
    def test_positive_forms(self):
        cases = {
            "100mg/m 2 per day": "100mg/m2 per day",
            "2,000 International Units/m 2 IM": "2,000 International Units/m2 IM",
            "1.2 grams per m 2 per day": "1.2 grams per m2 per day",
            "400 mg per m 2 twice daily": "400 mg per m2 twice daily",
            "75 mg / m 2 IV": "75 mg/m2 IV",
            "75 mg/m^2 IV": "75 mg/m2 IV",
            "75 mg/m ² IV": "75 mg/m2 IV",
            "75 mg/sq m IV": "75 mg/m2 IV",
            "75 mg per sq. m": "75 mg per m2",
            "75 mg per square meters": "75 mg per m2",
            "the dose is 400 mg/m 2.": "the dose is 400 mg/m2.",
            "**400 mg** per m 2 twice": "**400 mg per m2 twice",
        }
        for src, want in cases.items():
            with self.subTest(src=src):
                self.assertEqual(V.patch_m2(src), want)
                self.assertTrue(any(s.endswith("m2") or "m2 " in s or s.endswith("/m2") for s in spans(V.patch_m2(src))) or
                                any(sp.m2 for sp in find_spans(V.patch_m2(src))))

    def test_basis_visible_after_patch(self):
        for src in ("100mg/m 2", "2,000 International Units/m 2", "1.2 grams per m 2", "400 mg per m 2", "**400 mg** per m 2"):
            with self.subTest(src=src):
                self.assertFalse(any(sp.m2 for sp in find_spans(src)))
                self.assertTrue(find_spans(V.patch_m2(src))[0].m2)


class TestNegatives(unittest.TestCase):
    """Text without a BSA m-token after a dose unit / 'per' must be unchanged and keep its class."""

    UNCHANGED = [
        "walk 2 m before the injection",                      # length
        "infuse through a 2 m line",                          # length
        "a 0.2 micron filter, 1.5 m tubing",                  # length
        "M2 receptor antagonist; Mk 2 device",                 # m2 in names / codes
        "Lot M2-104, NDC 0409-2 m",                           # codes
        "Baichuan-M2-32B said 10 mg",                         # model name containing m2
        "10 mg/kg once daily",                                # /kg untouched
        "5 mg per kg body weight",                            # per kg untouched
        "100 mg/m2 every 3 weeks",                            # already readable -> unchanged
        "150 mg/m 25 minutes later",                          # "m 25" is not m2 (digit follows)
        "dose of 2 mg per mL",                                # concentration
        "1 g per m 3 of room air",                            # not m2
    ]

    def test_patch_identity(self):
        for s in self.UNCHANGED:
            with self.subTest(s=s):
                self.assertEqual(V.patch_m2(s), s)

    def test_true_bsa_errors_stay(self):
        cases = [  # (answer, target, primary, expected class)
            ("The dose is 60 mg/kg.", "The dose is 60 mg/m 2 IV.", None, "unit_error"),           # true per_kg vs m2
            ("The dose is 3.5 mg/m2.", "3.5 mg per kg body weight", None, "unit_error"),           # true m2 vs kg
            ("The dose is 100 mg.", "Give 100 mg per m 2 twice daily.", None, "unit_error"),       # answer drops BSA
            ("The dose is 10 mg/m2.", "Give 5 mg/kg on day 1.", None, "basis_error"),              # different basis
            ("The dose is 200 mg/m 2.", "Give 100mg/m 2 IV on day 1.", None, "value_error"),       # wrong number, BSA both
        ]
        for ans, tgt, pr, want in cases:
            with self.subTest(ans=ans, tgt=tgt):
                self.assertEqual(V.classify_v2(ans, tgt, tgt, pr)["auto_class"], want)

    def test_unpatched_rows_unchanged_in_data(self):
        rows = C.read_jsonl(V.OUT / "labels_v2.jsonl")
        for r in rows:
            if not r["answer_patched"] and not r["label_patched"] and r["class_v1"] != "no_dose":
                self.assertEqual(r["class_v1"], r["class_v2"], r["instance_id"])


class TestRealArtefacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        qs = {q["qid"]: q for q in C.read_jsonl(C.QUESTIONS)}
        cls.rows = {}
        for r in C.read_jsonl(C.RD2 / "extract_rows.jsonl"):
            if r["instance_id"] in M2_ARTEFACTS:
                cls.rows[r["instance_id"]] = (r, qs[r["qid"]])

    def test_all_33_flip(self):
        self.assertEqual(len(self.rows), 33)
        for iid, (r, q) in sorted(self.rows.items()):
            with self.subTest(iid=iid):
                v1 = classify(r["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"))
                v2 = V.classify_v2(r["answer"], q["target_sentence"], q["excerpt"], q.get("primary_target"), v1["auto_class"])
                self.assertIn(v1["auto_class"], UNIT_TYPE)
                self.assertEqual(v1["subtype"], "per_m2")
                self.assertNotIn(v2["auto_class"], UNIT_TYPE)

    def test_no_new_unit_type_errors(self):
        rows = C.read_jsonl(V.OUT / "labels_v2.jsonl")
        new = [r["instance_id"] for r in rows if r["class_v2"] in UNIT_TYPE and r["class_v1"] not in UNIT_TYPE]
        self.assertEqual(new, [])

    def test_column_totals(self):
        rows = C.read_jsonl(V.OUT / "labels_v2.jsonl")
        self.assertEqual(len(rows), 5760)
        nd1 = sum(r["class_v1"] == "no_dose" for r in rows)
        nd2 = sum(r["class_v2"] == "no_dose" for r in rows)
        self.assertEqual((nd1, nd2), (72, 68))


class TestNoDoseRecovery(unittest.TestCase):
    def test_recover_forms(self):
        self.assertEqual(V.recover_nodose("give 2.5 million units daily"), "give 2500000 units daily")
        self.assertEqual(V.recover_nodose("2.5 to 5 million units"), "2500000 to 5000000 units")
        self.assertEqual(V.recover_nodose("is 37.5, unit: mg."), "is 37.5 mg.")
        self.assertEqual(V.recover_nodose("4 fluid ounces of water"), "4 fluid ounces of water")

    def test_recovery_only_for_nodose(self):
        a = "The dose is 2.5 million units, i.e. 5 mg."
        self.assertEqual(V.classify_v2(a, "5 mg daily", "5 mg daily", None, "correct")["primary"], "5 mg")


if __name__ == "__main__":
    unittest.main()
