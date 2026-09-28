# REPORT

**Daily status (2026-09-28):** Job **61388** (`medverif-v3`) running — Qwen paraphrase + Phi-4; no `apply_stats.json` yet. **V1:** 10/10 shard headers OK (`notes/v1_shard_headers.json`); scoring stores full `raw_output` + released score; study label via `reparse_v1_study.py`. **Weights PID 3863732** still downloading (V2b+); 4.4 GB consolidated `.incomplete` left untouched. **Next:** PI QC review after 61388; then `not_remove` mining, V4/V2b GPU scoring; CPU early blocked (`nltk` missing in `.cache/cpu_extra`).

## Stage 0 — Environment and sources (2026-09-28)

What ran: inspection only. Cluster (`sinfo`, one `srun nvidia-smi -L`), GitHub commits, Hugging Face model/dataset cards, MedScore `verifier.py`, MiniCheck `minicheck.py`, AlignScore `evaluate.py`, RAGAS `_faithfulness.py`, and the arXiv:2609.30467 PDF. No model was downloaded and no verifier was executed. There are no numbers in `results/` yet.

What broke / differs from the prompt:

- `/data2/hpcshared/Vinh` is not writable (`anhnv:toandq`, mode 755). Repo is `/data2/hpcshared/medverif-audit`.
- MedScore's code default verifier is `gpt-4o`. The open model in the paper and in `demo/config_medrag.yaml` is `mistralai/Mistral-Small-24B-Instruct-2501`. V1 will use that open checkpoint. Prompt and parser stay as released (binary True/False, no system prompt on the provided-evidence path).
- The anonymous arXiv:2609.30467 repo describes a 4-way label scheme. That is not the public ACL MedScore code. We will not wrap it.
- Public MedScore data has no (claim, retrieved passage, verdict) triples.
- StatPearls text is not on Hugging Face. Textbooks chunks are (`id`, `title`, `content`, `contents`).
- MedExpert-gold is described in arXiv:2609.30467 (139 Supported, 86 Refuted) but was not found as a public dataset. Anonymous `data/` listing returned HTTP 401. Not available.
- `Qwen/Qwen3-14B-Instruct` is not a public model id. Planned V4 judge is `Qwen/Qwen3-14B`. MedGemma-27B is gated.
- Login Python is 3.8.10. MedScore wants 3.12 via conda. GPU is A100-80GB on `defq`. `node001` is DRAIN. Host RAM on the mixed nodes was low at this snapshot.

Key numbers: none from a run. Source facts are in `notes/environment.md`.

PI decisions on 2026-09-28, applied:

1. V1 is `mistralai/Mistral-Small-24B-Instruct-2501` revision `9527884`. `gpt-4o` is not run.
2. V4 is named RAGAS-NLI. Statement decomposition is skipped. Judge will be `Qwen/Qwen3-14B` with thinking off. Not run in Stage 1–2.
3. Evidence is Textbooks only.
4. Claim generator is `Qwen/Qwen2.5-32B-Instruct`. Support and INV checks are `microsoft/phi-4`. Neither is V1 or V4.
5. Unparseable verifier output will be `PARSE_FAIL`. Released V1 parser behavior is in `notes/v1_parser.md`.
6. GPU jobs use `--gres=gpu:1`, `--mem=64G`, `--exclude=node001`, caches under this repo.

Stage 1–2 is queued as SLURM job `medverif-s12` (`jobs/stage12.sbatch`). It waits until weights are local and the node has at least 40 GB free RAM, then runs a 16-per-type smoke and, if that keeps at least one base pair, the full 180-per-type run. If the node is short on RAM it releases the GPU and resubmits 15 minutes later. Stage 3 is not queued.

<!-- stage12-final -->
## Stage 1–2 — base pairs and counterfactuals

Numbers below are copied from `data/extract_stats.json`, `data/llm_stats.json`, and `data/smoke_llm_stats.json`.

- Chunks read: 125847. Sentences: 795464.
- Pool after rules: DOSE 1541, POLARITY 652.
- Sent to the generator: 360 candidates (cap 180 per type).
- Smoke bases kept: 26 (attempted 32).
- Full bases kept: 246 by type `{"DOSE": 155, "POLARITY": 91}`.
- Instances: 1695.
- Claim generator: Qwen/Qwen2.5-32B-Instruct `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`.
- Support and INV checker: microsoft/phi-4 `2db69c1c3e91a05d2c64a3185acfbaf36f744e25`.
- Drops: `{"inv_meaning_rejected": 80, "span_missing_in_claim": 4, "span_not_unique_in_claim": 5, "validator_no": 25}`.

QC sample: `qc/qc_samples.md`. QC counts: `qc/qc_stats.md`.
Stage 3 was not started.
<!-- /stage12-final -->
