# DEPRECATED — T8 synthetic INV/E1 unit sample (audit only)

**Status:** dropped 2026-09-29. Do **not** score on node30 or OpenRouter.

**Reason:** flawed construction (wrong INV semantics e.g. g→mg, edits on evidence only, non-measurement numerals). See `notes/t8_debug.md`, `notes/t8_aggrefact_inv_report.json`.

**Retained artifacts (git):**

| Path | Role |
|------|------|
| `data/t8/instances_aggrefact_inv.jsonl` | 200 INV/E1 instances (`valid=false`) |
| `data/t8/instances_aggrefact_c0.jsonl` | C0 baselines (`valid=false`) |
| `results/raw/t8/v1b_medscore*.jsonl` | exploratory v1b only |
| `qc/t8_aggrefact_inv_sample.csv` | human QC sample |
| `scripts/t8_build_aggrefact_inv_sample.py` | generator (historical) |

**Active T8 line:** T8b in-benchmark supported subgroups — gated on `qc/t8_mismatch_check.csv` precision ≥80% (`scripts/t8_mismatch_qc_report.py`).
