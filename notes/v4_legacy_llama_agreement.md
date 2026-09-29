# V4 legacy vs Llama-3.3-70B agreement

Legacy = `*.legacy.jsonl`; new provenance = `*.llama.jsonl`. Agreement ≥95% supports treating legacy as same Llama policy (still use `.llama` for analysis).

| Pack | n | agree | rate | ≥95% legacy≈Llama |
| --- | ---: | ---: | ---: | --- |
| main | 975 | 937 | 96.1% | yes |
| threshold | 220 | 195 | 88.6% | no |
| t4_eco | 433 | 389 | 89.8% | no |
| t4c_eco | 138 | 127 | 92.0% | no |
| t7 | 226 | 178 | 78.8% | no |
| m1 | 378 | 364 | 96.3% | yes |
| m1_t7 | 21 | 21 | 100.0% | yes |

## Paper provenance (legacy ≠ registry Llama)

All analyses and paper numbers use **`*.llama.jsonl`** only (registry `meta-llama/llama-3.3-70b-instruct`).

Packs with legacy↔Llama agreement **<95%** (legacy was **not** the registry model; do **not** treat legacy as Llama):
- **threshold**: 88.6% (n=220)
- **t4_eco**: 89.8% (n=433)
- **t4c_eco**: 92.0% (n=138)
- **t7**: 78.8% (n=226)

## main
- **C0**: 153/153 (100.0%)
- **E1-claim**: 235/242 (97.1%)
- **E1-evid**: 227/236 (96.2%)
- **E2**: 241/250 (96.4%)
- **INV-claim**: 81/94 (86.2%)

## threshold
- **C0**: 29/29 (100.0%)
- **E1-claim**: 52/57 (91.2%)
- **E1-evid**: 41/58 (70.7%)
- **E2**: 56/58 (96.6%)
- **INV-claim**: 17/18 (94.4%)

## t4_eco
- **ECO-answer**: 389/433 (89.8%)

## t4c_eco
- **ECO-answer-t4c**: 127/138 (92.0%)

## t7
- **E1-unit-claim**: 103/111 (92.8%)
- **E1-unit-evid**: 75/115 (65.2%)

## m1
- **C0**: 58/60 (96.7%)
- **E1-claim**: 112/115 (97.4%)
- **E1-evid**: 109/117 (93.2%)
- **INV-claim**: 85/86 (98.8%)

## m1_t7
- **C0**: 8/8 (100.0%)
- **E1-unit-claim**: 7/7 (100.0%)
- **E1-unit-evid**: 6/6 (100.0%)

