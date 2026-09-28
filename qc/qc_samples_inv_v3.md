# QC samples — INV paraphrase pilot (OpenRouter)

**WAIT for PI OK** before full paraphrase run.

- Generator: `qwen/qwen-2.5-72b-instruct` (≠ V1 Mistral, ≠ V4 Qwen3-14B)
- Validator: `microsoft/phi-4` (Phi-4)
- Pilot: **5 DOSE + 5 POLARITY** bases

## D0001 (DOSE, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
A two-hour oral glucose tolerance test involves drinking a solution containing exactly 75 g of glucose.
```

**Rewrite**
```
A solution containing 75 g of glucose is consumed during a two-hour oral glucose tolerance test.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608452-y0WBNXH0S950R9ekg1ui", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608454-atDr0LF5GeKecp1ZmAi1", "model": "microsoft/phi-4", "tokens": 67, "cost_usd": 4.83e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608455-KsH7BUKOoq99Sysh9qUl", "model": "microsoft/phi-4", "tokens": 120, "cost_usd": 9.52e-06}`

## D0002 (DOSE, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
Most clinicians agree that glucocorticoids, such as prednisone at a dose of 1 mg/kg as a single daily dose either orally or intravenously, are a reasonable first therapy for both PM and DM.
```

**Rewrite**
```
A reasonable first therapy for both PM and DM, according to most clinicians, is glucocorticoids such as prednisone at a dose of 1 mg/kg, administered as a single daily dose either orally or intravenously.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608456-Uaxv7EUn77LRoWL7ek1F", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608462-a0LIWdZHpyPfbDnBs1CA", "model": "microsoft/phi-4", "tokens": 95, "cost_usd": 6.79e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608463-aivm6GXERj4xEBAVer0q", "model": "microsoft/phi-4", "tokens": 174, "cost_usd": 1.33e-05}`

## D0003 (DOSE, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
Adalimumab is given by subcutaneous injection, 40 mg biweekly.
```

**Rewrite**
```
Biweekly, 40 mg of adalimumab is administered by subcutaneous injection.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608464-SKhLPUQqKF2e28geqE6h", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608466-ye06vtle4D4uF42N8Snm", "model": "microsoft/phi-4", "tokens": 67, "cost_usd": 4.83e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608468-bRtRLbcJ8bB4IKCKSCJ4", "model": "microsoft/phi-4", "tokens": 105, "cost_usd": 7.49e-06}`

## D0004 (DOSE, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** NO | **Pass:** False

**Original**
```
It is important to note that peripheral neuropathies can be seen in doses of 200 mg per day or higher, as well as interaction with other medications.
```

**Rewrite**
```
Peripheral neuropathies can occur at doses of 200 mg per day or higher, and interactions with other medications should also be considered.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608469-2rimI1HDarRiIuZw6KBT", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608471-sD9Kie41FhV6MMSTB3GF", "model": "microsoft/phi-4", "tokens": 75, "cost_usd": 5.39e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608472-PAdBOFFei1sLHwZjxM3y", "model": "microsoft/phi-4", "tokens": 127, "cost_usd": 9.03e-06}`

## D0005 (DOSE, main)

**Rule:** ok | **Fluency:** NO | **Meaning:** YES | **Pass:** False

**Original**
```
Etanercept is given by subcutaneous injection, 50 mg once weekly.
```

**Rewrite**
```
Once weekly, etanercept is administered by subcutaneous injection, 50 mg.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608474-lWKF4YikCmC6LaAFabvV", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608478-ityvSe1QkdSL5UYgoxNL", "model": "microsoft/phi-4", "tokens": 81, "cost_usd": 6.79e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608480-lgNFngWN4Q5LUispKBcU", "model": "microsoft/phi-4", "tokens": 119, "cost_usd": 9.45e-06}`

## P0003 (POLARITY, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
MMR and varicella vaccines should be administered simultaneously or more than 30 days apart.
```

**Rewrite**
```
Simultaneously or more than 30 days apart, MMR and varicella vaccines should be administered.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608481-ZeQUsppuS54N6sRlaqKL", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608487-YA1o0muIGS3fKnusD8MN", "model": "microsoft/phi-4", "tokens": 70, "cost_usd": 5.04e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608488-TGqNfBhpfs6KfxTp32C5", "model": "microsoft/phi-4", "tokens": 123, "cost_usd": 9.73e-06}`

## P0004 (POLARITY, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
If uterine perforation was excluded by ultrasonography, intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, should be administered.
```

**Rewrite**
```
Intravenous broad-spectrum antibiotic coverage, usually with a cephalosporin, should be administered if uterine perforation was excluded by ultrasonography.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608490-xvQl6fdrRo1WQeitjmK4", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608497-0Ke8Ci17DBZI93xFmpTT", "model": "microsoft/phi-4", "tokens": 82, "cost_usd": 5.88e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608498-oaBLaqanI5MYEf7MXHEQ", "model": "microsoft/phi-4", "tokens": 136, "cost_usd": 9.66e-06}`

## P0009 (POLARITY, main)

**Rule:** span_count | **Fluency:** YES | **Meaning:** YES | **Pass:** False

**Original**
```
The drug is relatively contraindicated in patients with a history of epilepsy and for use with other drugs that lower the seizure threshold.
```

**Rewrite**
```
Contraindicated in patients with a history of epilepsy, the drug is also not recommended for use with other drugs that lower the seizure threshold.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608500-Ren3ZC1JBKum2cCZS7Jy", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608508-IdmkI3AMBvZm5orTzcVR", "model": "microsoft/phi-4", "tokens": 77, "cost_usd": 5.53e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608509-8qYZk8XqNuElh2D85FBv", "model": "microsoft/phi-4", "tokens": 124, "cost_usd": 8.82e-06}`

## P0017 (POLARITY, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
Neither medication should be used with occlusive dressings.
```

**Rewrite**
```
With occlusive dressings, neither medication should be used.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608510-rSzukFtSqHvsoJYFgHIc", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608516-WHvSyqVKoNsxjxWVAczt", "model": "microsoft/phi-4", "tokens": 74, "cost_usd": 6.3e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608518-4k9T2j5A3ew0ROxQZh3a", "model": "microsoft/phi-4", "tokens": 91, "cost_usd": 6.51e-06}`

## P0019 (POLARITY, main)

**Rule:** ok | **Fluency:** YES | **Meaning:** YES | **Pass:** True

**Original**
```
For the second drug, pemetrexed should be used for non-squamous cell cancer.
```

**Rewrite**
```
Pemetrexed should be used for non-squamous cell cancer as the second drug.
```

_Gen:_ `{"provider": "DeepInfra", "request_id": "gen-1790608520-FUM3PQRYZrnSY45a1Rqn", "model": "qwen/qwen-2.5-72b-instruct", "generator": "qwen/qwen-2.5-72b-instruct"}`
_Val fluency:_ `{"provider": "DeepInfra", "request_id": "gen-1790608533-jPeKfwiQoWrWHbZldiCI", "model": "microsoft/phi-4", "tokens": 81, "cost_usd": 6.79e-06}`
_Val meaning:_ `{"provider": "DeepInfra", "request_id": "gen-1790608534-T7gjq1kz3RYgoOzrQ6uF", "model": "microsoft/phi-4", "tokens": 121, "cost_usd": 9.59e-06}`

