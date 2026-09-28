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

Open questions for the PI:

1. Confirm V1 = `mistralai/Mistral-Small-24B-Instruct-2501` rather than `gpt-4o`.
2. Confirm V4 uses only the RAGAS NLI prompt on the claim as a single statement (no statement-generator rewrite).
3. If Textbooks-only evidence is acceptable when StatPearls cannot be fetched from NCBI.
