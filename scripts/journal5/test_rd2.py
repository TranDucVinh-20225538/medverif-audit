"""Unit tests for journal 5 / RD2 (stdlib unittest; also runs under pytest).  CPU only, no network, no GPU.

    python -m unittest scripts/journal5/test_rd2.py      (from the repo root)
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rd2_common as C  # noqa: E402
import rd2_extract as X  # noqa: E402
import rd2_questions as Q  # noqa: E402
from unit_norm_fix import find_spans  # noqa: E402

RD_EXTRA = ("source", "rd2") + X.EXTRA


def tags(sentence, before=""):
    s = Q.repair_m2(sentence)
    sp = find_spans(s)
    prim = next(d for d in sp if not d.conc)
    return C.tag_dosing(s, before, sp, prim)


class TestReuseOfOriginalRDCode(unittest.TestCase):
    def test_question_builder_reproduces_rd_questions_exactly(self):
        mine = Q.rd_policy_questions(C.read_jsonl(C.RD1_LABELS))
        orig = C.read_jsonl(C.RD1 / "questions.jsonl")
        self.assertEqual(len(mine), 364)
        self.assertEqual(mine, orig)

    def test_extract_reproduces_rd_instances_exactly(self):
        inst, rows, _ = X.build(C.read_jsonl(C.RD1 / "questions.jsonl"), C.read_jsonl(C.RD1 / "answers.jsonl"))
        orig = C.read_jsonl(C.RD1 / "instances.jsonl")
        self.assertEqual(len(inst), len(orig))
        strip = lambda r: {k: v for k, v in r.items() if k not in RD_EXTRA}  # noqa: E731
        self.assertEqual([strip(r) for r in inst], [strip(r) for r in orig])
        self.assertEqual(set(orig[0]) - set(inst[0]), set())  # every RD key present in RD2 instances
        self.assertTrue(all(r["source"] == "journal5_rd2" for r in inst))


class TestRD2Questions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qs = C.read_jsonl(C.QUESTIONS)
        cls.man = json.loads((C.QUESTIONS.parent / "questions_manifest.json").read_text())

    def test_count_and_range(self):
        self.assertTrue(300 <= len(self.qs) <= 500)
        self.assertEqual(len({q["qid"] for q in self.qs}), len(self.qs))

    def test_deterministic_regeneration(self):
        p = self.man["params"]
        again, _ = Q.select(C.read_jsonl(C.RD2_LABELS), p["n"], p["per_drug"], p["gap"], p["fixed_share"], p["seed"])
        self.assertEqual(again, self.qs)

    def test_zero_overlap_with_rd(self):
        ex = C.rd1_exclusion()
        rd2_labels = {l["drug"]: l for l in C.read_jsonl(C.RD2_LABELS)}
        self.assertEqual({q["drug"] for q in self.qs} & ex["drugs"], set())
        self.assertEqual({q["set_id"] for q in self.qs} & ex["set_ids"], set())
        self.assertEqual({q["target_sentence"] for q in self.qs} & ex["target_sentences"], set())
        for q in self.qs:
            self.assertEqual(C.label_overlaps_rd1(rd2_labels[q["drug"]], ex), "", q["qid"])

    def test_schema_matches_rd_questions(self):
        rd = C.read_jsonl(C.RD1 / "questions.jsonl")[0]
        for q in self.qs:
            self.assertTrue(set(rd) <= set(q))
            self.assertEqual(q["masked"].count("[DOSE]"), 1)
            self.assertIn(q["target_sentence"], q["excerpt"])
            self.assertNotIn(q["primary_target"], q["masked"])

    def test_error_prone_share(self):
        ep = sum(q["stratum"] != "fixed" for q in self.qs)
        self.assertGreaterEqual(ep / len(self.qs), 0.8)

    def test_freeze_file_matches(self):
        if not C.FREEZE.is_file():
            self.skipTest("prereg/rd2_freeze.json not written yet")
        self.assertEqual(C.freeze_problems(), [])


class TestTaggerAndFilters(unittest.TestCase):
    def test_bsa_after_m2_repair(self):
        self.assertEqual(Q.repair_m2("75 mg/m 2 IV"), "75 mg/m2 IV")
        self.assertEqual(tags("Give 75 mg/m 2 intravenously over 1 hour.")["stratum"], "bsa")

    def test_weight_pediatric_loading(self):
        t = tags("Pediatric patients: a loading dose of 20 mg/kg followed by 5 mg/kg every 12 hours.")
        self.assertEqual(t["stratum"], "weight_based")
        self.assertIn("pediatric", t["dosing_types"])
        self.assertIn("loading_maintenance", t["dosing_types"])

    def test_renal_divided_fixed(self):
        self.assertEqual(tags("For CrCl 30 to 50 mL/min, give 250 mg every 12 hours.")["stratum"], "renal")
        self.assertEqual(tags("The usual dose is 600 mg/day given in 3 divided doses.")["stratum"], "divided_daily")
        self.assertEqual(tags("The recommended dose is 500 mg once daily.")["stratum"], "fixed")

    def test_non_dose_targets(self):
        s = "In patients with creatinine clearance below 30 mL/min, reduce the dose by half."
        self.assertEqual(Q.non_dose_target(s, find_spans(s)), "renal_threshold")
        s = "Dilute the dose in 100 mL of 0.9% Sodium Chloride Injection."
        self.assertEqual(Q.non_dose_target(s, find_spans(s)), "diluent_volume")
        s = "Give 5 mL by mouth twice daily."
        self.assertEqual(Q.non_dose_target(s, find_spans(s)), "")


class TestMockPipeline(unittest.TestCase):
    """Mock answers -> extraction with the original classifier -> instance schema + expected classes."""

    def test_mock_answers_extract(self):
        import rd2_generate as G
        qs = C.read_jsonl(C.QUESTIONS)[:24]
        gen = G.MockGen({G.render(q, c): (q, c) for q in qs for c in ("grounded", "closed")})
        answers = []
        for c in ("grounded", "closed"):
            outs = gen.generate([G.render(q, c) for q in qs])
            answers += [{"qid": q["qid"], "generator": "mock", "condition": c, "answer": G.clean(o["raw"])} for q, o in zip(qs, outs)]
        inst, rows, stats = X.build(qs, answers)
        self.assertEqual(len(rows), 48)
        g = [r for r in rows if r["condition"] == "grounded"]
        self.assertTrue(all(r["auto_class"] == "correct" for r in g), [(r["answer"], r["target_sentence"]) for r in g
                                                                         if r["auto_class"] != "correct"])
        dropped = [r for r in rows if r["condition"] == "closed" and r["primary"] and "/" not in r["primary"] and
                   any(s.kg or s.m2 for s in find_spans(r["target_sentence"])[:1])]
        for r in dropped:
            self.assertIn(r["auto_class"], ("unit_error", "basis_error"), r["answer"])
        rd_keys = set(C.read_jsonl(C.RD1 / "instances.jsonl")[0])
        self.assertTrue(all(rd_keys <= set(i) for i in inst))

    def test_think_block_stripped(self):
        import rd2_generate as G
        self.assertEqual(G.clean("<think>reasoning</think>\n The dose is 5 mg/kg."), "The dose is 5 mg/kg.")
        self.assertEqual(G.clean(" The dose is 5 mg. "), "The dose is 5 mg.")
        self.assertEqual(G.clean("<think>still reasoning about the dose"), "")

    def test_prompts_are_rd_prompts(self):
        import rd2_generate as G
        import rd_generate as R
        self.assertIs(G.PROMPTS, R.PROMPTS)
        self.assertEqual(G.MAX_TOKENS, 160)
        if C.FREEZE.is_file():
            self.assertEqual(json.loads(C.FREEZE.read_text())["prompts_sha256"], G.PROMPT_SHA)


if __name__ == "__main__":
    unittest.main()
