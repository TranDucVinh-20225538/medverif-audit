# Standing SHOULD (user permission)

## 1. E2-unit (≤ $1.5 OpenRouter on HPC job)

**Design:** For each of **115 T7 bases**, apply the same **×1000** unit swap to **both** claim and evidence (`condition=E2-unit`, expected **PASS**).

**Artifacts:**
- Builder: `scripts/build_e2_unit_instances.py` → `data/e2/instances_e2_unit_t7.jsonl`
- Node30 pending: merged into `data/expand/instances_pending_node30.jsonl` (+ `data/e2/instances_e2_unit_pending_node30.jsonl`)
- Scores: `results/raw/e2_unit/` (V4 → `v4_ragas_nli.llama.jsonl`)
- Jobs: `jobs/run_e2_unit_hpc.sh`, `jobs/run_e2_unit_node30.sh`
- Table: `scripts/e2_unit_comparison_report.py` → `notes/e2_unit_verifier_comparison.md`

**Verifiers:** HPC — V1, V4 (Llama), V1b, V5, T6-B; node30 — V2, V3, 7× T6-A, Bespoke.

**Report columns:** E2-unit PASS | E2-x2 PASS (same bases) | E1-unit-evid FAIL.

---

## 2. Expanded POL (after PI labels)

**Input:** `qc/expand_pol_flips.csv` (user labels `PI_ok`).

**When labels uploaded:**
1. Merge labeled CSV into analysis gates (`analysis/review_filters.py` / flip base sets).
2. Analysis set = **PI_ok=Y flips only** + template **INV** rows with **PI_ok=Y**.
3. Score all verifiers: HPC LLM judges; node30 encoders + Bespoke on pending JSONL.
4. Re-issue POL table: **original 26**, **expanded**, and **pooled** (`scripts/build_polarity_all_verifiers.py` or dedicated expand report).

**Status:** Waiting on user review of `qc/expand_pol_flips.csv`.
