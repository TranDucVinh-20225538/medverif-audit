#!/usr/bin/env python3
"""Prompt×model 2×2: E1-unit-evid (115) + E2 main x2 (117)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
E2 = ROOT / "data/e2/instances_main_x2.jsonl"
OUT = ROOT / "data/pxm/instances_e1evid_e2.jsonl"
MANIFEST = ROOT / "data/pxm/manifest.json"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    evid = [r for r in read_jsonl(T7) if r.get("condition") == "E1-unit-evid"]
    e2 = read_jsonl(E2)
    rows = []
    for r in evid:
        row = dict(r)
        row["pxm_cohort"] = "E1-unit-evid"
        rows.append(row)
    for r in e2:
        row = dict(r)
        row["pxm_cohort"] = "E2-x2"
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    MANIFEST.write_text(
        json.dumps(
            {
                "n_total": len(rows),
                "n_e1_unit_evid": len(evid),
                "n_e2_x2": len(e2),
                "cells": [
                    {
                        "slug": "pxm_gpt4o_ragas",
                        "model": "openai/gpt-4o",
                        "provider": "OpenAI",
                        "prompt": "RAGAS-NLI",
                        "verifier_module": "v4_ragas_nli",
                    },
                    {
                        "slug": "pxm_sonnet_medscore",
                        "model": "anthropic/claude-sonnet-4.6",
                        "provider": "Anthropic",
                        "prompt": "MedScore-provided",
                        "verifier_module": "v1b_medscore",
                    },
                ],
                "budget_usd": 2.0,
            },
            indent=2,
        )
        + "\n"
    )
    print(json.dumps({"out": str(OUT), "n": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
