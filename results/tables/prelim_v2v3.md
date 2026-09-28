# Preliminary V2 / V3 (cpu_early)

Instances: `data/v3/instances_cpu_early.jsonl` (1294 rows).
Scores (first tranche): `results/raw/v2a_minicheck.jsonl`, `v3_alignscore.jsonl` (1216 instance_ids; DOSE unit INV **68/68** scored).

Default binarization: **score > 0.5 → PASS** (repo default for V2a and V3).
Conditional slices: only bases whose **C0** verdict is PASS for that verifier.

## Interpretation: ranking failure, not calibration

AUROC(**C0** vs **INV-unit**) ≈ **0.97** — verifiers assign *much* lower scores to unit-equivalent claims than to the original C0 wording (they treat INV like a large claim change, not an invariant rewrite).

Threshold tuning does **not** rescue invariance without sacrificing E1 sensitivity: the best-F1 τ on C0+E1 is **above** 0.5, and raising τ **lowers** INV-unit pass while E1 fail rate is already high at default. There is no τ that simultaneously passes most INV-unit rows and fails most E1 rows — a **ranking** problem, not a fixed-offset calibration problem.

## INV-claim pass (68 scored DOSE unit rows; 78 POL rephrase pending node30)

| Verifier | INV-unit (all) | INV-unit (C0-cond) | INV-polarity scored |
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

Positive class: **C0** scores; negative: **INV-unit** scores (C0-conditional bases). Ideal invariance: AUROC ≈ **0.5** (no separation). Observed ≈ **0.97** → strong erroneous separation.

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

## Score drop from C0 (DOSE, paired by base, C0-conditional)

Drop = score(C0) − score(condition). Bootstrap **median** drop across bases (1000 resamples, seed 42).

| Verifier | INV-unit median drop [CI] | E1-claim x2 | E1-claim x10 |
| --- | --- | --- | --- |
| v2a_minicheck | 0.8522 [0.8089, 0.8722] | 0.9134 [0.9054, 0.9218] | 0.9113 [0.9003, 0.9259] |
| v3_alignscore | 0.7753 [0.6164, 0.8537] | 0.9732 [0.9625, 0.9787] | 0.9685 [0.9565, 0.9754] |

**Headline (median score drop from C0):** rewriting a dose in equivalent units (e.g. 500 mg → 0.5 g) costs **comparable** verifier score to a **2× dose error** — e.g. v2a_minicheck: median drop INV-unit 0.852 vs E1 x2 0.913; V3 is closer but same pattern.

## Threshold analysis

### Best F1 on C0 + E1 (C0-conditional DOSE)

Gold: C0 → PASS; E1-evid / E1-claim → FAIL. Higher τ **reduces** INV pass — no calibration fix.

| Verifier | Best-F1 τ | F1 | INV-unit pass @ τ | INV-unit pass @ 0.5 |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.7306 | 0.9077 | 5/66 | 8/66 |
| v3_alignscore | 0.7612 | 0.9282 | 11/65 | 19/65 |

### max_τ min(INV-unit pass, E1 fail) — no joint operating point

τ ∈ [0, 1] step 0.01; DOSE; C0-conditional. E1 = E1-evid + E1-claim.

| Verifier | Best τ | min(pass INV, fail E1) | INV pass @ τ | E1 fail @ τ |
| --- | --- | --- | --- | --- |
| v2a_minicheck | 0.07 | 0.583 | 60.6% | 58.3% |
| v3_alignscore | 0.03 | 0.778 | 78.5% | 77.8% |

At the best joint τ, **min(INV pass, E1 fail)** stays far below what we would need for a usable verifier — consistent with a ranking failure, not a single wrong threshold.

