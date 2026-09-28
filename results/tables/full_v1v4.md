# Full V1–V4 analysis

Status: **partial** (V1/V4 still scoring)

Filters: `valid=true`; conditional rates use C0 PASS; **POL E1/E2** use flip PI_ok=Y (**26** bases); **INV** uses `qc/inv_manual_review.csv` PI_ok=Y (DOSE unit always eligible); INV-unit **natural=Y** subset from `qc/unit_naturalness.csv`.

V1 agreement (50×2): **1.0** (v1_medscore).

## Parse-fail rate

| Verifier | PARSE_FAIL | n |
| --- | --- | --- |
| v1_medscore | 0/1006 | 1006 |
| v2a_minicheck | 0/1220 | 1220 |
| v3_alignscore | 0/1220 | 1220 |
| v4_ragas_nli | 5/407 | 407 |

## Cohen's κ (verifier × verifier, parsed PASS/FAIL/PARSE_FAIL)

|  | v1_medscore | v2a_minicheck | v3_alignscore | v4_ragas_nli |
| --- | --- | --- | --- | --- |
| v1_medscore | 1.000 | 0.765 | 0.816 | 0.874 |
| v2a_minicheck | 0.765 | 1.000 | 0.842 | 0.752 |
| v3_alignscore | 0.816 | 0.842 | 1.000 | 0.840 |
| v4_ragas_nli | 0.874 | 0.752 | 0.840 | 1.000 |

## Headline pass @ 0.5 (conditional on C0 PASS)

**DOSE (main analysis set)** — all valid main/threshold DOSE instances.

| Verifier | C0 | E1-claim | INV-unit (all valid) | INV-unit (natural=Y) |
| --- | --- | --- | --- | --- |
| v1_medscore | 119/119 | 2/238 | 38/57 | 14/22 |
| v2a_minicheck | 142/142 | 11/284 | 8/66 | 2/22 |
| v3_alignscore | 141/141 | 10/282 | 19/65 | 4/21 |
| v4_ragas_nli | 49/49 | 0/97 | 21/25 | 9/11 |

**POLARITY (human-verified flips, n=26)** — E1/E2 rows only for `qc/e1_pol_review.csv` PI_ok=Y; C0/INV on other POL bases may still appear in C0-only slices.

| Verifier | C0 (all valid POL main) | E1-claim (flip_ok Y only) | INV (PI_ok=Y) |
| --- | --- | --- | --- |
| v1_medscore | 45/45 | 0/12 | 33/34 |
| v2a_minicheck | 43/43 | 0/12 | 33/34 |
| v3_alignscore | 46/46 | 0/12 | 34/34 |
| v4_ragas_nli | — | — | 34/34 |

## Pending

Re-run after `v1_medscore` and `v4_ragas_nli` each cover all valid main+threshold instances.

