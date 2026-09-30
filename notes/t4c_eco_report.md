# T4c ecological (sentence-level claim; PI-labeled correct answers)

- Instances: **139** (`data/t4/eco_instances_t4c.jsonl`)
- FAIL rate on human-labeled **correct** answers by eco category.
- **Sig** = surface_variant or frequency_rephrased FAIL rate significantly **higher** than verbatim (non-overlapping 95% CIs and/or one-sided permutation *p* < 0.05).

## Summary table (all verifiers)

| verifier | category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---:|---|:---:|
| v1c_medscore | verbatim | 89 | 0.011 | [0.000, 0.034] |  |
| v1c_medscore | surface_variant | 26 | 0.115 | [0.000, 0.231] | **Y** (p=0.033) |
| v1c_medscore | frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |
| v1b_medscore | verbatim | 89 | 0.011 | [0.000, 0.034] |  |
| v1b_medscore | surface_variant | 26 | 0.115 | [0.000, 0.231] | **Y** (p=0.033) |
| v1b_medscore | frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |
| v5_ragas_nli | verbatim | 89 | 0.236 | [0.146, 0.326] |  |
| v5_ragas_nli | surface_variant | 26 | 0.231 | [0.077, 0.423] |  |
| v5_ragas_nli | frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |
| v4_ragas_nli | verbatim | 89 | 0.022 | [0.000, 0.056] |  |
| v4_ragas_nli | surface_variant | 26 | 0.077 | [0.000, 0.192] |  |
| v4_ragas_nli | frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |
| v1_medscore | verbatim | 0 | — | — | |
| v1_medscore | surface_variant | 0 | — | — | |
| v1_medscore | frequency_rephrased | 0 | — | — | |
| v6_ragas_nli | verbatim | 89 | 0.213 | [0.135, 0.303] |  |
| v6_ragas_nli | surface_variant | 26 | 0.192 | [0.038, 0.346] |  |
| v6_ragas_nli | frequency_rephrased | 24 | 0.083 | [0.000, 0.208] |  |
| v2a_minicheck | verbatim | 89 | 0.202 | [0.124, 0.281] |  |
| v2a_minicheck | surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| v2a_minicheck | frequency_rephrased | 24 | 0.292 | [0.125, 0.500] |  |
| v3_alignscore | verbatim | 89 | 0.180 | [0.101, 0.258] |  |
| v3_alignscore | surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| v3_alignscore | frequency_rephrased | 24 | 0.167 | [0.042, 0.333] |  |
| t6a_minicheck_roberta | verbatim | 89 | 0.337 | [0.236, 0.438] |  |
| t6a_minicheck_roberta | surface_variant | 26 | 0.462 | [0.269, 0.654] |  |
| t6a_minicheck_roberta | frequency_rephrased | 24 | 0.583 | [0.375, 0.750] | **Y** (p=0.025) |
| t6a_minicheck_deberta | verbatim | 89 | 0.449 | [0.337, 0.551] |  |
| t6a_minicheck_deberta | surface_variant | 26 | 0.500 | [0.308, 0.692] |  |
| t6a_minicheck_deberta | frequency_rephrased | 24 | 0.583 | [0.375, 0.792] |  |
| t6a_alignscore_base | verbatim | 89 | 0.202 | [0.124, 0.292] |  |
| t6a_alignscore_base | surface_variant | 26 | 0.346 | [0.154, 0.538] |  |
| t6a_alignscore_base | frequency_rephrased | 24 | 0.125 | [0.000, 0.250] |  |
| t6a_summac_zs | verbatim | 89 | 0.438 | [0.326, 0.539] |  |
| t6a_summac_zs | surface_variant | 26 | 0.385 | [0.192, 0.577] |  |
| t6a_summac_zs | frequency_rephrased | 24 | 0.417 | [0.208, 0.625] |  |
| t6a_summac_conv | verbatim | 89 | 0.708 | [0.607, 0.809] |  |
| t6a_summac_conv | surface_variant | 26 | 0.692 | [0.500, 0.846] |  |
| t6a_summac_conv | frequency_rephrased | 24 | 0.833 | [0.667, 0.958] |  |
| t6a_hhem | verbatim | 89 | 0.236 | [0.157, 0.326] |  |
| t6a_hhem | surface_variant | 26 | 0.346 | [0.192, 0.538] |  |
| t6a_hhem | frequency_rephrased | 24 | 0.583 | [0.375, 0.792] | **Y** (CI, p=0.002) |
| t6a_granite_guardian | verbatim | 89 | 0.146 | [0.079, 0.225] |  |
| t6a_granite_guardian | surface_variant | 26 | 0.192 | [0.038, 0.346] |  |
| t6a_granite_guardian | frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |
| v2b_bespoke | verbatim | 89 | 0.112 | [0.056, 0.180] |  |
| v2b_bespoke | surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| v2b_bespoke | frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |

## By verifier (detail)

### v1c_medscore
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.011 | [0.000, 0.034] |  |
| surface_variant | 26 | 0.115 | [0.000, 0.231] | Y |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |

### v1b_medscore
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.011 | [0.000, 0.034] |  |
| surface_variant | 26 | 0.115 | [0.000, 0.231] | Y |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |

### v5_ragas_nli
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.236 | [0.146, 0.326] |  |
| surface_variant | 26 | 0.231 | [0.077, 0.423] |  |
| frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |

### v4_ragas_nli
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.022 | [0.000, 0.056] |  |
| surface_variant | 26 | 0.077 | [0.000, 0.192] |  |
| frequency_rephrased | 24 | 0.000 | [0.000, 0.000] |  |

### v6_ragas_nli
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.213 | [0.135, 0.303] |  |
| surface_variant | 26 | 0.192 | [0.038, 0.346] |  |
| frequency_rephrased | 24 | 0.083 | [0.000, 0.208] |  |

### v2a_minicheck
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.202 | [0.124, 0.281] |  |
| surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| frequency_rephrased | 24 | 0.292 | [0.125, 0.500] |  |

### v3_alignscore
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.180 | [0.101, 0.258] |  |
| surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| frequency_rephrased | 24 | 0.167 | [0.042, 0.333] |  |

### t6a_minicheck_roberta
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.337 | [0.236, 0.438] |  |
| surface_variant | 26 | 0.462 | [0.269, 0.654] |  |
| frequency_rephrased | 24 | 0.583 | [0.375, 0.750] | Y |

### t6a_minicheck_deberta
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.449 | [0.337, 0.551] |  |
| surface_variant | 26 | 0.500 | [0.308, 0.692] |  |
| frequency_rephrased | 24 | 0.583 | [0.375, 0.792] |  |

### t6a_alignscore_base
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.202 | [0.124, 0.292] |  |
| surface_variant | 26 | 0.346 | [0.154, 0.538] |  |
| frequency_rephrased | 24 | 0.125 | [0.000, 0.250] |  |

### t6a_summac_zs
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.438 | [0.326, 0.539] |  |
| surface_variant | 26 | 0.385 | [0.192, 0.577] |  |
| frequency_rephrased | 24 | 0.417 | [0.208, 0.625] |  |

### t6a_summac_conv
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.708 | [0.607, 0.809] |  |
| surface_variant | 26 | 0.692 | [0.500, 0.846] |  |
| frequency_rephrased | 24 | 0.833 | [0.667, 0.958] |  |

### t6a_hhem
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.236 | [0.157, 0.326] |  |
| surface_variant | 26 | 0.346 | [0.192, 0.538] |  |
| frequency_rephrased | 24 | 0.583 | [0.375, 0.792] | Y |

### t6a_granite_guardian
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.146 | [0.079, 0.225] |  |
| surface_variant | 26 | 0.192 | [0.038, 0.346] |  |
| frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |

### v2b_bespoke
| category | n | FAIL rate | 95% CI | sig vs verbatim |
|---|---:|---:|---|:---:|
| verbatim | 89 | 0.112 | [0.056, 0.180] |  |
| surface_variant | 26 | 0.115 | [0.000, 0.231] |  |
| frequency_rephrased | 24 | 0.042 | [0.000, 0.125] |  |

