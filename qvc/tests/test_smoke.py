import unittest

from qvc.adapters.base import verdicts_from_jsonl
from qvc.data.loaders import load_inv_unit
from qvc.normalize import normalize_pair


class TestQVC(unittest.TestCase):
    def test_normalize_pair_mg_g(self):
        c, e = normalize_pair("500 mg daily", "0.5 g daily")
        self.assertIn("500 mg", c)
        self.assertIn("500 mg", e)

    def test_bundled_inv_unit(self):
        self.assertGreater(len(load_inv_unit()), 0)

    def test_verdicts_from_jsonl_missing(self):
        self.assertEqual(verdicts_from_jsonl("/nonexistent.jsonl"), {})


if __name__ == "__main__":
    unittest.main()
