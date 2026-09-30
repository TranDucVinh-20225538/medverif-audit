<!-- LEGACY — not for paper. Use results/tables/card_main.md and qvc/paper_numbers.json from scripts/compute_paper_numbers.py. -->

# Full V1–V4 analysis

Status: **partial** (V1/V4 still scoring)

Filters: `valid=true`; conditional rates use C0 PASS; **POL E1/E2** use flip PI_ok=Y (**26** bases); **INV** uses `qc/inv_manual_review.csv` PI_ok=Y (DOSE unit always eligible); INV-unit **natural=Y** subset from `qc/unit_naturalness.csv`.

V1 agreement (50×2): **1.0** (v1_medscore).

## Parse-fail rate

| Verifier | PARSE_FAIL | n |
| --- | --- | --- |
| v1_medscore | 0/1047 | 1047 |
| v2a_minicheck | 0/1206 | 1206 |
| v3_alignscore | 0/1206 | 1206 |
| v4_ragas_nli | 10/1045 | 1045 |

## Cohen's κ (verifier × verifier, parsed PASS/FAIL/PARSE_FAIL)

|  | v1_medscore | v2a_minicheck | v3_alignscore | v4_ragas_nli |
| --- | --- | --- | --- | --- |
| v1_medscore | 1.000 | 0.761 | 0.814 | 0.879 |
| v2a_minicheck | 0.761 | 1.000 | 0.840 | 0.774 |
| v3_alignscore | 0.814 | 0.840 | 1.000 | 0.826 |
| v4_ragas_nli | 0.879 | 0.774 | 0.826 | 1.000 |

## Headline pass @ 0.5 (conditional on C0 PASS)

**DOSE (main analysis set)** — all valid main/threshold DOSE instances.

| Verifier | C0 | E1-claim | INV-unit (all valid) | INV-unit (natural=Y) |
| --- | --- | --- | --- | --- |
| v1_medscore | 117/117 | 2/234 | 46/68 | 14/22 |
| v2a_minicheck | 140/140 | 11/280 | 8/66 | 2/22 |
| v3_alignscore | 139/139 | 10/278 | 19/65 | 4/21 |
| v4_ragas_nli | 116/116 | 1/232 | 57/65 | 17/20 |

**POLARITY (human-verified flips, n=26)** — E1/E2 rows only for `qc/e1_pol_review.csv` PI_ok=Y; C0/INV on other POL bases may still appear in C0-only slices.

| Verifier | C0 (all valid POL main) | E1-claim (flip_ok Y only) | INV (PI_ok=Y) |
| --- | --- | --- | --- |
| v1_medscore | 45/45 | 0/26 | 33/34 |
| v2a_minicheck | 43/43 | 0/12 | 33/34 |
| v3_alignscore | 46/46 | 0/12 | 34/34 |
| v4_ragas_nli | 46/46 | 1/25 | 34/34 |

## Pending

Re-run after `v1_medscore` and `v4_ragas_nli` each cover all valid main+threshold instances.

