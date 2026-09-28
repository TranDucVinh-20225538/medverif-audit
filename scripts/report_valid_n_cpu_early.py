#!/usr/bin/env python3
"""Valid-N table for instances_cpu_early.jsonl + H/I/J drop summary."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/data2/hpcshared/medverif-audit")
EARLY = ROOT / "data" / "v3" / "instances_cpu_early.jsonl"
REPORT = ROOT / "data" / "v3" / "qc_v3_apply_report.json"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main() -> None:
    rows = read_jsonl(EARLY)
    valid = [r for r in rows if r.get("valid", True)]
    counts: Counter[str] = Counter()
    by_subset: Counter[str] = Counter()
    for r in valid:
        key = f"{r['type']}|{r['condition']}|{r.get('subset', '?')}"
        counts[key] += 1
        by_subset[r.get("subset", "?")] += 1

    apply_report = json.loads(REPORT.read_text()) if REPORT.is_file() else {}
    out = {
        "instances_cpu_early_total_lines": len(rows),
        "valid_rows": len(valid),
        "invalid_rows": len(rows) - len(valid),
        "by_subset_valid": dict(by_subset),
        "valid_n_type_condition_subset": dict(sorted(counts.items())),
        "rebuilt_bases_H_I_J": apply_report.get("rebuilt_bases", []),
        "rebuilt_bases_n": len(apply_report.get("rebuilt_bases", [])),
        "paraphrase_todo_bases": apply_report.get("paraphrase_todo"),
        "polarity_domain_unclear_c0": apply_report.get("polarity_domain_unclear_c0"),
        "note": "Invalid rows include H-dropped POLARITY flips and other QC invalidations still present in audit export.",
    }
    print(json.dumps(out, indent=2))
    md = ROOT / "notes" / "valid_n_cpu_early.md"
    lines = [
        "# Valid N — `instances_cpu_early.jsonl`",
        "",
        f"- Total lines: **{out['instances_cpu_early_total_lines']}**",
        f"- Valid (scorable): **{out['valid_rows']}**",
        f"- Invalid in file: **{out['invalid_rows']}**",
        "",
        "## By subset (valid)",
        "",
        "| subset | N |",
        "|--------|---|",
    ]
    for k, v in sorted(by_subset.items()):
        lines.append(f"| {k} | {v} |")
    lines += ["", "## type × condition × subset (valid)", "", "| key | N |", "|-----|---|"]
    for k, v in sorted(counts.items()):
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "## Bases rebuilt (H/I/J)",
        "",
        f"Count: **{out['rebuilt_bases_n']}** — see `data/v3/qc_v3_apply_report.json` for IDs.",
        "",
        f"Paraphrase todo bases (G): **{out.get('paraphrase_todo_bases')}**",
        "",
    ]
    md.write_text("\n".join(lines) + "\n")
    print(f"wrote {md}", flush=True)


if __name__ == "__main__":
    main()
