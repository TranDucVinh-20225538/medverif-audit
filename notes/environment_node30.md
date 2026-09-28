# Environment — node30 (V2 MiniCheck / V3 AlignScore only)

Host: `node30`. Date: 2026-09-28. GPU jobs here do **not** use SLURM.

## GPU (do not reset)

`nvidia-smi` in this session sees **only GPU 0**. PCI lists 8× A100-SXM4-80GB; indices 1–7 are `No devices were found`.

| | GPU 0 |
|---|---|
| Name | NVIDIA A100-SXM4-80GB |
| Total | 81920 MiB |
| Used (snapshot before scoring) | ~71821 MiB |
| **Free** | **~9 GB** |
| Util | 0% (zombie holders) |

Holders `1210895` (~70 GB) and `1196180` (~1.7 GB) are **not in this namespace**. Not killed. `export CUDA_VISIBLE_DEVICES=0`.

**V2b skipped:** `bespokelabs/Bespoke-MiniCheck-7B` needs ~14 GB+ fp16 / vLLM. It does not fit in ~9 GB free. Not downloaded.

## Input

`data/v3/instances_cpu_early.jsonl`

- sha256: `069d1a8af25921eb76081cc7e118e467c41928d28c55e293c7c9ec04e1c68956`
- bytes: 2911059
- lines / valid: **1216** (1002 `main` + 214 `threshold`) — matches `notes/valid_n_cpu_early.md`

## Code (original, no patches)

| | Commit |
|---|---|
| MiniCheck clone | `b58b9fa69acbd1015ec970fa65dd752413a053d2` |
| AlignScore clone | `a0936d5afee642a46b22f6c02a163478447aa493` |

AlignScore **not** patched (`AdamW` still `from transformers import AdamW`; `load_from_checkpoint` on the Lightning 1.x instance; `nli_sp` uses **NLTK `sent_tokenize`** in `inference_per_example`; `__init__` still loads spaCy `en_core_web_sm`).

HPC patches in `notes/environment.md` are **not** applied on node30.

## Env

Path: `/root/medverif-audit/.venv` (Python 3.10.18).

| Package | Version |
|---|---|
| torch | 1.13.1+cu117 (`cuda True`, 1 visible device) |
| transformers | 4.30.2 (`AdamW` import OK) |
| pytorch-lightning | 1.9.5 |
| numpy | 1.24.4 |
| accelerate | 0.20.3 |
| datasets | 2.14.7 |
| scikit-learn | 1.3.2 |
| scipy | 1.10.1 |
| nltk | 3.8.1 |
| spacy | 3.5.4 |
| en_core_web_sm | 3.5.0 |
| huggingface_hub | 0.16.4 |
| protobuf | 3.20.0 (AlignScore pin `<=3.20`) |
| sentencepiece | 0.1.99 |
| setuptools | 69.5.1 (84.x dropped `pkg_resources`, needed by lightning-fabric) |

Pins follow AlignScore `pyproject.toml` (`torch>=1.12.1,<2`, `pytorch_lightning>=1.7.7,<2`) so original code runs. After `pip install -e AlignScore` replaced CUDA torch with CPU `1.13.1`, **reinstalled `torch==1.13.1+cu117`**. MiniCheck `pip -e` had pulled torch 2.14; that was reverted.

`python -m spacy download en_core_web_sm` 404'd (`-en_core_web_sm` URL). Installed wheel `en_core_web_sm-3.5.0`.

## Verifiers

| ID | Model | Rule | Precision |
|---|---|---|---|
| V2a | `lytang/MiniCheck-Flan-T5-Large` rev `96eafd01cee2d16cf81aaa2fb226b14f422a37b3` | PASS iff `pred_label==1` (`prob>0.5`) | fp32 |
| V3 | AlignScore-large ckpt `yzha/AlignScore` rev `8509e78d25bb914939fc585c626500c9b2944249`, backbone `FacebookAI/roberta-large` rev `722cf37b1afa9454edce342e7895e588b6ff1d59` | `evaluation_mode=nli_sp`, PASS iff `score>0.5` | fp32 |
| V2b | not run | — | — |

### Thresholds used for the logged `verdict` (raw `score` is stored unchanged)

Binarization is for the `verdict` field only. Sweep later from `score`.

| ID | Threshold | Inequality | Source |
|---|---|---|---|
| V2a | **0.5** | `pred_label = 1 if prob > 0.5 else 0` | MiniCheck repo (Tang et al., EMNLP 2024, [arXiv:2404.10774](https://arxiv.org/pdf/2404.10774.pdf)): `.cache/src/MiniCheck/minicheck/minicheck.py:151` `pred_label = [1 if prob > 0.5 else 0 for prob in max_support_prob]`. Same cut in `minicheck/inference.py:499` (`1 if final_score > 0.5 else 0`). Docstring L128–129: `0` unsupported / `1` supported. |
| V3 | **0.5** | PASS iff AlignScore `> 0.5` | AlignScore repo (Zha et al., ACL 2023, [arXiv:2305.16739](https://arxiv.org/abs/2305.16739)): `.cache/src/AlignScore/src/alignscore/model.py:204` `pred = [int(align_prob>0.5) for align_prob in output]`. Same default in `evaluate.py:216` (`m>0.5` for accuracy), `:218` (`thres=0.5` for balanced accuracy), `:222` (F1), `:237` (MCC). Paper/leaderboard report AUC-ROC on the continuous score; **0.5 is the official repo binarization**, not a paper-tuned operating point. `nli_sp` is the library default (`alignscore.py:5`). |

Runner: `scripts/run_node30_v2v3.py` (batch 8, halve on OOM, flock `jobs/locks/{v2a,v3}.lock`, resume by `instance_id`). Sequential V2 then V3. Does not call V1/V4, data gen, or SLURM.

Outputs: `results/raw/v2a_minicheck.jsonl`, `results/raw/v3_alignscore.jsonl`.
