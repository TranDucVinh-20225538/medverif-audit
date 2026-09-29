#!/usr/bin/env python3
"""Find malformed thousands-separator dose strings (e.g. 1,2000) in instance claims."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MALFORMED = re.compile(r"\d,\d{4}\b")

PATHS = {
    "main_cpu_early": ROOT / "data/v3/instances_cpu_early.jsonl",
    "main_main": ROOT / "data/v3/instances_main.jsonl",
    "expand_cpu_early": ROOT / "data/expand/instances_cpu_early.jsonl",
    "expand_main": ROOT / "data/expand/instances_main.jsonl",
    "expand_audit": ROOT / "data/expand/v3/instances_audit.jsonl",
}

CONDITIONS = frozenset({"E1-evid", "E1-claim", "E2", "INV-claim"})


def scan(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    hits: list[dict] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cond = row.get("condition") or ""
        if cond not in CONDITIONS and row.get("magnitude") not in ("x2", "x10", "flip", "unit_conversion"):
            if cond not in ("E1-evid", "E1-claim", "E2", "INV-claim"):
                continue
        for field in ("claim", "evidence"):
            text = row.get(field) or ""
            for m in MALFORMED.finditer(text):
                hits.append(
                    {
                        "instance_id": row.get("instance_id"),
                        "base_id": row.get("base_id"),
                        "condition": cond,
                        "magnitude": row.get("magnitude"),
                        "field": field,
                        "token": m.group(0),
                        "snippet": text[max(0, m.start() - 20) : m.end() + 20],
                    }
                )
    return hits


def main() -> None:
    report: dict = {"malformed_pattern": r"\d,\d{4}", "by_path": {}, "main_instance_ids": []}
    all_main_ids: set[str] = set()
    for name, path in PATHS.items():
        hits = scan(path)
        report["by_path"][name] = hits
        if name.startswith("main"):
            all_main_ids.update(h["instance_id"] for h in hits if h.get("instance_id"))
    report["main_instance_ids"] = sorted(all_main_ids)
    report["main_base_ids"] = sorted(
        {
            h["base_id"]
            for h in report["by_path"].get("main_main", []) + report["by_path"].get("main_cpu_early", [])
        }
    )
    expand_hits = (
        report["by_path"].get("expand_main", [])
        + report["by_path"].get("expand_cpu_early", [])
        + report["by_path"].get("expand_audit", [])
    )
    report["expand_base_ids"] = sorted({h["base_id"] for h in expand_hits})
    report["expand_instance_ids"] = sorted({h["instance_id"] for h in expand_hits if h.get("instance_id")})
    report["main_affected"] = report["main_instance_ids"] == []
    out = ROOT / "notes/comma_dose_main_audit.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("main_instance_ids", "main_base_ids", "expand_base_ids")}, indent=2))


if __name__ == "__main__":
    main()
