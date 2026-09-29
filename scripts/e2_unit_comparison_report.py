#!/usr/bin/env python3
"""E2-unit PASS vs E2-x2 PASS vs E1-unit-evid FAIL (per verifier)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

E2_UNIT = ROOT / "data/e2/instances_e2_unit_t7.jsonl"
E2_X2 = ROOT / "data/e2/instances_main_x2.jsonl"
T7 = ROOT / "data/t7/instances_e1_unit.jsonl"
RAW_E2U = ROOT / "results/raw/e2_unit"
RAW_E2M = ROOT / "results/raw/e2_main"
RAW_T7 = ROOT / "results/raw/t7"
RAW = ROOT / "results/raw"
T6A = ROOT / "notes/t6a_eco_checkers.json"
OUT = ROOT / "notes/e2_unit_verifier_comparison.md"
OUT_JSON = ROOT / "notes/e2_unit_verifier_comparison.json"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.open() if line.strip()]


def _slug(path: Path) -> str | None:
    name = path.name
    if ".legacy." in name or "quarantine" in name:
        return None
    if name.endswith(".llama.jsonl"):
        return name[: -len(".llama.jsonl")]
    if name.endswith(".jsonl"):
        return name[: -len(".jsonl")]
    return None


def score_dirs() -> list[Path]:
    return [RAW_E2U, RAW_E2M, RAW, RAW_T7, ROOT / "results/raw/t6b/full"]


def merged_scores(slug: str) -> dict[str, str]:
    m: dict[str, str] = {}
    paths: list[Path] = []
    if T6A.is_file():
        t6a = {c["id"]: c["jsonl"] for c in json.loads(T6A.read_text()).get("checkers", [])}
        if slug in t6a:
            for d in score_dirs():
                cand = d / t6a[slug]
                if cand.is_file():
                    paths.append(cand)
    if slug == "v2b_bespoke":
        for name in ("t6_bespoke_minicheck.jsonl", "v2b_bespoke.jsonl"):
            for d in score_dirs():
                cand = d / name
                if cand.is_file():
                    paths.append(cand)
    for d in score_dirs():
        for cand in (d / f"{slug}.llama.jsonl", d / f"{slug}.jsonl"):
            if cand.is_file():
                paths.append(cand)
    seen: set[Path] = set()
    for path in paths:
        if path in seen:
            continue
        seen.add(path)
        for row in read_jsonl(path):
            iid = row.get("instance_id")
            if iid:
                m[iid] = row.get("verdict") or ""
    return m


def all_slugs() -> list[str]:
    slugs: set[str] = set()
    for d in score_dirs():
        if d.is_dir():
            for p in d.glob("*.jsonl"):
                s = _slug(p)
                if s:
                    slugs.add(s)
    if T6A.is_file():
        slugs.update(c["id"] for c in json.loads(T6A.read_text()).get("checkers", []))
    slugs.add("v2b_bespoke")
    return sorted(slugs)


def rate(ids: list[str], scores: dict[str, str], want: str) -> tuple[float | None, int, int]:
    hits = []
    for iid in ids:
        v = scores.get(iid)
        if v and v != "PARSE_FAIL":
            hits.append(int(v == want))
    if not hits:
        return None, 0, len(ids)
    return sum(hits) / len(hits), len(hits), len(ids)


def main() -> None:
    t7_bases = {r["base_id"] for r in read_jsonl(T7)}
    e2_unit_ids = [r["instance_id"] for r in read_jsonl(E2_UNIT)]
    e1_evid_ids = [r["instance_id"] for r in read_jsonl(T7) if r.get("condition") == "E1-unit-evid"]
    e2_x2_ids = [
        r["instance_id"]
        for r in read_jsonl(E2_X2)
        if r.get("base_id") in t7_bases and r.get("condition") == "E2"
    ]

    table = {}
    for v in all_slugs():
        sc = merged_scores(v)
        if not sc:
            continue
        pu, nu, tu = rate(e2_unit_ids, sc, "PASS")
        px, nx, tx = rate(e2_x2_ids, sc, "PASS")
        fe, ne, te = rate(e1_evid_ids, sc, "FAIL")
        if nu == 0 and nx == 0 and ne == 0:
            continue
        table[v] = {
            "e2_unit_pass": pu,
            "e2_unit_n": nu,
            "e2_x2_pass": px,
            "e2_x2_n": nx,
            "e1_evid_fail": fe,
            "e1_evid_n": ne,
        }

    OUT_JSON.write_text(json.dumps(table, indent=2) + "\n")

    def fmt(x):
        return f"{x:.3f}" if x is not None else "—"

    lines = [
        "# E2-unit vs E2-x2 vs E1-unit-evid (T7 bases)",
        "",
        f"- **E2-unit:** {len(e2_unit_ids)} instances (`instances_e2_unit_t7.jsonl`); expected PASS.",
        f"- **E2-x2:** {len(e2_x2_ids)} main×2 rows on T7 bases.",
        f"- **E1-unit-evid:** {len(e1_evid_ids)} T7 instances; column = FAIL rate.",
        "",
        "| verifier | E2-unit PASS | E2-x2 PASS | E1-unit-evid FAIL |",
        "|---|---:|---:|---:|",
    ]
    for v, c in sorted(table.items()):
        lines.append(
            f"| {v} | {fmt(c['e2_unit_pass'])} ({c['e2_unit_n']}/{len(e2_unit_ids)}) | "
            f"{fmt(c['e2_x2_pass'])} ({c['e2_x2_n']}/{len(e2_x2_ids)}) | "
            f"{fmt(c['e1_evid_fail'])} ({c['e1_evid_n']}/{len(e1_evid_ids)}) |"
        )
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
