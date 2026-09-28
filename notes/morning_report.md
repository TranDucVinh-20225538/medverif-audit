# Morning report (2026-09-29 03:15 +07)

## Task status

| Task | Status | Notes |
|---|---|---|
| T7 E1-unit OR | see tmux/logs | `notes/t7_e1_unit_report.md` |
| T4 eco OR | see tmux/logs | `notes/t4_eco_report.md` |
| V4 main resume | see logs | dedupe: `notes/dedupe_v4_ragas_nli.json` |
| T6-B full | see tmux/logs | |
| Expand OR score | see logs | v1b/v5 T2: `results/raw/t2_full/` |
| T9 prep | inputs n=536 | **node30 only** `jobs/run_t9_node30.sh` |
| T10 prep | prep pushed 3066ccc — leaderboard HF dataset 401; qc/t10_sample.csv padded 30 rows | HHEM on node30; open HHEM-2.1 framing |
| T8 synthetic | **DEPRECATED** | do not score |
| T8b | **blocked** | `qc/t8_mismatch_check.csv` |

**OpenRouter credit remaining:** 37.01131264

## T7 (per verifier)

| verifier | E1-unit fail | E1 x2/x10 fail | INV-unit pass |
|---|---:|---:|---:|
| t6a_alignscore_base | None (n=0) | None (n=0) | None (n=0) |
| t6a_granite_guardian | None (n=0) | None (n=0) | None (n=0) |
| t6a_hhem | None (n=0) | None (n=0) | None (n=0) |
| t6a_minicheck_deberta | None (n=0) | None (n=0) | None (n=0) |
| t6a_minicheck_roberta | None (n=0) | None (n=0) | None (n=0) |
| t6a_summac_conv | None (n=0) | None (n=0) | None (n=0) |
| t6a_summac_zs | None (n=0) | None (n=0) | None (n=0) |
| v1_medscore | 0.8043478260869565 (n=230) | 0.9907407407407407 (n=432) | 0.7096774193548387 (n=124) |
| v1b_medscore | 0.5695652173913044 (n=230) | None (n=0) | None (n=0) |
| v2a_minicheck | None (n=0) | None (n=0) | None (n=0) |
| v2b_bespoke | None (n=0) | None (n=0) | None (n=0) |
| v3_alignscore | None (n=0) | None (n=0) | None (n=0) |
| v4_ragas_nli | 0.8956521739130435 (n=230) | 0.9953703703703703 (n=432) | 0.8613861386138614 (n=101) |
| v5_ragas_nli | 0.7678571428571429 (n=56) | None (n=0) | None (n=0) |
| v6_ragas_nli | None (n=0) | None (n=0) | None (n=0) |

## T4 eco false alarms (human-labeled correct answers)

_See `notes/t4_eco_report.md`_

## V4 row counts

```json
{
  "instances_cpu_main": 1085,
  "raw_lines": 1037,
  "unique_scored": 1037,
  "pending_vs_main": 48,
  "dedupe": {}
}
```

## Expand scoring coverage

```json
{
  "score_pending_manifest": {
    "scored_ids_in_raw_v2v3": 1403,
    "pending_cpu_early": 62,
    "pending_g_inv_paraphrase": 0,
    "pending_node30_total": 2436,
    "pending_t3_inv_pi_ok": 0,
    "pending_expand_set": 2374,
    "pending_node30_includes_expand": true,
    "paths": {
      "cpu_early_pending": "data/v3/instances_score_pending_cpu_early.jsonl",
      "g_inv_pending": "data/v3/instances_score_pending_g_inv.jsonl",
      "t3_inv_pending": "data/v3/instances_score_pending_t3_inv.jsonl",
      "node30_combined": "data/v3/instances_score_pending_node30.jsonl",
      "expand_pending": "data/expand/instances_score_pending.jsonl"
    },
    "node30_cmd_hint": "Score OUT_NODE30 with scripts/run_node30_v2v3.py (or cpu_early scorer) appending to results/raw/v2a_minicheck.jsonl and v3_alignscore.jsonl."
  },
  "expand_pending_n": 2374
}
```

## M1 before/after (4 verifiers)

Full table: `results/tables/m1_before_after.md`

## T3

- INV families instances: **397**; t3_t2 v1b lines: **425**

## QC files awaiting PI_ok review

- `qc/eco_review2.csv` (72 rows w/ empty PI_ok)
- `qc/eco_sample.csv` (100 rows w/ empty PI_ok)
- `qc/expand_dose_sample.csv` (80 rows w/ empty PI_ok)
- `qc/expand_pol_flips.csv` (250 rows w/ empty PI_ok)
- `qc/expand_unit_natural.csv` (153 rows w/ empty PI_ok)
- `qc/inv_families_sample.csv` (99 rows w/ empty PI_ok)
- `qc/inv_manual_review.csv` (56 rows w/ empty PI_ok)
- `qc/inv_manual_review_PI_ok_labels.csv` (56 rows w/ empty PI_ok)
- `qc/t10_sample.csv` (30 rows w/ empty PI_ok)
- `qc/t7_e1_unit_sample.csv` (30 rows w/ empty PI_ok)
- `qc/t8_aggrefact_inv_sample.csv` (30 rows w/ empty PI_ok)
- `qc/t8_mismatch_check.csv` (40 rows w/ empty PI_ok)
