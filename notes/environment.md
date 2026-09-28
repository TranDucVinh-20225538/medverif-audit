# Environment — medverif-audit

## AlignScore (`.cache/src/AlignScore`)

| Patch | File | Reason |
|-------|------|--------|
| `AdamW` import | `alignscore/model.py` | `transformers` no longer exports `AdamW` from top level; use `torch.optim.AdamW`. |
| `sklearn` import stub | `alignscore/model.py` | Inference-only CPU path may lack `scikit-learn`; stub `f1_score` (training metric only, not used in `nli_sp` scoring). |
| `load_from_checkpoint` | `alignscore/inference.py` | PyTorch Lightning 2.x: call `BERTAlignModel.load_from_checkpoint(...)` on the class, not on an instance. |
| *(none for splitter)* | `alignscore/inference.py` | **Upstream** loads `en_core_web_sm` in `__init__`. **`nli_sp`** scoring (our mode) uses **NLTK `sent_tokenize`** in `inference_per_example` — same as [upstream AlignScore](https://github.com/yuh-zha/AlignScore). Install: `scripts/install_en_core_web_sm.sh`. |

Parity check (20 pairs): `scripts/alignscore_parity_check.py` → `notes/alignscore_parity_20.json`.

## OpenRouter (V1, V4, G paraphrase pilot)

- API key: **`OPENROUTER_API_KEY`** (never commit).
- Enable: **`MEDVERIF_USE_OPENROUTER=1`** for `score_jsonl.py` / verifiers.
- Optional: **`MEDVERIF_OPENROUTER_PROVIDER`** (pinned provider, `allow_fallbacks=false`).
- V1 model: `mistralai/mistral-small-24b-instruct-2501` (override: `MEDVERIF_V1_OPENROUTER_MODEL`).
- V4 default (GPU): `Qwen/Qwen3-14B` with `enable_thinking=false`.
- V4 OpenRouter probe: `scripts/v4_openrouter_probe.py` → `notes/v4_openrouter_probe.json` (20 items × configs; gate: no `reasoning`, JSON in `content`, completion_tokens ≤150, parse ≥95%).
- **V4 OpenRouter deviation (2026-09-28):** Qwen3-14B on DeepInfra returns empty `content` + long `reasoning` even with `reasoning.enabled=false` and `/no_think`. If probe winner is not `no_think_suffix_deepinfra`, production V4 uses **`meta-llama/llama-3.3-70b-instruct`** (provider **DeepInfra**, same RAGAS-NLI prompt + `parse_verdict`). Chat template: **`Llama3InstructTokenizer`** (no gated HF download) unless `HF_TOKEN` + `MEDVERIF_V4_LLAMA_STRING_TEMPLATE=0`.
- G pilot: generator `qwen/qwen-2.5-72b-instruct`, validator `microsoft/phi-4` → `qc/qc_samples_inv_v3.md` (PI OK before full G).
- Long runners: `jobs/lib/flock.sh` (`medverif_acquire_lock`) on `run_v1_openrouter_full.sh`, `run_g_pilot.sh`, `run_v4_probe.sh`, `run_v4_openrouter_full.sh`, `run_cpu_early_login.sh`. Dedupe: `python3 scripts/dedupe_raw_jsonl.py`.
- Reliability: `scripts/openrouter_reliability.py` (smoke 5, then 50×2 agreement).

## CPU scoring (login)

```bash
jobs/run_cpu_early_login.sh
```

Uses `nice -n 19`, `OMP_NUM_THREADS=4`, `MKL_NUM_THREADS=4`.

## SLURM GPU wave (61407–61409)

Held intentionally; OpenRouter replaces GPU for V1/V4/G. Release only if resuming local vLLM: `scontrol release 61407 61408 61409`.
