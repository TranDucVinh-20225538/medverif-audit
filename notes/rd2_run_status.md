# RD2 run status

**All numbers in `results/journal5/rd2/report.md` are PROVISIONAL (auto labels) until the pharmacist adjudication
(`results/journal5/rd2/qc/rd2_adjudication_sheet.csv`) is done. `rd2_adjudication_key.csv` must not go to the
pharmacist.**

- Run date: 2026-10-02, 12:27–20:45 (UTC+7), operator: Cursor agent on bright92.
- Checkout: `4af0f53` (after `git pull --ff-only`); prereg commit `d3ac9bd254dddba51947259f93e7c4e0b27f83b0`
  (2026-10-02 03:43:10 +0000, "journal5: RD2 prereg (frozen before generation)").
- Preflight: freeze check OK, runner/analysis files changed since freeze: none; weights ok (llama31_8b 0e9e39f249a1,
  qwen25_14b cf98f3b3bbb4, medgemma_27b 5b667cf2ddcf, baichuan_m2_32b 360f684d3cd5, + qwen25_7b, medgemma_4b,
  qwen25_0p5b/1p5b/3b); vLLM 0.8.3; OPENROUTER_API_KEY set; no BLOCKER.
- Unit tests: 15/15 OK with `$MEDVERIF_PYTHON scripts/journal5/test_rd2.py -v`. The documented
  `python -m unittest scripts/journal5/test_rd2.py` fails with ImportError only because a site-packages package named
  `scripts` in the vllm env shadows the repo's `scripts/` (environment issue; no file changed).

## Generation (step 2)

| generator | backend | answers | empty | job / elapsed |
|---|---|---|---|---|
| llama31_8b | vLLM | 960/960 | 0 | 62252_0, 00:54:58 (node002) |
| qwen25_14b | vLLM | 960/960 | 0 | 62252_1, 00:39:28 (node002) |
| medgemma_27b | vLLM | 960/960 | 0 | 62278_2, 00:06:50 (node004) |
| baichuan_m2_32b | vLLM | 960/960 | 0 | 62278_3, 00:06:10 (node004) |
| gpt4o_mini | OpenRouter | 960/960 | 0 | login node, 12:28–12:34 |
| gemma3_27b | OpenRouter | 960/960 | 0 | login node, 12:34–12:47 |

`rd2_generate.py --dry-run`: todo 0 for all 6 generators. max_tokens unchanged (160).

## Extraction (step 3)

5,760 answers -> 5,688 instances; `auto_unit_type` = 459 (unit_error 135 + basis_error 324). Basis check: flag_full
271, flag_strict 134. UNF packs: changed v1 2,678, v2 2,849. Adjudication sheet: 1,845 rows (A 1,411, B 271, C 427).

| class | closed | grounded |
|---|---|---|
| correct | 996 | 2,658 |
| value_error | 665 | 3 |
| match_other_context | 459 | 164 |
| basis_error | 324 | 0 |
| time_ambiguous | 172 | 35 |
| unit_error | 123 | 12 |
| unverifiable | 72 | 5 |
| no_dose | 69 | 3 |

## Scoring (step 4)

- rd2-SMALL 62280 (CPU, cpuverif env, node004): tasks 0–4 COMPLETED in 01:18:37, 01:52:39, 01:33:34, 02:25:20,
  03:17:14. 5 score files x 5,688 rows; UNF v1 (2,678) and UNF v2 (2,849) score files for all 5 checkers.
- rd2-JG 62281 (array 0-6,8-9 = the default `JSPEC` of run_rd2_chain.sh): all 9 judges COMPLETED (4:45–27:33 each), 9 `judges/*__rd2.jsonl` x 5,688 rows.
- rd2-FT 62282 (array 0-7): all 8 FT models COMPLETED on GPU (6:33–10:23 each; no AlignScore CPU fallback);
  `ft/*__rd2_raw.jsonl` x 5,688 plus rd2unf raw/unf/unf_v2 x 2,849.
- API judges (login node, `run_rd2_chain.sh api-judges`, log `results/diagnostics/rd2_run/api_judges.log`): v4_ragas_nli 5,688/5,688 rows (unique), 0 parse fails, 15:17→20:37 incl. one automatic retry, $0.7941; v1_medscore 5,688/5,688 rows (unique), 0 parse fails, 16:15→18:55, $0.1921; `RD4_judges.done` written by the main loop (todo 0, served-model check passed).

## OpenRouter spend

**$1.0557** (cap $3, `MEDVERIF_RD2_MAX_USD=3`, not raised): generation $0.0694, API judges $0.9862 (RAGAS $0.7941 + MedScore $0.1921). Note: the `spent` field printed by `rd_score.py` ($1.1251 at the end) double-counts the generation cost because `rd_spent_usd` sums every jsonl under real_dose/ (per-generator answer files and the merged answers.jsonl); the per-row sum and `run_rd2_chain.sh status` both give $1.0557.

## GPU use

5.76 GPU-hours (sacct, rd2-GEN/JG/FT incl. the two cancelled GEN tasks). All RD2 jobs used 1 GPU each (TP=1).

## Deviations, retries and failures

1. **GPU count.** The prompt says at most 2 GPUs at once. The user explicitly allowed up to 4 once paperB finished;
   the GEN array throttle was raised to 4 with `scontrol update JobId=62252 ArrayTaskThrottle=4` (user QOS vip4 caps
   4 GPUs). In practice RD2 never held more than 2 GPUs at once.
2. **GEN tasks 2/3 cancelled on user request (not failures).** 62252_2 (medgemma_27b) and 62252_3 (baichuan_m2_32b)
   were still loading (no answers written) when the user asked to free GPUs/CPUs for paperB; cancelled at 13:59.
   node002 then went DRAIN ("Kill task failed", root, 13:59:56), most likely because the vLLM processes were stuck in
   NFS I/O (node002 NFS reads ~14 MB/s at the time; `import vllm` took ~15 min there vs 8 s on the login node).
   Not counted as retries. Admin needs to resume node002.
3. **Node override.** With node002 drained, the remaining jobs ran on node004 by overriding the sbatch directive on
   the command line only (`sbatch --exclude=node001,node002 ...`; no job file edited):
   GEN `--array=2,3` (62278), and the three `score --parallel 2` submissions (SMALL 62280, JG 62281 `0-6,8-9%2`,
   FT 62282 `0-7%2`), with `score_jobs.json` written in the same format as `run_rd2_chain.sh score`.
   JG/FT effectively ran one at a time because of the vip4 CPU cap (96 CPUs; SMALL used 80).
4. **API judges in parallel (user-approved).** `run_rd2_chain.sh api-judges` scores RAGAS then MedScore
   sequentially. To save time, v1_medscore was run concurrently by
   `results/diagnostics/rd2_run/medscore_parallel.py` (not committed), which imports `scripts/journal2/rd_score.py`
   and repeats its exact loop for v1_medscore only (same `src/score_jsonl.py` call, 100-row chunks,
   `rd_assert_budget` before every batch against the same $3 cap, same registry model
   mistralai/mistral-small-24b-instruct-2501 @ DeepInfra). It finished all 5,688 rows at 18:55, before the main loop reached v1_medscore (which then found todo 0 at 20:40), so the two processes never contended for the score lock.
5. **api-judges attempt 1 failed** (transient OpenRouter JSONDecodeError inside v4_ragas_nli `llm.generate`);
   `run_rd2_chain.sh` retried automatically after 60 s and resumed by instance_id. No further failures (attempts 2/3 not needed beyond the one retry).
6. No OOM, no BUDGET STOP, no model replacement, no code or prereg change; `prereg/rd2_amendments.md` untouched.
