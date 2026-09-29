"""Optional third-party verifier adapters (MiniCheck, AlignScore, HHEM, LLM judge)."""

from qvc.adapters.base import ScoredRowAdapter, verdicts_from_jsonl

__all__ = ["ScoredRowAdapter", "verdicts_from_jsonl"]
