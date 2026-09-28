# Preliminary V2 / V3 (cpu_early)

Instances: `data/v3/instances_cpu_early.jsonl` (1216 rows).
Scores: `results/raw/v2a_minicheck.jsonl`, `v3_alignscore.jsonl`.

Default binarization: **score > 0.5 → PASS** (repo default for V2a and V3).
Conditional slices: only bases whose **C0** verdict is PASS for that verifier.

## INV-claim pass (68 scored rows = DOSE unit_conversion only)

| Verifier | All INV-unit | C0-conditional INV-unit | INV-polarity (cpu_early) |
| --- | --- | --- | --- |
| v2a_minicheck | 8/68 | 8/66 | 0/0 |
| v3_alignscore | 19/68 | 19/65 | 0/0 |

## Pass @ default threshold (0.5), conditional on C0 PASS

| Verifier | Condition | PASS | Median score |
| --- | --- | --- | --- |
| v2a_minicheck | C0 | 185/185 | 0.9679 |
| v2a_minicheck | E1-evid | 34/298 | 0.0738 |
| v2a_minicheck | E1-claim | 11/298 | 0.0409 |
| v2a_minicheck | E2 | 293/298 | 0.9672 |
| v2a_minicheck | INV-unit | 8/66 | 0.0961 |
| v2a_minicheck | INV-polarity | — | — |
| v3_alignscore | C0 | 187/187 | 0.9814 |
| v3_alignscore | E1-evid | 25/296 | 0.0053 |
| v3_alignscore | E1-claim | 10/296 | 0.0015 |
| v3_alignscore | E2 | 293/296 | 0.9832 |
| v3_alignscore | INV-unit | 19/65 | 0.2055 |
| v3_alignscore | INV-polarity | — | — |

## AUROC

### C0 vs INV-unit (DOSE `unit_conversion`)

Positive class: **C0** scores; negative: **INV-unit** scores (C0-conditional bases). An ideal invariance-aware verifier should not rank equivalent claims differently → AUROC ≈ **0.5**.

| Verifier | AUROC | 95% CI | n(C0) | n(INV-unit) |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.9749 | [0.9407, 0.9951] | 185 | 66 |
| v3_alignscore | 0.9647 | [0.9360, 0.9872] | 187 | 65 |

### INV-unit vs E1-claim (DOSE; detects dose change vs invariance)

Positive: **INV-unit**; negative: **E1-claim** (mean of x2/x10 per base when both exist). Bootstrap: 1000 resamples, seed 42.

| Verifier | AUROC | 95% CI | Paired bases |
| --- | --- | --- | --- |
| v2a_minicheck | 0.6816 | [0.6088, 0.7583] | 66 |
| v3_alignscore | 0.8317 | [0.7768, 0.8890] | 65 |

## Threshold sweep (C0 + E1-evid + E1-claim)

Gold: C0 → PASS; E1-evid / E1-claim → FAIL. Search thresholds on observed scores (plus 0.00–1.00 grid) for best **F1**, then report INV-unit pass rate at that threshold (calibration vs ranking for invariance).

| Verifier | Best-F1 τ | F1 | INV-unit pass @ τ (C0-cond) | INV-unit pass @ 0.5 |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.7306 | 0.9077 | 5/66 | 8/66 |
| v3_alignscore | 0.7612 | 0.9282 | 11/65 | 19/65 |
