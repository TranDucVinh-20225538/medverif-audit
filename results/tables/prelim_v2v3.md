<!-- LEGACY — not for paper. Use results/tables/card_main.md and qvc/paper_numbers.json from scripts/compute_paper_numbers.py. -->

# Preliminary V2 / V3 (cpu_early)

Instances: `data/v3/instances_cpu_early.jsonl` (1249 rows).
Scores (first tranche): `results/raw/v2a_minicheck.jsonl`, `v3_alignscore.jsonl` (1216 instance_ids; DOSE unit INV **68/68** scored).

Default binarization: **score > 0.5 → PASS** (repo default for V2a and V3).
Conditional slices: only bases whose **C0** verdict is PASS for that verifier.

## Interpretation: ranking failure, not calibration

AUROC(**C0** vs **INV-unit**) ≈ **0.97** — verifiers assign *much* lower scores to unit-equivalent claims than to the original C0 wording (they treat INV like a large claim change, not an invariant rewrite).

Threshold tuning does **not** rescue invariance without sacrificing E1 sensitivity: the best-F1 τ on C0+E1 is **above** 0.5, and raising τ **lowers** INV-unit pass while E1 fail rate is already high at default. There is no τ that simultaneously passes most INV-unit rows and fails most E1 rows — a **ranking** problem, not a fixed-offset calibration problem.

## INV-claim pass (68 scored DOSE unit rows; 78 POL rephrase pending node30)

| Verifier | INV-unit (all) | INV-unit (C0-cond) | INV-polarity scored |
| --- | --- | --- | --- |
| v2a_minicheck | 8/66 | 8/64 | 33/34 |
| v3_alignscore | 18/66 | 18/63 | 34/34 |

## Pass @ default threshold (0.5), conditional on C0 PASS

| Verifier | Condition | PASS | Median score |
| --- | --- | --- | --- |
| v2a_minicheck | C0 | 180/180 | 0.9678 |
| v2a_minicheck | E1-evid | 34/277 | 0.0771 |
| v2a_minicheck | E1-claim | 11/277 | 0.0411 |
| v2a_minicheck | E2 | 282/286 | 0.9673 |
| v2a_minicheck | INV-unit | 8/64 | 0.0961 |
| v2a_minicheck | INV-polarity | 31/31 | 0.9758 |
| v3_alignscore | C0 | 182/182 | 0.9815 |
| v3_alignscore | E1-evid | 24/275 | 0.0048 |
| v3_alignscore | E1-claim | 9/275 | 0.0014 |
| v3_alignscore | E2 | 281/284 | 0.9836 |
| v3_alignscore | INV-unit | 18/63 | 0.1770 |
| v3_alignscore | INV-polarity | 34/34 | 0.9917 |

## AUROC

### C0 vs INV-unit (DOSE `unit_conversion`)

Positive class: **C0** scores; negative: **INV-unit** scores (C0-conditional bases). Ideal invariance: AUROC ≈ **0.5** (no separation). Observed ≈ **0.97** → strong  erroneous separation.

| Verifier | AUROC | 95% CI | n(C0) | n(INV-unit) |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.9741 | [0.9391, 0.9958] | 180 | 64 |
| v3_alignscore | 0.9704 | [0.9447, 0.9896] | 182 | 63 |

### INV-unit vs E1-claim (DOSE; detects dose change vs invariance)

Positive: **INV-unit**; negative: **E1-claim** (mean of x2/x10 per base when both exist). Bootstrap: 1000 resamples, seed 42.

| Verifier | AUROC | 95% CI | Paired bases |
| --- | --- | --- | --- |
| v2a_minicheck | 0.6777 | [0.5983, 0.7534] | 62 |
| v3_alignscore | 0.8320 | [0.7675, 0.8969] | 61 |

## Score drop from C0 (DOSE, paired by base, C0-conditional)

Drop = score(C0) − score(condition). Bootstrap **median** drop across bases (1000 resamples, seed 42).

| Verifier | INV-unit median drop [CI] | E1-claim x2 | E1-claim x10 |
| --- | --- | --- | --- |
| v2a_minicheck | 0.8522 [0.7982, 0.8735] | 0.9134 [0.9035, 0.9218] | 0.9112 [0.8990, 0.9261] |
| v3_alignscore | 0.7771 [0.6870, 0.8537] | 0.9746 [0.9625, 0.9799] | 0.9696 [0.9583, 0.9771] |

**Headline (median score drop from C0):** rewriting a dose in equivalent units (e.g. 500 mg → 0.5 g) costs **comparable** verifier score to a **2× dose error** — e.g. v2a_minicheck: median drop INV-unit 0.852 vs E1 x2 0.913; V3 is closer but same pattern.

## Threshold analysis

### Best F1 on C0 + E1 (C0-conditional DOSE)

Gold: C0 → PASS; E1-evid / E1-claim → FAIL. Higher τ **reduces** INV pass — no calibration fix.

| Verifier | Best-F1 τ | F1 | INV-unit pass @ τ | INV-unit pass @ 0.5 |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.7306 | 0.9054 | 5/64 | 8/64 |
| v3_alignscore | 0.6470 | 0.9286 | 13/63 | 18/63 |

### max_τ min(INV-unit pass, E1 fail) — no joint operating point

τ ∈ [0, 1] step 0.01; DOSE; C0-conditional. E1 = E1-evid + E1-claim.

| Verifier | Best τ | min(pass INV, fail E1) | INV pass @ τ | E1 fail @ τ |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.07 | 0.572 | 60.9% | 57.2% |
| v3_alignscore | 0.03 | 0.778 | 77.8% | 78.1% |

At the best joint τ, **min(INV pass, E1 fail)** stays far below what we would need for a usable verifier — consistent with a ranking failure, not a single wrong threshold.

