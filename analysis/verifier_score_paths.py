"""Resolve verifier score jsonl paths (prefer *.llama.jsonl) and enforce registry provenance."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from verifier_registry import assert_row_model, expected_openrouter, load_registry  # noqa: E402

REGISTRY_KEYS = frozenset(load_registry().get("verifiers", {}).keys())


def resolve_verifier_jsonl(raw_dir: Path, verifier: str) -> Path | None:
    """Resolve score jsonl; V4 uses Llama file only (plain ``v4_ragas_nli.jsonl`` excluded)."""
    raw_dir = Path(raw_dir)
    if verifier == "v4_ragas_nli":
        llama = raw_dir / f"{verifier}.llama.jsonl"
        return llama if llama.is_file() else None
    llama = raw_dir / f"{verifier}.llama.jsonl"
    plain = raw_dir / f"{verifier}.jsonl"
    if llama.is_file():
        return llama
    if plain.is_file():
        return plain
    return None


def _registry_lookup(verifier: str, row: dict) -> str | None:
    if verifier in REGISTRY_KEYS:
        return verifier
    slug = (row.get("verifier") or "").strip()
    if slug in REGISTRY_KEYS:
        return slug
    return None


def enforce_provenance(verifier: str, rows: list[dict]) -> None:
    """Fail loudly if a registry-backed score row lacks matching api_model."""
    if os.environ.get("MEDVERIF_SKIP_PROVENANCE_ASSERT", "").lower() in ("1", "true", "yes"):
        return
    for row in rows:
        key = _registry_lookup(verifier, row)
        if not key:
            continue
        if not expected_openrouter(key):
            continue
        assert_row_model(key, row)


def read_verifier_scores(
    raw_dir: Path,
    verifier: str,
    *,
    enforce: bool = True,
) -> list[dict]:
    path = resolve_verifier_jsonl(raw_dir, verifier)
    if path is None:
        return []
    rows = []
    with path.open() as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    if enforce:
        enforce_provenance(verifier, rows)
    return rows
