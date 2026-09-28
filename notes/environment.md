# Stage 0 — environment and sources

Inspection date: 2026-09-28. Nothing in this file is a pilot result. No verifier was run.

## Where this repo lives

`/data2/hpcshared/Vinh` is not writable by this account (`toandq`). It is owned by `anhnv:toandq` with mode `755`. The new project is therefore at `/data2/hpcshared/medverif-audit`, the nearest writable directory on the same filesystem.

## Cluster snapshot (2026-09-28)

Login node has no working NVIDIA driver (`nvidia-smi` failed). GPUs are only on SLURM.

| Item | Observed |
| --- | --- |
| Partition | `defq` (default), State=UP, DefaultTime=07:00:00, MaxTime=UNLIMITED |
| Job defaults | `DefCpuPerGPU=12`, `DefMemPerGPU=96000` |
| Nodes | `node001` gpu:8, 256 CPUs, 1000000 MB, State=`IDLE+DRAIN` (do not schedule here) |
| | `node002` gpu:8, 240 CPUs, 850000 MB, State=`MIXED`, AllocTRES included `gres/gpu=8`, free host RAM ~23 GB |
| | `node004` gpu:8, 240 CPUs, 850000 MB, State=`MIXED`, AllocTRES `gres/gpu=2` (6 GPUs not allocated), free host RAM ~10 GB |
| GPU model | Confirmed with `srun --partition=defq --gres=gpu:1 --time=00:02:00 --mem=4G nvidia-smi -L`: `NVIDIA A100-SXM4-80GB` |
| Disk | `/data2` is 175T, 138T used, 37T free (80%). `quota` is not installed. |
| Modules | `conda/23.5.0` at `/data2/shared/apps/conda`. CUDA toolkits 11.2, 11.7, 12.1 are modules. SLURM 21.08.8. |
| Login Python | `/usr/bin/python3` 3.8.10. Too old for the MedScore env (Python 3.12). Use conda. |
| Git | 2.25.1 |

Host RAM on the mixed nodes was low at this snapshot, so a 1-GPU job that inherits `DefMemPerGPU=96000` may queue even when a GPU looks free. A short 4 GB `srun` did start and returned the A100 name above.

## MedScore (V1 source)

- Repo: https://github.com/Heyuan9/MedScore
- Commit inspected: `207c2b723f02339091ecc29628bf745d184952f6` (2026-09-06, "change the Question+Answer context prompt in README into an easier --qa option")
- Paper: Huang et al., Findings of ACL 2026, https://aclanthology.org/2026.findings-acl.693/ (also arXiv:2505.18452)
- Install env (`environment.yml`): Python 3.12, `openai==1.93.0`, `vllm`, `spacy==3.7.4`.

### What the released verifier actually is

Code default `verifier.model_name` is `gpt-4o` with `server_path` `https://api.openai.com/v1`. That is not an open model.

The paper's open verifier, and the model named in `demo/config_medrag.yaml` for a local vLLM server, is `mistralai/Mistral-Small-24B-Instruct-2501`. Hugging Face API on 2026-09-28: exists, not gated, revision `9527884be6e5616bdd54de542f9ae13384489724`, safetensors total 23,572,403,200 parameters. bf16 weights are about 48 GB, so one A100-80GB is enough.

**Deviation recorded:** V1 will be this open checkpoint via vLLM, not `gpt-4o`. The prompt and parser stay the released ones.

### How to score one (claim, evidence) pair without retrieval

Use verifier type `provided` (`ProvidedEvidenceVerifier` in `medscore/verifier.py`). The stock class loads evidence from a JSON file `{id: evidence_string}`. A wrapper can call the same `format_input` without retrieval. Do not use type `medrag` for this pilot; that runs MedCPT retrieval.

Released call settings in `Verifier.__init__`: `temperature=0.0`, `top_p=1.0`, `seed=42` (`random_state`), `max_tokens=256`.

There is **no system message** for `provided` or `medrag`. The user message is exactly:

```
Answer the question based on the given context.

{evidence}

Input: {claim} True or False?
Output:
```

`internal` is a different construct (model knowledge, not evidence). Its system prompt is `INTERNAL_KNOWLEDGE_PROMPT` and must not be used for this audit.

### Claim format and verdict labels

Decomposition output fields: `id`, `sentence`, `sentence_id`, `claim`, `claim_id`. A claim is one fact string. "No verifiable claim" is the decomposer's empty-fact token; this pilot will not run the decomposer.

Parser (`parse_verification_output`):

- score `1.0` if the lowercased completion contains `true` and not `false`
- score `0.0` if it contains `false` and not `true`
- if both appear, score `1.0` iff the last `true` is after the last `false`
- if neither appears, score `1.0` only when none of the tokens `not`, `cannot`, `unknown`, `information` appear

Binary map for this study: **PASS iff score == 1.0**, else **FAIL**. Store `raw` and `score`.

### Released data

Public data files:

- `data/AskDocs.jsonl` and `data/AskDocs.demo.jsonl`: keys `id`, `question`, `doctor_response`, `response`. No verdict.
- `data/askdocsai_evidence.json`: 300 entries, id → a single string (the doctor response), not retrieved MedRAG passages and not a verdict.
- `data/calmqa_english.jsonl` exists; not a (claim, passage, verdict) release.

**No released (claim, retrieved passages, verdict) triples** were in the public tree.

### Separate code, not V1

arXiv:2609.30467 (2026-09-24, Huang et al.) points at https://anonymous.4open.science/r/Medical_RAG_eval-4AB5. That README describes a **different** verifier output: labels `Supported` / `Refuted` / `No Evidence` / `Ambiguous`, with scores 1.0 / 0.0 / 0.0 / 0.5, and a demo model name `mistralai/Mistral-Small-4-119B-2603`. The public ACL repo inspected above is still binary True/False. This pilot wraps the public ACL repo.

## MedExpert (Phase 2 only; not used to build this pilot)

- Code: https://github.com/JHU-CLSP/MedExpert commit `98d19d9ec7f0b03273b97a9d6bf5e71548c98ede` (2026-04-18)
- Data: https://huggingface.co/datasets/sonal-ssj/MedExpert
- License on the HF card: `cc-by-4.0`
- Configs: `medexpert-all` 572 rows, `medexpert-benchmark` 540 rows
- Fields observed on one `medexpert-benchmark` row: `id`, `domain`, `model`, `base_question_id`, `title`, `annotator`, `question`, `response`, `factuality` (sentence spans with `label` bool plus annotation severity/comment/highlight), `omissions`, `comments`, `references`, `meta`, `model_certainty`, `omission_severity`, `n_omissions`, `n_factuality_annotated_spans`, `topic`, `base_title`, `highest_fact_severity`, `iaa`

### MedExpert-gold (arXiv:2609.30467)

The PDF describes a double-checked subset **MedExpert-gold** with 139 Supported and 86 Refuted (Table 1). Hugging Face dataset search for `MedExpert-gold` returned no dataset. The anonymous repo root lists a `data/` directory, but `.../files/data/` returned HTTP 401 `not_connected`, so the subset files could not be inspected. **Treat MedExpert-gold as not available.** It is out of scope for this pilot anyway.

## MedRAG corpora

Org: https://huggingface.co/MedRAG. Toolkit: https://github.com/Teddy-XiongGZ/MEDRAG (also cited as gzxiong/MedRAG).

### Textbooks — usable now

- https://huggingface.co/datasets/MedRAG/textbooks
- Not gated. HF card `license` field is empty. README says 125,847 snippets, average 182 tokens, chunks ≤ 1000 characters from 18 MedQA textbooks.
- Files: `chunk/*.jsonl` (18 books), including `chunk/Pharmacology_Katzung.jsonl`.
- Fields on the first Katzung row: `id`, `title`, `content`, `contents`. Example id: `Pharmacology_Katzung_0`.
- That first chunk is a controlled-substance list, not a prose dose sentence. Stage 1 has to filter for usable sentences.

### StatPearls — content not on Hugging Face

- https://huggingface.co/datasets/MedRAG/statpearls
- Repo files are only `.gitattributes` and `README.md`. The README states StatPearls content cannot be redistributed and must be downloaded from NCBI Bookshelf (`statpearls_NBK430685.tar.gz`) and chunked with MedRAG's `src/data/statpearls.py`.
- Documented schema if built locally: `id`, `title`, `content`, `contents`. 301,202 snippets, average 119 tokens.

**Deviation recorded:** Stage 1 will start from the Textbooks chunks that are actually on Hugging Face. StatPearls will be added only if the NCBI tarball downloads and chunks cleanly. If it does not, the pilot stays on Textbooks and the drop is logged.

## V2 — MiniCheck

- Code: https://github.com/Liyan06/MiniCheck commit `b58b9fa69acbd1015ec970fa65dd752413a053d2` (2025-08-27)
- `MiniCheck.score(docs, claims)` returns `pred_label`, `raw_prob`. In `minicheck.py`, `pred_label` is 1 iff `prob > 0.5`.
- V2a: `lytang/MiniCheck-Flan-T5-Large`, code name `flan-t5-large`, revision `96eafd01cee2d16cf81aaa2fb226b14f422a37b3`, license MIT, not gated. Chunk size in code: 500. About 0.8B. Fits easily.
- V2b: `bespokelabs/Bespoke-MiniCheck-7B`, code name `Bespoke-MiniCheck-7B`, revision `1ed7786bcda3fa1dc35f7c4ed9e3f36b785d33b8`, not gated. Authors serve it with vLLM. 7B fits on one A100-80GB.
- Map: **PASS iff pred_label == 1** (supported). Keep `raw_prob`. Threshold 0.5 is the author's, not one we chose.
- Both will be wrapped. If V2b fails to install, V2a still counts toward the minimum of 3 verifiers.

## V3 — AlignScore

- Code: https://github.com/yuh-zha/AlignScore commit `a0936d5afee642a46b22f6c02a163478447aa493` (2024-03-11)
- Checkpoint: https://huggingface.co/yzha/AlignScore file `AlignScore-large.ckpt` (repo revision `8509e78d25bb914939fc585c626500c9b2944249`). RoBERTa-large, 355M. HF reports about 4.9 GB. Fits on GPU or CPU.
- Call: `AlignScore(model='roberta-large', ckpt_path=..., evaluation_mode='nli_sp')`, then `score(contexts=[evidence], claims=[claim])`. Default `evaluation_mode` in code is already `nli_sp`.
- `score()` returns a float. There is no threshold argument. In `evaluate.py` the authors binarize with `score > 0.5` for accuracy, balanced accuracy, F1, and MCC.
- Map: **PASS iff score > 0.5**. Keep the raw score.

## V4 — RAGAS faithfulness NLI prompt on a local open model

- Source inspected: https://github.com/vibrantlabsai/ragas/blob/main/src/ragas/metrics/_faithfulness.py
- Commit: `298b68274234c060deacab3cf5fb52aa3a20e885` (2026-02-24)
- The metric is two LLM calls: a statement generator, then `NLIStatementPrompt`. Faithfulness = fraction of statements with `verdict == 1`.
- NLI instruction, verbatim:

```
Your task is to judge the faithfulness of a series of statements based on a given context. For each statement you must return verdict as 1 if the statement can be directly inferred based on the context or 0 if the statement can not be directly inferred based on the context.
```

- Few-shot examples in that file: John/XYZ University (four statements, verdicts 0, 0, 1, 0) and the photosynthesis/Einstein example (verdict 0). The wrapper must copy those examples unchanged. Full frozen text will be stored under `notes/` when the wrapper is written in Stage 3, from this commit, not from memory.

**Deviation to confirm before Stage 3:** our unit is already one claim. Running the statement generator would rewrite that claim and confound the edit. The planned wrap is the NLI prompt only, with `statements = [claim]` and `context = evidence`. PASS iff `verdict == 1`. Raw score is that 0/1 (and the raw JSON). This is a wrap of the faithfulness judgment, not an edit of its wording.

### Judge checkpoint candidates (not downloaded yet)

| ID | HF on 2026-09-28 | Note |
| --- | --- | --- |
| `Qwen/Qwen3-14B` | 200, not gated, Apache-2.0, revision `40c069824f4251a91eefaf281ebe4c544efd3e18` | Fits one A100-80GB. There is no separate public `Qwen/Qwen3-14B-Instruct` (API returned 401). Qwen3 has a thinking mode; Stage 3 must log whether thinking was disabled. |
| `Qwen/Qwen3-32B` | 200, not gated | Tighter on 80 GB. Fallback if 14B is considered too small. |
| `google/medgemma-27b-text-it` | 200, `gated: auto`, license `other`, revision `5b667cf2ddcf064085bc90952edb35a0edbfb79c` | Not usable until a HF token with access is available. |
| `google/medgemma-27b-it` | 200 | Same gating issue. |

Planned V4 model, unless a token for MedGemma appears: `Qwen/Qwen3-14B`, temperature 0, served with vLLM.

## Binary map (all verifiers)

| Verifier | PASS | Raw score kept |
| --- | --- | --- |
| V1 MedScore provided-evidence | parsed score == 1.0 | raw completion and 0/1 score |
| V2a MiniCheck-Flan-T5-Large | prob > 0.5 | probability |
| V2b Bespoke-MiniCheck-7B | prob > 0.5 | probability |
| V3 AlignScore-large | score > 0.5 | AlignScore float |
| V4 RAGAS NLI on Qwen3-14B | verdict == 1 | raw JSON and 0/1 |

Minimum of 3 verifiers is met by V1, V2a, and V3 even if V2b or V4 cannot be installed.

## Not started

Stages 1–5. No conda env, no model weights, no corpus download, no `results/` numbers.
