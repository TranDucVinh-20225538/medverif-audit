# Independent audit gap resolution (`independent-audit-card.md`)

## 1. Main OpenRouter verifiers (V1b, V5, V1c, T6-B ×4)

| Verifier | Real on disk? | In prior zip? | Canonical path (main_dose) |
|----------|---------------|---------------|----------------------------|
| v1b_medscore | **Yes** — `results/raw/t2_full/v1b_medscore.jsonl` (533 rows) | **No** (only `results/raw/` root globs) | `results/raw/t2_full/v1b_medscore.jsonl` |
| v5_ragas_nli | **Yes** — `results/raw/t2_full/v5_ragas_nli.jsonl` | **No** | `results/raw/t2_full/v5_ragas_nli.jsonl` |
| v1c_medscore | **Yes** — `results/raw/t6b/full/v1c_medscore.jsonl` (1657 rows) | **No** | `results/raw/t6b/full/v1c_medscore.jsonl` |
| v6_ragas_gpt4o_mini | **Yes** — `t6b/full/` (647 rows) | **No** | `results/raw/t6b/full/v6_ragas_gpt4o_mini.jsonl` |
| v6_ragas_haiku45 | **Yes** — `t6b/full/` | **No** | same tree |
| v6_ragas_llama31_8b | **Yes** — `t6b/full/` | **No** | same tree |
| v6_ragas_mistral_small32 | **Yes** — `t6b/full/` | **No** | same tree |

**INV-unit (67 conversions, main):** all **67/67** instance ids present in the T2/T6b files above — draft **95–98% QI** is reproducible from those paths (not from missing `results/raw/{verifier}.jsonl`).

**C0 + INV-unit + E1 (main):** **475/722** instance ids scored in `t2_full` / `t6b/full` per verifier (cohort slice, not full 854 main DOSE). Remaining **247** ids were never in those cohort packs — **not rescored** in this pass (would exceed ≤$4); say if you want a targeted OpenRouter backfill list.

Root-level `results/raw/v1b_medscore.jsonl` etc. **do not exist** (real gap for tools that only look at root).

## 2. Unit naturalness (`qc/unit_naturalness.csv`)

- **58 rows, `natural` column empty on all 58** — no human Y/N labels committed for main unit audit sample.
- **`effective_unit_natural_y()`** (`analysis/review_filters.py`) reads **only** `qc/unit_naturalness.csv` → `natural`; else **rule** (`rule_natural_unit_conversion_label`).
- **Related but not wired:** `qc/unit2_PI_ok_labels.csv` (40 rows, **PI_ok** Y/N — inversion review, not naturalness); `qc/expand_unit_natural.csv` (`suggested_natural`, **PI_ok** empty). **`pi_merge_report.json`** notes 14Y/26N sample not merged into `unit_naturalness.csv`.

**Action:** you label `natural` on the 58 rows (or we wire a merge later).

## 3. Eleven main INV-unit rows missing from `results/raw` (v1, v2a, v3)

Instance ids (same for all three):

`D0001, D0009, D0018, D0031, D0042, D0044, D0053, D0061, D0124, D0141, D0176` × `__INV-claim__unit_conversion`.

Present in **`results/raw_m1/`** (M1-after rescore), **not** in **`results/raw/`** (before). Backfill job: `jobs/run_main_inv11_backfill.sh` → appends to root encoders.

## 4. Llama-70B main (`v4_ragas_nli.llama.jsonl`)

- **43** rows with `PARSE_FAIL` under `_parsed()` — rescore list in `data/v3/v4_llama_unparsed_rescore.jsonl`.
- **16** duplicate `instance_id`s (D0005/D0007/D0008 conditions) — **dedupe** via `scripts/dedupe_score_jsonl.py` (backup first).

## 5. Node30 small checkers — main E1-evid

**221** main `E1-evid` rows: **v2a/v3** covered on HPC and node30; **t6_*** (MiniCheck, AlignScore-base, SummaC, HHEM, Granite, Bespoke) on node30 root **561-row cpu_early slice** has **0/221** E1-evid. Same for HPC root t6 bespoke (533 rows, 0 E1-evid).

**Action:** document only; score **221 E1-evid** on HPC once 8 local verifiers are deployed (not node30).

## 6. Zip / canonical

- Zip now includes **`results/raw/t2_full/`**, **`results/raw/t6b/full/`**, **`release/canonical_sources.tsv`** (multi-path main_dose for OpenRouter cohort files).
