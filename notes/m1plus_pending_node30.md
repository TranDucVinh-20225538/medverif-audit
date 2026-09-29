# M1+ node30 pending pack (`instances_m1plus_pending_node30.jsonl`)

**Row count:** **930** (current scope; intentional).

## Composition

| slice | n |
|---|---:|
| T3 PI_ok=Y (`inv_frequency` + `inv_route`, valid in `instances_inv_families`) | 35 |
| T1 M1+ scope on `data/v3/instances_cpu_early.jsonl` (C0, E1-claim/evid, INV-unit) | 895 |
| **Total** | **930** |

- **36** label ids in `qc/inv_claim_PI_ok_labels.csv`; one id (`D0115__INV-claim__inv_route__orally_to_PO`) has no valid row in the inv-family JSONL.
- Normalization: `apply_m1_plus_pair` (M1 dose/unit + M1+ frequency/route), `m1_preapplied=true`.
- Score on node30: `jobs/run_t1_m1plus_score_node30.sh` → `results/raw_m1plus/`.

Rebuild: `python3 scripts/build_m1plus_pending_node30.py`.
