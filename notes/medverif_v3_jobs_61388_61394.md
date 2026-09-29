# medverif-v3 jobs 61388 / 61394

## What the job is

`jobs/label_v3.sbatch` → `src/generate_v3.py` (**not** instance scoring).

| Step | Models | Output |
|------|--------|--------|
| Paraphrase rounds 1–3 | Qwen2.5-32B-Instruct (vLLM) | `data/v3/para_attempts.jsonl` (append per 32-row chunk) |
| Fluency / meaning | Phi-4 (vLLM) | updates rows in `para_attempts.jsonl` |
| Side labels | Phi-4 | `flip_fluency.jsonl`, `dose_kind_phi.jsonl`, `domain_phi.jsonl` |
| Apply | CPU | `apply_v3.py`, `write_qc_v3.py` |

**Pack:** `data/v3/paraphrase_todo.jsonl` (194 bases now; log had 212 paraphrase + 62 flips at start of 61394).

## Resume behavior

- Skips bases with any `passed: true` in `para_attempts.jsonl`.
- Skips bases that already have a row for the current `attempt` number.
- `flip_fluency.jsonl` / kind files: written once if file exists (no merge dedupe).

## 61388 (CANCELLED, 41m, node002)

Log only shows vLLM platform detect; cancelled before meaningful work.

## 61394 (TIMEOUT 3h, node004)

From `jobs/logs/medverif-v3-61394.out`:

- Completed **Qwen attempt 1** paraphrase chunks (212 rows flushed incrementally in log).
- **Phi-4** pass for attempt 1; started attempt 2; wrote **32 rows** at attempt 2.
- **Attempt 3** started loading Qwen when **TIME limit** hit (20:30:54).

**Shared FS now:** `data/v3/para_attempts.jsonl` is **0 bytes** (mtime 2026-09-28 23:58) — progress from 61394 is **not** on disk; resume will restart paraphrase from scratch unless restored from backup elsewhere.

## Resubmit (2026-09-29)

- `label_v3.sbatch` timelimit **8:00:00** (was 3h).
- `HF_HUB_OFFLINE=1` unchanged (weights already in hub cache for Qwen + Phi-4).
- `append_jsonl` now `flush` + `fsync` per row.
