#!/usr/bin/env python3
"""Score T9 rows via AlignScore HTTP API + NeMo Guardrails 0.24.1 rail decision logic."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FACT_CHECK_THRESHOLD = 0.5


def fact_check_outcome(accuracy: float) -> tuple[str, bool, dict]:
    """Mirror nemoguardrails.library.self_check.facts.actions._fact_check_outcome."""
    if accuracy < FACT_CHECK_THRESHOLD:
        return "BLOCK", True, {"accuracy": accuracy}
    return "ALLOW", False, {"accuracy": accuracy}


def alignscore_request(api_url: str, evidence: list, response: str) -> float | None:
    """Mirror alignscore_request action (empty evidence → 1.0; HTTP error → None)."""
    if not evidence:
        return 1.0
    if isinstance(evidence, list):
        ev_str = "\n".join(str(x) for x in evidence if x)
    else:
        ev_str = str(evidence or "")
    payload = json.dumps({"evidence": ev_str, "claim": response}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError:
        return None
    except urllib.error.URLError:
        return None
    try:
        return float(body["alignscore"])
    except (KeyError, TypeError, ValueError):
        return None


def rail_decision(
    api_url: str,
    row: dict,
    *,
    fallback_to_self_check: bool = False,
) -> dict:
    """Mirror alignscore_check_facts when fallback_to_self_check is false (default)."""
    evidence = row.get("relevant_chunks")
    if evidence is None:
        ev = row.get("evidence") or ""
        evidence = [ev] if ev else []
    response = row.get("bot_message") or row.get("claim") or ""
    score = alignscore_request(api_url, evidence, response)
    if score is None:
        if fallback_to_self_check:
            return {
                "alignscore": None,
                "decision": "FALLBACK_SELF_CHECK",
                "blocked": None,
                "note": "self_check not run in batch scorer",
            }
        verdict, blocked, meta = fact_check_outcome(1.0)
        return {"alignscore": None, "decision": verdict, "blocked": blocked, **meta, "fallback": "allow_1.0"}
    verdict, blocked, meta = fact_check_outcome(score)
    return {"alignscore": score, "decision": verdict, "blocked": blocked, **meta}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--endpoint",
        default=os.environ.get("T9_ALIGN_SCORE_ENDPOINT", "http://127.0.0.1:5000/alignscore_base"),
    )
    ap.add_argument("--fallback-self-check", action="store_true")
    args = ap.parse_args()

    rows = read_jsonl(args.instances.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        for row in rows:
            dec = rail_decision(
                args.endpoint,
                row,
                fallback_to_self_check=args.fallback_self_check,
            )
            out = {**row, **dec, "endpoint": args.endpoint, "threshold": FACT_CHECK_THRESHOLD}
            handle.write(json.dumps(out, ensure_ascii=False) + "\n")
    print(json.dumps({"n": len(rows), "out": str(args.out)}, indent=2))


if __name__ == "__main__":
    main()
