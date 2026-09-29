"""OpenRouter RAGAS-NLI with registry slug v6_ragas_llama31_8b."""

import os

os.environ.setdefault("MEDVERIF_V6_VERIFIER_SLUG", "v6_ragas_llama31_8b")

from verifiers.v6_ragas_nli import load, parse_verdict, render, score_batch  # noqa: F401
