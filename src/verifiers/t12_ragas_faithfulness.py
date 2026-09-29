"""T12 RAGAS faithfulness (gpt-4o-mini @ OpenAI via registry)."""

from __future__ import annotations

from verifiers.t12_faithfulness_core import load_for, score_batch_factory

SLUG = "t12_ragas_faithfulness"

load = lambda: load_for(SLUG)
score_batch = score_batch_factory(SLUG)
