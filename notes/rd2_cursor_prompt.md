# Cursor prompt: run RD2 on HPC (bright92)

Copy everything between the two `-----` lines into Cursor (Agent mode) on bright92, opened in `/data2/hpcshared/medverif-audit`.

-----
You are running the pre-registered RD2 study of the medverif-audit repo on the HPC login node bright92.
Repo: `/data2/hpcshared/medverif-audit` (branch master). Scheduler: Slurm, partition `defq`. The GPU node has 4 shared
A100-80GB GPUs, so never use more than 2 GPUs at the same time. Work step by step. After each step, show me the key
output lines and wait for nothing; just continue unless a STOP rule triggers.

HARD RULES
- Never print, echo, cat or log any API key or token (`~/.medverif_keys`, `.env`, HF token). Only say "set" / "not set".
- Never force-push, never `git reset --hard`, never rebase, never `git stash` the existing local changes. The checkout has
  about 30 locally modified tracked files that belong to other work. Do not touch, commit or revert them.
- Never modify existing files under `data/`, `qc/`, `results/journal2/`, `results/journal3/`, `results/journal4/`, and
  never edit `prereg/rd2_prereg.md`, `prereg/rd2_freeze.json`, `results/journal5/rd2/real_dose/questions.jsonl`,
  `results/journal5/rd2/labels/*`, or any `scripts/journal5/*.py`. If a code fix seems needed, STOP and tell me what you
  would change and why (it must be logged in `prereg/rd2_amendments.md` first).
- Commit only RD2 outputs (`results/journal5/rd2/`, `notes/rd2_run_status.md`, `prereg/rd2_amendments.md`).
- OpenRouter spend for ALL of RD2 is capped at $3 (`MEDVERIF_RD2_MAX_USD=3`). Do not raise it.

STEP 0: update the checkout
```
cd /data2/hpcshared/medverif-audit
git status --short | head -40          # expect the known local modifications; note them, do not change them
git pull --ff-only
```
If `git pull --ff-only` fails because an upstream file conflicts with a local modification: STOP and show me the
message.

STEP 1: verify the pre-registration (before anything runs)
```
git log --diff-filter=A --format='%H %ci %s' -- prereg/rd2_prereg.md
```
It must print exactly one commit starting with `d3ac9bd` and subject `journal5: RD2 prereg (frozen before generation)`.
Then:
```
export MEDVERIF_PYTHON=/data2/cmdir/home/toandq/.conda/envs/vllm/bin/python
$MEDVERIF_PYTHON -m unittest scripts/journal5/test_rd2.py
bash jobs/run_rd2_chain.sh preflight
```
STOP if any test fails, if preflight prints `BLOCKER`, if `freeze check` is not `OK`, or if any of llama31_8b,
qwen25_14b, medgemma_27b or baichuan_m2_32b does not show status `ok` with a revision. Show me the whole preflight
output. A file listed under "runner/analysis files changed since freeze" is not a blocker, but report it.

STEP 2: generate answers (open models on GPU, sequential)
```
bash jobs/run_rd2_chain.sh gen            # sbatch array 0-3%1: llama31_8b, qwen25_14b, medgemma_27b, baichuan_m2_32b
bash jobs/run_rd2_chain.sh or-gen         # in parallel on the LOGIN node (needs internet): gpt-4o-mini + gemma-3-27b, ~$0.07
```
Monitor with `bash jobs/run_rd2_chain.sh status` and `tail -n 30 jobs/logs/rd2-GEN_<jobid>_<i>.out` every ~10 minutes.
Retry policy:
- If a task fails, read its log, fix only environment problems (not code), and resubmit that task:
  `sbatch --array=<i> jobs/journal5/rd2_GEN.sbatch`. It resumes from where it stopped. Do at most 2 retries per task.
- CUDA out of memory on task 2 or 3: resubmit with `MEDVERIF_RD2_GPU_UTIL=0.95 sbatch --array=<i> jobs/journal5/rd2_GEN.sbatch`.
  If it still fails, use `MEDVERIF_RD2_TP=2 sbatch --gres=gpu:2 --array=<i> jobs/journal5/rd2_GEN.sbatch`.
- If a model cannot be loaded after 2 attempts: STOP and tell me (the pre-registered replacement is `qwen25_7b`, and it
  needs an amendment entry first).
- `or-gen` retries itself 3 times. If it stops with "BUDGET STOP", do not raise the cap; report it.
Done when each of the 6 files `results/journal5/rd2/real_dose/answers/<generator>.jsonl` covers 960 (question,
condition) pairs. Check with
`$MEDVERIF_PYTHON scripts/journal5/rd2_generate.py --backend vllm --dry-run` (todo 0 for each local model) and
`$MEDVERIF_PYTHON scripts/journal5/rd2_generate.py --backend openrouter --dry-run` (todo 0). Some empty answers (e.g.
Baichuan reasoning cut at 160 tokens) are allowed after 3 passes. Count them and report them; do not change max_tokens.

STEP 3: extraction and classification (CPU, about 1 minute, login node)
```
bash jobs/run_rd2_chain.sh post
cat results/journal5/rd2/real_dose/extract_manifest.json | head -60
```
Expect about 5,700 instances. Report `auto_unit_type`, the class counts per condition, and the adjudication sheet row
count.

STEP 4: scoring with the paper's checkers and judges
```
bash jobs/run_rd2_chain.sh score --parallel 2   # rd2-SMALL (CPU, 5 small checkers incl. UNF v1/v2 rows), rd2-JG (9 local judges), rd2-FT (8 FT models)
bash jobs/run_rd2_chain.sh api-judges           # LOGIN node: Llama-3.3-70B RAGAS + Mistral-24B MedScore via OpenRouter, ~$1.0
```
Monitor as in step 2. Failed array tasks: resubmit only that index (`sbatch --array=<i> jobs/journal5/rd2_JG.sbatch`,
`rd2_FT.sbatch` or `rd2_SMALL.sbatch`), at most 2 retries; they resume by instance_id. AlignScore FT tasks (1, 3, 6, 7)
may fall back to CPU and take several hours. That is expected.
Done when `wc -l results/journal5/rd2/real_dose/scores/*.jsonl` shows 7 files with the same line count as
`instances.jsonl`, `results/journal5/rd2/judges/*__rd2.jsonl` exist for every judge that ran, and
`results/journal5/rd2/ft/*__rd2_raw.jsonl` exist for all 8 FT models.

STEP 5: provisional report and run log
```
bash jobs/run_rd2_chain.sh report
sacct -u $USER -S today --name=rd2-GEN,rd2-SMALL,rd2-JG,rd2-FT --format=JobID,JobName%12,State,Elapsed,AllocTRES%40 | tail -n 60
bash jobs/run_rd2_chain.sh status
```
Write `notes/rd2_run_status.md` (new file) with: date/time (UTC+7), commit hash used, Slurm job ids and elapsed times,
answers per generator (and empty answers), instances, auto class counts, OpenRouter spend, which judges/FT models
finished, every retry/failure and what you did about it, and a note that all numbers in `results/journal5/rd2/report.md`
are PROVISIONAL (auto labels) until the pharmacist adjudication is done.

STEP 6: commit and push (only RD2 outputs)
```
bash jobs/run_rd2_chain.sh commit
git log --oneline -3
```
If the push is rejected, run `git pull --no-rebase --no-edit` once and push again. Never force-push. If that fails,
STOP and show me the error.

STEP 7: tell me
- the answer and instance counts, auto unit/basis error count, OpenRouter spend, GPU hours used, and any blocked step;
- the path of the blind pharmacist sheet: `results/journal5/rd2/qc/rd2_adjudication_sheet.csv`. Only this file goes to the
  pharmacist. `rd2_adjudication_key.csv` must NOT be shared with them.
-----

## Expected runtime and resources (estimates)

| stage | where | resources | expected time |
|---|---|---|---|
| preflight + tests | login | CPU | < 2 min |
| GEN (4 open models × 960 answers) | Slurm, sequential `%1` | 1 × A100-80GB at a time, 128 GB RAM | llama-8B ~10 min, qwen-14B ~15 min, medgemma-27B ~25 min, baichuan-32B ~30 min (incl. load) → ~1.5 GPU-h, ~1.5–2 h wall |
| or-gen (2 × 960 calls) | login | network | 15–30 min, ≈ $0.07 (worst case $0.21) |
| post (merge, extract, basis check, UNF packs, sheet) | login | CPU | ~1 min |
| SMALL (5 checkers × ~5.7k rows + ~4k UNF rows) | Slurm array 0-4 | 16 CPU, 64 GB each, no GPU | ~1.5–4 h per task (RD: 75 min for 1451 rows × 5 checkers) |
| JG (9 local judges × ~5.7k rows) | Slurm `%2` | ≤ 2 GPUs | small ones 5–10 min, 14B ~20 min, 27–32B ~30–40 min → ~2.5 GPU-h, ~1.5 h wall |
| FT (8 models, rd2 raw + UNF pack) | Slurm `%2` | ≤ 2 GPUs (AlignScore may fall back to CPU) | MiniCheck-FT5 ~15 min each; AlignScore 20 min on GPU or 2–4 h on CPU |
| api-judges (2 × ~5.7k calls) | login | network | 1–2 h, ≈ $1.0 (RD: $0.25 for 1451) |
| report + commit | login | CPU | < 2 min |

Total: about 5–6 GPU-hours and never more than 2 GPUs at once. Wall time is about 6–10 h plus queue time. Total
OpenRouter spend is about $1.1 (hard cap $3 for all RD2 spend).
