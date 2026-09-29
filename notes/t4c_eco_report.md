# T4c ecological (sentence-level claim; PI-labeled correct answers)

- Instances: **139** (`data/t4/eco_instances_t4c.jsonl`)
- Claim = rule-based sentence(s) with target dose (+ next-sentence frequency if needed); evidence unchanged.

## FAIL rate on correct answers (bootstrap 95% CI)

### v1c_medscore
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.115 | [0.000, 0.231] |
| exact_verbatim | 89 | 0.011 | [0.000, 0.034] |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |

### v6_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.192 | [0.038, 0.346] |
| exact_verbatim | 89 | 0.213 | [0.135, 0.303] |
| frequency_rephrased | 24 | 0.083 | [0.000, 0.208] |

### v1b_medscore
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.115 | [0.000, 0.231] |
| exact_verbatim | 89 | 0.011 | [0.000, 0.034] |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |

### v5_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.231 | [0.077, 0.423] |
| exact_verbatim | 89 | 0.236 | [0.146, 0.326] |
| frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |

### v4_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.154 | [0.038, 0.308] |
| exact_verbatim | 89 | 0.124 | [0.067, 0.191] |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |

### v1_medscore (no scores yet)

### v2a_minicheck (no scores yet)

### v3_alignscore (no scores yet)

### t6a_minicheck_roberta (no scores yet)

### t6a_minicheck_deberta (no scores yet)

### t6a_alignscore_base (no scores yet)

### t6a_summac_zs (no scores yet)

### t6a_summac_conv (no scores yet)

### t6a_hhem (no scores yet)

### t6a_granite_guardian (no scores yet)

