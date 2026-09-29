# Lane B calibration vs node30

Calibration ids: 200
HPC dir: `results/raw/lane_b/calibration_200`
lane_b_env_id: `7e0333729b5da0af`

| Checker | n | agreement | mean |Δscore| | env_ids |
|---|---:|---:|---:|---|
| t6a_minicheck_roberta | 93 | 100.0% | 0.0000 | 7e0333729b5da0af |
| t6a_minicheck_deberta | 93 | 98.9% | 0.0068 | 7e0333729b5da0af |
| t6a_alignscore_base | 93 | 100.0% | 0.0000 | 7e0333729b5da0af |
| t6a_summac_zs | 93 | 67.7% | 0.6522 | 7e0333729b5da0af |
| t6a_summac_conv | 93 | 67.7% | 0.2085 | 7e0333729b5da0af |
| t6a_hhem | 0 | NA | NA | — |
| t6a_granite_guardian | 0 | NA | NA | — |

**PAUSE downstream packs** (agreement < 97%): t6a_summac_zs, t6a_summac_conv
