"""Display names and report family labels for the 19 canonical verifiers."""

from __future__ import annotations

FAMILY_SMALL = "small fine-tuned checkers"
FAMILY_7B = "7B fine-tuned checker"
FAMILY_LLM = "LLM judges"

FAMILY_ORDER: dict[str, int] = {
    FAMILY_SMALL: 0,
    FAMILY_7B: 1,
    FAMILY_LLM: 2,
    "other": 3,
}

FAMILY_COLORS: dict[str, str] = {
    FAMILY_SMALL: "#4c72b0",
    FAMILY_7B: "#55a868",
    FAMILY_LLM: "#c44e52",
    "other": "#888",
}

CANONICAL_VERIFIERS: tuple[str, ...] = (
    "v2a_minicheck",
    "v3_alignscore",
    "v2b_bespoke",
    "t6a_minicheck_roberta",
    "t6a_minicheck_deberta",
    "t6a_alignscore_base",
    "t6a_summac_zs",
    "t6a_summac_conv",
    "t6a_hhem",
    "t6a_granite_guardian",
    "v1_medscore",
    "v1b_medscore",
    "v1c_medscore",
    "v4_ragas_nli",
    "v5_ragas_nli",
    "v6_ragas_gpt4o_mini",
    "v6_ragas_haiku45",
    "v6_ragas_llama31_8b",
    "v6_ragas_mistral_small32",
)

DISPLAY_NAME: dict[str, str] = {
    "v2a_minicheck": "MiniCheck-Flan-T5-Large",
    "v3_alignscore": "AlignScore-large",
    "v2b_bespoke": "Bespoke-MiniCheck-7B",
    "t6a_minicheck_roberta": "MiniCheck-RoBERTa",
    "t6a_minicheck_deberta": "MiniCheck-DeBERTa",
    "t6a_alignscore_base": "AlignScore-base",
    "t6a_summac_zs": "SummaC-ZS",
    "t6a_summac_conv": "SummaC-Conv",
    "t6a_hhem": "HHEM",
    "t6a_granite_guardian": "Granite Guardian",
    "v1_medscore": "Mistral-Small-24B (MedScore)",
    "v1b_medscore": "GPT-4o (MedScore)",
    "v1c_medscore": "GPT-4o-mini (MedScore)",
    "v4_ragas_nli": "Llama-3.3-70B (RAGAS NLI)",
    "v5_ragas_nli": "Claude Sonnet 4.6 (RAGAS NLI)",
    "v6_ragas_gpt4o_mini": "GPT-4o-mini (RAGAS)",
    "v6_ragas_haiku45": "Claude Haiku 4.5 (RAGAS)",
    "v6_ragas_llama31_8b": "Llama-3.1-8B (RAGAS)",
    "v6_ragas_mistral_small32": "Mistral-Small-3.2-24B (RAGAS)",
}

VERIFIER_FAMILY: dict[str, str] = {
    "v2a_minicheck": FAMILY_SMALL,
    "v3_alignscore": FAMILY_SMALL,
    "v2b_bespoke": FAMILY_7B,
    **{v: FAMILY_SMALL for v in CANONICAL_VERIFIERS if v.startswith("t6a_")},
    **{
        v: FAMILY_LLM
        for v in CANONICAL_VERIFIERS
        if v.startswith("v1") or v.startswith("v4") or v.startswith("v5") or v.startswith("v6_")
    },
}


def verifier_display_name(slug: str) -> str:
    return DISPLAY_NAME.get(slug, slug)


def verifier_family(slug: str) -> str:
    return VERIFIER_FAMILY.get(slug, "other")
