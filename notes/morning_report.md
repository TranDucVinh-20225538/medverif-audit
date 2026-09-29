# Morning report (2026-09-29 08:03 +07)

## Task status

| Task | Status | Notes |
|---|---|---|
| T7 E1-unit OR | done 2026-09-29T04:30:51+07:00 | `notes/t7_e1_unit_report.md` |
| T4 eco OR | no session 2026-09-29T04:30:51+07:00 | `notes/t4_eco_report.md` |
| V4 main resume | no session 2026-09-29T04:30:51+07:00 | dedupe: `notes/dedupe_v4_ragas_nli.json` |
| T6-B full | no session 2026-09-29T04:30:51+07:00 | |
| Expand OR score | done 2026-09-29T08:03:26+07:00 | v1b/v5 T2: `results/raw/t2_full/` |
| T9 prep | inputs n=536 | **node30 only** `jobs/run_t9_node30.sh` |
| T10 prep | prep pushed 2026-09-29T08:03:41+07:00 | HHEM on node30; open HHEM-2.1 framing |
| T8 synthetic | **DEPRECATED** | do not score |
| T8b | **blocked** | `qc/t8_mismatch_check.csv` |

**OpenRouter credit remaining:** 33.411961680000005

## T7 (per verifier)

| verifier | E1-unit fail | E1 x2/x10 fail | INV-unit pass |
|---|---:|---:|---:|
| t6a_alignscore_base | 0.23043478260869565 (n=230) | None (n=0) | None (n=0) |
| t6a_granite_guardian | 0.34347826086956523 (n=230) | None (n=0) | None (n=0) |
| t6a_hhem | 0.05652173913043478 (n=230) | None (n=0) | None (n=0) |
| t6a_minicheck_deberta | 0.8043478260869565 (n=230) | None (n=0) | None (n=0) |
| t6a_minicheck_roberta | 0.34782608695652173 (n=230) | None (n=0) | None (n=0) |
| t6a_summac_conv | 0.691304347826087 (n=230) | None (n=0) | None (n=0) |
| t6a_summac_zs | 0.3695652173913043 (n=230) | None (n=0) | None (n=0) |
| v1_medscore | 0.8043478260869565 (n=230) | 0.9907407407407407 (n=432) | 0.7109375 (n=128) |
| v1b_medscore | 0.5695652173913044 (n=230) | None (n=0) | None (n=0) |
| v2a_minicheck | 0.3652173913043478 (n=230) | None (n=0) | None (n=0) |
| v2b_bespoke | 0.5347826086956522 (n=230) | None (n=0) | None (n=0) |
| v3_alignscore | 0.5043478260869565 (n=230) | None (n=0) | None (n=0) |
| v4_ragas_nli | 0.8956521739130435 (n=230) | 0.9953703703703703 (n=432) | 0.8613861386138614 (n=101) |
| v5_ragas_nli | 0.8347826086956521 (n=230) | None (n=0) | None (n=0) |
| v6_ragas_nli | None (n=0) | None (n=0) | None (n=0) |

## T4 eco false alarms (human-labeled correct answers)

_See `notes/t4_eco_report.md`_

## V4 row counts

```json
{
  "instances_cpu_main": 1085,
  "raw_lines": 1085,
  "unique_scored": 1085,
  "pending_vs_main": 0,
  "dedupe": {
    "instances": "data/v3/instances_cpu_main.jsonl",
    "n_instances": 1085,
    "scores": "results/raw/v4_ragas_nli.jsonl",
    "out": "results/raw/v4_ragas_nli.jsonl",
    "input_lines": 3446,
    "duplicate_instance_id": 0,
    "unknown_instance_id": 2361,
    "stale_content_sha1": 0,
    "kept": 1085,
    "sample_duplicate_ids": [],
    "sample_stale_ids": [],
    "sample_unknown_ids": [
      "P0002__C0__none",
      "P0002__E1-evid__flip",
      "P0002__E1-claim__flip",
      "P0002__E2__flip",
      "P0002__INV-claim__rephrase",
      "P0005__C0__none",
      "P0008__C0__none",
      "P0008__INV-claim__rephrase",
      "P0010__C0__none",
      "P0010__INV-claim__rephrase"
    ]
  }
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
