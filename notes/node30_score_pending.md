# node30 — score pending instances (V2a / V3)

After `git pull`, run `python3 scripts/build_score_pending.py` to refresh:

| File | Contents |
| --- | --- |
| `data/v3/instances_score_pending_cpu_early.jsonl` | New **cpu_early** rows (78× POLARITY `rephrase` INV) |
| `data/v3/instances_score_pending_g_inv.jsonl` | **G** LLM paraphrase INV (`instances_g_inv_paraphrase.jsonl`) |
| `data/v3/instances_score_pending_node30.jsonl` | **Union** for one node30 pass |

Append scores to the existing files (resume by `instance_id`):

- `results/raw/v2a_minicheck.jsonl`
- `results/raw/v3_alignscore.jsonl`

Use the same env as `notes/environment_node30.md` (MiniCheck + AlignScore, threshold 0.5).

On HPC, V1/V4 OpenRouter for the **cpu_early** pending slice only:

```bash
jobs/run_pending_v1v4_openrouter.sh
```

(or tmux wrapper if added).

Manifest: `notes/score_pending_manifest.json`.
