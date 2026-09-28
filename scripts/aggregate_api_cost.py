#!/usr/bin/env python3
"""Recompute results/api_cost.json from api_* fields in raw JSONL verdict files."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOB = [
    ROOT / "results" / "raw" / "v1_medscore.jsonl",
    ROOT / "results" / "raw" / "v4_ragas_nli.jsonl",
    ROOT / "results" / "raw_threshold" / "v1_medscore.jsonl",
    ROOT / "results" / "raw_threshold" / "v4_ragas_nli.jsonl",
]


def main() -> None:
    calls = []
    for path in GLOB:
        if not path.is_file():
            continue
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                if row.get("api_request_id") is None and row.get("api_total_tokens") is None:
                    continue
                calls.append({
                    "source": str(path.relative_to(ROOT)),
                    "instance_id": row.get("instance_id"),
                    "model": row.get("api_model"),
                    "provider": row.get("api_provider"),
                    "request_id": row.get("api_request_id"),
                    "prompt_tokens": row.get("api_prompt_tokens"),
                    "completion_tokens": row.get("api_completion_tokens"),
                    "total_tokens": row.get("api_total_tokens"),
                    "cost_usd": row.get("api_cost_usd"),
                })
    total_cost = sum(c.get("cost_usd") or 0.0 for c in calls)
    total_tokens = sum(c.get("total_tokens") or 0 for c in calls)
    out = {
        "source": "aggregate from raw jsonl api_* fields",
        "n_calls": len(calls),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "calls": calls,
    }
    dest = ROOT / "results" / "api_cost.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"wrote": str(dest), "n_calls": len(calls), "total_cost_usd": total_cost}))


if __name__ == "__main__":
    main()
