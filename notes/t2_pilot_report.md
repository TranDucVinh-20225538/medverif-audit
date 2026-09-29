# T2 pilot report

- Pilot instances: **100** (2 verifiers → **200** API calls when complete)
- Scored rows in raw: **200**
- Pilot spend (sum api_cost_usd in raw/t2_pilot): **$0.6026**
- Approx $/instance/verifier: **$0.00603**
- OpenRouter limit_remaining: **49.185474478**

- Projected full T2 (both verifiers, 533 instances): **~$6.42**

**Full T2 run blocked** until `notes/t2_full_approved` exists.

## v1b_medscore

| Stratum | PASS | FAIL | PARSE | n |
| --- | ---: | ---: | ---: | ---: |
| C0 | 30 | 0 | 0 | 30 |
| E1-claim/x2 | 2 | 28 | 0 | 30 |
| INV/unit_conversion | 39 | 1 | 0 | 40 |

- INV-unit PASS rate: **39/40**; E1-claim FAIL rate: **28/30** (expect high FAIL).

## v5_ragas_nli

| Stratum | PASS | FAIL | PARSE | n |
| --- | ---: | ---: | ---: | ---: |
| C0 | 30 | 0 | 0 | 30 |
| E1-claim/x2 | 0 | 30 | 0 | 30 |
| INV/unit_conversion | 37 | 3 | 0 | 40 |

- INV-unit PASS rate: **37/40**; E1-claim FAIL rate: **30/30** (expect high FAIL).

