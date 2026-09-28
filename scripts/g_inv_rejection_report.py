#!/usr/bin/env python3
"""Rejection reason counts + subject_reorder listing from para_attempts_g.jsonl."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
sys.path.insert(0, str(ROOT / "src"))

from generate_v3 import OUT, read_jsonl  # noqa: E402

ATTEMPTS = OUT / "para_attempts_g.jsonl"
REPORT_MD = ROOT / "notes" / "g_inv_rejection_report.md"
REPORT_JSON = ROOT / "notes" / "g_inv_rejection_report.json"


def attempt_reason(row: dict) -> str:
    if row.get("rule"):
        return f"rule:{row['rule']}"
    v = row.get("validator") or {}
    if v.get("hard_reject"):
        return f"hard:{v['hard_reject']}"
    if row.get("passed"):
        return "accepted"
    flu = v.get("fluent", "?")
    same = v.get("same_meaning", "?")
    return f"validator:{flu}/{same}"


def main() -> None:
    attempts = read_jsonl(ATTEMPTS)
    if not attempts:
        raise SystemExit(f"no attempts in {ATTEMPTS}")

    todo = {r["base_id"]: r for r in read_jsonl(OUT / "paraphrase_todo.jsonl")}
    reason_counts = Counter()
    by_base: dict[str, list[dict]] = {}
    for row in attempts:
        by_base.setdefault(row["base_id"], []).append(row)
        reason_counts[attempt_reason(row)] += 1

    passed_bases = {bid for bid, rows in by_base.items() if any(r.get("passed") for r in rows)}
    subject_rows: list[dict] = []
    for row in attempts:
        v = row.get("validator") or {}
        if v.get("hard_reject") != "subject_reorder":
            continue
        bid = row["base_id"]
        claim = todo.get(bid, {}).get("claim", "")
        subject_rows.append(
            {
                "base_id": bid,
                "attempt": row.get("attempt"),
                "original": claim,
                "rewrite": row.get("text", ""),
            }
        )

    final_status = Counter()
    for bid, rows in by_base.items():
        if any(r.get("passed") for r in rows):
            final_status["base_pass"] += 1
        else:
            final_status["base_fail"] += 1

    payload = {
        "n_attempt_rows": len(attempts),
        "n_bases": len(by_base),
        "bases_passed": len(passed_bases),
        "attempt_reason_counts": dict(reason_counts.most_common()),
        "final_base_status": dict(final_status),
        "subject_reorder": subject_rows,
    }
    REPORT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    lines = [
        "# G full run — rejection breakdown",
        "",
        f"- Attempt rows: {len(attempts)}",
        f"- Bases touched: {len(by_base)}",
        f"- Bases with ≥1 accepted attempt: {len(passed_bases)}",
        "",
        "## Attempt-level reason counts",
        "",
    ]
    for reason, n in reason_counts.most_common():
        lines.append(f"- `{reason}`: {n}")
    lines += ["", "## subject_reorder (hard rule)", ""]
    if not subject_rows:
        lines.append("(none in attempt log)")
    for item in subject_rows:
        lines += [
            f"### {item['base_id']} (attempt {item['attempt']})",
            "",
            "**Original**",
            "```",
            item["original"],
            "```",
            "",
            "**Rewrite**",
            "```",
            item["rewrite"],
            "```",
            "",
        ]
    REPORT_MD.write_text("\n".join(lines) + "\n")
    print(json.dumps({"md": str(REPORT_MD), "json": str(REPORT_JSON), "subject_reorder_n": len(subject_rows)}))


if __name__ == "__main__":
    main()
