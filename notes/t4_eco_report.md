# T4 ecological (PI-reviewed classifier + verifier metrics)

- Ecological answers in scored cohort: **438**
- PI-labeled rows (dev 100 + eco2 72): **172** (168 present in classified file)
- Classifier **fit on dev labels** (`eco_PI_ok_labels.csv`, collapsed exact): **1.000** (n=99) — tuning set, not held-out accuracy.
- **Held-out** classifier acceptance (`eco2_PI_ok_labels.csv`, PI_ok=Y): **0.625** (45/72 = 45/72 when fully labeled).
- Held-out pred vs gold category (strict): **0.826** (n=69 scored).
- False-alarm cohort: PI-labeled rows with final category `exact_surface_variant, exact_verbatim, frequency_rephrased`, excluding D0122/deepseek and D0077/command_r; **n=139**

## (a) Category distribution (PI-labeled rows only; final = human override)

| category | n |
|---|---:|
| exact_verbatim | 89 |
| omitted | 27 |
| exact_surface_variant | 26 |
| frequency_rephrased | 25 |
| changed_value | 1 |

## (b) FAIL rate on correct answers (PI-labeled cohort; bootstrap 95% CI)

Among human-labeled **correct** answers (`exact_verbatim`, `exact_surface_variant`, `frequency_rephrased`), fraction of verifier FAIL.

### v1c_medscore
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.077 | [0.000, 0.192] |
| exact_verbatim | 89 | 0.022 | [0.000, 0.056] |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |

### v6_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 26 | 0.231 | [0.077, 0.423] |
| exact_verbatim | 89 | 0.258 | [0.169, 0.348] |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |

### v1b_medscore (partial/missing scores)
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 0 | — | — |
| exact_verbatim | 0 | — | — |
| frequency_rephrased | 0 | — | — |

### v5_ragas_nli
| category | n | FAIL rate | 95% CI |
|---|---:|---:|---|
| exact_surface_variant | 2 | 0.500 | [0.000, 1.000] |
| exact_verbatim | 12 | 0.333 | [0.083, 0.583] |
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

## Cohort error rates (full scored ecological set)

- **Real dose-error rate** (final `changed_value` after PI override): **1/438 = 0.0023** in current cohort (**1/444** in the original ecological run; only **D0162__eco / command_r**).
- **Omission / target-mismatch rate** (final `omitted`): **71/438 = 0.1621**.
- Classifier raw `changed_value` (before PI override on unlabeled rows): **2**.

Classifier rules: `notes/t4_eco_classifier_rules.md`.

