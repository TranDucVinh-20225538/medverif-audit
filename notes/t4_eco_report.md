# T4 ecological (PI-reviewed classifier + verifier metrics)

- Answers classified: **444**
- Classifier **fit on dev labels** (`eco_PI_ok_labels.csv`, collapsed exact): **1.000** (n=100) — tuning set, not held-out accuracy.
- **Held-out** classifier accuracy (`eco_review2.csv` rows you labeled, excluding dev 100): **nan** (n=0 labeled / 72 on sheet).
- False-alarm cohort: correct `exact_surface_variant, exact_verbatim, frequency_rephrased`, excluding D0122/deepseek (empty) and D0077/command_r (wrong context); **n=365**

## (a) Category distribution (final = PI override on labeled rows)

| category | n |
|---|---:|
| exact_verbatim | 320 |
| omitted | 58 |
| exact_surface_variant | 26 |
| changed_value | 20 |
| frequency_rephrased | 20 |

### Per answerer

**command_r**: exact_verbatim=101, exact_surface_variant=14, changed_value=14, omitted=12, frequency_rephrased=7
**deepseek_chat**: exact_verbatim=106, omitted=27, exact_surface_variant=6, frequency_rephrased=5, changed_value=4
**gemma3_27b**: exact_verbatim=113, omitted=19, frequency_rephrased=8, exact_surface_variant=6, changed_value=2

## (b) FAIL rate on correct answers (bootstrap 95% CI)

Hypothesis: specialized checkers false-alarm more on `exact_surface_variant` than `exact_verbatim`; LLM judges less so.

### v1c_medscore
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.077 | [0.000, 0.192] |
| exact_verbatim | 320 | 0.016 | [0.003, 0.031] |
| frequency_rephrased | 19 | 0.000 | [0.000, 0.000] |

### v6_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 20 | 0.200 | [0.050, 0.400] |
| exact_verbatim | 248 | 0.214 | [0.165, 0.266] |
| frequency_rephrased | 13 | 0.000 | [0.000, 0.000] |

### v1b_medscore (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v5_ragas_nli (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v4_ragas_nli (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v1_medscore (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v2a_minicheck (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v3_alignscore (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_minicheck_roberta (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_minicheck_deberta (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_alignscore_base (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_summac_zs (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_summac_conv (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_hhem (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### t6a_granite_guardian (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

## (c) Detection on human-verified `changed_value` answers

Cohort: `eco_category_final=changed_value`, same exclusions as (b); **n=20**. FAIL rate = real-world sensitivity (verifier flags wrong dose).

| verifier | n scored | FAIL rate | 95% CI |
|---|---:|---:|---|
| v1c_medscore | 20 | 0.050 | [0.000, 0.150] |
| v6_ragas_nli | 17 | 0.353 | [0.118, 0.588] |
| v1b_medscore | 0 | — | — |
| v5_ragas_nli | 0 | — | — |
| v4_ragas_nli | 0 | — | — |
| v1_medscore | 0 | — | — |
| v2a_minicheck | 0 | — | — |
| v3_alignscore | 0 | — | — |
| t6a_minicheck_roberta | 0 | — | — |
| t6a_minicheck_deberta | 0 | — | — |
| t6a_alignscore_base | 0 | — | — |
| t6a_summac_zs | 0 | — | — |
| t6a_summac_conv | 0 | — | — |
| t6a_hhem | 0 | — | — |
| t6a_granite_guardian | 0 | — | — |

