"""Optional M1 preprocessing for verifier inputs."""

from __future__ import annotations

import os

from quantity_norm import apply_m1_pair


def m1_enabled() -> bool:
    return os.environ.get("MEDVERIF_M1", "").lower() in ("1", "true", "yes")


def verifier_inputs(row: dict) -> tuple[str, str]:
    claim = row.get("claim") or ""
    evidence = row.get("evidence") or ""
    if m1_enabled():
        claim, evidence = apply_m1_pair(claim, evidence)
    return claim, evidence
