"""Unit tests for scripts/journal5/rd2_ci.py (unittest; CPU, synthetic data, no repo outputs touched).

    $MEDVERIF_PYTHON scripts/journal5/test_rd2_ci.py -v      (run the file; the vllm env shadows `scripts`)
"""

from __future__ import print_function

import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rd2_ci as R  # noqa: E402


def _write(path, rows):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


class TestStats(unittest.TestCase):
    def test_mcnemar_exact(self):
        p, method, _ = R.mcnemar(10, 2)
        self.assertEqual(method, "exact")
        # 2 * P(X <= 2), X ~ Bin(12, 0.5) = 2 * 79 / 4096
        self.assertAlmostEqual(p, 2 * 79 / 4096.0, places=10)
        self.assertEqual(R.mcnemar(0, 0)[0], 1.0)
        self.assertEqual(R.mcnemar(5, 5)[0], 1.0)

    def test_mcnemar_chi2_cc(self):
        p, method, stat = R.mcnemar(30, 10)
        self.assertEqual(method, "chi2_cc")
        self.assertAlmostEqual(stat, (20 - 1) ** 2 / 40.0)
        self.assertAlmostEqual(p, 0.0026631, places=6)  # chi2 = 9.025, df 1
        self.assertEqual(R.mcnemar(12, 12)[1], "exact" if 24 < R.EXACT_BELOW else "chi2_cc")
        self.assertEqual(R.mcnemar(13, 12)[1], "chi2_cc")

    def test_holm(self):
        adj = R.holm([0.01, 0.04, 0.03, 0.005])
        np.testing.assert_allclose(adj, [0.03, 0.06, 0.06, 0.02])
        self.assertTrue(np.isnan(R.holm([np.nan, 0.01])[0]))
        self.assertEqual(R.holm([0.9, 0.8])[0], 1.0)

    def test_cluster_weights(self):
        W = R.cluster_weights(7, 50, np.random.default_rng(1))
        self.assertEqual(W.shape, (50, 7))
        self.assertTrue(np.all(W.sum(axis=1) == 7))
        W2 = R.cluster_weights(7, 50, np.random.default_rng(1))
        self.assertTrue(np.array_equal(W, W2))

    def test_boot_ci_contains_point(self):
        rng = np.random.default_rng(0)
        n_c = rng.integers(1, 6, size=200).astype(float)
        k_c = np.array([rng.binomial(int(n), 0.3) for n in n_c], dtype=float)
        lo, hi = R.boot_rate_ci(k_c, n_c, R.cluster_weights(200, 2000, rng))
        self.assertLess(lo, k_c.sum() / n_c.sum())
        self.assertGreater(hi, k_c.sum() / n_c.sum())
        self.assertGreater(lo, 0.2)
        self.assertLess(hi, 0.4)


class TestEndToEnd(unittest.TestCase):
    """Tiny synthetic RD2 directory with the real file layout."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        d = self.tmp
        rng = np.random.default_rng(3)
        inst, ids = [], []
        for q in range(40):
            for g in range(4):
                iid = "RD2_d%d_%d__g%d__closed" % (q // 2, q, g)
                cls = "unit_error" if (q + g) % 4 == 0 else ("correct" if (q + g) % 4 in (1, 2) else "value_error")
                inst.append({"instance_id": iid, "qid": "RD2_d%d_%d" % (q // 2, q), "drug": "d%d" % (q // 2),
                             "auto_class": cls, "generator": "g%d" % g, "answer_condition": "closed"})
                ids.append(iid)
        _write(os.path.join(d, "real_dose", "instances.jsonl"), inst)
        self.err = [r["instance_id"] for r in inst if r["auto_class"] == "unit_error"]
        self.non = [r["instance_id"] for r in inst if r["auto_class"] == "correct"]
        for f in R.PAPER.values():
            _write(os.path.join(d, "real_dose", "scores", f + ".jsonl"),
                   [{"instance_id": i, "score": float(rng.random())} for i in ids])
        # judge with parse fails
        _write(os.path.join(d, "judges", "jx__rd2.jsonl"),
               [{"instance_id": i, "verdict": ("PARSE_FAIL" if k % 10 == 0 else ("PASS" if k % 2 else "FAIL"))}
                for k, i in enumerate(ids)])
        # FT: base = all PASS; r1 = FAIL on the first 30 errors
        for fam in R.FT_FAMILIES:
            for r in ("base",) + R.FT_RATIOS:
                rows = []
                for i in ids:
                    v = "PASS"
                    if r == "r1" and i in self.err[:30]:
                        v = "FAIL"
                    rows.append({"instance_id": i, "verdict": v})
                _write(os.path.join(d, "ft", "%s_%s__rd2_raw.jsonl" % (fam, r)), rows)
                _write(os.path.join(d, "ft", "%s_%s__rd2unf_unf.jsonl" % (fam, r)),
                       [{"instance_id": i, "verdict": "FAIL"} for i in self.err[:3]])
        for var in ("unf_v1", "unf_v2"):
            for f in R.SMALL:
                _write(os.path.join(d, "real_dose", "unf", "scores_" + var, f + ".jsonl"),
                       [{"instance_id": i, "verdict": "PASS", "score": 0.9} for i in self.err[:5]])
        _write(os.path.join(d, "basis_check", "per_item.jsonl"),
               [{"instance_id": i, "flag_full": i in self.err[:20], "flag_strict": i in self.err[:10]} for i in ids])

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_run(self):
        out = os.path.join(self.tmp, "ci")
        rates, mc, meta = R.run(self.tmp, out, n_boot=200, seed=7)
        for fn in ("rd2_ci_rates.csv", "rd2_ci_mcnemar.csv", "rd2_ci.md", "rd2_ci_meta.json"):
            self.assertTrue(os.path.exists(os.path.join(out, fn)), fn)
        self.assertEqual(meta["n_error"], len(self.err))
        self.assertEqual(meta["n_nonerror"], len(self.non))
        # basis check: PASS = not flagged
        r = rates[(rates.system == "basis_check_full") & (rates.set == "error")].iloc[0]
        self.assertEqual((r.k_pass, r.n), (len(self.err) - 20, len(self.err)))
        # judge parse fails excluded from denominator and counted
        r = rates[(rates.system == "jx") & (rates.set == "error")].iloc[0]
        self.assertEqual(r.n + r.parse_fail, len(self.err))
        self.assertGreater(r.parse_fail, 0)
        self.assertLessEqual(r.ci_lo_qid, r.pass_rate)
        self.assertGreaterEqual(r.ci_hi_qid, r.pass_rate)
        # FT r1 vs base on errors: 30 discordant (base PASS, r1 FAIL) -> chi2 branch, tiny p
        m = mc[(mc.other == "FT minicheck_ft5_r1") & (mc.set == "error")].iloc[0]
        self.assertEqual((m.b_base_pass_other_fail, m.c_base_fail_other_pass), (30, 0))
        self.assertEqual(m.method, "chi2_cc")
        self.assertLess(m.p, 1e-6)
        self.assertGreaterEqual(m.p_holm_all, m.p)
        # UNF overlay: unchanged rows keep raw verdicts -> FT r0.5 unf_v1 differs from raw on exactly 3 errors
        m = mc[(mc.other == "FT minicheck_ft5_r0.5 unf_v1") & (mc.set == "error")].iloc[0]
        self.assertEqual((m.b_base_pass_other_fail, m.method), (3, "exact"))
        # 6 FT pairs + (5 small + 8 FT) x (v1 present; v2 small only) ... every test appears for both sets
        self.assertEqual(len(mc) % 2, 0)
        self.assertTrue(set(mc.set) == {"error", "nonerror"})

    def test_deterministic(self):
        a = R.run(self.tmp, "", n_boot=100, seed=11, write=False)[0]
        b = R.run(self.tmp, "", n_boot=100, seed=11, write=False)[0]
        self.assertTrue(a.equals(b))

    def test_labels_override(self):
        lab = os.path.join(self.tmp, "labels.csv")
        with open(lab, "w") as fh:
            fh.write("instance_id,ref\n%s,error\n%s,nonerror\n%s,unclear\n" % (self.err[0], self.non[0], self.non[1]))
        rates, mc, meta = R.run(self.tmp, "", n_boot=50, seed=1, labels_csv=lab, write=False)
        self.assertEqual((meta["n_error"], meta["n_nonerror"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
