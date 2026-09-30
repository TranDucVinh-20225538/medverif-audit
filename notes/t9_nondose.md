# T9 — NeMo Guardrails AlignScore rail after non-dose exclusion

NeMo 0.24.1, block if AlignScore < 0.5. Non-dose bases excluded (`src/non_dose_targets.py`, 15 bases). CI: 95% cluster bootstrap by base (1000, seed 42). Env: vllm (NeMo AlignScore HTTP server).

| rail | cell | blocked / total | rate [95% CI] | excluded non-dose rows |
|---|---|---:|---|---:|
| AlignScore-base | unit error ×1000 (claim+evid) | 44/216 | 20.4% [13.4, 27.8] | 14 |
| AlignScore-base | unit error ×1000 claim | 20/108 | 18.5% [11.1, 25.9] | 7 |
| AlignScore-base | unit error ×1000 evid | 24/108 | 22.2% [14.8, 30.6] | 7 |
| AlignScore-base | value error ×2 | 108/110 | 98.2% [95.5, 100.0] | 9 |
| AlignScore-large | unit error ×1000 (claim+evid) | 107/216 | 49.5% [41.2, 58.3] | 14 |
| AlignScore-large | unit error ×1000 claim | 60/108 | 55.6% [46.3, 64.8] | 7 |
| AlignScore-large | unit error ×1000 evid | 47/108 | 43.5% [34.3, 52.8] | 7 |
| AlignScore-large | value error ×2 | 108/110 | 98.2% [95.5, 100.0] | 9 |
