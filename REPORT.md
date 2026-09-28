# REPORT

**Daily status (2026-09-28):** **61394 TIMEOUT** at 3h (vLLM `torch.compile` + Qwen↔Phi reloads); `para_attempts.jsonl` kept, **no QC v3**. **Parallel wave (`submit_parallel.sh`):** **`stage3_v1`** + **`label_v3b`** + **`gpu_early`** (V2a GPU; V3 skipped if AlignScore/`AdamW`); **`stage4`** `afterok` V1+gpu_early → `phenomenon_checklist.md`. **V4:** Qwen3-14B **not ready** (3 missing shards, 3 `.incomplete`) — see `notes/qwen3_14b_download.json`. **61388→61394:** 61388 stuck node002; 61394 resubmit node004 then timed out. **Git:** local only.

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

## PI manual review (2026-09-28)

Files: `qc/inv_manual_review.csv` (merged `PI_ok`), `qc/unit_naturalness.csv` (`natural`), archive `qc/inv_manual_review_PI_ok_labels.csv`.

Validation: **95** labeled rows, key `(base_id, type, mechanism)`, **0** unmatched keys. Values **Y/N** only on reviewed rows.

| Slice | Y | N |
| --- | ---: | ---: |
| POLARITY / template | 34 | 8 |
| POLARITY / llm | 9 | 4 |
| DOSE / llm (sample=1 only) | 23 | 17 |
| Unit naturalness (58 bases) | 22 | 36 |

**Analysis filters:** INV enters only if `PI_ok=Y` (accepted: template POL **34**, llm POL **9**, llm DOSE **23**). DOSE llm rows with `sample=0` are excluded (not reviewed). INV-unit also reported for `natural=Y` subset (**22** bases).

**LLM paraphrase human acceptance** (despite passing generation rules + Gemini validator): DOSE **23/40 = 58%**; POLARITY **9/13 ≈ 69%**. Many rule-valid paraphrases are not meaning-preserving under human PI review.

## Scoring progress (2026-09-28)

Valid instances (main + threshold): **1258**. Unique scored ids in `results/raw/`:

| Verifier | Scored | Complete? |
| --- | ---: | --- |
| v1_medscore | 1080 | no (178 pending) |
| v4_ragas_nli | 419 | no (839 pending) |
| v2a_minicheck | 1403 | yes (≥ main+thr union) |
| v3_alignscore | 1403 | yes |

When V1 and V4 reach **1258** each (main + threshold + agreement subsample as queued), run `scripts/build_full_v1v4.py` → `results/tables/full_v1v4.md` (INV gated on `PI_ok=Y`; INV-unit also `natural=Y`; POL E1/E2 gated on `qc/e1_pol_review.csv` flip PI_ok=Y, **n=26**).

## Threats to validity

**QC rules B/H vs `valid=true` on C0.** Rules B (`flip_scope:*` from hedge terms in the polarity clause, e.g. `relatively`, `neither`) and H (`adjunct_after_predicate`, `predicate_not_at_clause_end`, `flip_not_intervention`, etc.) apply in `polarity_flip_allowed()` and set **`flip_block` on the base**. `apply_validity` marks only **`magnitude=flip`** instances (E1-evid, E1-claim, E2) invalid — **not** C0 or INV-claim. So bases such as **P0009**, **P0017** (rule B) and **P0049**, **P0060**, **P0066**, **P0069**, **P0076**, **P0094**, **P0104**, **P0143** (rule H) correctly remain **`valid=true` on C0** while their flip rows carry `invalid_reason`. Earlier notes that “rule B blocked the base” were imprecise.

**Human vs automatic gates.** Automatic QC is a **pre-filter**; reported paired POL E1/E2 analyses use **`qc/e1_pol_review.csv` PI_ok=Y (26 bases)**. Only **12/26** currently have valid flip instances in `instances_main.jsonl` / `cpu_early` (scores exist for those); the other 14 human-accepted flips still need instance/score alignment (audit flip text exists but `valid=false`).

**INV LLM paraphrase.** High rule+validator pass rate but low human PI_ok (DOSE 58%, POL 69%) — see PI manual review section.

**T3 rule-based INV families (2026-09-29).** Generator produced **114** claim-side edits (frequency / route / numerals / format). PI review of `qc/inv_families_sample.csv` → **`qc/inv_claim_PI_ok_labels.csv`** (**82** rows keyed by `instance_id`: **36 Y / 46 N**). **Analysis and scoring use `valid=true` ∧ `PI_ok=Y` only (n=36):** frequency **14 Y** (all **22** frequency rows reviewed), route **22 Y** (all **29** route rows reviewed). Families **`inv_numerals`** (**0/30** reviewed Y; generator breaks: mid-sentence capitalization, decimals/hyphenated names, mixed ranges, sentence-initial digits) and **`inv_format`** (**1** row, N) are kept in **`data/v3/instances_inv_families_audit.jsonl`** with **`valid=false`, `invalid_reason=family_dropped`**. Remaining frequency/route **N** rows use **`pi_review_n`**. Representative frequency **N** failure modes: **range truncation** (e.g. “one to qid”), **duplicated “daily”**, **“20 mg bid of X”** (dose-adjacent frequency edits). T3 OpenRouter scoring (V1b, V5, T6-B) and node30 (V2a, V3, T6-A) skip invalid rows via `score_jsonl` **`valid`** filter.
