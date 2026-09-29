"""Load canonical OpenRouter model pins from notes/openrouter_verifiers.json."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "notes" / "openrouter_verifiers.json"


def load_registry() -> dict:
    if not REGISTRY.is_file():
        raise FileNotFoundError(REGISTRY)
    return json.loads(REGISTRY.read_text())


def registry_key(verifier_module: str, row: dict | None = None) -> str:
    import os

    if verifier_module == "v6_ragas_nli":
        if row and row.get("verifier"):
            return str(row["verifier"])
        return os.environ.get("MEDVERIF_V6_VERIFIER_SLUG", "v6_ragas_nli")
    return verifier_module


def expected_openrouter(verifier_module: str, row: dict | None = None) -> dict | None:
    """Return {openrouter_model, provider} for verifiers.* module name."""
    reg = load_registry()
    key = registry_key(verifier_module, row)
    return reg.get("verifiers", {}).get(key)


def apply_env_defaults(verifier_module: str) -> None:
    """Set MEDVERIF_* env vars from registry when not already set."""
    import os

    key = registry_key(verifier_module)
    spec = expected_openrouter(verifier_module)
    if not spec:
        return
    env_map: dict[str, tuple[str, str]] = {
        "v1_medscore": ("MEDVERIF_V1_OPENROUTER_MODEL", "MEDVERIF_V1_PROVIDER"),
        "v4_ragas_nli": ("MEDVERIF_V4_OPENROUTER_MODEL", "MEDVERIF_V4_PROVIDER"),
        "v1b_medscore": ("MEDVERIF_V1B_OPENROUTER_MODEL", "MEDVERIF_V1B_PROVIDER"),
        "v5_ragas_nli": ("MEDVERIF_V5_OPENROUTER_MODEL", "MEDVERIF_V5_PROVIDER"),
        "v6_ragas_gpt4o_mini": ("MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
        "v6_ragas_haiku45": ("MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
        "v6_ragas_llama31_8b": ("MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
        "v6_ragas_mistral_small32": ("MEDVERIF_V6_OPENROUTER_MODEL", "MEDVERIF_V6_PROVIDER"),
        "t12_ragas_faithfulness": ("MEDVERIF_T12_RAGAS_MODEL", "MEDVERIF_T12_RAGAS_PROVIDER"),
        "t12_deepeval_faithfulness": ("MEDVERIF_T12_DEEVAL_MODEL", "MEDVERIF_T12_DEEVAL_PROVIDER"),
        "t12_trulens_groundedness": ("MEDVERIF_T12_TRULENS_MODEL", "MEDVERIF_T12_TRULENS_PROVIDER"),
    }
    pair = env_map.get(key) or env_map.get(verifier_module)
    if not pair:
        return
    model_key, prov_key = pair
    if not os.environ.get(model_key):
        os.environ[model_key] = spec["openrouter_model"]
    if not os.environ.get(prov_key):
        os.environ[prov_key] = spec.get("provider") or ""


def assert_row_model(verifier_module: str, row: dict) -> None:
    """Called from score_jsonl after every OpenRouter batch for registry verifiers."""
    spec = expected_openrouter(verifier_module, row)
    if not spec:
        return
    model = (row.get("api_model") or row.get("model") or "").strip()
    if not model:
        raise RuntimeError(
            f"{verifier_module}: missing api_model on scored row "
            f"(registry requires {spec['openrouter_model']!r})"
        )
    want = spec["openrouter_model"].lower()
    if want not in model.lower():
        raise RuntimeError(
            f"{verifier_module}: api_model {model!r} != registry {spec['openrouter_model']!r}"
        )
