# Quantity Validity Card (QVC)

Anonymous benchmark kit for medical **quantity validity** (entailment under dose/unit edits).

## Quickstart

```bash
pip install -e .
python -c "from qvc.data import load_inv_unit; print(len(load_inv_unit()))"
python -c "from qvc.normalize import normalize_pair; print(normalize_pair('500 mg', '0.5 g'))"
python scripts/qvc_reproduce_paper_numbers.py
pytest qvc/tests -q
```

See `qvc/evaluate/card.py` for `evaluate(verifier_fn)` and Markdown card output.
