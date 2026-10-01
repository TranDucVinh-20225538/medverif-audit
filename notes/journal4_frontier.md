# Journal 4 — frontier API LLMs as fact-check judges on the real-dose answers

Status (2026-10-01 23:40 UTC+7): **code only, not run at scale.** No API key was available on the build box, so the pipeline was
tested end to end with the `mock` provider and with a local fake HTTP server that mimics the OpenAI Responses, OpenAI Chat
Completions, Anthropic Messages and Gemini generateContent formats (including a 400 "temperature not supported" rejection,
503 retries, a 404 fatal stop, the budget stop and resume). Tested on Python 3.8.20 (pydantic 2.10, numpy 1.24) and 3.13. No result files are
committed.

## What is reused (so the numbers line up with the existing judges)

| piece | source (imported, not copied) |
|---|---|
| prompt | `scripts/journal3/j3_ragas_prompt.nli_prompt(evidence, [claim])`, the frozen RAGAS NLI prompt (ragas@298b682). It is vendored verbatim from `src/verifiers/ragas_nli_prompt.py`, and the script checks the two give the same output at startup. Sent as one raw user message with no system prompt and no suffix, the same as the API judges `src/verifiers/v5_ragas_nli.py` / `v6_ragas_nli.py` (GPT-4o-mini / Claude / Llama via OpenRouter) |
| inputs | `scripts/journal3/j3_common.pack_rows("rd")`: evidence = FDA label excerpt, claim = model answer, from `results/journal2/real_dose/instances.jsonl` (1451 rows). The chain-3 local judges got exactly these strings |
| strict parser | `j3_ragas_prompt.parse_verdict` = `src/verifiers/v4_ragas_nli.parse_verdict`. The first statement's `verdict` 1 gives PASS, 0 gives FAIL, anything else gives PARSE_FAIL |
| lenient parser | **New.** The repo had no regex-lenient parser. Rule: strict first; if that gives PARSE_FAIL, take the first match of `"verdict"\s*:\s*"?([01])\b`. The report recomputes it from `raw_output` for the frontier models **and** for the existing generative judges (Llama-3.3-70B RAGAS, the 7 chain-3 vLLM judges), so strict and lenient are defined the same way for every judge. For example, it recovers 123/193 of Qwen2.5-7B's RD parse fails |
| metrics | `scripts/journal3/j3_report.py`: `rd_block`, `RD_GROUPS`, `CB` (drug-clustered bootstrap), `RD_HDR`; card: `judge_card`, `card_metrics`. The output matches `notes/journal3_report.md` exactly for the existing judges (checked with `--report-only --subset all --boot 10000`) |
| labels | `auto_class` from the RD instances; precheck from `qc/ai_precheck_real_dose_unit_errors.csv` (read-only, `#` header lines skipped) |

## Subsets
`--subset all` (1451) | `adjudicable` (1202 = correct + value + unit-type; skips match_other_context / time_ambiguous /
unverifiable, about 17% cheaper; the metrics are identical because those rows are never in any cell) | `flagged47` (unit_error 15 + basis_error 32)
| `true12` (precheck `true_unit_error`) | `smoke` (10 fixed rows: 4 correct, 4 precheck-true, 2 value errors, one per drug).
`--pack card` runs the frozen 958-row DOSE card used in chain 3: C0, the evidence/claim ×2/×10 value edits, the claim-side and
evidence-side ×1000 unit swaps up and down, and conversions. It accepts `all` or `smoke`. With `all` you get the paper card cells (C0-conditional).

## Default models (checked on the provider docs on 2026-10-01)
| provider | default | why | price in/out per 1M tokens | alternatives with known price |
|---|---|---|---|---|
| OpenAI | `gpt-6-astra` | the flagship listed first on developers.openai.com/api/docs/models (released 2026-09-03) | $10 / $50 | `gpt-6.1-sol` ($2/$10), `gpt-6-luna` |
| Anthropic | `claude-opus-5-5` | the docs' "start here" model, Opus tier, released 2026-09-22. `claude-fable-5-1` is the top tier at 2.5× the price | $4 / $20 | `claude-sonnet-5-5` ($2/$10), `claude-fable-5-1` ($10/$50) |
| Google | `gemini-3.1-pro-preview` | the only current Pro model on the Gemini API model list (3.x releases after it are Flash) | $2 / $12 | `gemini-3-flash-preview` ($0.5/$3) |

Every request uses the lowest reasoning setting the model allows (`--effort low`). That maps to OpenAI `reasoning.effort` (Astra has no
none/minimal), Anthropic `output_config.effort` (Opus 5.5 thinking cannot be switched off) and Gemini `thinkingLevel` (3.1 Pro has
no `minimal`). Any other model ID works with `--model X --price-in A --price-out B`.

## Cost estimate (pre-run estimator, `--dry-run`)
Assumptions: prompt tokens = characters / 4 (Claude: characters / 3, because its newer tokenizer is about 35% denser); measured Llama-3 average is 1027 prompt tokens per row.
Output = 450 tokens per row (about 150 visible JSON + about 300 hidden reasoning). Reasoning tokens are billed as output and are the main uncertainty.
The "heavy" column assumes 1200 output tokens per row.

| model | rows | input tokens | est. USD (450 out/row) | USD if 1200 out/row | full-run cap in the wrapper |
|---|---|---|---|---|---|
| gpt-6-astra | 1451 | 1.63 M | **49** | 103 | 75 |
| claude-opus-5-5 | 1451 | 2.18 M | **22** | 44 | 35 |
| gemini-3.1-pro-preview | 1451 | 1.63 M | **11** | 24 | 20 |
| each model, smoke | 10 | ~11-15 k | 0.08-0.34 | ≤0.75 | 1 |
| each model, card (958) | 958 | 1.3-1.7 M | 8 (Gemini) / 14 (Opus) / 35 (Astra) | — | same as RD |

The smoke run gives the real tokens per row. Before the full run starts, the script recomputes the projection from those observed tokens (it uses the larger of
the estimate and the observed projection). If the projection is over `--max-usd`, it refuses to start and makes no calls. During a run it reserves the
worst-case cost (prompt + `max_output_tokens`) for every in-flight request, so the total in the model's jsonl cannot exceed `--max-usd`
(the cap is cumulative across resumes).

## How to run (Mac, or the HPC **login** node; compute nodes have no internet)
```bash
cd medverif-audit && git pull
python3 -m pip install --user 'pydantic>=2' numpy        # Python 3.8 gets pydantic 2.10 / numpy 1.24
export OPENAI_API_KEY=...  ANTHROPIC_API_KEY=...  GEMINI_API_KEY=...   # any subset; providers without a key are skipped
bash jobs/run_frontier_rd.sh --dry-run                  # estimates only
bash jobs/run_frontier_rd.sh --smoke-only               # 10 rows per provider, <= $1 each
bash jobs/run_frontier_rd.sh                            # smoke -> gate -> full 1451 -> reports (resumable; re-run to continue)
#   options: --subset adjudicable | --providers openai,gemini | --with-card ; env MAX_USD_OPENAI=.. OPENAI_MODEL=.. CONCURRENCY=..
# single provider by hand:
python3 scripts/journal4/frontier_judges_rd.py --provider openai --subset smoke
python3 scripts/journal4/frontier_judges_rd.py --provider openai --subset all --max-usd 75 --yes
python3 scripts/journal4/frontier_judges_rd.py --report-only --subset all --boot 10000
```
Outputs: `results/journal4/frontier/<model>.jsonl` holds one row per answer: strict and lenient verdict, raw output, tokens, reasoning tokens, cost,
temperature actually sent, API model and request id. Card runs go to `<model>__card.jsonl`. Reports are `report_rd_<subset>.{md,json}`:
a runs table (parse fails strict/lenient, truncation, tokens, cost); RD metrics strict and lenient for every frontier model, with the paper
checkers/judges and the chain-3 judges recomputed on the same rows; and a per-case table of the 12 precheck-true unit errors (drug, label
dose, answer dose, mechanism, the 7 existing checker verdicts from the precheck csv, the 7 chain-3 judge verdicts, and the frontier verdicts).

## Caveats
- **Temperature.** The script sends temperature 0. GPT-6 Astra (a reasoning model) and Claude Opus 5.5 (thinking always on) are expected to
  reject it. In that case the script logs a warning and continues with the provider default for the rest of the run; the per-row field
  `temperature_sent` is null. Gemini accepts 0, but Google recommends 1.0 for Gemini 3 because lower values can cause looping. Watch the smoke
  parse-fail/truncation counts, or pass `--temperature none`. So these runs are not deterministic in the way the temperature-0 local judges are.
- **Hidden reasoning tokens** count against `--max-output-tokens` (default 2048). If the cap is hit, the visible JSON can be empty, giving PARSE_FAIL
  and incrementing "truncated". The wrapper's smoke gate stops a provider when there are more than 3/10 strict parse fails or any truncation.
- The strict parser is the comparable number. Lenient is an extra column and was not used in the paper.
- Model IDs are served snapshots or aliases on the run date. The `api_model` field records what actually answered.
- RD labels are automatic, and the 12 precheck-true cases were checked by AI, not humans (same caveat as journal chain 3).
- The static prompt prefix is under 1k tokens, so automatic prompt caching likely does not apply. Costs above assume no caching and no Batch API
  (Batch would be 50% cheaper on all three providers, but it is not implemented).
