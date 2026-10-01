# Environment divergence: T15-OOD T18 base leg (appendix)

**Finding: root cause found, and it is not a numerical environment effect.** The withdrawn T18 "base" numbers
(`results/raw/t15/base_t18_ood.jsonl`, vllm env, job 61633) were produced with the **fine-tuned T15 weights**,
not stock MiniCheck-RoBERTa-Large.

## Symptom

- vllm-env T15-OOD base vs earlier T18 MiniCheck-RoBERTa scores: 66/74 verdict agreement on identical text
  (e.g. T180012 unit_swap: 0.005 FAIL vs 0.897 PASS).
- Reference-env rescoring (cpuverif, job 61635): base T18 **97/106** vs the vllm-env file; ft T18 **106/106**;
  ft T24b **202/202**. cpuverif base reproduces the earlier `results/raw/t18/t6_minicheck_roberta.jsonl`
  **74/74** (max |Δscore| 2.9e-6).

## Checks, in the requested order (probe: `scripts/env_divergence_probe.py`, job 61651, 8 disagreeing + 4 agreeing rows, CPU in both envs)

| Check | cpuverif | vllm | Result |
| --- | --- | --- | --- |
| MiniCheck library / sentence splitting | `.cache/src/MiniCheck` @ `b58b9fa`, nltk 3.10.3 | same | **identical** sentence lists and chunks (sha1 + text) on 12/12 rows |
| Library versions | torch 2.14.0+cpu, transformers 5.17.0, tokenizers 0.23.2 | torch 2.6.0+cu124, transformers 4.51.2, tokenizers 0.21.1 | differ, but no effect on outputs (below) |
| Tokenizer / max_length / truncation | `RobertaTokenizer`, model_max_length 512, max_model_len 512 | `RobertaTokenizerFast`, 512, 512 | **identical** input_ids on 12/12 rows (73–189 tokens, none truncated) |
| dtype | float32, CPU | float32, CPU | same; logits identical to 2 d.p. |
| Unicode | 7/8 disagreeing rows pure ASCII; 1 (T180070) has Czech diacritics; agreeing controls include ó and – | — | not associated |
| Scores, one row at a time | T180012 0.897 | T180012 **0.897** | vllm env reproduces cpuverif on all 12 rows |

Because the vllm env gives the reference scores when each row is run on its own, the divergence had to come from the batch job.

## Root cause

`src/verifiers/minicheck_roberta_lib._patch_roberta_ckpt` (used to load the T15 fine-tuned checkpoint) replaces
`minicheck.inference.Inferencer.__init__` **process-wide** so that `roberta-large` loads `.cache/checkpoints/t15_roberta/best`.
`scripts/t15_eval.py --pack-leg both` scores packs in `PACKS` order, base then ft, in **one process**. In job 61633
(`--packs t24b,t18_ood`) the order was: T24b base (stock) → T24b ft (**patch installed**) → T18 base (stock loader,
now silently loading ft weights) → T18 ft. Evidence: vllm `base_t18_ood` scores are **byte-identical to `ft_t18_ood` on 106/106 rows**,
while every row is labelled `verifier: t6a_minicheck_roberta`. The 9 base disagreements are 8 rows where stock and ft differ
in verdict plus T180043 ×10.

## Scope check (other T15 base files, same test: base score == ft score)

`base_main_dose` 0/996, `base_t7` 0/214, `base_t17` 0/540, `base_t14` 0/227, `base_t18` 0/736, `base_t18_medical_expand` 0/213,
`base_t24b` 0/202, `base_aggrefact_test` 0/29320 → **only `base_t18_ood` is contaminated**. (In job 61620, `t17` precedes `t7`
in `PACKS` and `ft_t17` was already complete, so the ft loader never ran before a base leg.)

## Fix and policy

- Guard added in `src/verifiers/t6a_minicheck.load`: raises if the T15 checkpoint patch is active in the process (verified).
- All T15/MiniCheck numbers now come from the reference env **cpuverif** (`results/raw/t15_cpuverif/`, `scripts/t15_score_cpuverif.py`,
  one leg per process). The vllm-env T15 files are superseded.
- Library-version differences between cpuverif and vllm had no measurable effect on MiniCheck-RoBERTa here (identical ids and logits).
