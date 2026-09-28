# REPORT

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
