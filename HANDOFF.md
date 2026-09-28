# HANDOFF

Repo: `/data2/hpcshared/medverif-audit`. Do not score `data/instances.jsonl` (pre-fix labels). Do not cancel jobs whose names start with `p3-noadv`.

## 1. Current state

Stage 1–2 is done: 246 kept bases, 1695 instances in `data/instances.jsonl`. QC v2 rebuilt that set (threshold and scope held out; unit conversion tightened; lexical / not_remove flips). QC v3 CPU rules are applied in `data/v3/instances_audit.jsonl`: every old INV-paraphrase row is `valid=false`. Phi-4 fluency, dose_kind/domain labels, and new Qwen paraphrases are not applied yet (`data/v3/apply_stats.json` does not exist). SLURM job 61388 is running that GPU step. No verifier has written `results/raw/*.jsonl`. V1 shard files are all 10 on disk; the downloader process is still alive. A CPU MiniCheck/AlignScore job was written and not submitted.

## 2. Jobs

`squeue -u $USER` at write time:

```
61389 defq p3-noadv82 PD QOSMaxGRESPerUser
61387 defq p3-noadv42 PD QOSMaxGRESPerUser
61382 defq p3-noadv-ex PD Dependency
61388 defq medverif-v3 R 9:22 node002
61381_3 defq p3-noadv R node002
61381_1 defq p3-noadv R node004
61381_2 defq p3-noadv R node004
```

Ours, still running:

- `61388` Qwen paraphrase + Phi-4 checks. Script `/data2/hpcshared/medverif-audit/jobs/label_v3.sbatch`. Log `/data2/hpcshared/medverif-audit/jobs/logs/medverif-v3-61388.out` (empty when this file was written; stdout is buffered). On success: `data/v3/para_attempts.jsonl`, `flip_fluency.jsonl`, `dose_kind_phi.jsonl`, `domain_phi.jsonl`, rewritten `instances_audit.jsonl`, `instances_main.jsonl`, `instances_threshold.jsonl`, `apply_stats.json`, `qc/qc_samples_v3.md`, `qc/qc_stats.md`. It sbatches `jobs/stage3_v1.sbatch` only if every V1 shard file has a valid safetensors header.
- Login PID `3863732`: `/data2/hpcshared/medverif-audit/scripts/repair_qwen_shards.py`. Log `/data2/hpcshared/medverif-audit/jobs/logs/repair_qwen.log`. Do not kill it. It already verified Qwen and Phi sha256, then started verifier downloads. It is still fetching Mistral, including `consolidated.safetensors` (a duplicate of the shards; ignore that file).

Not ours. Do not cancel: `61381_*`, `61387`, `61389`, `61382`. They are `ctrl_noadv` training/extraction under `/data2/hpcshared/Vinh-/paper-3/scripts/`. They hold the account at the 4-GPU cap.

`jobs/cpu_early.sbatch` is not in the queue.

## 3. Data versions

| Path | Meaning |
| --- | --- |
| `data/base_pairs.jsonl` | 246 Stage 1–2 kept bases |
| `data/instances.jsonl` | 1695 original instances. Do not score |
| `data/llm_stats.json` | generator/validator drop counts |
| `data/v2/instances_main.jsonl` | 1456 rows after v2 rules, before v3 |
| `data/v2/instances_threshold.jsonl` | 243 threshold rows, v2 |
| `data/v2/bases_threshold.jsonl` | threshold bases; field `threshold_quantifier` |
| `data/v2/bases_scope_excluded.jsonl` | polarity dropped for only/except/unless/but/if not |
| `data/v3/instances_audit.jsonl` | v2 rows plus `valid`. Old paraphrases `invalid_reason=inv_paraphrase_v2`. 61388 will rewrite this |
| `data/v3/instances_cpu_early.jsonl` | 1365 `valid=true` rows, no paraphrase (1158 main + 207 threshold) |
| `data/v3/instances_cpu_main.jsonl` | those 1158 main rows |
| `data/v3/paraphrase_todo.jsonl` | bases 61388 paraphrases |
| `qc/qc_samples_v2.md`, `qc/qc_stats.md` | v2 review. v3 samples not written |

Pre-Phi main C0 with `valid=true` (will change when 61388 finishes): DOSE 122, POLARITY 62.

Cross tab type × flip_mechanism × dose_kind:

- DOSE / — / prescriptive 97
- DOSE / — / unclear 16
- DOSE / — / measurement 7
- DOSE / — / descriptive 2
- POLARITY / lexical / — 32
- POLARITY / not_insert / — 27
- POLARITY / not_remove / — 3

Also on those 184 bases: domain_kind treatment 38, unclear 21, other 2, diagnostic_procedure 1; `c0_drift` 10; `ocr_noise` 5. Threshold still valid: 28 DOSE (prescriptive 21, unclear 6, measurement 1).

Instance fields now: `instance_id`, `base_id`, `type`, `subset`, `condition`, `magnitude`, `claim`, `evidence`, `expected_verdict`, `claim_span`, `evidence_span`, `claim_c0`, `evidence_c0`, `diff`, `flip_mechanism`, `dose_kind`, `domain_kind`, `c0_drift`, `ocr_noise`, `valid`, `invalid_reason`. `threshold_quantifier` is on the v2 base files, not on audit instances. Analysis must use `valid=true` only.

## 4. Models

Cache: `HF_HOME=/data2/hpcshared/medverif-audit/.cache/huggingface` (hub under `.../hub`).

| Model | Revision | Disk |
| --- | --- | --- |
| `Qwen/Qwen2.5-32B-Instruct` | `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd` | 17 shards, sha256 matched |
| `microsoft/phi-4` | `2db69c1c3e91a05d2c64a3185acfbaf36f744e25` | 6 shards, sha256 matched |
| `mistralai/Mistral-Small-24B-Instruct-2501` | `9527884be6e5616bdd54de542f9ae13384489724` | 10 `model-*.safetensors` files present. Sizes matched HF for shards 1–8. Shards 9–10 were still `.incomplete` at the last size check and the files exist now. Re-check size and header before any GPU load. Ignore `consolidated.safetensors` |
| `lytang/MiniCheck-Flan-T5-Large` | `96eafd01cee2d16cf81aaa2fb226b14f422a37b3` | not verified |
| `bespokelabs/Bespoke-MiniCheck-7B` | `1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8` | not started |
| `yzha/AlignScore` file `AlignScore-large.ckpt` | `8509e78d25bb914939fc585c626500c9b2944249` | not started |
| `FacebookAI/roberta-large` | `722cf37b1afa9454edce342e7895e588b6ff1d59` | not started. Ignore `pytorch_model.bin` |
| `Qwen/Qwen3-14B` | `40c069824f4251a91eefaf281ebe4c544efd3e18` | not started |

Code clones, not weights: `/data2/hpcshared/medverif-audit/.cache/src/MiniCheck` at `b58b9fa69acbd1015ec970fa65dd752413a053d2`, `.../AlignScore` at `a0936d5afee642a46b22f6c02a163478447aa493`.

## 5. Verifiers

Smoke pairs: `/data2/hpcshared/medverif-audit/tests/smoke_pairs.jsonl` (6 hand pairs). No smoke results. No `results/raw` verdicts.

- V1 `src/verifiers/v1_medscore.py`. MedScore prompt, no system message. Study verdict is whole-word `true`/`false`, else `PARSE_FAIL`. Released parser score stored separately. `not true` stays PASS.
- V2a `src/verifiers/v2a_minicheck.py`. Flan-T5-Large. PASS iff their `pred_label==1` (`prob>0.5`). Forced `.to("cpu")`. Not run.
- V2b: no wrapper.
- V3 `src/verifiers/v3_alignscore.py`. `evaluation_mode=nli_sp`, PASS iff score `>0.5`, `device=cpu`. Not run.
- V4 `src/verifiers/v4_ragas_nli.py`. Qwen3, `enable_thinking=False`. `statements[0].verdict` 1 PASS, 0 FAIL, else `PARSE_FAIL`. Not run.
- Scorer: `PYTHONPATH=src python src/score_jsonl.py --verifier <module> --instances <jsonl> --out <jsonl>`. Skips `valid=false` and finished `instance_id`s.

## 6. Code map

Run GPU scripts with `cd /data2/hpcshared/medverif-audit` and `PYTHONPATH=src` inside conda env `vllm`.

- `src/extract_candidates.py` — textbook pool to `data/candidates.jsonl`.
- `src/stage12_llm.py` — Qwen claims, Phi-4 yes/no. Used by `jobs/stage12.sbatch`.
- `src/perturb.py` — C0/E1/E2/unit-INV instances. Unit-INV skipped when no natural conversion.
- `src/text_utils.py` — dose regex, flips, `natural_unit_conversion`.
- `src/qc_rules.py` — v2 threshold and scope rules.
- `src/rebuild_v2.py` — writes `data/v2/*`.
- `src/qc_v3.py` — grammar, hedges, OCR, dose_kind, domain. `python src/qc_v3.py`. `validate_v2.py` / `write_qc_v2.py` already wrote the v2 QC files.
- `src/prepare_v3.py` — builds the audit file. Already run.
- `src/generate_v3.py` — what job 61388 runs.
- `src/apply_v3.py` — merges Phi/Qwen labels. Called at the end of 61388.
- `src/write_qc_v3.py` — writes `qc/qc_samples_v3.md` after apply.
- `src/cpu_early.py` — CPU V2a+V3, skips paraphrase, 20-item ETA gate. Not submitted.
- `src/score_jsonl.py` — resumable verifier scoring.
- `src/v1_parser.py` — do not edit the released parser.
- `src/selftest_rules.py` — `PYTHONPATH=src python src/selftest_rules.py`.
- `analysis/analyze.py` — Stage 4. `PYTHONPATH=src:.cache/pydeps python analysis/analyze.py --instances ... --verdicts ... --outdir ...`. `--selftest` passed. Skips `valid=false`.
- `analysis/make_mock.py` — mock figures under `tests/mock_out/` only.
- `jobs/stage12.sbatch` — finished (job 61379).
- `jobs/label_v3.sbatch` — job 61388.
- `jobs/stage3_v1.sbatch` — smoke, then main, then threshold. Not submitted by hand.
- `jobs/cpu_early.sbatch` — not submitted.
- `scripts/download_verifiers.py` — V1 then V2a, V2b, AlignScore, RoBERTa, Qwen3. Ignore Mistral `consolidated.safetensors`.
- `scripts/repair_qwen_shards.py` — the live PID 3863732.

## 7. Environment

```
source /data2/shared/apps/conda/etc/profile.d/conda.sh
conda activate vllm
export HF_HOME=/data2/hpcshared/medverif-audit/.cache/huggingface
export HUGGINGFACE_HUB_CACHE=$HF_HOME/hub
export HF_HUB_DISABLE_TELEMETRY=1
```

Env `vllm`: Python 3.12.9, torch 2.6.0+cu124, vllm 0.8.3, transformers 4.51.2, huggingface_hub 0.30.2. Login Python is 3.8; do not use it for GPU jobs. Partition `defq`, `--exclude=node001`, QoS `vip4` max 4 GPUs. GPU jobs that worked: `--gres=gpu:1 --mem=64G --cpus-per-task=8`. `hf_transfer` is not installed. Do not pip into the `vllm` env. Extra packages go to `.cache/pydeps` or `.cache/cpu_extra`. A pip into `.cache/cpu_extra` (nltk, spacy, pytorch-lightning) was started on the login node and was not confirmed finished.

## 8. Open TODOs

1. Wait for 61388. Read `data/v3/apply_stats.json` and `qc/qc_samples_v3.md`. Do not score until `instances_main.jsonl` exists.
2. Size-check all 10 V1 shards against HF metadata, then header-check. Ignore `consolidated.safetensors`.
3. After 61388 exits, if it did not sbatch Stage 3: `sbatch /data2/hpcshared/medverif-audit/jobs/stage3_v1.sbatch`.
4. CPU early run, only after `cpu_extra` imports work and a GPU slot is not required: `sbatch /data2/hpcshared/medverif-audit/jobs/cpu_early.sbatch`. It writes `results/raw/v2a_minicheck.jsonl`, `results/raw/v3_alignscore.jsonl`, and `results/tables/phenomenon_checklist_PRELIM.md`.
5. When PID 3863732 exits, finish remaining verifier weights with `download_verifiers.py` (V2b, V3, V4).
6. Stage 4 on `valid=true` main only: `PYTHONPATH=src:.cache/pydeps python analysis/analyze.py --instances /data2/hpcshared/medverif-audit/data/v3/instances_main.jsonl --verdicts /data2/hpcshared/medverif-audit/results/raw --outdir /data2/hpcshared/medverif-audit/results`. Checklist path: `results/tables/phenomenon_checklist.md`.
7. There is no git remote. `git push` cannot succeed until one is added. Do not invent a URL. Most code and data files are still uncommitted; this handoff commit is only `HANDOFF.md`.

## 9. Pitfalls

- NFS + hf_xet corrupts shards. `huggingface_hub` 0.30.2 ignores `HF_HUB_DISABLE_XET`. Set `huggingface_hub.file_download.is_xet_available = lambda: False` in the process.
- Matching file size is not integrity. Zero safetensors headers happened with the right size. Check the 8-byte header with `read(8)`, never `Path.read_bytes()` on a multi-GB shard.
- `consolidated.safetensors` is a second copy of V1 (~47 GB). The live downloader is pulling it. Do not load it.
- Do not map `PARSE_FAIL` to `FAIL`.
- `.cache/pydeps` has numpy 2.5.3. GPU jobs must not put that directory on `PYTHONPATH` or it shadows torch’s numpy.
- Four HF streams stayed near ~11 MB/s total. Login `quota` is unavailable; `/data2` had free space. Job 61388’s log stays empty until Python flushes; check `squeue`.
