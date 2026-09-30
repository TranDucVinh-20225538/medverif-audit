# M1 report — Lane B + Lane C packs

Before = scores on **original** text (`results/raw`…); after = **M1** (pre-applied T7 pack and/or `MEDVERIF_M1=1` / `raw_m1/lane_c`). Bootstrap **1000** resamples by `base_id`, seed **42**. QI = INV-claim **PASS** | C0; NS/US = E1 **FAIL** | C0.

## Lane B · m1_t7_e1_unit

- Instances (analysis keep): **214**
- M1 dose-span coverage: **418/468** (89.3%)

### Normalizer failure categories (non-ok spans)

- **per_kg_per_day**: 46 — e.g. _that glucocorticoids (e.g., prednisone, 1 mg/kg, as a single daily dose orally, or intravenously) are a reasonable first therapy for both PM_
- **range**: 4 — e.g. _.) Infliximab is given intravenously, 3–5 mg/kg body weight, and then repeated 2 weeks later, again 6 weeks later, and then at 8-week interv_

### Before → after metrics

| Verifier | QI | NS claim | NS evid | US claim | US evid |
| --- | --- | --- | --- | --- | --- |
| t6_alignscore_base | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

**t6_alignscore_base** E1-unit-evid M1 repairs: **2/107** FAIL→PASS.
- `D0016__E1-unit-evid__x1000`: 0.759965717792511
- `D0143__E1-unit-evid__x1000`: 0.8506614565849304

| t6_granite_guardian | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| t6_hhem | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| t6_minicheck_deberta | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

**t6_minicheck_deberta** E1-unit-evid M1 repairs: **19/107** FAIL→PASS.
- `D0011__E1-unit-evid__x1000`: 0.5532019138336182
- `D0013__E1-unit-evid__x1000`: 0.5370256304740906
- `D0026__E1-unit-evid__x1000`: 0.5014413595199585
- `D0036__E1-unit-evid__x1000`: 0.9463419914245605
- `D0038__E1-unit-evid__x1000`: 0.8833045363426208

| t6_minicheck_roberta | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

**t6_minicheck_roberta** E1-unit-evid M1 repairs: **1/107** FAIL→PASS.
- `D0104__E1-unit-evid__x1000`: 0.8257179856300354

| t6_summac_conv | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| t6_summac_zs | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| Mistral-Small-24B (MedScore) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| GPT-4o (MedScore) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| GPT-4o-mini (MedScore) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| MiniCheck-Flan-T5-Large | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

**MiniCheck-Flan-T5-Large** E1-unit-evid M1 repairs: **8/107** FAIL→PASS.
- `D0016__E1-unit-evid__x1000`: 0.6503533720970154
- `D0025__E1-unit-evid__x1000`: 0.9339961409568787
- `D0036__E1-unit-evid__x1000`: 0.9749954342842102
- `D0048__E1-unit-evid__x1000`: 0.9510093331336975
- `D0055__E1-unit-evid__x1000`: 0.9791982173919678

| Bespoke-MiniCheck-7B | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| AlignScore-large | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

**AlignScore-large** E1-unit-evid M1 repairs: **2/107** FAIL→PASS.
- `D0033__E1-unit-evid__x1000`: 0.5283347368240356
- `D0126__E1-unit-evid__x1000`: 0.7429755926132202

| Llama-3.3-70B (RAGAS NLI) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| v4_ragas_nli.legacy | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| Claude Sonnet 4.6 (RAGAS NLI) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| GPT-4o-mini (RAGAS) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| Claude Haiku 4.5 (RAGAS) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| Llama-3.1-8B (RAGAS) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |
| Mistral-Small-3.2-24B (RAGAS) | NA → NA | NA → NA | NA → NA | NA → NA | NA → NA |

## Lane B · m1_main_inv_e1_c0

- Instances (analysis keep): **692**
- M1 dose-span coverage: **1190/1415** (84.1%)

### Normalizer failure categories (non-ok spans)

- **per_kg_per_day**: 213 — e.g. _icoids, such as prednisone at a dose of 1 mg/kg as a single daily dose either orally or intravenously, are a reasonable first therapy for bo_
- **range**: 12 — e.g. _.) Infliximab is given intravenously, 3–5 mg/kg body weight, and then repeated 2 weeks later, again 6 weeks later, and then at 8-week interv_

### Before → after metrics

| Verifier | QI | NS claim | NS evid | US claim | US evid |
| --- | --- | --- | --- | --- | --- |
| t6_alignscore_base | NA → 0.193 [0.105,0.298] (11/57) | NA → 0.955 [0.923,0.982] (211/221) | NA → 0.946 [0.909,0.977] (209/221) | NA → NA | NA → NA |
| t6_minicheck_deberta | NA → 0.873 [0.782,0.964] (48/55) | NA → 0.981 [0.959,0.995] (209/213) | NA → 0.962 [0.930,0.990] (205/213) | NA → NA | NA → NA |
| t6_minicheck_roberta | NA → 0.927 [0.855,0.982] (51/55) | NA → 0.963 [0.936,0.986] (207/215) | NA → 0.930 [0.893,0.966] (200/215) | NA → NA | NA → NA |
| Mistral-Small-24B (MedScore) | 0.677 [0.565,0.790] (42/62) → NA | 0.995 [0.986,1.000] (221/222) → NA | 0.946 [0.910,0.978] (210/222) → NA | NA → NA | NA → NA |
| MiniCheck-Flan-T5-Large | 0.083 [0.017,0.150] (5/60) → NA | 0.958 [0.921,0.986] (206/215) → NA | 0.893 [0.843,0.940] (192/215) → NA | NA → NA | NA → NA |
| Bespoke-MiniCheck-7B | 0.774 [0.661,0.871] (48/62) → 0.803 [0.705,0.902] (49/61) | 0.974 [0.952,0.996] (229/235) → 0.983 [0.965,0.996] (231/235) | NA → 0.936 [0.899,0.970] (220/235) | NA → NA | NA → NA |
| AlignScore-large | 0.246 [0.140,0.351] (14/57) → NA | 0.981 [0.953,1.000] (207/211) → NA | 0.943 [0.905,0.976] (199/211) → NA | NA → NA | NA → NA |
| Llama-3.3-70B (RAGAS NLI) | 0.758 [0.645,0.855] (47/62) → NA | 0.970 [0.948,0.991] (228/235) → NA | 0.923 [0.885,0.958] (217/235) → NA | NA → NA | NA → NA |
| v4_ragas_nli.legacy | 0.881 [0.797,0.966] (52/59) → NA | 0.996 [0.987,1.000] (233/234) → NA | 0.966 [0.931,0.992] (226/234) → NA | NA → NA | NA → NA |

## Lane C · m1_h2_main

- Instances (analysis keep): **854**
- M1 dose-span coverage: **1600/1875** (85.3%)

### Normalizer failure categories (non-ok spans)

- **per_kg_per_day**: 259 — e.g. _icoids, such as prednisone at a dose of 1 mg/kg as a single daily dose either orally or intravenously, are a reasonable first therapy for bo_
- **range**: 16 — e.g. _.) Infliximab is given intravenously, 3–5 mg/kg body weight, and then repeated 2 weeks later, again 6 weeks later, and then at 8-week interv_

### Before → after metrics

| Verifier | QI | NS claim | NS evid | US claim | US evid |
| --- | --- | --- | --- | --- | --- |
| Mistral-Small-24B (MedScore) | 0.677 [0.565,0.790] (42/62) → 0.918 [0.852,0.984] (56/61) | 0.995 [0.986,1.000] (210/211) → 0.995 [0.985,1.000] (208/209) | 0.953 [0.915,0.981] (201/211) → 0.952 [0.913,0.981] (199/209) | NA → 0.991 [0.972,1.000] (105/106) | NA → 0.906 [0.849,0.962] (96/106) |
| GPT-4o (MedScore) | NA → 0.967 [0.918,1.000] (59/61) | NA → 0.967 [0.943,0.990] (202/209) | NA → 0.746 [0.675,0.808] (156/209) | NA → 1.000 [1.000,1.000] (106/106) | NA → 0.236 [0.160,0.321] (25/106) |
| GPT-4o-mini (MedScore) | NA → 0.885 [0.803,0.951] (54/61) | NA → 0.971 [0.942,0.995] (203/209) | NA → 0.943 [0.896,0.981] (197/209) | NA → 0.981 [0.953,1.000] (104/106) | NA → 0.736 [0.642,0.811] (78/106) |
| MiniCheck-Flan-T5-Large | 0.083 [0.017,0.150] (5/60) → NA | 0.956 [0.916,0.990] (194/203) → NA | 0.887 [0.834,0.937] (180/203) → NA | NA → NA | NA → NA |
| Bespoke-MiniCheck-7B | 0.774 [0.661,0.871] (48/62) → NA | 0.972 [0.943,0.995] (205/211) → NA | NA → NA | NA → NA | NA → NA |
| AlignScore-large | 0.246 [0.140,0.351] (14/57) → NA | 0.980 [0.950,1.000] (195/199) → NA | 0.940 [0.899,0.975] (187/199) → NA | NA → NA | NA → NA |
| Llama-3.3-70B (RAGAS NLI) | 0.758 [0.645,0.855] (47/62) → 0.871 [0.790,0.952] (54/62) | 0.971 [0.947,0.990] (203/209) → 0.995 [0.986,1.000] (210/211) | 0.923 [0.880,0.962] (193/209) → 0.972 [0.942,0.995] (205/211) | NA → 1.000 [1.000,1.000] (107/107) | NA → 0.869 [0.804,0.925] (93/107) |
| v4_ragas_nli.legacy | 0.881 [0.797,0.966] (52/59) → NA | 1.000 [1.000,1.000] (209/209) → NA | 0.966 [0.928,0.995] (201/208) → NA | NA → NA | NA → NA |
| Claude Sonnet 4.6 (RAGAS NLI) | NA → 0.952 [0.903,1.000] (59/62) | NA → 1.000 [1.000,1.000] (211/211) | NA → 0.976 [0.948,1.000] (206/211) | NA → 1.000 [1.000,1.000] (107/107) | NA → 0.645 [0.551,0.729] (69/107) |
| GPT-4o-mini (RAGAS) | NA → 0.966 [0.915,1.000] (57/59) | NA → 0.995 [0.985,1.000] (202/203) | NA → 0.970 [0.932,0.995] (197/203) | NA → 0.990 [0.971,1.000] (102/103) | NA → 0.932 [0.883,0.971] (96/103) |
| Claude Haiku 4.5 (RAGAS) | NA → 0.983 [0.950,1.000] (59/60) | NA → 1.000 [1.000,1.000] (207/207) | NA → 0.976 [0.942,1.000] (202/207) | NA → 1.000 [1.000,1.000] (105/105) | NA → 0.952 [0.914,0.990] (100/105) |
| Llama-3.1-8B (RAGAS) | NA → 0.881 [0.797,0.949] (52/59) | NA → 0.985 [0.961,1.000] (200/203) | NA → 0.970 [0.946,0.990] (197/203) | NA → 1.000 [1.000,1.000] (103/103) | NA → 0.777 [0.689,0.864] (80/103) |
| Mistral-Small-3.2-24B (RAGAS) | NA → 0.984 [0.952,1.000] (61/62) | NA → 1.000 [1.000,1.000] (211/211) | NA → 0.938 [0.900,0.972] (198/211) | NA → 0.963 [0.925,1.000] (103/107) | NA → 0.766 [0.682,0.850] (82/107) |

