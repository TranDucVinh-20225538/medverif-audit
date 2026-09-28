#!/usr/bin/env python3
"""PASS rates for prompt×model cells × cohort."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INST = ROOT / "data/pxm/instances_e1evid_e2.jsonl"
RAW = ROOT / "results/raw/pxm"
MANIFEST = ROOT / "data/pxm/manifest.json"
OUT_MD = ROOT / "notes/prompt_x_model_report.md"
OUT_JSON = ROOT / "notes/prompt_x_model_report.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def main() -> None:
    inst = read_jsonl(INST)
    cohort_ids: dict[str, set[str]] = defaultdict(set)
    for r in inst:
        cohort_ids[r.get("pxm_cohort", "?")].add(r["instance_id"])

    cells = json.loads(MANIFEST.read_text()).get("cells", [])
    table: dict[str, dict[str, dict]] = {}
    for cell in cells:
        slug = cell["slug"]
        scores = {row["instance_id"]: row for row in read_jsonl(RAW / f"{slug}.jsonl")}
        table[slug] = {"label": f"{cell['model']} × {cell['prompt']}", "cohorts": {}}
        for cohort, ids in cohort_ids.items():
            hits = []
            for iid in ids:
                rec = scores.get(iid)
                if rec and rec.get("verdict") in ("PASS", "FAIL"):
                    hits.append(int(rec["verdict"] == "PASS"))
            if hits:
                table[slug]["cohorts"][cohort] = {
                    "pass_rate": sum(hits) / len(hits),
                    "n_pass": sum(hits),
                    "n": len(hits),
                }
            else:
                table[slug]["cohorts"][cohort] = {"pass_rate": None, "n_pass": 0, "n": len(ids)}

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(table, indent=2) + "\n")

    lines = [
        "# Prompt × model 2×2 (crossed assignment)",
        "",
        "| cell | model | prompt | E1-unit-evid PASS | E2-x2 PASS |",
        "|---|---|---|---:|---:|",
    ]
    for cell in cells:
        slug = cell["slug"]
        row = table.get(slug, {})
        c = row.get("cohorts", {})

        def fmt(cohort: str) -> str:
            x = c.get(cohort, {})
            if x.get("n", 0) == 0 or x.get("pass_rate") is None:
                return "—"
            return f"{x['pass_rate']:.3f} ({x['n_pass']}/{x['n']})"

        lines.append(
            f"| {slug} | {cell['model']} | {cell['prompt']} | {fmt('E1-unit-evid')} | {fmt('E2-x2')} |"
        )
    lines.extend(
        [
            "",
            "Expected: **E1-unit-evid** → low PASS (FAIL); **E2-x2** → high PASS.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}")


if __name__ == "__main__":
    main()
