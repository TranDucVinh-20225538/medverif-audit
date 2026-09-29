# node30 — score pending instances (V2a / V3)

After `git pull`, run `python3 scripts/build_score_pending.py` to refresh:

| File | Contents |
| --- | --- |
| `data/v3/instances_score_pending_cpu_early.jsonl` | New **cpu_early** rows (78× POLARITY `rephrase` INV) |
| `data/v3/instances_score_pending_g_inv.jsonl` | **G** LLM paraphrase INV (`instances_g_inv_paraphrase.jsonl`) |
| `data/v3/instances_score_pending_node30.jsonl` | **Union** for one node30 pass (raw / non-M1) |
| `data/v3/instances_m1_pending_node30.jsonl` | **T1-M1**: C0 + E1 + INV-unit, M1-normalized claim/evidence + `content_sha1` |
| `data/v3/instances_pol_flip_pending_node30.jsonl` | **14** human flip_ok Y bases missing V2/V3 (included in combined pending) |
| `data/v3/instances_m1plus_score_pending_node30.jsonl` | **M1+** rows not yet in `results/raw_m1plus/` |
| `data/t7/instances_e1_unit_m1_pending.jsonl` | **T7 M1**: 230 E1-unit + 115 C0 (M1 pre-applied) |

Append scores (resume by `instance_id`):

- Non-M1: `results/raw/v2a_minicheck.jsonl`, `results/raw/v3_alignscore.jsonl`
- **T1-M1:** `results/raw_m1/v2a_minicheck.jsonl`, `results/raw_m1/v3_alignscore.jsonl`
- **M1+:** `results/raw_m1plus/v2a_minicheck.jsonl`, `results/raw_m1plus/v3_alignscore.jsonl`
- **T7 M1:** `results/raw_m1/t7/*.jsonl`

Use the same env as `notes/environment_node30.md` (MiniCheck + AlignScore, threshold 0.5).

**T1-M1:** on node30 only, run `jobs/run_t1_m1_score_node30.sh` (not on HPC).

On HPC, V1/V4 OpenRouter for the **cpu_early** pending slice only:

```bash
jobs/run_pending_v1v4_openrouter.sh
```

(or tmux wrapper if added).

Manifest: `notes/score_pending_manifest.json`.
