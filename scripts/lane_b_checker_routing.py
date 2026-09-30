#!/usr/bin/env python3
"""Load Lane B checker → env routing (cpuverif vs cpuverif_legacy)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTING_JSON = ROOT / "notes/lane_b_checker_routing.json"


def load_routing() -> dict:
    return json.loads(ROUTING_JSON.read_text())


def cpuverif_checkers() -> list[str]:
    return list(load_routing()["cpuverif_checkers"])


def legacy_checkers() -> list[str]:
    return list(load_routing()["legacy_checkers"])


def legacy_downstream_allowed() -> set[str]:
    return set(load_routing().get("legacy_downstream_allowed") or [])


def save_legacy_downstream_allowed(checkers: list[str]) -> None:
    doc = load_routing()
    doc["legacy_downstream_allowed"] = sorted(checkers)
    ROUTING_JSON.write_text(json.dumps(doc, indent=2) + "\n")
