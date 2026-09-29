"""OpenRouter RAGAS-NLI with registry slug v6_ragas_mistral_small32."""

import os

os.environ.setdefault("MEDVERIF_V6_VERIFIER_SLUG", "v6_ragas_mistral_small32")

from verifiers.v6_ragas_nli import load, parse_verdict, render, score_batch  # noqa: F401
