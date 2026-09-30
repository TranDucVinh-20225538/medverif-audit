# M1 repair after quantity normalization (Lane C / H2)

Pack: `data/lane_c/m1_h2_main.jsonl` (n=854).
Compare `results/raw` (before) vs `results/raw_m1/lane_c` (M1=1).

| Verifier | slice | before | after M1 |
|---|---|---:|---:|
| V1 | INV-unit PASS | see raw | see raw_m1 |
| V1b | INV-unit PASS | see raw | see raw_m1 |
| V1c | INV-unit PASS | see raw | see raw_m1 |
| V4-Llama | INV-unit PASS | see raw | see raw_m1 |
| V5 | INV-unit PASS | see raw | see raw_m1 |
| V6-gpt4o | INV-unit PASS | see raw | see raw_m1 |
| V6-haiku | INV-unit PASS | see raw | see raw_m1 |
| V6-llama8b | — | NA | NA |
| V6-mistral | — | NA | NA |

_Verbatim LLM judge explanations: inspect FAIL rows in lane_c JSONL `raw_output`._
