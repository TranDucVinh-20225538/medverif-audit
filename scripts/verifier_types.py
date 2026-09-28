"""Verifier type taxonomy for cost/validity analysis."""

from __future__ import annotations

VERIFIER_TYPE: dict[str, str] = {
    "v1_medscore": "LLM-based checker",
    "v1b_medscore": "LLM judge",
    "v1c_medscore": "LLM judge",
    "v4_ragas_nli": "LLM judge",
    "v5_ragas_nli": "LLM judge",
    "v6_ragas_gpt4o_mini": "LLM judge",
    "v6_ragas_haiku45": "LLM judge",
    "v6_ragas_llama31_8b": "LLM judge",
    "v6_ragas_mistral_small32": "LLM judge",
    "v2a_minicheck": "encoder-NLI checker",
    "v3_alignscore": "encoder-NLI checker",
}


def verifier_type(label: str) -> str:
    return VERIFIER_TYPE.get(label, "—")
