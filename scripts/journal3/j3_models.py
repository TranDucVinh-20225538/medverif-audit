"""Model registries for journal chain 3.

JUDGES: local open LLM judges (vLLM, bf16, temperature 0, seed 42, RAGAS-NLI prompt = the paper's v4/v6 judge prompt).
Array index = position in JUDGES.  Default Slurm array 0-6; index 7 (Qwen2.5-32B, ~66 GB bf16 on one A100-80GB) is
opt-in (`--with-32b`); indices 8-9 (MedGemma-27B-text, Baichuan-M2-32B) are opt-in medical judges.  size_gb = bf16 safetensors on the Hub (approx.; the download step records exact sizes).
FT: chain-1 C2 fine-tunes (checkpoints under .cache/checkpoints/jr_<model>_r<ratio>/) + their bases via the same
library inference path.  Order puts the primary runs first.
"""

JUDGES = [
    # slug,          hf_id,                                params_b, size_gb, family,  gated
    ("qwen25_7b",    "Qwen/Qwen2.5-7B-Instruct",           7.6,  15.2, "qwen2.5", False),
    ("llama31_8b",   "meta-llama/Llama-3.1-8B-Instruct",   8.0,  16.1, "llama3",  True),
    ("medgemma_4b",  "google/medgemma-4b-it",              4.3,   8.6, "gemma3",  True),
    ("qwen25_0p5b",  "Qwen/Qwen2.5-0.5B-Instruct",         0.5,   1.0, "qwen2.5", False),
    ("qwen25_1p5b",  "Qwen/Qwen2.5-1.5B-Instruct",         1.5,   3.1, "qwen2.5", False),
    ("qwen25_3b",    "Qwen/Qwen2.5-3B-Instruct",           3.1,   6.2, "qwen2.5", False),
    ("qwen25_14b",   "Qwen/Qwen2.5-14B-Instruct",         14.7,  29.6, "qwen2.5", False),
    ("qwen25_32b",   "Qwen/Qwen2.5-32B-Instruct",         32.8,  65.5, "qwen2.5", False),
    # medical open LLMs (journal 4, opt-in; packs card + rd): text-only Gemma-3 27B, Qwen2.5-32B-based Baichuan-M2
    ("medgemma_27b", "google/medgemma-27b-text-it",       27.0,  54.0, "gemma3_text", True),
    ("baichuan_m2_32b", "baichuan-inc/Baichuan-M2-32B",   32.8,  65.5, "qwen2.5", False),
]
JUDGE_DEFAULT_ARRAY = "0-6"
JUDGE_PACKS = ("card", "rag", "rd")

FT = [  # (model, tag); tag 'base' = released weights through the same inference path
    ("minicheck_ft5", "r1"), ("alignscore_large", "r1"), ("minicheck_ft5", "base"), ("alignscore_large", "base"),
    ("minicheck_ft5", "r0.5"), ("minicheck_ft5", "r2"), ("alignscore_large", "r0.5"), ("alignscore_large", "r2"),
]
FT_PACKS = [("rd", "raw"), ("ho", "raw"), ("ho", "unf"), ("ho", "unf_v2"), ("rdunf", "raw"), ("rdunf", "unf"), ("rdunf", "unf_v2")]
# AlignScore-large base checkpoint (same pin as scripts/journal/jr_ft_train.py)
AS_REPO, AS_FILE, AS_REV = "yzha/AlignScore", "AlignScore-large.ckpt", "8509e78d25bb914939fc585c626500c9b2944249"
MC_BASE = "lytang/MiniCheck-Flan-T5-Large"


def judge(slug_or_idx):
    if isinstance(slug_or_idx, int) or str(slug_or_idx).isdigit():
        return JUDGES[int(slug_or_idx)]
    for j in JUDGES:
        if j[0] == slug_or_idx:
            return j
    raise KeyError(slug_or_idx)


def ft_name(model: str, tag: str) -> str:
    return "%s_%s" % (model, tag)
